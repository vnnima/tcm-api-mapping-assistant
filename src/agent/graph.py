from __future__ import annotations
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import Dict, List, Any, TypedDict

from agent.rag import rag_search
from agent.utils import (URL_RE, parse_client_ident, parse_endpoints,
                         parse_wsm_user, parse_yes_no, no_endpoint_information)
from agent.config import Config


llm = ChatOpenAI(model=Config.OPENAI_MODEL, temperature=0)


class State(TypedDict):
    # TODO: Maybe add this Annotated[XY, add] thing. Look at docs
    messages: List[Dict[str, Any]]
    provisioning: Dict[str, Any]
    started: bool
    completed: bool
    rag_snippets: List[str]
    user_input: str


def intro_node(state: State) -> State:
    existing_messages = state.get("messages", [])

    state.setdefault("messages", [])
    state.setdefault("provisioning", {})

    if state.get("completed", False):
        return state
    if state.get("started", False):
        return state
    # If there are already messages in the conversation, don't show intro again
    if len(existing_messages) > 0:
        return state

    state["messages"].append({
        "role": "assistant",
        "meta": "intro",
        "content": (
            "Hallo! Ich bin dein **AEB API Mapping Assistant**. "
            "Ich helfe dir dabei, die **TCM Screening API** sauber in dein System zu integrieren.\n\n"
            "Möchtest du mit der Integration beginnen? (Ja/Nein)"
        )
    })
    return state


def clarify_node(state: State) -> State:
    """Generic clarify node that looks at the last question and user's response to provide help."""
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])

    # Find the last assistant message (the question)
    last_question = "eine Frage"  # fallback
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            last_question = msg.get("content", "")
            break

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
    state["messages"].append({"role": "assistant", "content": resp.content})

    # Clear user_input so we wait for new input
    state["user_input"] = ""

    return state


def ask_endpoints_node(state: State) -> State:
    state["started"] = True

    prov = state.setdefault("provisioning", {})
    user_input = state.get("user_input") or ""

    # TODO: Look at this. This seems fishy. Do we need this?
    # IMPORTANT: If we're coming from intro with a yes/no answer, clear it
    # because that input was for the intro question, not the endpoints question
    if not state.get("provisioning", {}).get("test_endpoint") and not state.get("provisioning", {}).get("prod_endpoint"):
        # Check if the input looks like a yes/no answer rather than endpoint attempt
        yn_result = parse_yes_no(user_input)
        if yn_result is not None:
            user_input = ""
            state["user_input"] = ""

    found = parse_endpoints(user_input)

    # TODO: The URL extration logic ca be improved
    # If exactly one URL and no prior endpoints, accept as test by default
    single = URL_RE.findall(user_input)
    if single and len(single) == 1 and not found and no_endpoint_information(prov):
        found = {"test_endpoint": single[0]}

    prov.update(found)

    # If user provided input but parsing failed, route to clarify
    if no_endpoint_information(prov):
        if user_input.strip():
            state["user_input"] = user_input
            return state

        new_message = {
            "role": "assistant",
            "content": (
                "Bitte zuerst die **AEB RZ Endpoints** angeben (mindestens eine URL). "
                "Diese sind für die API-Integration erforderlich.\n"
                f"Hinweis: {Config.ENDPOINTS_HELP_URL}\n\n"
                "Format:\n"
                "Test: https://...\n"
                "Prod:  https://..."
            )
        }
        state["messages"].append(new_message)
        state["user_input"] = ""
        return state

    # If we get here, we have at least one endpoint
    lines = []
    if prov.get("test_endpoint"):
        lines.append(f"- Test: {prov['test_endpoint']}")
    if prov.get("prod_endpoint"):
        lines.append(f"- Prod:  {prov['prod_endpoint']}")
    if len(lines) == 1:
        # TODO: There is acutally no way to add the second endpoint later. Maybe remove this entirely
        lines.append(
            "Hinweis: Den zweiten Endpoint (Test/Prod) können Sie später ergänzen.")

    confirmation_message = {
        "role": "assistant",
        "content": "Danke! Endpoints erfasst:\n" + "\n".join(lines)
    }
    state["messages"].append(confirmation_message)

    state["user_input"] = ""
    return state


def ask_client_node(state: State) -> State:
    prov = state.setdefault("provisioning", {})
    user_input = state.get("user_input") or ""

    # Check if we just came from clarify_endpoints and need to show confirmation
    # We can detect this by checking if we have endpoints but no confirmation message yet
    if (prov.get("test_endpoint") or prov.get("prod_endpoint")):
        # Check if we already showed endpoints confirmation by looking at recent messages
        recent_messages = state.get(
            "messages", [])[-3:]  # Check last 3 messages
        has_endpoints_confirmation = any("Danke! Endpoints erfasst" in msg.get("content", "")
                                         for msg in recent_messages)

        if not has_endpoints_confirmation:
            # Show endpoints confirmation
            lines = []
            if prov.get("test_endpoint"):
                lines.append(f"- Test: {prov['test_endpoint']}")
            if prov.get("prod_endpoint"):
                lines.append(f"- Prod:  {prov['prod_endpoint']}")

            confirmation_message = {
                "role": "assistant",
                "content": "Danke! Endpoints erfasst:\n" + "\n".join(lines)
            }
            state["messages"].append(confirmation_message)

    if not prov.get("clientIdentCode"):
        guess = parse_client_ident(user_input)
        if guess:
            prov["clientIdentCode"] = guess

    if not prov.get("clientIdentCode"):
        state["messages"].append({
            "role": "assistant",
            "content": (
                "2) **Mandantenname (clientIdentCode)**:\n"
                "- Für jeden Kunden steht ein eigener Mandant zur Verfügung.\n"
                "Bitte teilen Sie Ihren **clientIdentCode** mit (z. B. ACME01).\n\n"
                "Format: `clientIdentCode=ACME01` oder `Mandant: ACME01`"
            )
        })
        # Clear user_input for consistent state management
        state["user_input"] = ""
        return state

    state["messages"].append({
        "role": "assistant",
        "content": f"Danke! Mandant erfasst: clientIdentCode={prov['clientIdentCode']}"
    })

    state["user_input"] = ""
    return state


