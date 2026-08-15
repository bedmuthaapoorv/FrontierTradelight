"""Builds a Nifty 50 benchmark curve to compare the backtest's portfolio
equity against.

NSE's actual index-history endpoints (both the archives.nseindia.com and
niftyindices.com variants jugaad_data wraps) return bot-blocked/empty
responses from this network - same class of block as the live-quote API
(see sell_screener.py's docstring). Instead of the real index level, this
builds an equal-weighted proxy from the Nifty 50 constituents' own daily
closes (fetched via the same fetch_stock_history() used everywhere else in
this project), normalized to start at the portfolio's initial capital so
the two curves are directly comparable on the same chart.
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd

from constants import NIFTY50_CACHE_PATH
from nse_utils import fetch_stock_history

CACHE_PATH = NIFTY50_CACHE_PATH
CACHE_EXPIRY_DAYS = 1
NIFTY_50_LIST_URL = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"


def _fetch_nifty_50_symbols():
    try:
        return pd.read_csv(NIFTY_50_LIST_URL)["Symbol"].tolist()
    except Exception:
        return None


def build_nifty_50_benchmark(start_date, end_date, initial_capital):
    """Returns a DataFrame (Date, Equity) tracking what initial_capital
    would be worth if spread equally across the Nifty 50 constituents on
    start_date, or None if it couldn't be built (list/data unavailable)."""
    cached = _read_cache(start_date, end_date, initial_capital)
    if cached is not None:
        return cached

    symbols = _fetch_nifty_50_symbols()
    if not symbols:
        return None

    closes = {}
    for symbol in symbols:
        try:
            df = fetch_stock_history(symbol, from_date=start_date, to_date=end_date, series="EQ")
            if df is None or df.empty:
                continue
            df = df.sort_values("DATE").set_index("DATE")
            df.index = pd.to_datetime(df.index).normalize()
            # jugaad_data's chunked monthly fetches can overlap at month
            # boundaries, producing duplicate dates - keep the last value.
            series = df["CLOSE"]
            closes[symbol] = series[~series.index.duplicated(keep="last")]
        except Exception:
            continue

    if not closes:
        return None

    price_df = pd.DataFrame(closes).sort_index().ffill().dropna(how="all")
    if price_df.empty:
        return None

    # Equal-weight: normalize each stock to 1.0 at its first available
    # price, average across stocks each day, scale by initial_capital.
    normalized = price_df / price_df.iloc[0]
    index_curve = normalized.mean(axis=1) * initial_capital

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
