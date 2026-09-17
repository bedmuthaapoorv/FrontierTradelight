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

from backup_utils import backup_markdown, group_backups, list_backups, strategy_slug
from constants import APP_DIR, BACKUP_DIR, BENCHMARK_END_DATE, BENCHMARK_START_DATE, RULES_PATH, STRATEGY_STATS_PATH
from stats_utils import hash_rules_content, load_strategy_stats

router = APIRouter(prefix="/stats")

CURRENT_LIVE_OPTION = "Current (live rules.md)"


def _format_option_label(group_key):
    if group_key == CURRENT_LIVE_OPTION:
        return group_key
    label = group_key[: -len("_rules")] if group_key.endswith("_rules") else group_key
    return label.replace("_", " ").title()


def _group_key_for_name(strategy_name):
    """Reuses strategy_slug's exact slugification (lowercase, non-alnum ->
    _) by feeding it a synthetic "Strategy Name: ..." line, rather than
    duplicating that regex here - the group key MUST be produced the same
    way backup_markdown produces it, or badges would silently never
    match."""
    return f"{strategy_slug(f'Strategy Name: {strategy_name}')}_rules"


def _best_performing_group_key(stats_df):
    """The rules.md backup group key (see backup_utils.group_backups) for
    the strategy with the highest recorded Composite Score - so the Rules
    tab's version drawer can badge whichever saved strategy actually
    backtested best, not just whichever is currently live. Returns None
    if there are no scored rows yet."""
    scored = stats_df.dropna(subset=["Composite Score"])
    if scored.empty:
        return None
    best_name = scored.loc[scored["Composite Score"].idxmax(), "Strategy Name"]
    return _group_key_for_name(best_name)


def _best_scoring_file_by_group(stats_df):
    """For every strategy name with a recorded score, figures out WHICH
    specific backup file within that strategy's own version history is
    the exact content that earned it - not just which strategy NAME
    scored best, but which dated save.

    Each strategy_stats.csv row now carries a "Rules Content Hash" (see
    stats_utils.hash_rules_content), captured by backtest.py at the exact
    moment a benchmark run used that content. This hashes every backup
    file within the row's own group and looks for a match - a content
    hash is used rather than string-comparing full file text just to keep
    this cheap once there are many backups.

    Returns {group_key: filename}. A row is skipped (no entry) if it has
    no recorded hash (e.g. it predates this tracking) or if none of the
    group's current backup files match (e.g. that exact save was later
    deleted, or it's still only the live, never-backed-up rules.md -
    which the version drawer doesn't list as a file to badge anyway)."""
    if "Rules Content Hash" not in stats_df.columns:
        return {}
    scored = stats_df.dropna(subset=["Composite Score", "Rules Content Hash"])
    if scored.empty:
        return {}

    groups = group_backups(list_backups(BACKUP_DIR))
    result = {}
    for _, row in scored.iterrows():
        group_key = _group_key_for_name(row["Strategy Name"])
        target_hash = row["Rules Content Hash"]
        for filename in groups.get(group_key, []):
            backup_path = os.path.join(BACKUP_DIR, filename)
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue
            if hash_rules_content(content) == target_hash:
                result[group_key] = filename
                break
    return result


@router.get("")
def get_stats():
    stats_df = load_strategy_stats(STRATEGY_STATS_PATH)
    if stats_df.empty:
        return {
            "benchmark_start": BENCHMARK_START_DATE.isoformat(),
            "benchmark_end": BENCHMARK_END_DATE.isoformat(),
            "best_performing_group_key": None,
            "best_scoring_file_by_group": {},
            "rows": [],
        }

    best_group_key = _best_performing_group_key(stats_df)
    best_file_by_group = _best_scoring_file_by_group(stats_df)
    stats_df = stats_df.sort_values(by="Composite Score", ascending=False, na_position="last")
    return {
        "benchmark_start": BENCHMARK_START_DATE.isoformat(),
        "benchmark_end": BENCHMARK_END_DATE.isoformat(),
        "best_performing_group_key": best_group_key,
        "best_scoring_file_by_group": best_file_by_group,
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
