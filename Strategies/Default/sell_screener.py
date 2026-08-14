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

from constants import HOLDINGS_PATH, SELL_REPORT_PATH
from nse_utils import fetch_stock_history

warnings.filterwarnings("ignore")


def load_holdings(path):
    df = pd.read_csv(path, parse_dates=["EntryDate"])
    if "CurrentPrice" not in df.columns:
        df["CurrentPrice"] = None
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


def apply_live_price(full_df, current_price):
    """Folds a manually-entered live price into today's bar, so the exit
    check reacts to what you're looking at right now rather than NSE's last
    published close (which can lag by up to a day - see sell_screener's
    module docstring). If NSE has already published a bar for today, the
    live price extends that bar's high/low and becomes its close. Otherwise
    a new single-point bar is appended for today."""
    if current_price is None or pd.isna(current_price):
        return full_df

    today = pd.Timestamp(datetime.date.today())
    current_price = float(current_price)

    if not full_df.empty and full_df.index[-1].date() == today.date():
        full_df = full_df.copy()
        last_idx = full_df.index[-1]
        full_df.loc[last_idx, "high"] = max(full_df.loc[last_idx, "high"], current_price)
        full_df.loc[last_idx, "low"] = min(full_df.loc[last_idx, "low"], current_price)
        full_df.loc[last_idx, "close"] = current_price
        return full_df

    new_row = pd.DataFrame(
        [{"open": current_price, "high": current_price, "low": current_price, "close": current_price}],
        index=[today],
    )
    return pd.concat([full_df, new_row])


def evaluate_holding(symbol, entry_price, entry_date, full_df, current_price=None):
    """Mirrors backtest.py's _open_and_resolve_trade, but with today as the
    open-ended right edge instead of a fixed backtest end date, and without
    the RangeEnd fallback - a holding with no exit signal yet is just a hold."""
    import generated_exit_strategy

    full_df = apply_live_price(full_df, current_price)

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
        "Reason": describe_hold_reason(entry_price, entry_date, signal_history, future),
        "CurrentPrice": round(current_price, 2),
        "ReturnPct": round(return_pct, 2),
    }


def describe_hold_reason(entry_price, entry_date, signal_history, future):
    """Turns generated_exit_strategy.describe_state()'s raw numbers into a
    human-readable explanation of how close each exit condition is to
    firing, instead of just "not met yet"."""
    import generated_exit_strategy

    describe_state = getattr(generated_exit_strategy, "describe_state", None)
    if describe_state is None:
        return "Exit condition not met yet."

    try:
        state = describe_state(entry_price, entry_date, signal_history, future)
    except Exception:
        state = None

    if state is None:
        return "Exit condition not met yet."

    parts = []
    if state.get("TrailingStop") is not None and state.get("DistanceToStopPct") is not None:
        parts.append(
            f"Trailing stop at {state['TrailingStop']:.2f} "
            f"({state['DistanceToStopPct']:.1f}% below current price)"
        )
    if state.get("DaysHeld") is not None and state.get("DaysToMaxHold") is not None:
        parts.append(f"{state['DaysHeld']}/90 trading days held")

    return "; ".join(parts) if parts else "Exit condition not met yet."


def screen_holdings(holdings):
    results = []
    for holding in holdings:
        symbol = holding["Symbol"]
        entry_price = float(holding["EntryPrice"])
        entry_date = holding["EntryDate"]
        current_price = holding.get("CurrentPrice")

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

            results.append(evaluate_holding(symbol, entry_price, entry_date, full_df, current_price))
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
    parser.add_argument("--holdings", default=HOLDINGS_PATH)
    parser.add_argument("--out", default=SELL_REPORT_PATH)
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
