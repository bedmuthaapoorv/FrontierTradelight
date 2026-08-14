"""Backtest generated_rules.py + generated_exit_strategy.py over a date range."""

import os
import subprocess
import sys

import pandas as pd
import streamlit as st

import backtest as backtest_engine
import inflation_utils
import nifty_utils
import strings
from constants import (
    APP_DIR,
    BACKTEST_LOG_PATH,
    BACKTEST_PORTFOLIO_PATH,
    BACKTEST_SUMMARY_PATH,
    BACKTEST_TRADES_PATH,
)
from ui_helpers import nonempty_csv_exists, read_text, show_guide

TITLE = "Backtest"
ORDER = 50


def render():
    st.subheader("Backtest the current strategy")
    st.caption(strings.BACKTEST_TAB_CAPTION)

    show_guide("BACKTEST_GUIDE.md", "New to backtesting? Read the guide")
    st.caption(strings.EXIT_STRATEGY_ELSEWHERE_CAPTION)

    st.divider()

    start_date, end_date, initial_capital, max_positions, is_running = render_config()
    render_run_controls(start_date, end_date, initial_capital, max_positions, is_running)
    render_portfolio_result(initial_capital)
    render_summary_and_trades()


def render_config():
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date")
    with col2:
        end_date = st.date_input("End date")

    col3, col4 = st.columns(2)
    with col3:
        initial_capital = st.number_input("Starting capital (Rs.)", min_value=1000.0, value=100000.0, step=10000.0)
    with col4:
        max_positions = st.number_input("Max concurrent positions", min_value=1, value=10, step=1)

    st.caption(strings.POSITION_SLOTS_CAPTION)
    st.caption(strings.CACHE_CAPTION)

    is_running = st.session_state.get("backtest_running", False)

    if start_date < end_date and not is_running:
        try:
            est = backtest_engine.estimate_runtime(start_date, end_date)
            if est["to_fetch_stocks"] == 0:
                st.info(f"All {est['total_stocks']} stocks already cached for this range — should finish in well under a minute.")
            else:
                low_min = est["estimated_low_seconds"] / 60
                high_min = est["estimated_high_seconds"] / 60
                st.info(
                    f"{est['to_fetch_stocks']} of {est['total_stocks']} stocks need fetching from NSE "
                    f"(~{est['months_per_stock']} monthly requests each for this range) — "
                    f"estimated **{low_min:.1f}-{high_min:.1f} min**. "
                    f"({est['cached_stocks']} already cached.)"
                )
        except Exception:
            pass

    return start_date, end_date, initial_capital, max_positions, is_running


@st.fragment(run_every=2)
def show_backtest_progress():
    """Polls the running backtest's log file and process status every 2s,
    without blocking the rest of the page (so the Stop button stays clickable)."""
    process = st.session_state.get("backtest_process")
    if process is None:
        return

    if os.path.exists(BACKTEST_LOG_PATH):
        st.code(read_text(BACKTEST_LOG_PATH)[-3000:] or "Starting...")

    if process.poll() is not None:
        st.session_state.backtest_running = False
        if process.returncode == 0:
            st.success("Backtest complete. See results below.")
        else:
            st.error(f"backtest.py exited with code {process.returncode}.")
        st.rerun()


def render_run_controls(start_date, end_date, initial_capital, max_positions, is_running):
    run_col, stop_col = st.columns([1, 1])
    with run_col:
        run_clicked = st.button("Run backtest", disabled=is_running)
    with stop_col:
        stop_clicked = st.button("Stop backtest", disabled=not is_running)

    if run_clicked:
        if start_date >= end_date:
            st.error("Start date must be before end date.")
        else:
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
            st.rerun()

    if stop_clicked:
        process = st.session_state.get("backtest_process")
        if process is not None and process.poll() is None:
            process.terminate()
        st.session_state.backtest_running = False
        st.warning(strings.BACKTEST_STOPPED_WARNING)

    if is_running:
        show_backtest_progress()


