"""Risk tab: Value at Risk on the last backtest's trades, plus a
risk-based-sizing-vs-equal-weight comparison (headline metrics, equity
curves with drill-down, Monte Carlo drawdown calibration, portfolio heat,
risk-by-sector, and per-trade sizing rationale).

Also home to the chart/drill-down helpers (`selectable_line_chart`,
`render_period_drilldown`) shared with tabs/backtest.py's equity chart -
kept here (not duplicated) since this module has no import of its own on
tabs.backtest, so tabs/backtest.py importing from here can't create a
circular import.
"""

import json
import os

import altair as alt
import pandas as pd
import streamlit as st

import backtest
import strings
from constants import (
    BACKTEST_PORTFOLIO_PATH,
    BACKTEST_PORTFOLIO_RISK_PATH,
    BACKTEST_RISK_INFO_PATH,
    BACKTEST_TRADES_PATH,
    BACKTEST_TRADES_RISK_PATH,
)
from ui_helpers import nonempty_csv_exists

TITLE = "Risk"
ORDER = 60


def _perf_stats(portfolio_df, initial_capital):
    """CAGR / max-drawdown / total-return, same math as the Backtest tab's
    metric tiles, factored out so the Risk tab can compute it for both the
    equal-weight and risk-sized curves without duplicating the formula."""
    final_equity = portfolio_df["Equity"].iloc[-1]
    total_return_pct = (final_equity - initial_capital) / initial_capital * 100

    span_days = (portfolio_df["Date"].max() - portfolio_df["Date"].min()).days
    years = span_days / 365.25
    cagr_pct = ((final_equity / initial_capital) ** (1 / years) - 1) * 100 if years > 0 and final_equity > 0 else None

    running_max = portfolio_df["Equity"].cummax()
    drawdown_pct = (portfolio_df["Equity"] - running_max) / running_max * 100
    max_dd_pct = drawdown_pct.min()

    return {
        "final_equity": final_equity, "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct, "max_dd_pct": max_dd_pct,
    }


def _to_date(raw):
    """Normalize one endpoint of a Vega-Lite temporal selection to a date.

    Vega-Lite reports temporal selection bounds as epoch MILLISECONDS
    (a plain int/float), not nanoseconds - passing one straight to
    pd.to_datetime() makes pandas read it as nanoseconds, collapsing every
    selection to 1970-01-01. Strings (ISO dates) are also accepted, since
    the exact serialization varies by Vega-Lite version."""
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            return pd.to_datetime(raw, unit="ms").date()
        return pd.to_datetime(raw).date()
    except (ValueError, TypeError, OverflowError):
        return None


def selectable_line_chart(df, y_cols, key, y_axis_title=None):
    """Render an Altair line chart with a draggable x-axis (date) selection
    brush, so the caller can drill into whatever period the user selects.
    Returns a (start_date, end_date) tuple if a range is currently selected,
    else None."""
    if len(y_cols) == 1:
        chart = alt.Chart(df).mark_line().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y(f"{y_cols[0]}:Q", title=y_axis_title or y_cols[0]),
        )
    else:
        long_df = df.melt(id_vars=["Date"], value_vars=y_cols, var_name="Series", value_name="Value")
        chart = alt.Chart(long_df).mark_line().encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Value:Q", title=y_axis_title or "Value"),
            color="Series:N",
        )

    brush = alt.selection_interval(name="date_range", encodings=["x"])
    chart = chart.add_params(brush).properties(height=350)

    event = st.altair_chart(chart, on_select="rerun", key=key, use_container_width=True)

    selection = None
    try:
        selection = event.selection.date_range
    except AttributeError:
        try:
            selection = event["selection"]["date_range"]
        except (TypeError, KeyError):
            selection = None

    if selection and selection.get("Date") and len(selection["Date"]) == 2:
        start_raw, end_raw = selection["Date"]
        start_date = _to_date(start_raw)
        end_date = _to_date(end_raw)
        if start_date is None or end_date is None:
            return None
        # A drag right-to-left reports the bounds reversed; normalize so
        # callers can always assume start <= end.
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        return (start_date, end_date)
    return None


