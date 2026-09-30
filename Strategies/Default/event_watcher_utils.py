"""Event Watcher: two independent, unrelated news sources surfaced in one tab.

1. PIB (Press Information Bureau) press releases.

Origin: Cochin Shipyard rallied ~11% from 23 Jul to 26 Aug 2026 and none of
the headline-news catalysts we checked (a JV, an MoU, Q1 results) lined up
with the actual price data - what did line up was INS Malvan's commissioning
on 22 Jul 2026, announced via PIB. This module scans PIB press releases for
that same kind of naval commissioning/induction announcement and flags which
listed shipbuilder it names, so a future rally like that one shows up as a
same-day alert instead of something we reconstruct after the fact.

Entirely a news-driven signal, separate from the OHLCV-based rules.md
screener/backtester - this never produces a backtestable strategy, only a
manual candidate list in its own tab. Deliberately informational only: an
earlier version attached a composite BUY/HOLD/SELL score and a price-target
"Ceiling" to each match, but with a matched-event count this small, both
were mostly noise dressed up as a number ("insufficient data"/N=1 in
practice) - removed rather than kept as a plausible-looking distraction.
Same reasoning the Meesho investor-meet section below has always used.

Feed source: PIB has no official API, and its own RSS
(pib.gov.in/RssMain.aspx) turned out to be unusable for this - inspecting
the raw XML directly showed it has no date field at all, returns Hindi
titles even with Lang=1 (so our English keyword list matched nothing), and
Regid=3 does not actually filter to Ministry of Defence releases (it's a
generic recent-releases feed spanning every ministry). We instead point at
benbenny141/pib-rss (https://github.com/benbenny141/pib-rss), an unofficial,
hourly-updated scrape of PIB that fixes exactly those three problems: real
English titles, a real pubDate per release, and a per-item ministry
category/creator field we can filter on. It's a single-maintainer community
project, not a government source - it could go stale or disappear without
warning, so treat "no new matches" and "feed unreachable" as genuinely
different failure modes (see the last_error surfaced to the UI) rather than
assuming silence means nothing happened.

2. Meesho (NSE: MEESHO) investor/analyst meet tracking - see the section
below starting at MEESHO_SYMBOL. A second, unrelated source layered onto
this same module rather than a new abstraction: different feed (NSE's own
corporate-announcements API, not PIB), different schema. Also
informational-only, like the PIB events above - see that section's
docstrings for why. Kept hardcoded to one symbol rather than generalized to
"any company's investor meets", since that's the only use case asked for and
generalizing now would mean guessing at a config schema nobody needs yet.
"""

import io
import json
import os
import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import jugaad_data.nse as nse
import pandas as pd
import requests
from pypdf import PdfReader

from constants import (
    EVENT_WATCHER_EVENTS_PATH,
    EVENT_WATCHER_INVESTOR_MEETS_META_PATH,
    EVENT_WATCHER_INVESTOR_MEETS_PATH,
    EVENT_WATCHER_KEYWORDS_PATH,
    EVENT_WATCHER_META_PATH,
    EVENT_WATCHER_SCANNED_PATH,
)

# Unofficial, community-maintained PIB scrape - see module docstring for why
# PIB's own RSS isn't usable. Updated hourly.
PIB_FEED_URL = "https://benbenny141.github.io/pib-rss/feed.xml"

# The live feed.xml is a rolling window (~8 days) of the most recent
# releases - for anything older, we go back through the feed repo's own git
# history (it's committed on every scheduled run, not force-pushed) and read
# docs/feed.xml as it existed a few days after the target date, so the
# window still covers it. See fetch_historical() below.
PIB_FEED_REPO = "benbenny141/pib-rss"
PIB_FEED_PATH_IN_REPO = "docs/feed.xml"
GITHUB_COMMITS_API = f"https://api.github.com/repos/{PIB_FEED_REPO}/commits"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{PIB_FEED_REPO}"

