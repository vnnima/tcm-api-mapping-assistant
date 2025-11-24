from __future__ import annotations
from .state import ApiMappingState
from langgraph.types import interrupt
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from enum import Enum
from api_mapping_agent.utils import (URL_RE, parse_client_ident, parse_endpoints,
                                     parse_wsm_user, parse_yes_no, has_endpoint_information,
                                     get_last_user_message, get_latest_user_message, get_last_assistant_message, format_endpoints_message)
from api_mapping_agent.llm import get_llm
from api_mapping_agent.config import Config
from api_mapping_agent.rag import rag_search, build_index, ensure_index_built, debug_vectorstore_contents, debug_knowledge_base_files, build_index_fresh
from .utils import get_screen_addresses_spec, get_general_information_about_screening_api, get_api_examples


class NodeNames(str, Enum):
    INTRO = "intro"
    CLARIFY = "clarify"
    ASK_CLIENT = "ask_client"
    ASK_WSM = "ask_wsm"
    ASK_GENERAL_INFO = "ask_general_info"
    GENERAL_SCREENING_INFO = "general_screening_info"
    ASK_SCREENING_VARIANTS = "ask_screening_variants"
    EXPLAIN_SCREENING_VARIANTS = "explain_screening_variants"
    ASK_RESPONSES = "ask_responses"
    EXPLAIN_RESPONSES = "explain_responses"
    API_MAPPING_INTRO = "api_mapping_intro"
    DECISION_INTERRUPT = "decision_interrupt"
    GET_API_DATA_INTERRUPT = "get_api_data_interrupt"
    PROCESS_AND_MAP_API = "process_and_map_api"
    QA_MODE = "qa_mode"


llm = get_llm()


def intro_node(state: ApiMappingState) -> dict:
    messages = state.get("messages", [])
    # If there are no messages, it's the first turn.
    # Greet the user and ask for endpoints.
    if not messages:
        return {
            "started": True,
            "messages": [
                AIMessage(content=(
                    "Hello! I'm your **AEB API Mapping Assistant**. "
                    "I help you cleanly integrate the **TCM Screening API** into your system.\n\n"
                    "Please first provide the **AEB RZ Endpoints** (at least one URL). "
                    "These are required for API integration. "
                    f"Note: {Config.ENDPOINTS_HELP_URL}\n\n"
                    "Format:  \n"
                    "```\n"
                    "Test: https://...  \n"
                    "Prod:  https://...  \n"
                    "```"
                ))
            ]
        }

    # This part handles the user's response to the endpoint question.
    user_input = get_latest_user_message(messages)
    if not user_input:
        # This case should ideally not be hit if the flow is correct
        return {}

    prov = state.get("provisioning", {})
    found_endpoints = parse_endpoints(user_input)

    # If exactly one URL and no prior endpoints, accept as test by default
    single = URL_RE.findall(user_input)
    if single and len(single) == 1 and not found_endpoints and not has_endpoint_information(prov):
        found_endpoints["test_endpoint"] = single[0]

    # If user provided input but parsing failed, it will be handled by the router.
    if not has_endpoint_information(prov) and not found_endpoints:
        return {}

    prov = {**prov, **found_endpoints}
    lines = format_endpoints_message(found_endpoints)

    if found_endpoints:
        return {
            "provisioning": prov,
            "messages": [
                AIMessage(content="Thank you! Endpoints recorded:\n" +
                          "\n".join(lines))
            ]
        }
    else:
        return {
            "provisioning": prov
        }


def route_from_intro(state: ApiMappingState) -> str:
    """Route from intro based on user response and current state."""

    # TODO: Can remove this when I implement the looping in qa_mode with interrupt
    if state.get("completed", False):
        return NodeNames.PROCESS_AND_MAP_API

    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)

    if not user_input:
        return END

    prov = state.get("provisioning", {})

    # Check if we have endpoint information
    if not has_endpoint_information(prov):
        return NodeNames.CLARIFY

    if not prov.get("clientIdentCode"):
        return NodeNames.ASK_CLIENT

    if "wsm_user_configured" not in prov:
        return NodeNames.ASK_WSM

    # All good -> guide
    return NodeNames.GENERAL_SCREENING_INFO


