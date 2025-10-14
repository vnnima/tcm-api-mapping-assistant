"""Centralized LLM configuration module.

This module provides a single instance of the LangChain LLM to be shared
across all subgraphs and components, avoiding multiple initializations.
"""

from langchain_openai import ChatOpenAI
from api_mapping_agent.config import Config


# Single LLM instance to be shared across the application
llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0)


def get_llm() -> ChatOpenAI:
    """Get the shared LLM instance.

    Returns:
        ChatOpenAI: The configured LLM instance.
    """
    return llm


def create_custom_llm(model: str | None = None, temperature: float = 0) -> ChatOpenAI:
    """Create a custom LLM instance with different parameters.

    Args:
        model: The model name to use (defaults to Config.OPENAI_MODEL)
        temperature: The temperature setting (defaults to 0)

    Returns:
        ChatOpenAI: A new LLM instance with custom parameters.
    """
    model = model or Config.OPENAI_MODEL
    return ChatOpenAI(model=model, temperature=temperature)
