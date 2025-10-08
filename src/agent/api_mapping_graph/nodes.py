from __future__ import annotations
from .state import ApiMappingState
from langgraph.types import interrupt
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from enum import Enum
from agent.utils import (URL_RE, parse_client_ident, parse_endpoints,
                         parse_wsm_user, parse_yes_no, has_endpoint_information,
                         get_last_user_message, get_latest_user_message, get_last_assistant_message, format_endpoints_message)
from agent.llm import get_llm
from agent.config import Config
from agent.rag import rag_search, build_index, ensure_index_built, debug_vectorstore_contents, debug_knowledge_base_files


class NodeNames(str, Enum):
    INTRO = "intro"
    CLARIFY = "clarify"
    ASK_ENDPOINTS = "ask_endpoints"
    ASK_CLIENT = "ask_client"
    ASK_WSM = "ask_wsm"
    GENERAL_SCREENING_INFO = "general_screening_info"
    EXPLAIN_SCREENING_VARIANTS = "explain_screening_variants"
    EXPLAIN_RESPONSES = "explain_responses"
    API_MAPPING_INTRO = "api_mapping_intro"
    DECISION_INTERRUPT = "decision_interrupt"
    GET_API_DATA_INTERRUPT = "get_api_data_interrupt"
    PROCESS_AND_MAP_API = "process_and_map_api"
    QA_MODE = "qa_mode"


llm = get_llm()


def intro_node(state: ApiMappingState) -> dict:
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
    if yn is None:
        return {}
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


def route_from_intro(state: ApiMappingState) -> str:
    """Route from intro based on user response and current state."""

    # TODO: Can remove this when I implement the looping in qa_mode with interrupt
    if state.get("completed", False):
        return NodeNames.QA_MODE

    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)

    if not user_input:
        return END

    if state.get("started", False):
        prov = state.get("provisioning", {})

        if not has_endpoint_information(prov):
            return NodeNames.ASK_ENDPOINTS

        if not prov.get("clientIdentCode"):
            return NodeNames.ASK_CLIENT

        if "wsm_user_configured" not in prov:
            return NodeNames.ASK_WSM

        # All good -> guide
        return NodeNames.GENERAL_SCREENING_INFO

    # If user hasn't started yet, check their yes/no response
    yn = parse_yes_no(user_input or "")

    if yn is None:
        return NodeNames.CLARIFY
    elif yn is False:
        # TODO: Add a node where we explain where to get this info from.
        return END
    else:
        return NodeNames.ASK_ENDPOINTS


def clarify_node(state: ApiMappingState) -> dict:
    """Generic clarify node that looks at the last question and user's response to provide help."""
    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)

    last_question = get_last_assistant_message(
        messages) or "Möchtest du mit der API Mapping Integration beginnen? (Ja/Nein)"
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


def route_from_clarify(state: ApiMappingState) -> str:
    """Route from clarify node - after clarification, route back to appropriate node."""
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)
    prov = state.get("provisioning", {})

    if not user_input:
        return END
    if not has_endpoint_information(prov):
        return NodeNames.ASK_ENDPOINTS
    if not prov.get("clientIdentCode"):
        return NodeNames.ASK_CLIENT
    if "wsm_user_configured" not in prov:
        return NodeNames.ASK_WSM
    else:
        return NodeNames.INTRO


def ask_endpoints_node(state: ApiMappingState) -> dict:
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
    found_endpoints = parse_endpoints(user_input)

    # If exactly one URL and no prior endpoints, accept as test by default
    single = URL_RE.findall(user_input)
    if single and len(single) == 1 and not found_endpoints and not has_endpoint_information(prov):
        found_endpoints["test_endpoint"] = single[0]

    # If user provided input but parsing failed, route to clarify
    if not has_endpoint_information(prov) and not found_endpoints:
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

    prov = {**prov, **found_endpoints}

    lines = format_endpoints_message(found_endpoints)

    return {
        "started": True,
        "provisioning": prov,
        "messages": [
            AIMessage(content="Danke! Endpoints erfasst:\n" + "\n".join(lines))
        ]
    }


def route_from_endpoints(state: ApiMappingState) -> str:
    """Route from endpoints based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and not has_endpoint_information(prov):
        return NodeNames.CLARIFY

    if not has_endpoint_information(prov):
        return END

    return NodeNames.ASK_CLIENT


def ask_client_node(state: ApiMappingState) -> dict:
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
                content=f"Danke! Mandant erfasst: clientIdentCode={prov.get('clientIdentCode', 'N/A')}")
        ]
    }


def route_from_client(state: ApiMappingState) -> str:
    """Route from client based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and not prov.get("clientIdentCode"):
        return NodeNames.CLARIFY

    if not prov.get("clientIdentCode"):
        return END

    return NodeNames.ASK_WSM


