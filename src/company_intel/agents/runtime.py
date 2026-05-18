"""Shared agent-execution plumbing.

Every agent module (research / qa / disambiguation) has the same shape:
  1. spawn a background thread that wraps the body in try/except,
  2. run the agent and stream its state (so compaction events surface),
  3. pull either a structured response or a plain text message,
  4. update the Task on success or error.

This module owns those four steps so the agent modules stay focused on
their prompt + their structured output schema.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Optional

from ..eventbus import Task, TaskCallback


# ---- threading -----------------------------------------------------------


def run_in_background(
    task: Task,
    target: Callable[..., None],
    *args: Any,
) -> None:
    """Spawn `target(*args)` in a daemon thread. Any exception updates the
    task with status='error' so the UI can render it."""

    def wrapped() -> None:
        try:
            target(*args)
        except Exception as exc:  # noqa: BLE001 — surface anything as a notice
            task.status = "error"
            task.error = str(exc)
            task.push_notice("error", str(exc))

    threading.Thread(target=wrapped, daemon=True).start()


# ---- agent execution -----------------------------------------------------


def run_agent(
    agent,
    user_text: str,
    task: Task,
    *,
    recursion_limit: int = 60,
) -> dict:
    """Stream the agent to completion. Logs compaction events into the task.
    Returns the final state dict (same shape as agent.invoke would yield).
    """
    seen_compactions: set[tuple] = set()
    final: dict = {}
    config = {
        "callbacks": [TaskCallback(task)],
        "recursion_limit": recursion_limit,
    }
    inputs = {"messages": [{"role": "user", "content": user_text}]}
    for state in agent.stream(inputs, config=config, stream_mode="values"):
        if isinstance(state, dict):
            final = state
            _maybe_log_compaction(task, final, seen_compactions)
    return final


def _maybe_log_compaction(
    task: Task, state: dict, seen: set[tuple]
) -> None:
    event = state.get("_summarization_event")
    if not event:
        return
    fingerprint = (event.get("cutoff_index", 0), event.get("file_path"))
    if fingerprint in seen:
        return
    seen.add(fingerprint)
    summarised = event.get("cutoff_index", 0)
    kept = max(0, len(state.get("messages") or []) - summarised)
    path = event.get("file_path")
    suffix = f" (history saved to {path})" if path else ""
    task.push_notice(
        "compaction",
        f"🗜 Compacted: summarised {summarised} older message(s); "
        f"kept the most recent {kept}.{suffix}",
    )


# ---- response extraction -------------------------------------------------


def extract_structured(state: dict) -> Any:
    """Pull the structured_response (Pydantic model) from agent state."""
    structured = state.get("structured_response") or state.get("response")
    if structured is None:
        raise RuntimeError("Agent did not return a structured response.")
    return structured


def extract_text(msg: Any) -> str:
    """Extract user-facing prose from an AIMessage.

    Only text-typed parts count — tool-use / reasoning parts are skipped.
    Leading JSON blobs (the model occasionally echoes its `write_todos`
    arguments) are also stripped, belt-and-braces, in case the prompt
    rule against echoing tool args fails.
    """
    content = getattr(msg, "content", msg)
    if isinstance(content, str):
        return _strip_leading_json(content)
    if isinstance(content, list):
        parts: list[str] = []
        for p in content:
            if not isinstance(p, dict):
                continue
            if p.get("type") in (None, "text", "output_text"):
                t = p.get("text", "")
                if isinstance(t, str) and t.strip():
                    parts.append(t)
        return _strip_leading_json("".join(parts).strip())
    return _strip_leading_json(str(content))


def _strip_leading_json(text: str) -> str:
    """Drop a balanced leading `{...}` or `[...]` JSON object from `text`."""
    text = text.lstrip()
    if not text or text[0] not in "{[":
        return text
    open_ch = text[0]
    close_ch = "}" if open_ch == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[i + 1:].lstrip()
    return text


# ---- user-message construction ------------------------------------------


def qualified_target_message(
    name: str,
    domain: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """Build the standard 'research/analyse THIS company' opener."""
    qualifiers = [
        f"web domain: {domain}" if domain else None,
        f"category: {category}" if category else None,
    ]
    quals = "; ".join(q for q in qualifiers if q)
    suffix = f" ({quals})" if quals else ""
    return (
        f"Research the company **{name}**{suffix}. "
        "This exact entity — not any similarly-named company."
    )
