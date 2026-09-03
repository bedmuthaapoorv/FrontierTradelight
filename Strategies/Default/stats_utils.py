"""Persists each strategy's latest backtest stats (CAGR, Max Drawdown,
Composite Score) across runs, keyed by the strategy's declared name - so
switching strategies and backtesting each one builds up a running
leaderboard instead of only ever showing the most recent run."""

import os
from datetime import datetime

import pandas as pd

COLUMNS = ["Strategy Name", "CAGR (%/yr)", "Max Drawdown (%)", "Composite Score", "Last Updated"]


def load_strategy_stats(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path)


def upsert_strategy_stats(path, strategy_name, cagr_pct, max_dd_pct, composite_score):
    """Overwrites the row for strategy_name with its latest stats, leaving
    every other strategy's previously saved row untouched. Does nothing if
    strategy_name is blank (rules.md has no declared "Strategy Name")."""
    if not strategy_name:
        return

    stats_df = load_strategy_stats(path)
    stats_df = stats_df[stats_df["Strategy Name"] != strategy_name]

    new_row = pd.DataFrame([{
        "Strategy Name": strategy_name,
        "CAGR (%/yr)": cagr_pct,
        "Max Drawdown (%)": max_dd_pct,
        "Composite Score": composite_score,
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    stats_df = pd.concat([stats_df, new_row], ignore_index=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    stats_df.to_csv(path, index=False)
