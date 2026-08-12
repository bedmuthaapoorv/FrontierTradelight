"""View the latest stock_report.csv produced by the Run tab."""

import os

import pandas as pd
import streamlit as st

from constants import REPORT_PATH

TITLE = "Results"
ORDER = 30


def render():
    st.subheader("stock_report.csv")
    if not os.path.exists(REPORT_PATH):
        st.info("No report yet. Run the screener from the Run tab first.")
        return

    df = pd.read_csv(REPORT_PATH)
    if "Passed" in df.columns:
        passed_only = st.checkbox("Show only stocks that passed all filters")
        if passed_only:
            df = df[df["Passed"] == True]
    st.dataframe(df, use_container_width=True)
    st.caption(f"{len(df)} rows")
