import os
import subprocess
import sys

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
)
from backup_utils import backup_markdown, list_backups
import strings

st.set_page_config(page_title="Frontier TradeLight", layout="wide")
st.title("Frontier TradeLight")
st.caption(strings.APP_DESCRIPTION)

tab_rules, tab_run, tab_results, tab_backtest = st.tabs(["Rules", "Run", "Results", "Backtest"])


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


with tab_rules:
    st.subheader("Edit rules.md")

    guide_path = os.path.join(APP_DIR, "RULES_GUIDE.md")
    if os.path.exists(guide_path):
        with st.expander("New to rules.md? Read the guide"):
            with open(guide_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())

    if "rules_content" not in st.session_state:
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            st.session_state.rules_content = f.read()

    edited = st.text_area(
        "Strategy rules",
        value=st.session_state.rules_content,
        height=600,
        label_visibility="collapsed",
    )

    if st.button("Save rules.md"):
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            previous_content = f.read()
        if previous_content.strip():
            backup_name = backup_markdown(previous_content, BACKUP_DIR, "rules")
            st.info(f"Backed up previous rules.md to Rules_backup/{backup_name}")

        with open(RULES_PATH, "w", encoding="utf-8") as f:
            f.write(edited)
        st.session_state.rules_content = edited
        st.success("Saved rules.md")

    st.divider()

    st.subheader("Load a previous strategy")
    backups = list_backups(BACKUP_DIR)
    if not backups:
        st.caption(strings.NO_RULES_BACKUPS_CAPTION)
    else:
        selected_backup = st.selectbox("Choose a backed-up strategy", backups)
        backup_path = os.path.join(BACKUP_DIR, selected_backup)
        with open(backup_path, "r", encoding="utf-8") as f:
            backup_content = f.read()

        with st.expander(f"Preview {selected_backup}"):
            st.code(backup_content, language="markdown")

        if st.button(f"Overwrite rules.md with {selected_backup}"):
            with open(RULES_PATH, "r", encoding="utf-8") as f:
                current_content = f.read()
            if current_content.strip() and current_content != backup_content:
                backup_name = backup_markdown(current_content, BACKUP_DIR, "rules")
                st.info(f"Backed up previous rules.md to Rules_backup/{backup_name}")

            with open(RULES_PATH, "w", encoding="utf-8") as f:
                f.write(backup_content)
            st.session_state.rules_content = backup_content
            st.success(f"rules.md overwritten with {selected_backup}")
            st.rerun()

with tab_run:
    st.subheader("Generate screening logic")
    st.caption(strings.GENERATE_SCREENER_CAPTION)
    if st.button("Run generate_screener.py"):
        with st.spinner("Generating screening logic..."):
            code = run_script("generate_screener.py")
        if code == 0:
            st.success("generated_rules.py updated.")
        else:
            st.error(f"generate_screener.py exited with code {code}.")

    st.divider()

    st.subheader("Run the screener")
    st.caption(strings.RUN_SCREENER_CAPTION)
    if st.button("Run stock_screener.py"):
        with st.spinner("Running screener..."):
            code = run_script("stock_screener.py")
        if code == 0:
            st.success("stock_report.csv updated. See the Results tab.")
        else:
            st.error(f"stock_screener.py exited with code {code}.")

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

@st.fragment(run_every=2)
def show_backtest_progress():
    """Polls the running backtest's log file and process status every 2s,
    without blocking the rest of the page (so the Stop button stays clickable)."""
    process = st.session_state.get("backtest_process")
    if process is None:
        return

    if os.path.exists(BACKTEST_LOG_PATH):
        with open(BACKTEST_LOG_PATH, "r", encoding="utf-8") as f:
            log_content = f.read()
        st.code(log_content[-3000:] or "Starting...")

    if process.poll() is not None:
        st.session_state.backtest_running = False
        if process.returncode == 0:
            st.success("Backtest complete. See results below.")
        else:
            st.error(f"backtest.py exited with code {process.returncode}.")
        st.rerun()


