"""Waiting screen while the research agent runs.

Owns the polling fragment that watches the active task and routes to
the company view (with a toast) when research completes.
"""
import streamlit as st

from ...eventbus import get_task
from .. import state


def render() -> None:
    st.title("Researching…")
    st.caption(
        "Watch the right panel for live progress. You'll be redirected "
        "when it's done."
    )
    _poll()


@st.fragment(run_every=1)
def _poll() -> None:
    ss = st.session_state
    tid = ss.get("active_task_id")
    if not tid:
        return
    t = get_task(tid)
    if t is None or t.status == "running":
        return
    if t.status == "error":
        st.error(f"Research failed: {t.error}")
        return

    result = t.result or {}
    company_id = result.get("company_id")
    if not company_id:
        return
    if tid not in ss.popup_shown_for:
        ss.popup_shown_for.add(tid)
        st.toast(f"Research complete: {t.title}", icon="🎉")
        state.open_company(company_id)
        st.rerun(scope="app")
