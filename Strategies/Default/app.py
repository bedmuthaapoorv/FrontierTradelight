import json
import os
import subprocess
import sys

import altair as alt
import pandas as pd
import streamlit as st

import backtest
from constants import (
    APP_DIR,
    RULES_PATH,
    REPORT_PATH,
    BACKUP_DIR,
    EXIT_RULES_PATH,
    EXIT_BACKUP_DIR,
    BACKTEST_TRADES_PATH,
    BACKTEST_SUMMARY_PATH,
    BACKTEST_PORTFOLIO_PATH,
    BACKTEST_LOG_PATH,
    BACKTEST_TRADES_RISK_PATH,
    BACKTEST_SUMMARY_RISK_PATH,
    BACKTEST_PORTFOLIO_RISK_PATH,
    BACKTEST_RISK_INFO_PATH,
    BACKTEST_RISK_LOG_PATH,
    HOLDINGS_PATH,
    SELL_REPORT_PATH,
)
from backup_utils import backup_markdown, list_backups
import strings

st.set_page_config(page_title="Frontier TradeLight", layout="wide")
st.title("Frontier TradeLight")
st.caption(strings.APP_DESCRIPTION)

tab_rules, tab_run, tab_results, tab_sell, tab_backtest, tab_risk = st.tabs(
    ["Rules", "Run", "Results", "Sell", "Backtest", "Risk"]
)


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_script(script_name, args=None):
    """Run a script in Default/ and stream its output."""
    process = subprocess.Popen(
        [sys.executable, script_name, *(args or [])],
        cwd=APP_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output_box = st.empty()
    lines = []
    for line in process.stdout:
        lines.append(line.rstrip())
        output_box.code("\n".join(lines[-200:]))
    process.wait()
    return process.returncode


def run_script_with_feedback(button_label, script_name, spinner_text, success_text):
    if st.button(button_label):
        with st.spinner(spinner_text):
            code = run_script(script_name)
        if code == 0:
            st.success(success_text)
        else:
            st.error(f"{script_name} exited with code {code}.")


def show_guide(filename, expander_label):
    guide_path = os.path.join(APP_DIR, filename)
    if os.path.exists(guide_path):
        with st.expander(expander_label):
            st.markdown(read_text(guide_path))


def nonempty_csv_exists(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def load_into_session(session_key, path):
    if session_key not in st.session_state:
        st.session_state[session_key] = read_text(path)


def save_with_backup(path, backup_dir, suffix, backup_label, new_content, session_key):
    """Back up the file's current contents, then overwrite it with new_content."""
    previous_content = read_text(path)
    if previous_content.strip():
        backup_name = backup_markdown(previous_content, backup_dir, suffix)
        st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

    write_text(path, new_content)
    st.session_state[session_key] = new_content


def strategy_editor(*, session_key, path, guide_filename, guide_label, backup_dir,
                     backup_suffix, backup_label, text_area_label, text_area_height,
                     save_button_label, save_success_message, no_backups_caption):
    """Renders the edit/save/restore workflow shared by rules.md and exit_rules.md."""
    show_guide(guide_filename, guide_label)
    load_into_session(session_key, path)

    edited = st.text_area(
        text_area_label,
        value=st.session_state[session_key],
        height=text_area_height,
        label_visibility="collapsed",
    )

    if st.button(save_button_label):
        save_with_backup(path, backup_dir, backup_suffix, backup_label, edited, session_key)
        st.success(save_success_message)

    return edited


def backup_restore_section(*, path, backup_dir, backup_suffix, backup_label,
                            session_key, no_backups_caption, selectbox_label,
                            overwrite_label_prefix, success_message_prefix,
                            show_in_expander=False):
    backups = list_backups(backup_dir)
    if not backups:
        st.caption(no_backups_caption)
        return

    selected_backup = st.selectbox(selectbox_label, backups)
    backup_content = read_text(os.path.join(backup_dir, selected_backup))

    if show_in_expander:
        st.code(backup_content, language="markdown")
    else:
        with st.expander(f"Preview {selected_backup}"):
            st.code(backup_content, language="markdown")

    if st.button(f"{overwrite_label_prefix} {selected_backup}"):
        current_content = read_text(path)
        if current_content.strip() and current_content != backup_content:
            backup_name = backup_markdown(current_content, backup_dir, backup_suffix)
            st.info(f"Backed up previous {os.path.basename(path)} to {backup_label}/{backup_name}")

        write_text(path, backup_content)
        st.session_state[session_key] = backup_content
        st.success(f"{success_message_prefix} {selected_backup}")
        st.rerun()


with tab_rules:
    st.subheader("Edit rules.md")

    strategy_editor(
        session_key="rules_content",
        path=RULES_PATH,
        guide_filename="RULES_GUIDE.md",
        guide_label="New to rules.md? Read the guide",
        backup_dir=BACKUP_DIR,
        backup_suffix="rules",
        backup_label="Rules_backup",
        text_area_label="Strategy rules",
        text_area_height=600,
        save_button_label="Save rules.md",
        save_success_message="Saved rules.md",
        no_backups_caption=strings.NO_RULES_BACKUPS_CAPTION,
    )

    st.divider()

    st.subheader("Load a previous strategy")
    backup_restore_section(
        path=RULES_PATH,
        backup_dir=BACKUP_DIR,
        backup_suffix="rules",
        backup_label="Rules_backup",
        session_key="rules_content",
        no_backups_caption=strings.NO_RULES_BACKUPS_CAPTION,
        selectbox_label="Choose a backed-up strategy",
        overwrite_label_prefix="Overwrite rules.md with",
        success_message_prefix="rules.md overwritten with",
    )

with tab_run:
    st.subheader("Generate screening logic")
    st.caption(strings.GENERATE_SCREENER_CAPTION)
    run_script_with_feedback(
        "Run generate_screener.py",
        "generate_screener.py",
        "Generating screening logic...",
        "generated_rules.py updated.",
    )

    st.divider()

    st.subheader("Run the screener")
    st.caption(strings.RUN_SCREENER_CAPTION)
    run_script_with_feedback(
        "Run stock_screener.py",
        "stock_screener.py",
        "Running screener...",
        "stock_report.csv updated. See the Results tab.",
    )

with tab_results:
    st.subheader("stock_report.csv")
    if not os.path.exists(REPORT_PATH):
        st.info("No report yet. Run the screener from the Run tab first.")
    else:
        df = pd.read_csv(REPORT_PATH)
        if "Passed" in df.columns:
            passed_only = st.checkbox("Show only stocks that passed all filters")
            if passed_only:
                df = df[df["Passed"] == True]
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} rows")

with tab_sell:
    st.subheader("Check your holdings against the exit strategy")
    st.caption(strings.SELL_TAB_CAPTION)
    st.caption(strings.HOLDINGS_EDITOR_CAPTION)

    if "holdings_df" not in st.session_state:
        if os.path.exists(HOLDINGS_PATH):
            st.session_state.holdings_df = pd.read_csv(HOLDINGS_PATH, parse_dates=["EntryDate"])
        else:
            st.session_state.holdings_df = pd.DataFrame(
                columns=["Symbol", "EntryPrice", "EntryDate"]
            )

    holdings_editor = st.data_editor(
        st.session_state.holdings_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Symbol": st.column_config.TextColumn(required=True),
            "EntryPrice": st.column_config.NumberColumn(required=True, min_value=0.0),
            "EntryDate": st.column_config.DateColumn(required=True),
        },
        key="holdings_editor",
    )

    holdings_ready = holdings_editor.dropna(subset=["Symbol", "EntryPrice", "EntryDate"])

    if not holdings_editor.equals(st.session_state.holdings_df):
        holdings_ready.to_csv(HOLDINGS_PATH, index=False)
        st.session_state.holdings_df = holdings_editor

    if st.button("Check exit signals", disabled=holdings_ready.empty):
        with st.spinner("Checking exit signals..."):
            code = run_script("sell_screener.py", ["--holdings", HOLDINGS_PATH, "--out", SELL_REPORT_PATH])
        if code == 0:
            st.success("Sell check complete.")
        else:
            st.error(f"sell_screener.py exited with code {code}.")

    if holdings_ready.empty:
        st.caption(strings.NO_HOLDINGS_CAPTION)

    if nonempty_csv_exists(SELL_REPORT_PATH):
        st.divider()
        st.subheader("Recommendations")
        try:
            sell_df = pd.read_csv(SELL_REPORT_PATH)

            def highlight_recommendation(row):
                color = {"SELL": "#ffcccc", "HOLD": "#ccffcc"}.get(row["Recommendation"], "")
                return [f"background-color: {color}"] * len(row)

            st.dataframe(
                sell_df.style.apply(highlight_recommendation, axis=1),
                use_container_width=True,
            )
        except pd.errors.EmptyDataError:
            st.caption("No results from the last check.")

