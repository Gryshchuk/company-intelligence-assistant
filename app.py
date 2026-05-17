"""Streamlit entry — all the actual UI lives in company_intel.ui."""
import sys
from pathlib import Path

# Make src/ importable without needing an editable install — useful on
# hosts like Streamlit Community Cloud that only run `pip install -r
# requirements.txt`. Locally the editable install still wins.
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st  # noqa: E402

from company_intel.ui import log_pane, sidebar, state, theme, views  # noqa: E402

st.set_page_config(
    page_title="Company Intel",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme.inject()
state.init()
sidebar.render()

main_col, right_col = st.columns([3, 2], gap="large")
with right_col:
    log_pane.render()
with main_col:
    views.render(st.session_state.view)
