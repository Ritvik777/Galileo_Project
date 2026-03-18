from agents.state import AgentState
from llm import get_llm
from observability import get_langchain_config, log_span

#@log_span wraps this call for observability tracking.
@log_span(span_type="agent", name="Supervisor Routing Agent")
def classify(state: AgentState) -> dict:
    """LLM reads the message and picks: 'gtm' or 'outreach'."""
    llm = get_llm(temperature=0)
    resp = llm.invoke(
        "Classify into ONE word: gtm or outreach.\n\n"
        "gtm = product questions, features, pricing, comparisons\n"
        "outreach = write email, LinkedIn post, marketing content\n\n"
        f"Message: {state['question']}\nCategory:",
        config=get_langchain_config(
            metadata={"node": "classify", "question": state["question"]},
            tags=["agent:supervisor_routing"],
        ) or None,
    )
    agent = resp.content.strip().lower().strip("\"'.,")
    if agent not in ("gtm", "outreach"):
        agent = "gtm"
    return {"agent_type": agent, "steps": [f"Supervisor Routing Agent → {agent.upper()}"]}

#LangGraph uses this to decide which subgraph runs next (GTM vs Outreach).
def route(state: AgentState) -> str:
    return state["agent_type"]


#Overall flow:
# User message → classify picks gtm or outreach →
# route returns that choice → the graph routes to the right agent.