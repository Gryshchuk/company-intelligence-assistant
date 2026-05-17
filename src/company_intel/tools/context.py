"""Holds the active company id for the current research task.

Set once at the start of an agent run; tools read it to know which LanceDB
table to write into without polluting tool signatures.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Optional

_active_company: ContextVar[Optional[str]] = ContextVar("active_company", default=None)


def set_active_company(company_id: str) -> None:
    _active_company.set(company_id)


def current_company() -> str:
    cid = _active_company.get()
    if not cid:
        raise RuntimeError("No active company set for tool call.")
    return cid