def render_portfolio_result(initial_capital):
    if not nonempty_csv_exists(BACKTEST_PORTFOLIO_PATH):
        return

    st.divider()
    st.subheader("Portfolio result")
    try:
        portfolio_df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
        if not portfolio_df.empty and os.path.exists(BACKTEST_TRADES_PATH):
            trades_for_capital = pd.read_csv(BACKTEST_TRADES_PATH)
            final_equity = portfolio_df["Equity"].iloc[-1]
            total_return_pct = (final_equity - initial_capital) / initial_capital * 100
            funded_count = int(trades_for_capital["Funded"].sum()) if "Funded" in trades_for_capital.columns else 0
            skipped_count = len(trades_for_capital) - funded_count

            span_days = (portfolio_df["Date"].max() - portfolio_df["Date"].min()).days
            years = span_days / 365.25
            if years > 0 and final_equity > 0:
                cagr_pct = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
                cagr_display = f"{cagr_pct:+.2f}%/yr"
            else:
                cagr_display = "N/A"

            running_max = portfolio_df["Equity"].cummax()
            drawdown_pct = (portfolio_df["Equity"] - running_max) / running_max * 100
            max_dd_pct = drawdown_pct.min()

            show_inflation_adjusted = st.checkbox(
                "Show inflation-adjusted results", help=strings.INFLATION_ADJUSTED_HELP
            )

            yearly_rates = inflation_utils.fetch_india_cpi_yearly() if show_inflation_adjusted else None

            display_equity, display_return_pct, display_cagr, inflation_caption = adjust_for_inflation(
                portfolio_df, initial_capital, final_equity, total_return_pct, years,
                show_inflation_adjusted, yearly_rates,
            )

            if inflation_caption:
                st.caption(inflation_caption)

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric(
                "Final equity" + (" (inflation-adjusted)" if show_inflation_adjusted else ""),
                f"Rs.{display_equity:,.0f}",
                f"{display_return_pct:+.2f}% total",
            )
            m2.metric(
                "CAGR" + (" (inflation-adjusted)" if show_inflation_adjusted else ""),
                display_cagr,
                help=strings.CAGR_HELP,
            )
            m3.metric("Max drawdown", f"{max_dd_pct:.1f}%", help=strings.MAX_DRAWDOWN_HELP)
            m4.metric("Funded trades", funded_count)
            m5.metric("Skipped (no capital)", skipped_count)

            render_equity_chart(portfolio_df, initial_capital, show_inflation_adjusted, yearly_rates)

            with st.expander("Year-by-year breakdown"):
                st.caption(strings.YEARLY_BREAKDOWN_CAPTION)
                yearly_df = portfolio_df.copy()
                yearly_df["Year"] = yearly_df["Date"].dt.year
                yearly = yearly_df.groupby("Year")["Equity"].agg(["first", "last"])
                yearly["Return %"] = (yearly["last"] - yearly["first"]) / yearly["first"] * 100
                yearly = yearly.rename(columns={"first": "Start Equity", "last": "End Equity"})
                st.dataframe(
                    yearly.style.format({"Start Equity": "Rs.{:,.0f}", "End Equity": "Rs.{:,.0f}", "Return %": "{:+.1f}%"}),
                    use_container_width=True,
                )
    except pd.errors.EmptyDataError:
        st.caption("No portfolio data from the last run.")


def deflate_equity(dates, equity, yearly_rates):
    """Converts a nominal equity curve to real (inflation-adjusted) terms,
    using each calendar year's actual India CPI inflation rate rather than
    one flat assumed rate - years without published data yet fall back to
    the latest known year's rate. Compounds daily within each year."""
    latest_known_rate = yearly_rates[max(yearly_rates)]
    daily_pct = dates.dt.year.map(lambda year: yearly_rates.get(year, latest_known_rate))
    daily_factor = (1 + daily_pct / 100) ** (1 / 365.25)
    deflator = daily_factor.cumprod()
    deflator = deflator / deflator.iloc[0]
    return equity / deflator


