from agents.state import AgentState
from llm import get_llm
from observability import get_langchain_config, log_span

OUTREACH_HINTS = {
    "email",
    "send email",
    "mail",
    "linkedin",
    "post",
    "marketing",
    "market",
    "campaign",
    "outreach",
    "lead",
    "prospect",
    "copy",
    "cold email",
}


def _rule_based_route(message: str) -> str | None:
    text = message.lower()
    if any(hint in text for hint in OUTREACH_HINTS):
        return "outreach"
    return None


@log_span(span_type="agent", name="router_classify")
def classify(state: AgentState) -> dict:
    """LLM reads the message and picks: 'gtm' or 'outreach'."""
    rule_choice = _rule_based_route(state["question"])
    if rule_choice:
        return {"agent_type": rule_choice, "steps": [f"Router(rule) → {rule_choice.upper()}"]}

    llm = get_llm(temperature=0)
    resp = llm.invoke(
        "Classify into ONE word: gtm or outreach.\n\n"
        "gtm = product questions, features, pricing, comparisons\n"
        "outreach = write email, LinkedIn post, marketing content\n\n"
        f"Message: {state['question']}\nCategory:",
        config=get_langchain_config(
            metadata={"node": "classify", "question": state["question"]},
            tags=["agent:router"],
        ) or None,
    )
    agent = resp.content.strip().lower().strip("\"'.,")
    if agent not in ("gtm", "outreach"):
        agent = "gtm"
    return {"agent_type": agent, "steps": [f"Router → {agent.upper()}"]}


def route(state: AgentState) -> str:
    return state["agent_type"]
