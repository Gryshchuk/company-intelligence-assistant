"""LanceDB-backed vector + full-text store. One table per company."""
from __future__ import annotations

import threading
import uuid

import lancedb
import pyarrow as pa
import tiktoken
from langchain_openai import OpenAIEmbeddings

from .config import EMBED_DIM, EMBED_MODEL, LANCEDB_DIR
from .eventbus import record_embedding_tokens

# OpenAI's embedding-3 family uses cl100k_base.
_token_enc = tiktoken.get_encoding("cl100k_base")


def _count_tokens(texts: list[str]) -> int:
    return sum(len(_token_enc.encode(t)) for t in texts)

_embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
_db = lancedb.connect(str(LANCEDB_DIR))

# Serialize all writes — Lance's CreateIndex transaction does not tolerate
# concurrent callers, and the deep agent fires parallel index_text tool calls.
_write_lock = threading.Lock()
# Track which tables have dirty FTS indexes so we rebuild lazily before search.
_fts_dirty: set[str] = set()


def _table_name(company_id: str) -> str:
    return f"c_{company_id}"


def _schema() -> pa.Schema:
    return pa.schema([
        pa.field("chunk_id", pa.string()),
        pa.field("text", pa.string()),
        pa.field("source", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), EMBED_DIM)),
    ])


def _open_or_create(company_id: str):
    name = _table_name(company_id)
    if name in _db.table_names():
        return _db.open_table(name)
    return _db.create_table(name, schema=_schema())


def _chunk(text: str, size: int = 1200, overlap: int = 150) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def add_text(company_id: str, text: str, source: str) -> int:
    chunks = _chunk(text)
    if not chunks:
        return 0
    record_embedding_tokens(_count_tokens(chunks))
    vectors = _embeddings.embed_documents(chunks)
    rows = [
        {
            "chunk_id": uuid.uuid4().hex,
            "text": c,
            "source": source,
            "vector": v,
        }
        for c, v in zip(chunks, vectors)
    ]
    name = _table_name(company_id)
    with _write_lock:
        table = _open_or_create(company_id)
        table.add(rows)
        _fts_dirty.add(name)
    return len(chunks)


def _ensure_fts(name: str) -> None:
    with _write_lock:
        if name in _fts_dirty:
            _db.open_table(name).create_fts_index("text", replace=True)
            _fts_dirty.discard(name)


def vector_search(
    company_id: str, query: str, k: int = 5
) -> list[dict]:
    name = _table_name(company_id)
    if name not in _db.table_names():
        return []
    record_embedding_tokens(_count_tokens([query]))
    vec = _embeddings.embed_query(query)
    rows = _db.open_table(name).search(vec).limit(k).to_list()
    return [{"text": r["text"], "source": r["source"]} for r in rows]


def keyword_search(
    company_id: str, query: str, k: int = 5
) -> list[dict]:
    name = _table_name(company_id)
    if name not in _db.table_names():
        return []
    _ensure_fts(name)
    table = _db.open_table(name)
    try:
        rows = (
            table.search(query, query_type="fts").limit(k).to_list()
        )
    except Exception:
        return []
    return [{"text": r["text"], "source": r["source"]} for r in rows]


def chunk_count(company_id: str) -> int:
    name = _table_name(company_id)
    if name not in _db.table_names():
        return 0
    return _db.open_table(name).count_rows()


def drop_all() -> None:
    """Delete every company's vector table."""
    with _write_lock:
        for name in list(_db.table_names()):
            _db.drop_table(name)
        _fts_dirty.clear()
