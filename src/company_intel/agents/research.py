"""Research orchestrator. Loads the SKILL.md library and delegates per topic."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Optional

from deepagents import create_deep_agent

from .. import store
from ..config import build_chat_model
from ..eventbus import Task, new_task, set_active_task
from ..schemas import ResearchResult
from ..tools import (
    fetch_url,
    index_text,
    index_url,
    index_wikipedia,
    set_active_company,
    web_search,
    wikipedia_lookup,
)
from . import runtime

SKILLS_DIR = Path(__file__).parent.parent / "skills"


def _strip_frontmatter(text: str) -> str:
    """Drop YAML frontmatter (---…---) at the top of a SKILL.md."""
    if not text.startswith("---"):
        return text.strip()
    end = text.find("\n---", 3)
    return text[end + 4 :].strip() if end >= 0 else text.strip()


def _load_skills_library() -> str:
    """Concatenate every SKILL.md body into one prompt section."""
    sections = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        body = _strip_frontmatter(skill_md.read_text())
        sections.append(f"### Skill: {skill_dir.name}\n\n{body}")
    return "\n\n---\n\n".join(sections)


ORCHESTRATOR_PROMPT = """\
You are a company research analyst. Your job is to build a per-company \
knowledge base that a downstream Q&A agent (NO web access) can later \
use to answer questions like:

- "Who are their competitors?"
- "What is their business model?"
- "When was the company founded? Who founded it?"
- "How do they make money?"
- "How much does the company earn? What's their funding / valuation?"
- "Where are they based? Who runs them now?"

Anything not indexed by you is unanswerable later. Index generously.

Today is {today} (current year: {year}).

Target identity (DO NOT change):
- Company name: **{company_name}**
- Web domain: {company_domain}
- Category / vertical: {company_category}

Many companies share similar names. Always qualify queries with this \
exact name AND the category (and the domain when relevant). If a \
source describes a different company — even with the same name but a \
different category — IGNORE it.

Recommended query shape for any web search: \
`"{company_name}" {company_category}`. \
This keeps you on the right entity and the right industry.

You have a SKILL LIBRARY (below) — each skill is a focused playbook \
for one slice of the research. Use the skills; they own the HOW.

Process:
1. `write_todos` — exactly one todo per skill in the SKILL LIBRARY. \
No extra "verify" or "finalize" todos.
2. For each skill-todo, follow that skill's playbook. Index content \
via `index_url` / `index_wikipedia` (full page enters the KB, not \
your context). Use `fetch_url` only when you must read a page \
yourself. Mark the todo `completed` before moving on.
3. When the last skill-todo is `completed`, emit the structured \
ResearchResult immediately. The structured response is the \
terminator — it ends the graph. Do not call any more tools.

If something is genuinely missing from the KB (e.g. founders aren't \
in any indexed source), just write "not disclosed in sources" in \
the summary for that part. Do not loop back for more searches.

Output (ResearchResult):
- `summary` — 3-6 sentences. Should cover what the company does, \
founding year, founders, and where it's based when those are in \
the KB.
- `competitors` / `local_peers` / `global_peers` — the competitors \
skill returns three labelled groups (DIRECT / LOCAL / GLOBAL); map \
each to the matching field. Only NAMED companies — never categories \
like "other astrology apps".
- `competitors` REQUIRED (≥3). `local_peers` and `global_peers` \
populated when the playbook found entries.

Never invent.

================================================================
SKILL LIBRARY:
================================================================

{skills_library}
"""


def _build_agent(
    company_name: str,
    company_domain: Optional[str],
    company_category: Optional[str] = None,
):
    today = date.today()
    prompt = ORCHESTRATOR_PROMPT.format(
        today=today.isoformat(),
        year=today.year,
        company_name=company_name,
        company_domain=company_domain or "(unknown — discover and verify the official site)",
        company_category=company_category or "(unknown — infer from the company's own pages)",
        skills_library=_load_skills_library(),
    )
    return create_deep_agent(
        model=build_chat_model(),
        tools=[
            web_search,
            index_url,
            index_wikipedia,
            fetch_url,
            wikipedia_lookup,
            index_text,
        ],
        system_prompt=prompt,
        response_format=ResearchResult,
    )


def start_research(
    name: str,
    domain: Optional[str] = None,
    category: Optional[str] = None,
) -> Task:
    """Kick off research in a background thread; return the Task for live polling."""
    task = new_task(title=f"Research: {name}")
    company = store.upsert(
        name=name, domain=domain, summary="", category=category
    )
    task.push_notice(
        "info", f"Created company record {company['id']} for '{name}'"
    )
    runtime.run_in_background(
        task, _do_research, task, company["id"], name, domain, category
    )
    return task


def _do_research(
    task: Task,
    company_id: str,
    name: str,
    domain: Optional[str],
    category: Optional[str],
) -> None:
    set_active_company(company_id)
    set_active_task(task)
    agent = _build_agent(name, domain, category)
    state = runtime.run_agent(
        agent,
        runtime.qualified_target_message(name, domain, category),
        task,
        recursion_limit=240,
    )
    result: ResearchResult = runtime.extract_structured(state)
    _persist(task, result, name, domain, category)


def _persist(
    task: Task,
    r: ResearchResult,
    name: str,
    domain: Optional[str],
    category: Optional[str],
) -> None:
    row = store.upsert(
        name=name,
        domain=domain,
        summary=r.summary,
        category=category,
        competitors=r.competitors,
        local_peers=r.local_peers,
        global_peers=r.global_peers,
    )
    task.result = {"company_id": row["id"], "summary": r.summary}
    task.status = "done"
    task.push_notice("done", f"Indexed {len(r.sources_indexed)} source(s).")