def ask_wsm_node(state: ApiMappingState) -> dict:
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

    yn = "Ja" if prov.get("wsm_user_configured") else "Nein"
    return {
        "provisioning": prov,
        "messages": [
            AIMessage(content=f"WSM-Benutzer vorhanden: {yn}.")
        ]
    }


def route_from_wsm(state: ApiMappingState) -> str:
    """Route from WSM based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and not prov.get("wsm_user_configured"):
        return NodeNames.CLARIFY

    if not prov.get("wsm_user_configured"):
        return END

    return NodeNames.GENERAL_SCREENING_INFO


def general_screening_info_node(state: ApiMappingState) -> dict:
    prov = state.get("provisioning", {})
    response_content = f"""
### Anleitung zur Erst-Integration der Sanktionslistenprüfung

#### 1. Formate
- **JSON/REST**: Nutzung der REST-API für die Kommunikation.

#### 2. Prüfrelevante Objekte
- **Stammdaten**: Einzelprüfung oder Bulk (max. 100 Einträge).
- **Transaktionen**: Prüfung bei Anlage oder Änderung.

#### 3. Felder
- **Pflichtfelder**:
  - Name
  - Adresse
  - Eindeutige Referenz
- **Prüfrelevante Felder**:
  - Adresstyp
- **Optionale Felder**: Keine spezifischen optionalen Felder definiert.

#### 4. Trigger
- **Anlage/Änderung**: Automatische Prüfung bei neuen oder geänderten Stammdaten und Transaktionen.
- **Periodische Batchprüfung**: Empfohlen 1× pro Monat.

#### 5. Anbindungsvarianten
- **a) Einseitige Übergabe via screenAddresses**:
  - Response: Treffer/Nichttreffer
  - E-Mail an TCM-Empfänger
  - Manuelles (Ent-)Sperren erforderlich

- **b) Übergabe + regelmäßige Nachprüfung**:
  - Parameter: `suppressLogging=true`
  - Frequenz: Alle 60 Minuten
  - Automatische Entsperrung nach Good-Guy

- **c) Optionaler Deep-Link via screeningLogEntry**:
  - Temporärer Link
  - Integration als Button/Menu im Partnersystem

#### 6. Response-Szenarien
- **matchFound=true & wasGoodGuy=false**:
  - Ergebnis: Treffer
  - Aktion: (Optional) Sperre/Benachrichtigung

- **matchFound=false & wasGoodGuy=false**:
  - Ergebnis: Kein Treffer
  - Aktion: Keine

- **matchFound=false & wasGoodGuy=true**:
  - Ergebnis: Kein Treffer (bereits Good-Guy)
  - Aktion: Keine

#### Endpoints
- **Test-Endpoint**: {prov.get('test_endpoint') or '<fehlt>'}
- **Prod-Endpoint**: {prov.get('prod_endpoint') or '<fehlt>'}
- **Mandant (clientIdentCode)**: {prov.get('clientIdentCode') or '<fehlt>'}
- **WSM Benutzer vorhanden**: {('Ja' if prov.get('wsm_user_configured') else 'Nein' if prov.get('wsm_user_configured') is not None else '<unbekannt>')}

#### Hinweise
- Log-Einträge können in Compliance Screening Logs erstellt werden, um einen zentralen Audit-Trail zu führen.
- Technische Überwachung der Aktualität der Sanktionslisten ist möglich, um z. B. Firewall-Probleme zu identifizieren.
"""

    return {
        "messages": [AIMessage(content=response_content)],
        "next_node_after_qa": NodeNames.EXPLAIN_SCREENING_VARIANTS,
    }


def decision_interrupt_node(state: ApiMappingState) -> dict:
    payload = interrupt({
        "type": "choice_or_question",
        "prompt": "Drücke `weiter` zum Fortfahren oder stelle deine Frage.",
    })

    decision, question = None, None

    if isinstance(payload, dict):
        if payload.get("continue") is True or str(payload.get("continue")).lower() in {"true", "1", "yes"}:
            decision = "continue"
        elif "question" in payload:
            decision = "qa"
            question = str(payload["question"]).strip()
    else:
        raise ValueError(f"Unexpected interrupt payload type: {type(payload)}")

    if decision is None:
        decision = "qa"
        question = (question or "").strip()

    out = {"decision": decision, "pending_question": question}
    if question:
        out["messages"] = [HumanMessage(content=question)]
    return out


def route_from_decision_interrupt(state: ApiMappingState) -> str:
    if state.get("decision") == "continue":
        return state.get("next_node_after_qa", NodeNames.EXPLAIN_SCREENING_VARIANTS)
    return NodeNames.QA_MODE


def explain_screening_variants_node(state: ApiMappingState) -> dict:
    """Explain the three screening variants for API integration."""
    response_content = """
