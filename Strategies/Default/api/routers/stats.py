"""Serves the strategy leaderboard and the strategy-switch flow used before
a benchmark backtest - the FastAPI equivalent of tabs/stats.py, reusing
stats_utils.load_strategy_stats and backup_utils.group_backups/list_backups
verbatim so the numbers and strategy options can never diverge from the
Streamlit app. Actually launching the benchmark backtest reuses the
existing /backtest/run endpoint - the frontend just calls it with the fixed
benchmark date range - and record_stats_if_benchmark (already wired into
/backtest/status) writes this leaderboard's rows, exactly as it does for
the Streamlit app.

File IO and the generate_screener.py subprocess are done directly here
(not via ui_helpers.write_and_sync/run_script, which touch st.session_state
and st.empty()) - same reason api/routers/markdown_files.py rolls its own
_read_text/_write_text instead of reusing the Streamlit-bound helpers.
"""

import os
import subprocess
import sys

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from backup_utils import backup_markdown, group_backups, list_backups
from constants import APP_DIR, BACKUP_DIR, BENCHMARK_END_DATE, BENCHMARK_START_DATE, RULES_PATH, STRATEGY_STATS_PATH
from stats_utils import load_strategy_stats

router = APIRouter(prefix="/stats")

CURRENT_LIVE_OPTION = "Current (live rules.md)"


def _format_option_label(group_key):
    if group_key == CURRENT_LIVE_OPTION:
        return group_key
    label = group_key[: -len("_rules")] if group_key.endswith("_rules") else group_key
    return label.replace("_", " ").title()


@router.get("")
def get_stats():
    stats_df = load_strategy_stats(STRATEGY_STATS_PATH)
    if stats_df.empty:
        return {
            "benchmark_start": BENCHMARK_START_DATE.isoformat(),
            "benchmark_end": BENCHMARK_END_DATE.isoformat(),
            "rows": [],
        }

    stats_df = stats_df.sort_values(by="Composite Score", ascending=False, na_position="last")
    return {
        "benchmark_start": BENCHMARK_START_DATE.isoformat(),
        "benchmark_end": BENCHMARK_END_DATE.isoformat(),
        "rows": [
            {
                "strategy_name": row["Strategy Name"],
                "exit_strategy_name": None if pd.isna(row["Exit Strategy Name"]) or not row["Exit Strategy Name"] else row["Exit Strategy Name"],
                "cagr_pct": None if pd.isna(row["CAGR (%/yr)"]) else float(row["CAGR (%/yr)"]),
                "max_dd_pct": None if pd.isna(row["Max Drawdown (%)"]) else float(row["Max Drawdown (%)"]),
                "num_trades": None if "Number of Trades" not in row or pd.isna(row["Number of Trades"]) else int(row["Number of Trades"]),
                "composite_score": None if pd.isna(row["Composite Score"]) else float(row["Composite Score"]),
                "last_updated": row["Last Updated"],
            }
            for _, row in stats_df.iterrows()
        ],
    }


@router.get("/strategy-options")
def get_strategy_options():
    groups = group_backups(list_backups(BACKUP_DIR))
    return {
        "options": [{"key": CURRENT_LIVE_OPTION, "label": CURRENT_LIVE_OPTION}]
        + [{"key": k, "label": _format_option_label(k)} for k in groups.keys()]
    }


class LoadStrategyRequest(BaseModel):
    group_key: str


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


@router.post("/load-strategy")
def load_strategy_for_benchmark(body: LoadStrategyRequest):
    """Overwrites the live rules.md with the selected backup's latest
    version (backing up whatever was live first) and regenerates
    generated_rules.py from it - mirrors tabs/stats.py's
    _load_strategy_for_benchmark exactly."""
    groups = group_backups(list_backups(BACKUP_DIR))
    latest_file_by_group = {key: versions[0] for key, versions in groups.items()}

    if body.group_key not in latest_file_by_group:
        return {"status": "error", "message": f"Unknown strategy group: {body.group_key}"}

    backup_path = os.path.join(BACKUP_DIR, latest_file_by_group[body.group_key])
    new_content = _read_text(backup_path)

    current_content = _read_text(RULES_PATH) if os.path.exists(RULES_PATH) else ""
    if current_content.strip() and current_content != new_content:
        backup_markdown(current_content, BACKUP_DIR, "rules")

    _write_text(RULES_PATH, new_content)

    process = subprocess.run(
        [sys.executable, "generate_screener.py"], cwd=APP_DIR, capture_output=True, text=True,
    )
    if process.returncode != 0:
        return {
            "status": "error",
            "message": f"generate_screener.py failed (exit {process.returncode}) - benchmark not started.",
        }

    return {"status": "ok"}
