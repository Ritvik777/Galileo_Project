"""
Outreach Agent
===============
Finds leads via Apollo, creates personalized drafts, sends ONLY when user says "send".

Nodes: outreach_research → outreach_generate → send_gate ─┬─ send → outreach_send → END
                                                           └─ review → END (show drafts)
"""

import re
from agents.state import AgentState
from llm import get_llm
from agents.tools import search_knowledge_base, web_search, apollo_search, send_email, call_tools


LEAD_KEYWORDS = {"research leads", "find leads", "find prospects", "find companies", "find people", "who can i", "prospect", "leads for"}
SEND_KEYWORDS = {"send it", "send them", "send those", "send the email", "send email", "mail them", "email them", "deliver", "blast"}


def _wants_leads(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in LEAD_KEYWORDS)


def outreach_research(state: AgentState) -> dict:
    q = state["question"]

    if _wants_leads(q):
        # User wants leads → MUST call Apollo + knowledge base
        ctx, log = call_tools(
            q,
            tools=[apollo_search, search_knowledge_base],
            system_prompt=(
                "The user wants to find leads/prospects. You MUST:\n"
                "1. Call apollo_search with relevant job titles (e.g. 'VP Engineering, CTO, Head of AI') "
                "and optionally an industry (e.g. 'computer software', 'artificial intelligence')\n"
                "2. Call search_knowledge_base to get our product info for personalization\n\n"
                "ALWAYS call apollo_search. Do NOT skip it."
            ),
        )
    else:
        # User wants content → knowledge base + web
        ctx, log = call_tools(
            q,
            tools=[search_knowledge_base, web_search],
            system_prompt=(
                "Find product info and target audience data for creating content. "
                "Use search_knowledge_base for product talking points. "
                "Use web_search for company/industry info to personalize."
            ),
        )

    return {"context": ctx, "steps": [f"Outreach Research → {', '.join(log) or 'none'}"]}


def outreach_generate(state: AgentState) -> dict:
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
        recipient_emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', state["question"])
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

    resp = llm.invoke(prompt)
    return {"answer": resp.content, "steps": [f"Outreach Generate → {len(resp.content)} chars"]}


def send_gate(state: AgentState) -> dict:
    q = state["question"].lower()
    should_send = any(kw in q for kw in SEND_KEYWORDS)
    label = "📤 user wants to SEND" if should_send else "👀 review only (no send)"
    return {"steps": [f"Send Gate → {label}"]}


def route_send(state: AgentState) -> str:
    q = state["question"].lower()
    if any(kw in q for kw in SEND_KEYWORDS):
        return "send"
    return "review"


def outreach_send(state: AgentState) -> dict:
    content = state["answer"]
    emails_found = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', content)

    if not emails_found:
        emails_found = re.findall(r'[\w.+-]+@[\w-]+\.[\w.]+', state["question"])

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

    for to in emails_found:
        html = f"""
        <div style="font-family: -apple-system, Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a1a; line-height: 1.6;">
            {body_html}
            <hr style="border: none; border-top: 1px solid #e5e5e5; margin: 24px 0;">
            <p style="font-size: 12px; color: #999;">Sent via Galileo Marketing AI</p>
        </div>
        """

        result = send_email.invoke({"to_email": to, "subject": subject, "html_body": html})
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