def render_edge_warning(trades_df, risk_info=None, ruin_tolerance_pct=5.0):
    """Surface the two findings that make the sizing engine's output
    misleading if read at face value: a non-positive Kelly fraction (the
    sample shows no edge, so the engine is only floored at the default risk
    % rather than sizing up into an edge) and a risk of ruin above
    tolerance (which halves every subsequent position). Both are decisions
    the engine makes silently in backtest.py's sizing path - without this
    banner the only visible symptom is "positions look small"."""
    if trades_df is None or trades_df.empty or "RMultiple" not in trades_df.columns:
        return

    stats = backtest.kelly_stats(trades_df["RMultiple"].tolist())
    kelly = stats["kelly_fraction"]
    ruin_pct = (risk_info or {}).get("risk_of_ruin_pct")

    problems = []
    if kelly is not None and kelly <= 0:
        problems.append(
            f"**No positive edge in this sample.** Win rate {stats['win_rate'] * 100:.1f}% at a "
            f"{stats['payoff_ratio']:.2f} payoff ratio gives a Kelly fraction of "
            f"**f\\* = {kelly:+.3f}** — Kelly's verdict is not to bet this strategy at all. "
            f"Sizing is falling back to the flat default risk %, not sizing into an edge."
        )
    if ruin_pct is not None and ruin_pct > ruin_tolerance_pct:
        problems.append(
            f"**Risk of ruin {ruin_pct:.1f}%** (tolerance {ruin_tolerance_pct:.0f}%) — every "
            f"position size below has already been halved as a result."
        )

    if not problems:
        return

    st.error(
        "### Sizing engine is in damage-control mode\n\n"
        + "\n\n".join(f"- {p}" for p in problems)
        + "\n\nPosition sizing controls how fast a losing strategy bleeds; it cannot make "
          "negative expectancy profitable. Treat the comparison below as *which sizing loses "
          "less*, not as a validated edge — the fix lives in the entry/exit rules."
    )


def render_period_drilldown(date_range, trades_by_label):
    """Given a (start_date, end_date) tuple from selectable_line_chart (or
    None) and a dict of {label: trades_df}, show a per-label breakdown of
    which trades were active during that window.

    Stats are computed over FUNDED trades only, and P&L in Rs. (allocated
    capital x the trade's % return), not raw ProfitRs. Both matter: ProfitRs
    is the return on a notional flat Rs.100 stake, so it is identical across
    sizing modes by construction - the whole difference between equal-weight
    and risk-based sizing lives in which signals got funded at all and how
    much capital each one received. Summing raw ProfitRs across trades of
    different position sizes would make the two modes look identical and
    wouldn't be a real P&L figure either.
    """
    if date_range is None:
        st.caption("Drag across the chart above to inspect a specific time period.")
        return

    start_date, end_date = date_range

    def _render_one(label, trades_df):
        st.markdown(f"**{label}** ({start_date} to {end_date})")
        entry_dates = pd.to_datetime(trades_df["EntryDate"]).dt.date
        exit_dates = pd.to_datetime(trades_df["ExitDate"]).dt.date
        active = trades_df[(entry_dates <= end_date) & (exit_dates >= start_date)]

        signals_count = len(active)
        funded = active[active["Funded"] == True] if "Funded" in active.columns else active

        if funded.empty:
            st.caption(f"No funded trades in this window ({signals_count} signals fired but none were funded).")
            return

        if "AllocatedCapital" in funded.columns:
            pnl_rs = funded["AllocatedCapital"] * funded["ProfitRs"] / 100
        else:
            pnl_rs = None

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Funded trades", len(funded), f"of {signals_count} signals")
        m2.metric("Win rate", f"{(funded['ProfitRs'] > 0).mean() * 100:.1f}%")

        if pnl_rs is not None:
            m3.metric("Realized P&L", f"Rs.{pnl_rs.sum():+,.0f}")
            best_idx, worst_idx = pnl_rs.idxmax(), pnl_rs.idxmin()
            m4.metric("Best trade", f"{funded.loc[best_idx, 'Symbol']} Rs.{pnl_rs.max():+,.0f}")
            st.caption(
                f"Worst trade: {funded.loc[worst_idx, 'Symbol']} Rs.{pnl_rs.min():+,.0f} "
                f"({funded.loc[worst_idx, 'ProfitRs']:+.1f}%) | "
                f"Avg return per funded trade: {funded['ProfitRs'].mean():+.2f}%"
            )
        else:
            m3.metric("Avg return", f"{funded['ProfitRs'].mean():+.2f}%")
            best_idx = funded["ProfitRs"].idxmax()
            m4.metric("Best trade", f"{funded.loc[best_idx, 'Symbol']} {funded['ProfitRs'].max():+.1f}%")

        display = funded.copy()
        if pnl_rs is not None:
            display.insert(len(display.columns), "PnL_Rs", pnl_rs.round(0))
            display = display.sort_values("PnL_Rs")
        st.dataframe(display, use_container_width=True)

        if signals_count > len(funded):
            with st.expander(f"{signals_count - len(funded)} unfunded signals in this window"):
                st.caption(
                    "Signals that fired but the portfolio couldn't take - no free position slot, "
                    "insufficient cash, or (in risk mode) a heat cap shrank them below the minimum size."
                )
                st.dataframe(active[active["Funded"] != True], use_container_width=True)

    labels = list(trades_by_label.items())
    if len(labels) == 2:
        cols = st.columns(2)
        for col, (label, trades_df) in zip(cols, labels):
            with col:
                _render_one(label, trades_df)
    else:
        for label, trades_df in labels:
            _render_one(label, trades_df)


