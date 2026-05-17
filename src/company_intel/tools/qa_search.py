"""Read-only retrieval tools for the Q&A agent. No web access."""
from __future__ import annotations

from .. import vectordb
from .context import current_company


def _format(rows: list[dict]) -> str:
    if not rows:
        return "No matches."
    return "\n\n".join(f"[{r['source']}]\n{r['text']}" for r in rows)


def vector_search(query: str, k: int = 5) -> str:
    """Semantic search over the active company's knowledge base. Returns up to `k` chunks with their sources."""
    return _format(vectordb.vector_search(current_company(), query, k))


def keyword_search(query: str, k: int = 5) -> str:
    """Full-text keyword search over the active company's knowledge base. Best for proper nouns, numbers, exact phrases."""
    return _format(vectordb.keyword_search(current_company(), query, k))