## Drei Varianten für die Sanktionslistenprüfung per API

### 1. Einseitige Datenübergabe (Basis-Variante)

**Funktionsweise:**
- Übergabe einzelner Geschäftspartner oder Transaktionsdaten via `screenAddresses`
- Datensatz sollte Name, Adresse, eindeutige Referenz und Adresstyp enthalten
- Prüfung gegen Sanktionslisten, Protokollierung in TCM
- Response: Treffer/Nichttreffer direkt im API-Response

**Workflow bei Treffer:**
- Optional: Automatische Sperre im Partnersystem oder Benutzerbenachrichtigung
- E-Mail-Versendung an konfigurierten TCM-Empfänger (Compliance-Verantwortlicher)
- Manuelle Bearbeitung in TCM: Good-Guy-Definition oder Treffer-Bestätigung
- Entsperrung im Partnersystem erfolgt manuell nach Good-Guy-Definition

### 2. Übergabe mit automatischer Nachprüfung (Erweiterte Variante)

**Zusätzliche Funktionalität:**
- Regelmäßige automatische Nachprüfung offener Treffer (z.B. alle 60 Minuten)
- Verwendung derselben `screenAddresses` API mit Parameter `suppressLogging=true`
- Automatische Entsperrung nach Good-Guy-Definition in TCM

**Implementierung:**
- Partnersystem speichert Objekte mit Adresstreffern
- Periodische Wiederholung der Prüfung mit `suppressLogging=true`
- Automatisches Entsperren bei Good-Guy-Status

### 3. Deep-Link Integration (Komfort-Funktion)

**Zusätzliche Schnittstelle:**
- API `screeningLogEntry` für temporäre Weblinks zur TCM-Trefferbearbeitung
- Implementierung als Button/Menüeintrag im Partnersystem
- Direkter Zugang zur Bearbeitungsmaske in TCM

**Anwendung:**
- Benutzer kann Treffer direkt aus dem Partnersystem heraus bearbeiten
- Link nur temporär gültig - daher on-demand Generierung erforderlich
- Erhöht Benutzerfreundlichkeit und Workflow-Effizienz

### Empfehlung
- **Variante 1:** Für einfache Integration, manuelle Nachbearbeitung akzeptabel
- **Variante 2:** Für automatisierte Workflows, reduziert manuellen Aufwand
- **Variante 3:** Zusätzlich zu Variante 1 oder 2 für optimale Benutzererfahrung
"""

    return {
        "messages": [AIMessage(content=response_content)],
        "next_node_after_qa": NodeNames.EXPLAIN_RESPONSES,
    }


def explain_responses_node(state: ApiMappingState) -> dict:
    """Explain the different response scenarios from the screening API."""
    response_content = """
## API Response-Szenarien und Systemreaktionen

Die Sanktionslistenprüfung liefert verschiedene Response-Kombinationen, die unterschiedliche Aktionen im Partnersystem erfordern:

### 📍 Treffer-Szenario
```json
{
  "matchFound": true,
  "wasGoodGuy": false
}
```
**Bedeutung:** Sanktionslistentreffer gefunden, noch nicht als unbedenklich eingestuft

**Empfohlene Systemreaktion:**
- 🔒 **Automatische Sperre** des Geschäftspartners/der Transaktion
- 📧 **Benachrichtigung** an Compliance-Verantwortliche
- 🚫 **Blockierung** weiterer Geschäftsprozesse bis zur manuellen Freigabe
- 📝 **Logging** der Sperrung für Audit-Zwecke

### ✅ Unbedenklich-Szenario
```json
{
  "matchFound": false,
  "wasGoodGuy": false
}
```
**Bedeutung:** Keine Sanktionslistentreffer gefunden

**Empfohlene Systemreaktion:**
- ✅ **Keine Aktion erforderlich** - Geschäftsprozess kann fortgesetzt werden
- 📝 **Optional:** Protokollierung der erfolgreichen Prüfung

