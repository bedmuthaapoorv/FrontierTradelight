"""Point-in-time lookups over the cached annual fundamentals
(data/fundamentals/annual.csv, built by fetch_fundamentals.py).

Every lookup takes a `day` and only sees fiscal years whose available_from
(year-end + the SEBI 60-day results deadline) is on or before that day, so a
backtest never uses results before they were published. Figures are
Screener.in's restated numbers, not as first reported; EPS is already
adjusted for bonuses and splits.

No network access here - run fetch_fundamentals.py to populate the cache.
"""

import bisect
import functools
import inspect
import math
import os
import re

import pandas as pd

from constants import FUNDAMENTALS_ANNUAL_PATH

FINANCIAL_SECTOR_RE = re.compile(r"financ|bank", re.I)


@functools.lru_cache(maxsize=1)
def load_annual():
    if not os.path.exists(FUNDAMENTALS_ANNUAL_PATH):
        raise RuntimeError("No fundamentals cache. Run `python fetch_fundamentals.py` first.")
    df = pd.read_csv(FUNDAMENTALS_ANNUAL_PATH)
    df["period_end"] = pd.to_datetime(df["period_end"]).dt.date
    df["available_from"] = pd.to_datetime(df["available_from"]).dt.date
    return df


@functools.lru_cache(maxsize=1)
def _by_symbol():
    return {sym: g.sort_values("period_end").reset_index(drop=True)
            for sym, g in load_annual().groupby("symbol")}


def fundamentals_as_of(symbol, day):
    """Annual rows for `symbol` that were public by `day`, oldest first."""
    rows = _by_symbol().get(symbol)
    if rows is None:
        return pd.DataFrame(columns=load_annual().columns)
    return rows[rows["available_from"] <= day].reset_index(drop=True)


def _valid(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def _cagr(start, end, years, abs_base=False):
    """Compound annual growth; with abs_base, a loss-making base year uses
    |start| (S&P GARP convention) so a turnaround still gets a number."""
    if not (_valid(start) and _valid(end)):
        return None
    base = abs(start) if abs_base else start
    if base <= 0 or end <= 0:
        return None
    return (end / base) ** (1 / years) - 1


def _year_back(rows, latest, years):
    target = latest["period_end"].replace(year=latest["period_end"].year - years)
    match = rows[rows["period_end"] == target]
    return match.iloc[0] if not match.empty else None


def metrics_as_of(symbol, day, close=None):
    """GARP inputs as known on `day`, or None if no fiscal year was public yet.
    Values that can't be computed come back as None. Pass `close` (the day's
    price, on the same bonus-adjusted basis as the price cache) for P/E and PEG."""
    rows = fundamentals_as_of(symbol, day)
    rows = rows[rows["months"] == 12]
    if rows.empty:
        return None
    return _with_price(_base_metrics(rows), close)


def _plain(x):
    """numpy scalars -> Python floats so the dict is JSON-safe and generated
    strategy code never has to deal with pandas/numpy types."""
    return float(x) if x is not None else None


def _base_metrics(rows):
    """Price-independent metrics from public full-year rows (oldest first)."""
    latest = rows.iloc[-1]

    positive_eps_years = 0
    for eps in reversed(rows["eps"].tolist()):
        if not (_valid(eps) and eps > 0):
            break
        positive_eps_years += 1

    base = _year_back(rows, latest, 3)
    eps_cagr = _cagr(base["eps"], latest["eps"], 3, abs_base=True) if base is not None else None
    sales_cagr = _cagr(base["sales"], latest["sales"], 3) if base is not None else None

    equity = latest["equity_capital"] + latest["reserves"]
    has_equity = _valid(equity) and equity > 0
    is_financial = bool(FINANCIAL_SECTOR_RE.search(str(latest["sector"])))
    roe = latest["net_profit"] / equity if has_equity and _valid(latest["net_profit"]) else None
    de = None
    if not is_financial and has_equity and _valid(latest["borrowings"]):
        de = latest["borrowings"] / equity

    return {
        "latest_fy": latest["period_end"].isoformat(),
        "available_from": latest["available_from"].isoformat(),
        "basis": str(latest["basis"]),
        "eps": _plain(latest["eps"]) if _valid(latest["eps"]) else None,
        "positive_eps_years": positive_eps_years,
        "eps_cagr_3y": _plain(eps_cagr),
        "sales_cagr_3y": _plain(sales_cagr),
        "roe": _plain(roe),
        "de": _plain(de),
        "is_financial": is_financial,
    }


def _with_price(base, close):
    pe = peg = None
    if close is not None and _valid(close) and base["eps"] is not None and base["eps"] > 0:
        pe = float(close) / base["eps"]
        if base["eps_cagr_3y"] is not None and base["eps_cagr_3y"] > 0:
            peg = pe / (base["eps_cagr_3y"] * 100)
    return {**base, "pe": pe, "peg": peg}


_base_cache = {}


def snapshot(closes, day):
    """{symbol: metrics} for every symbol in `closes` ({symbol: that day's
    close}) that had a public fiscal year by `day`; symbols without data are
    left out. The price-independent part is cached per (symbol, latest public
    year), so in a day-by-day backtest it is only recomputed when a new
    year's results become available."""
    if load_annual_or_none() is None:
        return {}
    full_years = _full_years_by_symbol()
    out = {}
    for symbol, close in closes.items():
        entry = full_years.get(symbol)
        if entry is None:
            continue
        rows, available = entry
        n_public = bisect.bisect_right(available, day)
        if n_public == 0:
            continue
        key = (symbol, n_public)
        base = _base_cache.get(key)
        if base is None:
            base = _base_cache[key] = _base_metrics(rows.iloc[:n_public])
        out[symbol] = _with_price(base, close)
    return out


@functools.lru_cache(maxsize=1)
def _full_years_by_symbol():
    """symbol -> (full-year rows sorted by availability, list of their
    available_from dates) for bisect lookups."""
    out = {}
    for symbol, rows in _by_symbol().items():
        full = rows[rows["months"] == 12].sort_values("available_from").reset_index(drop=True)
        if not full.empty:
            out[symbol] = (full, full["available_from"].tolist())
    return out


@functools.lru_cache(maxsize=None)
def _accepts_fundamentals(fn):
    try:
        return "fundamentals" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def call_evaluate_stock(fn, symbol, df, universe, sector_ranks, market_breadth, fundamentals):
    """Calls a compiled evaluate_stock, passing `fundamentals` only if that
    strategy was compiled with the parameter - strategies compiled before it
    existed keep their 5-argument signature and keep working unchanged."""
    if _accepts_fundamentals(fn):
        return fn(symbol, df, universe, sector_ranks, market_breadth, fundamentals=fundamentals)
    return fn(symbol, df, universe, sector_ranks, market_breadth)


def load_annual_or_none():
    """Like load_annual(), but None when the cache hasn't been built yet, so
    callers can run strategies without fundamentals instead of crashing."""
    try:
        return load_annual()
    except RuntimeError:
        return None
