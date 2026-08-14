import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import pandas as pd

from constants import UNIVERSE_CACHE_PATH
from nse_utils import fetch_stock_history

CACHE_FILE = UNIVERSE_CACHE_PATH
CACHE_EXPIRY_DAYS = 1

def fetch_nifty_100():
    """Fetches the Nifty 100 constituents from NSE."""
    url = "https://archives.nseindia.com/content/indices/ind_nifty100list.csv"
    try:
        df = pd.read_csv(url)
        # Columns: Company Name, Industry, Symbol, Series, ISIN Code
        return df
    except Exception as e:
        print(f"Error fetching Nifty 100 list: {e}")
        return None

def fetch_symbol_return(symbol, from_date, to_date):
    """Fetches 6-month history for a single symbol and returns its % return."""
    df = fetch_stock_history(symbol=symbol, from_date=from_date, to_date=to_date, series="EQ")
    if df is None or df.empty or len(df) <= 10:
        return None

    df = df.sort_values(by="DATE")
    first_close = float(df["CLOSE"].iloc[0])
    last_close = float(df["CLOSE"].iloc[-1])
    return float((last_close - first_close) / first_close * 100)

def get_top_stocks_by_sector(limit_per_sector=50):
    """
    Fetches the Nifty 100 stocks, calculates their 6-month performance,
    and returns the top `limit_per_sector` stocks per sector.
    """
    # Check cache first
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cache_date = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    print("Loaded stock universe from cache.")
                    return cached_data['universe']
        except Exception as e:
            print(f"Error reading cache, fetching fresh data: {e}")

    print("Fetching Nifty 100 list from NSE...")
    nifty100_df = fetch_nifty_100()
    if nifty100_df is None or nifty100_df.empty:
        print("Failed to fetch Nifty 100, returning empty universe.")
        return {}

    tickers_list = nifty100_df['Symbol'].tolist()

    print(f"Fetching 6-month historical data for {len(tickers_list)} stocks...")
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=182)

    performance = []
    symbol_info = {
        row['Symbol']: {"Name": row['Company Name'], "Sector": row['Industry']}
        for _, row in nifty100_df.iterrows()
    }

    with ThreadPoolExecutor(max_workers=5) as executor:
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
            except Exception as e:
                # Some tickers might fail or have no data
                print(f"Failed to fetch {symbol}: {e}")

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

    # Save to cache
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "universe": top_stocks
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
