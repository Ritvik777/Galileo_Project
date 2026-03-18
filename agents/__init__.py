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
from observability import ensure_galileo_initialized, get_logger_instance, is_galileo_enabled


def ask(question: str, source: str = "ui_interface") -> dict:
    ensure_galileo_initialized()
    base_state = {
        "question": question, "agent_type": "", "context": "", "answer": "",
        "is_pricing": False, "user_email": "", "send_requested": False, "steps": [],
    }
    if not is_galileo_enabled():
        return graph.invoke(base_state)

    logger = get_logger_instance()
    if logger is None:
        return graph.invoke(base_state)

    in_existing_trace = logger.current_parent() is not None
    trace_name = "Automated Evals" if source == "automated_evals" else "UI Interface"
    if not in_existing_trace:
        logger.start_trace(input={"question": question}, name=trace_name)
    try:
        result = graph.invoke(base_state)
        if not in_existing_trace:
            logger.conclude(result.get("answer", ""))
            logger.flush()
        return result
    except Exception:
        if not in_existing_trace:
            try:
                logger.flush()
            except Exception:
                pass
        raise


def get_graph_image() -> bytes:
    return graph.get_graph().draw_mermaid_png()
