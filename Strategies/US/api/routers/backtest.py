"""Launch/poll/stop a backtest.py subprocess and serve its results, reusing
backtest_runner.py's pure helpers (_latest_progress, _format_eta,
compute_metrics, read_backtest_meta, record_stats_if_benchmark) and
inflation_utils.deflate_equity so the numbers are computed identically
everywhere. The job is tracked in a module-level dict - fine for this
single-user local tool, where only one backtest ever runs at a time.
"""

import json
import os
import subprocess
import sys
import time

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import inflation_utils
import sp500_utils
from backtest_runner import (
    _format_eta,
    _latest_progress,
    compute_metrics,
    read_backtest_meta,
    record_stats_if_benchmark,
)
from constants import (
    APP_DIR,
    BACKTEST_LOG_PATH,
    BACKTEST_META_PATH,
    BACKTEST_PORTFOLIO_PATH,
    BACKTEST_TRADES_PATH,
)
from inflation_utils import deflate_equity

router = APIRouter(prefix="/backtest")

_job = {"process": None, "start_time": None, "initial_capital": None}


class RunRequest(BaseModel):
    start: str
    end: str
    initial_capital: float
    max_positions: int


# Launches backtest.py as a subprocess with the given date range/capital/
# slots; refuses to start a second one while one is already running.
@router.post("/run")
def run_backtest(body: RunRequest):
    if _job["process"] is not None and _job["process"].poll() is None:
        raise HTTPException(status_code=409, detail="A backtest is already running.")

    args = [
        "--start", body.start,
        "--end", body.end,
        "--initial-capital", str(body.initial_capital),
        "--max-positions", str(int(body.max_positions)),
    ]
    with open(BACKTEST_LOG_PATH, "w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            [sys.executable, "backtest.py", *args],
            cwd=APP_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )
    _job["process"] = process
    _job["start_time"] = time.time()
    _job["initial_capital"] = body.initial_capital
    return {"status": "started"}


# Terminates the running backtest subprocess, if any.
@router.post("/stop")
def stop_backtest():
    process = _job["process"]
    if process is not None and process.poll() is None:
        process.terminate()
    _job["process"] = None
    return {"status": "stopped"}


# Polls the running backtest's log for progress/ETA; once it exits, clears
# the job and records the result to the Stats leaderboard if it matches
# the benchmark date range.
@router.get("/status")
def backtest_status():
    process = _job["process"]
    if process is None:
        return {"running": False}

    if os.path.exists(BACKTEST_LOG_PATH):
        with open(BACKTEST_LOG_PATH, "r", encoding="utf-8") as f:
            log_tail = f.read()[-4000:]
    else:
        log_tail = ""
    progress = _latest_progress(log_tail)
    day = total = None
    eta_seconds = None
    if progress:
        day, total, _day_date = progress
        if _job["start_time"] and day > 0:
            elapsed = time.time() - _job["start_time"]
            seconds_per_day = elapsed / day
            eta_seconds = seconds_per_day * max(0, total - day)

    exit_code = process.poll()
    running = exit_code is None

    result = {
        "running": running,
        "day": day,
        "total_days": total,
        "eta_seconds": eta_seconds,
        "log_tail": log_tail,
    }

    if not running:
        _job["process"] = None
        result["exit_code"] = exit_code
        if exit_code == 0:
            recorded, reason = record_stats_if_benchmark()
            result["stats_recorded"] = recorded
            result["stats_reason"] = reason

    return result


# Returns the last completed backtest's headline numbers (CAGR, drawdown,
# Sharpe-based composite score, funded/skipped trade counts, meta).
@router.get("/result")
def backtest_result():
    if not os.path.exists(BACKTEST_PORTFOLIO_PATH):
        return {"available": False}
    try:
        portfolio_df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
    except pd.errors.EmptyDataError:
        return {"available": False}
    if portfolio_df.empty:
        return {"available": False}

    initial_capital = _job["initial_capital"] or 100000.0
    if os.path.exists(BACKTEST_META_PATH):
        with open(BACKTEST_META_PATH, "r", encoding="utf-8") as f:
            initial_capital = json.load(f).get("initial_capital", initial_capital)

    final_equity = float(portfolio_df["Equity"].iloc[-1])
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100
    cagr_pct, max_dd_pct, composite_score = compute_metrics(portfolio_df, initial_capital)

    funded_count = skipped_count = 0
    if os.path.exists(BACKTEST_TRADES_PATH):
        trades_df = pd.read_csv(BACKTEST_TRADES_PATH)
        if "Funded" in trades_df.columns:
            funded_count = int(trades_df["Funded"].sum())
            skipped_count = len(trades_df) - funded_count

    return {
        "available": True,
        "initial_capital": initial_capital,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "max_dd_pct": max_dd_pct,
        "composite_score": composite_score,
        "funded_count": funded_count,
        "skipped_count": skipped_count,
        "meta": read_backtest_meta(),
    }


