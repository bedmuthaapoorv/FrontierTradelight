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
import pandas_ta as ta
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

# Coarse grouping so the signal/duration logic can reason about "what kind of
# catalyst is this" instead of treating a keel-laying (years from revenue)
# the same as a signed contract (revenue-driving now). Keyed by the exact
# keyword strings in DEFAULT_EVENT_KEYWORDS/EVENT_KEYWORDS; a keyword added
# later via the UI's keyword editor that isn't in this map falls back to
# "other" in _event_type rather than raising - the taxonomy is a refinement
# layer on top of matching, not a gate on it.
KEYWORD_TO_EVENT_TYPE: dict[str, str] = {
    "commission": "commissioning",
    "commissioned": "commissioning",
    "commissioning": "commissioning",
    "induct": "commissioning",
    "inducted": "commissioning",
    "induction": "commissioning",
    "handed over": "commissioning",
    "handing over": "commissioning",
    "delivered to indian navy": "commissioning",
    "delivery of": "commissioning",
    "keel laying": "construction_milestone",
    "keel-laying": "construction_milestone",
    "steel cutting": "construction_milestone",
    "launch of": "construction_milestone",
    "contract with": "contract_award",
    "signs contract": "contract_award",
    "inks contract": "contract_award",
    "contract worth": "contract_award",
}


def _event_type(keyword: str | None) -> str:
    """Coarse catalyst category for `keyword` (see KEYWORD_TO_EVENT_TYPE).
    "other" for anything not in the map - e.g. a keyword added later via the
    keyword-editor drawer that hasn't been classified yet - so matching
    never breaks even when the taxonomy lags the keyword list."""
    if not keyword:
        return "other"
    return KEYWORD_TO_EVENT_TYPE.get(keyword.strip().lower(), "other")


COLUMNS = ["Date", "Title", "Link", "MatchedKeyword", "MatchedSymbols", "Source"]

# Below this many historical instances of an event_type, a prior (median CAR,
# median duration) is withheld rather than shown - with 1-2 real observations
# a "median" is just that one number wearing a stats term, and presenting it
# as a calibrated estimate would be more misleading than showing nothing.
MIN_SAMPLE_FOR_PRIOR = 5

SIGNAL_CACHE_TTL = timedelta(hours=6)

# In-memory only - a stale cached signal just means the tab shows a slightly
# outdated read until it expires or the process restarts, never wrong data
# written anywhere.
_signal_cache: dict[str, tuple[datetime, dict]] = {}


def _atr(df: pd.DataFrame, length: int = 14) -> float | None:
    """Average True Range off a HIGH/LOW/CLOSE frame - same pandas_ta call as
    generated_exit_strategy.py's _get_atr, used here to size a price move
    against the stock's own recent volatility instead of a flat percentage
    threshold (one stock's normal noise is another's breakout)."""
    try:
        atr_series = ta.atr(df["HIGH"], df["LOW"], df["CLOSE"], length=length)
        value = atr_series.iloc[-1]
        return float(value) if pd.notna(value) else None
    except Exception:
        return None


def _price_signal(symbols: list[str], event_date_str: str, event_type: str = "other") -> dict:
    """Composite signal for a matched announcement, based on how far the
    first matched symbol has moved since the event date, sized against the
    stock's own volatility and against how this event_type has historically
    played out (once enough instances exist to say anything about that).

    Returns a dict rather than a single BUY/HOLD/SELL label:
      SignalLabel      - "Buy" / "Neutral" / "Fade" / "N/A"
      SignalScore      - -100..100, the move-so-far z-score scaled and
                         capped; more negative once the move already looks
                         "played out" relative to the stock's own ATR
      MoveSoFarPct     - raw % move from entry_close to current_close
      MoveZScore       - MoveSoFarPct's underlying move in ATR units
                         (None if ATR couldn't be computed)
      PriorEventTypeCAR - median historical % move for this event_type
                         across past matched events, or None below
                         MIN_SAMPLE_FOR_PRIOR
      PriorSampleSize  - how many past instances of this event_type that
                         median is based on
      SignalConfidence - "Low" / "Medium" / "High", from PriorSampleSize -
                         a stand-in for "should you trust SignalScore", not
                         a claim that the score itself is more precise

    This is a heuristic for a manual candidate list, not a validated rule -
    unlike rules.md/exit_rules.md, it has never been backtested."""
    empty: dict = {
        "SignalLabel": "N/A",
        "SignalScore": None,
        "MoveSoFarPct": None,
        "MoveZScore": None,
        "PriorEventTypeCAR": None,
        "PriorSampleSize": 0,
        "SignalConfidence": "Low",
    }
    if not symbols:
        return dict(empty)
    symbol = symbols[0]
    cache_key = f"{symbol}:{event_date_str}:{event_type}"
    cached = _signal_cache.get(cache_key)
    if cached and datetime.now(timezone.utc) - cached[0] < SIGNAL_CACHE_TTL:
        return dict(cached[1])

    result = dict(empty)
    try:
        event_ts = pd.to_datetime(event_date_str, utc=True, errors="coerce")
        if pd.isna(event_ts):
            _signal_cache[cache_key] = (datetime.now(timezone.utc), dict(result))
            return dict(result)
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
                        result["SignalLabel"] = "HOLD"
                        result["MoveSoFarPct"] = 0.0
                    else:
                        pct_move = (current_close - entry_close) / entry_close * 100
                        result["MoveSoFarPct"] = pct_move

                        # ATR needs ~14 prior trading sessions to mean
                        # anything - the -7-calendar-day window above (kept
                        # narrow so a Saturday event date still lands on the
                        # right entry close) isn't enough for that, so pull
                        # a separate, wider lookback (~45 calendar days is
                        # comfortably >14 trading sessions even across a
                        # holiday-heavy stretch) just for the ATR input.
                        atr_history = fetch_stock_history(
                            symbol=symbol, from_date=event_date - timedelta(days=45), to_date=event_date, series="EQ"
                        )
                        atr_asof_entry = _atr(atr_history) if atr_history is not None and not atr_history.empty else None
                        move_z = None
                        if atr_asof_entry and atr_asof_entry > 0:
                            move_z = (current_close - entry_close) / atr_asof_entry
                            result["MoveZScore"] = move_z

                        prior_car, prior_n = _event_type_prior_car(event_type)
                        result["PriorEventTypeCAR"] = prior_car
                        result["PriorSampleSize"] = prior_n
                        result["SignalConfidence"] = _confidence_from_sample(prior_n)

                        # Score is the move-so-far in ATR units, scaled to
                        # +-100 and clipped - a move already several ATRs
                        # above entry scores as SELL (likely played out), a
                        # small move as BUY (room to run), regardless of what
                        # raw % that happens to be for this particular stock.
                        # Labels are kept to the existing BUY/HOLD/SELL
                        # vocabulary (rather than e.g. "Fade"/"Neutral") so
                        # the frontend's color-coding, which switches on
                        # these exact strings, keeps working unchanged.
                        if move_z is not None:
                            score = max(-100.0, min(100.0, move_z * 25.0))
                            result["SignalScore"] = score
                            if score >= 40:
                                result["SignalLabel"] = "SELL"
                            elif score <= -10:
                                result["SignalLabel"] = "HOLD"
                            else:
                                result["SignalLabel"] = "BUY"
                        else:
                            # No usable ATR (too little history) - fall back
                            # to sign-of-move only, same coarse read as
                            # before this rewrite.
                            result["SignalLabel"] = "BUY" if pct_move > 0 else "HOLD"
    except Exception:
        result = dict(empty)

    _signal_cache[cache_key] = (datetime.now(timezone.utc), dict(result))
    return dict(result)


