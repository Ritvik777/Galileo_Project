from typing import TypedDict, Annotated


def _merge(a: list, b: list) -> list:
    return a + b


class AgentState(TypedDict):
    question: str
    agent_type: str                        # "gtm" or "outreach"
    context: str                           # info gathered by tools
    answer: str                            # final response
    is_pricing: bool                       # is this a pricing question?
    user_email: str                        # verified email (or empty)
    send_requested: bool                   # did user ask to send outreach?
    steps: Annotated[list[str], _merge]    # trace log
