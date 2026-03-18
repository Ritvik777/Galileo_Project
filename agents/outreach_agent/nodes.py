import re
from typing import Any

from langchain_core.runnables import RunnableConfig

from agents.state import AgentState
from llm import get_llm
from agents.tools import search_knowledge_base, web_search, apollo_search, send_email, call_tools
from observability import merge_node_config


LEAD_KEYWORDS = {"research leads", "find leads", "find prospects", "find companies", "find people", "who can i", "prospect", "leads for"}
SEND_KEYWORDS = {"send it", "send them", "send those", "send the email", "send email", "mail them", "email them", "deliver", "blast"}
EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.]+"


def _wants_leads(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in LEAD_KEYWORDS)


def _should_send(question: str) -> bool:
    q = question.lower()
    if any(kw in q for kw in SEND_KEYWORDS):
        return True

    # If user includes an address and asks to send, treat it as explicit send intent.
    has_email = re.search(EMAIL_PATTERN, question) is not None
    has_send_verb = bool(re.search(r"\bsend\b", q))
    return has_email and has_send_verb


def _extract_emails(text: str) -> list[str]:
    return re.findall(EMAIL_PATTERN, text)


def _llm_send_decision(question: str, draft: str, config: RunnableConfig | None = None) -> str | None:
    try:
        llm = get_llm(temperature=0)
        resp = llm.invoke(
            "Decide whether the user is explicitly asking to SEND an email now.\n"
            "Return exactly one word: send or review.\n\n"
            "Rules:\n"
            "- send: explicit execution intent (e.g. send it, send now, send to <email>, go ahead and send)\n"
            "- review: drafting, editing, brainstorming, or unclear intent\n"
            "- If uncertain, return review.\n\n"
            f"User message: {question}\n"
            f"Current draft preview: {draft[:400]}\n"
            "Decision:",
            config=merge_node_config(
                config,
                metadata={"node": "send_gate_decision", "agent_type": "outreach"},
                tags=["agent:outreach", "gate:send"],
            ) or None,
        )
        decision = str(resp.content).strip().lower()
        if "send" in decision:
            return "send"
        if "review" in decision:
            return "review"
        return None
    except Exception:
        return None


def outreach_research(state: AgentState, config: RunnableConfig | None = None) -> dict:
    q = state["question"]

    if _wants_leads(q):
        ctx, log = call_tools(
            q,
            tools=[apollo_search, search_knowledge_base],
            config=config,
            system_prompt=(
                "The user wants to find leads/prospects. You MUST:\n"
                "1. Call apollo_search with relevant job titles (e.g. 'VP Engineering, CTO, Head of AI') "
                "and optionally an industry (e.g. 'computer software', 'artificial intelligence')\n"
                "2. Call search_knowledge_base to get our product info for personalization\n\n"
                "ALWAYS call apollo_search. Do NOT skip it."
            ),
        )
    else:
        ctx, log = call_tools(
            q,
            tools=[search_knowledge_base, web_search],
            config=config,
            system_prompt=(
                "Find product info and target audience data for creating content. "
                "Use search_knowledge_base for product talking points. "
                "Use web_search for company/industry info to personalize."
            ),
        )

    return {"context": ctx, "steps": [f"Outreach Research → {', '.join(log) or 'none'}"]}


