"""Fetch a Wikipedia article and add its full content to the company KB. \
Content never enters the agent's context — only a chunk count is returned."""
from __future__ import annotations

from .. import vectordb
from .context import current_company
from .wikipedia_lookup import _load_page


def index_wikipedia(topic: str) -> str:
    """Fetch the Wikipedia article for `topic` and add the full page to \
the active company's knowledge base. Returns only a chunk count — the \
article text does NOT enter your context. Use this for any company \
whose Wikipedia page you want indexed."""
    page = _load_page(topic)
    if page is None:
        return f"No Wikipedia page for '{topic}'."
    cid = current_company()
    source = f"wikipedia:{page.title}"
    n = vectordb.add_text(cid, page.text, source)
    return (
        f"Indexed {n} chunk(s) from {source} ({len(page.text)} chars). "
        f"URL: {page.fullurl}"
    )
