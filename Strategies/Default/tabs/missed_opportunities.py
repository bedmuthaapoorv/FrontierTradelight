"""Surfaces near-misses from the last backtest: stocks that failed exactly
one rule, and what a simple hold would have returned - so you can see,
per rule, whether it's blocking winners or correctly filtering losers.
"""

import pandas as pd
import streamlit as st

import strings
from constants import BACKTEST_TRADES_PATH, NEAR_MISSES_PATH
from ui_helpers import nonempty_csv_exists

TITLE = "Missed Opportunities"
ORDER = 55


def render():
    st.subheader("Near-misses from the last backtest")
    st.caption(strings.MISSED_OPPORTUNITIES_CAPTION)

    if not nonempty_csv_exists(NEAR_MISSES_PATH):
        st.info(strings.NO_NEAR_MISSES_INFO)
        return

    try:
        near_misses_df = pd.read_csv(NEAR_MISSES_PATH)
    except pd.errors.EmptyDataError:
        st.info(strings.NO_NEAR_MISSES_INFO)
        return

    if near_misses_df.empty:
        st.info(strings.NO_NEAR_MISSES_INFO)
        return

    render_rule_breakdown(near_misses_df)
    st.divider()
    render_top_near_misses(near_misses_df)


def render_rule_breakdown(near_misses_df):
    st.subheader("By blocking rule")
    st.caption(strings.RULE_BREAKDOWN_CAPTION)

    by_rule = near_misses_df.groupby("FailedRule")["ForwardReturnPct"].agg(
        NearMisses="count",
        AvgForwardReturnPct="mean",
        WinRatePct=lambda s: (s > 0).mean() * 100,
    ).reset_index()
    by_rule = by_rule.sort_values("AvgForwardReturnPct", ascending=False)

    benchmark_avg, benchmark_win_rate = load_realized_trade_benchmark()
    if benchmark_avg is not None:
        st.caption(
            f"Your realized trades averaged {benchmark_avg:+.2f}% profit "
            f"with a {benchmark_win_rate:.0f}% win rate - rows above that "
            "are near-misses that outperformed what you actually captured."
        )

    st.dataframe(
        by_rule.rename(columns={
            "FailedRule": "Rule that blocked it",
            "NearMisses": "Near-misses",
            "AvgForwardReturnPct": f"Avg {strings.NEAR_MISS_HOLDING_DAYS}-day forward return",
            "WinRatePct": "Win rate",
        }).style.format({
            f"Avg {strings.NEAR_MISS_HOLDING_DAYS}-day forward return": "{:+.2f}%",
            "Win rate": "{:.0f}%",
        }),
        use_container_width=True,
    )


def load_realized_trade_benchmark():
    if not nonempty_csv_exists(BACKTEST_TRADES_PATH):
        return None, None
    try:
        trades_df = pd.read_csv(BACKTEST_TRADES_PATH)
    except pd.errors.EmptyDataError:
        return None, None
    if trades_df.empty or "ProfitRs" not in trades_df.columns:
        return None, None
    return trades_df["ProfitRs"].mean(), (trades_df["ProfitRs"] > 0).mean() * 100


def render_top_near_misses(near_misses_df):
    st.subheader("Biggest individual near-misses")
    st.caption(strings.TOP_NEAR_MISSES_CAPTION)

    display_columns = ["Date", "Symbol", "FailedRuleDetail", "ClosenessScore", "ForwardReturnPct"]
    top = near_misses_df.sort_values("ForwardReturnPct", ascending=False).head(20)[display_columns]
    st.dataframe(
        top.rename(columns={
            "FailedRuleDetail": "Why it was rejected",
            "ForwardReturnPct": f"{strings.NEAR_MISS_HOLDING_DAYS}-day forward return",
        }).style.format({f"{strings.NEAR_MISS_HOLDING_DAYS}-day forward return": "{:+.2f}%"}),
        use_container_width=True,
    )
