"""
agents/ — The multi-agent system
==================================
  state.py              → shared pipeline state
  tools.py              → shared tools (RAG + web search)
  graph.py              → wires everything into a LangGraph

  router_agent/         → 🚦 Supervisor Routing Agent (picks which agent handles it)
  gtm_agent/            → 🎯 GTM Agent (product questions + pricing gate)
  outreach_agent/       → 📝 Outreach Agent (content creation)
"""

from agents.graph import graph
from observability import ensure_galileo_initialized, get_langchain_config, get_logger_instance, is_galileo_enabled


def ask(question: str) -> dict:
    # Make sure Galileo is ready before we run the graph.
    ensure_galileo_initialized()
    base_state = {
        "question": question, "agent_type": "", "context": "", "answer": "",
        "is_pricing": False, "user_email": "", "send_requested": False, "steps": [],
    }
    # If Galileo is not configured, run normally without tracing.
    if not is_galileo_enabled():
        config = get_langchain_config(metadata={"question": question})
        return graph.invoke(base_state, config=config)

    logger = get_logger_instance()
    if logger is None:
        config = get_langchain_config(metadata={"question": question})
        return graph.invoke(base_state, config=config)

    # If a parent trace already exists, we join it instead of creating nested top traces.
    in_existing_trace = logger.current_parent() is not None
    if not in_existing_trace:
        # Start one top-level trace for this user question.
        logger.start_trace(input={"question": question}, name="ask_agent")
    # Build config AFTER start_trace so GalileoCallback gets start_new_trace=False
    # and nests graph spans under ask_agent instead of creating a sibling "Agent" trace.
    config = get_langchain_config(metadata={"question": question})
    try:
        result = graph.invoke(base_state, config=config)
        if not in_existing_trace:
            # Finish + flush so this trace appears in Galileo UI quickly.
            logger.conclude(result.get("answer", ""))
            logger.flush()
        return result
    except Exception:
        if not in_existing_trace:
            try:
                # Flush partial trace on errors for debugging.
                logger.flush()
            except Exception:
                pass
        raise


def get_graph_image() -> bytes:
    return graph.get_graph().draw_mermaid_png()
