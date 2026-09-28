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
    EVENT_WATCHER_STATS_PATH,
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

# Same MaxHold convention as generated_exit_strategy.py's resolve_exit(): a
# move that's still open after this many trading sessions is treated as
# "resolved" anyway for calibration purposes, rather than waiting forever
# for a reversion that may never come.
MAX_HOLD_DAYS = 90

# How much of the peak GAIN (peak_close - entry_close) has to be given back
# before a move counts as "resolved" (played out) rather than still-live -
# see _duration_walk. 50% is a round, conservative middle point; not backed
# by a specific study (the research behind this redesign found no published
# duration data for contract/PSU-announcement events specifically to
# calibrate this against - see the "Event announcement signal and swing
# duration" report), deliberately easy to retune here as real history
# accumulates.
RESOLUTION_REVERSION_PCT = 50.0

SIGNAL_CACHE_TTL = timedelta(hours=6)

# In-memory only - a stale cached signal just means the tab shows a slightly
# outdated read until it expires or the process restarts, never wrong data
# written anywhere.
_signal_cache: dict[str, tuple[datetime, dict]] = {}
_duration_cache: dict[str, tuple[datetime, dict]] = {}


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

                        type_stats = get_event_type_stats().get("event_types", {}).get(event_type, {})
                        result["PriorEventTypeCAR"] = type_stats.get("median_car_pct")
                        result["PriorSampleSize"] = type_stats.get("n", 0)
                        result["SignalConfidence"] = _confidence_from_sample(type_stats.get("n", 0))

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


def _duration_walk(symbol: str, event_date_str: str) -> dict | None:
    """Day-by-day walk from the event's entry close through to today (capped
    at MAX_HOLD_DAYS trading sessions), tracking the running peak close and
    how far price has since given back from it. Same days_held/highest_close
    shape as generated_exit_strategy.py's resolve_exit()/describe_state(),
    simplified to describe a move rather than manage a stop - this is the
    one function both the live per-row duration estimate and the historical
    calibration store are built on, so a completed historical event and an
    still-open one go through identical logic.

    Returns None if there isn't enough OHLCV data to say anything; otherwise:
      DaysHeld              - trading sessions elapsed since entry (0 = no
                               session has closed since the event yet)
      EntryClose / CurrentClose / PeakClose (highest close since entry)
      PeakReturnPct          - PeakClose vs EntryClose, %
      DaysToPeak             - sessions from entry to PeakClose; None if the
                               most recent session IS the peak (the move may
                               still be climbing - can't call a peak final
                               on the day it happens)
      CurrentReturnPct       - CurrentClose vs EntryClose, %
      ReversionFromPeakPct   - % of the peak GAIN given back by CurrentClose
                               (0 if still at/above peak); computed causally
                               day-by-day against the running peak-to-date,
                               not the eventual all-time peak, so it matches
                               what a live position would actually observe
      DaysTo50PctReversion   - first day index at which the running
                               reversion-from-peak-to-date first reached
                               RESOLUTION_REVERSION_PCT; None if it never has
      Resolved               - True once DaysTo50PctReversion is set or
                               DaysHeld >= MAX_HOLD_DAYS - i.e. this instance
                               is a completed sample usable for calibration,
                               not still an open/live move
    """
    try:
        event_ts = pd.to_datetime(event_date_str, utc=True, errors="coerce")
        if pd.isna(event_ts):
            return None
        event_date = event_ts.date()
        to_date = date.today()
        if event_date > to_date:
            return None
        # Widen a week before the event so a non-trading event date (e.g. a
        # Saturday PIB release) still lands on the last real close at/before
        # it - same reasoning as _price_signal's fetch below.
        df = fetch_stock_history(symbol=symbol, from_date=event_date - timedelta(days=7), to_date=to_date, series="EQ")
        if df is None or df.empty:
            return None
        df = df.sort_values(by="DATE")
        on_or_before = df[df["DATE"].dt.date <= event_date]
        if on_or_before.empty:
            return None
        entry_close = float(on_or_before.iloc[-1]["CLOSE"])
        entry_row_date = on_or_before.iloc[-1]["DATE"].date()
        after = df[df["DATE"].dt.date > entry_row_date].iloc[:MAX_HOLD_DAYS]

        days_held = len(after)
        if days_held == 0:
            return {
                "DaysHeld": 0,
                "EntryClose": entry_close,
                "CurrentClose": entry_close,
                "PeakClose": entry_close,
                "PeakReturnPct": 0.0,
                "DaysToPeak": None,
                "CurrentReturnPct": 0.0,
                "ReversionFromPeakPct": 0.0,
                "DaysTo50PctReversion": None,
                "Resolved": False,
            }

        peak_close = entry_close
        days_to_peak = 0
        days_to_50pct_reversion = None
        for i, (_, row) in enumerate(after.iterrows(), start=1):
            close = float(row["CLOSE"])
            if close > peak_close:
                peak_close = close
                days_to_peak = i
            peak_gain_so_far = peak_close - entry_close
            if days_to_50pct_reversion is None and peak_gain_so_far > 0:
                reversion_so_far = (peak_close - close) / peak_gain_so_far * 100
                if reversion_so_far >= RESOLUTION_REVERSION_PCT:
                    days_to_50pct_reversion = i

        current_close = float(after.iloc[-1]["CLOSE"])
        peak_gain = peak_close - entry_close
        peak_return_pct = (peak_gain / entry_close * 100) if entry_close else 0.0
        current_return_pct = ((current_close - entry_close) / entry_close * 100) if entry_close else 0.0
        reversion_from_peak_pct = (
            max(0.0, (peak_close - current_close) / peak_gain * 100) if peak_gain > 0 else 0.0
        )
        still_rising = days_to_peak == days_held
        resolved = days_to_50pct_reversion is not None or days_held >= MAX_HOLD_DAYS

        return {
            "DaysHeld": days_held,
            "EntryClose": entry_close,
            "CurrentClose": current_close,
            "PeakClose": peak_close,
            "PeakReturnPct": peak_return_pct,
            "DaysToPeak": None if still_rising else days_to_peak,
            "CurrentReturnPct": current_return_pct,
            "ReversionFromPeakPct": reversion_from_peak_pct,
            "DaysTo50PctReversion": days_to_50pct_reversion,
            "Resolved": resolved,
        }
    except Exception:
        return None


