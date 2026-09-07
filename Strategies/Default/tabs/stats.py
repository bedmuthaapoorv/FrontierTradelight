"""Leaderboard of every strategy's latest backtest stats, persisted across
runs (see stats_utils.py) so switching strategies and backtesting each one
builds up a comparison table instead of only ever showing the last run."""

import os

import streamlit as st

from backtest_runner import launch_backtest, show_backtest_progress
from backup_utils import backup_markdown, group_backups, list_backups
from constants import BACKUP_DIR, BENCHMARK_END_DATE, BENCHMARK_START_DATE, RULES_PATH, STRATEGY_STATS_PATH
from stats_utils import load_strategy_stats
from ui_helpers import read_text, run_script, write_and_sync

TITLE = "Stats"
ORDER = 60

BENCHMARK_INITIAL_CAPITAL = 100000.0
BENCHMARK_MAX_POSITIONS = 10
CURRENT_LIVE_OPTION = "Current (live rules.md)"


def _format_option_label(group_key):
    if group_key == CURRENT_LIVE_OPTION:
        return group_key
    label = group_key[:-len("_rules")] if group_key.endswith("_rules") else group_key
    return label.replace("_", " ").title()


def _strategy_options():
    """Every strategy available to benchmark: the currently live rules.md,
    plus one entry per distinct strategy saved under Rules_backup/ (its
    newest version - group_backups already sorts each group newest-first).
    Returns (option_labels, group_to_latest_file)."""
    groups = group_backups(list_backups(BACKUP_DIR))
    return [CURRENT_LIVE_OPTION] + list(groups.keys()), {key: versions[0] for key, versions in groups.items()}


def _load_strategy_for_benchmark(selected_group, latest_file_by_group):
    """Overwrites the live rules.md with the selected backup (backing up
    whatever was live first, same as the Rules tab's own overwrite flow),
    then regenerates generated_rules.py from it. Returns True on success."""
    backup_path = os.path.join(BACKUP_DIR, latest_file_by_group[selected_group])
    new_content = read_text(backup_path)

    current_content = read_text(RULES_PATH)
    if current_content.strip() and current_content != new_content:
        backup_markdown(current_content, BACKUP_DIR, "rules")

    write_and_sync(RULES_PATH, new_content, "rules_content")

    with st.spinner(f"Regenerating rules.md logic for {_format_option_label(selected_group)}..."):
        exit_code = run_script("generate_screener.py")
    if exit_code != 0:
        st.error(f"generate_screener.py failed (exit {exit_code}) - benchmark not started.")
        return False
    return True


def render():
    st.subheader("Strategy stats")
    st.caption(
        "The latest CAGR, Max Drawdown, and Composite Score recorded for "
        "each strategy backtested over the benchmark range below. Running "
        "a backtest updates only that strategy's row here - it never "
        "re-runs other strategies, and every other strategy's row is left "
        "exactly as it was."
    )
    st.caption(
        f"This table only updates from a backtest run over the exact "
        f"benchmark range - **{BENCHMARK_START_DATE} to {BENCHMARK_END_DATE}** "
        f"(5 years) - so every row is a fair, apples-to-apples comparison. "
        f"A backtest run over any other range (e.g. from the Backtest tab) "
        f"will NOT update this table."
    )

    is_running = st.session_state.get("backtest_running", False)
    options, latest_file_by_group = _strategy_options()

    btn_col, select_col = st.columns([1, 2])
    with btn_col:
        run_clicked = st.button(
            "Benchmark backtest", disabled=is_running,
            help=f"Runs {BENCHMARK_START_DATE} to {BENCHMARK_END_DATE} for the strategy chosen on the right, then updates this table with the result.",
        )
    with select_col:
        selected = st.selectbox(
            "Strategy to benchmark", options, disabled=is_running, label_visibility="collapsed",
            format_func=_format_option_label,
        )

    if selected != CURRENT_LIVE_OPTION:
        st.caption(
            f"Selecting a strategy here and clicking Benchmark backtest makes it "
            f"the LIVE strategy (rules.md) - whatever's live now is backed up "
            f"first, same as overwriting from the Rules tab's restore modal."
        )

    if run_clicked:
        ready = True
        if selected != CURRENT_LIVE_OPTION:
            ready = _load_strategy_for_benchmark(selected, latest_file_by_group)
        if ready:
            launch_backtest(BENCHMARK_START_DATE, BENCHMARK_END_DATE, BENCHMARK_INITIAL_CAPITAL, BENCHMARK_MAX_POSITIONS)
            st.rerun()

    if is_running:
        show_backtest_progress()

    stats_df = load_strategy_stats(STRATEGY_STATS_PATH)
    if stats_df.empty:
        st.info("No strategy stats yet. Run a Benchmark backtest above first.")
        return

    stats_df = stats_df.sort_values(by="Composite Score", ascending=False, na_position="last")
    st.dataframe(
        stats_df.style.format({
            "CAGR (%/yr)": "{:+.2f}%",
            "Max Drawdown (%)": "{:.1f}%",
            "Composite Score": "{:.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