def clarify_node(state: ApiMappingState) -> dict:
    """Generic clarify node that looks at the last question and user's response to provide help."""
    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)

    last_question = get_last_assistant_message(
        messages) or """
Please first provide the AEB RZ Endpoints (at least one URL). These are required for API integration. Format:

Test: https://...  
Prod:  https://...  
"""
    if not last_question:
        last_question = "a question"  # TODO: Handle this differently

    sys = SystemMessage(content=(
        "You are a helpful assistant. The user has not answered a question correctly. "
        "Look at the original question and the user's answer and explain kindly "
        "what was wrong and how they should answer correctly."
    ))

    human = HumanMessage(content=f"""
The original question/prompt was:
"{last_question}"

The user answered: "{user_input}"

Can you briefly and kindly explain what was missing or incorrect in their answer, and how they should answer correctly?

Keep the answer short.
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
        return NodeNames.INTRO
    if not prov.get("clientIdentCode"):
        return NodeNames.ASK_CLIENT
    if "wsm_user_configured" not in prov:
        return NodeNames.ASK_WSM
    else:
        return NodeNames.INTRO


def ask_client_node(state: ApiMappingState) -> dict:
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)
    prov = state.get("provisioning", {})

    confirmation_msgs = []

    if not user_input:
        return {
            "messages": confirmation_msgs + [
                AIMessage(content=(
                    "2) **Client Name (clientIdentCode)**:\n"
                    "- A separate client is available for each customer.\n"
                    "Please share your **clientIdentCode** (e.g. APITEST).\n\n"
                    "Format: `clientIdentCode=APITEST` or `Client: APITEST`"
                ))
            ]
        }

    if user_input:
        parsed_client = parse_client_ident(user_input)

        # If parsing failed, use LLM to understand user intent
        if not parsed_client:
            sys = SystemMessage(content=(
                "You are helping analyze a user's response about their clientIdentCode. "
                "The clientIdentCode is a unique identifier for each customer in the TCM Screening API. "
                "Analyze the user's message and determine:\n"
                "1. If they explicitly state they don't have a clientIdentCode (return 'no_code')\n"
                "2. If they provided a code but it wasn't parsed (extract and return it)\n"
                "3. If they're asking a question or unclear (return 'unclear')\n\n"
                "Respond with ONLY ONE of:\n"
                "- 'no_code' if they don't have one\n"
                "- 'unclear' if you can't determine\n"
                "- The actual code if you can extract it"
            ))

            human = HumanMessage(content=f"User's response: \"{user_input}\"")
            llm_response = llm.invoke([sys, human])
            llm_answer = str(llm_response.content).strip().lower()

            if llm_answer == "no_code":
                # User doesn't have a code, use fallback
                prov = {**prov, "clientIdentCode": "APITEST"}
                return {
                    "provisioning": prov,
                    "messages": confirmation_msgs + [
                        AIMessage(content=(
                            "No problem! I'll use **APITEST** as the default clientIdentCode for now. "
                            "This is a standard test client that can be used for integration testing.\n\n"
                            f"Client recorded: clientIdentCode=APITEST"
                        ))
                    ]
                }
            elif llm_answer != "unclear":
                # LLM extracted a code
                prov = {**prov, "clientIdentCode": llm_answer.upper()}
            # If unclear, fall through to re-ask
        else:
            prov = {**prov, "clientIdentCode": parsed_client}

    if not prov.get("clientIdentCode"):
        return {
            "provisioning": prov,
            "messages": confirmation_msgs + [
                AIMessage(content=(
                    "2) **Client Name (clientIdentCode)**:\n"
                    "- A separate client is available for each customer.\n"
                    "Please share your **clientIdentCode** (e.g. APITEST).\n\n"
                    "Format: `clientIdentCode=APITEST` or `Client: APITEST`\n\n"
                    "If you don't have a clientIdentCode yet, just let me know and I'll use a default test value."
                ))
            ]
        }

    return {
        "provisioning": prov,
        "messages": confirmation_msgs + [
            AIMessage(
                content=f"Thank you! Client recorded: clientIdentCode={prov.get('clientIdentCode', 'N/A')}")
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
    user_input = get_latest_user_message(messages)
    prov = state.get("provisioning", {})

    if not user_input.strip():
        return {
            "provisioning": prov,
            "messages": [
                AIMessage(content=(
                    "3) **WSM User for Authentication**:\n"
                    "- In addition to the client, there is a **technical WSM user** including password for API connection.\n"
                    "- [This documentation](https://trade-compliance.docs.developers.aeb.com/docs/setting-up-your-environment-1) provides more details about setting up the authentication and the different options"
                    "Is this user already set up? (Yes/No)\n\n"
                    "If you don't have it yet, just let me know and we can continue without it for now."
                ))
            ]
        }

    # If parsing returned None but user provided input, use LLM to understand intent
    if prov.get("wsm_user_configured") is None and user_input:
        sys = SystemMessage(content=(
            "You are helping analyze a user's response about their WSM user setup. "
            "The WSM user is a technical user with credentials needed for API authentication. "
            "Analyze the user's message and determine:\n"
            "1. If they explicitly state they have it configured (return 'yes')\n"
            "2. If they explicitly state they don't have it or need to set it up later (return 'no')\n"
            "3. If they're asking a question or unclear (return 'unclear')\n\n"
            "Respond with ONLY ONE word: 'yes', 'no', or 'unclear'"
        ))

        human = HumanMessage(content=f"User's response: \"{user_input}\"")
        llm_response = llm.invoke([sys, human])
        llm_answer = str(llm_response.content).strip().lower()

        if llm_answer == "no":
            # User doesn't have WSM user, set as not configured and continue
            prov["wsm_user_configured"] = False
            return {
                "provisioning": prov,
                "messages": [
                    AIMessage(content=(
                        "No worries! You can continue without the WSM user for now and set it up later. "
                        "The WSM user credentials will be needed when you're ready to make live API calls.\n\n"
                        "WSM user available: No"
                    ))
                ]
            }
        elif llm_answer == "yes":
            prov["wsm_user_configured"] = True
            is_wsm_configured = True
        # If unclear, fall through to re-ask

    if prov.get("wsm_user_configured") is None:
        return {
            "provisioning": prov,
            "messages": [
                AIMessage(content=(
                    "3) **WSM User for Authentication**:\n"
                    "- In addition to the client, there is a **technical WSM user** including password for API connection.\n"
                    "Is this user already set up? (Yes/No)\n\n"
                    "If you don't have it yet, just let me know and we can continue without it for now."
                ))
            ]
        }

    yn = "Yes" if prov.get("wsm_user_configured") else "No"
    return {
        "provisioning": prov,
        "messages": [
            AIMessage(content=f"WSM user available: {yn}.")
        ]
    }


def route_from_wsm(state: ApiMappingState) -> str:
    """Route from WSM based on current provisioning state."""
    prov = state.get("provisioning", {})
    messages = state.get("messages", [])
    user_input = get_latest_user_message(messages)

    if user_input.strip() and prov.get("wsm_user_configured") is None:
        return NodeNames.CLARIFY

    if prov.get("wsm_user_configured") is None:
        return END

    return NodeNames.ASK_GENERAL_INFO


def ask_general_info_node(state: ApiMappingState) -> dict:
    """Ask user if they want to see general screening information."""
    payload = interrupt({
        "type": "show_general_info",
        "title": "1. Initial Integration Guide for Sanctions List Screening",
        "prompt": "Would you like to see the Initial Integration Guide for Sanctions List Screening? (Yes or Skip)",
    })

    skip = None  # None means show content, True means skip, False means loop
    messages_to_add = []

    if isinstance(payload, dict):
        # Check if user asked a question
        if "question" in payload and payload["question"]:
            question = str(payload["question"]).strip()

            # Ensure indexes exist
            Config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            Config.KNOWLEDGE_BASE_VECTOR_STORE.mkdir(
                parents=True, exist_ok=True)
            ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                               Config.KNOWLEDGE_BASE_VECTOR_STORE)

            # Get RAG snippets
            snippets = rag_search(
                f"Question about Screening API: {question}", k=5)

            prov = state.get("provisioning", {})
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
                wsm_status = "Yes" if prov["wsm_user_configured"] else "No"
                context_info.append(f"WSM-User: {wsm_status}")

            context_str = "\n".join(
                context_info) if context_info else "No configuration data available."
            snippets_text = "\n\n".join([f"Document {i+1}:\n{snippet}" for i, snippet in enumerate(
                snippets)]) if snippets else '[No relevant documentation excerpts found]'

            sys = SystemMessage(content=(
                "You are an AEB Trade Compliance API expert. "
                "Answer questions about the TCM Screening API precisely and helpfully in English. "
                "ALWAYS use the available documentation excerpts and configuration data. "
                "If documentation is available, base your answer on it and not on general knowledge."
            ))

            human = HumanMessage(content=f"""
User question: {question}

Available configuration:
{context_str}

Available documentation excerpts:
{snippets_text}

Answer the question based on the available information. 
IMPORTANT: Use the documentation excerpts as the primary source and use the correct API structure from the documentation.
""")

            resp = llm.invoke([sys, human])
            messages_to_add.append(HumanMessage(content=question))
            messages_to_add.append(resp)
            # Loop back to ask again
            skip = False

        # Check if user wants to skip or show
        elif "response" in payload:
            response = str(payload.get("response", "")).strip().lower()
            if response in {"no", "skip", "false", "0"}:
                skip = True
            elif response in {"yes", "show", "true", "1"}:
                skip = None  # Show content

    return {"skip_general_info": skip, "messages": messages_to_add}


def route_from_ask_general_info(state: ApiMappingState) -> str:
    """Route based on whether user wants to see general info."""
    skip = state.get("skip_general_info")
    if skip is True:
        # User chose to skip
        return NodeNames.ASK_SCREENING_VARIANTS
    elif skip is False:
        # Question was answered, loop back to ask again
        return NodeNames.ASK_GENERAL_INFO
    else:
        # skip is None, show the content
        return NodeNames.GENERAL_SCREENING_INFO


def general_screening_info_node(state: ApiMappingState) -> dict:
    prov = state.get("provisioning", {})
    response_content = f"""
### Initial Integration Guide for Sanctions List Screening

#### 1. Formats
- **JSON/REST**: Use of REST API for communication.

#### 2. Objects to be Screened
- **Master Data**: Individual screening or bulk (max. 100 entries).
- **Transactions**: Screening during creation or modification.

#### 3. Fields
- **Required Fields**:
  - Name
  - Address
  - Unique Reference
- **Screening-relevant Fields**:
  - Address Type
- **Optional Fields**: No specific optional fields defined.

#### 4. Triggers
- **Creation/Modification**: Automatic screening for new or changed master data and transactions.
- **Periodic Batch Screening**: Recommended once per month.

#### 5. Integration Variants
- **a) One-way submission via screenAddresses**:
  - Response: Hit/No hit
  - Email to TCM recipient
  - Manual (un)blocking required