with tab_backtest:
    st.subheader("Backtest the current strategy")
    st.caption(strings.BACKTEST_TAB_CAPTION)

    backtest_guide_path = os.path.join(APP_DIR, "BACKTEST_GUIDE.md")
    if os.path.exists(backtest_guide_path):
        with st.expander("New to backtesting? Read the guide"):
            with open(backtest_guide_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())

    st.subheader("Exit strategy")
    st.caption(strings.EXIT_STRATEGY_CAPTION)

    if "exit_rules_content" not in st.session_state:
        with open(EXIT_RULES_PATH, "r", encoding="utf-8") as f:
            st.session_state.exit_rules_content = f.read()

    edited_exit_rules = st.text_area(
        "Exit strategy rules",
        value=st.session_state.exit_rules_content,
        height=300,
        label_visibility="collapsed",
    )

    exit_save_col, exit_gen_col = st.columns(2)
    with exit_save_col:
        if st.button("Save exit_rules.md"):
            with open(EXIT_RULES_PATH, "r", encoding="utf-8") as f:
                previous_content = f.read()
            if previous_content.strip():
                backup_name = backup_markdown(previous_content, EXIT_BACKUP_DIR, "exit_rules")
                st.info(f"Backed up previous exit_rules.md to ExitRules_backup/{backup_name}")

            with open(EXIT_RULES_PATH, "w", encoding="utf-8") as f:
                f.write(edited_exit_rules)
            st.session_state.exit_rules_content = edited_exit_rules
            st.success("Saved exit_rules.md")

    with exit_gen_col:
        if st.button("Generate exit strategy"):
            with st.spinner("Generating exit logic..."):
                code = run_script("generate_exit_strategy.py")
            if code == 0:
                st.success("generated_exit_strategy.py updated.")
            else:
                st.error(f"generate_exit_strategy.py exited with code {code}.")

    with st.expander("Load a previous exit strategy"):
        exit_backups = list_backups(EXIT_BACKUP_DIR)
        if not exit_backups:
            st.caption(strings.NO_EXIT_BACKUPS_CAPTION)
        else:
            selected_exit_backup = st.selectbox("Choose a backed-up exit strategy", exit_backups)
            exit_backup_path = os.path.join(EXIT_BACKUP_DIR, selected_exit_backup)
            with open(exit_backup_path, "r", encoding="utf-8") as f:
                exit_backup_content = f.read()

            st.code(exit_backup_content, language="markdown")

            if st.button(f"Overwrite exit_rules.md with {selected_exit_backup}"):
                with open(EXIT_RULES_PATH, "r", encoding="utf-8") as f:
                    current_content = f.read()
                if current_content.strip() and current_content != exit_backup_content:
                    backup_name = backup_markdown(current_content, EXIT_BACKUP_DIR, "exit_rules")
                    st.info(f"Backed up previous exit_rules.md to ExitRules_backup/{backup_name}")

                with open(EXIT_RULES_PATH, "w", encoding="utf-8") as f:
                    f.write(exit_backup_content)
                st.session_state.exit_rules_content = exit_backup_content
                st.success(f"exit_rules.md overwritten with {selected_exit_backup}")
                st.rerun()

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
            ]

            log_file = open(BACKTEST_LOG_PATH, "w")
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

    if os.path.exists(BACKTEST_PORTFOLIO_PATH) and os.path.getsize(BACKTEST_PORTFOLIO_PATH) > 0:
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

                st.line_chart(portfolio_df.set_index("Date")["Equity"])

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

    if os.path.exists(BACKTEST_SUMMARY_PATH) and os.path.getsize(BACKTEST_SUMMARY_PATH) > 0:
        st.divider()
        st.subheader("Summary by ClosenessScore bucket")
        try:
            st.dataframe(pd.read_csv(BACKTEST_SUMMARY_PATH), use_container_width=True)
        except pd.errors.EmptyDataError:
            st.caption("No trades were simulated in the last run, so there's no summary to bucket.")

    if os.path.exists(BACKTEST_TRADES_PATH) and os.path.getsize(BACKTEST_TRADES_PATH) > 0:
        st.subheader("Individual trades")
        try:
            st.dataframe(pd.read_csv(BACKTEST_TRADES_PATH), use_container_width=True)
        except pd.errors.EmptyDataError:
            st.caption("No trades were simulated in the last run.")