def recompute_event_type_stats() -> dict:
    """Rebuilds the event_type_stats.json calibration store from every row
    in events.csv, bucketed by event_type. This is what _price_signal's
    PriorEventTypeCAR and _swing_duration_estimate's EstDaysToPeak /
    EstDaysTo50PctReversion actually read - computed here, once, rather than
    re-walking every historical row's OHLCV (one fetch_stock_history call
    each) on every single get_state() request as the row count grows.

    median_car_pct / car_iqr_*_pct / median_days_to_peak /
    median_days_to_50pct_reversion are all None below MIN_SAMPLE_FOR_PRIOR
    (car stats gated on total matched instances `n`; duration stats gated on
    `resolved_n`, since an in-progress move can't say how long a finished
    move like this typically takes) - n/resolved_n themselves are always
    reported so the UI can show e.g. "n=1" instead of just hiding the row."""
    events = load_events()
    event_types: dict[str, dict] = {}

    if not events.empty:
        buckets: dict[str, list[dict]] = {}
        for _, row in events.iterrows():
            event_type = _event_type(row.get("MatchedKeyword"))
            buckets.setdefault(event_type, []).append(row.to_dict())

        for event_type, rows in buckets.items():
            car_samples: list[float] = []
            days_to_peak_samples: list[int] = []
            days_to_50pct_samples: list[int] = []
            resolved_n = 0
            for row in rows:
                symbols = [s for s in str(row.get("MatchedSymbols", "")).split(",") if s]
                if not symbols:
                    continue
                walk = _duration_walk(symbols[0], row.get("Date", ""))
                if walk is None:
                    continue
                if walk["DaysHeld"] > 0:
                    car_samples.append(walk["CurrentReturnPct"])
                if walk["Resolved"]:
                    resolved_n += 1
                    if walk["DaysToPeak"] is not None:
                        days_to_peak_samples.append(walk["DaysToPeak"])
                    if walk["DaysTo50PctReversion"] is not None:
                        days_to_50pct_samples.append(walk["DaysTo50PctReversion"])

            n = len(rows)
            car_ok = n >= MIN_SAMPLE_FOR_PRIOR and car_samples
            duration_ok = resolved_n >= MIN_SAMPLE_FOR_PRIOR
            car_series = pd.Series(car_samples) if car_ok else None
            event_types[event_type] = {
                "n": n,
                "resolved_n": resolved_n,
                "median_car_pct": float(car_series.median()) if car_series is not None else None,
                "car_iqr_low_pct": float(car_series.quantile(0.25)) if car_series is not None else None,
                "car_iqr_high_pct": float(car_series.quantile(0.75)) if car_series is not None else None,
                "median_days_to_peak": (
                    int(pd.Series(days_to_peak_samples).median()) if duration_ok and days_to_peak_samples else None
                ),
                "median_days_to_50pct_reversion": (
                    int(pd.Series(days_to_50pct_samples).median()) if duration_ok and days_to_50pct_samples else None
                ),
            }

    stats = {
        "event_types": event_types,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "min_sample_for_prior": MIN_SAMPLE_FOR_PRIOR,
    }
    with open(EVENT_WATCHER_STATS_PATH, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    return stats


def get_event_type_stats() -> dict:
    """Reads the calibration store, rebuilding it first if it's missing
    (fresh install) or stale (events.csv has a newer mtime than the store -
    e.g. refresh()/fetch_historical() just appended rows, or the store was
    deleted by hand). Cheap to check on every call; the rebuild itself is
    the only non-trivial cost, and only runs when something actually
    changed."""
    needs_rebuild = not os.path.exists(EVENT_WATCHER_STATS_PATH)
    if not needs_rebuild and os.path.exists(EVENT_WATCHER_EVENTS_PATH):
        needs_rebuild = os.path.getmtime(EVENT_WATCHER_EVENTS_PATH) > os.path.getmtime(EVENT_WATCHER_STATS_PATH)
    if needs_rebuild:
        return recompute_event_type_stats()
    with open(EVENT_WATCHER_STATS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _swing_duration_estimate(symbols: list[str], event_date_str: str, event_type: str) -> dict:
    """Per-row duration output: the live day-by-day walk for this specific
    instance (DaysHeld/PeakReturnPct/DaysToPeak/ReversionFromPeakPct) merged
    with the event_type's historical duration prior from the calibration
    store (EstDaysToPeak/EstDaysTo50PctReversion), once enough *resolved*
    instances of this event_type exist to say anything about that - see
    recompute_event_type_stats(). This is the answer to "how long does a
    swing like this tend to last", the piece the pre-redesign Event Watcher
    had no way to report at all."""
    empty: dict = {
        "DaysHeld": None,
        "PeakReturnPct": None,
        "DaysToPeak": None,
        "CurrentReturnPct": None,
        "ReversionFromPeakPct": None,
        "EstDaysToPeak": None,
        "EstDaysTo50PctReversion": None,
        "DurationSampleSize": 0,
        "DurationConfidence": "Low",
    }
    if not symbols:
        return dict(empty)
    symbol = symbols[0]
    cache_key = f"{symbol}:{event_date_str}:{event_type}"
    cached = _duration_cache.get(cache_key)
    if cached and datetime.now(timezone.utc) - cached[0] < SIGNAL_CACHE_TTL:
        return dict(cached[1])

    result = dict(empty)
    walk = _duration_walk(symbol, event_date_str)
    if walk is not None:
        result["DaysHeld"] = walk["DaysHeld"]
        result["PeakReturnPct"] = walk["PeakReturnPct"]
        result["DaysToPeak"] = walk["DaysToPeak"]
        result["CurrentReturnPct"] = walk["CurrentReturnPct"]
        result["ReversionFromPeakPct"] = walk["ReversionFromPeakPct"]

    type_stats = get_event_type_stats().get("event_types", {}).get(event_type, {})
    result["EstDaysToPeak"] = type_stats.get("median_days_to_peak")
    result["EstDaysTo50PctReversion"] = type_stats.get("median_days_to_50pct_reversion")
    result["DurationSampleSize"] = type_stats.get("resolved_n", 0)
    result["DurationConfidence"] = _confidence_from_sample(type_stats.get("resolved_n", 0))

    _duration_cache[cache_key] = (datetime.now(timezone.utc), dict(result))
    return dict(result)


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
        duration = _swing_duration_estimate(symbols, row.get("Date", ""), event_type)
        # "Signal"/"Duration" stay simple for the pre-redesign frontend
        # table (BUY/HOLD/SELL string, days-held number); "SignalDetail"/
        # "DurationDetail" carry the full composite-score/duration
        # breakdown for the updated UI to consume.
        row["Signal"] = signal["SignalLabel"]
        row["SignalDetail"] = signal
        row["EventType"] = event_type
        row["Duration"] = duration["DaysHeld"]
        row["DurationDetail"] = duration
    return {
        "last_checked": meta.get("last_checked"),
        "last_error": meta.get("last_error"),
        "watchlist": {symbol: names[0] for symbol, names in WATCHLIST.items()},
        "event_type_stats": get_event_type_stats().get("event_types", {}),
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
            recompute_event_type_stats()

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
            recompute_event_type_stats()

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
    if removed:
        recompute_event_type_stats()
    return {"status": "ok", "removed": removed}