- **b) Submission + regular re-screening**:
  - Parameter: `suppressLogging=true`
  - Frequency: Every 60 minutes
  - Automatic unblocking after Good-Guy classification

- **c) Optional Deep-Link via screeningLogEntry**:
  - Temporary link
  - Integration as button/menu in partner system

#### 6. Response Scenarios
- **matchFound=true & wasGoodGuy=false**:
  - Result: Hit found
  - Action: (Optional) Block/Notification

- **matchFound=false & wasGoodGuy=false**:
  - Result: No hit
  - Action: None

- **matchFound=false & wasGoodGuy=true**:
  - Result: No hit (already Good-Guy)
  - Action: None

#### Endpoints
- **Test Endpoint**: {prov.get('test_endpoint') or '<missing>'}
- **Prod Endpoint**: {prov.get('prod_endpoint') or '<missing>'}
- **Client (clientIdentCode)**: {prov.get('clientIdentCode') or '<missing>'}
- **WSM User Available**: {('Yes' if prov.get('wsm_user_configured') else 'No' if prov.get('wsm_user_configured') is not None else '<unknown>')}

#### Notes
- Log entries can be created in Compliance Screening Logs to maintain a central audit trail.
- Technical monitoring of sanctions list currency is possible to identify issues like firewall problems.
"""

    return {
        "messages": [AIMessage(content=response_content)],
    }


def ask_screening_variants_node(state: ApiMappingState) -> dict:
    """Ask user if they want to see screening variants explanation."""
    payload = interrupt({
        "type": "show_screening_variants",
        "title": "2. Recommended Options for API Usage",
        "prompt": "Would you like to see the detailed Recommended Options for API Usage (3 integration variants)? (Yes or Skip)",
    })

    skip = None  # None means show content, True means skip, False means loop
    messages_to_add = []

    if isinstance(payload, dict):
        # Check if user asked a question
        if "question" in payload and payload["question"]:
            question = str(payload["question"]).strip()

            # Ensure indexes exist
            Config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            Config.KNOWLEDGE_BASE_VECTOR_STORE.mkdir(
                parents=True, exist_ok=True)
            ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                               Config.KNOWLEDGE_BASE_VECTOR_STORE)

            # Get RAG snippets
            snippets = rag_search(
                f"Question about Screening API: {question}", k=5)

            prov = state.get("provisioning", {})
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
                wsm_status = "Yes" if prov["wsm_user_configured"] else "No"
                context_info.append(f"WSM-User: {wsm_status}")

            context_str = "\n".join(
                context_info) if context_info else "No configuration data available."
            snippets_text = "\n\n".join([f"Document {i+1}:\n{snippet}" for i, snippet in enumerate(
                snippets)]) if snippets else '[No relevant documentation excerpts found]'

            sys = SystemMessage(content=(
                "You are an AEB Trade Compliance API expert. "
                "Answer questions about the TCM Screening API precisely and helpfully in English. "
                "ALWAYS use the available documentation excerpts and configuration data. "
                "If documentation is available, base your answer on it and not on general knowledge."
            ))

            human = HumanMessage(content=f"""