def adjust_for_inflation(portfolio_df, initial_capital, final_equity, total_return_pct, years,
                          enabled, yearly_rates):
    """Returns (final_equity, total_return_pct, cagr_display, caption) - the
    nominal values unchanged if `enabled` is False, or the inflation-adjusted
    equivalents (falling back to nominal with an error caption if the CPI
    data couldn't be fetched) if True. Used to swap the metric tiles in
    place rather than adding a separate row of "adjusted" metrics."""
    nominal_cagr_display = f"{(((final_equity / initial_capital) ** (1 / years) - 1) * 100):+.2f}%/yr" if years > 0 and final_equity > 0 else "N/A"

    if not enabled:
        return final_equity, total_return_pct, nominal_cagr_display, None

    if not yearly_rates:
        return final_equity, total_return_pct, nominal_cagr_display, strings.INFLATION_FETCH_ERROR

    real_equity_series = deflate_equity(portfolio_df["Date"], portfolio_df["Equity"], yearly_rates)
    real_final_equity = real_equity_series.iloc[-1]
    real_total_return_pct = (real_final_equity - initial_capital) / initial_capital * 100
    if years > 0 and real_final_equity > 0:
        real_cagr_display = f"{(((real_final_equity / initial_capital) ** (1 / years) - 1) * 100):+.2f}%/yr"
    else:
        real_cagr_display = "N/A"

    years_used = sorted(set(portfolio_df["Date"].dt.year) & set(yearly_rates))
    rates_summary = ", ".join(f"{y}: {yearly_rates[y]:+.1f}%" for y in years_used)
    caption = f"India CPI inflation (World Bank): {rates_summary}"

    return real_final_equity, real_total_return_pct, real_cagr_display, caption


def render_equity_chart(portfolio_df, initial_capital, show_inflation_adjusted, yearly_rates):
    show_nifty_comparison = st.checkbox(
        "Compare with Nifty 50", help=strings.NIFTY_COMPARISON_HELP
    )

    chart_df = portfolio_df.set_index("Date")[["Equity"]].rename(columns={"Equity": "Nominal"})

    if show_inflation_adjusted and yearly_rates:
        chart_df["Inflation-adjusted"] = deflate_equity(
            portfolio_df["Date"], portfolio_df["Equity"], yearly_rates
        ).values

    if show_nifty_comparison:
        start_date = portfolio_df["Date"].min().date()
        end_date = portfolio_df["Date"].max().date()
        with st.spinner("Building Nifty 50 benchmark..."):
            benchmark_df = nifty_utils.build_nifty_50_benchmark(start_date, end_date, initial_capital)

        if benchmark_df is None:
            st.error(strings.NIFTY_FETCH_ERROR)
        else:
            st.caption(strings.NIFTY_COMPARISON_CAPTION)
            benchmark_series = benchmark_df.set_index("Date")["Equity"].reindex(
                chart_df.index, method="ffill"
            )
            chart_df["Nifty 50"] = benchmark_series.values

    st.line_chart(chart_df)


def render_summary_and_trades():
    if nonempty_csv_exists(BACKTEST_SUMMARY_PATH):
        st.divider()
        st.subheader("Summary by ClosenessScore bucket")
        try:
            st.dataframe(pd.read_csv(BACKTEST_SUMMARY_PATH), use_container_width=True)
        except pd.errors.EmptyDataError:
            st.caption("No trades were simulated in the last run, so there's no summary to bucket.")

    if nonempty_csv_exists(BACKTEST_TRADES_PATH):
        st.subheader("Individual trades")
        try:
            st.dataframe(pd.read_csv(BACKTEST_TRADES_PATH), use_container_width=True)
        except pd.errors.EmptyDataError:
            st.caption("No trades were simulated in the last run.")
