"""Leaderboard of every strategy's latest backtest stats, persisted across
runs (see stats_utils.py) so switching strategies and backtesting each one
builds up a comparison table instead of only ever showing the last run."""

import streamlit as st

from constants import STRATEGY_STATS_PATH
from stats_utils import load_strategy_stats

TITLE = "Stats"
ORDER = 60


def render():
    st.subheader("Strategy stats")
    st.caption(
        "The latest CAGR, Max Drawdown, and Composite Score recorded for "
        "each strategy you've backtested. Running a backtest updates only "
        "that strategy's row here - it never re-runs other strategies, and "
        "every other strategy's row is left exactly as it was."
    )

    stats_df = load_strategy_stats(STRATEGY_STATS_PATH)
    if stats_df.empty:
        st.info("No strategy stats yet. Run a backtest from the Backtest tab first.")
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