def run_risk_comparison():
    """Blocking: re-simulates portfolio sizing in sizing_mode='risk' on top
    of the *same* trades just produced by the equal-weight run (via
    --trades-in), so both curves reflect identical signals and only sizing
    differs. Cheap relative to the main run - skips signal generation
    entirely, reusing the cached price history."""
    params = st.session_state.get("backtest_params")
    if not params:
        return False

    risk_args = [
        "--start", params["start"], "--end", params["end"],
        "--initial-capital", str(params["initial_capital"]),
        "--max-positions", str(params["max_positions"]),
        "--trades-in", BACKTEST_TRADES_PATH,
        "--sizing-mode", "risk",
        "--trades-out", BACKTEST_TRADES_RISK_PATH,
        "--summary-out", BACKTEST_SUMMARY_RISK_PATH,
        "--portfolio-out", BACKTEST_PORTFOLIO_RISK_PATH,
        "--risk-info-out", BACKTEST_RISK_INFO_PATH,
        "--half-kelly-cap-pct", str(params["half_kelly_cap_pct"]),
        "--min-trades-for-kelly", str(params["min_trades_for_kelly"]),
        "--default-risk-pct", str(params["default_risk_pct"]),
        "--portfolio-heat-cap-pct", str(params["portfolio_heat_cap_pct"]),
        "--sector-heat-cap-pct", str(params["sector_heat_cap_pct"]),
        "--mc-simulations", str(params["mc_simulations"]),
        "--mc-ruin-threshold-pct", str(params["mc_ruin_threshold_pct"]),
    ]
    with open(BACKTEST_RISK_LOG_PATH, "w", encoding="utf-8") as log_file:
        result = subprocess.run(
            [sys.executable, "backtest.py", *risk_args],
            cwd=APP_DIR, stdout=log_file, stderr=subprocess.STDOUT,
        )
    return result.returncode == 0


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
            if st.session_state.get("compare_risk_sizing") and not st.session_state.get("risk_compare_done"):
                with st.spinner("Comparing against risk-based sizing (reusing the same trades)..."):
                    ok = run_risk_comparison()
                st.session_state.risk_compare_done = True
                if ok:
                    st.success("Risk-based sizing comparison complete. See the Risk tab.")
                else:
                    st.error(f"Risk comparison run failed - see {os.path.basename(BACKTEST_RISK_LOG_PATH)}.")
        else:
            st.error(f"backtest.py exited with code {process.returncode}.")
        st.rerun()


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