def render_value_at_risk():
    if not nonempty_csv_exists(BACKTEST_TRADES_PATH):
        st.info("Run a backtest from the Backtest tab first to see Value at Risk here.")
        return

    try:
        var_trades = pd.read_csv(BACKTEST_TRADES_PATH)

        vc1, vc2, vc3 = st.columns([2, 2, 1])
        with vc1:
            var_method_label = st.radio(
                "Method", ["Historical (default)", "Monte Carlo"], horizontal=True,
                help=strings.VAR_METHOD_HELP,
            )
            var_method = "historical" if var_method_label.startswith("Historical") else "monte_carlo"
        with vc2:
            var_confidences = st.multiselect(
                "Confidence level(s)", ["90%", "95%", "99%"], default=["95%", "99%"],
            )
        with vc3:
            var_horizon = st.number_input(
                "Horizon (trades)", min_value=1, value=1, step=1,
                disabled=(var_method == "historical"),
                help="Only used for Monte Carlo - compounds this many resampled trades per simulated path.",
            )

        confidence_levels = tuple(sorted(float(c.strip("%")) / 100 for c in var_confidences)) or (0.95,)

        portfolio_equity = None
        if nonempty_csv_exists(BACKTEST_PORTFOLIO_PATH):
            pf = pd.read_csv(BACKTEST_PORTFOLIO_PATH)
            if not pf.empty:
                portfolio_equity = float(pf["Equity"].iloc[-1])
        if portfolio_equity is None:
            portfolio_equity = float(var_trades["AllocatedCapital"].sum()) if "AllocatedCapital" in var_trades.columns else 100000.0

        var_report = backtest.compute_var_report(
            var_trades, portfolio_equity, confidence_levels=confidence_levels,
            method=var_method, n_simulations=2000, horizon_trades=int(var_horizon),
        )

        st.markdown(f"#### Portfolio VaR / CVaR ({var_method_label.split(' ')[0]}, on Rs.{portfolio_equity:,.0f})")
        var_cols = st.columns(len(confidence_levels))
        for col, conf in zip(var_cols, confidence_levels):
            stats = var_report["portfolio"][f"{conf * 100:.0f}"]
            col.metric(
                f"VaR {conf * 100:.0f}%",
                f"{stats['VaR_pct']:.1f}%" if pd.notna(stats["VaR_pct"]) else "N/A",
                f"Rs.{stats['VaR_rs']:,.0f} loss" if stats["VaR_rs"] is not None else None,
                delta_color="off",
                help=f"With {conf * 100:.0f}% confidence, a trade won't lose more than this. "
                     f"CVaR (worst-case average beyond that): {stats['CVaR_pct']:.1f}% "
                     f"(Rs.{stats['CVaR_rs']:,.0f})." if pd.notna(stats.get("CVaR_pct")) else None,
            )

        if not var_report["by_symbol"].empty:
            st.markdown("#### VaR by asset")
            st.caption(strings.VAR_BY_ASSET_CAPTION)
            st.dataframe(var_report["by_symbol"], use_container_width=True)
        else:
            st.caption("No symbol has enough closed trades yet for a per-asset VaR estimate.")

    except pd.errors.EmptyDataError:
        st.caption("No trade data from the last run.")


