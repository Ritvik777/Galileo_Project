"""
llm.py — Language Model Router
The "brain" that reads text and generates answers.
"""
from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
)


def get_llm(temperature=0.7):
    if not ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing. Add it to your .env file and restart Streamlit."
        )
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as exc:
        raise RuntimeError(
            "langchain-anthropic is not installed. Run: pip install langchain-anthropic"
        ) from exc
    return ChatAnthropic(
        model=ANTHROPIC_MODEL,
        temperature=temperature,
        anthropic_api_key=ANTHROPIC_API_KEY,
    )
