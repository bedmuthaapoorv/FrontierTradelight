import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="jugaad_data")

import pandas as pd
import pandas_ta as ta
from jugaad_data.nse import stock_df


def fetch_stock_history(symbol, from_date, to_date, series="EQ", retries=3, backoff_seconds=2):
    """Fetch NSE history for a symbol, retrying transient failures (rate
    limiting / bot-detection blocks show up as empty or non-JSON responses)."""
    last_error = None
    for attempt in range(retries):
        try:
            return stock_df(symbol=symbol, from_date=from_date, to_date=to_date, series=series)
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(backoff_seconds * (attempt + 1))
    raise last_error


def calculate_sector_strength(data, universe):
    """Rank sectors by average 30-day return and map each symbol to its sector's rank.

    `data` maps symbol -> a DataFrame with a lowercase 'close' column, sorted
    ascending by date. Only uses data already present in each DataFrame, so
    passing a date-truncated slice (as the backtester does) keeps this
    look-ahead free.
    """
    sector_returns = {}

    for symbol, info in universe.items():
        df = data.get(symbol)
        if df is None or len(df) < 30:
            continue

        recent = df["close"].iloc[-30:]
        pct_return = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100

        sector = info["Sector"]
        sector_returns.setdefault(sector, []).append(pct_return)

    sector_avg_return = {
        sector: sum(returns) / len(returns)
        for sector, returns in sector_returns.items()
    }

    ranked_sectors = sorted(sector_avg_return, key=sector_avg_return.get, reverse=True)
    sector_rank = {sector: rank + 1 for rank, sector in enumerate(ranked_sectors)}

    return {
        symbol: sector_rank.get(info["Sector"], 99)
        for symbol, info in universe.items()
    }


def calculate_atr_stats(df, atr_period=14, avg_period=60):
    """Current ATR(atr_period) and its trailing avg_period-day rolling
    average, both computed from `df` only up to its last available row (so
    passing a date-truncated slice, as the backtester does, keeps this
    look-ahead free). This is the "vol-ratio" input for risk-based position
    sizing: current ATR relative to its own recent average tells the sizer
    whether a stock is unusually volatile right now versus its own normal
    range, independent of price level or sector.

    Returns {"ATR": nan, "ATR_Avg60": nan} if there isn't enough history for
    either the ATR itself or the rolling average of it.
    """
    if len(df) < atr_period + avg_period:
        return {"ATR": float("nan"), "ATR_Avg60": float("nan")}

    atr_series = ta.atr(df["high"], df["low"], df["close"], length=atr_period)
    current_atr = atr_series.iloc[-1]
    atr_avg = atr_series.iloc[-avg_period:].mean()

    return {"ATR": current_atr, "ATR_Avg60": atr_avg}


def calculate_market_breadth(data, ma_period=50):
    """Percentage (0-100) of stocks in `data` currently trading above their
    own MA(ma_period). A stand-in for a Nifty benchmark regime filter, built
    entirely from data the pipeline already fetches (no external index).

    `data` maps symbol -> a DataFrame with a lowercase 'close' column, sorted
    ascending by date. Only uses data already present in each DataFrame, so
    passing a date-truncated slice (as the backtester does) keeps this
    look-ahead free. Returns 50.0 (neutral) if nothing is computable.
    """
    above = 0
    total = 0

    for df in data.values():
        if df is None or len(df) < ma_period:
            continue

        ma = df["close"].rolling(ma_period).mean().iloc[-1]
        if pd.isna(ma):
            continue

        total += 1
        if df["close"].iloc[-1] > ma:
            above += 1

    if total == 0:
        return 50.0

    return (above / total) * 100
