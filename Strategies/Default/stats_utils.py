"""Persists each strategy's latest backtest stats (CAGR, Max Drawdown,
Number of Trades, Composite Score) across runs, keyed by the strategy's
declared name - so switching strategies and backtesting each one builds up
a running leaderboard instead of only ever showing the most recent run.

Also records a hash of the exact rules.md content that produced each
score ("Rules Content Hash") - this is what lets the Rules tab figure out
WHICH specific saved backup file within a strategy's version history
actually earned that score, not just which strategy name did (see
api/routers/stats.py's version-matching logic). Only rows recorded after
this column was added carry a hash; older rows have none and simply can't
be matched to a specific file."""

import hashlib
import os
from datetime import datetime

import pandas as pd

COLUMNS = ["Strategy Name", "Exit Strategy Name", "CAGR (%/yr)", "Max Drawdown (%)", "Number of Trades", "Composite Score", "Rules Content Hash", "Last Updated"]


def hash_rules_content(content):
    """A stable content hash (sha256 hex digest) used to match a recorded
    score back to the exact backup file (or live rules.md) it came from -
    plain string equality on file content would work too, but a hash keeps
    strategy_stats.csv from carrying full rules.md text in every row."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_strategy_stats(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(path)


def upsert_strategy_stats(path, strategy_name, cagr_pct, max_dd_pct, composite_score, exit_strategy_name=None, num_trades=None, rules_content_hash=None):
    """Overwrites the row for strategy_name with its latest stats, leaving
    every other strategy's previously saved row untouched. Does nothing if
    strategy_name is blank (rules.md has no declared "Strategy Name").

    Note: rows are keyed by strategy_name alone, not by (strategy_name,
    exit_strategy_name) - backtesting the same rules.md with a different
    exit strategy overwrites the same row rather than creating a second
    one. Exit Strategy Name is recorded so you can see which exit produced
    the numbers currently shown, not to distinguish multiple rows."""
    if not strategy_name:
        return

    stats_df = load_strategy_stats(path)
    stats_df = stats_df[stats_df["Strategy Name"] != strategy_name]

    new_row = pd.DataFrame([{
        "Strategy Name": strategy_name,
        "Exit Strategy Name": exit_strategy_name or "",
        "CAGR (%/yr)": cagr_pct,
        "Max Drawdown (%)": max_dd_pct,
        "Number of Trades": num_trades,
        "Composite Score": composite_score,
        "Rules Content Hash": rules_content_hash,
        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }])

    stats_df = pd.concat([stats_df, new_row], ignore_index=True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    stats_df.to_csv(path, index=False)
