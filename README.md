# Galileo Marketing Assistant (Multi-Agent LangGraph)

This repository is a **multi-agent marketing assistant** built with LangGraph.

- Router decides between **GTM** and **Outreach** behavior
- GTM branch answers product and pricing questions
- Outreach branch creates content, finds leads, and can send emails
- Full observability with Galileo tracing/session support

Project explainer page (GitHub Pages): `index.html`

---

## Architecture (Current)

### Graph flow

```text
START -> classify
          |- gtm      -> gtm_retrieve -> pricing_gate --not_pricing--> gtm_generate -> END
          |                                         \--pricing-------> collect_email --valid--> gtm_generate -> END
          |                                                                            \--no_email----------> END
          |
          \- outreach -> outreach_research -> outreach_generate -> send_gate --review--> END
                                                                     \--send------------> outreach_send -> END
```

### Agents

- **Router Agent** (`agents/router_agent/nodes.py`)
  - Uses rule-based hints first, then LLM fallback
  - Routes to `gtm` or `outreach`

- **GTM Agent** (`agents/gtm_agent/nodes.py`)
  - Retrieves context from internal KB + web
  - Pricing gate requires verified email before full pricing output
  - Generates final product/pricing response

- **Outreach Agent** (`agents/outreach_agent/nodes.py`)
  - Researches context (and uses Apollo for lead-intent prompts)
  - Generates marketing content (email/post)
  - Send gate determines review-only vs actual send via SendGrid

### Shared state

Defined in `agents/state.py`:

- `question`
- `agent_type`
- `context`
- `answer`
- `is_pricing`
- `user_email`
- `send_requested`
- `steps` (merged pipeline trace)

---

## Key files

```text
app.py                          # Streamlit entrypoint
ui/ui.py                        # Sidebar, chat, trace rendering
agents/graph.py                 # LangGraph node wiring
agents/router_agent/nodes.py    # classify + route
agents/gtm_agent/nodes.py       # GTM branch nodes
agents/outreach_agent/nodes.py  # Outreach branch nodes
agents/tools.py                 # KB/web/Apollo/SendGrid tools + tool loop
vector_db/database.py           # Qdrant store/search and collection checks
vector_db/chunker.py            # text/pdf chunking
vector_db/embeddings.py         # Gemini embeddings model
observability/galileo.py        # tracing/session setup
evals/run_galileo_evals.py      # baseline evaluation suite
```

---

## Tech stack

| Component | Technology |
|---|---|
| Orchestration | LangGraph |
| LLM | Anthropic (`ChatAnthropic`) |
| Embeddings | Google Gemini embeddings (`gemini-embedding-001`) |
| Vector DB | Qdrant Cloud |
| Web Search | DuckDuckGo |
| Leads | Apollo API |
| Email | SendGrid |
| UI | Streamlit |
| Observability / Evals | Galileo |

---

## Setup and run

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp .env.example .env
```

Fill `.env` with your values:

- Core:
  - `GOOGLE_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
- Optional outreach features:
  - `APOLLO_API_KEY`
  - `SENDGRID_API_KEY`
  - `SENDGRID_FROM_EMAIL`
- Observability/evals:
  - `GALILEO_API_KEY`
  - `GALILEO_PROJECT`
  - `GALILEO_LOG_STREAM`

### 3) Start app

```bash
streamlit run app.py
```

---

## Evaluations

Run baseline eval suite:

```bash
python evals/run_galileo_evals.py
```

Experiment mode:

```bash
GALILEO_EVAL_MODE=experiment python evals/run_galileo_evals.py
```

See full eval documentation in `evals/README.md`.

---

## GitHub Pages (branch deploy)

This repo uses root `index.html` for docs page.

In GitHub settings:

- Pages source: **Deploy from a branch**
- Branch: `main`
- Folder: `/(root)`

Then open:

- `https://ritvik777.github.io/Galileo_Project/`
