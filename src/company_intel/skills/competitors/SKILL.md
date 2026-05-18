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
   for ours (e.g. Figma → Sketch, Adobe XD, Penpot). You should always dinf competitor list
2. **Local-market peers** — companies in the SAME industry vertical
   operating in the same country / region as our target. They may not
   be direct substitutes; they share the local market context.
   Examples for a Ukrainian fintech: monobank, Sense Bank, Privat24.
3. **Global peers** — companies in the same broad industry / category
   anywhere in the world. These are the "category leaders" or "notable
   players" people might compare us to even without direct overlap.

## CRITICAL — named companies only

Every entry in every list MUST be a **specific named company** (e.g.
"Co-Star", "Sanctuary", "Purple Garden", "Keen"). Generic categories
like "other astrology apps", "psychic platforms", "online tarot
services" are NOT acceptable competitors. If you only have categories
after your first pass, the skill is NOT done — you must do another
search round (see retry rule below) until you have named companies.

A company's own marketing pages rarely name competitors. So if the
TARGET company's own site says "unlike other X apps" without naming
them, that is a **signal to leave the site** and hit third-party
comparison sources.

If you can't determine the company's home country from indexed sources
or its domain TLD, fall back to listing only direct + global peers and
note that locality couldn't be determined.

## DO NOT start with the company's own site

The TARGET company's own about / faq / press pages will almost never
name competitors — that's a marketing choice. Do not index them
looking for competitor names; you'll just get "we stand out from
other X apps" with no actual names. Always go to **third-party
sources** for competitor identification.

## Procedure (in priority order)

### Step 1 — Direct competitors

**Run these Google-style searches FIRST. They are the most reliable
source of named competitors.** The orchestrator already gave you the
company's **category** (e.g. "astrology app", "design tool", "food
delivery") — USE IT in every query, don't search by bare name. Do at
least 5 of these:

- `top companies in <category>` — review roundups
- `best <category>` — comparison articles
- `alternatives to "<company>"`
- `top 10 solutions in <category>`
- `"<company>" vs` — autocomplete-style; comparison articles


For every result page that names ≥2 competitors, `index_url(<url>)`.

Once you have a few named candidates from Google, you can ALSO
consult these third-party directories for cross-reference:

1. **Crunchbase** — same pattern, same verification.
2. **G2 / Capterra / Gartner** — alternatives pages.

If after Step 1 + 2 you still have fewer than 3 named competitors,
the company may be in a smaller niche — search by exact category
synonyms (e.g. "tarot reading app", "horoscope app", "spiritual
guidance app" for an astrology product) until you have ≥3 names.

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

## Retry rule

After your first pass, check what you have. If fewer than 3 NAMED
companies in `DIRECT COMPETITORS` (or fewer than 2 in each peer
group), do another search round. Useful follow-ups:

- `top <category> apps <current-year>` — e.g. `top astrology apps 2026`
- `best <category> apps for <use case>` — e.g.
  `best psychic reading app for live chat`
- `<category> app comparison` / `<category> apps reviews` — review
  sites name multiple players in one article
- `vs <target-company>` — e.g. `Co-Star vs Nebula`,
  `Sanctuary vs Nebula` (try a likely competitor name as a probe)
- `app store category <category>` — search for the App Store /
  Play Store category leaders

Index the most substantive result pages (`index_url`) so the names
are searchable for Q&A later.

## Rules

- Qualify every query with relevant qualifiers (industry, country,
  current year). Avoid bare-word searches.
- Never invent. Only list companies that appeared in your sources.
- Categories ≠ competitors — do not return "other X platforms" as if
  it were a competitor.
- Do not put the same company in two groups. If something fits both
  direct and local-peer, prefer the more specific bucket (direct).
- Do not include the target company itself in any list.
- Vary phrasing across queries — no identical repeats.
- Prefer `index_url` over `fetch_url`. Read pages yourself only when
  you can't extract what you need from search snippets.