def outreach_generate(state: AgentState, config: RunnableConfig | None = None) -> dict:
    llm = get_llm(temperature=0.7)

    ctx = state.get("context", "")
    has_leads = "leads" in ctx.lower() and "Email:" in ctx

    if has_leads:
        prompt = (
            "You found REAL leads from Apollo with their emails. "
            "For EACH lead that has an email, write a personalized email.\n\n"
            "Rules:\n"
            "- Write ONLY emails, NOT LinkedIn posts\n"
            "- Use their actual name, title, company, and industry\n"
            "- Connect their likely pain points to our product benefits\n"
            "- Keep each email 2-3 short paragraphs\n"
            "- Use HTML formatting (<p>, <b>)\n"
            "- Sign off as 'The Galileo Team'\n"
            "- NO placeholder text like [Your Name] — use real data only\n\n"
            "Format EACH email as:\n"
            "**To: FirstName LastName** (their@email.com)\n"
            "**Subject:** <personalized subject>\n"
            "<email body>\n"
            "---\n\n"
            f"Leads + product info:\n{ctx}\n\n"
            f"Request: {state['question']}"
        )
    else:
        recipient_emails = _extract_emails(state["question"])
        recipient_hint = ""
        if recipient_emails:
            recipient_hint = (
                f"\nThe user specified recipient(s): {', '.join(recipient_emails)}. "
                "Address the email to them and include their email in the output "
                "using the format: **To:** name (email@example.com)\n"
            )

        prompt = (
            "You are a content specialist. Create EXACTLY what the user asks for.\n"
            "- If they ask for a LinkedIn post: write ONLY a LinkedIn post\n"
            "- If they ask for an email: write ONLY an email\n"
            "- Do NOT create multiple content types\n"
            "- No placeholder text like [Your Name]\n"
            "- Sign off as 'The Galileo Team'\n"
            f"{recipient_hint}\n"
            f"Context:\n{ctx}\n\n"
            f"Request: {state['question']}\nContent:"
        )

    resp = llm.invoke(
        prompt,
        config=merge_node_config(
            config,
            metadata={
                "node": "outreach_generate",
                "agent_type": "outreach",
                "send_requested": bool(state.get("send_requested")),
            },
            tags=["agent:outreach", "phase:generate"],
        ) or None,
    )
    return {"answer": resp.content, "steps": [f"Outreach Generate → {len(resp.content)} chars"]}


def send_gate(state: AgentState, config: RunnableConfig | None = None) -> dict:
    llm_decision = _llm_send_decision(state["question"], state.get("answer", ""), config)
    if llm_decision is None:
        should_send = _should_send(state["question"])
        source = "rule-fallback"
    else:
        should_send = llm_decision == "send"
        source = "llm"
    label = "📤 user wants to SEND" if should_send else "👀 review only (no send)"
    return {"send_requested": should_send, "steps": [f"Send Gate({source}) → {label}"]}


def route_send(state: AgentState, config: RunnableConfig | None = None) -> str:
    return "send" if state.get("send_requested") else "review"


def outreach_send(state: AgentState, config: RunnableConfig | None = None) -> dict:
    content = state["answer"]
    emails_found = _extract_emails(content)

    if not emails_found:
        emails_found = _extract_emails(state["question"])

    if not emails_found:
        return {
            "answer": state["answer"] + "\n\n---\n⚠️ *No email addresses found in drafts to send.*",
            "steps": ["Outreach Send → ❌ no emails found in generated content"],
        }

    subject_match = re.search(r'\*{0,2}Subject:?\*{0,2}\s*(.+)', content)
    subject = subject_match.group(1).strip() if subject_match else "A Personalized Introduction to Galileo"

    body = re.sub(r'\*{0,2}To:?\*{0,2}.*\n?', '', content)
    body = re.sub(r'\*{0,2}Subject:?\*{0,2}.*\n?', '', body)
    body = body.strip().strip('-').strip()

    body = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', body)
    body_html = ''.join(f'<p style="margin: 0 0 12px 0;">{p.strip()}</p>'
                        for p in body.split('\n\n') if p.strip())
    if not body_html:
        body_html = body.replace('\n', '<br>')

    sent = []
    failed = []

    invoke_config = merge_node_config(
        config,
        metadata={"node": "outreach_send"},
        tags=["agent:outreach", "tool:send_email"],
    )
    for to in emails_found:
        html = f"""
        <div style="font-family: -apple-system, Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a1a; line-height: 1.6;">
            {body_html}
            <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;">
            <p style="font-size: 12px; color: #999;">Sent via Galileo Marketing AI</p>
        </div>
        """

        result = send_email.invoke({"to_email": to, "subject": subject, "html_body": html}, config=invoke_config)
        if "SENT" in result:
            sent.append(to)
        else:
            failed.append(f"{to} ({result})")

    summary = ""
    if sent:
        summary += f"✅ **Sent to:** {', '.join(sent)}\n\n"
    if failed:
        summary += f"❌ **Failed:** {', '.join(failed)}\n\n"

    return {
        "answer": f"{summary}---\n\n{state['answer']}",
        "steps": [f"Outreach Send → ✅ {len(sent)} sent, ❌ {len(failed)} failed"],
    }
