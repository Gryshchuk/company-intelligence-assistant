---
name: business-model
description: Characterize what the company sells, how they make money, who they sell to, their pricing model, and their go-to-market. Reads pricing / product / customers pages from the company site, plus third-party analyses.
allowed-tools: [web_search, index_url, fetch_url]
---

# Business model skill

## When to use

To describe how the company operates as a business — orthogonal to
overview (general facts) and financials (funding numbers).

## Dimensions to cover

1. **What they sell** — products and services.
2. **Revenue streams** — SaaS subscription, marketplace fees, ads,
   hardware, services, licensing, freemium tier upsell, etc.
3. **Customer segments** — SMB / mid-market / enterprise / consumer /
   developers / specific verticals.
4. **Pricing model** — published tiers, per-seat vs usage-based, free
   tier presence, enterprise quote-only.
5. **Go-to-market** — self-serve, sales-led, channel / partners.

## Procedure

1. `index_url("<domain>/pricing")` — pricing tiers usually live here.
   `fetch_url` it AFTER indexing only if you need to read tier names
   for the summary.
2. `index_url("<domain>/product")`, `index_url("<domain>/customers")`,
   `index_url("<domain>/solutions")` for the rest.
3. `index_url("<domain>/about")` for the elevator pitch.
4. `web_search` for `"<company>" business model` or
   `"<company>" pricing` for third-party write-ups; `index_url` the
   promising results.

## Output

A short plain-text summary structured around the five dimensions
above. Say "not visible in sources" for any dimension you can't
verify. Do not invent.

## Rules

- Qualify every web query with the company name and domain.
- Do not infer pricing from unrelated companies.
- Prefer `index_url` over `fetch_url` — only read pages yourself when
  you need a specific value for the summary.