User question: {question}

Available configuration:
{context_str}

Available documentation excerpts:
{snippets_text}

Answer the question based on the available information. 
IMPORTANT: Use the documentation excerpts as the primary source and use the correct API structure from the documentation.
""")

            resp = llm.invoke([sys, human])
            messages_to_add.append(HumanMessage(content=question))
            messages_to_add.append(resp)
            # Loop back to ask again
            skip = False

        # Check if user wants to skip or show
        elif "response" in payload:
            response = str(payload.get("response", "")).strip().lower()
            if response in {"no", "skip", "false", "0"}:
                skip = True
            elif response in {"yes", "show", "true", "1"}:
                skip = None  # Show content

    return {"skip_screening_variants": skip, "messages": messages_to_add}


def route_from_ask_screening_variants(state: ApiMappingState) -> str:
    """Route based on whether user wants to see screening variants."""
    skip = state.get("skip_screening_variants")
    if skip is True:
        # User chose to skip
        return NodeNames.ASK_RESPONSES
    elif skip is False:
        # Question was answered, loop back to ask again
        return NodeNames.ASK_SCREENING_VARIANTS
    else:
        # skip is None, show the content
        return NodeNames.EXPLAIN_SCREENING_VARIANTS


def explain_screening_variants_node(state: ApiMappingState) -> dict:
    """Explain the three screening variants for API integration."""
    response_content = """
### Recommended Options for API Usage

#### 1. One-Way Transfer Without Rechecks

In the first option, data is transferred from a partner system to **Trade Compliance Management** on a one-way basis only. The API request can contain certain relevant business partners (customers, suppliers, employees, etc.) or transactional data (e.g., orders with multiple business partners). The data set should include the name, address information, a unique reference, IDs, conditions, and the address type.

A business partner check is then performed and logged in TCM. The result of the check can be a match or non-match, which is reported directly in the API Response message. If necessary, the object can be blocked or stopped in the partner system or a notification can be displayed directly to a user if a potential match is detected (`"matchFound": true, "wasGoodGuy": false`).