# The exact ministry name string this feed uses (confirmed by inspecting its
# live entries) - matched case-insensitively against each entry's author.
MINISTRY_FILTER = "ministry of defence"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# Listed shipbuilders that build/refit the vessels PIB announces as
# commissioned/inducted - the mapping this whole watcher exists for.
# Keyed by NSE symbol; values are name fragments as PIB actually writes them.
# These three DEFAULT_* dicts are the seed used the first time keywords.json
# doesn't exist yet (fresh install) - after that, the persisted file is the
# source of truth and these are never read again. Edit keywords.json (or use
# the Event Watcher tab's "Edit keywords" drawer) to change live behavior,
# not these.
DEFAULT_WATCHLIST: dict[str, list[str]] = {
    "COCHINSHIP": ["cochin shipyard"],
    "MAZDOCK": ["mazagon dock", "mazagon dock shipbuilders"],
    "GRSE": ["garden reach", "garden reach shipbuilders"],
    # Not a shipbuilder - added for MoD supply-contract announcements (see
    # DEFAULT_EVENT_KEYWORDS' "contract with" etc. below), the first
    # non-commissioning event type this watcher tracks. Real example:
    # "MoD signs Rs 811 crore contract with BDL for 160 Satellite Smart
    # Anti Airfield Weapons for IAF" named BDL by its NSE ticker directly
    # in the headline, not its full name - "bdl" is included as a fragment
    # for that reason, even though it's a short, generic-looking acronym.
    "BDL": ["bharat dynamics", "bdl"],
}

# PIB's actual commissioning/induction headlines usually name the VESSEL or
# its CLASS, not the shipbuilder - confirmed by pulling the real INS Malvan
# release ("INDIAN NAVY COMMISSIONS INS MALVAN, THE SECOND OF THE
# MAHE-CLASS ANTI-SUBMARINE WARFARE SHALLOW WATER CRAFT", PRID=2287788),
# which never says "Cochin Shipyard" at all. Matching on WATCHLIST names
# alone would have missed the exact event this tool was built around.
# This maps known vessel/class names to the shipbuilder that actually
# builds them, so _match_symbols can catch these too. Verified against
# independent sources: Kamorta-class corvettes are built at GRSE, Kolkata;
# the Scorpene-derived Kalvari-class submarines are built at MAZDOCK, Mumbai.
DEFAULT_VESSEL_CLASS_TO_SYMBOL: dict[str, str] = {
    "mahe-class": "COCHINSHIP",
    "mahe class": "COCHINSHIP",
    "next generation missile vessel": "COCHINSHIP",
    "ngmv": "COCHINSHIP",
    "kamorta-class": "GRSE",
    "kamorta class": "GRSE",
    "scorpene": "MAZDOCK",
    "scorpene-class": "MAZDOCK",
}

# Announcement language that indicates a vessel entering/leaving service -
# the specific event type that moved COCHINSHIP, not routine MoD news.
DEFAULT_EVENT_KEYWORDS = [
    "commission",
    "commissioned",
    "commissioning",
    "induct",
    "inducted",
    "induction",
    "handed over",
    "handing over",
    "delivered to indian navy",
    "delivery of",
    "keel laying",
    "keel-laying",
    "steel cutting",
    "launch of",
    # A second, independent event type: MoD signing a supply/production
    # contract with a watchlisted company - a real revenue-driving catalyst
    # distinct from a vessel commissioning, e.g. "MoD signs Rs 811 crore
    # contract with BDL for 160 Satellite Smart Anti Airfield Weapons for
    # IAF" (BDL +1.3% the next trading day). "contract with" is the phrase
    # that actually survives PIB's headline template (the deal value sits
    # between "signs" and "contract", so "signs contract" as one phrase
    # would NOT have matched this real title) - kept as a substring match
    # exactly like every other keyword here (see _match_keyword).
    "contract with",
    "signs contract",
    "inks contract",
    "contract worth",
]

COLUMNS = ["Date", "Title", "Link", "MatchedKeyword", "MatchedSymbols", "Source"]


def _load_keyword_config() -> dict:
    if not os.path.exists(EVENT_WATCHER_KEYWORDS_PATH):
        return {
            "event_keywords": list(DEFAULT_EVENT_KEYWORDS),
            "watchlist": {k: list(v) for k, v in DEFAULT_WATCHLIST.items()},
            "vessel_class_to_symbol": dict(DEFAULT_VESSEL_CLASS_TO_SYMBOL),
        }
    with open(EVENT_WATCHER_KEYWORDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_keyword_config() -> None:
    with open(EVENT_WATCHER_KEYWORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"event_keywords": EVENT_KEYWORDS, "watchlist": WATCHLIST, "vessel_class_to_symbol": VESSEL_CLASS_TO_SYMBOL},
            f,
            indent=2,
        )


# Mutable module-level config, loaded once at import - _match_symbols and
# _match_keyword read these names directly, so editing them in place (via
# set_keyword_config) takes effect on the very next refresh/historical fetch
# without restarting the process.
_initial_config = _load_keyword_config()
EVENT_KEYWORDS: list[str] = _initial_config["event_keywords"]
WATCHLIST: dict[str, list[str]] = _initial_config["watchlist"]
VESSEL_CLASS_TO_SYMBOL: dict[str, str] = _initial_config["vessel_class_to_symbol"]


