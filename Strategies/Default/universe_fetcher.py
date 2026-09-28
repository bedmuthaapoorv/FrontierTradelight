import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import pandas as pd

from constants import UNIVERSE_CACHE_PATH
from nse_utils import fetch_stock_history

CACHE_FILE = UNIVERSE_CACHE_PATH
CACHE_EXPIRY_DAYS = 1

# jugaad-data hits NSE's raw historical API directly, which throttles/
# bot-detects under sustained concurrent load - staggering requests (same
# pattern stock_screener.py uses for its own daily fetch) cuts down on
# correlated failures where a burst of simultaneous requests gets an entire
# window rate-limited at once, so even per-request retries inside
# fetch_stock_history keep failing until the window passes.
FETCH_WORKERS = 5
STAGGER_SECONDS = (0.1, 0.5)

def fetch_nifty_500():
    """Fetches the Nifty 500 constituents from NSE.

    Nifty 500, not Nifty 100 - the Nifty 100 is large-caps only, which made
    MarketBreadth (calculate_market_breadth, computed over this same
    universe) measure "% of large-caps above their own 50-day MA" rather
    than a broad-market breadth figure, and diverged sharply from
    broader-market breadth readings during this project's own testing.
    Nifty 500 covers large + mid + small caps, matching what "market
    breadth" normally means."""
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        # Columns: Company Name, Industry, Symbol, Series, ISIN Code
        return df
    except Exception as e:
        print(f"Error fetching Nifty 500 list: {e}")
        return None

def fetch_symbol_return(symbol, from_date, to_date, retries=3, backoff_seconds=3):
    """Fetches 6-month history for a single symbol and returns its % return.

    Staggers its own start (see STAGGER_SECONDS) and retries with its own
    backoff on top of fetch_stock_history's internal retries - a burst of
    ~500 concurrent requests can get an entire time window rate-limited at
    once, so a failure here often means "try again after a longer pause,"
    not "this symbol is broken." Returns None only after every attempt is
    exhausted, same as before - callers already treat None as "skip this
    symbol," so this doesn't change that contract, just makes it less
    likely to fire spuriously."""
    time.sleep(random.uniform(*STAGGER_SECONDS))
    last_error = None
    for attempt in range(retries):
        try:
            df = fetch_stock_history(symbol=symbol, from_date=from_date, to_date=to_date, series="EQ")
            if df is None or df.empty or len(df) <= 10:
                return None
            df = df.sort_values(by="DATE")
            first_close = float(df["CLOSE"].iloc[0])
            last_close = float(df["CLOSE"].iloc[-1])
            return float((last_close - first_close) / first_close * 100)
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(backoff_seconds * (attempt + 1))
    print(f"Giving up on {symbol} after {retries} attempts: {last_error}")
    return None

def get_top_stocks_by_sector(limit_per_sector=50):
    """
    Fetches the Nifty 500 stocks, calculates their 6-month performance,
    and returns the top `limit_per_sector` stocks per sector.
    """
    # Check cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cache_date = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    fetched = cached_data.get("fetched_count")
                    requested = cached_data.get("requested_count")
                    if fetched is not None and requested:
                        print(f"Loaded stock universe from cache ({fetched}/{requested} Nifty 500 stocks fetched).")
                    else:
                        print("Loaded stock universe from cache.")
                    return cached_data['universe']
        except Exception as e:
            print(f"Error reading cache, fetching fresh data: {e}")

    print("Fetching Nifty 500 list from NSE...")
    nifty500_df = fetch_nifty_500()
    if nifty500_df is None or nifty500_df.empty:
        print("Failed to fetch Nifty 500, returning empty universe.")
        return {}

    tickers_list = nifty500_df['Symbol'].tolist()

    print(f"Fetching 6-month historical data for {len(tickers_list)} stocks...")
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=182)

    performance = []
    symbol_info = {
        row['Symbol']: {"Name": row['Company Name'], "Sector": row['Industry']}
        for _, row in nifty500_df.iterrows()
    }

    failed_symbols = []

    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as executor:
        future_to_symbol = {
            executor.submit(fetch_symbol_return, symbol, from_date, to_date): symbol
            for symbol in tickers_list
        }
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                pct_return = future.result()
                if pct_return is not None:
                    performance.append({
                        "Ticker": symbol,
                        "Name": symbol_info[symbol]["Name"],
                        "Sector": symbol_info[symbol]["Sector"],
                        "Return": pct_return
                    })
                else:
                    failed_symbols.append(symbol)
            except Exception as e:
                # Some tickers might fail or have no data
                print(f"Failed to fetch {symbol}: {e}")
                failed_symbols.append(symbol)

    # A first concurrent pass can lose a lot of symbols at once if NSE
    # throttles the whole burst together (fetch_symbol_return's own
    # retries/backoff happen too close together in time to help with a
    # window-wide block). Retry failures sequentially, one at a time with a
    # real pause between each, well after the burst that likely caused the
    # block has passed - slower, but recovers most of them in practice.
    if failed_symbols:
        print(f"Retrying {len(failed_symbols)} symbol(s) sequentially after the concurrent pass...")
        still_failed = []
        for symbol in failed_symbols:
            time.sleep(1.0)
            pct_return = fetch_symbol_return(symbol, from_date, to_date, retries=2, backoff_seconds=5)
            if pct_return is not None:
                performance.append({
                    "Ticker": symbol,
                    "Name": symbol_info[symbol]["Name"],
                    "Sector": symbol_info[symbol]["Sector"],
                    "Return": pct_return
                })
            else:
                still_failed.append(symbol)
        failed_symbols = still_failed

    success_count = len(performance)
    total_count = len(tickers_list)
    success_rate = success_count / total_count * 100 if total_count else 0
    print(f"Fetched {success_count}/{total_count} Nifty 500 stocks successfully ({success_rate:.0f}%).")
    if success_rate < 70:
        print(
            f"WARNING: only {success_rate:.0f}% of the Nifty 500 universe was fetched - "
            "sector strength and market breadth are being computed over a smaller, "
            "potentially unrepresentative sample. This usually means NSE throttled "
            "the fetch; re-running later (or with fewer concurrent workers) may help. "
            f"{len(failed_symbols)} symbol(s) still failing: {failed_symbols[:20]}"
            + (" ..." if len(failed_symbols) > 20 else "")
        )

    perf_df = pd.DataFrame(performance)

    if perf_df.empty:
        print("Failed to calculate performance, returning empty universe.")
        return {}

    # Group by Sector and get top N performers
    print("Ranking stocks by sector...")
    top_stocks = {}

    for sector, group in perf_df.groupby('Sector'):
        # Sort by return descending
        top_group = group.sort_values(by='Return', ascending=False).head(limit_per_sector)
        for _, row in top_group.iterrows():
            top_stocks[row['Ticker']] = {
                "Name": row['Name'],
                "Sector": row['Sector']
            }

    # Save to cache, including the fetch success rate so a small/stale-looking
    # universe can be diagnosed later without re-running this whole fetch.
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "universe": top_stocks,
                "fetched_count": success_count,
                "requested_count": total_count,
            }, f, indent=4)
        print("Saved fresh stock universe to cache.")
    except Exception as e:
        print(f"Warning: Failed to save cache: {e}")

    return top_stocks

if __name__ == "__main__":
    # Test script execution
    universe = get_top_stocks_by_sector(limit_per_sector=5)
    print(f"Total stocks in dynamic universe: {len(universe)}")
    print("Sample stocks:")
    for i, (k, v) in enumerate(universe.items()):
        if i < 10:
            print(f"{k}: {v}")
