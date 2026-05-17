---
name: news
description: Surface significant recent news about the company — launches, funding, hires, layoffs, partnerships, controversies — from the current and prior 12 months. Indexes articles via index_url so the bodies don't enter the agent context.
allowed-tools: [web_search, index_url, fetch_url]
---

# News skill

## When to use

To populate the "recent news" section of the company profile. Always
required.

## Procedure

Run AT LEAST 3 varied `web_search` queries. Suggested patterns
(qualify with the company name AND domain):

- `"<company>" news <current-year>`
- `"<company>" announces` / `launches` / `acquires` / `raises`
- `"<company>" CEO` / `hires` / `layoffs`
- `site:techcrunch.com "<company>"`,
  `site:bloomberg.com "<company>"`,
  `site:reuters.com "<company>"`

For each clearly relevant article URL, call
`index_url(<article url>)`. This ingests the full article without
putting it into your context.

`fetch_url` an article only when you need a specific date or quote
that isn't in the search snippet. Index FIRST, then read if needed.

## Output

A plain-text bullet list of up to 8 newsworthy items. Each entry:

- Date as `YYYY-MM`.
- One-line summary.

## Rules

- Skip stories that are obviously about a different company with a
  similar name.
- Do not invent events.
- Prefer the current year. The orchestrator will tell you the date
  in its task description.
- Prefer `index_url` over `fetch_url`. Search snippets usually carry
  enough info for the summary bullets.
