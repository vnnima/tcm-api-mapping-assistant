from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Dict, List, Any, TypedDict, Annotated, Sequence

from agent.rag import rag_search
from agent.utils import (URL_RE, parse_client_ident, parse_endpoints,
                         parse_wsm_user, parse_yes_no, has_endpoint_information,
                         get_last_user_message, get_latest_user_message, get_last_assistant_message, format_endpoints_message)
from agent.config import Config


llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0)


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    provisioning: Dict[str, Any]
    started: bool
    completed: bool
    rag_snippets: List[str]


def intro_node(state: State) -> dict:
    if state.get("completed", False):
        return {}

    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if not user_input:
        return {
            "messages": [
                AIMessage(content=(
                    "Hallo! Ich bin dein **AEB API Mapping Assistant**. "
                    "Ich helfe dir dabei, die **TCM Screening API** sauber in dein System zu integrieren.\n\n"
                    "Möchtest du mit der Integration beginnen? (Ja/Nein)"
                ))
            ]
        }

    yn = parse_yes_no(user_input)
    if yn is False:
        return {
            "completed": True,
            "messages": [
                AIMessage(content=(
                    "Alles klar! Wenn du später Hilfe bei der TCM Screening API Integration benötigst, stehe ich gerne zur Verfügung. "
                    "Viel Erfolg!"
                ))
            ]
        }
    else:
        return {
            "started": True,
            "messages": [
                AIMessage(content=(
                    "Super! Dann lass uns mit der Integration der TCM Screening API beginnen. "
                    "Zuerst benötige ich einige Informationen von dir."
                ))
            ]
        }


def clarify_node(state: State) -> dict:
    """Generic clarify node that looks at the last question and user's response to provide help."""
    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)

    last_question = get_last_assistant_message(messages)
    if not last_question:
        last_question = "eine Frage"

    sys = SystemMessage(content=(
        "Du bist ein hilfsbereiter Assistant. Der Benutzer hat eine Frage nicht richtig beantwortet. "
        "Schaue dir die ursprüngliche Frage und die Antwort des Benutzers an und erkläre freundlich, "
        "was falsch war und wie er richtig antworten soll."
    ))

    human = HumanMessage(content=f"""
Die ursprüngliche Frage/Aufforderung war:
"{last_question}"

Der Benutzer hat geantwortet: "{user_input}"

Analysiere die Antwort und erkläre freundlich:
1. Was das Problem mit der Antwort ist
2. Wie er richtig antworten soll (mit konkreten Beispielen)
3. Stelle die Frage dann nochmal

Bleibe kurz, hilfreich und freundlich.
""")

    resp = llm.invoke([sys, human])
    return {"messages": [resp]}


def ask_endpoints_node(state: State) -> dict:
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if not user_input:
        return {
            "messages": [
                AIMessage(content=(
                    "Bitte zuerst die **AEB RZ Endpoints** angeben (mindestens eine URL). "
                    "Diese sind für die API-Integration erforderlich.\n"
                    f"Hinweis: {Config.ENDPOINTS_HELP_URL}\n\n"
                    "Format:\n"
                    "Test: https://...\n"
                    "Prod:  https://..."
                ))
            ]
        }

    prov = state.get("provisioning", {})
    found = parse_endpoints(user_input)

    # If exactly one URL and no prior endpoints, accept as test by default
    single = URL_RE.findall(user_input)
    if single and len(single) == 1 and not found and not has_endpoint_information(prov):
        found = {"test_endpoint": single[0]}

    # If user provided input but parsing failed, route to clarify
    if not has_endpoint_information(prov) and not found:
        if user_input.strip():
            return {}

        # First time asking - show initial request
        return {
            "started": True,
            "messages": [
                AIMessage(content=(
                    "Bitte zuerst die **AEB RZ Endpoints** angeben (mindestens eine URL). "
                    "Diese sind für die API-Integration erforderlich.\n"
                    f"Hinweis: {Config.ENDPOINTS_HELP_URL}\n\n"
                    "Format:\n"
                    "Test: https://...\n"
                    "Prod:  https://..."
                ))
            ]
        }

    prov.update(found)

    lines = format_endpoints_message(found)

    return {
        "started": True,
        "provisioning": prov,
        "messages": [
            AIMessage(content="Danke! Endpoints erfasst:\n" + "\n".join(lines))
        ]
    }


