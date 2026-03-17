"""
GTM (Go-To-Market) Agent
=========================
Answers product questions. If about pricing → asks for email first.

Nodes: gtm_retrieve → pricing_gate → collect_email → gtm_generate
"""

import re
from agents.state import AgentState
from llm import get_llm
from agents.tools import search_knowledge_base, web_search, call_tools


def gtm_retrieve(state: AgentState) -> dict:
    ctx, log = call_tools(
        state["question"],
        tools=[search_knowledge_base, web_search],
        system_prompt=(
            "Find product info and competitor data for the user's question. "
            "Use search_knowledge_base for internal docs. "
            "Use web_search for competitor/market data."
        ),
    )
    return {"context": ctx, "steps": [f"GTM Retrieve → {', '.join(log) or 'none'}"]}


def pricing_gate(state: AgentState) -> dict:
    llm = get_llm(temperature=0)
    resp = llm.invoke(
        "Does this question ask about pricing, cost, or plans? "
        "Reply ONLY 'yes' or 'no'.\n\n"
        f"Question: {state['question']}\nAnswer:"
    )
    is_pricing = "yes" in resp.content.strip().lower()
    label = "🔒 pricing — email needed" if is_pricing else "✅ not pricing"
    return {"is_pricing": is_pricing, "steps": [f"Pricing Gate → {label}"]}


def route_pricing(state: AgentState) -> str:
    return "pricing" if state.get("is_pricing") else "not_pricing"


def collect_email(state: AgentState) -> dict:
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', state["question"])
    if not match:
        return {
            "user_email": "",
            "answer": "💰 **Pricing requires a verified email.** Please reply with your work email.",
            "steps": ["Collect Email → ❌ no email found"],
        }
    return {"user_email": match.group(), "steps": [f"Collect Email → ✅ {match.group()}"]}


def route_email(state: AgentState) -> str:
    return "valid" if state.get("user_email") else "no_email"


def gtm_generate(state: AgentState) -> dict:
    llm = get_llm()
    extra = ""
    if state.get("user_email"):
        extra = f"\nUser email verified ({state['user_email']}). Include full pricing details.\n"
    resp = llm.invoke(
        f"You are a product specialist. Answer using ONLY this context.{extra}\n\n"
        f"Context:\n{state['context']}\n\n"
        f"Question: {state['question']}\nAnswer:"
    )
    return {"answer": resp.content, "steps": [f"GTM Generate → {len(resp.content)} chars"]}
