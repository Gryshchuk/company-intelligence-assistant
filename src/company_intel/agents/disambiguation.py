"""Decide whether a company name needs disambiguation before we research it.

Runs as a tracked deep agent so progress appears in the Activity pane. If
the model is unsure, it searches the web to discover real candidates rather
than relying solely on prior knowledge.
"""
from __future__ import annotations

import threading

from deepagents import create_deep_agent

from ..config import build_chat_model
from ..eventbus import Task, TaskCallback, new_task
from ..schemas import Disambiguation
from ..tools.web_search import web_search


DISAMBIG_PROMPT = """\
You decide whether a user's company name unambiguously identifies a single \
company.

Process:
1. From your own knowledge, judge whether the name is clear or could mean \
multiple distinct organizations (parent vs subsidiary, same name in \
different industries, or a common word used by several companies).
2. If you are NOT highly confident the name is unique, run AT LEAST 4 \
varied `web_search` queries to broaden coverage. Tavily's index differs \
from Google's, so different phrasings surface different companies. Try \
variations like:    
   - `"<name>" 
   - `"<name>" company`
   - `"<name>" website`
   - `<name> app` or `<name> startup`
   - `"<name>" Ukraine`
   - just `<name>` (no quotes) to catch brands the engine ranks highly
3. The user may also have given extra context (an industry, a domain, a \
product name). Use it to focus your queries.
4. Compile 5-10 distinct candidates. For each: canonical name, one-line \
description, primary web domain (no protocol). Prefer candidates whose \
domain you actually saw in web_search results — don't invent domains.
5. If, after searching, you're confident the name maps to ONE company, \
set clear=True and fill canonical_name and domain.

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

    def run():
        try:
            cb = TaskCallback(task)
            agent = _build_agent()
            result = agent.invoke(
                {"messages": [{"role": "user", "content": f"Input: {name}"}]},
                config={"callbacks": [cb], "recursion_limit": 30},
            )
            structured: Disambiguation = (
                result.get("structured_response") or result.get("response")
            )
            if structured is None:
                raise RuntimeError("Disambiguation agent returned no structured response.")
            task.result = {"disambiguation": structured.model_dump()}
            task.status = "done"
        except Exception as e:
            task.status = "error"
            task.error = str(e)
            task.push_notice("error", str(e))

    threading.Thread(target=run, daemon=True).start()
    return task
