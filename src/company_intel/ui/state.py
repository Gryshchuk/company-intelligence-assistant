"""Session state init + flow helpers.

All "kick off an agent, point the log at it, switch the view" transitions
live here so the views themselves don't have to know about session_state
keys or about how to launch an agent.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from .. import store
from ..agents import start_disambiguate, start_qa, start_research


def init() -> None:
    """Seed all session_state keys we depend on."""
    ss = st.session_state
    ss.setdefault("view", "input")
    ss.setdefault("current_company_id", None)
    ss.setdefault("active_task_id", None)
    ss.setdefault("pending_name", "")
    ss.setdefault("candidates", [])
    ss.setdefault("disambig_task_id", None)
    ss.setdefault("chat", {})  # company_id -> list[{q, a, task_id}]
    ss.setdefault("popup_shown_for", set())


# ---- navigation -----------------------------------------------------------


def go_to_input() -> None:
    ss = st.session_state
    ss.view = "input"
    ss.current_company_id = None


def open_company(company_id: str) -> None:
    """Switch to the company view. Does NOT clear active_task_id — the log
    persists across navigation until a new task replaces it."""
    ss = st.session_state
    ss.current_company_id = company_id
    ss.view = "company"


# ---- agent launch flows ---------------------------------------------------


def start_disambiguation_flow(input_text: str) -> None:
    ss = st.session_state
    ss.pending_name = input_text
    task = start_disambiguate(input_text)
    ss.active_task_id = task.id
    ss.disambig_task_id = task.id
    ss.view = "disambiguating"


def start_research_flow(name: str, domain: Optional[str]) -> None:
    """If we already know this company, just open it. Otherwise kick off
    research and switch to the researching view."""
    existing = store.find(name, domain)
    if existing:
        open_company(existing["id"])
        st.toast(f"Opened existing record for {existing['name']}.")
        return
    task = start_research(name=name, domain=domain)
    st.session_state.active_task_id = task.id
    st.session_state.view = "researching"


def start_qa_flow(company_id: str, question: str) -> None:
    ss = st.session_state
    task = start_qa(company_id, question)
    ss.active_task_id = task.id
    transcript = ss.chat.setdefault(company_id, [])
    transcript.append({"q": question, "a": None, "task_id": task.id})


def clear_chat(company_id: str) -> None:
    st.session_state.chat[company_id] = []


def reset_all() -> None:
    store.reset_all()
    st.session_state.clear()
