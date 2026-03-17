# Galileo Evaluations

This folder contains a baseline evaluation suite for the multi-agent app.

## What "good" looks like

- Correct routing between GTM and Outreach behavior.
- Strong instruction adherence to the user's requested format.
- Resistance to prompt-injection style inputs.
- Generated outputs do not contain placeholder tokens like `[Your Name]`.

## Included evaluation mix

- Built-in Galileo metric: `GalileoMetrics.instruction_adherence`
- Built-in Galileo metric: `GalileoMetrics.prompt_injection`
- Custom deterministic metric: `No Placeholder Tokens`

## Dataset size

The suite uses 12 synthetic examples in `run_galileo_evals.py`.

## Run

1. Configure environment variables:
   - `GALILEO_API_KEY`
   - `GALILEO_PROJECT`
   - `GALILEO_LOG_STREAM`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run:
   - `python evals/run_galileo_evals.py`

Optional:
- `GALILEO_EXPERIMENT_NAME` to override the default experiment name.
- `GALILEO_EVAL_PROJECT` to send eval runs to a different project.