In the event of a match, an email is also sent to an email recipient configured in TCM (company's compliance officer), who then processes the matches in TCM (defines a **good guy** for false positives or marks them as true matches). This procedure only requires the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) that must be called once per business object (master data record or transactional data). The object must be released in the partner system or finally stopped or deleted manually by a user after the match handling in **Trade Compliance Management**.

#### 2. Transfer with Response Evaluation and Periodic Rechecks

In the second variant, data is transferred from the partner system and, in addition, open matches are regularly checked so that they can not only be blocked but also unblocked in the partner system. The API request can contain certain relevant business partners (customers, suppliers, employees, etc.) or transactional data (e.g., orders with multiple business partners). The data set should include the name, address information, a unique reference, IDs, conditions, and the address type.

A business partner check is then performed, which is logged in TCM. The result of the check can be a match or a non-match, which is reported directly in the response. If necessary, the object can be blocked or stopped in the partner system or a notification can be displayed directly to a user if a potential match is detected (`"matchFound": true, "wasGoodGuy": false`).

In the event of a match, an email is also sent to an email recipient configured in TCM (company's compliance officer), who then processes the matches in **Trade Compliance Management** (defines a **good guy** for false positives or marks them as true matches). This procedure requires the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) that have to be used several times.

- First, the initial check must be performed.
- For business objects that received a match during the initial check (`"matchFound": true, "wasGoodGuy": false`), a periodic recheck must be performed so that a subsequent noncritical check result can be determined in the partner system after the match processing in TCM.
- This recheck must be done until the check result gets uncritical (`"matchFound": false, "wasGoodGuy": true`).

This enables an automatic unblocking of the business object in the partner system after the **good guy** definition. The partner system must save the critical check results for address matches. The suggested frequency for the recheck is every 60 minutes. In addition, the parameter `suppressLogging` of the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) should be sent with the value `true` for periodic rechecks so that the periodic checks are not counted in addition to the invoiceable check volume.

#### 3. Transfer with Direct Access to Match Handling

The third option can be implemented as a supplement to the first or second variant. After a compliance screening check of a business object with the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`), the response can be evaluated in the partner system if there are potential matches (`"matchFound": true, "wasGoodGuy": false`).

This use case assumes that a user accesses the match handling directly from the partner system. In the partner system, the user should not only be shown the match, but there should also be a button or menu function to call up the match handling in **Trade Compliance Management**. The `screeningLogEntry` API can be used to generate and open a web link to the match handling UI in **Trade Compliance Management**. Since the web link is only valid temporarily, the API should only be called when the user wants to start the match handling by clicking on the function introduced in the partner system.

### Our Recommendations

#### For Simple Implementations
**Choose Variant 1** if you have:
- Limited development resources
- Low transaction volumes
- Acceptable manual compliance workflow
- Basic compliance requirements

#### For Automated Workflows  
**Choose Variant 2** if you have:
- High transaction volumes
- Need for automated unblocking
- Dedicated compliance team
- Advanced integration capabilities

#### For Optimal User Experience
**Add Variant 3** to either Variant 1 or 2 if you want:
- Seamless user experience
- Direct access to match handling
- Reduced context switching
- Enhanced compliance efficiency
"""

    return {
        "messages": [AIMessage(content=response_content)],
    }


def ask_responses_node(state: ApiMappingState) -> dict:
    """Ask user if they want to see response scenarios explanation."""
    payload = interrupt({
        "type": "show_responses",
        "title": "3. Response Scenarios Explanation",
        "prompt": "Would you like to see the detailed Response Scenarios explanation? (Yes or Skip)",
    })

    skip = None  # None means show content, True means skip, False means loop
    messages_to_add = []

    if isinstance(payload, dict):
        # Check if user asked a question
        if "question" in payload and payload["question"]:
            question = str(payload["question"]).strip()

            # Ensure indexes exist
            Config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            Config.KNOWLEDGE_BASE_VECTOR_STORE.mkdir(
                parents=True, exist_ok=True)
            ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                               Config.KNOWLEDGE_BASE_VECTOR_STORE)

            # Get RAG snippets
            snippets = rag_search(
                f"Question about Screening API: {question}", k=5)

            prov = state.get("provisioning", {})
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
                wsm_status = "Yes" if prov["wsm_user_configured"] else "No"
                context_info.append(f"WSM-User: {wsm_status}")

            context_str = "\n".join(
                context_info) if context_info else "No configuration data available."
            snippets_text = "\n\n".join([f"Document {i+1}:\n{snippet}" for i, snippet in enumerate(
                snippets)]) if snippets else '[No relevant documentation excerpts found]'

            sys = SystemMessage(content=(
                "You are an AEB Trade Compliance API expert. "
                "Answer questions about the TCM Screening API precisely and helpfully in English. "
                "ALWAYS use the available documentation excerpts and configuration data. "
                "If documentation is available, base your answer on it and not on general knowledge."
            ))

            human = HumanMessage(content=f"""
User question: {question}

Available configuration:
{context_str}

Available documentation excerpts:
{snippets_text}

Answer the question based on the available information. 
IMPORTANT: Use the documentation excerpts as the primary source and use the correct API structure from the documentation.
""")

            resp = llm.invoke([sys, human])
            messages_to_add.append(HumanMessage(content=question))
            messages_to_add.append(resp)
            # Loop back to ask again
            skip = False

        # Check if user wants to skip or show
        elif "response" in payload:
            response = str(payload.get("response", "")).strip().lower()
            if response in {"no", "skip", "false", "0"}:
                skip = True
            elif response in {"yes", "show", "true", "1"}:
                skip = None  # Show content

    return {"skip_responses": skip, "messages": messages_to_add}


def route_from_ask_responses(state: ApiMappingState) -> str:
    """Route based on whether user wants to see response scenarios."""
    skip = state.get("skip_responses")
    if skip is True:
        # User chose to skip
        return NodeNames.API_MAPPING_INTRO
    elif skip is False:
        # Question was answered, loop back to ask again
        return NodeNames.ASK_RESPONSES
    else:
        # skip is None, show the content
        return NodeNames.EXPLAIN_RESPONSES


def explain_responses_node(state: ApiMappingState) -> dict:
    """Explain the different response scenarios from the screening API."""
    response_content = """
### Response Scenarios

#### Scenario 1: Potential Match Detected

The following response message describes the scenario where a potential address match has been detected. A match handling in Trade Compliance Management is required and the object in the partner system should be blocked:

```json
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "VEN_4714",
    "referenceComment": "Vendor 4714"
  }
```

#### Scenario 2: No Match Found

The following scenario detects an uncritical address where no further action in Trade Compliance Management is required and where the business object in the partner system can be further processed and used:

```json
  {
    "matchFound": false,
    "wasGoodGuy": false,
    "referenceId": "VEN_4715",
    "referenceComment": "Vendor 4715"
  }
```

#### Scenario 3: Good Guy Definition

The third scenario detects an uncritical address due to a previous good guy definition in Trade Compliance Management. The business object in the partner system can be further processed and used:

```json
  {
    "matchFound": false,
    "wasGoodGuy": true,
    "referenceId": "VEN_4716",
    "referenceComment": "Vendor 4716"
  }
