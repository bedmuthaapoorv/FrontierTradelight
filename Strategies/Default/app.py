import streamlit as st

import strings
from tabs import discover_tabs

st.set_page_config(page_title="Frontier TradeLight", layout="wide")
st.title("Frontier TradeLight")
st.caption(strings.APP_DESCRIPTION)

tab_modules = discover_tabs()
streamlit_tabs = st.tabs([module.TITLE for module in tab_modules])

for streamlit_tab, module in zip(streamlit_tabs, tab_modules):
    with streamlit_tab:
        module.render()