with tab_backtest:
    st.subheader("Backtest the current strategy")
    st.caption(strings.BACKTEST_TAB_CAPTION)

    show_guide("BACKTEST_GUIDE.md", "New to backtesting? Read the guide")

    st.subheader("Exit strategy")
    st.caption(strings.EXIT_STRATEGY_CAPTION)

    load_into_session("exit_rules_content", EXIT_RULES_PATH)

    edited_exit_rules = st.text_area(
        "Exit strategy rules",
        value=st.session_state.exit_rules_content,
        height=300,
        label_visibility="collapsed",
    )

    exit_save_col, exit_gen_col = st.columns(2)
    with exit_save_col:
        if st.button("Save exit_rules.md"):
            save_with_backup(
                EXIT_RULES_PATH, EXIT_BACKUP_DIR, "exit_rules", "ExitRules_backup",
                edited_exit_rules, "exit_rules_content",
            )
            st.success("Saved exit_rules.md")

    with exit_gen_col:
        run_script_with_feedback(
            "Generate exit strategy",
            "generate_exit_strategy.py",
            "Generating exit logic...",
            "generated_exit_strategy.py updated.",
        )

    with st.expander("Load a previous exit strategy"):
        backup_restore_section(
            path=EXIT_RULES_PATH,
            backup_dir=EXIT_BACKUP_DIR,
            backup_suffix="exit_rules",
            backup_label="ExitRules_backup",
            session_key="exit_rules_content",
            no_backups_caption=strings.NO_EXIT_BACKUPS_CAPTION,
            selectbox_label="Choose a backed-up exit strategy",
            overwrite_label_prefix="Overwrite exit_rules.md with",
            success_message_prefix="exit_rules.md overwritten with",
            show_in_expander=True,
        )

    st.divider()

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

    compare_risk_sizing = st.checkbox(
        "Also compare with risk-based sizing (half-Kelly + heat caps)",
        value=st.session_state.get("compare_risk_sizing", False),
        help=strings.COMPARE_RISK_SIZING_HELP,
    )

    with st.expander("Risk sizing parameters"):
        rc1, rc2 = st.columns(2)
        with rc1:
            half_kelly_cap_pct = st.number_input("Half-Kelly cap (% risk/trade)", min_value=0.1, value=2.0, step=0.1)
            min_trades_for_kelly = st.number_input("Min closed trades before Kelly kicks in", min_value=1, value=20, step=1)
            default_risk_pct = st.number_input("Default/cold-start risk % per trade", min_value=0.1, value=1.0, step=0.1)
            mc_simulations = st.number_input("Monte Carlo simulations", min_value=100, value=2000, step=100)
        with rc2:
            portfolio_heat_cap_pct = st.number_input("Portfolio heat cap (%)", min_value=0.5, value=6.0, step=0.5)
            sector_heat_cap_pct = st.number_input("Sector heat cap (%)", min_value=0.5, value=3.0, step=0.5)
            mc_ruin_threshold_pct = st.number_input("Ruin threshold (% equity drop)", max_value=-1.0, value=-50.0, step=5.0)
        st.caption(strings.RISK_PARAMS_CAPTION)

    is_running = st.session_state.get("backtest_running", False)

    if start_date < end_date and not is_running:
        try:
            est = backtest.estimate_runtime(start_date, end_date)
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
                "--sizing-mode", "equal_weight",
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
            st.session_state.compare_risk_sizing = compare_risk_sizing
            st.session_state.risk_compare_done = False
            st.session_state.backtest_params = {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "initial_capital": initial_capital,
                "max_positions": int(max_positions),
                "half_kelly_cap_pct": half_kelly_cap_pct,
                "min_trades_for_kelly": int(min_trades_for_kelly),
                "default_risk_pct": default_risk_pct,
                "portfolio_heat_cap_pct": portfolio_heat_cap_pct,
                "sector_heat_cap_pct": sector_heat_cap_pct,
                "mc_simulations": int(mc_simulations),
                "mc_ruin_threshold_pct": mc_ruin_threshold_pct,
            }
            st.rerun()

    if stop_clicked:
        process = st.session_state.get("backtest_process")
        if process is not None and process.poll() is None:
            process.terminate()
        st.session_state.backtest_running = False
        st.warning(strings.BACKTEST_STOPPED_WARNING)

    if is_running:
        show_backtest_progress()

    if nonempty_csv_exists(BACKTEST_PORTFOLIO_PATH):
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

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Final equity", f"Rs.{final_equity:,.0f}", f"{total_return_pct:+.2f}% total")
                m2.metric("CAGR", cagr_display, help=strings.CAGR_HELP)
                m3.metric("Max drawdown", f"{max_dd_pct:.1f}%", help=strings.MAX_DRAWDOWN_HELP)
                m4.metric("Funded trades", funded_count)
                m5.metric("Skipped (no capital)", skipped_count)

                st.caption(strings.CHART_DRILLDOWN_HINT)
                eq_selection = selectable_line_chart(
                    portfolio_df, ["Equity"], key="eq_chart_backtest", y_axis_title="Equity (Rs.)"
                )
                render_period_drilldown(eq_selection, {"Equal-weight": trades_for_capital})

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


with tab_risk:
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

    if not nonempty_csv_exists(BACKTEST_TRADES_PATH):
        st.info("Run a backtest from the Backtest tab first to see Value at Risk here.")
    else:
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

    st.divider()
    st.subheader("Risk-based sizing vs. equal-weight")
    st.caption(strings.RISK_TAB_CAPTION)

    have_both = nonempty_csv_exists(BACKTEST_PORTFOLIO_PATH) and nonempty_csv_exists(BACKTEST_PORTFOLIO_RISK_PATH)

    if not have_both:
        st.info(
            "Run a backtest from the Backtest tab with \"Also compare with risk-based sizing\" "
            "checked to see the comparison here."
        )
    else:
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