def get_keyword_config() -> dict:
    """Read-modify-write shape for the editor drawer: watchlist and vessel
    aliases as lists (not dicts) so the UI can render/reorder/edit them
    without juggling object keys."""
    return {
        "event_keywords": list(EVENT_KEYWORDS),
        "watchlist": [{"symbol": symbol, "names": list(names)} for symbol, names in WATCHLIST.items()],
        "vessel_class_aliases": [{"phrase": phrase, "symbol": symbol} for phrase, symbol in VESSEL_CLASS_TO_SYMBOL.items()],
    }


def set_keyword_config(payload: dict) -> dict:
    """Validates and replaces the live matching config, then persists it to
    keywords.json so it survives a restart. Rebinds EVENT_KEYWORDS/WATCHLIST/
    VESSEL_CLASS_TO_SYMBOL in place (clear + update) rather than reassigning
    the names, so _match_symbols/_match_keyword - which capture these as
    globals - see the change immediately without needing `global` there."""
    event_keywords = [str(k).strip().lower() for k in payload.get("event_keywords", []) if str(k).strip()]
    if not event_keywords:
        return {"status": "error", "message": "At least one event keyword is required."}

    watchlist = {}
    for group in payload.get("watchlist", []):
        symbol = str(group.get("symbol", "")).strip().upper()
        names = [str(n).strip().lower() for n in group.get("names", []) if str(n).strip()]
        if not symbol:
            continue
        watchlist[symbol] = names

    aliases = {}
    for row in payload.get("vessel_class_aliases", []):
        phrase = str(row.get("phrase", "")).strip().lower()
        symbol = str(row.get("symbol", "")).strip().upper()
        if not phrase or not symbol:
            continue
        aliases[phrase] = symbol

    EVENT_KEYWORDS.clear()
    EVENT_KEYWORDS.extend(event_keywords)
    WATCHLIST.clear()
    WATCHLIST.update(watchlist)
    VESSEL_CLASS_TO_SYMBOL.clear()
    VESSEL_CLASS_TO_SYMBOL.update(aliases)

    _save_keyword_config()
    return {"status": "ok", **get_keyword_config()}


def _match_symbols(title: str) -> list[str]:
    lowered = title.lower()
    found = {symbol for symbol, names in WATCHLIST.items() if any(name in lowered for name in names)}
    for phrase, symbol in VESSEL_CLASS_TO_SYMBOL.items():
        if phrase in lowered:
            found.add(symbol)
    return list(found)


def _match_keyword(title: str) -> str | None:
    lowered = title.lower()
    for kw in EVENT_KEYWORDS:
        if kw in lowered:
            return kw
    return None


