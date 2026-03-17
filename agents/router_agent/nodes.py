from agents.state import AgentState
from llm import get_llm


def classify(state: AgentState) -> dict:
    """LLM reads the message and picks: 'gtm' or 'outreach'."""
    llm = get_llm(temperature=0)
    resp = llm.invoke(
        "Classify into ONE word: gtm or outreach.\n\n"
        "gtm = product questions, features, pricing, comparisons\n"
        "outreach = write email, LinkedIn post, marketing content\n\n"
        f"Message: {state['question']}\nCategory:"
    )
    agent = resp.content.strip().lower().strip("\"'.,")
    if agent not in ("gtm", "outreach"):
        agent = "gtm"
    return {"agent_type": agent, "steps": [f"Router → {agent.upper()}"]}


def route(state: AgentState) -> str:
    return state["agent_type"]
