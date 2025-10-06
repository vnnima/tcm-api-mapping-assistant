from __future__ import annotations
from agent.utils import get_latest_user_message, get_last_user_message
from agent.llm import get_llm
from .state import RequestValidationState, ValidationNodeNames
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json


llm = get_llm()


def get_request_node(state: RequestValidationState) -> Dict[str, Any]:
    """Get the API request from the user for validation."""
    messages = state.get("messages", [])

    # Check if we already have a user request extracted
    if state.get("user_request"):
        return {}  # Request already processed

    # If no messages yet, show the initial prompt
    if not messages:
        return {
            "messages": [
                AIMessage(content=(
                    "# API Request Validation\n\n"
                    "Ich helfe Ihnen dabei, Ihren API-Aufruf für die AEB TCM Screening API zu validieren.\n\n"
                    "**Bitte geben Sie Ihren API-Request ein:**\n"
                    "- Als JSON-Format\n"
                    "- Vollständige Request-Struktur\n"
                    "- Beispiel mit echten oder Test-Daten\n\n"
                    "Ich prüfe dann:\n"
                    "✅ Syntax und technische Korrektheit\n"
                    "✅ Vollständigkeit der prüfrelevanten Felder\n"
                    "✅ Fachliche Qualität der Datenfelder\n"
                    "✅ Verbesserungsvorschläge für bessere Treffer-Bearbeitung"
                ))
            ]
        }

    # Try to get the latest user message
    user_input = get_latest_user_message(messages)

    if not user_input.strip():
        # No user input yet, stay in this node
        return {}

    # We have user input, extract it as the request
    return {
        "user_request": user_input.strip(),
        "messages": [
            AIMessage(
                content=f"Danke! Ich analysiere Ihren API-Request:\n\n```json\n{user_input.strip()}\n```")
        ]
    }


def validate_request_node(state: RequestValidationState) -> Dict[str, Any]:
    """Validate the API request for syntax, completeness, and quality."""
    user_request = state.get("user_request")
    if not user_request:
        return {}

    # Read the system prompt
    try:
        with open("src/agent/request_validation_graph/system-prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except FileNotFoundError:
        system_prompt = (
            "You are an expert in AEB Trade Compliance Management API validation. "
            "Analyze API requests for syntax, completeness, and quality."
        )

    sys_message = SystemMessage(content=system_prompt)

    human_message = HumanMessage(content=f"""
Bitte analysieren Sie den folgenden API-Request für die AEB TCM Screening API:

```json
{user_request}
```

**Führen Sie eine vollständige Validierung durch:**

1. **Syntax-Prüfung:**
   - Ist das JSON technisch korrekt?
   - Sind alle Pflichtfelder vorhanden?
   - Stimmt die API-Struktur?

2. **Fachliche Vollständigkeit:**
   - Sind alle prüfrelevanten Felder vorhanden?
   - Sind die Feldwerte fachlich sinnvoll befüllt?
   - Entspricht der `addressType` den Daten?

3. **Qualitäts-Analyse:**
   - Welche Datenqualitätsprobleme gibt es?
   - Welche Felder könnten die Trefferqualität verbessern?
   - Gibt es Inkonsistenzen in den Daten?

4. **Verbesserungsvorschläge:**
   - Welche zusätzlichen Felder sollten befüllt werden?
   - Wie können Organisationseinheiten, IDs, Conditions verbessert werden?
   - Welche Optimierungen würden die Treffer-Bearbeitung erleichtern?

**Antworten Sie strukturiert mit:**
- ✅/❌ für jeden Prüfpunkt
- Konkreten Verbesserungsvorschlägen
- Einem optimierten Request-Beispiel
- Begründungen für alle Empfehlungen

Seien Sie detailliert und praxisorientiert!
""")

    response = llm.invoke([sys_message, human_message])

    # Parse validation results (simplified - in a real implementation you might want more structured parsing)
    content = str(response.content).lower() if response.content else ""
    syntax_valid = "✅" in str(response.content) and (
        "syntax" in content or "json" in content)
    required_fields_present = "✅" in str(
        response.content) and "pflichtfeld" in content

    return {
        "validation_results": {
            "analysis": response.content,
            "syntax_valid": syntax_valid,
            "required_fields_present": required_fields_present
        },
        "syntax_valid": syntax_valid,
        "required_fields_present": required_fields_present,
        "messages": [response]
    }


def show_results_node(state: RequestValidationState) -> Dict[str, Any]:
    """Show the final validation results and mark as completed."""
    validation_results = state.get("validation_results")
    if not validation_results:
        return {
            "messages": [
                AIMessage(content="❌ Keine Validierungsergebnisse verfügbar.")
            ],
            "completed": True
        }

    # Create a summary message based on validation results
    syntax_status = "✅" if state.get("syntax_valid") else "❌"
    fields_status = "✅" if state.get("required_fields_present") else "❌"

    summary_content = f"""
## 📋 Validierung Abgeschlossen

**Ergebnisse:**
- {syntax_status} **Syntax**: {"Korrekt" if state.get("syntax_valid") else "Probleme gefunden"}
- {fields_status} **Pflichtfelder**: {"Vollständig" if state.get("required_fields_present") else "Unvollständig"}

Die detaillierte Analyse finden Sie in der vorherigen Nachricht.

**Nächste Schritte:**
- 🔄 Weiteren Request validieren
- 📝 Request basierend auf Empfehlungen überarbeiten  
- ❓ Fragen zu den Verbesserungsvorschlägen stellen

*Für eine neue Validierung geben Sie einfach einen neuen API-Request ein.*
"""

    return {
        "messages": [
            AIMessage(content=summary_content)
        ],
        "completed": True
    }


# Routing functions
def route_from_get_request(state: RequestValidationState) -> str:
    """Route from get_request node."""
    # If we have a user request, proceed to validation
    if state.get("user_request"):
        return ValidationNodeNames.VALIDATE_REQUEST

    # Check if we have any user messages to process
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    # If we have user input, stay in get_request to process it
    if user_input.strip():
        return ValidationNodeNames.GET_REQUEST

    # No user input and no request - end the flow
    return "__end__"


def route_from_validate_request(state: RequestValidationState) -> str:
    """Route from validate_request node."""
    return ValidationNodeNames.SHOW_RESULTS


def route_from_show_results(state: RequestValidationState) -> str:
    """Route from show_results node."""
    # This could be extended to loop back for another validation
    return "__end__"
