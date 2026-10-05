"""Builds an S&P 500 benchmark curve to compare the backtest's portfolio
equity against - the US counterpart of Default/nifty_utils.py.

Uses SPY (the S&P 500 ETF) fetched through the same Alpaca bars endpoint
as every stock, since Alpaca serves equities/ETFs rather than raw index
levels. Like the Nifty 50 index level the India side uses, SPY's price
excludes reinvested dividends, so both benchmarks are price-return. It's
treated exactly like a single stock: close normalized to 1.0 at the first
available date, scaled by the portfolio's initial capital.
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd

from constants import SP500_CACHE_PATH
from market_data import fetch_stock_history

CACHE_PATH = SP500_CACHE_PATH
CACHE_EXPIRY_DAYS = 1
BENCHMARK_SYMBOL = "SPY"


def build_sp_500_benchmark(start_date, end_date, initial_capital):
    """Returns a DataFrame (Date, Equity) tracking what initial_capital
    invested in SPY on start_date would be worth, or None if it couldn't
    be fetched."""
    cached = _read_cache(start_date, end_date, initial_capital)
    if cached is not None:
        return cached

    try:
        df = fetch_stock_history(BENCHMARK_SYMBOL, start_date, end_date)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    close = df.set_index("DATE")["CLOSE"].dropna()
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
