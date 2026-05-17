"""Research orchestrator. Loads the SKILL.md library and delegates per topic."""
from __future__ import annotations

import threading
from datetime import date
from pathlib import Path
from typing import Optional

from deepagents import create_deep_agent

from .. import store
from ..config import build_chat_model
from ..eventbus import Task, TaskCallback, new_task, set_active_task
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
You are a company research analyst. You follow a library of skill \
playbooks — each one is a focused procedure for a specific research \
topic. Today's date is {today} (current year: {year}).

Target identity (DO NOT change):
- Company name: **{company_name}**
- Web domain: {company_domain}

Many companies share similar names. ALWAYS qualify queries with this \
exact name AND the domain. If a source describes a different company \
with a similar name, IGNORE it.

Token discipline (critical — we have a 200k TPM ceiling):
- **Prefer `index_url(url)` and `index_wikipedia(topic)`** to bring \
content into the knowledge base. They ingest the full page and return \
only a chunk count — the page body never enters your context.
- Use `fetch_url` / `wikipedia_lookup` only when you must read a \
specific page yourself; both return at most ~6000 characters as a \
preview, not the full body.
- `index_text(source, text)` is for content you've already extracted \
in conversation (e.g. a search snippet you want preserved). Do NOT \
use it after `fetch_url` just to re-index the same page — call \
`index_url` instead.

Knowledge-base discipline — index aggressively, anything that could be \
useful later for Q&A:
- The Q&A agent that runs after research has NO web access and can \
ONLY answer from what you index. Anything you don't index is lost.
- For every URL or Wikipedia topic that contains substantive facts \
about THIS company — `index_url` / `index_wikipedia` it. Err on the \
side of more indexing, not less. The cheap path is cheap.
- Beyond what the skills explicitly require, index any page that \
contains: leadership names, customer logos / case studies, product \
documentation pages, technology stack info, partnerships, press \
mentions, regulatory filings, controversies, hiring trends — basically \
anything a future user might reasonably ask about.
- When `web_search` returns a result that looks substantive but you \
don't need to read it yourself, you can still pass the URL to \
`index_url` to capture it. Don't skip a useful source just because you \
don't need it for the structured response.
- If a search snippet contains a concrete fact (a date, a number, a \
name) that isn't on any page you indexed, capture it with \
`index_text("web_search:<query>", "<snippet text>")` so Q&A can \
retrieve it later.

Process:
1. Call `write_todos` to lay out the plan — one todo per skill listed \
in the SKILL LIBRARY below. Do NOT skip any skill.
2. For each todo, follow that skill's playbook EXACTLY. Each skill \
indexes its sources via the cheap `index_url` / `index_wikipedia` \
path. Mark the todo completed before moving to the next.
3. When all skills have run, return the structured ResearchResult.

Output rules:
- Do not duplicate work — each topic is handled by exactly one skill.
- The competitors playbook returns THREE labelled groups: \
DIRECT COMPETITORS, LOCAL-MARKET PEERS, GLOBAL PEERS. Map each group \
into the matching structured field (`competitors`, `local_peers`, \
`global_peers`). Do NOT collapse them into one list.
- `competitors` is REQUIRED (aim 3-8). `local_peers` and \
`global_peers` should be populated when the playbook found entries; \
empty list is acceptable only if it genuinely couldn't.
- `summary` is 3-6 sentences synthesised from what the playbooks \
found. Do not invent.

================================================================
SKILL LIBRARY — your canonical playbooks, follow them step by step:
================================================================

{skills_library}
"""


def _build_agent(company_name: str, company_domain: Optional[str]):
    today = date.today()
    prompt = ORCHESTRATOR_PROMPT.format(
        today=today.isoformat(),
        year=today.year,
        company_name=company_name,
        company_domain=company_domain or "(unknown — discover and verify the official site)",
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


def start_research(name: str, domain: Optional[str] = None) -> Task:
    """Kick off research in a background thread; return the Task for live polling."""
    task = new_task(title=f"Research: {name}")
    company = store.upsert(name=name, domain=domain, summary="")
    task.push_notice("info", f"Created company record {company['id']} for '{name}'")

    def run():
        try:
            set_active_company(company["id"])
            set_active_task(task)
            agent = _build_agent(name, domain)
            cb = TaskCallback(task)
            user_msg = (
                f"Research the company **{name}**"
                + (f" (web domain: {domain})" if domain else "")
                + ". This exact entity — not any similarly-named company."
            )
            # Use stream so we can watch for compaction events as they happen
            # and push them into the activity log. Last yielded value is the
            # final state — same shape as agent.invoke() would return.
            result = None
            seen_compactions = 0
            for state in agent.stream(
                {"messages": [{"role": "user", "content": user_msg}]},
                config={"callbacks": [cb], "recursion_limit": 240},
                stream_mode="values",
            ):
                result = state
                event = state.get("_summarization_event") if isinstance(state, dict) else None
                if event:
                    # cutoff_index changes each time a new compaction happens.
                    msgs = state.get("messages") or []
                    summarised_msgs = event.get("cutoff_index", 0)
                    file_path = event.get("file_path")
                    fingerprint = (summarised_msgs, file_path)
                    if fingerprint not in getattr(run, "_seen", set()):
                        run._seen = getattr(run, "_seen", set()) | {fingerprint}
                        seen_compactions += 1
                        suffix = f" (history saved to {file_path})" if file_path else ""
                        task.push_notice(
                            "compaction",
                            f"🗜 Compacted: summarised {summarised_msgs} older message(s); "
                            f"kept the most recent {max(0, len(msgs) - summarised_msgs)}.{suffix}",
                        )
            structured: ResearchResult = (
                result.get("structured_response") or result.get("response")
            )
            if structured is None:
                raise RuntimeError("Agent did not return a structured response.")
            row = store.upsert(
                name=name,
                domain=domain,
                summary=structured.summary,
                competitors=structured.competitors,
                local_peers=structured.local_peers,
                global_peers=structured.global_peers,
            )
            task.result = {
                "company_id": row["id"],
                "summary": structured.summary,
            }
            task.status = "done"
            task.push_notice(
                "done",
                f"Indexed {len(structured.sources_indexed)} source(s).",
            )
        except Exception as e:
            task.status = "error"
            task.error = str(e)
            task.push_notice("error", str(e))

    threading.Thread(target=run, daemon=True).start()
    return task
