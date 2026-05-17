---
name: financials
description: Gather a comprehensive financial profile — funding rounds, valuation, investors, AND year-by-year revenue / profit / margin figures for the current and previous fiscal year. Tracxn / Crunchbase first, then PitchBook / Owler / Dealroom, then earnings releases and financial press. Indexes every page so all numbers stay searchable.
allowed-tools: [web_search, index_url, fetch_url]
---

# Financials skill

## When to use

To build the company's financial profile. Required.

## What to capture

You're collecting two layers:

### A. Capital & ownership
- Total raised across all rounds.
- Latest round: stage, amount, date.
- Latest valuation (post-money).
- Lead investors and notable backers.
- IPO date and ticker if public.
- Recent M&A activity (acquired, acquirer, divestitures).

### B. Operating financials — current FY AND previous FY (or four most
recent quarters when only quarterly data is published)

For EACH of the two years/periods, try to capture every metric the
company actually reports:

- Revenue (top line).
- Revenue growth YoY (%).
- Gross profit / gross margin.
- Operating income / operating margin.
- Net income / net margin.
- EBITDA / adjusted EBITDA.
- ARR or run-rate (for SaaS/subscription businesses).
- Free cash flow.
- R&D spend, sales-and-marketing spend (if disclosed).
- Customer count, employee count, headcount growth.

Mark anything not disclosed as "not disclosed" — do NOT fabricate.
Private companies usually disclose only a subset; that's fine.

## Procedure (in priority order)

1. **Tracxn** — `web_search` for `site:tracxn.com "<company>" funding`,
   then `index_url(<tracxn url>)`. Tracxn pages include both funding
   data and select operating metrics.
2. **Crunchbase** — search, then `index_url` the company profile.
3. **PitchBook / Owler / Dealroom** — `index_url` what surfaces.
4. **Annual reports / 10-K / 10-Q** (public companies) — search
   `"<company>" annual report <current-year>` or
   `"<company>" 10-K <current-year>`; `index_url` the press-release
   page or the investor-relations summary URL (NOT the raw PDF —
   trafilatura can't extract PDFs).
5. **Earnings releases** — for the last two reported periods, search
   `"<company>" earnings <quarter> <year>` and `index_url` the
   release page.
6. **Investor pages** — `index_url("<domain>/investors")` if the
   company is public or VC-backed and has one.
7. **Financial press** — Bloomberg, Reuters, TechCrunch, Forbes for
   commentary on the latest results; `index_url` substantive articles.

Always qualify queries with the company's name AND domain to avoid
hitting a similarly-named entity.

## Indexing discipline

This skill exists partly so the Q&A agent can later answer questions
like "what was their Q3 revenue?" or "how did margins change YoY?".
That works only if the source pages are in the vector store.

- **Prefer `index_url`** for every relevant page. Each page becomes
  searchable chunks.
- Use `fetch_url` only when you must read a specific figure that you
  can't extract from a search snippet. After reading, `index_url` the
  same URL so the page is also in the KB.
- Do NOT skip indexing earnings releases just because you already
  extracted the headline number — the article often has line items
  the Q&A agent will need.

## Output

The orchestrator does not require a structured `financials` field.
Return a short plain-text summary for the orchestrator's overview,
covering:

- Capital: total raised, latest round (stage/amount/date), latest
  valuation, lead investors.
- Operating: revenue for current FY and previous FY (with % growth),
  plus profitability indicator (net income or EBITDA, with margin).
- Note "not disclosed in sources" for anything you couldn't find.

Detailed line items don't need to appear in this summary — they live
in the indexed sources, and Q&A will retrieve them on demand.

## Rules

- Do not invent numbers. If unsure, say "not disclosed".
- Always include the period (FY2025, Q3 2025, etc.) next to every
  figure — never a bare number.
- Prefer `index_url` over `fetch_url` to keep your context small.