def _load_meta() -> dict:
    if not os.path.exists(EVENT_WATCHER_META_PATH):
        return {"last_checked": None, "last_error": None}
    with open(EVENT_WATCHER_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_meta(meta: dict) -> None:
    with open(EVENT_WATCHER_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f)


def _entry_to_scanned_row(entry: dict, matched: bool, symbols: list[str], keyword: str | None, source: str) -> dict:
    return {
        "Date": entry.get("published", "") or entry.get("updated", ""),
        "Title": entry.get("title", ""),
        "Link": entry.get("link", ""),
        "Matched": matched,
        "MatchedKeyword": keyword or "",
        "MatchedSymbols": ",".join(symbols),
        "Source": source,
    }


def _save_scanned(rows: list[dict]) -> None:
    """Every Ministry of Defence release the last refresh/historical fetch
    saw, matched or not - lets the UI show what got filtered out and why,
    not just the survivors kept in events.csv. Overwritten on each new scan
    (this is "what did we just see", not an accumulating history like
    events.csv - the feed's own rolling window already limits how far back
    a single scan can look anyway)."""
    with open(EVENT_WATCHER_SCANNED_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f)


def get_scanned() -> list[dict]:
    if not os.path.exists(EVENT_WATCHER_SCANNED_PATH):
        return []
    with open(EVENT_WATCHER_SCANNED_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)
    # Sort by the actual parsed timestamp, not the raw string - LIVE rows use
    # RFC-822 dates ("Wed, 16 Sep 2026 11:42:00 +0530"), which don't sort
    # correctly as text (weekday names/unpadded fields break lexical order).
    # Unparseable dates sort last rather than crashing or scattering randomly.
    return sorted(
        rows,
        key=lambda r: pd.to_datetime(r.get("Date", ""), errors="coerce", utc=True) or pd.Timestamp.min.tz_localize("UTC"),
        reverse=True,
    )


def load_events() -> pd.DataFrame:
    if not os.path.exists(EVENT_WATCHER_EVENTS_PATH):
        return pd.DataFrame(columns=COLUMNS)
    # keep_default_na=False: a blank Link (simulated rows have none) must
    # stay "" on reload, not become NaN - NaN isn't valid JSON and breaks
    # every response this feeds.
    return pd.read_csv(EVENT_WATCHER_EVENTS_PATH, keep_default_na=False)


def get_state() -> dict:
    meta = _load_meta()
    events = load_events()
    if not events.empty:
        # Sort by the actual parsed timestamp, not the raw string - see
        # get_scanned()'s comment on why RFC-822 dates don't sort as text.
        events = events.assign(_sort_ts=pd.to_datetime(events["Date"], errors="coerce", utc=True))
        events = events.sort_values("_sort_ts", ascending=False, na_position="last").drop(columns="_sort_ts")
    records = events.to_dict("records")
    return {
        "last_checked": meta.get("last_checked"),
        "last_error": meta.get("last_error"),
        "watchlist": {symbol: names[0] for symbol, names in WATCHLIST.items()},
        "events": records,
    }


def refresh() -> dict:
    """Fetches the community PIB feed, keeps only Ministry of Defence
    releases, matches naval-commissioning language against the shipbuilder
    watchlist, and merges any new matches into the on-disk cache (all other
    items are discarded - only ones with both an event keyword AND a
    watchlisted symbol survive; the feed only holds a rolling window of
    recent releases, so we accumulate our own history across refreshes
    rather than re-deriving it each time)."""
    meta = _load_meta()
    existing = load_events()

    try:
        resp = requests.get(PIB_FEED_URL, headers=REQUEST_HEADERS, timeout=20)
        resp.raise_for_status()
        parsed = feedparser.parse(resp.content)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"Feed did not parse: {parsed.bozo_exception}")

        defence_entries = [e for e in parsed.entries if MINISTRY_FILTER in e.get("author", "").lower()]

        new_rows = []
        scanned_rows = []
        existing_links = set(existing["Link"]) if not existing.empty else set()
        for entry in defence_entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            symbols = _match_symbols(title)
            keyword = _match_keyword(title)
            matched = bool(symbols and keyword)
            scanned_rows.append(_entry_to_scanned_row(entry, matched, symbols, keyword, "LIVE"))
            if link in existing_links or not matched:
                continue
            published = entry.get("published", "") or entry.get("updated", "")
            new_rows.append(
                {
                    "Date": published or datetime.now(timezone.utc).isoformat(),
                    "Title": title,
                    "Link": link,
                    "MatchedKeyword": keyword,
                    "MatchedSymbols": ",".join(symbols),
                    "Source": "LIVE",
                }
            )

        _save_scanned(scanned_rows)

        if new_rows:
            combined = pd.concat([existing, pd.DataFrame(new_rows, columns=COLUMNS)], ignore_index=True)
            combined.to_csv(EVENT_WATCHER_EVENTS_PATH, index=False)

        meta["last_checked"] = datetime.now(timezone.utc).isoformat()
        meta["last_error"] = None
        _save_meta(meta)
        return {"status": "ok", "new_matches": len(new_rows), "scanned": len(defence_entries)}
    except Exception as exc:
        meta["last_checked"] = datetime.now(timezone.utc).isoformat()
        meta["last_error"] = str(exc)
        _save_meta(meta)
        return {"status": "error", "message": str(exc)}


def _find_snapshot_sha(target: date) -> str | None:
    """The feed repo's docs/feed.xml is committed on every scheduled run
    (real git history, not a force-pushed branch), so a snapshot from a few
    days AFTER target still has target inside its rolling ~8-day window.
    Tries progressively further-out snapshots until one actually contains
    the target date; returns None if none of them do."""
    for offset_days in (2, 5, 9, 14, 21):
        until = datetime.combine(target + timedelta(days=offset_days), datetime.min.time()).isoformat() + "Z"
        resp = requests.get(
            GITHUB_COMMITS_API,
            params={"path": PIB_FEED_PATH_IN_REPO, "until": until, "per_page": 1},
            timeout=20,
        )
        resp.raise_for_status()
        commits = resp.json()
        if not commits:
            continue
        sha = commits[0]["sha"]
        raw_url = f"{GITHUB_RAW_BASE}/{sha}/{PIB_FEED_PATH_IN_REPO}"
        raw_resp = requests.get(raw_url, timeout=30)
        raw_resp.raise_for_status()
        parsed = feedparser.parse(raw_resp.content)
        target_str = target.strftime("%d %b %Y")
        if any(target_str in e.get("published", "") for e in parsed.entries):
            return sha
    return None


