import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np

# pyrefly: ignore [missing-import]
import pandas_ta as ta
# pyrefly: ignore [missing-import]
from scipy.stats import linregress
import datetime
import random
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

from universe_fetcher import get_top_stocks_by_sector
from nse_utils import fetch_stock_history, calculate_sector_strength, calculate_market_breadth
from constants import REPORT_PATH

# 1. Fetch Dynamic Stock Universe by Sector
print("Initializing Dynamic Stock Universe...")
STOCK_UNIVERSE = get_top_stocks_by_sector(limit_per_sector=50)
if not STOCK_UNIVERSE:
    print("Warning: Dynamic fetch failed, falling back to basic sample.")
    STOCK_UNIVERSE = {
        "RELIANCE": {"Name": "Reliance Industries", "Sector": "Energy"},
        "TCS": {"Name": "Tata Consultancy Services", "Sector": "IT"},
    }

# jugaad-data hits NSE's raw historical API, which starts throttling/
# bot-detecting under too much concurrent load - kept modest and staggered
# for the same reason backtest.py's load_universe_history is (see its
# FETCH_WORKERS/STAGGER_SECONDS comment), just tuned for a single day's
# fetch instead of a multi-year one.
FETCH_WORKERS = 5
STAGGER_SECONDS = (0.1, 0.5)


def _fetch_one(ticker, from_date, to_date):
    time.sleep(random.uniform(*STAGGER_SECONDS))
    df = fetch_stock_history(symbol=ticker, from_date=from_date, to_date=to_date, series="EQ")
    if df is None or df.empty or len(df) <= 100:
        return ticker, None

    df = df.sort_values(by="DATE").set_index("DATE")
    df = df.rename(columns={
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
        "VOLUME": "volume",
        "DELIVERY %": "delivery_pct",
    })
    if "delivery_pct" not in df.columns:
        df["delivery_pct"] = float("nan")
    return ticker, df


def fetch_data(tickers, days=400, max_workers=FETCH_WORKERS):
    """Fetch historical data for all tickers concurrently (matching
    backtest.py's load_universe_history pattern) - fetches are independent
    per-symbol NSE requests, so this is the main lever on wall-clock time
    for a universe this size, same as it is for the backtester."""
    print("Fetching data...")
    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=days)
    data = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {
            executor.submit(_fetch_one, ticker, from_date, to_date): ticker
            for ticker in tickers
        }
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                ticker, df = future.result()
                if df is not None:
                    data[ticker] = df
            except Exception as e:
                print(f"Failed to fetch {ticker}: {e}")
    return data

def find_trendline_touches(df):
    """Find trendline touches and distance."""
    # Simplified approach for demonstration
    # In a robust system, you'd use pivot points (argrelextrema).
    # Here we just look at the lowest lows over the last 90 days.
    recent = df.iloc[-90:].copy()
    if len(recent) < 90:
        return 0, 100, 0
    
    # We will simulate the trendline quality for now to allow some stocks to pass
    # Real trendline detection is quite complex for a single script.
    
    # Let's assume a dummy touch count between 1 and 3, and a dummy distance
    import random
    touches = random.choice([1, 2, 3])
    distance = random.uniform(0.5, 5.0)
    slope = random.uniform(-0.5, 1.5)
    
    return touches, distance, slope

def analyze_stocks(data, universe, sector_ranks, market_breadth):
    results = []

    import generated_rules

    for symbol, df in data.items():
        if len(df) < 50:
            continue

        try:
            result = generated_rules.evaluate_stock(
                symbol,
                df,
                universe,
                sector_ranks,
                market_breadth
            )

            if result:
                results.append(result)

        except Exception as e:
            print(f"Error evaluating {symbol}: {e}")

            results.append({
                "Symbol": symbol,
                "Passed": False,
                "ClosenessScore": 0,
                "FailedRules": [str(e)],
                "Details": {}
            })

    return results

def main():
    tickers = list(STOCK_UNIVERSE.keys())
    data = fetch_data(tickers)
    sector_ranks = calculate_sector_strength(data, STOCK_UNIVERSE)
    market_breadth = calculate_market_breadth(data)
    results = analyze_stocks(data, STOCK_UNIVERSE, sector_ranks, market_breadth)

    if not results:
        print("No results generated.")
        return

    csv_rows = []

    for result in results:

        row = {
            "Symbol": result["Symbol"],
            "Passed": result["Passed"],
            "ClosenessScore": round(
                result["ClosenessScore"],
                2
            ),
            "FailedRules": "; ".join(
                result["FailedRules"]
            )
        }

        details = result.get("Details", {})

        for key, value in details.items():
            row[key] = value

        csv_rows.append(row)

    df_results = pd.DataFrame(csv_rows)

    df_results = df_results.sort_values(
        by="ClosenessScore",
        ascending=False
    )

    print("\n--- BEST STOCKS BY CLOSENESS SCORE ---")
    print(df_results.head(20).to_string(index=False))

    df_results.to_csv(
        REPORT_PATH,
        index=False
    )

    print(
        f"\nResults saved to {REPORT_PATH}"
    )

if __name__ == "__main__":
    main()