### 🟢 Good-Guy-Szenario
```json
{
  "matchFound": false,
  "wasGoodGuy": true
}
```
**Bedeutung:** Bereits als unbedenklich (Good-Guy) klassifiziert, daher keine erneute Prüfung

**Empfohlene Systemreaktion:**
- ✅ **Keine Aktion erforderlich** - Good-Guy-Status bestätigt
- 📝 **Optional:** Vermerk über Good-Guy-Status im System
- ⚡ **Performance-Vorteil** durch verkürzte Prüfzeit
"""

    return {
        "messages": [AIMessage(content=response_content)],
        "next_node_after_qa": NodeNames.API_MAPPING_INTRO,
    }


def api_mapping_intro_node(state: ApiMappingState) -> dict:
    """Introduce the API mapping service and gather initial system information."""
    response_content = """
## 🔄 API Mapping Service

Jetzt können wir Ihnen beim Mapping Ihrer bestehenden API-Struktur auf die AEB TCM Screening API helfen.

**Was wir benötigen:**

### 1. System-Information
Bitte beschreiben Sie:
- **Systemname/Typ:** Welches System möchten Sie anbinden? (z.B. SAP, Salesforce, Custom ERP)
- **Prozess:** Welcher Geschäftsprozess soll integriert werden? (z.B. Kundenanlage, Bestellverarbeitung, Lieferantenprüfung)

### 2. API-Metadaten
Wir benötigen Ihre bestehende API-Struktur in einem der folgenden Formate:
- **JSON-Schema** Ihrer Adress-/Partnerdaten
- **XML-Beispiel** einer typischen Datenanfrage
- **CSV-Struktur** mit Feldnamen und -beschreibungen
- **OpenAPI/Swagger** Definition

**Nächster Schritt:** Bitte nennen Sie zunächst Ihr **Systemname** und den **anzubindenden Prozess**.
"""

    return {
        "messages": [AIMessage(content=response_content)],
        "next_node_after_qa": NodeNames.PROCESS_AND_MAP_API,
    }


def get_api_data_interrupt_node(state: ApiMappingState) -> dict:
    payload = interrupt({
        "type": "get_api_data",
        "prompt": "Bitte geben Sie Ihren Systemnamen, Prozess und bestehenden API-Metadaten an (z.B. JSON-Schema, XML-Beispiel, CSV-Struktur, OpenAPI/Swagger Definition).",
    })

    system_name, process, api_metadata = None, None, None
    if isinstance(payload, dict):
        if payload.get("system_name"):
            system_name = str(payload["system_name"]).strip()
        if payload.get("process"):
            process = str(payload["process"]).strip()
        if payload.get("api_metadata"):
            api_metadata = api_metadata  # This is the filename
    else:
        raise ValueError(f"Unexpected interrupt payload type: {type(payload)}")

    out: dict = {}
    if system_name:
        out["system_name"] = system_name
    if process:
        out["process"] = process
    if api_metadata:
        out["api_metadata"] = api_metadata
    return out


def process_and_map_api_node(state: ApiMappingState) -> dict:
    """Process customer API metadata and generate mapping suggestions."""
    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)
    prov = state.get("provisioning", {})

    ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                       Config.KNOWLEDGE_BASE_VECTOR_STORE)
    ensure_index_built(Config.API_DATA_DIR.as_posix(),
                       Config.API_DATA_VECTOR_STORE)

    api_data_snippets = rag_search(
        "name, street, address, firstname, surname, entity, postbox, city, country, district", k=5,
        store_dir=Config.API_DATA_VECTOR_STORE,
    )

    docs_snippets = rag_search(
        "REST API, screening, name, street, address, firstname, surname, entity, postbox, city, country, district", k=5,
        store_dir=Config.KNOWLEDGE_BASE_VECTOR_STORE,
    )

    sys = SystemMessage(content=(
        "Du bist ein Experte für API-Mapping zwischen Kundensystemen und der AEB TCM Screening API. "
        "Analysiere die vom Kunden bereitgestellten API-Metadaten und erstelle ein präzises Mapping "
        "auf die AEB screenAddresses API-Struktur. Berücksichtige dabei die verfügbare Dokumentation."
    ))

    human = HumanMessage(content=f"""
Analysiere die folgenden Kunden-API-Metadaten und erstelle ein detailliertes Mapping zur AEB TCM Screening API:

**Kunden-API-Struktur:**
```
{user_input}
```

