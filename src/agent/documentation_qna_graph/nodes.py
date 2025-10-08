from __future__ import annotations
from agent.documentation_qna_graph.tools import get_tcm_api_documentation_url
from agent.utils import get_latest_user_message
from agent.rag import rag_search, ensure_index_built
from agent.llm import get_llm
from .state import DocumentationQnaState, QnaNodeNames
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import END
from agent.config import Config


llm = get_llm().bind_tools([get_tcm_api_documentation_url])


def welcome_node(state: DocumentationQnaState) -> Dict[str, Any]:
    """Welcome the user and explain the documentation Q&A service."""
    messages = state.get("messages", [])

    # TODO: This does not work like that. I have to find a way to initialize the state with a message.
    if not messages:
        return {
            "messages": [
                AIMessage(content=(
                    "# 📚 AEB TCM Screening API Dokumentation Q&A\n\n"
                    "Willkommen! Ich bin Ihr Dokumentations-Assistent für die AEB TCM Screening API.\n\n"
                    "**Was ich für Sie tun kann:**\n"
                    "• Fragen zur API-Struktur und Parametern beantworten\n"
                    "• Beispiele für API-Aufrufe und Responses erklären\n"
                    "• Integration und Implementierung unterstützen\n"
                    "• Troubleshooting bei API-Problemen helfen\n\n"
                    "**Stellen Sie einfach Ihre Frage** - ich durchsuche die gesamte Dokumentation "
                    "und gebe Ihnen eine präzise Antwort basierend auf den offiziellen Unterlagen.\n\n"
                    "**Beispiel-Fragen:**\n"
                    "- Wie ist die Request-Struktur für screenAddresses aufgebaut?\n"
                    "- Was bedeutet der Parameter suppressLogging?\n"
                    "- Welche Response-Codes gibt es und was bedeuten sie?\n"
                    "- Wie implementiere ich eine Batch-Prüfung?\n\n"
                    "*Ihre Frage:*"
                ))
            ]
        }

    user_input = get_latest_user_message(messages).strip()

    if user_input and user_input.strip():
        return {"messages": [user_input]}

    return {}


def answer_question_node(state: DocumentationQnaState) -> Dict[str, Any]:
    """Answer user questions using RAG search on the knowledge base."""
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages).strip()

    if not user_input:
        # No question to answer, shouldn't happen
        return {
            "messages": [
                AIMessage(
                    content="Bitte stellen Sie eine Frage zur AEB TCM Screening API Dokumentation.")
            ]
        }

    ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                       Config.KNOWLEDGE_BASE_DIR)

    # Perform RAG search on the knowledge base
    try:
        snippets = rag_search(f"API documentation question: {user_input}")
        search_results = snippets if snippets else []
    except Exception as e:
        search_results = []
        print(f"RAG search failed: {e}")

    # Prepare system message for the LLM
    sys = SystemMessage(content=(
        "Du bist ein Experte für die AEB TCM Screening API Dokumentation. "
        "Beantworte Benutzerfragen präzise und hilfreich auf Deutsch basierend auf den verfügbaren Dokumentationsauszügen. "
        "Nutze IMMER die bereitgestellten Dokumentationsauszüge als primäre Quelle. "
        "Wenn keine passenden Informationen in den Auszügen gefunden werden, sage das ehrlich und "
        "verwende das get_tcm_api_documentation_url Tool um den Link zur offiziellen Dokumentation bereitzustellen. "
        "Gib konkrete Beispiele und Code-Snippets wenn möglich. "
        "Strukturiere deine Antwort klar mit Überschriften und Listen."
    ))

    # Prepare documentation excerpts
    if search_results:
        snippets_text = "\n\n".join([
            f"**Dokumentationsauszug {i+1}:**\n{snippet}"
            for i, snippet in enumerate(search_results)
        ])
    else:
        snippets_text = "*Keine passenden Dokumentationsauszüge gefunden.*"

    # Create human message with question and context
    human = HumanMessage(content=f"""
**Benutzerfrage:** {user_input}

**Verfügbare Dokumentationsauszüge:**
{snippets_text}

Beantworte die Frage basierend auf den verfügbaren Dokumentationsauszügen. 
Wenn die Dokumentation nicht ausreicht, nutze das get_tcm_api_documentation_url Tool und füge den Link in deine Antwort ein.
Nutze klare Strukturierung mit Markdown-Formatierung.
""")

    try:
        conversation_messages = [sys] + list(messages) + [human]
        ai_response = llm.invoke(conversation_messages)

        response_messages = [ai_response]

        # TODO: Maybe there is a better way to include the info from a Tool call. See ToolNode?
        tool_calls = getattr(ai_response, 'tool_calls', None)
        if tool_calls:
            for tool_call in tool_calls:
                if tool_call["name"] == "get_tcm_api_documentation_url":
                    tool_result = get_tcm_api_documentation_url.invoke({})

                    tool_message = ToolMessage(
                        content=str(tool_result),
                        tool_call_id=tool_call["id"]
                    )
                    response_messages.append(tool_message)

            if len(response_messages) > 1:  # Tool was executed
                final_conversation = conversation_messages + response_messages
                final_response = llm.invoke(final_conversation)
                response_messages.append(final_response)

    except Exception as e:
        response_messages = [AIMessage(content=(
            f"Entschuldigung, bei der Verarbeitung Ihrer Frage ist ein Fehler aufgetreten: {str(e)}\n\n"
            "Bitte versuchen Sie es erneut oder formulieren Sie Ihre Frage anders."
        ))]

    return {
        "messages": response_messages,
        "search_results": search_results,
    }


def route_from_welcome(state: DocumentationQnaState) -> str:
    """Route from welcome node based on user input."""
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages).strip()

    if not user_input:
        return END
    return QnaNodeNames.ANSWER_QUESTION


def route_from_answer(state: DocumentationQnaState) -> str:
    return END
