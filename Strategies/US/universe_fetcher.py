import json
import os
from datetime import datetime, timedelta

import pandas as pd

from constants import UNIVERSE_CACHE_PATH
from market_data import fetch_bars_batch

CACHE_FILE = UNIVERSE_CACHE_PATH
CACHE_EXPIRY_DAYS = 1

# Maintained mirror of Wikipedia's S&P 500 constituents table, as plain CSV
# (no HTML scraping / lxml needed). Columns include Symbol, Security, and
# GICS Sector - the 11 GICS sectors play the role the Nifty 500 list's
# Industry column plays in the India pipeline.
SP500_CSV_URL = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"


def fetch_sp_500():
    """Fetches the S&P 500 constituents (Symbol, Security, GICS Sector, ...).

    Share-class tickers come dotted (BRK.B, BF.B), which is also the form
    Alpaca expects, so symbols are used as-is."""
    try:
        return pd.read_csv(SP500_CSV_URL)
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        return None


def _six_month_returns(symbols, from_date, to_date):
    """{symbol: % return over the window}, from one batched Alpaca fetch."""
    histories = fetch_bars_batch(
        symbols, from_date, to_date,
        progress=lambda done, total: print(f"  fetched {done}/{total} symbols"),
    )
    returns = {}
    for symbol, df in histories.items():
        if len(df) <= 10:
            continue
        first_close = float(df["CLOSE"].iloc[0])
        last_close = float(df["CLOSE"].iloc[-1])
        returns[symbol] = (last_close - first_close) / first_close * 100
    return returns


def get_top_stocks_by_sector(limit_per_sector=50):
    """
    Fetches the S&P 500 stocks, calculates their 6-month performance,
    and returns the top `limit_per_sector` stocks per GICS sector.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                cache_date = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cache_date < timedelta(days=CACHE_EXPIRY_DAYS):
                    fetched = cached_data.get("fetched_count")
                    requested = cached_data.get("requested_count")
                    if fetched is not None and requested:
                        print(f"Loaded stock universe from cache ({fetched}/{requested} S&P 500 stocks fetched).")
                    else:
                        print("Loaded stock universe from cache.")
                    return cached_data['universe']
        except Exception as e:
            print(f"Error reading cache, fetching fresh data: {e}")

    print("Fetching S&P 500 list...")
    sp500_df = fetch_sp_500()
    if sp500_df is None or sp500_df.empty:
        print("Failed to fetch S&P 500, returning empty universe.")
        return {}

    symbol_info = {
        row['Symbol']: {"Name": row['Security'], "Sector": row['GICS Sector']}
        for _, row in sp500_df.iterrows()
    }
    tickers_list = list(symbol_info)

    print(f"Fetching 6-month historical data for {len(tickers_list)} stocks...")
    to_date = datetime.now().date()
    from_date = to_date - timedelta(days=182)
    returns = _six_month_returns(tickers_list, from_date, to_date)

    performance = [
        {"Ticker": symbol, "Name": symbol_info[symbol]["Name"],
         "Sector": symbol_info[symbol]["Sector"], "Return": pct_return}
        for symbol, pct_return in returns.items()
        if symbol in symbol_info
    ]
    failed_symbols = [s for s in tickers_list if s not in returns]

    success_count = len(performance)
    total_count = len(tickers_list)
    success_rate = success_count / total_count * 100 if total_count else 0
    print(f"Fetched {success_count}/{total_count} S&P 500 stocks successfully ({success_rate:.0f}%).")
    if failed_symbols:
        print(f"No usable data for {len(failed_symbols)} symbol(s): {failed_symbols[:20]}"
              + (" ..." if len(failed_symbols) > 20 else ""))
    if success_rate < 70:
        print(
            f"WARNING: only {success_rate:.0f}% of the S&P 500 universe was fetched - "
            "sector strength and market breadth are being computed over a smaller, "
            "potentially unrepresentative sample."
        )

    perf_df = pd.DataFrame(performance)

    if perf_df.empty:
        print("Failed to calculate performance, returning empty universe.")
        return {}

    print("Ranking stocks by sector...")
    top_stocks = {}

    for sector, group in perf_df.groupby('Sector'):
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
    universe = get_top_stocks_by_sector(limit_per_sector=5)
    print(f"Total stocks in dynamic universe: {len(universe)}")
    print("Sample stocks:")
    for i, (k, v) in enumerate(universe.items()):
        if i < 10:
            print(f"{k}: {v}")
