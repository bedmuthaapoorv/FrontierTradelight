"""Edit the exit strategy and check current holdings against it."""

import os

import pandas as pd
import streamlit as st

import strings
from constants import EXIT_BACKUP_DIR, EXIT_RULES_PATH, HOLDINGS_PATH, SELL_REPORT_PATH
from ui_helpers import (
    backup_restore_modal,
    editable_markdown,
    load_into_session,
    nonempty_csv_exists,
    run_script,
    run_script_with_feedback,
    save_with_backup,
)

TITLE = "Sell"
ORDER = 40


def render():
    st.subheader("Check your holdings against the exit strategy")
    st.caption(strings.SELL_TAB_CAPTION)

    render_exit_strategy_editor()

    st.divider()

    render_holdings_editor()


def render_exit_strategy_editor():
    st.subheader("Exit strategy")
    st.caption(strings.EXIT_STRATEGY_CAPTION)

    load_into_session("exit_rules_content", EXIT_RULES_PATH)

    with st.expander("Exit strategy rules", expanded=False):
        exit_gen_col, exit_save_col = st.columns(2)
        with exit_gen_col:
            run_script_with_feedback(
                "Generate exit strategy",
                "generate_exit_strategy.py",
                "Generating exit logic...",
                "generated_exit_strategy.py updated.",
            )

        edited_exit_rules = editable_markdown("exit_rules_content", "Exit strategy rules", 300)

        with exit_save_col:
            if st.button("Save exit_rules.md"):
                save_with_backup(
                    EXIT_RULES_PATH, EXIT_BACKUP_DIR, "exit_rules", "ExitRules_backup",
                    edited_exit_rules, "exit_rules_content",
                )
                st.success("Saved exit_rules.md")

    backup_restore_modal(
        modal_title="Load a previous exit strategy",
        open_button_label="Load a previous exit strategy",
        path=EXIT_RULES_PATH,
        backup_dir=EXIT_BACKUP_DIR,
        backup_suffix="exit_rules",
        backup_label="ExitRules_backup",
        session_key="exit_rules_content",
        no_backups_caption=strings.NO_EXIT_BACKUPS_CAPTION,
        selectbox_label="Choose a backed-up exit strategy",
        overwrite_label_prefix="Overwrite exit_rules.md with",
        success_message_prefix="exit_rules.md overwritten with",
    )


def render_holdings_editor():
    st.subheader("Your holdings")
    st.caption(strings.HOLDINGS_EDITOR_CAPTION)

    if "holdings_df" not in st.session_state:
        if os.path.exists(HOLDINGS_PATH):
            st.session_state.holdings_df = pd.read_csv(HOLDINGS_PATH, parse_dates=["EntryDate"])
        else:
            st.session_state.holdings_df = pd.DataFrame(
                columns=["Symbol", "EntryPrice", "EntryDate", "CurrentPrice"]
            )

    if "CurrentPrice" not in st.session_state.holdings_df.columns:
        st.session_state.holdings_df["CurrentPrice"] = pd.NA

    # Note: st.session_state.holdings_df is only ever set above (the
    # initial load) - it must NOT be reassigned to the editor's output
    # below. data_editor tracks its own per-cell edit diff internally
    # under `key`; feeding that same output back in as next rerun's
    # `value` replays the diff against already-edited data, causing a
    # one-rerun revert-then-reapply flicker on every edit.
    holdings_editor = st.data_editor(
        st.session_state.holdings_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Symbol": st.column_config.TextColumn(required=True),
            "EntryPrice": st.column_config.NumberColumn(required=True, min_value=0.0),
            "EntryDate": st.column_config.DateColumn(required=True),
            "CurrentPrice": st.column_config.NumberColumn(
                required=False, min_value=0.0, help=strings.CURRENT_PRICE_HELP
            ),
        },
        key="holdings_editor",
    )

    holdings_ready = holdings_editor.dropna(subset=["Symbol", "EntryPrice", "EntryDate"])

    if not holdings_ready.equals(st.session_state.get("holdings_last_saved")):
        holdings_ready.to_csv(HOLDINGS_PATH, index=False)
        st.session_state.holdings_last_saved = holdings_ready.copy()

    if st.button("Check exit signals", disabled=holdings_ready.empty):
        with st.spinner("Checking exit signals..."):
            code = run_script("sell_screener.py", ["--holdings", HOLDINGS_PATH, "--out", SELL_REPORT_PATH])
        if code == 0:
            st.success("Sell check complete.")
        else:
            st.error(f"sell_screener.py exited with code {code}.")

    if holdings_ready.empty:
        st.caption(strings.NO_HOLDINGS_CAPTION)

    render_recommendations()


def render_recommendations():
    if not nonempty_csv_exists(SELL_REPORT_PATH):
        return

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
