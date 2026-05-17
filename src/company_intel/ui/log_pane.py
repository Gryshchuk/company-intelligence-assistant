"""Right pane: live activity log + token/cost panel. Pure rendering — no
view transitions live here (those are owned by the polling fragments in
ui/views/disambiguating.py and ui/views/researching.py).
"""
from __future__ import annotations

import streamlit as st

from ..eventbus import get_task

STATUS_LABEL = {
    "running": "⏳ running",
    "done": "✅ done",
    "error": "❌ error",
}
TODO_MARK = {"completed": "✅", "in_progress": "🔄", "pending": "◻️"}
RUN_ICON = {"running": "⏳", "done": "🛠", "error": "❌"}


def _shorten(value: object, limit: int = 80) -> str:
    s = value if isinstance(value, str) else repr(value)
    s = s.replace("\n", " ")
    return s if len(s) <= limit else s[:limit] + "…"


def _input_preview(inputs: dict) -> str:
    parts = []
    for k, v in inputs.items():
        if isinstance(v, str) and len(v) > 80:
            parts.append(f"{k}=<{len(v)} chars>")
        else:
            parts.append(f"{k}={_shorten(v, 60)}")
    return ", ".join(parts)


def _render_tool_run(run: dict) -> None:
    icon = RUN_ICON.get(run["status"], "🛠")
    preview = _input_preview(run["inputs"])
    header = f"{icon} {run['name']}"
    if preview:
        header += f"  · {_shorten(preview, 70)}"
    with st.expander(header, expanded=False):
        st.markdown("**Input**")
        st.json(run["inputs"], expanded=False)
        if run["status"] != "running":
            st.markdown("**Output**")
            st.code(run["output"] or "(empty)", language="text")


def _render_notice(notice: dict) -> None:
    text = notice["text"]
    kind = notice["kind"]
    if kind == "error":
        st.error(text)
    elif kind == "compaction":
        st.info(text)
    else:
        st.caption(text)


def _render_tokens(snap: dict) -> None:
    st.markdown("**Tokens & cost**")
    st.caption("Chat model")
    a, b, c = st.columns(3)
    a.metric("In", f"{snap['chat_tokens_in']:,}")
    b.metric("Out", f"{snap['chat_tokens_out']:,}")
    c.metric("Cost", f"${snap['chat_cost_usd']:.4f}")
    st.caption("Embeddings")
    d, e = st.columns(2)
    d.metric("Tokens", f"{snap['embed_tokens']:,}")
    e.metric("Cost", f"${snap['embed_cost_usd']:.5f}")
    st.markdown(f"**Total: ${snap['total_cost_usd']:.4f}**")


@st.fragment(run_every=1)
def render() -> None:
    st.subheader("Activity")
    task_id = st.session_state.get("active_task_id")
    if not task_id:
        st.caption("No active task.")
        return
    task = get_task(task_id)
    if task is None:
        st.caption("Task not found.")
        return

    snap = task.snapshot()
    st.write(f"**{snap['title']}**  ·  {STATUS_LABEL[snap['status']]}")

    if snap["todos"]:
        st.markdown("**Plan**")
        for t in snap["todos"]:
            mark = TODO_MARK.get(t.get("status", "pending"), "◻️")
            st.markdown(f"- {mark} {t.get('content', '')}")

    st.markdown("**Log**")
    log_box = st.container(height=380, border=True)
    with log_box:
        for run in snap["tool_runs"][-100:]:
            _render_tool_run(run)
        for notice in snap["notices"][-30:]:
            _render_notice(notice)

    _render_tokens(snap)


@st.fragment(run_every=1)
def render_transcript(company_id: str) -> None:
    """Live-updating Q&A transcript — polls pending tasks each second."""
    transcript = st.session_state.chat.setdefault(company_id, [])
    for turn in transcript:
        if turn["a"] is None and turn.get("task_id"):
            t = get_task(turn["task_id"])
            if t and t.status == "done" and t.result:
                turn["a"] = t.result.get("answer", "")
            elif t and t.status == "error":
                turn["a"] = f"Error: {t.error}"
    for turn in transcript:
        with st.chat_message("user"):
            st.write(turn["q"])
        with st.chat_message("assistant"):
            st.write(turn["a"] or "_thinking…_")