def ask_client_node(state: State) -> dict:
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)
    prov = state.get("provisioning", {})

    confirmation_msgs = []

    if not user_input:
        return {
            "messages": confirmation_msgs + [
                AIMessage(content=(
                    "2) **Mandantenname (clientIdentCode)**:\n"
                    "- Für jeden Kunden steht ein eigener Mandant zur Verfügung.\n"
                    "Bitte teilen Sie Ihren **clientIdentCode** mit (z. B. ACME01).\n\n"
                    "Format: `clientIdentCode=ACME01` oder `Mandant: ACME01`"
                ))
            ]
        }

    # # Check if we just came from clarify_endpoints and need to show confirmation
    # # We can detect this by checking if we have endpoints but no confirmation message yet
    # if has_endpoint_information(prov):
    #     # Check if we already showed endpoints confirmation by looking at recent messages
    #     recent_messages = messages[-3:] if len(messages) >= 3 else messages
    #     has_endpoints_confirmation = any("Danke! Endpoints erfasst" in get_message_content(msg)
    #                                      for msg in recent_messages if isinstance(msg, AIMessage))

    #     if not has_endpoints_confirmation:
    #         # Show endpoints confirmation
    #         lines = []
    #         if prov.get("test_endpoint"):
    #             lines.append(f"- Test: {prov['test_endpoint']}")
    #         if prov.get("prod_endpoint"):
    #             lines.append(f"- Prod:  {prov['prod_endpoint']}")

    #         confirmation_msgs.append(
    #             AIMessage(content="Danke! Endpoints erfasst:\n" +
    #                       "\n".join(lines))
    #         )

    if user_input:
        prov = {**prov, "clientIdentCode": parse_client_ident(user_input)}

    if not prov.get("clientIdentCode"):
        return {
            "provisioning": prov,
            "messages": confirmation_msgs + [
                AIMessage(content=(
                    "2) **Mandantenname (clientIdentCode)**:\n"
                    "- Für jeden Kunden steht ein eigener Mandant zur Verfügung.\n"
                    "Bitte teilen Sie Ihren **clientIdentCode** mit (z. B. ACME01).\n\n"
                    "Format: `clientIdentCode=ACME01` oder `Mandant: ACME01`"
                ))
            ]
        }

    return {
        "provisioning": prov,
        "messages": confirmation_msgs + [
            AIMessage(
                content=f"Danke! Mandant erfasst: clientIdentCode={prov['clientIdentCode']}")
        ]
    }


def ask_wsm_node(state: State) -> dict:
    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)
    prov = state.get("provisioning", {})

    # Try to parse WSM user status from input
    is_wsm_configured = parse_wsm_user(user_input) if user_input else None
    if is_wsm_configured is not None:
        prov["wsm_user_configured"] = is_wsm_configured

    if not prov.get("wsm_user_configured"):
        return {
            "provisioning": prov,
            "messages": [
                AIMessage(content=(
                    "3) **WSM Benutzer für Authentifizierung**:\n"
                    "- Zusätzlich zum Mandanten gibt es einen **technischen WSM-Benutzer** inkl. Passwort für die API-Anbindung.\n"
                    "Ist dieser Benutzer bereits eingerichtet? (Ja/Nein)"
                ))
            ]
        }

    yn = "Ja" if prov["wsm_user_configured"] else "Nein"
    return {
        "provisioning": prov,
        "messages": [
            AIMessage(content=f"WSM-Benutzer vorhanden: {yn}.")
        ]
    }


