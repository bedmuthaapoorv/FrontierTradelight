"""Shared logic for launching a backtest.py subprocess, polling its
progress, and recording results into the Stats tab's CSV - used by both
tabs/backtest.py (user-chosen date range) and tabs/stats.py (the fixed
benchmark range), so both go through the exact same launch/poll/record
path instead of duplicating it, and only one backtest can ever be running
at a time regardless of which tab started it (tracked via the same
st.session_state keys)."""

import json
import os
import re
import subprocess
import sys
import time

import pandas as pd
import streamlit as st

from constants import (
    APP_DIR,
    BACKTEST_LOG_PATH,
    BACKTEST_META_PATH,
    BACKTEST_PORTFOLIO_PATH,
    BACKTEST_TRADES_PATH,
    BENCHMARK_END_DATE,
    BENCHMARK_START_DATE,
    STRATEGY_STATS_PATH,
)
from stats_utils import upsert_strategy_stats
from ui_helpers import read_text


def launch_backtest(start_date, end_date, initial_capital, max_positions):
    """Starts backtest.py as a subprocess and stores it in session_state
    for show_backtest_progress() to track. Caller is responsible for
    calling st.rerun() afterward."""
    args = [
        "--start", start_date.isoformat(),
        "--end", end_date.isoformat(),
        "--initial-capital", str(initial_capital),
        "--max-positions", str(int(max_positions)),
    ]

    with open(BACKTEST_LOG_PATH, "w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [sys.executable, "backtest.py", *args],
            cwd=APP_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    st.session_state.backtest_process = process
    st.session_state.backtest_running = True
    st.session_state.backtest_start_time = time.time()


def read_backtest_meta():
    """The strategy/exit-strategy/date-range the CURRENT
    backtest_portfolio.csv actually belongs to - recorded by backtest.py
    at the moment it ran, not re-read from rules.md/exit_rules.md/the
    date inputs now, since any of those can change after the fact without
    a new backtest being run. All values None if unavailable (e.g. a
    portfolio.csv from before this tracking existed)."""
    empty = {"strategy_name": None, "exit_strategy_name": None, "start_date": None, "end_date": None}
    if not os.path.exists(BACKTEST_META_PATH):
        return empty
    try:
        with open(BACKTEST_META_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except (json.JSONDecodeError, OSError):
        return empty
    return {
        "strategy_name": meta.get("strategy_name") or None,
        "exit_strategy_name": meta.get("exit_strategy_name") or None,
        "start_date": meta.get("start_date") or None,
        "end_date": meta.get("end_date") or None,
    }


def is_benchmark_range(meta):
    return (
        meta.get("start_date") == BENCHMARK_START_DATE.isoformat()
        and meta.get("end_date") == BENCHMARK_END_DATE.isoformat()
    )


def compute_metrics(portfolio_df, initial_capital):
    """CAGR / Max Drawdown / Composite Score, computed identically
    everywhere in this app so the Backtest tab's display and the Stats
    tab's recorded numbers can never quietly diverge."""
    final_equity = portfolio_df["Equity"].iloc[-1]
    span_days = (portfolio_df["Date"].max() - portfolio_df["Date"].min()).days
    years = span_days / 365.25

    if years > 0 and final_equity > 0:
        cagr_pct = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
    else:
        cagr_pct = None

    running_max = portfolio_df["Equity"].cummax()
    drawdown_pct = (portfolio_df["Equity"] - running_max) / running_max * 100
    max_dd_pct = drawdown_pct.min()

    daily_returns = portfolio_df["Equity"].pct_change().dropna()
    sharpe_ratio = (
        (daily_returns.mean() / daily_returns.std()) * (252 ** 0.5)
        if daily_returns.std() > 0 else 0.0
    )

    composite_score = (
        (cagr_pct / 100 * sharpe_ratio) / abs(max_dd_pct / 100)
        if cagr_pct is not None and max_dd_pct != 0 else None
    )
    return cagr_pct, max_dd_pct, composite_score


def record_stats_if_benchmark():
    """Upserts into the Stats tab's CSV ONLY if backtest_portfolio.csv was
    just produced by a run over the exact benchmark date range - so the
    leaderboard only ever holds apples-to-apples comparisons, never a
    stray shorter/longer test run silently mixed in. Called once, right
    when a backtest actually finishes (see show_backtest_progress) - not
    on every page view, so the table updates exactly when a benchmark
    backtest runs and never otherwise.

    Returns (recorded: bool, reason: str) so the caller can tell the user
    what happened - "recorded", "range mismatch", or "no strategy name"."""
    meta = read_backtest_meta()
    if not meta["strategy_name"]:
        return False, "no strategy name"
    if not is_benchmark_range(meta):
        return False, "range mismatch"

    try:
        portfolio_df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return False, "no portfolio data"
    if portfolio_df.empty:
        return False, "no portfolio data"

    # initial_capital isn't stored in portfolio.csv itself - read it from
    # the same run's recorded meta.
    with open(BACKTEST_META_PATH, "r", encoding="utf-8") as f:
        initial_capital = json.load(f).get("initial_capital", 100000.0)

    cagr_pct, max_dd_pct, composite_score = compute_metrics(portfolio_df, initial_capital)
    if cagr_pct is None:
        return False, "degenerate run"

    num_trades = None
    try:
        trades_df = pd.read_csv(BACKTEST_TRADES_PATH)
        if "Funded" in trades_df.columns:
            num_trades = int(trades_df["Funded"].sum())
    except (FileNotFoundError, pd.errors.EmptyDataError):
        pass

    upsert_strategy_stats(
        STRATEGY_STATS_PATH, meta["strategy_name"], cagr_pct, max_dd_pct, composite_score,
        exit_strategy_name=meta["exit_strategy_name"], num_trades=num_trades,
    )
    return True, "recorded"


_PROGRESS_LINE_RE = re.compile(r"Evaluating day (\d+)/(\d+) \(([\d-]+)\)")


def _latest_progress(log_tail):
    """Returns (day_num, total_days, day_date) from the LAST "Evaluating
    day X/Y (date)..." line in the given log text, or None if no such
    line is present yet (e.g. still in the pre-evaluation data-fetch
    phase, which prints no per-day progress)."""
    matches = _PROGRESS_LINE_RE.findall(log_tail)
    if not matches:
        return None
    day_num, total_days, day_date = matches[-1]
    return int(day_num), int(total_days), day_date


def _format_eta(seconds):
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    if minutes == 0:
        return f"{secs}s"
    return f"{minutes}m {secs}s"


@st.fragment(run_every=2)
def show_backtest_progress():
    """Polls the running backtest's log file and process status every 2s,
    without blocking the rest of the page (so a Stop button stays
    clickable). Shared by the Backtest tab and the Stats tab's Benchmark
    Backtest button - whichever one launched the run, this is where
    Stats-tab recording actually happens, exactly once, right as the
    process exits successfully."""
    process = st.session_state.get("backtest_process")
    if process is None:
        return

    if os.path.exists(BACKTEST_LOG_PATH):
        log_tail = read_text(BACKTEST_LOG_PATH)[-4000:]
        progress = _latest_progress(log_tail)

        if progress is None:
            st.info("Fetching/preparing data... (per-day progress starts once this completes)")
        else:
            day_num, total_days, day_date = progress
            fraction = day_num / total_days if total_days else 0.0

            start_time = st.session_state.get("backtest_start_time")
            eta_text = ""
            if start_time and day_num > 0:
                elapsed = time.time() - start_time
                seconds_per_day = elapsed / day_num
                remaining_days = max(0, total_days - day_num)
                eta_text = f" - est. {_format_eta(seconds_per_day * remaining_days)} remaining"

            st.progress(
                fraction,
                text=f"Evaluating day {day_num}/{total_days} ({day_date}){eta_text}",
            )

        with st.expander("Raw log"):
            st.code(log_tail or "Starting...")

    if process.poll() is not None:
        st.session_state.backtest_running = False
        if process.returncode == 0:
            st.success("Backtest complete. See results below.")
            recorded, reason = record_stats_if_benchmark()
            if recorded:
                st.success("Stats tab updated (this run matched the benchmark range).")
            elif reason == "range mismatch":
                st.info(
                    "Stats tab NOT updated - this run wasn't over the benchmark range "
                    f"({BENCHMARK_START_DATE} to {BENCHMARK_END_DATE}). Use \"Benchmark "
                    "backtest\" on the Stats tab for a comparable result."
                )
        else:
            st.error(f"backtest.py exited with code {process.returncode}.")
        st.rerun()
