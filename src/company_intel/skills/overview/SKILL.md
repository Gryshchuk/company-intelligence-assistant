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
   Wikipedia article AND indexes it in one shot.
2. Index the company's own site — it is the primary source of truth
   for what they do and how they describe themselves. Always start
   with `index_url("<domain>/")` (the homepage), then add the
   `/about` / `/company` / `/about-us` page if it exists. If they
   have a `/team`, `/leadership`, or `/press` page, `index_url` those
   too — that's where founder names and dates often live.
3. **Founding year + founders are REQUIRED data points.** If steps 1-2
   didn't surface them clearly, search aggressively:
   - `web_search` for `"<company>" founded` and `"<company>" founder`.
   - `web_search` for `"<company>" CEO` (CEO is often the founder).
   - LinkedIn company page: `web_search` for
     `site:linkedin.com/company "<company>"` then `index_url` it —
     LinkedIn company pages reliably show founding year.
   - Press releases / Crunchbase / parent-company pages.
   - For each promising result, `fetch_url` (preview) to confirm it's
     the right company, then `index_url` to capture.
4. Only call `fetch_url` to read a specific page yourself; everything
   substantive must go through `index_url` / `index_wikipedia`.

## Required output (do NOT skip any line)

- What the company does (one sentence).
- **Founded:** year (and exact date if known).
- **Founder(s):** named individuals — or "not disclosed in sources"
  ONLY after you've tried Wikipedia + LinkedIn + at least one search
  for `"<company>" founder`.
- **Parent company / owner:** if the company is a subsidiary, name
  the parent (relevant here: many astrology / psychic apps are owned
  by larger holdings).
- **Headquarters:** city / country if known.
- **Size signals:** employees, customers, users — if mentioned.

If after thorough search a field is genuinely not in any source, say
"not disclosed in sources" for THAT field. Do not skip the entire
output because one item is missing.

## Rules

- Qualify any web query with the exact company name AND domain.
- If a Wikipedia or about page describes a different company that
  shares the name, do NOT index it. Try a more specific topic.
- Do not invent facts.