# TODO: Hardcode this response. Dont need to waste llm tokens here...
def guide_use_cases_node(state: State) -> dict:
    prov = state.get("provisioning", {})
    snippets = rag_search(
        "AEB screening API endpoints auth clientIdentCode suppressLogging screeningLogEntry batch 100", k=3
    )

    # TODO: Define some standard prompts somewhere
    sys = SystemMessage(content=(
        "Du bist ein AEB-Trade-Compliance Onboarding-Assistent. "
        "Antworte präzise auf Deutsch, stichpunktartig, ohne Marketingfloskeln."
    ))
    human = HumanMessage(content=f"""
Erzeuge eine kurze Anleitung für die Erst-Integration der Sanktionslistenprüfung.

Kontext:
- Test-Endpoint: {prov.get('test_endpoint') or '<fehlt>'}
- Prod-Endpoint: {prov.get('prod_endpoint') or '<fehlt>'}
- Mandant (clientIdentCode): {prov.get('clientIdentCode') or '<fehlt>'}
- WSM Benutzer vorhanden: {('Ja' if prov.get('wsm_user_configured') else 'Nein' if prov.get('wsm_user_configured') is not None else '<unbekannt>')}

Bitte decke ab:
1) Formate (JSON/REST).
2) Prüfrelevante Objekte (Stammdaten einzeln/Bulk ≤100; Transaktionen).
3) Felder: Pflicht / prüfrelevant / optional (Name, Adresse, eindeutige Referenz, Adresstyp).
4) Trigger: Anlage/Änderung Stammdaten & Transaktionen; periodische Batchprüfung (z. B. 1×/Monat).
5) Drei Anbindungsvarianten:
   a) Einseitige Übergabe via screenAddresses (Response → Treffer/Nichttreffer; E-Mail an TCM-Empfänger; manuelles (Ent-)Sperren).
   b) Übergabe + regelmäßige Nachprüfung mit suppressLogging=true (z. B. alle 60 Min.) zur automatischen Entsperrung nach Good-Guy.
   c) Optionaler Deep-Link via screeningLogEntry (temporärer Link; Button/Menu im Partnersystem).
6) Response-Szenarien:
   - matchFound=true & wasGoodGuy=false → Treffer → (optional) Sperre/Benachrichtigung.
   - matchFound=false & wasGoodGuy=false → kein Treffer → keine Aktion.
   - matchFound=false & wasGoodGuy=true → kein Treffer (bereits Good-Guy) → keine Aktion.

Berücksichtige (falls vorhanden) Doku-Auszüge:
{snippets if snippets else '[keine RAG-Snippets gefunden]'}
""")
    resp = llm.invoke([sys, human])

    return {
        "completed": True,
        "messages": [resp]
    }


def qa_mode_node(state: State) -> dict:
    """Handle free-flowing Q&A after the initial flow is completed."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_question = get_latest_user_message(messages)

    # If no question provided, show prompt and wait for input
    if not user_question or not user_question.strip():
        prompt_msg = AIMessage(
            content="Wie kann ich dir bei der TCM Screening API Integration helfen? Stelle gerne deine Frage!")
        return { "messages": [prompt_msg] }

    snippets = rag_search(
        f"Question about Screening API: {user_question}", k=5)

    # Build context from provisioning data
    context_info = []
    if prov.get("test_endpoint"):
        context_info.append(f"Test-Endpoint: {prov['test_endpoint']}")
    if prov.get("prod_endpoint"):
        context_info.append(f"Prod-Endpoint: {prov['prod_endpoint']}")
    if prov.get("clientIdentCode"):
        context_info.append(
            f"Mandant (clientIdentCode): {prov['clientIdentCode']}")
    if "wsm_user_configured" in prov:
        wsm_status = "Ja" if prov["wsm_user_configured"] else "Nein"
        context_info.append(f"WSM-Benutzer: {wsm_status}")

    context_str = "\n".join(
        context_info) if context_info else "Keine Konfigurationsdaten verfügbar."

    sys = SystemMessage(content=(
        "Du bist ein AEB-Trade-Compliance API-Experte. "
        "Beantworte Fragen zur TCM Screening API präzise und hilfreich auf Deutsch. "
        "Nutze IMMER die verfügbaren Dokumentationsauszüge und Konfigurationsdaten. "
        "Wenn Dokumentation verfügbar ist, basiere deine Antwort darauf und nicht auf allgemeinem Wissen."
    ))

    snippets_text = "\n\n".join([f"Dokument {i+1}:\n{snippet}" for i, snippet in enumerate(
        snippets)]) if snippets else '[Keine passenden Dokumentationsauszüge gefunden]'

    human = HumanMessage(content=f"""
Benutzerfrage: {user_question}

Verfügbare Konfiguration:
{context_str}

Verfügbare Dokumentationsauszüge:
{snippets_text}

