from .. import vectordb
from .context import current_company


def index_text(source: str, text: str) -> str:
    """Save `text` to the active company's knowledge base, chunked and embedded for later Q&A.
    `source` should identify the origin (URL, or 'wikipedia:<title>').
    Call this for every substantive piece of content you want the Q&A agent to remember."""
    cid = current_company()
    n = vectordb.add_text(cid, text, source)
    return f"Indexed {n} chunk(s) from {source}."
