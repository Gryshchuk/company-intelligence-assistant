"""Structured-output schemas used by the agents.

Kept in one place so the shape of agent responses is easy to scan and
modify without hunting through individual agent modules.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

# ---- disambiguation --------------------------------------------------------


class Candidate(BaseModel):
    name: str = Field(description="Canonical company name as it should be stored.")
    description: str = Field(
        description="One-line description distinguishing this entity from the others."
    )
    domain: Optional[str] = Field(
        default=None,
        description="Primary web domain if known (no protocol, e.g. 'figma.com').",
    )


class Disambiguation(BaseModel):
    clear: bool = Field(
        description="True if the input unambiguously refers to a single company."
    )
    canonical_name: Optional[str] = Field(
        default=None, description="If clear, the canonical company name."
    )
    domain: Optional[str] = Field(
        default=None, description="If clear, the primary web domain."
    )
    candidates: list[Candidate] = Field(
        default_factory=list,
        description="If not clear, 2-6 distinct companies the input could mean.",
    )


# ---- research --------------------------------------------------------------


class ResearchResult(BaseModel):
    summary: str = Field(description="3-6 sentence overview of THIS specific company.")
    competitors: list[str] = Field(
        default_factory=list,
        description=(
            "DIRECT competitors — companies whose product substitutes for "
            "the target's. Aim for 3-8 names that actually appeared in "
            "indexed sources."
        ),
    )
    local_peers: list[str] = Field(
        default_factory=list,
        description=(
            "Same-industry companies operating in the target's home country "
            "or region. They share the local market context but may not be "
            "direct substitutes. Aim for 3-5 names. Empty list if the home "
            "market couldn't be determined."
        ),
    )
    global_peers: list[str] = Field(
        default_factory=list,
        description=(
            "Same-industry / category companies anywhere in the world — the "
            "category leaders or notable players in the same broad space. "
            "Aim for 3-5 names."
        ),
    )
    sources_indexed: list[str] = Field(
        default_factory=list,
        description="Sources written to the knowledge base.",
    )