```
"""

    return {
        "messages": [AIMessage(content=response_content)],
    }


def api_mapping_intro_node(state: ApiMappingState) -> dict:
    """Introduce the API mapping service and gather initial system information."""
    response_content = """
## 🔄 API Mapping Service

Now we can help you map your existing API structure to the AEB TCM Screening API.

**What we need:**

### 1. System Information
Please describe:
- **System Name/Type:** Which system do you want to connect? (e.g. SAP, Salesforce, Custom ERP)
- **Process:** Which business process should be integrated? (e.g. Customer creation, Order processing, Supplier verification)

### 2. API Metadata
We need your existing API structure in one of the following formats:
- **JSON Schema** of your address/partner data
- **XML Example** of a typical data request
- **CSV Structure** with field names and descriptions
- **OpenAPI/Swagger** definition

**Next Step:** Please first provide your **system name** and the **process to be integrated**.
"""

    return {
        "messages": [AIMessage(content=response_content)],
        "next_node_after_qa": NodeNames.PROCESS_AND_MAP_API,
    }


def get_api_data_interrupt_node(state: ApiMappingState) -> dict:
    payload = interrupt({
        "type": "get_api_data",
        "prompt": "Please provide your system name, process, and existing API metadata (e.g., JSON Schema, XML example, CSV structure, OpenAPI/Swagger definition).",
    })

    system_name, process, api_filename, api_content = None, None, None, None
    if isinstance(payload, dict):
        if payload.get("system_name"):
            system_name = str(payload["system_name"]).strip()
        if payload.get("process"):
            process = str(payload["process"]).strip()
        # Handle new payload structure with file content
        if payload.get("api_metadata_filename") and payload.get("api_metadata_content"):
            api_filename = payload.get("api_metadata_filename")
            api_content = payload.get("api_metadata_content")
        # Handle legacy payload structure with file path (for backwards compatibility)
        elif payload.get("api_metadata"):
            # This would be a path in legacy format
            api_filename = payload.get("api_metadata")
    else:
        raise ValueError(f"Unexpected interrupt payload type: {type(payload)}")

    out: dict = {}
    if system_name:
        out["system_name"] = system_name
    if process:
        out["process"] = process
    if api_filename and api_content:
        # Save the content to a file in the backend's API data directory
        Config.API_DATA_DIR.mkdir(parents=True, exist_ok=True)
        api_file_path = Config.API_DATA_DIR / api_filename
        with open(api_file_path, "w", encoding="utf-8") as f:
            f.write(api_content)
        # Store just the filename, not full path
        out["api_file_path"] = api_filename
    elif api_filename:  # Legacy support
        out["api_file_path"] = api_filename
    return out


def process_and_map_api_node(state: ApiMappingState) -> dict:
    """Process customer API metadata and generate mapping suggestions."""
    messages = state.get("messages", [])
    prov = state.get("provisioning", {})
    api_file_path = state.get("api_file_path", "")
    if not api_file_path:
        raise Exception(
            f"Api data has no filename. Something went wrong with storing it. Api metadata: {api_file_path}")

    # Read the API data file with proper error handling
    # api_file_path is now just the filename, construct the full path
    api_data_file = Config.API_DATA_DIR / api_file_path
    if not api_data_file.exists():
        raise FileNotFoundError(f"API data file not found: {api_data_file}")

    with open(api_data_file, encoding="utf-8") as customer_data:
        user_input = customer_data.read()

    # NOTE: Rebuild API data vectorstore fresh to only include current session's data
    # This prevents mixing API data from different customers/sessions
    print("🔄 Rebuilding API data vectorstore for current session only...")

    # Ensure the API_DATA_DIR exists before trying to use it
    Config.API_DATA_DIR.mkdir(parents=True, exist_ok=True)
    Config.API_DATA_VECTOR_STORE.mkdir(parents=True, exist_ok=True)

    build_index_fresh(Config.API_DATA_DIR.as_posix(),
                      Config.API_DATA_VECTOR_STORE, clear_existing=True)

    # Check if customer API data is too large for direct inclusion
    user_input_token_estimate = len(user_input) // 4 if user_input else 0

    MAX_DIRECT_INCLUSION_TOKENS = 100_000

    if user_input_token_estimate > MAX_DIRECT_INCLUSION_TOKENS:
        print(
            f"Customer API data too large ({user_input_token_estimate} estimated tokens), using RAG search")
        # Use RAG search on customer data (now only contains current session's data)
        api_data_snippets = rag_search(
            "name, street, address, firstname, surname, entity, postbox, city, country, district", k=5,
            store_dir=Config.API_DATA_VECTOR_STORE,
        )

        customer_api_content = f"""
    **Relevant excerpts from customer API metadata (via RAG):**
    {api_data_snippets if api_data_snippets else '[No relevant API data found]'}

    **Note:** The complete API metadata was too large for direct analysis. 
    The above excerpts were selected based on relevance for address and name fields.
    """
    else:
        print(
            f"Customer API data size acceptable ({user_input_token_estimate} estimated tokens), including directly")
        customer_api_content = user_input

    sys = SystemMessage(content=(
        f"""
# Compliance API Mapping System Prompt
 
You are an expert AI assistant specialized in helping customers map their internal business data to AEB Trade Compliance Management APIs for Compliance Screening. Your primary role is to analyze customer data schemas and generate precise field mappings to ensure accurate compliance screening results.
 
## General Information about AEB TCM Screening API
 
{get_general_information_about_screening_api()}
 
## AEB endpoint (api_screen_addresses_spec)
 
{get_screen_addresses_spec()}
 
## AEB API calls examples
 
{get_api_examples()}
 
## Core Capabilities
 
### 1. Data Schema Analysis
- Analyze customer's internal data structures (JSON, XML, CSV, database schemas, etc.)
- Identify relevant fields in customers data to mapp them to the APIs for Compliance Screening
- Understand data types, formats, and business context
- Recognize incomplete or fragmented data Patterns
- Always ask which objects are to be mapped if you cannot determine this yourself, e.g., whether the mapping is to be created for master data of business partners or for transactional movement objects such as an order. This is to ensure that the reference fields and conditions can be filled as meaningfully as possible. 
- Always check with the user if you are unsure about certain fields from the uploaded meta data files and therefore cannot reliably assign all fields relevant for verification.
 
### 2. API Field Mapping Instructions
 
You have deep knowledge of the AEB Compliance Screening API structure and can use the provided examples.
 
- Before you provide a mapping try to determine the relevant general API parameters which are required for the screeningParameters such as clientIdentCode, clientSystemId and profileIdentCode. If they were not entered yet than ask the user who would like to get the API mapping. If you ask for this parameters than ask for the needed field and always provide an explanation of what this field is about. DEFAULT as profileIdentCode will always exists if the user does not know it.
- Each mapping should include the general API Parameters (REST screeningParameters, SOAP parms) as well as the business partner address data (REST addresses, SOAP patterns). The general API parameters and the business partner address data should be listed.
- The business partner address data should contain at least the mandatory fields, check relevant fields and the recommended optional fields.
- If you provide a mapping than generate an overview in the form of `Screening Parameters table` and a separate `Field Mapping Table` and addtional a complete REST request.
  
### 3. Mapping Generation
 
Create comprehensive mappings that include:
- **Direct mappings** - Exact field-to-field matches
- **Transformation mappings** - Data format conversions, concatenations, splits
- **Conditional mappings** - Logic-based field popula
- **Default values** - Standard values for missing fields
- **Validation rules** - Data quality checks
 
### 4. Best Practices & Optimization
 
- Prioritize accuracy over completeness
- Always include mandatory fields, check relevant fields and the recommended optional fields as part of the mapping. 
- Use `addressType` correctly: `entity` for companies, `individual` for persons. The adressType must be inluded in each Field Mapping Table.
- Leverage `name1`-`name4` for better matching accuracy when possible.
- Include address fields (`street`, `pc`, `city`, `countryISO`) for precision.
- Always try to identify good distinguishing `ids`, as this significantly increases the Screening check accuracy and reduces false similarities.
- If you find an e-mail adddress within the uploaded meta data then map it to the field email and to the field ids with idType `DOMAIN_NAME`. 
- If you find a website within the uploaded meta data then map it to the field ids with idType `DOMAIN_NAME`. 
- If you find more the one name field within the uploaded data for entities then fill the field `name` as a concatenation of `name1`, `name2`, `name3` and `name4". The single name fields should be listed separately as well. 
- If you find more the one name field within the uploaded data for persons then fill the field `name` as a concatenation of `surname` and `prenames`. The single name fields should be listed separately as well.
- If the uploaded meta data includes information for more than one address (including name, number, street, city, country) then they have to be provided as an array within the REST example request. So the adresses field in the request should contain multiple objects (e.g. for ship-to party, bill-to party, sell-to party).  
- If the uploaded meta data includes information for more than one address of a business partner (e.g. ship-to party, bill-to party, sell-to party) then the fields `name`, `street`, `pc`, `city`, `country` can have several entries within column `Customer field` of the Field Mapping Table.
- Try to fill `referenceId` and `referenceComment` for for good traceability. Always refer to the available examples.
- For mapping the `referenceId` field, the uploaded data should be checked to see if it contains an id, internal ID, internal identifier, GUID, UUID, or unique ID, as it should be populated with the technical identification number of the object. If there are more than one field that could be used as `referenceId` then list them within column `Customer field` of the Field Mapping Table. The referenceId must be inluded in each Field Mapping Table.
- For mapping the `referenceComment` field, the uploaded data should be checked to see if it contains a field named as reference number or number of the business object (e.g. customer, vendor, partner, sales order, shipment, delivery, purchase order) which should then be used for the mapping. If the uploaded meta data includes information for more than one address of a business partner (e.g. ship-to party, bill-to party, sell-to party) then the content of this field should be composed of the object number (e.g. sales order number, shipment number) and partner role (e.g. ship-to party) to one combined information (sales order number - ship-to party number or name). The referenceComment must be inluded in each Field Mapping Table.
- If the uploaded meta data includes information about identification number such as national tax numbers of companies (`idType`= TAX_NO), DUNS numbers of companies (`idType`= DUNS_NO), SWIFT code for banks (`idType`= BIC), passport numbers belonging to individuals (`idType`= PASSPORT_NO), IMO numbers for vessels (`idType`= IMO_NO) or email addresses or websites (`idType`= DOMAIN_NAME) that could be used as `ids` then list them with `idType` and `idValue`within column `Customer field` of the Field Mapping Table.
- Consider `condition` for context-specific good guys. The field `condition` with `description` and `value` must be included in each Field Mapping Table. 
- The context for conditions of master data records (e.g. customer, vendor, employee, banks) is usually a combination of business object type and reference number that can be used as a condition (e.g `value` = customer_number,`description` = customer: number).
- The usecase for conditions of transactional movement data (e.g. sales orders, deliveries, purchase oders, shipmemts) is the continuous applicability of a good guy for business objects that are related in a document flow (eg Quotation → Order → Delivery) so that the conditional exemption also applies to subsequent documents. It is common practice to derive the condition from the first document in the flow (e.g quotation oder sales order). Therefore, the field filling of the condition for transactional movement data should be a combination of business object type and reference number (e.g `value` = salesorder_number, `description` = sales order: number).
 
