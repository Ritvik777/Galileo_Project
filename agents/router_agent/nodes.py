import logging

from langchain_core.runnables import RunnableConfig

from agents.state import AgentState
from llm import get_llm
from observability import merge_node_config

logger = logging.getLogger(__name__)


def classify(state: AgentState, config: RunnableConfig | None = None) -> dict:
    """LLM reads the message and picks: 'gtm' or 'outreach'. Falls back to gtm on failure."""
    try:
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
            logger.warning(
                "Router: LLM returned unparseable category %r, defaulting to gtm.",
                resp.content,
            )
            agent = "gtm"
    except Exception as exc:
        logger.exception(
            "Router: classify LLM call failed, defaulting to gtm. Error: %s",
            exc,
        )
        agent = "gtm"

    return {"agent_type": agent, "steps": [f"Supervisor Routing Agent → {agent.upper()}"]}

# LangGraph uses this to decide which subgraph runs next (GTM vs Outreach).
def route(state: AgentState, config: RunnableConfig | None = None) -> str:
    return state["agent_type"]


#Overall flow:
# User message → classify picks gtm or outreach →
# route returns that choice → the graph routes to the right agent.