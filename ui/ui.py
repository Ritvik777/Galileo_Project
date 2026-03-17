import streamlit as st
from datetime import datetime, UTC
from services.vector_db_service import add_text_documents, add_pdf_document
from services.agent_service import ask_agent, load_graph_image
from observability import start_chat_session


STYLE_BLOCK = """
<style>
    :root {
        --app-bg: #ffffff;
        --panel-bg: #f7f7f7;
        --card-bg: #ffffff;
        --border: #d9d9d9;
        --text-main: #111111;
        --text-muted: #4b4b4b;
        --brand: #111111;
    }
    .stApp {
        background: var(--app-bg) !important;
        color: var(--text-main) !important;
    }
    [data-testid="stAppViewContainer"] {
        background: var(--app-bg) !important;
    }
    [data-testid="stHeader"] {
        background: #ffffff !important;
    }
    [data-testid="stSidebar"] {
        background: var(--panel-bg) !important;
        border-right: 1px solid var(--border);
    }
    [data-testid="stSidebar"] * {
        color: var(--text-main) !important;
    }
    .stMarkdown, .stCaption, .stText, p, label, h1, h2, h3 {
        color: var(--text-main) !important;
    }
    .stTextInput input, .stTextArea textarea, .stChatInput textarea, [data-testid="stChatInput"] textarea {
        background: var(--card-bg) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    [data-testid="stBottomBlockContainer"] {
        background: #ffffff !important;
        border-top: 1px solid var(--border);
    }
    [data-testid="stChatInput"] {
        max-width: 100% !important;
        margin: 0 !important;
    }
    [data-testid="stChatInputContainer"] {
        background: #ffffff !important;
    }
    .stButton button {
        background: #ffffff !important;
        color: var(--text-main) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    .stAlert {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    [data-testid="stSidebar"] {
        background: var(--panel-bg);
    }
    .agent-badge {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 999px;
        margin-bottom: 8px;
    }
    .badge-gtm { background: #eeeeee; color: #111111; }
    .badge-outreach { background: #eeeeee; color: #111111; }
    .trace-step {
        background: var(--card-bg);
        color: var(--text-main);
        border-left: 3px solid var(--brand);
        border: 1px solid var(--border);
        padding: 8px 14px;
        margin: 4px 0;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        font-size: 13px;
    }
    .hero-subtitle {
        font-size: 14px;
        color: var(--text-muted);
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .stat-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: none;
    }
    .stat-number { font-size: 28px; font-weight: 700; color: var(--brand); }
    .stat-label {
        font-size: 12px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
"""

BADGES = {
    "gtm": ("🎯 GTM Agent", "badge-gtm"),
    "outreach": ("📝 Outreach Agent", "badge-outreach"),
}
SEND_WORDS = ["send", "market", "deliver", "mail them", "email them"]


def apply_styles() -> None:
    st.markdown(STYLE_BLOCK, unsafe_allow_html=True)


def initialize_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("awaiting_email", False)
    st.session_state.setdefault("pricing_question", "")
    st.session_state.setdefault("pending_drafts", "")
    st.session_state.setdefault("galileo_session_started", False)
    if not st.session_state.messages:
        st.session_state.galileo_session_started = False


def _reset_chat_state() -> None:
    st.session_state.messages = []
    st.session_state.awaiting_email = False
    st.session_state.pricing_question = ""
    st.session_state.pending_drafts = ""
    st.session_state.galileo_session_started = False


def _render_trace(steps: list[str]) -> None:
    if not steps:
        return
    with st.expander("🔍 Pipeline Trace"):
        for index, step in enumerate(steps, start=1):
            st.markdown(
                f'<div class="trace-step">Step {index}: {step}</div>',
                unsafe_allow_html=True,
            )


def _render_stats(doc_count: int) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">{doc_count}</div>
                <div class="stat-label">Docs in DB</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-number">3</div>
                <div class="stat-label">Agents</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_doc_upload() -> None:
    with st.expander("📄 Add Knowledge Base Docs", expanded=False):
        text_input = st.text_area(
            "Paste product docs, one per line:",
            height=140,
            placeholder="Paste your Galileo product docs here...",
        )
        if st.button("➕ Add Text", use_container_width=True):
            if text_input.strip():
                try:
                    with st.spinner("Embedding..."):
                        count = add_text_documents(text_input)
                    st.success(f"Added {count} chunks!")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not add text documents: {error}")
            else:
                st.warning("Paste some text first.")

        pdf_file = st.file_uploader("Or upload a PDF", type=["pdf"], label_visibility="collapsed")
        if pdf_file and st.button("📎 Add PDF", use_container_width=True):
            try:
                with st.spinner("Processing..."):
                    count = add_pdf_document(pdf_file)
                st.success(f"Added {count} chunks!")
                st.rerun()
            except Exception as error:
                st.error(f"Could not add PDF: {error}")


