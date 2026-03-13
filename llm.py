"""
llm.py — OpenAI Language Model
================================
The "brain" that reads text and generates answers.

Uses: OpenAI GPT-4o-mini (fast + cheap + smart enough for RAG)
"""

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY, LLM_MODEL


def get_llm(temperature=0):
    """
    Create and return the OpenAI chat model.

    temperature=0 means the model gives consistent, focused answers.
    Higher temperature (e.g. 0.7) would make it more creative/random.
    """
    return ChatOpenAI(
        model=LLM_MODEL,
        temperature=temperature,
        openai_api_key=OPENAI_API_KEY,
    )
