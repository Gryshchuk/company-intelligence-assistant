"""Fetch a URL and add its full content to the company KB. Content never \
enters the agent's context — only a chunk count is returned."""
from __future__ import annotations

from .. import vectordb
from .context import current_company
from .fetch_url import _extract_clean_text


def index_url(url: str) -> str:
    """Fetch `url` and add its full content to the active company's \
knowledge base. Returns only a chunk count — the page text does NOT \
enter your context, so this is the cheapest way to ingest a source. \
Use this whenever you already know a URL is relevant; only use \
`fetch_url` first if you need to inspect a page yourself before \
deciding to index it."""
    text = _extract_clean_text(url)
    if not text:
        return f"Could not fetch or extract {url}."
    cid = current_company()
    n = vectordb.add_text(cid, text, url)
    return f"Indexed {n} chunk(s) from {url} ({len(text)} chars)."
