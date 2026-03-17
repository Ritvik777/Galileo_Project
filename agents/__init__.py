"""
agents/ — The multi-agent system
==================================
  state.py              → shared pipeline state
  tools.py              → shared tools (RAG + web search)
  graph.py              → wires everything into a LangGraph

  router_agent/         → 🚦 Router Agent (picks which agent handles it)
  gtm_agent/            → 🎯 GTM Agent (product questions + pricing gate)
  outreach_agent/       → 📝 Outreach Agent (content creation)
"""

from agents.graph import graph


def ask(question: str) -> dict:
    return graph.invoke({
        "question": question, "agent_type": "", "context": "", "answer": "",
        "is_pricing": False, "user_email": "", "send_requested": False, "steps": [],
    })


def get_graph_image() -> bytes:
    return graph.get_graph().draw_mermaid_png()
