import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="jugaad_data")

import pandas as pd
from jugaad_data.nse import stock_df


def fetch_stock_history(symbol, from_date, to_date, series="EQ", retries=3, backoff_seconds=2):
    """Fetch NSE history for a symbol, retrying transient failures (rate
    limiting / bot-detection blocks show up as empty or non-JSON responses).

    jugaad_data's `series` argument is not reliable as a filter: for some
    symbols (e.g. NTPC, which also has several bond/NCD series like N1, N6,
    NA sharing the same base symbol) it silently returns EVERY series for
    that symbol, not just the one requested - multiple unrelated
    instruments' prices interleaved under the same DATE. Re-filtering by
    the returned SERIES column ourselves is the only reliable way to get
    just the equity series actually asked for."""
    last_error = None
    for attempt in range(retries):
        try:
            df = stock_df(symbol=symbol, from_date=from_date, to_date=to_date, series=series)
            if df is not None and not df.empty and "SERIES" in df.columns:
                df = df[df["SERIES"] == series]
            if df is not None and not df.empty and "DATE" in df.columns:
                df = df.copy()
                # jugaad_data's stock_df stamps every row's DATE at
                # 18:30:00 - that's UTC, and 18:30 UTC + 5:30 (India has no
                # DST, so this offset is exact) = 24:00 = IST midnight of
                # the FOLLOWING calendar day. Taking .dt.date() on the raw
                # value (as every caller does) silently reports every
                # close one day behind its real IST trading date. Verified
                # two ways: cross-checked against independently-confirmed
                # Meesho closes (21 Sep 2026 = Rs.219.15, 22 Sep 2026 =
                # Rs.240.19, which only line up against this data if you
                # add a day to the naive date), and against NSE's own
                # holiday list, which confirms 14 Sep 2026 (Ganesh
                # Chaturthi) was a market holiday - a gap in the naive
                # dates that only makes sense with this +1-day correction.
                # Fixed once here, centrally, rather than at every call
                # site (event_watcher_utils.py's signal/duration/ATR
                # calculations all read this DATE column and inherit the
                # fix automatically).
                df["DATE"] = df["DATE"] + pd.Timedelta(days=1)
            return df
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
