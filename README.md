# Galileo: AI Marketing Agent with Observations & Evals

This repository is a **Galileo: AI Marketing Agent with Observations & Evals** built with LangGraph.

This multi-agent system is built for two production workflows in one assistant: **GTM product support** and **outreach content execution**.  
Each user request is first routed to the correct specialist branch, then processed through branch-specific nodes that gather context, apply business gates (pricing email verification or send intent), and return a final response with full Galileo trace visibility.

- Router decides between **GTM** and **Outreach** behavior
- GTM branch answers product and pricing questions
- Outreach branch creates content, finds leads, and can send emails
- Full observability with Galileo tracing/session support

Project explainer page (GitHub Pages): [Click here for Technical Understanding Blog](https://ritvik777.github.io/Galileo_Project/)

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

## How Galileo SDK is used (Tracing + Evals)

Galileo integration in this repo is centralized and explicit:

- **Core helper layer:** `observability/galileo.py`
  - `ensure_galileo_initialized()` calls `galileo_context.init(...)`
  - `get_langchain_config(...)` injects `GalileoCallback` into LLM/tool invokes
  - `log_span(...)` wraps functions with Galileo span decorators
  - `start_chat_session(...)` starts per-chat Galileo sessions
  - `get_logger_instance()` returns the active logger for trace/session operations

- **Top-level request trace:** `agents/__init__.py`
  - `ask(question)` initializes Galileo when enabled
  - Starts top trace with `logger.start_trace(...)`
  - Concludes and flushes with `logger.conclude(...)` + `logger.flush()`

- **Node + tool spans:** `agents/router_agent/nodes.py`, `agents/gtm_agent/nodes.py`, `agents/outreach_agent/nodes.py`, `agents/tools.py`
  - Nodes/tools are decorated with `@log_span(...)`
  - LLM calls pass `config=get_langchain_config(...)` for callback-level tracing metadata

- **UI session wiring:** `ui/ui.py`
  - `handle_new_prompt(...)` starts one Galileo session per fresh chat via `start_chat_session(...)`
  - Optional console links are exposed by `get_console_links()`

- **Eval integration:** `evals/run_galileo_evals.py`
  - **Sessions mode:** `logger.start_session(...)` per dataset row
  - **Experiment mode:** `run_experiment(...)` from `galileo.experiments`
  - Uses same `ask()` path, so eval and production routing logic stay aligned

Required Galileo env vars are in `.env.example`:
- `GALILEO_API_KEY`
- `GALILEO_PROJECT`
- `GALILEO_LOG_STREAM`

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
