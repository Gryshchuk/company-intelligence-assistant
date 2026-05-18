"""Disambiguation candidates + 'tell me more' refinement input."""
import streamlit as st

from .. import state


def render() -> None:
    ss = st.session_state
    st.title("Which one did you mean?")
    st.caption(f"'{ss.pending_name}' could refer to several companies.")

    for i, cand in enumerate(ss.candidates):
        _render_candidate(i, cand)

    st.divider()
    _render_refinement_form()


def _render_candidate(i: int, cand: dict) -> None:
    with st.container(border=True):
        domain = cand.get("domain")
        category = cand.get("category")
        title = f"**{cand['name']}**"
        if category:
            title += f"  ·  _{category}_"
        st.markdown(title)
        st.write(cand["description"])
        if st.button("Pick this one", key=f"cand_{i}"):
            state.start_research_flow(cand["name"], domain, category)
            st.rerun()


def _render_refinement_form() -> None:
    st.markdown("**None of these?**")
    st.caption(
        "Add any details — what they do, where they're based, a domain "
        "or URL — and I'll search again."
    )
    with st.form("refinement", clear_on_submit=True):
        refinement = st.text_input(
            "Tell me more",
            placeholder=(
                "e.g. the astrology app at asknebula.com — or the "
                "cybersecurity firm acquired by Splunk"
            ),
            label_visibility="collapsed",
        )
        if st.form_submit_button("Search again", type="primary"):
            hint = refinement.strip()
            if hint:
                pending = st.session_state.pending_name
                state.start_disambiguation_flow(
                    f"{pending} — extra context from user: {hint}"
                )
                st.rerun()
