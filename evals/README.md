# Galileo Evaluations and Project Run Guide

This folder contains the evaluation harness for the current **multi-agent Galileo Marketing Assistant**.
The system is designed to run two branches from one entrypoint: **GTM support** and **Outreach execution**.  
Runtime flow is: classify request -> run branch nodes -> apply gate logic -> produce answer/send action, with Galileo tracing and eval logging across the full path.

**Click here for Technical Understanding Blog:** [https://ritvik777.github.io/Galileo_Project/](https://ritvik777.github.io/Galileo_Project/)

## Galileo SDK placement in code (quick map)

- `observability/galileo.py`
  - Initializes Galileo context (`ensure_galileo_initialized`)
  - Adds LangChain callback config (`get_langchain_config`)
  - Exposes span decorator (`log_span`)
  - Starts chat sessions (`start_chat_session`)
  - Returns logger/helpers (`get_logger_instance`, `get_console_links`)

- `agents/__init__.py`
  - `ask(...)` starts top-level trace with `logger.start_trace(...)`
  - flush/conclude lifecycle handled in same function

- Node + tool files:
  - `agents/router_agent/nodes.py`
  - `agents/gtm_agent/nodes.py`
  - `agents/outreach_agent/nodes.py`
  - `agents/tools.py`
  - Each uses `@log_span(...)`; LLM invokes use `get_langchain_config(...)`

- `ui/ui.py`
  - Starts one Galileo session per new chat thread via `start_chat_session(...)`

- `evals/run_galileo_evals.py`
  - Sessions mode: `logger.start_session(...)` per example
  - Experiment mode: `run_experiment(...)` from Galileo SDK
  - Uses the same `ask()` runtime path as the app

The app has:

- A **Router agent** (`gtm` vs `outreach`)
- A **GTM branch** (retrieval, pricing gate, email collection, answer generation)
- An **Outreach branch** (research, content generation, send gate, optional SendGrid delivery)

The eval runner executes this same production path by calling `agents.ask(...)`, so eval behavior matches runtime behavior.

---

## What this project does

At runtime, one user message flows through `agents/graph.py`:

1. `classify` routes to `gtm` or `outreach`
2. GTM path:
   - `gtm_retrieve`
   - `pricing_gate`
   - optional `collect_email`
   - `gtm_generate`
3. Outreach path:
   - `outreach_research`
   - `outreach_generate`
   - `send_gate`
   - optional `outreach_send`

The shared state lives in `agents/state.py` (`question`, `agent_type`, `context`, `answer`, `is_pricing`, `user_email`, `send_requested`, `steps`).

---

## What this eval suite checks

`run_galileo_evals.py` currently uses **17 synthetic test prompts** across:

- GTM product + pricing behavior
- Outreach draft generation behavior
- Explicit send intent behavior
- Apollo lead generation behavior
- Adversarial / robustness prompts
- Mixed intent edge cases

Declared quality goals:

- Correct routing (GTM vs Outreach)
- Instruction following (format/content intent)
- Prompt-injection robustness
- No obvious placeholder outputs (example: `[Your Name]`)

---

## Tool coverage check (sessions mode)

In default `sessions` mode, each case logs pipeline steps and the script parses observed tools from `steps`.

Expected tool coverage:

- `search_knowledge_base`
- `web_search`
- `apollo_search`
- `send_email`

At the end, it prints PASS/fail coverage summary.

---

## Run the full project locally

From repo root:

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Create env file

```bash
cp .env.example .env
```

3. Fill required `.env` values

- Core app:
  - `GOOGLE_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `QDRANT_URL`
  - `QDRANT_API_KEY`
- Outreach optional features:
  - `APOLLO_API_KEY` (lead search)
  - `SENDGRID_API_KEY`
  - `SENDGRID_FROM_EMAIL`
- Galileo observability/evals:
  - `GALILEO_API_KEY`
  - `GALILEO_PROJECT`
  - `GALILEO_LOG_STREAM`

4. Run app

```bash
streamlit run app.py
```

---

## Run evaluations

### Mode A: Sessions (default)

Each prompt is logged as a separate Galileo session.

```bash
python evals/run_galileo_evals.py
```

### Mode B: Experiment

Runs with Galileo Experiments API:

```bash
GALILEO_EVAL_MODE=experiment python evals/run_galileo_evals.py
```

Optional env overrides:

- `GALILEO_EXPERIMENT_NAME`
- `GALILEO_EVAL_PROJECT`

---

## Notes

- The eval harness calls the same `ask()` entrypoint as the UI, reducing eval/prod drift.
- If Galileo env vars are missing, eval logging will fail because the script expects logger initialization for sessions/experiments.
