"""Fetch a web page. Preview-only tool (truncated) + internal helper for indexers."""
from __future__ import annotations

from typing import Optional

import trafilatura

# Preview returned to the agent is capped — full pages can be 50k+ chars
# and a few parallel fetches will blow through the TPM ceiling. Indexers
# (see `index_url`) use the helper below to grab the full content without
# routing it through the agent's context.
_PREVIEW_CHAR_LIMIT = 6000


def _extract_clean_text(url: str) -> Optional[str]:
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return None
    return trafilatura.extract(
        downloaded, include_comments=False, include_tables=True
    )


def fetch_url(url: str) -> str:
    """Download a web page and return its main text. Truncated to the first \
~6000 characters as a PREVIEW; use `index_url(url)` to add the full \
content to the knowledge base without bringing it into your context."""
    text = _extract_clean_text(url)
    if not text:
        return f"Could not fetch or extract {url}."
    if len(text) > _PREVIEW_CHAR_LIMIT:
        truncated = text[:_PREVIEW_CHAR_LIMIT]
        return (
            f"URL: {url}\n[TRUNCATED preview — {len(text)} chars total, "
            f"showing first {_PREVIEW_CHAR_LIMIT}. Call `index_url('{url}')` "
            f"to index the full page.]\n\n{truncated}"
        )
    return f"URL: {url}\n\n{text}"
