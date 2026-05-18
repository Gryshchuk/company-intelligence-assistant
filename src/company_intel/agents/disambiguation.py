"""Decide whether a company name needs disambiguation before we research it.

Runs as a tracked deep agent so progress appears in the Activity pane. If
the model is unsure, it searches the web to discover real candidates rather
than relying solely on prior knowledge.
"""
from __future__ import annotations

from deepagents import create_deep_agent

from ..config import build_chat_model
from ..eventbus import Task, new_task
from ..schemas import Disambiguation
from ..tools.web_search import web_search
from . import runtime


DISAMBIG_PROMPT = """\
You decide whether a user's company name unambiguously identifies a single \
company AND extract a short industry / vertical phrase (the **category**) \
that downstream research can append to the name to narrow searches.

Output for EVERY company you mention — both the clear-match and each \
candidate — must include:
- canonical name
- web domain (no protocol, e.g. `figma.com`) — never invent; only \
include a domain you actually saw in a search result
- category — 2-5 word industry / vertical phrase usable in queries, \
e.g. `astrology app`, `design tool`, `B2B SaaS for HR analytics`, \
`food delivery`, `online insurance broker`

Process:
1. From your own knowledge, judge whether the name is clear or could mean \
multiple distinct organizations (parent vs subsidiary, same name in \
different industries, or a common word used by several companies).
2. If you are NOT highly confident the name is unique, run AT LEAST 4 \
varied `web_search` queries to broaden coverage. Tavily's index differs \
from Google's, so different phrasings surface different companies. Try \
variations like:
   - `"<name>" company`
   - `"<name>" website`
   - `<name> app` or `<name> startup`
   - `"<name>" Ukraine` (or another likely region)
   - just `<name>` (no quotes) to catch brands the engine ranks highly
3. The user may also have given extra context (an industry, a domain, a \
product name). Use it to focus your queries AND to seed the category \
field.
4. Compile 5-10 distinct candidates. For each: canonical name, one-line \
description distinguishing it from the others, web domain, category. \
Prefer candidates whose domain you actually saw in web_search results.
5. If after searching you're confident the name maps to ONE company, \
set `clear=True` and fill `canonical_name`, `domain`, AND `category`.

Return only the structured response.
"""


def _build_agent():
    return create_deep_agent(
        model=build_chat_model(),
        tools=[web_search],
        system_prompt=DISAMBIG_PROMPT,
        response_format=Disambiguation,
    )


def start_disambiguate(name: str) -> Task:
    """Kick off disambiguation in a background thread; returns the Task for live polling."""
    task = new_task(title=f"Disambiguate: {name}")
    runtime.run_in_background(task, _do_disambiguate, task, name)
    return task


def _do_disambiguate(task: Task, name: str) -> None:
    agent = _build_agent()
    state = runtime.run_agent(agent, f"Input: {name}", task, recursion_limit=30)
    result: Disambiguation = runtime.extract_structured(state)
    task.result = {"disambiguation": result.model_dump()}
    task.status = "done"