# Returns the equity curve for charting, optionally alongside an
# inflation-adjusted series and/or an S&P 500 (SPY) benchmark series.
@router.get("/chart")
def backtest_chart(inflation: bool = False, benchmark: bool = False):
    if not os.path.exists(BACKTEST_PORTFOLIO_PATH):
        return {"dates": [], "nominal": [], "inflation_adjusted": None, "benchmark": None}

    portfolio_df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
    if portfolio_df.empty:
        return {"dates": [], "nominal": [], "inflation_adjusted": None, "benchmark": None}

    dates = portfolio_df["Date"].dt.strftime("%Y-%m-%d").tolist()
    nominal = portfolio_df["Equity"].tolist()

    inflation_series = None
    if inflation:
        yearly_rates = inflation_utils.fetch_cpi_yearly()
        if yearly_rates:
            inflation_series = deflate_equity(
                portfolio_df["Date"], portfolio_df["Equity"], yearly_rates
            ).tolist()

    benchmark_series_out = None
    if benchmark:
        initial_capital = _job["initial_capital"] or 100000.0
        if os.path.exists(BACKTEST_META_PATH):
            with open(BACKTEST_META_PATH, "r", encoding="utf-8") as f:
                initial_capital = json.load(f).get("initial_capital", initial_capital)
        start_date = portfolio_df["Date"].min().date()
        end_date = portfolio_df["Date"].max().date()
        benchmark_df = sp500_utils.build_sp_500_benchmark(start_date, end_date, initial_capital)
        if benchmark_df is not None:
            benchmark_series = (
                benchmark_df.set_index("Date")["Equity"]
                .reindex(portfolio_df.set_index("Date").index, method="ffill")
            )
            benchmark_series_out = benchmark_series.tolist()

    return {
        "dates": dates,
        "nominal": nominal,
        "inflation_adjusted": inflation_series,
        "benchmark": benchmark_series_out,
    }


# Returns the real daily equity path split by calendar year, for the Deep
# Dive tab's client-side year-range analysis.
@router.get("/portfolio-by-year")
def backtest_portfolio_by_year():
    """Daily equity path for each calendar year in the last backtest, plus
    the overall date range - everything the Deep Dive tab needs to
    replicate tabs/deep_dive.py's stitch_equity/elapsed_years logic
    client-side against the REAL daily path (not a bucketed
    approximation), for whatever year selection the user picks."""
    if not os.path.exists(BACKTEST_PORTFOLIO_PATH):
        return {"years": [], "overall_min": None, "overall_max": None}
    df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
    if df.empty:
        return {"years": [], "overall_min": None, "overall_max": None}

    df["Year"] = df["Date"].dt.year
    years = []
    for year, group in df.groupby("Year"):
        g = group.sort_values("Date")
        years.append({
            "year": int(year),
            "dates": g["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "equity": g["Equity"].tolist(),
            "return_pct": float((g["Equity"].iloc[-1] - g["Equity"].iloc[0]) / g["Equity"].iloc[0] * 100),
        })

    return {
        "years": years,
        "overall_min": df["Date"].min().strftime("%Y-%m-%d"),
        "overall_max": df["Date"].max().strftime("%Y-%m-%d"),
    }


# Returns each calendar year's start/end equity and return % - the
# summarized (non-daily) year-by-year view.
@router.get("/yearly")
def backtest_yearly():
    if not os.path.exists(BACKTEST_PORTFOLIO_PATH):
        return {"rows": []}
    df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
    if df.empty:
        return {"rows": []}

    df["Year"] = df["Date"].dt.year
    yearly = df.groupby("Year")["Equity"].agg(["first", "last"])
    yearly["ReturnPct"] = (yearly["last"] - yearly["first"]) / yearly["first"] * 100

    return {
        "rows": [
            {
                "year": int(year),
                "start_equity": float(row["first"]),
                "end_equity": float(row["last"]),
                "return_pct": float(row["ReturnPct"]),
            }
            for year, row in yearly.iterrows()
        ]
    }
