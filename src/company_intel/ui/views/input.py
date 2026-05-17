"""Initial 'enter a company name' form."""
import streamlit as st

from .. import state


def render() -> None:
    st.title("Research a company")
    with st.form("research_form", clear_on_submit=False):
        name = st.text_input(
            "Company name",
            placeholder="e.g. Figma, Spotify, Airbnb",
        )
        submitted = st.form_submit_button("Research", type="primary")
    if submitted and name.strip():
        state.start_disambiguation_flow(name.strip())
        st.rerun()