Beantworte die Frage basierend auf den verfügbaren Informationen. 
WICHTIG: Nutze die Dokumentationsauszüge als primäre Quelle und verwende die korrekte API-Struktur aus der Dokumentation.
""")

    resp = llm.invoke([sys, human])

    return {
        "messages": [resp]
    }


def route_from_intro(state: State) -> str:
    """Route from intro based on user response and current state."""

    # TODO: Can remove this when I implement the looping in qa_mode with interrupt
    if state.get("completed", False):
        return "qa_mode"

    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)

    if not user_input:
        return END

    if state.get("started", False):
        prov = state.get("provisioning", {})

        if not has_endpoint_information(prov):
            return "ask_endpoints"

        if not prov.get("clientIdentCode"):
            return "ask_client"

        if "wsm_user_configured" not in prov:
            return "ask_wsm"

        # All good -> guide
        return "guide_use_cases"

    # If user hasn't started yet, check their yes/no response
    yn = parse_yes_no(user_input or "")

    if yn is None:
        return "clarify"
    elif yn is False:
        # TODO: Add a node where we explain where to get this info from.
        return END
    else:
        return "ask_endpoints"


def route_from_endpoints(state: State) -> str:
    """Route from endpoints based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and not has_endpoint_information(prov):
        return "clarify"

    if not has_endpoint_information(prov):
        return END

    return "ask_client"


def route_from_clarify(state: State) -> str:
    """Route from clarify node - after clarification, route back to appropriate node."""
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)
    prov = state.get("provisioning", {})

    if not user_input:
        return END
    if not has_endpoint_information(prov):
        return "ask_endpoints"
    if not prov.get("clientIdentCode"):
        return "ask_client"
    if "wsm_user_configured" not in prov:
        return "ask_wsm"
    else:
        return "intro"


def route_from_client(state: State) -> str:
    """Route from client based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and not prov.get("clientIdentCode"):
        return "clarify"

    if not prov.get("clientIdentCode"):
        return END

    return "ask_wsm"


def route_from_wsm(state: State) -> str:
    """Route from WSM based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and not prov.get("wsm_user_configured"):
        return "clarify"

    if not prov.get("wsm_user_configured"):
        return END

    return "guide_use_cases"


def route_from_guide(state: State) -> str:
    """Route from guide - mark as completed and go to Q&A mode."""
    return "qa_mode"


def route_from_qa(state: State) -> str:
    """Q&A mode - check if we should continue or end."""
    return END


def build_graph():
    """Build the graph with conditional edges and persistence."""
    # checkpointer = InMemorySaver() # TODO: Don't need this with Langgraph API

    g = StateGraph(State)

    g.add_node("intro", intro_node)
    g.add_node("clarify", clarify_node)
    g.add_node("ask_endpoints", ask_endpoints_node)
    g.add_node("ask_client", ask_client_node)
    g.add_node("ask_wsm", ask_wsm_node)
    g.add_node("guide_use_cases", guide_use_cases_node)
    g.add_node("qa_mode", qa_mode_node)

    g.add_edge(START, "intro")

    g.add_conditional_edges("intro", route_from_intro, {
        "qa_mode": "qa_mode",
        "ask_endpoints": "ask_endpoints",
        "ask_client": "ask_client",
        "ask_wsm": "ask_wsm",
        "clarify": "clarify",
        "__end__": END
    })
    g.add_conditional_edges("clarify", route_from_clarify, {
        "clarify": "clarify",
        "intro": "intro",
        "ask_endpoints": "ask_endpoints",
        "ask_client": "ask_client",
        "__end__": END
    })
    g.add_conditional_edges("ask_endpoints", route_from_endpoints, {
        "ask_client": "ask_client",
        "clarify": "clarify",
        "__end__": END
    })
    g.add_conditional_edges("ask_client", route_from_client, {
        "clarify": "clarify",
        "ask_wsm": "ask_wsm",
        "__end__": END
    })
    g.add_conditional_edges("ask_wsm", route_from_wsm, {
        "clarify": "clarify",
        "guide_use_cases": "guide_use_cases",
        "__end__": END
    })
    g.add_conditional_edges("guide_use_cases", route_from_guide, {
        "qa_mode": "qa_mode"
    })
    g.add_conditional_edges("qa_mode", route_from_qa, {
        "qa_mode": "qa_mode",
        "__end__": END
    })

    # return g.compile(checkpointer=checkpointer) # TODO: Don't need this with Langgraph API
    return g.compile()


api_mapping_graph = build_graph()
