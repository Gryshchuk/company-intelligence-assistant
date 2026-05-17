"""Central configuration: paths, model ids, pricing."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
COMPANIES_FILE = DATA_DIR / "companies.json"
LANCEDB_DIR = DATA_DIR / "lancedb"

DATA_DIR.mkdir(parents=True, exist_ok=True)
LANCEDB_DIR.mkdir(parents=True, exist_ok=True)

CHAT_MODEL = "openai:gpt-5.4-mini"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

# Bumped from the langchain default (2) so a short OpenAI TPM spike doesn't
# kill a long research run — the SDK applies exponential backoff between
# retries.
CHAT_MAX_RETRIES = 6


def build_chat_model():
    """Single place to construct the chat model.

    The OpenAI provider ships a full `model.profile` for `gpt-5.4-mini`
    (max_input_tokens=400_000, tool_calling, structured_output, …) which
    deepagents' SummarizationMiddleware reads to pick fraction-based
    compaction thresholds (trigger at ~85%, keep ~10%). We don't need to
    override the profile — just make sure we don't strip it.
    """
    from langchain.chat_models import init_chat_model

    return init_chat_model(CHAT_MODEL, max_retries=CHAT_MAX_RETRIES)


# USD per 1M tokens. Edit these if OpenAI's published prices change.
# Defaults are placeholders in the gpt-4o-mini / gpt-4o range; check the
# live pricing page for the authoritative numbers.
PRICING_PER_MTOK = {
    "gpt-5.4-mini": {"in": 0.15, "out": 0.60},
    "gpt-5.4": {"in": 5.00, "out": 15.00},
    "text-embedding-3-small": {"in": 0.02, "out": 0.0},
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