def fetch_historical(target_iso_date: str) -> dict:
    """Real historical lookup, not a fixture: the live feed only covers the
    last ~8 days, so for anything older we pull the feed repo's own git
    history and read docs/feed.xml as it existed a few days after the
    target date (see _find_snapshot_sha) - the same file, just an older
    commit of it, still containing real PIB releases with real dates and
    real links.

    Runs the exact same Ministry-of-Defence + keyword/symbol matching as
    refresh(). Rows land tagged Source="HISTORICAL" alongside LIVE matches
    (both are equally real; the tag only says which fetch path found them).
    """
    try:
        target = date.fromisoformat(target_iso_date)
    except ValueError:
        return {"status": "error", "message": f"Invalid date: {target_iso_date!r} (expected YYYY-MM-DD)"}

    try:
        sha = _find_snapshot_sha(target)
        if sha is None:
            return {
                "status": "error",
                "message": f"No feed snapshot in the pib-rss repo's history covers {target.isoformat()} "
                "(repo history may not go back that far, or GitHub's API is unreachable).",
            }

        raw_url = f"{GITHUB_RAW_BASE}/{sha}/{PIB_FEED_PATH_IN_REPO}"
        raw_resp = requests.get(raw_url, timeout=30)
        raw_resp.raise_for_status()
        parsed = feedparser.parse(raw_resp.content)

        target_str = target.strftime("%d %b %Y")
        day_entries = [e for e in parsed.entries if target_str in e.get("published", "")]
        defence_entries = [e for e in day_entries if MINISTRY_FILTER in e.get("author", "").lower()]

        existing = load_events()
        existing_links = set(existing["Link"]) if not existing.empty else set()
        new_rows = []
        scanned_rows = []
        for entry in defence_entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            symbols = _match_symbols(title)
            keyword = _match_keyword(title)
            matched = bool(symbols and keyword)
            scanned_rows.append(_entry_to_scanned_row(entry, matched, symbols, keyword, "HISTORICAL"))
            if link in existing_links or not matched:
                continue
            new_rows.append(
                {
                    "Date": entry.get("published", target.isoformat()),
                    "Title": title,
                    "Link": link,
                    "MatchedKeyword": keyword,
                    "MatchedSymbols": ",".join(symbols),
                    "Source": "HISTORICAL",
                }
            )

        _save_scanned(scanned_rows)

        if new_rows:
            combined = pd.concat([existing, pd.DataFrame(new_rows, columns=COLUMNS)], ignore_index=True)
            combined.to_csv(EVENT_WATCHER_EVENTS_PATH, index=False)

        return {
            "status": "ok",
            "date": target.isoformat(),
            "defence_releases_that_day": len(defence_entries),
            "new_matches": len(new_rows),
        }
    except requests.RequestException as exc:
        return {"status": "error", "message": f"GitHub fetch failed: {exc}"}


def clear_historical() -> dict:
    """Removes every HISTORICAL row, leaving real-time LIVE matches untouched."""
    existing = load_events()
    if existing.empty:
        return {"status": "ok", "removed": 0}
    removed = int((existing["Source"] == "HISTORICAL").sum())
    remaining = existing[existing["Source"] != "HISTORICAL"]
    remaining.to_csv(EVENT_WATCHER_EVENTS_PATH, index=False)
    return {"status": "ok", "removed": removed}


# --------------------------------------------------------------------------
# Meesho (NSE: MEESHO) investor/analyst meet tracking
# --------------------------------------------------------------------------
# A second, independent event source in the same tab (see module docstring).
# Data source: investor.meesho.com/announcements returns "Access Denied" to
# automated requests, so this uses NSE's own corporate-announcements API via
# jugaad_data (already a project dependency) instead - the same API NSE's
# own "corporate-filings-announcements" page is built on.
MEESHO_SYMBOL = "MEESHO"

