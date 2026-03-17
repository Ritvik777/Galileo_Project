import streamlit as st
from vector_db import add_documents, get_document_count, extract_text_from_pdf
from agents import ask, get_graph_image

st.set_page_config(page_title="Galileo AI — Multi-Agent", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: var(--secondary-background-color);
    }
    .agent-badge {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 8px;
    }
    .badge-gtm { background: #059669; color: white; }
    .badge-outreach { background: #2563eb; color: white; }
    .trace-step {
        background: var(--secondary-background-color);
        color: var(--text-color);
        border-left: 3px solid #6366f1;
        border: 1px solid rgba(128, 128, 128, 0.35);
        padding: 8px 14px;
        margin: 4px 0;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        font-size: 13px;
    }
    .hero-subtitle {
        font-size: 14px;
        color: var(--text-color);
        opacity: 0.78;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .stat-card {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .stat-number { font-size: 28px; font-weight: 700; color: #a78bfa; }
    .stat-label {
        font-size: 12px;
        color: var(--text-color);
        opacity: 0.72;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

BADGES = {
    "gtm": ("🎯 GTM Agent", "badge-gtm"),
    "outreach": ("📝 Outreach Agent", "badge-outreach"),
}
SEND_WORDS = ["send", "market", "deliver", "mail them", "email them"]


def initialize_session_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("awaiting_email", False)
    st.session_state.setdefault("pricing_question", "")
    st.session_state.setdefault("pending_drafts", "")


def render_trace(steps: list[str]) -> None:
    if not steps:
        return
    with st.expander("🔍 Pipeline Trace"):
        for index, step in enumerate(steps, start=1):
            st.markdown(
                f'<div class="trace-step">Step {index}: {step}</div>',
                unsafe_allow_html=True,
            )


def render_sidebar(doc_count: int) -> None:
    with st.sidebar:
        st.markdown("## 🚀 Galileo Marketing AI")
        st.caption("Multi-Agent RAG for GTM & Outreach")
        st.divider()

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

        st.divider()

        with st.expander("📄 Add Knowledge Base Docs", expanded=False):
            text_input = st.text_area(
                "Paste product docs, one per line:",
                height=140,
                placeholder="Paste your Galileo product docs here...",
            )
            if st.button("➕ Add Text", use_container_width=True):
                lines = [line.strip() for line in text_input.strip().split("\n") if line.strip()]
                if lines:
                    with st.spinner("Embedding..."):
                        count = add_documents(lines)
                    st.success(f"Added {count} chunks!")
                    st.rerun()
                else:
                    st.warning("Paste some text first.")

            pdf_file = st.file_uploader("Or upload a PDF", type=["pdf"], label_visibility="collapsed")
            if pdf_file and st.button("📎 Add PDF", use_container_width=True):
                with st.spinner("Processing..."):
                    count = add_documents([extract_text_from_pdf(pdf_file)])
                st.success(f"Added {count} chunks!")
                st.rerun()

        with st.expander("🗺️ Agent Graph", expanded=False):
            try:
                st.image(get_graph_image())
            except Exception:
                st.code(
                    "classify ─┬─ gtm_retrieve → pricing_gate → gtm_generate\n"
                    "          └─ outreach_research → outreach_generate"
                )

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
            render_trace(message.get("trace", []))


def handle_new_prompt(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        question_for_agent = prompt
        if st.session_state.awaiting_email:
            question_for_agent = f"{st.session_state.pricing_question} My email is {prompt}"
        elif st.session_state.pending_drafts and any(word in prompt.lower() for word in SEND_WORDS):
            question_for_agent = (
                f"{prompt}\n\n"
                "Here are the drafted emails to send:\n"
                f"{st.session_state.pending_drafts}"
            )

        try:
            with st.spinner("🔄 Routing to the right agent..."):
                result = ask(question_for_agent)
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

        if result.get("is_pricing") and not result.get("user_email"):
            st.session_state.awaiting_email = True
            if not st.session_state.pricing_question:
                st.session_state.pricing_question = prompt
        else:
            st.session_state.awaiting_email = False
            st.session_state.pricing_question = ""

        if result.get("agent_type") == "outreach" and result.get("answer"):
            st.session_state.pending_drafts = result["answer"]

        label, css_class = BADGES.get(result.get("agent_type", "gtm"), ("gtm", "badge-gtm"))
        st.markdown(f'<span class="agent-badge {css_class}">{label}</span>', unsafe_allow_html=True)
        st.markdown(result.get("answer", ""))
        render_trace(result.get("steps", []))

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("answer", ""),
            "agent": result.get("agent_type", "gtm"),
            "trace": result.get("steps", []),
        }
    )

initialize_session_state()
doc_count = get_document_count()

render_sidebar(doc_count)

# ── Main Chat ────────────────────────────────────────

st.markdown("# 🚀 Galileo Marketing Assistant")
st.markdown('<p class="hero-subtitle">Ask about Galileo products, compare with competitors, or generate marketing content — the right agent handles it.</p>', unsafe_allow_html=True)

if not st.session_state.messages and doc_count == 0:
    st.info("👈 Add Galileo product docs to the knowledge base first — expand **Add Knowledge Base Docs** in the sidebar.")

render_chat_history()

new_prompt = st.chat_input("Ask about Galileo, or request marketing content...")
if new_prompt:
    handle_new_prompt(new_prompt)
