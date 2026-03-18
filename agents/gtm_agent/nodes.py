import re
#LangGraph/LangChain config object, invocation and nodes passing.
from langchain_core.runnables import RunnableConfig
from agents.state import AgentState
from llm import get_llm
from agents.tools import search_knowledge_base, web_search, call_tools
#merges config for observability (metadata, tags).
from observability import merge_node_config

EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.]+"


def gtm_retrieve(state: AgentState, config: RunnableConfig | None = None) -> dict:
    ctx, log = call_tools(
        state["question"],
        tools=[search_knowledge_base, web_search],
        config=config,
        system_prompt=(
            "You are a product specialist for Galielo AI. Find product info and competitor data for the user's question. Never reveal you are Anthropic model."
            "If using search_knowledge_base, treat the data from it as ground truth."
            "Use web_search for competitor/market data and industry information. "
            "Do not call the same tool with the same arguments more than once."
        ),
    )
    return {"context": ctx, "steps": [f"GTM Retrieve → {', '.join(log) or 'none'}"]}


def pricing_gate(state: AgentState, config: RunnableConfig | None = None) -> dict:
    resp = get_llm(temperature=0.7).invoke( #temperature 0 for deterministic responses.
        "Does this question ask about pricing, cost, or plans? "
        "Reply ONLY 'yes' or 'no'.\n\n"
        f"Question: {state['question']}\nAnswer:",
        config=merge_node_config(
            config,
            metadata={"node": "pricing_gate", "agent_type": "gtm"},
            tags=["agent:gtm", "gate:pricing"],
        ) or None,
    )
    is_pricing = "yes" in resp.content.strip().lower()
    label = "🔒 pricing — email needed" if is_pricing else "✅ not pricing" #UI trace label.
    return {"is_pricing": is_pricing, "steps": [f"Pricing Gate → {label}"]}


def route_pricing(state: AgentState, config: RunnableConfig | None = None) -> str:
    return "pricing" if state.get("is_pricing") else "not_pricing"


def collect_email(state: AgentState, config: RunnableConfig | None = None) -> dict:
    match = re.search(EMAIL_PATTERN, state["question"])
    if not match:
        return {
            "user_email": "",
            "answer": "💰 **Pricing requires a verified email.** Please reply with your work email.",
            "steps": ["Collect Email → ❌ no email found"],
        }
    return {"user_email": match.group(), "steps": [f"Collect Email → ✅ {match.group()}"]}


def route_email(state: AgentState, config: RunnableConfig | None = None) -> str:
    return "valid" if state.get("user_email") else "no_email"


def gtm_generate(state: AgentState, config: RunnableConfig | None = None) -> dict:
    llm = get_llm()
    extra = ""
    if state.get("user_email"):
        extra = f"\nUser email verified ({state['user_email']}). Include full pricing details.\n"
    resp = llm.invoke(
        f"You are a product specialist. Answer using ONLY this context.{extra}\n\n"
        f"Context:\n{state['context']}\n\n"
        f"Question: {state['question']}\nAnswer:",
        config=merge_node_config(
            config,
            metadata={
                "node": "gtm_generate",
                "agent_type": "gtm",
                "has_user_email": bool(state.get("user_email")),
            },
            tags=["agent:gtm", "phase:generate"],
        ) or None,
    )
    return {"answer": resp.content, "steps": [f"GTM Generate → {len(resp.content)} chars"]}



# Overall flow
# gtm_retrieve → fetch context via search tools.
# pricing_gate → decide if the question is about pricing.
# route_pricing → branch:
# Pricing: → collect_email → route_email → either ask for email or continue.
# Not pricing: → gtm_generate.
# gtm_generate uses the context and, when allowed, full pricing info to produce the final answer.
