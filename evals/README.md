# Galileo Evaluations

This folder contains a baseline evaluation suite for the multi-agent app.

## What "good" looks like

- Correct routing between GTM and Outreach behavior.
- Strong instruction adherence to the user's requested format.
- Resistance to prompt-injection style inputs.
- Generated outputs do not contain placeholder tokens like `[Your Name]`.

## Metrics

- No metrics are hardcoded in `run_galileo_evals.py`.
- Configure and run metrics directly in the Galileo UI.
- Routing LLM-as-judge prompt template is available at:
  - `evals/prompts/routing_agent_judge_prompt.md`

## Dataset size

The suite uses 15 synthetic examples in `run_galileo_evals.py`.

## Run

1. Configure environment variables:
   - `GALILEO_API_KEY`
   - `GALILEO_PROJECT`
   - `GALILEO_LOG_STREAM`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python evals/run_galileo_evals.py`
   - Default mode logs each use case as a separate Galileo session.
   - To run as a Galileo Experiment instead:
     - `GALILEO_EVAL_MODE=experiment python evals/run_galileo_evals.py`

Optional:
- `GALILEO_EXPERIMENT_NAME` to override the default experiment name.
- `GALILEO_EVAL_PROJECT` to send eval runs to a different project.
