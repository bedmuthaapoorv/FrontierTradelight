"""Builds a Nifty 50 benchmark curve to compare the backtest's portfolio
equity against.

Uses NIFTYBEES (the Nippon India Nifty 50 ETF) fetched through the same
NSE stock-history path as every stock in the backtest. It used to fetch
the raw index level via jugaad_data's index_df, but that wraps
niftyindices.com's history endpoint, which now redirects to a login page
(and NSE's own indicesHistory API is bot-blocked), so it always returned
None. NIFTYBEES retains the constituents' dividends, so it tracks closer
to the Nifty 50 total-return index than the price index (roughly +92% vs
+82% over 2021-2025) - a slightly tougher, fairer benchmark. It's treated
exactly like a single stock: close normalized to 1.0 at the first
available date, scaled by the portfolio's initial capital - the same
approach as US/sp500_utils.py with SPY.
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd

from constants import NIFTY50_CACHE_PATH
from nse_utils import adjust_for_splits_and_bonuses, fetch_stock_history

CACHE_PATH = NIFTY50_CACHE_PATH
CACHE_EXPIRY_DAYS = 1
BENCHMARK_SYMBOL = "NIFTYBEES"


def build_nifty_50_benchmark(start_date, end_date, initial_capital):
    """Returns a DataFrame (Date, Equity) tracking what initial_capital
    invested in the Nifty 50 (via NIFTYBEES) on start_date would be worth, or
    None if it couldn't be fetched."""
    cached = _read_cache(start_date, end_date, initial_capital)
    if cached is not None:
        return cached

    try:
        df = fetch_stock_history(BENCHMARK_SYMBOL, start_date, end_date)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    df = df.sort_values("DATE")
    # Same split/bonus back-adjustment the backtest applies to every stock
    # (NIFTYBEES itself split 1:10 in Dec 2019).
    ohlcv = df.rename(columns={
        "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close", "VOLUME": "volume",
    })[["open", "high", "low", "close", "volume"]]
    ohlcv.index = pd.to_datetime(df["DATE"]).dt.normalize()
    close = adjust_for_splits_and_bonuses(ohlcv)["close"]
    # jugaad_data's chunked fetches can overlap at boundaries, producing
    # duplicate dates - keep the last value.
    close = close[~close.index.duplicated(keep="last")].dropna()
    if close.empty:
        return None

    index_curve = (close / close.iloc[0]) * initial_capital

    result = pd.DataFrame({"Date": index_curve.index, "Equity": index_curve.values})
    _write_cache(result, start_date, end_date, initial_capital)
    return result


def _read_cache(start_date, end_date, initial_capital):
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        cache_date = datetime.fromisoformat(cached["timestamp"])
        if datetime.now() - cache_date >= timedelta(days=CACHE_EXPIRY_DAYS):
            return None
        key = f"{start_date.isoformat()}_{end_date.isoformat()}_{initial_capital}"
        if cached.get("key") != key:
            return None
        df = pd.read_json(cached["data"], orient="split")
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    except Exception:
        return None


def _write_cache(result, start_date, end_date, initial_capital):
    try:
        key = f"{start_date.isoformat()}_{end_date.isoformat()}_{initial_capital}"
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "key": key,
                "data": result.to_json(orient="split", date_format="iso"),
            }, f)
    except Exception:
        pass
