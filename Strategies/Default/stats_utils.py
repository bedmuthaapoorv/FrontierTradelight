"""Persists each strategy's latest backtest stats (CAGR, Max Drawdown,
Number of Trades, Composite Score) across runs, keyed by the (entry
strategy name, exit strategy name) pair - so switching entry strategies,
or re-benchmarking the same entry against a different exit strategy,
builds up a running leaderboard instead of the latest run silently
overwriting an earlier, differently-paired one.

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
    """Overwrites the row for (strategy_name, exit_strategy_name) with its
    latest stats, leaving every other row untouched. Does nothing if
    strategy_name is blank (rules.md has no declared "Strategy Name").

    Rows are keyed by the (Strategy Name, Exit Strategy Name) PAIR, not by
    strategy_name alone - benchmarking the same entry rules.md against two
    different exit strategies keeps two separate leaderboard rows, so you
    can compare them, instead of the second run silently erasing the
    first's recorded numbers. A blank/missing Exit Strategy Name is its own
    distinct key (matches other blank ones, not a different exit's row)."""
    if not strategy_name:
        return

    exit_strategy_name = exit_strategy_name or ""

    stats_df = load_strategy_stats(path)
    same_pair = (stats_df["Strategy Name"] == strategy_name) & (
        stats_df["Exit Strategy Name"].fillna("") == exit_strategy_name
    )
    stats_df = stats_df[~same_pair]

    new_row = pd.DataFrame([{
        "Strategy Name": strategy_name,
        "Exit Strategy Name": exit_strategy_name,
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
