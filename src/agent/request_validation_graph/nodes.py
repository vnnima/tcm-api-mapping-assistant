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
                "I'll help you validate your API call for the AEB TCM Screening API.\n\n"
                "**Please enter your API request:**\n"
                "- In JSON format\n"
                "- Complete request structure\n"
                "- Example with real or test data\n\n"
                "I will then check:\n"
                "✅ Syntax and technical correctness\n"
                "✅ Completeness of audit-relevant fields\n"
                "✅ Professional quality of data fields\n"
                "✅ Improvement suggestions for better hit processing"
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
                content=f"Thank you! I'm analyzing your API request:\n\n```json\n{user_input.strip()}\n```")
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
Please analyze the following API request for the AEB TCM Screening API:

```json
{user_request}
```

**Perform a comprehensive validation:**

1. **Syntax check:**
   * Is the JSON technically correct?
   * Are all required fields present?
   * Does the API structure match?

2. **Functional completeness:**
   * Are all screening-relevant fields included?
   * Are the field values populated in a meaningful, domain-correct way?
   * Does the `addressType` correspond to the data?

3. **Quality analysis:**
   * What data quality issues are present?
   * Which fields could improve match quality?
   * Are there inconsistencies in the data?

4. **Recommendations for improvement:**
   * Which additional fields should be filled?
   * How can organizational units, IDs, and conditions be improved?
   * Which optimizations would make hit processing easier?

**Respond in a structured way with:**

* ✅/❌ for each check item
* Concrete improvement suggestions
* An optimized request example
* Justifications for all recommendations

Be detailed and practice-oriented!

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
            AIMessage(content="❌ No validation results available.")
            ],
            "completed": True
        }

    # Create a summary message based on validation results
    syntax_status = "✅" if state.get("syntax_valid") else "❌"
    fields_status = "✅" if state.get("required_fields_present") else "❌"

    summary_content = f"""
## 📋 Validation Complete

**Results:**
- {syntax_status} **Syntax**: {"Correct" if state.get("syntax_valid") else "Issues found"}
- {fields_status} **Required Fields**: {"Complete" if state.get("required_fields_present") else "Incomplete"}

You can find the detailed analysis in the previous message.

**Next Steps:**
- 🔄 Validate another request
- 📝 Revise request based on recommendations  
- ❓ Ask questions about the improvement suggestions

*To perform a new validation, simply enter a new API request.*
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
