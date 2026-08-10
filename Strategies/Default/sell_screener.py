"""Tells you what to sell today, the sell-side mirror of stock_screener.py.

stock_screener.py runs generated_rules.py (from rules.md) against the whole
universe to find new buys. This script runs generated_exit_strategy.py (from
exit_rules.md) against your current holdings to find sells: for each
holding, it replays the exit logic over every trading day since entry using
data available as of today, and reports whether it would have already fired.
"""

import argparse
import datetime
import sys
import warnings

import pandas as pd

from nse_utils import fetch_stock_history

warnings.filterwarnings("ignore")


def load_holdings(path):
    df = pd.read_csv(path, parse_dates=["EntryDate"])
    return df.to_dict("records")


def fetch_history(symbol, entry_date, lookback_days=200):
    from_date = entry_date - datetime.timedelta(days=lookback_days)
    to_date = datetime.date.today()
    df = fetch_stock_history(symbol=symbol, from_date=from_date, to_date=to_date, series="EQ")
    if df is None or df.empty:
        return None
    df = df.sort_values(by="DATE").set_index("DATE")
    return df.rename(columns={
        "OPEN": "open",
        "HIGH": "high",
        "LOW": "low",
        "CLOSE": "close",
        "VOLUME": "volume",
    })


def evaluate_holding(symbol, entry_price, entry_date, full_df):
    """Mirrors backtest.py's _open_and_resolve_trade, but with today as the
    open-ended right edge instead of a fixed backtest end date, and without
    the RangeEnd fallback - a holding with no exit signal yet is just a hold."""
    import generated_exit_strategy

    entry_date = entry_date.date() if hasattr(entry_date, "date") else entry_date
    signal_history = full_df[full_df.index.date <= entry_date]
    future = full_df[full_df.index.date >= entry_date]

    if future.empty:
        return {
            "Symbol": symbol,
            "Recommendation": "UNKNOWN",
            "Reason": "No price data available since entry date.",
            "CurrentPrice": None,
            "ReturnPct": None,
        }

    current_price = float(future["close"].iloc[-1])
    return_pct = (current_price - entry_price) / entry_price * 100

    try:
        exit_result = generated_exit_strategy.resolve_exit(entry_price, entry_date, signal_history, future)
    except Exception as e:
        exit_result = None
        print(f"Error evaluating exit for {symbol}: {e}")

    if exit_result is not None:
        return {
            "Symbol": symbol,
            "Recommendation": "SELL",
            "Reason": exit_result.get("ExitReason", "Exit condition met"),
            "ExitDate": pd.Timestamp(exit_result["ExitDate"]).date(),
            "ExitPrice": round(float(exit_result["ExitPrice"]), 2),
            "CurrentPrice": round(current_price, 2),
            "ReturnPct": round(return_pct, 2),
        }

    return {
        "Symbol": symbol,
        "Recommendation": "HOLD",
        "Reason": "Exit condition not met yet.",
        "CurrentPrice": round(current_price, 2),
        "ReturnPct": round(return_pct, 2),
    }


def screen_holdings(holdings):
    results = []
    for holding in holdings:
        symbol = holding["Symbol"]
        entry_price = float(holding["EntryPrice"])
        entry_date = holding["EntryDate"]

        try:
            full_df = fetch_history(symbol, entry_date.date() if hasattr(entry_date, "date") else entry_date)
            if full_df is None:
                results.append({
                    "Symbol": symbol,
                    "Recommendation": "UNKNOWN",
                    "Reason": "Could not fetch price history.",
                    "CurrentPrice": None,
                    "ReturnPct": None,
                })
                continue

            results.append(evaluate_holding(symbol, entry_price, entry_date, full_df))
        except Exception as e:
            results.append({
                "Symbol": symbol,
                "Recommendation": "UNKNOWN",
                "Reason": str(e),
                "CurrentPrice": None,
                "ReturnPct": None,
            })

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--holdings", default="holdings.csv")
    parser.add_argument("--out", default="sell_report.csv")
    args = parser.parse_args()

    holdings = load_holdings(args.holdings)
    if not holdings:
        print("No holdings to check.")
        return

    results = screen_holdings(holdings)
    df_results = pd.DataFrame(results)

    print("\n--- SELL SCREENER RESULTS ---")
    print(df_results.to_string(index=False))

    df_results.to_csv(args.out, index=False)
    print(f"\nResults saved to {args.out}")


if __name__ == "__main__":
    sys.exit(main() or 0)
