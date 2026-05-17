"""Q&A agent: plans, retrieves from the company's vector + FTS store, answers."""
from __future__ import annotations

import threading
from typing import Optional

from deepagents import create_deep_agent

from .. import store
from ..config import build_chat_model
from ..eventbus import Task, TaskCallback, new_task, set_active_task
from ..tools import set_active_company
from ..tools.qa_search import keyword_search, vector_search

QA_PROMPT = """\
{company_context}

You answer questions about this company using ONLY its local knowledge \
base. You do not have web access. The knowledge base was built from \
Wikipedia, the official website, recent news, and competitor / \
funding / business-model sources.

## Answering style

**Answer directly. Do not ask the user to clarify unless the question \
is genuinely impossible to interpret.**

- If a question has multiple reasonable interpretations (e.g. "how \
much does it earn?" could mean revenue, profit, or ARR), DO NOT ask \
which one — answer for all of them. Pull every relevant figure you \
can find and present them together with their labels.
- Always use the MOST RECENT data point available in the knowledge \
base. State the year/quarter alongside each figure (e.g. "Revenue \
FY2025: $245.1B"). If older data is also notable (trend, growth), \
include it briefly.
- Reply in the same language as the question.
- Be specific and complete. Quote concrete numbers, names, dates \
when the sources have them. Don't give vague summaries when figures \
exist.

## Process

1. Call `write_todos` to lay out a short retrieval plan covering every \
plausible interpretation of the question — one todo per sub-topic. For \
"how much does it earn?": revenue, net income, operating income, ARR, \
gross profit (whichever the company actually reports).
2. Work the plan step by step. For each todo:
   - Call `vector_search` with a focused query.
   - If you need exact figures, names, or proper nouns, also call \
     `keyword_search` for those terms.
3. When all todos are done, compose the answer:
   - Lead with the direct response — numbers first, prose second.
   - Cite the `[source]` of each fact you use (the source label \
     appears at the start of each retrieved chunk).
   - If the knowledge base has nothing about a specific aspect, say \
     so for THAT aspect only and still answer the rest. Never refuse \
     the whole question over one missing detail.

## When to ask back

Only if the question references something the agent cannot identify \
in the KB at all (e.g. "what about their X product" and there's no X \
in the KB). Even then, give a partial answer first ("I don't see an \
'X' product in our sources — here's what I do have about their \
products: …") instead of asking blind.

## Output format — STRICT

Your final message MUST contain ONLY the prose answer to the user. \
NEVER include:
- Your todo list or any JSON like `{{"todos":[...]}}`.
- Tool call arguments, plans, or intermediate reasoning.
- "Here is my plan", "Step 1", "Working on", etc.

The user sees only your final message. Everything before it (plan, \
searches) happens behind the scenes — do not echo any of it.
"""


def _build_agent(company_name: str, domain: Optional[str]):
    ctx = f"You are answering questions about the company **{company_name}**"
    if domain:
        ctx += f" (web domain: {domain})"
    ctx += "."
    return create_deep_agent(
        model=build_chat_model(),
        tools=[vector_search, keyword_search],
        system_prompt=QA_PROMPT.format(company_context=ctx),
    )


def _message_text(msg) -> str:
    """Extract user-facing prose from an AIMessage.

    Only text-typed parts count — tool-use / reasoning parts are skipped.
    Leading JSON blobs (the model occasionally echoes its `write_todos`
    arguments) are also stripped as a belt-and-braces guard against the
    prompt rule failing.
    """
    content = getattr(msg, "content", msg)
    if isinstance(content, str):
        return _strip_leading_json(content)
    if isinstance(content, list):
        parts = []
        for p in content:
            if not isinstance(p, dict):
                continue
            # Accept untagged dicts or those explicitly typed as text.
            if p.get("type") in (None, "text", "output_text"):
                t = p.get("text", "")
                if isinstance(t, str) and t.strip():
                    parts.append(t)
        return _strip_leading_json("".join(parts).strip())
    return _strip_leading_json(str(content))


def _strip_leading_json(text: str) -> str:
    """If the message starts with a balanced JSON object/array, drop it."""
    text = text.lstrip()
    if not text or text[0] not in "{[":
        return text
    open_ch, close_ch = text[0], "}" if text[0] == "{" else "]"
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[i + 1:].lstrip()
    return text


def start_qa(company_id: str, question: str) -> Task:
    company = store.get(company_id)
    if company is None:
        raise ValueError(f"Unknown company {company_id}")
    task = new_task(title=f"Q&A: {question[:60]}")

    def run():
        try:
            set_active_company(company_id)
            set_active_task(task)
            agent = _build_agent(company["name"], company.get("domain"))
            cb = TaskCallback(task)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]},
                config={"callbacks": [cb], "recursion_limit": 25},
            )
            task.result = {"answer": _message_text(result["messages"][-1])}
            task.status = "done"
        except Exception as e:
            task.status = "error"
            task.error = str(e)
            task.push_notice("error", str(e))

    threading.Thread(target=run, daemon=True).start()
    return task