def _render_graph() -> None:
    with st.expander("🗺️ Agent Graph", expanded=False):
        try:
            st.image(load_graph_image())
        except Exception:
            st.code(
                "classify ─┬─ gtm_retrieve → pricing_gate → gtm_generate\n"
                "          └─ outreach_research → outreach_generate"
            )


def _render_how_it_works() -> None:
    with st.expander("🤖 How it works", expanded=False):
        st.markdown("""
**Router Agent** classifies your message:
- Product / pricing question → **GTM Agent**
- Content creation request → **Outreach Agent**

**GTM Agent** 🎯
- Searches Galileo docs + live web
- Gates pricing behind email verification

**Outreach Agent** 📝
- Researches product context + audience
- Creates LinkedIn posts, emails, marketing copy

**Tools:** `search_knowledge_base` (Qdrant) · `web_search` (DuckDuckGo)
""")


def render_sidebar(doc_count: int) -> None:
    with st.sidebar:
        st.markdown("## 🚀 Galileo Marketing AI")
        st.caption("Multi-Agent RAG for GTM & Outreach")
        if st.button("🆕 New Chat", use_container_width=True):
            _reset_chat_state()
            st.rerun()
        st.divider()
        _render_stats(doc_count)
        st.divider()
        _render_doc_upload()
        _render_graph()
        _render_how_it_works()
        st.divider()
        st.caption("Galileo AI · LangGraph · Qdrant · OpenAI")


def render_chat_history() -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            agent_type = message.get("agent")
            if agent_type:
                label, css_class = BADGES.get(agent_type, (agent_type, "badge-gtm"))
                st.markdown(f'<span class="agent-badge {css_class}">{label}</span>', unsafe_allow_html=True)
            st.markdown(message["content"])
            _render_trace(message.get("trace", []))


def _build_agent_question(prompt: str) -> str:
    if st.session_state.awaiting_email:
        return f"{st.session_state.pricing_question} My email is {prompt}"
    if st.session_state.pending_drafts and any(word in prompt.lower() for word in SEND_WORDS):
        return (
            f"{prompt}\n\n"
            "Here are the drafted emails to send:\n"
            f"{st.session_state.pending_drafts}"
        )
    return prompt


def _update_session_from_result(prompt: str, result: dict) -> None:
    if result.get("is_pricing") and not result.get("user_email"):
        st.session_state.awaiting_email = True
        if not st.session_state.pricing_question:
            st.session_state.pricing_question = prompt
    else:
        st.session_state.awaiting_email = False
        st.session_state.pricing_question = ""

    if result.get("agent_type") == "outreach" and result.get("answer"):
        st.session_state.pending_drafts = result["answer"]


def _push_assistant_message(result: dict) -> None:
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("answer", ""),
            "agent": result.get("agent_type", "gtm"),
            "trace": result.get("steps", []),
        }
    )


def handle_new_prompt(prompt: str) -> None:
    if not st.session_state.messages and not st.session_state.galileo_session_started:
        session_name = f"streamlit-chat-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        st.session_state.galileo_session_started = start_chat_session(session_name)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        question_for_agent = _build_agent_question(prompt)
        try:
            with st.spinner("🔄 Routing to the right agent..."):
                result = ask_agent(question_for_agent)
        except Exception as error:
            error_text = str(error)
            st.error(f"Setup issue: {error_text}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Setup issue: {error_text}",
                "agent": "gtm",
                "trace": ["App Error → configuration needed"],
            })
            return

        _update_session_from_result(prompt, result)

        label, css_class = BADGES.get(result.get("agent_type", "gtm"), ("gtm", "badge-gtm"))
        st.markdown(f'<span class="agent-badge {css_class}">{label}</span>', unsafe_allow_html=True)
        st.markdown(result.get("answer", ""))
        _render_trace(result.get("steps", []))

    _push_assistant_message(result)
