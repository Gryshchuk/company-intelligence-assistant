"""Waiting screen while the disambiguation agent runs.

Owns the polling fragment that watches the task and routes onward:
- clear=True  -> kick off research
- clear=False -> show the candidate cards
- error       -> back-to-input fallback
"""
import streamlit as st

from ...eventbus import get_task
from .. import state


def render() -> None:
    st.title("Checking the name…")
    st.caption(
        f"Looking up '{st.session_state.pending_name}'. "
        "Watch the right panel for progress."
    )
    _poll()


@st.fragment(run_every=1)
def _poll() -> None:
    ss = st.session_state
    tid = ss.get("disambig_task_id")
    if not tid:
        return
    t = get_task(tid)
    if t is None or t.status == "running":
        return
    if t.status == "error":
        st.error(f"Disambiguation failed: {t.error}")
        if st.button("Back to input"):
            ss.disambig_task_id = None
            state.go_to_input()
            st.rerun(scope="app")
        return

    d = (t.result or {}).get("disambiguation") or {}
    ss.disambig_task_id = None
    if d.get("clear"):
        state.start_research_flow(
            d.get("canonical_name") or ss.pending_name,
            d.get("domain"),
            d.get("category"),
        )
    else:
        ss.candidates = d.get("candidates", [])
        ss.view = "disambig"
    st.rerun(scope="app")
