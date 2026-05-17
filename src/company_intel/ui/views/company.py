"""Company profile + Q&A chat."""
import streamlit as st

from ... import store
from .. import log_pane, state


_PEER_GROUPS = (
    ("Direct competitors", "competitors"),
    ("Local-market peers", "local_peers"),
    ("Global peers", "global_peers"),
)


def render() -> None:
    company = _load_company()
    if company is None:
        return
    _render_header(company)
    _render_peer_groups(company)
    st.divider()
    _render_chat(company)


def _load_company() -> dict | None:
    cid = st.session_state.get("current_company_id")
    company = store.get(cid) if cid else None
    if company is None:
        st.warning("Company not found.")
        st.session_state.view = "input"
    return company


def _render_header(company: dict) -> None:
    st.title(company["name"])
    if company.get("domain"):
        st.caption(company["domain"])
    if company.get("summary"):
        st.write(company["summary"])
    else:
        st.caption("_No summary yet — research is still running._")


def _render_peer_groups(company: dict) -> None:
    for label, key in _PEER_GROUPS:
        items = company.get(key) or []
        if items:
            st.markdown(f"**{label}**")
            st.markdown(_pills(items), unsafe_allow_html=True)


def _pills(items: list[str]) -> str:
    return " ".join(
        f"<span style='display:inline-block;padding:2px 10px;"
        f"margin:2px 4px 2px 0;border:1px solid #3A3936;"
        f"border-radius:999px;font-size:0.85rem;'>{c}</span>"
        for c in items
    )


def _render_chat(company: dict) -> None:
    cid = company["id"]
    hdr_l, hdr_r = st.columns([3, 1])
    hdr_l.subheader("Ask about this company")
    transcript = st.session_state.chat.setdefault(cid, [])
    if transcript and hdr_r.button(
        "🧹 Clear conversation", use_container_width=True
    ):
        state.clear_chat(cid)
        st.rerun()

    log_pane.render_transcript(cid)

    q = st.chat_input("Your question")
    if q:
        state.start_qa_flow(cid, q)
        st.rerun()
