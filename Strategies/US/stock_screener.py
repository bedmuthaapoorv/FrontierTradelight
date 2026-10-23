import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np

# pyrefly: ignore [missing-import]
import pandas_ta as ta
# pyrefly: ignore [missing-import]
from scipy.stats import linregress
import datetime
import json
import warnings
warnings.filterwarnings('ignore')

from universe_fetcher import get_top_stocks_by_sector
from market_data import fetch_bars_batch, calculate_sector_strength, calculate_market_breadth
from constants import MARKET_BREADTH_PATH, REPORT_PATH

# 1. Fetch Dynamic Stock Universe by Sector
print("Initializing Dynamic Stock Universe...")
STOCK_UNIVERSE = get_top_stocks_by_sector(limit_per_sector=50)
if not STOCK_UNIVERSE:
    print("Warning: Dynamic fetch failed, falling back to basic sample.")
    STOCK_UNIVERSE = {
        "AAPL": {"Name": "Apple Inc.", "Sector": "Information Technology"},
        "XOM": {"Name": "ExxonMobil", "Sector": "Energy"},
    }

def _prepare_df(raw):
    df = raw.sort_values(by="DATE").set_index("DATE")
    df = df.rename(columns={
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
        "VOLUME": "volume",
    })
    # US exchanges publish no delivery %; kept as a NaN column so rules
    # written against the India data shape still run.
    df["delivery_pct"] = float("nan")
    return df


def fetch_data(tickers, days=400):
    """Fetch historical data for all tickers in one batched Alpaca call
    (see market_data.fetch_bars_batch) - a few multi-symbol requests
    instead of one staggered request per stock."""
    print("Fetching data...")
    to_date = datetime.date.today()
    from_date = to_date - datetime.timedelta(days=days)
    histories = fetch_bars_batch(
        tickers, from_date, to_date,
        progress=lambda done, total: print(f"  fetched {done}/{total} symbols"),
    )
    return {
        ticker: _prepare_df(raw)
        for ticker, raw in histories.items()
        if len(raw) > 100
    }

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

def save_market_breadth(breadth, stocks):
    """Persist the latest breadth reading so the UI header can show it
    without refetching the whole universe."""
    with open(MARKET_BREADTH_PATH, "w", encoding="utf-8") as f:
        json.dump({"breadth": round(breadth, 1), "stocks": stocks, "as_of": datetime.datetime.now().isoformat(timespec="seconds")}, f)


def main():
    tickers = list(STOCK_UNIVERSE.keys())
    data = fetch_data(tickers)
    sector_ranks = calculate_sector_strength(data, STOCK_UNIVERSE)
    market_breadth = calculate_market_breadth(data)
    save_market_breadth(market_breadth, len(data))
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
