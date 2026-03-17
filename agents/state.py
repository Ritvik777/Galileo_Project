from typing import TypedDict, Annotated


def _merge(a: list, b: list) -> list:
    return a + b


class AgentState(TypedDict):
    question: str
    agent_type: str
    context: str
    answer: str
    is_pricing: bool
    user_email: str
    send_requested: bool
    steps: Annotated[list[str], _merge]
