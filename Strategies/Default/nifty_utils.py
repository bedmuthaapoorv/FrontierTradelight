"""Builds a Nifty 50 benchmark curve to compare the backtest's portfolio
equity against.

Fetches the real Nifty 50 index level itself (via jugaad_data's index_df,
which wraps NSE's archives.nseindia.com index-history endpoint) and treats
it exactly like a single stock: normalize its close to 1.0 at the first
available date, scale by the portfolio's initial capital. This avoids the
survivorship bias and equal-weight distortion of building a proxy out of
today's Nifty 50 constituent list applied retroactively (real historical
constituents/weights aren't reconstructed here - we just use the published
index level directly).
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd
from jugaad_data.nse import index_df

from constants import NIFTY50_CACHE_PATH

CACHE_PATH = NIFTY50_CACHE_PATH
CACHE_EXPIRY_DAYS = 1
INDEX_SYMBOL = "NIFTY 50"


def build_nifty_50_benchmark(start_date, end_date, initial_capital):
    """Returns a DataFrame (Date, Equity) tracking what initial_capital
    invested in the real Nifty 50 index on start_date would be worth, or
    None if it couldn't be fetched."""
    cached = _read_cache(start_date, end_date, initial_capital)
    if cached is not None:
        return cached

    try:
        df = index_df(symbol=INDEX_SYMBOL, from_date=start_date, to_date=end_date)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    df = df.sort_values("HistoricalDate").set_index("HistoricalDate")
    df.index = pd.to_datetime(df.index).normalize()
    close = df["CLOSE"]
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