# The exact `desc` value NSE tags an investor/analyst-meet filing with
# (confirmed against live API responses for MEESHO) - every other `desc`
# (ESOP grants, board outcomes, etc.) is discarded. This alone isn't
# specific enough though: it also tags POST-meet filings (call recordings,
# transcripts) that have no schedule/date table at all - `desc` narrows to
# "investor-meet-related", and `attchmntText` containing "schedule" (seen
# as "Schedule of meet", "Schedule of Investors/Analysts meet", and
# "Revised Schedule of ...") narrows further to "announces a future
# meeting", which is the only kind of filing with a date to parse out.
INVESTOR_MEET_DESC = "Analysts/Institutional Investor Meet/Con. Call Updates"
INVESTOR_MEET_SCHEDULE_MARKER = "schedule"

# `desc`+"schedule" narrows to "announces a future meeting", but that still
# lets through other scheduled-event types NSE files under the same broad
# desc bucket - earnings conference calls ("Meesho Limited - Q1FY27 Earnings
# Conference Call"), broker-conference slots named after the conference, not
# the meeting type ("Kotak Chasing Growth 2026", "Advantage India - Axis
# Capital's India Conference"), and standalone non-deal roadshows filed
# without the "Meeting with Institutional Investors" header at all. Real
# examples pulled from this tracker's own cached data before this filter
# existed. Matched against the PDF-parsed EventName (see
# _parse_meeting_event_name) with startswith rather than equality: a
# multi-day roadshow's Event cell parses as "Meeting with Institutional
# Investors Non-Deal Roadshow" or "...Particulars of event One-on-one/
# Group Meetings" (the regex boundary bleeds into the next field) - both are
# still genuinely a Meeting with Institutional Investors filing and should
# be kept, just with untrimmed trailing text.
INVESTOR_MEET_EVENT_NAME_PREFIX = "meeting with institutional investors"

# How far back each refresh looks. Meesho IPO'd Dec 2025; 400 days
# comfortably covers "since IPO" with buffer, and re-querying the whole
# window every refresh (rather than tracking a cursor) is deliberately
# simple - the SeqId dedup below makes it idempotent, and the corporate-
# announcements endpoint is cheap compared to the PDF downloads.
INVESTOR_MEET_LOOKBACK_DAYS = 400

INVESTOR_MEETS_COLUMNS = ["SeqId", "Symbol", "FilingDate", "MeetingDate", "EventName", "PdfUrl"]

