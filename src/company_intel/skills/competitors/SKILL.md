---
name: competitors
description: Identify three groups of comparable companies — direct competitors (offer the same product), local-market peers (same industry in the company's country/region), and global peers (same industry worldwide). Uses index_url so pages are ingested without flooding your context.
allowed-tools: [web_search, index_url, fetch_url]
---

# Competitors skill

## When to use

Always required. Populates the company's competitor profile in three
flavours.

## What "comparable" means here

You're returning THREE distinct lists, do not mix them:

1. **Direct competitors** — companies whose product directly substitutes
   for ours (e.g. Figma → Sketch, Adobe XD, Penpot).
2. **Local-market peers** — companies in the SAME industry vertical
   operating in the same country / region as our target. They may not
   be direct substitutes; they share the local market context.
   Examples for a Ukrainian fintech: monobank, Sense Bank, Privat24.
3. **Global peers** — companies in the same broad industry / category
   anywhere in the world. These are the "category leaders" or "notable
   players" people might compare us to even without direct overlap.

If you can't determine the company's home country from indexed sources
or its domain TLD, fall back to listing only direct + global peers and
note that locality couldn't be determined.

## Procedure (in priority order)

### Step 1 — Direct competitors

1. **Tracxn** — `web_search` for
   `site:tracxn.com "<company>" competitors`. If a Tracxn page is
   returned, `index_url(<tracxn url>)` (competitors live under
   `#competitors`, funding under `#funding-and-investors`).
2. **Crunchbase** — search, then `index_url(<crunchbase url>)`.
3. **G2 / Capterra / Gartner** — find the product category page; if
   it's the "alternatives to <company>" page, `index_url` it.
4. **Direct queries** as fallback: `"<company>" competitors`,
   `"<company>" vs`, `alternatives to "<company>"`.

### Step 2 — Local-market peers

First identify the company's home market (country or region) from the
overview / about page already indexed.

Then search the SAME INDUSTRY in that market:

- `<industry/category> companies <country>`
- `top <industry> startups <country>`
- `leading <industry> <country>`
- `<country> <industry> directory` (Built In, AIN, Dou.ua,
  DACH-startups, etc. — region-specific tech directories)
- `site:<local-tech-press-domain> <industry>` (e.g.
  `site:ain.ua fintech`, `site:sifted.eu <category>` for EU)

`index_url` any list page that names 5+ companies in the vertical.

### Step 3 — Global peers

Search the industry without geographic qualifier:

- `top <industry> companies`
- `leading <industry> platforms`
- `<industry> market leaders <current-year>`
- `site:builtin.com <industry>`
- `site:g2.com category:<category>`
- `<industry> Magic Quadrant` (for B2B / enterprise verticals)

`index_url` any directory or roundup page that names several
companies.

## Output

Return a plain-text response with THREE labelled sections, e.g.:

```
DIRECT COMPETITORS:
- Sketch — design tool, Mac-only, predates Figma
- Adobe XD — Adobe's competing prototyping tool
- ...

LOCAL-MARKET PEERS (US):
- Canva — graphics platform, US-active
- Webflow — visual web builder, San Francisco
- ...

GLOBAL PEERS (design / collaboration software):
- Miro — visual collaboration whiteboard
- Notion — collaborative docs
- ...
```

Aim for 3-8 in DIRECT, 3-5 in LOCAL, 3-5 in GLOBAL. Use the exact
labels above (DIRECT COMPETITORS / LOCAL-MARKET PEERS / GLOBAL PEERS)
so the orchestrator can parse them.

## Rules

- Qualify every query with relevant qualifiers (industry, country,
  current year). Avoid bare-word searches.
- Never invent. Only list companies that appeared in your sources.
- Do not put the same company in two groups. If something fits both
  direct and local-peer, prefer the more specific bucket (direct).
- Do not include the target company itself in any list.
- Vary phrasing across queries — no identical repeats.
- Prefer `index_url` over `fetch_url`. Read pages yourself only when
  you can't extract what you need from search snippets.