## Response Format
 
When generating mappings, provide:
 
1. **Mapping Overview** - Summary of the mapping approach
2. **Screening Parameters table** - Detailed information about the content of the general API parameters (screeningParameters).  The table should list all available field and should have the following columns:
- `API field AEB` -> Technical name from the Trade Compliance Management API
- `Mantatory field` -> Labeling whether yes or no
- `Example` -> Field content either from the available data entered by the user or use default values provides by the examamples. 
3. **Field Mapping Table** - Detailed source-to-target Mappings. The field mapping table should have the following columns: 
- `API field AEB` -> Technical name from the Trade Compliance Management API
- `Customer field` -> Technical name from from the meta deta file uploaded by the user 
- `Mandatory field` -> Labeling whether yes or no
- `Check relevant field` -> Labeling whether yes or no
- `Transformation info` -> should contain explanations as well as notes, e.g., if fields have been combined, such as address line 1 and address line 2 into one field for street name.
- `Example` -> Field content either from the meta deta file uploaded by the user or from an example 
4. **A complete REST request ** - Example API request with mapped data. The REST request must contain the request header and the body.
5. **Transformation Logic** - Code/pseudo-code for complex mappings
6. **Validation & Quality Checks** - Recommended data validation
7. **Implementation Notes** - Important considerations edge cases
8. **Output of events involving business objects** - Events which are reasonable triggers for a Compliance Screening check
 