def ask_wsm_node(state: State) -> State:
    prov = state.setdefault("provisioning", {})
    user_input = state.get("user_input") or ""

    if "wsm_user_configured" not in prov:
        guess = parse_wsm_user(user_input)
        if guess is not None:
            prov["wsm_user_configured"] = guess

    if "wsm_user_configured" not in prov:
        state["messages"].append({
            "role": "assistant",
            "content": (
                "3) **WSM Benutzer für Authentifizierung**:\n"
                "- Zusätzlich zum Mandanten gibt es einen **technischen WSM-Benutzer** inkl. Passwort für die API-Anbindung.\n"
                "Ist dieser Benutzer bereits eingerichtet? (Ja/Nein)"
            )
        })
        return state

    yn = "Ja" if prov["wsm_user_configured"] else "Nein"
    state["messages"].append(
        {"role": "assistant", "content": f"WSM-Benutzer vorhanden: {yn}."})

    state["user_input"] = ""
    return state


def guide_use_cases_node(state: State) -> State:
    prov = state.get("provisioning", {})
    snippets = rag_search(
        "AEB screening API endpoints auth clientIdentCode suppressLogging screeningLogEntry batch 100", k=3
    )

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
    state["messages"].append({"role": "assistant", "content": resp.content})

    state["completed"] = True

    return state


def qa_mode_node(state: State) -> State:
    """Handle free-flowing Q&A after the initial flow is completed."""
    prov = state.get("provisioning", {})
    user_question = state.get("user_input", "")

    # If no question provided, show prompt and wait for input
    if not user_question.strip():
        state["messages"].append({
            "role": "assistant",
            "content": "Wie kann ich dir bei der TCM Screening API Integration helfen? Stelle gerne deine Frage!"
        })
        # Clear user_input for consistent state management
        state["user_input"] = ""
        return state

    # Search for relevant information with more specific terms
    snippets = rag_search(
        f"screening request example JSON REST API {user_question}", k=5)

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
    state["messages"].append({"role": "assistant", "content": resp.content})

    state["user_input"] = ""

    return state


def route_from_intro(state: State) -> str:
    """Route from intro based on user response and current state."""

    if state.get("completed", False):
        return "qa_mode"

    # Wait for user input instead of looping
    user_input = state.get("user_input", "")
    if not user_input:
        return END

    if state.get("started", False):
        prov = state.get("provisioning", {})

        if no_endpoint_information(prov):
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
    user_input = state.get("user_input", "")

    if user_input.strip() and no_endpoint_information(prov):
        return "clarify"

    # If no endpoints and no input, wait for input
    if no_endpoint_information(prov):
        return END

    return "ask_client"


def route_from_clarify(state: State) -> str:
    """Route from clarify node - determine what type of input was expected and handle accordingly."""
    user_input = state.get("user_input", "")
    messages = state.get("messages", [])
    prov = state.get("provisioning", {})

    if not user_input:
        return END

    # TODO: This entire logic can maybe be solved by a llm call instead of programtically
    # If we haven't started yet, we're expecting yes/no to begin
    if not state.get("started", False):
        yn = parse_yes_no(user_input or "")

        if yn is None:
            return "clarify"
        elif yn is False:
            return END
        else:
            return "ask_endpoints"

    # If we've started but don't have endpoints, we're expecting endpoints
    elif no_endpoint_information(prov):

        found = parse_endpoints(user_input)

        single = URL_RE.findall(user_input)
        if single and len(single) == 1 and not found:
            found = {"test_endpoint": single[0]}

        if found and (found.get("test_endpoint") or found.get("prod_endpoint")):
            prov = state.setdefault("provisioning", {})
            prov.update(found)

            state["started"] = True
            return "ask_client"
        else:
            # Still invalid endpoints - stay in clarify mode
            return "clarify"

    # TODO: Add handling for other clarification types (client, WSM) when we add clarify nodes for those
    else:
        return "clarify"


def route_from_client(state: State) -> str:
    """Route from client based on current provisioning state."""
    prov = state.get("provisioning", {})
    # TODO: add clarify node
    if not prov.get("clientIdentCode"):
        return END

    return "ask_wsm"


def route_from_wsm(state: State) -> str:
    """Route from WSM based on current provisioning state."""
    prov = state.get("provisioning", {})
    # TODO: add clarify node
    if "wsm_user_configured" not in prov:
        return END

    return "guide_use_cases"


def route_from_guide(state: State) -> str:
    """Route from guide - mark as completed and go to Q&A mode."""
    return "qa_mode"


def route_from_qa(state: State) -> str:
    """Q&A mode - check if we should continue or end."""
    user_input = state.get("user_input", "")

    if not user_input or user_input.lower() in ['quit', 'exit', 'bye', 'done']:
        return END

    return "qa_mode"


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
        "clarify": "clarify",
        "__end__": END
    })
    g.add_conditional_edges("clarify", route_from_clarify, {
        "clarify": "clarify",
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
        "ask_wsm": "ask_wsm",
        "__end__": END
    })
    g.add_conditional_edges("ask_wsm", route_from_wsm, {
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