def render_risk_sizing_comparison():
    st.subheader("Risk-based sizing vs. equal-weight")
    st.caption(strings.RISK_TAB_CAPTION)

    have_both = nonempty_csv_exists(BACKTEST_PORTFOLIO_PATH) and nonempty_csv_exists(BACKTEST_PORTFOLIO_RISK_PATH)

    if not have_both:
        st.info(
            "Run a backtest from the Backtest tab with \"Also compare with risk-based sizing\" "
            "checked to see the comparison here."
        )
        return

    try:
        ew_portfolio = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
        risk_portfolio = pd.read_csv(BACKTEST_PORTFOLIO_RISK_PATH, parse_dates=["Date"])
        ew_trades = pd.read_csv(BACKTEST_TRADES_PATH)
        risk_trades = pd.read_csv(BACKTEST_TRADES_RISK_PATH)
        params = st.session_state.get("backtest_params", {})
        capital = params.get("initial_capital", ew_portfolio["Equity"].iloc[0])

        ew_stats = _perf_stats(ew_portfolio, capital)
        risk_stats = _perf_stats(risk_portfolio, capital)

        st.markdown("#### Headline comparison")
        hc1, hc2, hc3, hc4 = st.columns(4)
        hc1.metric(
            "Final equity", f"Rs.{risk_stats['final_equity']:,.0f}",
            f"{risk_stats['final_equity'] - ew_stats['final_equity']:+,.0f} vs equal-weight",
        )
        hc2.metric(
            "CAGR", f"{risk_stats['cagr_pct']:+.2f}%/yr" if risk_stats["cagr_pct"] is not None else "N/A",
            f"{(risk_stats['cagr_pct'] - ew_stats['cagr_pct']):+.2f}pp vs equal-weight"
            if risk_stats["cagr_pct"] is not None and ew_stats["cagr_pct"] is not None else None,
        )
        hc3.metric(
            "Max drawdown", f"{risk_stats['max_dd_pct']:.1f}%",
            f"{(risk_stats['max_dd_pct'] - ew_stats['max_dd_pct']):+.1f}pp vs equal-weight",
            delta_color="inverse",
        )
        funded_risk = int(risk_trades["Funded"].sum()) if "Funded" in risk_trades.columns else 0
        funded_ew = int(ew_trades["Funded"].sum()) if "Funded" in ew_trades.columns else 0
        hc4.metric("Funded trades", funded_risk, f"{funded_risk - funded_ew:+d} vs equal-weight")

        st.caption(
            f"Equal-weight: Rs.{ew_stats['final_equity']:,.0f} final "
            f"({ew_stats['cagr_pct']:+.2f}%/yr, {ew_stats['max_dd_pct']:.1f}% max DD) — "
            f"Risk-based: Rs.{risk_stats['final_equity']:,.0f} final "
            f"({risk_stats['cagr_pct']:+.2f}%/yr, {risk_stats['max_dd_pct']:.1f}% max DD)"
        )

        st.markdown("#### Equity curves")
        merged = pd.merge(
            ew_portfolio[["Date", "Equity"]].rename(columns={"Equity": "Equal-weight"}),
            risk_portfolio[["Date", "Equity"]].rename(columns={"Equity": "Risk-based"}),
            on="Date", how="outer",
        ).sort_values("Date").ffill()
        st.caption(strings.CHART_DRILLDOWN_HINT)
        compare_selection = selectable_line_chart(
            merged, ["Equal-weight", "Risk-based"], key="eq_chart_compare", y_axis_title="Equity (Rs.)"
        )
        render_period_drilldown(compare_selection, {"Equal-weight": ew_trades, "Risk-based": risk_trades})

        if os.path.exists(BACKTEST_RISK_INFO_PATH):
            with open(BACKTEST_RISK_INFO_PATH, "r", encoding="utf-8") as f:
                risk_info = json.load(f)
            st.markdown("#### Monte Carlo drawdown calibration")
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("P50 max drawdown", f"{risk_info.get('drawdown_p50', 0):.1f}%",
                       help="Median simulated max drawdown across bootstrapped paths - the throttle applies no penalty below this.")
            mc2.metric("P90 max drawdown", f"{risk_info.get('drawdown_p90', 0):.1f}%",
                       help="90th-percentile simulated max drawdown - sizing is throttled toward 0.25x once realized drawdown passes this.")
            mc3.metric("Risk of ruin", f"{risk_info.get('risk_of_ruin_pct', 0):.2f}%",
                       help="Fraction of bootstrapped paths where equity ever fell below the configured ruin threshold.")

        st.markdown("#### Portfolio heat over time (risk-based run)")
        st.caption(
            "Total capital-at-risk to each open position's initial stop, as a % of equity. "
            "Capped by the portfolio/sector heat caps set in the Backtest tab."
        )
        st.caption(strings.CHART_DRILLDOWN_HINT)
        heat_selection = selectable_line_chart(
            risk_portfolio, ["PortfolioHeatPct"], key="heat_chart", y_axis_title="Portfolio Heat (%)"
        )
        render_period_drilldown(heat_selection, {"Risk-based": risk_trades})

        if "Sector" in risk_trades.columns and risk_trades["Sector"].notna().any():
            st.markdown("#### Risk by sector (risk-based run)")
            sector_summary = risk_trades[risk_trades["Funded"] == True].groupby("Sector").agg(
                Trades=("Symbol", "count"),
                TotalDollarRiskAllocated=("DollarRiskAllocated", "sum"),
                AvgSectorHeatAtEntry=("SectorHeatAtEntry", "mean"),
            ).reset_index().sort_values("TotalDollarRiskAllocated", ascending=False)
            st.dataframe(
                sector_summary.style.format({
                    "TotalDollarRiskAllocated": "Rs.{:,.0f}", "AvgSectorHeatAtEntry": "{:.2f}%",
                }),
                use_container_width=True,
            )

        st.markdown("#### Per-trade sizing rationale (risk-based run)")
        only_capped = st.checkbox("Show only trades where a heat cap shrank the position", value=False)
        rationale_cols = [
            "Symbol", "EntryDate", "Sector", "RMultiple", "BaseRiskPct", "VolMultiplier",
            "BreadthMultiplier", "DrawdownThrottleMultiplier", "FinalRiskPct",
            "DollarRiskAllocated", "AllocatedCapital", "CapBreached", "SizingRationale",
        ]
        rationale_cols = [c for c in rationale_cols if c in risk_trades.columns]
        display_trades = risk_trades
        if only_capped and "CapBreached" in risk_trades.columns:
            display_trades = risk_trades[~risk_trades["CapBreached"].isin(["None", None]) & risk_trades["CapBreached"].notna()]
        st.dataframe(display_trades[rationale_cols], use_container_width=True)

    except pd.errors.EmptyDataError:
        st.caption("No comparable data from the last run.")


def render():
    if nonempty_csv_exists(BACKTEST_TRADES_PATH):
        try:
            edge_trades = pd.read_csv(BACKTEST_TRADES_PATH)
            edge_risk_info = None
            if os.path.exists(BACKTEST_RISK_INFO_PATH):
                with open(BACKTEST_RISK_INFO_PATH, "r", encoding="utf-8") as f:
                    edge_risk_info = json.load(f)
            render_edge_warning(edge_trades, edge_risk_info)
        except (pd.errors.EmptyDataError, json.JSONDecodeError):
            pass

    st.subheader("Value at Risk")
    st.caption(strings.VAR_SECTION_CAPTION)
    render_value_at_risk()

    st.divider()
    render_risk_sizing_comparison()
