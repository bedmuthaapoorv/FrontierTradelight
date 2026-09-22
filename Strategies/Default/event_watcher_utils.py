"""PIB (Press Information Bureau) event watcher.

Origin: Cochin Shipyard rallied ~11% from 23 Jul to 26 Aug 2026 and none of
the headline-news catalysts we checked (a JV, an MoU, Q1 results) lined up
with the actual price data - what did line up was INS Malvan's commissioning
on 22 Jul 2026, announced via PIB. This module scans PIB press releases for
that same kind of naval commissioning/induction announcement and flags which
listed shipbuilder it names, so a future rally like that one shows up as a
same-day alert instead of something we reconstruct after the fact.

Entirely a news-driven signal, separate from the OHLCV-based rules.md
screener/backtester - this never produces a backtestable strategy, only a
manual candidate list in its own tab.

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
"""

import json
import os
from datetime import date, datetime, timedelta, timezone

import feedparser
import pandas as pd
import requests

from constants import (
    EVENT_WATCHER_EVENTS_PATH,
    EVENT_WATCHER_KEYWORDS_PATH,
    EVENT_WATCHER_META_PATH,
    EVENT_WATCHER_SCANNED_PATH,
)
from nse_utils import fetch_stock_history

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
]

COLUMNS = ["Date", "Title", "Link", "MatchedKeyword", "MatchedSymbols", "Source"]

# Reference point for the BUY/HOLD/SELL heuristic below: Cochin Shipyard's
# entire post-commissioning rally (23 Jul-26 Aug 2026) was ~11% - the one
# real case this watcher is modeled on. Not a backtested threshold (this
# watcher never feeds the backtester, see module docstring), just a rough
# "has a comparable move already happened" read.
SIGNAL_RALLY_ALREADY_PLAYED_OUT_PCT = 10.0
SIGNAL_CACHE_TTL = timedelta(hours=6)

# In-memory only - a stale cached signal just means the tab shows a slightly
# outdated read until it expires or the process restarts, never wrong data
# written anywhere.
_signal_cache: dict[str, tuple[datetime, str]] = {}


def _price_signal(symbols: list[str], event_date_str: str) -> str:
    """BUY/HOLD/SELL for a matched announcement, based on how far the first
    matched symbol has already moved since the event date.

    BUY  - up since the event, but by less than a Cochin-Shipyard-sized
           rally - the move may still have room to run.
    HOLD - flat or down since the event - the catalyst hasn't (yet) shown up
           in price, or price data couldn't be read cleanly.
    SELL - already up more than that reference rally - a historically
           comparable move has likely already played out.

    This is a heuristic for a manual candidate list, not a validated rule -
    unlike rules.md/exit_rules.md, it has never been backtested."""
    if not symbols:
        return "N/A"
    symbol = symbols[0]
    cache_key = f"{symbol}:{event_date_str}"
    cached = _signal_cache.get(cache_key)
    if cached and datetime.now(timezone.utc) - cached[0] < SIGNAL_CACHE_TTL:
        return cached[1]

    signal = "N/A"
    try:
        event_ts = pd.to_datetime(event_date_str, utc=True, errors="coerce")
        if pd.isna(event_ts):
            return signal
        event_date = event_ts.date()
        to_date = date.today()
        if event_date <= to_date:
            # Widen a week before the event so a non-trading event date
            # (e.g. a Saturday PIB release) still lands on the last real
            # close at/before it, instead of finding zero rows there.
            df = fetch_stock_history(
                symbol=symbol, from_date=event_date - timedelta(days=7), to_date=to_date, series="EQ"
            )
            if df is not None and not df.empty:
                df = df.sort_values(by="DATE")
                on_or_before_event = df[df["DATE"].dt.date <= event_date]
                if not on_or_before_event.empty:
                    entry_close = float(on_or_before_event.iloc[-1]["CLOSE"])
                    current_close = float(df.iloc[-1]["CLOSE"])
                    if df.iloc[-1]["DATE"].date() == on_or_before_event.iloc[-1]["DATE"].date():
                        # No trading session has closed since the event yet -
                        # genuinely too early to read a move, not a data gap.
                        signal = "HOLD"
                    else:
                        pct_move = (current_close - entry_close) / entry_close * 100
                        if pct_move >= SIGNAL_RALLY_ALREADY_PLAYED_OUT_PCT:
                            signal = "SELL"
                        elif pct_move > 0:
                            signal = "BUY"
                        else:
                            signal = "HOLD"
    except Exception:
        signal = "N/A"

    _signal_cache[cache_key] = (datetime.now(timezone.utc), signal)
    return signal


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
    for row in records:
        symbols = [s for s in str(row.get("MatchedSymbols", "")).split(",") if s]
        row["Signal"] = _price_signal(symbols, row.get("Date", ""))
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
