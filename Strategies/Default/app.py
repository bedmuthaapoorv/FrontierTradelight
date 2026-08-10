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
    HOLDINGS_PATH,
    SELL_REPORT_PATH,
)
from backup_utils import backup_markdown, list_backups
import strings

st.set_page_config(page_title="Frontier TradeLight", layout="wide")
st.title("Frontier TradeLight")
st.caption(strings.APP_DESCRIPTION)

tab_rules, tab_run, tab_results, tab_sell, tab_backtest = st.tabs(
    ["Rules", "Run", "Results", "Sell", "Backtest"]
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
