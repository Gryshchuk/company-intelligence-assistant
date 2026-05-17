"""Left sidebar — company list, '+ new', destructive 'remove all'."""
import streamlit as st

from .. import store
from . import state


def render() -> None:
    with st.sidebar:
        st.header("Companies")
        if st.button("＋ New research", use_container_width=True):
            state.go_to_input()
        st.divider()

        companies = store.list_companies()
        if not companies:
            st.caption("No companies yet.")
        for row in companies:
            label = row["name"] + (
                f"  ·  {row['domain']}" if row.get("domain") else ""
            )
            if st.button(label, key=f"co_{row['id']}", use_container_width=True):
                state.open_company(row["id"])
                st.rerun()

        if companies:
            st.divider()
            with st.popover("🗑 Remove all data", use_container_width=True):
                st.warning(
                    f"This deletes **{len(companies)}** companies and all "
                    "embeddings. It cannot be undone."
                )
                if st.button("Yes, delete everything", type="primary"):
                    state.reset_all()
                    st.rerun()
