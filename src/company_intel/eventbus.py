"""Thread-safe per-task tool-run log + token/cost tracker.

Chat and embedding usage are tracked separately. The agent runs in a
background thread and pushes events here; the Streamlit loop reads
snapshots to render the log pane.
"""
from __future__ import annotations

import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from .config import CHAT_MODEL, EMBED_MODEL, PRICING_PER_MTOK


@dataclass
class ToolRun:
    """One tool invocation, mutated in place when the result arrives."""

    run_id: str
    name: str
    inputs: dict[str, Any]
    started_at: float
    output: Optional[str] = None
    status: str = "running"  # running | done | error
    ended_at: Optional[float] = None


@dataclass
class Notice:
    """A free-form log line that isn't a tool call."""

    ts: float
    kind: str
    text: str


@dataclass
class Task:
    id: str
    title: str
    notices: list[Notice] = field(default_factory=list)
    tool_runs: list[ToolRun] = field(default_factory=list)
    todos: list[dict] = field(default_factory=list)
    chat_tokens_in: int = 0
    chat_tokens_out: int = 0
    embed_tokens: int = 0
    chat_cost_usd: float = 0.0
    embed_cost_usd: float = 0.0
    status: str = "running"  # running | done | error
    result: Optional[dict] = None
    error: Optional[str] = None
    lock: threading.Lock = field(default_factory=threading.Lock)

    def push_notice(self, kind: str, text: str) -> None:
        with self.lock:
            self.notices.append(Notice(ts=time.time(), kind=kind, text=text))

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "id": self.id,
                "title": self.title,
                "notices": [vars(n) for n in self.notices],
                "tool_runs": [vars(r) for r in self.tool_runs],
                "todos": list(self.todos),
                "chat_tokens_in": self.chat_tokens_in,
                "chat_tokens_out": self.chat_tokens_out,
                "embed_tokens": self.embed_tokens,
                "chat_cost_usd": self.chat_cost_usd,
                "embed_cost_usd": self.embed_cost_usd,
                "total_cost_usd": self.chat_cost_usd + self.embed_cost_usd,
                "status": self.status,
                "result": self.result,
                "error": self.error,
            }


# Active task for the current research/Q&A run, used by code paths that
# can't be reached through LangChain callbacks (e.g. embedding calls).
_active_task: ContextVar[Optional[Task]] = ContextVar(
    "active_task", default=None
)


def set_active_task(task: Optional[Task]) -> None:
    _active_task.set(task)


def current_task() -> Optional[Task]:
    return _active_task.get()


_TASKS: dict[str, Task] = {}
_TASKS_LOCK = threading.Lock()


def new_task(title: str) -> Task:
    task = Task(id=uuid.uuid4().hex[:8], title=title)
    with _TASKS_LOCK:
        _TASKS[task.id] = task
    return task


def get_task(task_id: str) -> Optional[Task]:
    with _TASKS_LOCK:
        return _TASKS.get(task_id)


def _short_model(model_id: str) -> str:
    """Strip the provider prefix: 'openai:gpt-5.4' -> 'gpt-5.4'."""
    return (model_id or "").split(":")[-1]


def _rates(model_id: str, fallback_id: str) -> dict:
    return (
        PRICING_PER_MTOK.get(_short_model(model_id))
        or PRICING_PER_MTOK.get(_short_model(fallback_id))
        or {"in": 0.0, "out": 0.0}
    )


def _chat_cost(model_id: str, tokens_in: int, tokens_out: int) -> float:
    r = _rates(model_id, CHAT_MODEL)
    return (tokens_in * r["in"] + tokens_out * r["out"]) / 1_000_000


def _embed_cost(tokens: int) -> float:
    r = _rates(EMBED_MODEL, EMBED_MODEL)
    return tokens * r["in"] / 1_000_000


def record_embedding_tokens(tokens: int) -> None:
    """Add embedding-token usage to the currently active task."""
    task = current_task()
    if task is None or tokens <= 0:
        return
    cost = _embed_cost(tokens)
    with task.lock:
        task.embed_tokens += tokens
        task.embed_cost_usd += cost


def _rid(run_id: Any) -> str:
    return str(run_id) if isinstance(run_id, UUID) else str(run_id or "")


class TaskCallback(BaseCallbackHandler):
    """Bridges LangChain agent events to a Task log."""

    def __init__(self, task: Task) -> None:
        self.task = task

    def on_tool_start(self, serialized, input_str, **kwargs):
        name = (
            (serialized or {}).get("name")
            or kwargs.get("name")
            or "tool"
        )
        inputs = kwargs.get("inputs")
        if not isinstance(inputs, dict):
            inputs = {"_": input_str}
        run = ToolRun(
            run_id=_rid(kwargs.get("run_id")),
            name=name,
            inputs=inputs,
            started_at=time.time(),
        )
        with self.task.lock:
            self.task.tool_runs.append(run)
        if name == "write_todos":
            todos = inputs.get("todos") if isinstance(inputs, dict) else None
            if isinstance(todos, list):
                with self.task.lock:
                    self.task.todos = todos

    def _finish_run(self, run_id: Any, output: str, status: str) -> None:
        rid = _rid(run_id)
        with self.task.lock:
            for run in reversed(self.task.tool_runs):
                if run.run_id == rid and run.status == "running":
                    run.output = output
                    run.status = status
                    run.ended_at = time.time()
                    return

    def on_tool_end(self, output, **kwargs):
        self._finish_run(kwargs.get("run_id"), str(output), "done")

    def on_tool_error(self, error, **kwargs):
        self._finish_run(kwargs.get("run_id"), str(error), "error")

    def on_llm_end(self, response, **kwargs):
        usage = _extract_usage(response)
        if not usage:
            return
        tin, tout = usage
        model_id = _model_from_response(response) or CHAT_MODEL
        cost = _chat_cost(model_id, tin, tout)
        with self.task.lock:
            self.task.chat_tokens_in += tin
            self.task.chat_tokens_out += tout
            self.task.chat_cost_usd += cost

    def on_chain_error(self, error, **kwargs):
        self.task.push_notice("error", str(error))


def _extract_usage(response) -> Optional[tuple[int, int]]:
    """Pull (input_tokens, output_tokens) from a chat-model response."""
    try:
        for gen_list in getattr(response, "generations", []):
            for gen in gen_list:
                msg = getattr(gen, "message", None)
                meta = getattr(msg, "usage_metadata", None) if msg else None
                if meta:
                    return (
                        int(meta.get("input_tokens", 0)),
                        int(meta.get("output_tokens", 0)),
                    )
        out = getattr(response, "llm_output", None) or {}
        tu = out.get("token_usage") or {}
        if tu:
            return (
                int(tu.get("prompt_tokens", 0)),
                int(tu.get("completion_tokens", 0)),
            )
    except Exception:
        pass
    return None


def _model_from_response(response) -> str:
    """Best-effort extraction of the model id from an LLM response."""
    try:
        for gen_list in getattr(response, "generations", []):
            for gen in gen_list:
                msg = getattr(gen, "message", None)
                meta = getattr(msg, "response_metadata", None) or {}
                for key in ("model_name", "model"):
                    if meta.get(key):
                        return meta[key]
    except Exception:
        pass
    out = getattr(response, "llm_output", None) or {}
    return out.get("model_name") or out.get("model") or ""