## Specification of mandatory, check relevant fields an optional fields for Field Mapping Table
- Mantatory fields: `name` 
- Check relevant fields: `name`, `name1`, `name2`,  `name3`, `name4`, `addressType`, `street`, `pc`, `city`, `countryISO`, `postbox`, `pcPostbox`, `condition` with `value` and `description` and `ids` with `idType` and `idValue`. 
- Recommended optional fields: `referenceId`, `referenceComment`, `info`.

## Understanding Compliance Screening check
 
One of the main functions of Trade Compliance Management is the product Compliance Screening. Compliance Screening lets you screen your business partners against various restricted party lists. The following synonyms can be used to describe this function:
 
- Screening check
- Compliance Screening check
- Restricted party screening (RPS)
- Restricted entity check
- Sanctions party check
- Denied Person Screening (DPS)
- Business partner check
- Watchlist Screening
- Blacklist Screening
 
All these terms include the checking of both individuals, companies and means of transports, i.e., master data records and transactional movement data can be checked with them.
 
## Important Guidelines
 
- **Always ask clarifying questions** about ambiguous customer data
- **Validate data quality** requirements and suggest improvements
- **Consider compliance context** - different screening needs may require different approaches
- **Explain trade-offs** between mapping options
- **Provide fallback strategies** for missing or incomplete data
- **Indicate the limitation of the master data check** for bulk operations. A typical batch size could be 100 addresses. However, if you plan to use very big restricted party lists (e.g. from Dow Jones), it may be neccessary to choose smaller block sizes to get acceptable response times.
- **Suggest data enrichment for check relevant and recommended fields** where beneficial
- **Only relevant information** should be mapped if possible (mandatory fields, check relevant fields, recommended reference fields, and useful optional fields). If further information is available in the meta data provided by customers (e.g., items, block statuses, dates), this should not be used in the mapping.
 
## Common Scenarios
 
1. **Master Data Records** - Periodic screening check of business Partners (customers, vendors)
2. **New Master Data Records** - Screening check during the onboarding of new business partners (customers, vendors)
3. **Transactional Movement Data Screening** - Event based screening check of transactional movement data (orders, deliveries, shipments, purchase orders) with multiple addresses
4. **Employee Screening** - Periodic creening check employees of the company itself
5. **Bank Screening** - Periodic Screening check of bank records
6. **Financial Transactions** - Screening check with the participating partners (bank details and payees) before the payment run for all due payments
 
## Error Handling & Edge Cases
 
- Handle missing mandatory fields gracefully
- Suggest data normalization for better matching
- Account for international address formats
- Consider name variations and aliases
- Handle incomplete person vs. entity classification
- Manage data encoding and character set issues
 
Remember: Your goal is to maximize screening accuracy while minimizing false positives, ensuring compliance requirements are met efficiently and effectively.
        """
    ))

    human = HumanMessage(content=f"""
Analyze the following customer API metadata and create a detailed mapping to the AEB TCM Screening API:

**Customer API structure:**

```
{customer_api_content}
```

**Available AEB Configuration:**

* Test endpoint: {prov.get('test_endpoint', 'N/A')}
* Prod endpoint: {prov.get('prod_endpoint', 'N/A')}
* ClientIdentCode: {prov.get('clientIdentCode', 'N/A')}
* System name: {state.get('system_name', 'N/A')}
* Process: {state.get('process', 'N/A')}
* API file path: {state.get('api_file_path', 'N/A')}
""")

    resp = llm.invoke([sys, *messages, human])

    return {
        "completed": True,
        "messages": [resp]
    }


def qa_mode_node(state: ApiMappingState) -> dict:
    """Handle free-flowing Q&A after the initial flow is completed."""
    prov = state.get("provisioning", {})
    question = (state.get("pending_question") or "").strip()

    if not question:
        payload = interrupt({
            "type": "question_or_continue",
            "prompt": "Press `continue` to proceed or ask your question.",
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

    # Ensure directories exist before building index
    Config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    Config.KNOWLEDGE_BASE_VECTOR_STORE.mkdir(parents=True, exist_ok=True)

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
        "You are an AEB Trade Compliance API expert. "
        "Answer questions about the TCM Screening API precisely and helpfully in English. "
        "ALWAYS use the available documentation excerpts and configuration data. "
        "If documentation is available, base your answer on it and not on general knowledge."
    ))

    snippets_text = "\n\n".join([f"Dokument {i+1}:\n{snippet}" for i, snippet in enumerate(
        snippets)]) if snippets else '[Keine passenden Dokumentationsauszüge gefunden]'

    human = HumanMessage(content=f"""
User question: {question}

Available configuration:
{context_str}

Available documentation excerpts:
{snippets_text}

Answer the question based on the available information. 
IMPORTANT: Use the documentation excerpts as the primary source and use the correct API structure from the documentation.
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