def _confidence_from_sample(n: int) -> str:
    if n >= MIN_SAMPLE_FOR_PRIOR * 2:
        return "High"
    if n >= MIN_SAMPLE_FOR_PRIOR:
        return "Medium"
    return "Low"


def _event_type_prior_car(event_type: str) -> tuple[float | None, int]:
    """Median MoveSoFarPct (as of each event's most recent close at the time
    it was last read) across all past matched events sharing `event_type`,
    withheld below MIN_SAMPLE_FOR_PRIOR since a "median" of 1-2 points isn't
    a calibrated prior yet - see module-level MIN_SAMPLE_FOR_PRIOR comment.
    Recomputed from events.csv on each call rather than cached: the dataset
    is a handful of rows, so this is cheap, and it means a freshly-added
    historical event is reflected immediately without a separate rebuild
    step."""
    events = load_events()
    if events.empty:
        return None, 0
    matching = events[events["MatchedKeyword"].apply(lambda kw: _event_type(kw) == event_type)]
    if matching.empty:
        return None, 0

    moves = []
    for _, row in matching.iterrows():
        symbols = [s for s in str(row.get("MatchedSymbols", "")).split(",") if s]
        if not symbols:
            continue
        pct_move = _raw_move_pct(symbols[0], row.get("Date", ""))
        if pct_move is not None:
            moves.append(pct_move)

    n = len(moves)
    if n < MIN_SAMPLE_FOR_PRIOR:
        return None, n
    return float(pd.Series(moves).median()), n


def _raw_move_pct(symbol: str, event_date_str: str) -> float | None:
    """Entry-close-to-current-close % move only, no scoring - the one number
    _event_type_prior_car needs per historical row. Deliberately not routed
    through _price_signal to avoid recursion (that function calls
    _event_type_prior_car) and to skip work (ATR, confidence) that isn't
    needed here."""
    try:
        event_ts = pd.to_datetime(event_date_str, utc=True, errors="coerce")
        if pd.isna(event_ts):
            return None
        event_date = event_ts.date()
        to_date = date.today()
        if event_date > to_date:
            return None
        df = fetch_stock_history(symbol=symbol, from_date=event_date - timedelta(days=7), to_date=to_date, series="EQ")
        if df is None or df.empty:
            return None
        df = df.sort_values(by="DATE")
        on_or_before_event = df[df["DATE"].dt.date <= event_date]
        if on_or_before_event.empty:
            return None
        entry_close = float(on_or_before_event.iloc[-1]["CLOSE"])
        current_close = float(df.iloc[-1]["CLOSE"])
        if df.iloc[-1]["DATE"].date() == on_or_before_event.iloc[-1]["DATE"].date():
            return None
        return (current_close - entry_close) / entry_close * 100
    except Exception:
        return None


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
        event_type = _event_type(row.get("MatchedKeyword"))
        signal = _price_signal(symbols, row.get("Date", ""), event_type)
        # "Signal" stays a plain label string for the existing frontend table
        # (Phase 5 of the Event Watcher redesign updates the UI to consume
        # the full breakdown); "SignalDetail" carries the composite score,
        # ATR-normalized move, and event-type prior for once it does.
        row["Signal"] = signal["SignalLabel"]
        row["SignalDetail"] = signal
        row["EventType"] = event_type
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
