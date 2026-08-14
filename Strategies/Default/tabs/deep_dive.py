"""Deep Dive: interactive exploration of the last backtest, not just a
summary. Lets you pick which years to include and see the resulting CAGR
recompute live, plus a plain-language risk-adjusted return metric - meant
for building intuition about how much a single strong/weak year is
carrying the headline number, not for a fixed report."""

import pandas as pd
import streamlit as st

import strings
from constants import BACKTEST_PORTFOLIO_PATH
from ui_helpers import nonempty_csv_exists

TITLE = "Deep Dive"
ORDER = 52


def render():
    st.subheader("Explore the last backtest, year by year")
    st.caption(strings.DEEP_DIVE_CAPTION)

    if not nonempty_csv_exists(BACKTEST_PORTFOLIO_PATH):
        st.info(strings.DEEP_DIVE_NO_DATA_INFO)
        return

    try:
        portfolio_df = pd.read_csv(BACKTEST_PORTFOLIO_PATH, parse_dates=["Date"])
    except pd.errors.EmptyDataError:
        st.info(strings.DEEP_DIVE_NO_DATA_INFO)
        return

    if portfolio_df.empty:
        st.info(strings.DEEP_DIVE_NO_DATA_INFO)
        return

    yearly_returns = compute_yearly_returns(portfolio_df)
    if len(yearly_returns) < 2:
        st.info(strings.DEEP_DIVE_NOT_ENOUGH_YEARS_INFO)
        return

    render_year_picker(portfolio_df, yearly_returns)


def compute_yearly_returns(portfolio_df):
    """Returns {year: pct_return} for every calendar year present, using
    the same first-to-last equity method as the Backtest tab's Year-by-year
    breakdown, so the two stay consistent."""
    df = portfolio_df.copy()
    df["Year"] = df["Date"].dt.year
    grouped = df.groupby("Year")["Equity"].agg(["first", "last"])
    returns = (grouped["last"] - grouped["first"]) / grouped["first"] * 100
    return returns.to_dict()


def render_year_picker(portfolio_df, yearly_returns):
    years = sorted(yearly_returns)

    st.write("**Include which years?**")
    cols = st.columns(len(years))
    selected_years = []
    for col, year in zip(cols, years):
        with col:
            checked = st.checkbox(
                str(year), value=True, key=f"deep_dive_year_{year}",
                help=f"{yearly_returns[year]:+.1f}% this year"
            )
        if checked:
            selected_years.append(year)

    st.divider()

    all_stats = compute_stats(portfolio_df, yearly_returns, years, full_range=True)
    is_full_selection = set(selected_years) == set(years)
    selected_stats = (
        compute_stats(portfolio_df, yearly_returns, selected_years, full_range=is_full_selection)
        if selected_years else None
    )

    render_comparison(all_stats, selected_stats, len(years), len(selected_years))

    if selected_stats:
        st.divider()
        render_stitched_chart(portfolio_df, selected_years)


def compute_stats(portfolio_df, yearly_returns, years, full_range=False):
    """Compounds the given years' returns together (chronologically) into
    a CAGR, and computes the Return-to-Pain ratio (CAGR / worst drawdown)
    over the equity path stitched from just those years.

    When `full_range` is True (every available year is selected), uses the
    exact continuous first-to-last equity change instead of compounding
    per-calendar-year buckets - bucketing skips the actual day-to-day
    equity change across each Dec 31 -> Jan 1 boundary, which would
    otherwise make "all years selected" not quite match the Backtest tab's
    own CAGR for the same run. A genuine subset selection has no such
    single correct answer (it's an inherently hypothetical "what if"), so
    it still uses the bucketed approximation."""
    if not years:
        return None

    years = sorted(years)

    if full_range:
        first_equity = portfolio_df["Equity"].iloc[0]
        last_equity = portfolio_df["Equity"].iloc[-1]
        compounded = last_equity / first_equity
        years_elapsed = (portfolio_df["Date"].max() - portfolio_df["Date"].min()).days / 365.25
    else:
        compounded = 1.0
        for year in years:
            compounded *= (1 + yearly_returns[year] / 100)
        years_elapsed = elapsed_years(portfolio_df, years)

    total_return_pct = (compounded - 1) * 100
    cagr_pct = (compounded ** (1 / years_elapsed) - 1) * 100 if years_elapsed > 0 else 0.0

    stitched = stitch_equity(portfolio_df, years)
    running_max = stitched.cummax()
    drawdown_pct = (stitched - running_max) / running_max * 100
    max_dd_pct = drawdown_pct.min()

    return_to_pain = (cagr_pct / abs(max_dd_pct)) if max_dd_pct < 0 else None

    return {
        "years": years,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "years_elapsed": years_elapsed,
        "max_dd_pct": max_dd_pct,
        "return_to_pain": return_to_pain,
        "stitched": stitched,
    }


