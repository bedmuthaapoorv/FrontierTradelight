"""Generate the screening logic from rules.md, then run it against the universe."""

import streamlit as st

import strings
from ui_helpers import run_script_with_feedback

TITLE = "Run"
ORDER = 20


def render():
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
