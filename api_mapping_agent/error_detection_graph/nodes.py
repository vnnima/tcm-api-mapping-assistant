from __future__ import annotations
from api_mapping_agent.utils import get_latest_user_message
from api_mapping_agent.rag import rag_search, ensure_index_built
from api_mapping_agent.llm import get_llm
from .state import ErrorDetectionState
from typing import Dict, Any
from langgraph.graph import END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from api_mapping_agent.config import Config


llm = get_llm()


def chat_node(state: ErrorDetectionState) -> Dict[str, Any]:
    """Handle conversational API error help."""
    messages = state.get("messages", [])

    # If no messages yet, show the welcome message
    if not messages:
        return {
            "messages": [
                AIMessage(content=(
                    """
                Hello! I help with problems related to the AEB TCM Screening API.
                
                You can simply describe what happened - for example:
                - \"I'm getting a 400 error\"
                - \"What does this error code mean?\"
                """
                ))
            ]
        }

    # Get the user's question
    user_input = get_latest_user_message(messages)

    if not user_input or not user_input.strip():
        return {}

    ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                       Config.KNOWLEDGE_BASE_VECTOR_STORE)

    # TODO: Get error codes documentation via RAG search when available
    try:
        relevant_docs = rag_search(f"API error help: {user_input}", k=3)
    except Exception:
        relevant_docs = []

    # Create a conversational system prompt
    sys = SystemMessage(content=(
        "You are a helpful API support assistant for the AEB TCM Screening API. "
        "Answer questions about API errors briefly and precisely in English. "
        "Be friendly and conversational. If the user shows code or errors, analyze them. "
        "Use the entire conversation history to understand the context. "
        "If no specific docs are available, use your knowledge about common API problems.\n\n"

        "COMMON API ERRORS:\n"
        "• 400 Bad Request: Syntax/validation error\n"
        "• 401 Unauthorized: Authentication missing\n"
        "• 403 Forbidden: No permission\n"
        "• 404 Not Found: Wrong endpoint\n"
        "• 500 Server Error: Backend problem\n\n"

        "COMMON TYPOS:\n"
        "• 'addresse' instead of 'addresses'\n"
        "• 'clientId' instead of 'clientIdentCode'\n"
        "• 'suppressLog' instead of 'suppressLogging'\n\n"

        "Reply briefly and helpfully. Ask for more details if you need them.\n"

        "Available documentation excerpts:\n" +
        ("\n".join(relevant_docs)
         if relevant_docs else "No relevant documents found.")
    ))

    human = HumanMessage(content=user_input)
    try:
        response = llm.invoke([sys, *messages, human])
    except Exception as e:
        response = AIMessage(
            content=f"Sorry, an error occurred: {str(e)}")

    return {
        "messages": [response]
    }


def route_chat(state: ErrorDetectionState) -> str:
    """Simple routing - always stay in chat mode."""
    return END