**Verfügbare AEB Konfiguration:**
- Test-Endpoint: {prov.get('test_endpoint', 'N/A')}
- Prod-Endpoint: {prov.get('prod_endpoint', 'N/A')} 
- ClientIdentCode: {prov.get('clientIdentCode', 'N/A')}
- WSM Benutzer konfiguriert: {('Ja' if prov.get('wsm_user_configured') else 'Nein' if prov.get('wsm_user_configured') is not None else 'Unbekannt')}
- Systemname: {state.get('system_name', 'N/A')}
- Prozess: {state.get('process', 'N/A')}
- API-Metadaten: {state.get('api_metadata', 'N/A')}

**Aufgabe:**
1. **Feldmapping analysieren:** Identifiziere Kunden-Felder und weise sie AEB-Feldern zu
2. **Transformationen vorschlagen:** Beschreibe notwendige Datenkonvertierungen
3. **JSON-Beispiel generieren:** Erstelle ein vollständiges screenAddresses Request-Beispiel
4. **Validierungsregeln:** Definiere Datenqualitätsprüfungen
5. **Implementierungshinweise:** Gebe praktische Umsetzungstipps

**Berücksichtige AEB API Dokumentation:**
{docs_snippets if docs_snippets else '[Keine Dokumentation verfügbar]'}
**Berücksichtige die API Metadaten des Kunden:**
{api_data_snippets if api_data_snippets else '[Keine Daten verfügbar]'}

Strukturiere deine Antwort klar und praxisorientiert mit JSON-Beispielen.
""")

    resp = llm.invoke([sys, human])

    return {
        "messages": [resp]
    }


def qa_mode_node(state: ApiMappingState) -> dict:
    """Handle free-flowing Q&A after the initial flow is completed."""
    prov = state.get("provisioning", {})
    question = (state.get("pending_question") or "").strip()

    if not question:
        payload = interrupt({
            "type": "question_or_continue",
            "prompt": "Wie kann ich dir bei der TCM Screening API Integration helfen? "
                      "Stelle deine Frage – oder schreibe `weiter`, um fortzufahren.",
        })
        if isinstance(payload, dict):
            if payload.get("continue") is True or str(payload.get("continue")).lower() in {"true", "1", "yes"}:
                return {"decision": "continue"}
            elif "question" in payload:
                decision = "qa"
                question = str(payload["question"]).strip()
        else:
            raise ValueError(
                f"Unexpected interrupt payload type: {type(payload)}")

    # If still no question stay here
    if not question:
        return {"decision": "qa"}

    # Check for debug commands
    if question.lower().strip() in ["debug", "debug rag", "debug vectorstore"]:
        debug_knowledge_base_files(Config.KNOWLEDGE_BASE_DIR.as_posix())
        debug_vectorstore_contents(Config.KNOWLEDGE_BASE_VECTOR_STORE)
        return {
            "messages": [AIMessage(content="Debug information has been printed to the console. Check the server logs for detailed RAG system status.")],
            "decision": "qa",
            "pending_question": "",
        }

    ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                       Config.KNOWLEDGE_BASE_VECTOR_STORE)

    snippets = rag_search(f"Question about Screening API: {question}", k=5)

    context_info = []
    if prov.get("test_endpoint"):
        context_info.append(
            f"Test-Endpoint: {prov.get('test_endpoint', 'N/A')}")
    if prov.get("prod_endpoint"):
        context_info.append(
            f"Prod-Endpoint: {prov.get('prod_endpoint', 'N/A')}")
    if prov.get("clientIdentCode"):
        context_info.append(
            f"Mandant (clientIdentCode): {prov.get('clientIdentCode', 'N/A')}")
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
Benutzerfrage: {question}

Verfügbare Konfiguration:
{context_str}

Verfügbare Dokumentationsauszüge:
{snippets_text}

Beantworte die Frage basierend auf den verfügbaren Informationen. 
WICHTIG: Nutze die Dokumentationsauszüge als primäre Quelle und verwende die korrekte API-Struktur aus der Dokumentation.
""")

    resp = llm.invoke([sys, human])

    decision, question = None, None

    if decision is None:
        decision = "qa"
        question = (question or "").strip()

    return {
        "messages": [resp],
        "decision": decision or "qa",
        "pending_question": question,
    }


def route_from_qa_mode(state: ApiMappingState, config: RunnableConfig) -> str:
    decision = state.get("decision")
    if decision == "continue":
        return state.get("next_node_after_qa")
    return NodeNames.QA_MODE
