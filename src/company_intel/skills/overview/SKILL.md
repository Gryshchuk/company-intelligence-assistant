---
name: overview
description: Collect a company's general overview — what they do, year founded, headquarters, founders, size signals — from Wikipedia and the official about page. Indexes both sources directly to keep your context small.
allowed-tools: [index_wikipedia, index_url, fetch_url]
---

# Overview skill

## When to use

The very first step of researching a company. Establishes the baseline
facts the other skills build on.

## Procedure

1. Call `index_wikipedia(<company full name>)`. This fetches the
   Wikipedia article AND indexes it in one shot. The article text
   does NOT enter your context — you only get a chunk count back.
2. Call `index_url("<domain>/about")` (or `<domain>/company` if that
   exists instead). Same: fetched and indexed in one shot.
3. Only call `fetch_url(<url>)` if you genuinely need to read a page
   yourself to extract a specific fact. It returns a 6k-char preview.

## Output

Return a short plain-text summary covering:

- What the company does (one sentence).
- Year founded, headquarters, founders if known.
- Size signals if mentioned (employees, customers).

If you need specific facts you don't already know, use the orchestrator's
later `vector_search` to query the knowledge base — do not refetch.

## Rules

- Qualify any web query with the exact company name AND domain.
- If a Wikipedia or about page describes a different company that
  shares the name, do NOT index it. Try a more specific topic.
- Do not invent facts.