def elapsed_years(portfolio_df, years):
    """Actual elapsed time represented by the given years, in years - NOT
    just a count of calendar-year buckets, and NOT the gap between a
    year's first and last TRADE EVENT (portfolio_df only has a row when a
    trade opens or closes, so a year with no trades in its last few weeks
    would otherwise look "short" even though the strategy was evaluated
    every trading day). Instead, clips each year to true calendar-year
    boundaries (Jan 1 - Dec 31), further clipped only by the overall
    backtest's actual start/end date for the first/last year - a year
    fully inside the backtest range always counts as a full year."""
    overall_min = portfolio_df["Date"].min()
    overall_max = portfolio_df["Date"].max()

    total_days = 0
    for year in years:
        year_start = max(pd.Timestamp(year=year, month=1, day=1), overall_min)
        year_end = min(pd.Timestamp(year=year, month=12, day=31), overall_max)
        if year_end < year_start:
            continue
        total_days += (year_end - year_start).days + 1

    return total_days / 365.25


def stitch_equity(portfolio_df, years):
    """Concatenates each selected year's actual daily equity path (not
    just its start/end), rescaled so each year picks up where the previous
    selected year left off - preserves real intra-year volatility for the
    drawdown calculation instead of pretending each year was a straight
    line from start to end."""
    df = portfolio_df.copy()
    df["Year"] = df["Date"].dt.year

    pieces = []
    running_value = 100.0
    for year in sorted(years):
        year_df = df[df["Year"] == year].sort_values("Date")
        if year_df.empty:
            continue
        year_equity = year_df["Equity"].values
        rescaled = year_equity / year_equity[0] * running_value
        pieces.append(pd.Series(rescaled))
        running_value = rescaled[-1]

    return pd.concat(pieces, ignore_index=True)


def render_comparison(all_stats, selected_stats, total_years, selected_count):
    if selected_count == total_years:
        st.caption(strings.DEEP_DIVE_ALL_YEARS_CAPTION)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**All years**")
        render_stat_block(all_stats)

    with col2:
        st.markdown(f"**Selected ({selected_count} of {total_years} years)**")
        if selected_stats is None:
            st.caption(strings.DEEP_DIVE_NO_YEARS_SELECTED_CAPTION)
        else:
            render_stat_block(selected_stats)


def render_stat_block(stats):
    is_partial_year = stats["years_elapsed"] < 1
    cagr_label = "CAGR (extrapolated!)" if is_partial_year else "CAGR"

    st.metric("Total return", f"{stats['total_return_pct']:+.2f}%")
    st.metric(cagr_label, f"{stats['cagr_pct']:+.2f}%/yr", help=strings.DEEP_DIVE_PARTIAL_YEAR_HELP if is_partial_year else None)
    if is_partial_year:
        st.caption(strings.DEEP_DIVE_PARTIAL_YEAR_CAPTION.format(months=stats["years_elapsed"] * 12))
    st.metric("Worst drawdown", f"{stats['max_dd_pct']:.1f}%")
    if stats["return_to_pain"] is not None:
        st.metric("Return-to-Pain ratio", f"{stats['return_to_pain']:.2f}", help=strings.RETURN_TO_PAIN_HELP)
    else:
        st.metric("Return-to-Pain ratio", "N/A", help=strings.RETURN_TO_PAIN_HELP)


def render_stitched_chart(portfolio_df, selected_years):
    st.caption(strings.DEEP_DIVE_STITCHED_CHART_CAPTION)
    stitched = stitch_equity(portfolio_df, selected_years)
    st.line_chart(stitched)
