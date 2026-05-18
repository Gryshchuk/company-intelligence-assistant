"""Persistent index of researched companies. Dedup by normalized name OR domain."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from .config import COMPANIES_FILE


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def _normalize_domain(domain: Optional[str]) -> Optional[str]:
    if not domain:
        return None
    d = domain.strip().lower()
    if "://" in d:
        d = urlparse(d).netloc or d
    return d.removeprefix("www.") or None


def _read() -> list[dict]:
    if not COMPANIES_FILE.exists():
        return []
    return json.loads(COMPANIES_FILE.read_text())


def _write(rows: list[dict]) -> None:
    COMPANIES_FILE.write_text(json.dumps(rows, indent=2))


def list_companies() -> list[dict]:
    return sorted(_read(), key=lambda r: r["name"].lower())


def find(name: str, domain: Optional[str] = None) -> Optional[dict]:
    n, d = _normalize_name(name), _normalize_domain(domain)
    for row in _read():
        if _normalize_name(row["name"]) == n:
            return row
        if d and _normalize_domain(row.get("domain")) == d:
            return row
    return None


def upsert(
    name: str,
    domain: Optional[str],
    summary: str,
    category: Optional[str] = None,
    competitors: Optional[list[str]] = None,
    local_peers: Optional[list[str]] = None,
    global_peers: Optional[list[str]] = None,
) -> dict:
    rows = _read()
    existing = find(name, domain)
    if existing:
        existing.update(
            name=name,
            domain=_normalize_domain(domain),
            summary=summary,
        )
        if category is not None:
            existing["category"] = category
        if competitors is not None:
            existing["competitors"] = competitors
        if local_peers is not None:
            existing["local_peers"] = local_peers
        if global_peers is not None:
            existing["global_peers"] = global_peers
        _write(rows)
        return existing
    row = {
        "id": uuid.uuid4().hex[:12],
        "name": name,
        "domain": _normalize_domain(domain),
        "summary": summary,
        "category": category,
        "competitors": competitors or [],
        "local_peers": local_peers or [],
        "global_peers": global_peers or [],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    rows.append(row)
    _write(rows)
    return row


def get(company_id: str) -> Optional[dict]:
    for row in _read():
        if row["id"] == company_id:
            return row
    return None


def reset_all() -> None:
    """Wipe the company index and every vector table."""
    from . import vectordb

    if COMPANIES_FILE.exists():
        COMPANIES_FILE.unlink()
    vectordb.drop_all()
