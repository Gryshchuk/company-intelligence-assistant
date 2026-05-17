# Company Intelligence Assistant

A Streamlit app that researches a company end-to-end with a deep agent,
then lets you ask grounded questions about it from a per-company
knowledge base.


## Brief

> Accept a company name (e.g. *Figma*, *Spotify*, *Airbnb*),
> automatically gather content from public sources (the official site,
> Wikipedia, news, Crunchbase, …), structure and store it locally
> (embeddings / search-friendly format), and expose a chat interface
> where the user can ask things like *"Who are their competitors?"*,
> *"What is their business model?"*, *"When was the company founded?"*,
> *"How do they make money?"*. All answers must come **solely** from
> the stored data — no live web access during chat.

---

## 1 · What it does

- **Disambiguate** an input name — if `Nebula` could mean five things,
  ask which one (with web-discovered candidates).
- **Research** the chosen company across Wikipedia, the official site,
  recent news, Crunchbase / Tracxn, G2 / Capterra. Indexes every
  substantive page into a vector + full-text store.
- **Identify peers in three groups** — direct competitors,
  local-market peers (same vertical, same country), global peers.
- **Q&A** — chat with each company. The Q&A agent has no web access;
  it answers strictly from the indexed knowledge base via semantic +
  keyword search.
- **Live activity pane** — plan (todos), every tool call (expandable),
  chat + embedding token usage, cost, compaction events.

---

## 2 · Tech stack

| Layer | Choice |
|---|---|
| LLM | OpenAI `gpt-5.4-mini` via [LangChain](https://docs.langchain.com) |
| Agent framework | [`deepagents`](https://docs.langchain.com/oss/python/deepagents/overview) — planning + skills + filesystem + summarisation middleware |
| Skills | [Anthropic Agent Skills](https://docs.langchain.com/oss/python/deepagents/skills) format (`SKILL.md` + YAML frontmatter) |
| UI | Streamlit (single-process, async log via 1-second fragments) |
| Vector + FTS | [LanceDB](https://lancedb.com) — one table per company |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dim) |
| Web search | Tavily |
| Page extraction | trafilatura |
| Wikipedia | `wikipedia-api` |
| Token counting | tiktoken (cl100k_base) |

---

## 3 · Running it

### Local (uv / venv)

```bash
cp .env.example .env        # then fill in the keys below
uv sync                     # or: pip install -e .
streamlit run app.py
```

Open <http://localhost:8501>.

### Docker

```bash
cp .env.example .env        # then fill in the keys below
docker compose up --build
```

Open <http://localhost:8501>. The `./data` directory is mounted as a
volume — LanceDB tables and `companies.json` survive container
restarts.

### Required environment variables

| Key | Purpose |
|---|---|
| `OPENAI_API_KEY` | Chat model, embeddings, structured-output calls. **Required.** |
| `TAVILY_API_KEY` | Web search for the research and disambiguation agents. **Required.** |

Both go in `.env` (gitignored). See [`.env.example`](.env.example).

---

## 4 · Components

```
┌─────────────────────────────────────────────────────────────────┐
│  Streamlit UI  (src/company_intel/ui/)                          │
│  ├─ theme  ├─ state  ├─ sidebar  ├─ log_pane  └─ views/         │
└──────────────────────────┬──────────────────────────────────────┘
                           │ launches via state.start_*_flow
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Agents  (src/company_intel/agents/)                            │
│  ├─ disambiguation  ├─ research  └─ qa                          │
│  Each runs in a background thread; events stream to eventbus.   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ uses
                           ▼
┌──────────────┐   ┌─────────────────┐   ┌───────────────────────┐
│  Skills      │   │  Tools          │   │  Vector storage       │
│  SKILL.md    │   │  index_url      │   │  LanceDB + tiktoken   │
│  playbooks   │   │  index_wiki     │   │  one table / company  │
│  per topic   │   │  web_search     │   │  vector + FTS index   │
└──────────────┘   │  fetch_url      │   └───────────────────────┘
                   │  wikipedia      │
                   │  qa_search      │
                   └─────────────────┘
```

**Deep agent** — `deepagents.create_deep_agent`. Built-ins: `write_todos`,
filesystem ops, `task`, summarisation (auto-compacts at 85% of the
model's 400k context). We add: `web_search`, `fetch_url`,
`wikipedia_lookup`, plus the three indexers below.

**Skills** ([`skills/`](src/company_intel/skills/)) — `SKILL.md` files
the research orchestrator inlines into its prompt at build time:
`overview`, `competitors`, `financials`, `business-model`, `news`.
Each is a focused playbook (sources, queries, output shape, rules).
Editing a skill needs no code change.

**Tools** ([`tools/`](src/company_intel/tools/)) — leaf-level Python
functions. The three indexer tools (`index_url`, `index_wikipedia`,
`index_text`) fetch + chunk + embed in one shot and return only a
count, keeping page bodies out of the agent's context. `fetch_url` and
`wikipedia_lookup` return ~6k-char previews only.

**Vector storage** ([`vectordb.py`](src/company_intel/vectordb.py)) —
LanceDB connection, one table per company (`c_<id>`). Text is chunked
to ~1200 chars / 150 overlap, embedded with `text-embedding-3-small`,
and indexed for both vector and full-text (FTS) search. FTS is built
lazily on first keyword search.

**User session** — Streamlit `session_state`, initialised once in
[`ui/state.py`](src/company_intel/ui/state.py). Tracks current view,
current company, the active background task (so the live log can
follow it across navigation), pending disambiguation, chat transcripts
per company. Agent kick-offs go through `start_*_flow` helpers — no
view talks to agents directly.

**Model** — single source of truth in
[`config.py:build_chat_model()`](src/company_intel/config.py). Wraps
`init_chat_model("openai:gpt-5.4-mini")` with `max_retries=6` for TPM
backoff. The auto-populated `model.profile` (max_input_tokens=400k,
tool_calling, structured_output) drives the summarisation middleware's
fraction-based compaction thresholds.

---

## License

MIT
