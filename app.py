import streamlit as st
from vector_db import add_documents, get_document_count, extract_text_from_pdf
from agents import ask, get_graph_image

st.set_page_config(page_title="Galileo AI — Multi-Agent", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f1117; }
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
        background: #1a1c25;
        border-left: 3px solid #6366f1;
        padding: 8px 14px;
        margin: 4px 0;
        border-radius: 0 6px 6px 0;
        font-family: monospace;
        font-size: 13px;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #8b8d98;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .stat-card {
        background: #1a1c25;
        border: 1px solid #23252f;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .stat-number { font-size: 28px; font-weight: 700; color: #a78bfa; }
    .stat-label { font-size: 12px; color: #8b8d98; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "awaiting_email" not in st.session_state:
    st.session_state.awaiting_email = False
    st.session_state.pricing_question = ""
if "pending_drafts" not in st.session_state:
    st.session_state.pending_drafts = ""

BADGES = {
    "gtm": ("🎯 GTM Agent", "badge-gtm"),
    "outreach": ("📝 Outreach Agent", "badge-outreach"),
}

# ── Sidebar ──────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🚀 Galileo Marketing AI")
    st.caption("Multi-Agent RAG for GTM & Outreach")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{get_document_count()}</div>
            <div class="stat-label">Docs in DB</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-number">3</div>
            <div class="stat-label">Agents</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    with st.expander("📄 Add Knowledge Base Docs", expanded=False):
        text = st.text_area("Paste product docs, one per line:", height=140, placeholder="Paste your Galileo product docs here...")
        if st.button("➕ Add Text", use_container_width=True):
            lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
            if lines:
                with st.spinner("Embedding..."):
                    count = add_documents(lines)
                st.success(f"Added {count} chunks!")
                st.rerun()
            else:
                st.warning("Paste some text first.")

        pdf = st.file_uploader("Or upload a PDF", type=["pdf"], label_visibility="collapsed")
        if pdf and st.button("📎 Add PDF", use_container_width=True):
            with st.spinner("Processing..."):
                count = add_documents([extract_text_from_pdf(pdf)])
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

# ── Main Chat ────────────────────────────────────────

st.markdown("# 🚀 Galileo Marketing Assistant")
st.markdown('<p class="hero-subtitle">Ask about Galileo products, compare with competitors, or generate marketing content — the right agent handles it.</p>', unsafe_allow_html=True)

if not st.session_state.messages and get_document_count() == 0:
    st.info("👈 Add Galileo product docs to the knowledge base first — expand **Add Knowledge Base Docs** in the sidebar.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "agent" in msg:
            label, css_class = BADGES.get(msg["agent"], (msg["agent"], "badge-gtm"))
            st.markdown(f'<span class="agent-badge {css_class}">{label}</span>', unsafe_allow_html=True)
        st.markdown(msg["content"])
        if "trace" in msg and msg["trace"]:
            with st.expander("🔍 Pipeline Trace"):
                for i, s in enumerate(msg["trace"], 1):
                    st.markdown(f'<div class="trace-step">Step {i}: {s}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Ask about Galileo, or request marketing content..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if st.session_state.awaiting_email:
            question = f"{st.session_state.pricing_question} My email is {prompt}"
        elif st.session_state.pending_drafts and any(kw in prompt.lower() for kw in ["send", "market", "deliver", "mail them", "email them"]):
            question = f"{prompt}\n\nHere are the drafted emails to send:\n{st.session_state.pending_drafts}"
        else:
            question = prompt

        with st.spinner("🔄 Routing to the right agent..."):
            result = ask(question)

        if result.get("is_pricing") and not result.get("user_email"):
            st.session_state.awaiting_email = True
            st.session_state.pricing_question = st.session_state.pricing_question or prompt
        else:
            st.session_state.awaiting_email = False
            st.session_state.pricing_question = ""

        if result.get("agent_type") == "outreach" and result.get("answer"):
            st.session_state.pending_drafts = result["answer"]

        label, css_class = BADGES.get(result["agent_type"], (result["agent_type"], "badge-gtm"))
        st.markdown(f'<span class="agent-badge {css_class}">{label}</span>', unsafe_allow_html=True)
        st.markdown(result["answer"])

        if result["steps"]:
            with st.expander("🔍 Pipeline Trace"):
                for i, s in enumerate(result["steps"], 1):
                    st.markdown(f'<div class="trace-step">Step {i}: {s}</div>', unsafe_allow_html=True)

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "agent": result["agent_type"],
        "trace": result["steps"],
    })
