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
                    "# AEB TCM Screening API Documentation Q&A\n\n"
                    "Welcome! I am your documentation assistant for the AEB TCM Screening API.\n\n"
                    "**What I can do for you:**\n"
                    "• Answer questions about API structure and parameters\n"
                    "• Explain examples of API calls and responses\n"
                    "• Support integration and implementation\n"
                    "• Help with API troubleshooting\n\n"
                    "**Simply ask your question** - I will search through the entire documentation "
                    "and provide you with a precise answer based on the official documents.\n\n"
                    "**Example questions:**\n"
                    "- How is the request structure for screenAddresses built?\n"
                    "- What does the suppressLogging parameter mean?\n"
                    "- What response codes are there and what do they mean?\n"
                    "- How do I implement batch screening?\n\n"
                    "*Your question:*"
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
                    content="Please ask a question about the AEB TCM Screening API documentation.")
            ]
        }

    ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                       Config.KNOWLEDGE_BASE_VECTOR_STORE)

    # Perform RAG search on the knowledge base
    try:
        snippets = rag_search(f"API documentation question: {user_input}")
        search_results = snippets if snippets else []
    except Exception as e:
        search_results = []
        print(f"RAG search failed: {e}")

    # Prepare system message for the LLM
    sys = SystemMessage(content=(
        "You are an expert for the AEB TCM Screening API documentation. "
        "Answer user questions precisely and helpfully in English based on the available documentation excerpts. "
        "ALWAYS use the provided documentation excerpts as your primary source. "
        "If no suitable information is found in the excerpts, say so honestly and "
        "use the get_tcm_api_documentation_url tool to provide the link to the official documentation. "
        "Provide concrete examples and code snippets when possible. "
        "Structure your answer clearly with headings and lists."
    ))

    # Prepare documentation excerpts
    if search_results:
        snippets_text = "\n\n".join([
            f"**Documentation excerpt {i+1}:**\n{snippet}"
            for i, snippet in enumerate(search_results)
        ])
    else:
        snippets_text = "*No matching documentation excerpts found.*"

        # Create human message with question and context
    human = HumanMessage(content=f"""
**User question:** {user_input}

**Available documentation excerpts:**
{snippets_text}

Answer the question based on the available documentation excerpts. 
If the documentation is not sufficient, use the get_tcm_api_documentation_url tool and include the link in your answer.
Use clear structuring with Markdown formatting.
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
