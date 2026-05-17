"""Wikipedia preview tool (truncated) + internal helper for the indexer."""
from __future__ import annotations

from typing import Optional

import wikipediaapi

_wiki = wikipediaapi.Wikipedia(
    user_agent="company-intel/0.1 (research)", language="en"
)

_PREVIEW_CHAR_LIMIT = 6000


def _load_page(topic: str) -> Optional[wikipediaapi.WikipediaPage]:
    page = _wiki.page(topic)
    return page if page.exists() else None


def wikipedia_lookup(topic: str) -> str:
    """Fetch the Wikipedia article for `topic` and return its plaintext. \
Truncated to the first ~6000 characters as a PREVIEW; use \
`index_wikipedia(topic)` to add the full page to the knowledge base \
without bringing it into your context."""
    page = _load_page(topic)
    if page is None:
        return f"No Wikipedia page for '{topic}'."
    text = page.text
    header = f"# {page.title}\nURL: {page.fullurl}\n\n"
    if len(text) > _PREVIEW_CHAR_LIMIT:
        truncated = text[:_PREVIEW_CHAR_LIMIT]
        return (
            f"{header}[TRUNCATED preview — {len(text)} chars total, "
            f"showing first {_PREVIEW_CHAR_LIMIT}. Call "
            f"`index_wikipedia('{topic}')` to index the full article.]\n\n"
            f"{truncated}"
        )
    return header + text