# Labelled "Date" for a single-day meet or "Date of events" for a multi-day
# roadshow (both seen in real filings) - text between that label and the
# following "Mode" label holds one or more "<Weekday>, <Month> <Day>,
# <Year>" tokens, one per meeting day.
_MEETING_DATE_SECTION_RE = re.compile(r"\bDate(?:\s+of\s+events?)?\b\s*[:\-]?\s*(.*?)\bMode\b", re.IGNORECASE | re.DOTALL)
_MEETING_DATE_TOKEN_RE = re.compile(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s*(\d{4})")

# The "Event" field ("Meeting with Institutional Investors" in every filing
# checked) - the label always sits right before either "Name of Event",
# "Particulars of event(s)", or straight to "Date" depending on the filing.
_MEETING_EVENT_NAME_RE = re.compile(
    r"\bEvent\b\s*[:\-]?\s*(.*?)\s*(?:Name of Event|Particulars of events?|Date)",
    re.IGNORECASE | re.DOTALL,
)

# A multi-column table (one column per meeting day) extracts as its cell
# text repeated once per column - e.g. a 4-day roadshow's "Event" cell
# becomes "Meeting with Institutional Investors" x4 concatenated. Collapses
# immediately-repeated phrases (2-8 words) back down to one occurrence;
# applied iteratively since collapsing one repeat can reveal another
# (see _parse_meeting_event_name).
_REPEATED_PHRASE_RE = re.compile(r"\b(\w[\w/-]*(?:\s+\w[\w/-]*){1,7})\s+\1\b", re.IGNORECASE)


def _dedupe_repeated_phrase(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = _REPEATED_PHRASE_RE.sub(r"\1", text)
    return text


def _parse_meeting_dates(pdf_text: str) -> list[date]:
    """Extracts the actual meeting date(s) from an investor-meet filing's
    PDF body. The filing timestamp (an_dt/sort_date from the corporate-
    announcements API) is NOT the meeting date - SEBI LODR Reg. 30 requires
    filing at least 2 working days before the meeting (Meesho has
    repeatedly filed late or same-day and disclosed the delay in the PDF
    itself), and the real date(s) - sometimes several, for a multi-day
    roadshow - only appear in a small table inside the PDF. Returns every
    date found in that table; empty if the expected "Date .../ Mode" shape
    isn't there (unexpected layout, or the PDF fetch/parse failed) rather
    than guessing from the filing date."""
    section_match = _MEETING_DATE_SECTION_RE.search(pdf_text)
    if not section_match:
        return []
    dates = []
    for month_str, day_str, year_str in _MEETING_DATE_TOKEN_RE.findall(section_match.group(1)):
        try:
            dates.append(datetime.strptime(f"{month_str} {day_str} {year_str}", "%B %d %Y").date())
        except ValueError:
            continue
    return dates


def _parse_meeting_event_name(pdf_text: str) -> str | None:
    """Best-effort "Event" field (e.g. "Meeting with Institutional
    Investors") for display - None if the expected label isn't found,
    falling back to the API's own attchmntText at the call site."""
    match = _MEETING_EVENT_NAME_RE.search(pdf_text)
    if not match:
        return None
    # pypdf can't map some PDFs' custom-encoded dash glyph to a real
    # Unicode codepoint and emits U+FFFD instead - swap in a plain hyphen
    # rather than showing a replacement-character box in the UI.
    name = _dedupe_repeated_phrase(" ".join(match.group(1).split())).replace("�", "-")
    return name or None


def _download_pdf_text(session: requests.Session, url: str) -> str | None:
    """Downloads an NSE corporate-announcement PDF and extracts its text.

    A bare `requests.get` (or even an NSELive session used exactly as
    NSELive builds it) 404s here rather than returning the PDF -
    NSELive.__init__ permanently sets a literal `Host: www.nseindia.com`
    header on its session, and `requests` sends that header as-is on every
    request from that session instead of inferring it per-URL. The PDF
    lives on a different host (nsearchives.nseindia.com), which 404s
    because the Host header doesn't match the host it's actually being
    asked for - confirmed by comparing the 404 HTML body against a 200 PDF
    response with only that one header corrected. Overriding Host back to
    the PDF's own host for just this request is the fix; the session's
    other cookies (set against nseindia.com when NSELive() was
    constructed) are what nsearchives.nseindia.com actually needs to allow
    the request through at all."""
    try:
        host = urlparse(url).hostname
        resp = session.get(url, headers={"Host": host}, timeout=30)
        resp.raise_for_status()
        reader = PdfReader(io.BytesIO(resp.content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return None


def load_investor_meets() -> pd.DataFrame:
    if not os.path.exists(EVENT_WATCHER_INVESTOR_MEETS_PATH):
        return pd.DataFrame(columns=INVESTOR_MEETS_COLUMNS)
    return pd.read_csv(EVENT_WATCHER_INVESTOR_MEETS_PATH, keep_default_na=False, dtype={"SeqId": str})


def _save_investor_meets(df: pd.DataFrame) -> None:
    df.to_csv(EVENT_WATCHER_INVESTOR_MEETS_PATH, index=False)


def _load_investor_meets_meta() -> dict:
    if not os.path.exists(EVENT_WATCHER_INVESTOR_MEETS_META_PATH):
        return {"last_checked": None, "last_error": None}
    with open(EVENT_WATCHER_INVESTOR_MEETS_META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_investor_meets_meta(meta: dict) -> None:
    with open(EVENT_WATCHER_INVESTOR_MEETS_META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f)


def refresh_investor_meets() -> dict:
    """Pulls MEESHO's NSE corporate-announcements feed, keeps only
    Investors/Analysts-meet filings, downloads and parses each new one's
    attached PDF to recover the real meeting date(s), and merges any new
    (filing, meeting-date) pairs into the on-disk cache. Idempotent via
    SeqId (NSE's own unique id per filing) - safe to call repeatedly.

    Deliberately informational only - no Signal/Ceiling scoring attached,
    same as the PIB-derived events above. A 9-event backtest across every
    "Meeting with Institutional Investors" filing since Meesho's Dec 2025
    IPO found no reliable directional edge (meet-day to next-day: 4/9
    positive, median -0.38%; meet-day to +2 days: 6/9 positive, median
    +0.55%, but two-thirds of the total gain came from just two events, at
    least one independently attributable to an unrelated brokerage note,
    not the meeting itself) - not a real sample size or a validated signal,
    just a reason not to attach a score to this feed."""
    meta = _load_investor_meets_meta()
    existing = load_investor_meets()
    existing_seq_ids = set(existing["SeqId"]) if not existing.empty else set()

    try:
        live = nse.NSELive()
        to_date = date.today()
        from_date = to_date - timedelta(days=INVESTOR_MEET_LOOKBACK_DAYS)
        announcements = live.corporate_announcements(
            segment="equities", from_date=from_date, to_date=to_date, symbol=MEESHO_SYMBOL
        )
        meet_filings = [
            a
            for a in (announcements or [])
            if a.get("desc") == INVESTOR_MEET_DESC
            and INVESTOR_MEET_SCHEDULE_MARKER in a.get("attchmntText", "").lower()
        ]

        new_rows = []
        for filing in meet_filings:
            seq_id = str(filing.get("seq_id", ""))
            if not seq_id or seq_id in existing_seq_ids:
                continue
            existing_seq_ids.add(seq_id)

            pdf_url = filing.get("attchmntFile", "")
            pdf_text = _download_pdf_text(live.s, pdf_url) if pdf_url else None
            meeting_dates = _parse_meeting_dates(pdf_text) if pdf_text else []
            event_name = (_parse_meeting_event_name(pdf_text) if pdf_text else None) or filing.get("attchmntText", "")
            filing_date = filing.get("an_dt") or filing.get("exchdisstime") or filing.get("sort_date", "")

            # desc + "schedule" only narrows to "a scheduled event of some
            # kind" - earnings calls, broker-conference slots, and bare
            # roadshows share that same bucket (see
            # INVESTOR_MEET_EVENT_NAME_PREFIX). Only "Meeting with
            # Institutional Investors" filings are what this tracker is
            # actually meant to surface; skip anything else. Deliberately
            # NOT written to the cache at all (not even as a filtered-out
            # row), so a filing rejected here has no seq_id in
            # events.csv/existing_seq_ids and gets its PDF re-downloaded and
            # re-checked on every future refresh rather than remembered as
            # "seen" - a few extra PDF fetches for the small number of
            # non-matching filings Meesho has filed is a fine trade for not
            # needing a second persisted "skipped" list.
            if not event_name.strip().lower().startswith(INVESTOR_MEET_EVENT_NAME_PREFIX):
                continue

            # No meeting_dates means the PDF fetch/parse failed or the
            # layout didn't match what we expect - still record the filing
            # (with an empty MeetingDate) so it's visible with a link to
            # check by hand, rather than silently dropping it.
            for meeting_date in meeting_dates or [None]:
                new_rows.append(
                    {
                        "SeqId": seq_id,
                        "Symbol": MEESHO_SYMBOL,
                        "FilingDate": filing_date,
                        "MeetingDate": meeting_date.isoformat() if meeting_date else "",
                        "EventName": event_name,
                        "PdfUrl": pdf_url,
                    }
                )

        if new_rows:
            combined = pd.concat([existing, pd.DataFrame(new_rows, columns=INVESTOR_MEETS_COLUMNS)], ignore_index=True)
            _save_investor_meets(combined)

        meta["last_checked"] = datetime.now(timezone.utc).isoformat()
        meta["last_error"] = None
        _save_investor_meets_meta(meta)
        return {"status": "ok", "new_filings": len(new_rows), "scanned": len(meet_filings)}
    except Exception as exc:
        meta["last_checked"] = datetime.now(timezone.utc).isoformat()
        meta["last_error"] = str(exc)
        _save_investor_meets_meta(meta)
        return {"status": "error", "message": str(exc)}


def get_investor_meets_state() -> dict:
    """Every cached MEESHO investor/analyst meet, newest meeting (or newest
    filing, for rows whose date couldn't be parsed) first. Status is
    "scheduled" if MeetingDate is today or later, "past" if it's before
    today, "unknown" if the PDF's date couldn't be parsed - purely
    informational, no Signal/Ceiling attached (see refresh_investor_meets'
    docstring for why)."""
    meta = _load_investor_meets_meta()
    df = load_investor_meets()
    today = date.today()

    rows = []
    for _, row in df.iterrows():
        meeting_date_str = str(row.get("MeetingDate", "") or "")
        if meeting_date_str:
            status = "scheduled" if date.fromisoformat(meeting_date_str) >= today else "past"
        else:
            status = "unknown"
        rows.append(
            {
                "Symbol": row.get("Symbol", ""),
                "FilingDate": row.get("FilingDate", ""),
                "MeetingDate": meeting_date_str or None,
                "EventName": row.get("EventName", ""),
                "PdfUrl": row.get("PdfUrl", ""),
                "Status": status,
            }
        )

    rows.sort(key=lambda r: r["MeetingDate"] or r["FilingDate"] or "", reverse=True)
    return {
        "last_checked": meta.get("last_checked"),
        "last_error": meta.get("last_error"),
        "meets": rows,
    }
