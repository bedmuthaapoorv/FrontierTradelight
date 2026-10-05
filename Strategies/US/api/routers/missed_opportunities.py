"""Serves near_misses.csv grouped by blocking rule, plus the realized-trade
benchmark and biggest individual near-misses - the FastAPI equivalent of
tabs/missed_opportunities.py, computing the exact same aggregations
(same groupby/agg calls) so the numbers can never diverge from the
Streamlit app.
"""

import os

import pandas as pd
from fastapi import APIRouter

from backtest_runner import read_backtest_meta
from constants import BACKTEST_TRADES_PATH, NEAR_MISSES_PATH

router = APIRouter(prefix="/missed-opportunities")


def _load_realized_trade_benchmark():
    if not os.path.exists(BACKTEST_TRADES_PATH) or os.path.getsize(BACKTEST_TRADES_PATH) == 0:
        return None, None
    try:
        trades_df = pd.read_csv(BACKTEST_TRADES_PATH)
    except pd.errors.EmptyDataError:
        return None, None
    if trades_df.empty or "ProfitRs" not in trades_df.columns:
        return None, None
    return float(trades_df["ProfitRs"].mean()), float((trades_df["ProfitRs"] > 0).mean() * 100)


@router.get("")
def get_missed_opportunities():
    if not os.path.exists(NEAR_MISSES_PATH) or os.path.getsize(NEAR_MISSES_PATH) == 0:
        return {"available": False}

    try:
        near_misses_df = pd.read_csv(NEAR_MISSES_PATH)
    except pd.errors.EmptyDataError:
        return {"available": False}
    if near_misses_df.empty:
        return {"available": False}

    by_rule = near_misses_df.groupby("FailedRule")["ForwardReturnPct"].agg(
        NearMisses="count",
        AvgForwardReturnPct="mean",
        WinRatePct=lambda s: (s > 0).mean() * 100,
    ).reset_index()
    by_rule = by_rule.sort_values("AvgForwardReturnPct", ascending=False)

    realized_avg, realized_win_rate = _load_realized_trade_benchmark()

    top = near_misses_df.sort_values("ForwardReturnPct", ascending=False).head(20)[
        ["Date", "Symbol", "FailedRuleDetail", "ClosenessScore", "ForwardReturnPct"]
    ]

    meta = read_backtest_meta()

    return {
        "available": True,
        "strategy_name": meta["strategy_name"],
        "exit_strategy_name": meta["exit_strategy_name"],
        "realized_avg_profit": realized_avg,
        "realized_win_rate": realized_win_rate,
        "rule_rows": [
            {
                "rule": row["FailedRule"],
                "count": int(row["NearMisses"]),
                "avg_forward_return_pct": float(row["AvgForwardReturnPct"]),
                "win_rate_pct": float(row["WinRatePct"]),
            }
            for _, row in by_rule.iterrows()
        ],
        "top_rows": [
            {
                "date": row["Date"],
                "symbol": row["Symbol"],
                "reason": row["FailedRuleDetail"],
                "closeness_score": float(row["ClosenessScore"]),
                "forward_return_pct": float(row["ForwardReturnPct"]),
            }
            for _, row in top.iterrows()
        ],
    }
