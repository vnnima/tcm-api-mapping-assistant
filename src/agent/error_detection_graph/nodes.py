from __future__ import annotations
from agent.utils import get_latest_user_message
from agent.rag import rag_search, ensure_index_built
from agent.llm import get_llm
from .state import ErrorDetectionState
from typing import Dict, Any
from langgraph.graph import END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from agent.config import Config


llm = get_llm()


def chat_node(state: ErrorDetectionState) -> Dict[str, Any]:
    """Handle conversational API error help."""
    messages = state.get("messages", [])

    # If no messages yet, show the welcome message
    if not messages:
        return {
            "messages": [
                AIMessage(content=(
                    "# 🔍 API Error Hilfe\n\n"
                    "Hallo! Ich helfe bei Problemen mit der AEB TCM Screening API.\n\n"
                    "Sie können mir einfach beschreiben was passiert ist - zum Beispiel:\n"
                    "• \"Ich bekomme einen 400 Fehler\"\n"
                    "• \"Mein Request funktioniert nicht\"\n"
                    "• \"Was bedeutet dieser Error Code?\"\n\n"
                    "Was ist das Problem?"
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
        "Du bist ein hilfsbereiter API-Support für die AEB TCM Screening API. "
        "Beantworte Fragen zu API-Fehlern kurz und präzise auf Deutsch. "
        "Sei freundlich und gesprächig. Wenn der Benutzer Code oder Errors zeigt, analysiere sie. "
        "Nutze den gesamten Gesprächsverlauf um den Kontext zu verstehen. "
        "Wenn keine spezifischen Docs verfügbar sind, nutze dein Wissen über häufige API-Probleme.\n\n"

        "HÄUFIGE API-FEHLER:\n"
        "• 400 Bad Request: Syntax-/Validierungsfehler\n"
        "• 401 Unauthorized: Authentifizierung fehlt\n"
        "• 403 Forbidden: Keine Berechtigung\n"
        "• 404 Not Found: Endpoint falsch\n"
        "• 500 Server Error: Backend-Problem\n\n"

        "HÄUFIGE TYPOS:\n"
        "• 'addresse' statt 'addresses'\n"
        "• 'clientId' statt 'clientIdentCode'\n"
        "• 'suppressLog' statt 'suppressLogging'\n\n"

        "Antworte kurz und hilfsbereit. Frage nach, wenn du mehr Details brauchst.\n"

        "Verfügbare Dokumentationsauszüge:\n" +
        ("\n".join(relevant_docs)
         if relevant_docs else "Keine relevanten Dokumente gefunden.")
    ))

    human = HumanMessage(content=user_input)
    try:
        response = llm.invoke([sys, *messages, human])
    except Exception as e:
        response = AIMessage(
            content=f"Entschuldigung, da ist ein Fehler aufgetreten: {str(e)}")

    return {
        "messages": [response]
    }


def route_chat(state: ErrorDetectionState) -> str:
    """Simple routing - always stay in chat mode."""
    return END
