#RunnableConfig from LangChain – config object passed through the graph (e.g. callbacks, run metadata).
from langchain_core.runnables import RunnableConfig
#states
from agents.state import AgentState
from llm import get_llm
#merge_node_config to add node metadata to the config.
from observability import merge_node_config

# GalileoCallback (via graph.invoke config) logs this node; no @log_span to avoid duplicate spans.
def classify(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """LLM reads the message and picks: 'gtm' or 'outreach'."""
    llm = get_llm(temperature=0)
    resp = llm.invoke(
        "Classify into ONE word: gtm or outreach.\n\n"
        "gtm = product questions, features, pricing, comparisons\n"
        "outreach = write email, LinkedIn post, marketing content\n\n"
        f"Message: {state['question']}\nCategory:",
        config=merge_node_config(
            config,
            metadata={"node": "classify", "question": state["question"]},
            tags=["agent:supervisor_routing"],
        ) or None,
    )
    agent = resp.content.strip().lower().strip("\"'.,")
    if agent not in ("gtm", "outreach"):
        agent = "gtm"
    return {"agent_type": agent, "steps": [f"Supervisor Routing Agent → {agent.upper()}"]}

# LangGraph uses this to decide which subgraph runs next (GTM vs Outreach).
def route(state: AgentState, config: RunnableConfig | None = None) -> str:
    return state["agent_type"]


#Overall flow:
# User message → classify picks gtm or outreach →
# route returns that choice → the graph routes to the right agent.