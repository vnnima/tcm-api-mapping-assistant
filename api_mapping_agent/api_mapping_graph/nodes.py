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
    prov = state.get("provisioning", {})

    # Prepare welcome messages container (may be used when returning from QA)
    welcome_msgs = []

    # If there's an explicit resume flag for ask_endpoints, handle it immediately
    def _handle_endpoints_payload(endpoints_payload, welcome_msgs=None):
        """Process a payload returned from an `ask_endpoints` interrupt.

        Returns a state-delta dict if the payload contains data to consume, or
        None to indicate the interrupt should be shown (no consumption).
        """
        if not isinstance(endpoints_payload, dict):
            return None

        # Structured fields
        if "test_url" in endpoints_payload or "prod_url" in endpoints_payload:
            test_url = str(endpoints_payload.get("test_url", "")).strip()
            prod_url = str(endpoints_payload.get("prod_url", "")).strip()
            found_endpoints = {}
            if test_url:
                found_endpoints["test_endpoint"] = test_url
            if prod_url:
                found_endpoints["prod_endpoint"] = prod_url

            if found_endpoints:
                return {
                    "provisioning": found_endpoints,
                    "decision": None,
                    "started": False,
                    "resume_after_qa": None,
                    "messages": [AIMessage(content="Thank you! Endpoints recorded:\n" + "\n".join(format_endpoints_message(found_endpoints)))]
                }

        # Free-text endpoints
        if "endpoints" in endpoints_payload:
            endpoints_text = str(endpoints_payload["endpoints"]).strip()
            found_endpoints = parse_endpoints(endpoints_text)
            if found_endpoints:
                return {
                    "provisioning": found_endpoints,
                    "decision": None,
                    "started": False,
                    "resume_after_qa": None,
                    "messages": [AIMessage(content="Thank you! Endpoints recorded:\n" + "\n".join(format_endpoints_message(found_endpoints)))]
                }

        # Direct question from the ask_endpoints UI
        if "question" in endpoints_payload and endpoints_payload["question"]:
            question = str(endpoints_payload["question"]).strip()
            return {
                "pending_question": question,
                "decision": "qa",
                "next_node_after_qa": NodeNames.INTRO,
                "resume_after_qa": "ask_endpoints",
                "messages": [HumanMessage(content=question)]
            }

        # Skip/default
        if "response" in endpoints_payload:
            response = str(endpoints_payload.get(
                "response", "")).strip().lower()
            if response in {"skip", "no", "false", "0"}:
                return {
                    "provisioning": {"test_endpoint": "https://default-test.aeb.com", "prod_endpoint": "https://default-prod.aeb.com"},
                    "decision": None,
                    "started": False,
                    "resume_after_qa": None,
                    "messages": [AIMessage(content="Using default endpoints. You can update these later if needed.")]
                }

        return None

    # Debug: log incoming resume flag and provisioning briefly
    try:
        print(
            f"DEBUG intro_node ENTRY: decision={state.get('decision')} resume_after_qa={state.get('resume_after_qa')} provisioning_keys={list(state.get('provisioning', {}).keys())}")
    except Exception:
        pass

    # If we're returning from QA and need to resume a specific interrupt, handle that first
    if not has_endpoint_information(prov) and state.get("decision") in ["qa", "continue"]:
        if state.get("resume_after_qa") == "ask_endpoints":
            endpoints_payload = interrupt({
                "type": "ask_endpoints",
                "title": "Step 1: AEB RZ Endpoints",
                "prompt": "We start with step 1. To establish an API connection to Trade Compliance Management, you will need the endpoints for the test and production environments from your AEB contact person. Please log in to https://my.aeb.com/home/ and open the Trade Compliance Management tile in the \"My products\" and \"My test systems\" section. The URLs will be displayed in your browser. Please enter these in the input mask to proceed to the next step. If you don't know the endpoint right now, you can skip that step and we continue with default settings.",
            })

            out = _handle_endpoints_payload(endpoints_payload)
            if out is not None:
                return out

            # Show endpoint prompt
            return {
                "started": True,
                "decision": None,
                "resume_after_qa": None,
                "messages": [AIMessage(content=(
                    """
We start with step 1. To establish an API connection to Trade Compliance Management, you will need the **endpoints for the test and production environments** from your AEB contact person. Please log in to [AEB Home](https://my.aeb.com/home/) and open the Trade Compliance Management tile in the "My products" and "My test systems" section. The URLs will be displayed in your browser. **Please enter these in the input mask to proceed to the next step.**

If you don't know the endpoint right now, you can skip that step and we continue with default settings.
"""
                ))]
            }

    # Only trigger the start interrupt on the very first run (no messages at all)
    if not messages:
        welcome_msgs = [AIMessage(content=(
            "Welcome to the **API Mapping Assistant**. This assistant guides you step by step through all the relevant steps required to technically connect your partner or host system to Compliance Screening via an API.\n\n"
            "Please press Start to begin; all configuration inputs will be collected via the form controls that appear next."))]

        payload = interrupt({
            "type": "start_or_question",
            "prompt": "Press 'Start' to begin the integration process.",
        })

        # If the interrupt was consumed (resume), and user chose Start, show the endpoints interrupt
        if isinstance(payload, dict) and (payload.get("decision") == "start" or payload.get("start") is True or str(payload.get("start", "")).lower() in {"true", "1", "yes", "start"}):
            endpoints_payload = interrupt({
                "type": "ask_endpoints",
                "title": "Step 1: AEB RZ Endpoints",
                "prompt": "We start with step 1. To establish an API connection to Trade Compliance Management, you will need the endpoints for the test and production environments from your AEB contact person. Please log in to https://my.aeb.com/home/ and open the Trade Compliance Management tile in the \"My products\" and \"My test systems\" section. The URLs will be displayed in your browser. Please enter these in the input mask to proceed to the next step. If you don't know the endpoint right now, you can skip that step and we continue with default settings.",
            })

            out = _handle_endpoints_payload(endpoints_payload, welcome_msgs)
            if out is not None:
                return out

            # Show the endpoint prompt (started) if nothing consumed
            return {"started": True, "messages": welcome_msgs + [AIMessage(content=(
                "Great! Let's get started with the integration.\n\n"
                "Please enter the Test and Production endpoint URLs in the form shown."))]}

    # Check if we're returning from QA mode and still need endpoints
    if not has_endpoint_information(prov) and state.get("decision") in ["qa", "continue"]:
        # If QA asked while the endpoints prompt was active, re-show the endpoints interrupt
        if state.get("resume_after_qa") == "ask_endpoints":
            # Clear the resume flag so it doesn't persist
            resume_flag = state.get("resume_after_qa")
            endpoints_payload = interrupt({
                "type": "ask_endpoints",
                "title": "Step 1: AEB RZ Endpoints",
                "prompt": "We start with step 1. To establish an API connection to Trade Compliance Management, you will need the endpoints for the test and production environments from your AEB contact person. Please log in to https://my.aeb.com/home/ and open the Trade Compliance Management tile in the \"My products\" and \"My test systems\" section. The URLs will be displayed in your browser. Please enter these in the input mask to proceed to the next step. If you don't know the endpoint right now, you can skip that step and we continue with default settings.",
            })

            if isinstance(endpoints_payload, dict):
                # Remove the resume flag from state on consumption
                out = {}
                # Check if user asked a question
                if "question" in endpoints_payload and endpoints_payload["question"]:
                    question = str(endpoints_payload["question"]).strip()
                    return {
                        "pending_question": question,
                        "decision": "qa",
                        "next_node_after_qa": NodeNames.INTRO,
                        "resume_after_qa": "ask_endpoints",
                        "messages": [HumanMessage(content=question)]
                    }
                # Check if user wants to skip
                elif "response" in endpoints_payload:
                    response = str(endpoints_payload.get(
                        "response", "")).strip().lower()
                    if response in {"skip", "no", "false", "0"}:
                        # Use default endpoints
                        return {
                            "provisioning": {"test_endpoint": "https://default-test.aeb.com", "prod_endpoint": "https://default-prod.aeb.com"},
                            "decision": None,  # Clear decision
                            "started": False,
                            "resume_after_qa": None,
                            "messages": [
                                AIMessage(
                                    content="Using default endpoints. You can update these later if needed.")
                            ]
                        }
                # If user provided endpoint data directly
                elif "endpoints" in endpoints_payload:
                    endpoints_text = str(
                        endpoints_payload["endpoints"]).strip()
                    found_endpoints = parse_endpoints(endpoints_text)
                    if found_endpoints:
                        return {
                            "provisioning": found_endpoints,
                            "decision": None,  # Clear decision
                            "started": False,
                            "resume_after_qa": None,
                            "messages": [
                                AIMessage(content="Thank you! Endpoints recorded:\n" +
                                          "\n".join(format_endpoints_message(found_endpoints)))
                            ]
                        }

            # If we get here, show the endpoint prompt with started flag
            return {
                "started": True,
                "decision": None,  # Clear decision
                "resume_after_qa": None,
                "messages": [AIMessage(content=(
                    """
We start with step 1. To establish an API connection to Trade Compliance Management, you will need the **endpoints for the test and production environments** from your AEB contact person. Please log in to [AEB Home](https://my.aeb.com/home/) and open the Trade Compliance Management tile in the "My products" and "My test systems" section. The URLs will be displayed in your browser. **Please enter these in the input mask to proceed to the next step.**

If you don't know the endpoint right now, you can skip that step and we continue with default settings.
"""))]
            }

        # First, re-show the welcome/start interrupt so the user can Start or ask another question
        start_payload = interrupt({
            "type": "start_or_question",
            "prompt": "Press 'Start' to begin the integration process or type a question below.",
        })

        if isinstance(start_payload, dict):
            # If user chose to start, proceed to the endpoints interrupt (same flow as initial start)
            if start_payload.get("decision") == "start" or start_payload.get("start") is True or str(start_payload.get("start", "")).lower() in {"true", "1", "yes", "start"}:
                endpoints_payload = interrupt({
                    "type": "ask_endpoints",
                    "title": "Step 1: AEB RZ Endpoints",
                    "prompt": "Please provide the AEB RZ Endpoints.",
                })

                if isinstance(endpoints_payload, dict):
                    # Check if user asked a question
                    if "question" in endpoints_payload and endpoints_payload["question"]:
                        question = str(endpoints_payload["question"]).strip()
                        return {
                            "pending_question": question,
                            "decision": "qa",
                            "next_node_after_qa": NodeNames.INTRO,
                            "messages": [HumanMessage(content=question)]
                        }
                    # If user provided test_url and prod_url
                    elif "test_url" in endpoints_payload or "prod_url" in endpoints_payload:
                        test_url = str(endpoints_payload.get(
                            "test_url", "")).strip()
                        prod_url = str(endpoints_payload.get(
                            "prod_url", "")).strip()

                        found_endpoints = {}
                        if test_url:
                            found_endpoints["test_endpoint"] = test_url
                        if prod_url:
                            found_endpoints["prod_endpoint"] = prod_url

                        if found_endpoints:
                            return {
                                "provisioning": found_endpoints,
                                "started": False,
                                "messages": [welcome_msgs[0] if welcome_msgs else AIMessage(content=""), AIMessage(content="Thank you! Endpoints recorded:\n" + "\n".join(format_endpoints_message(found_endpoints)))]
                            }

                # If we get here, show the endpoint prompt with started flag
                return {
                    "started": True,
                    "messages": welcome_msgs + [
                        AIMessage(content=(
                            """
We start with step 1. To establish an API connection to Trade Compliance Management, you will need the **endpoints for the test and production environments** from your AEB contact person. Please log in to [AEB Home](https://my.aeb.com/home/) and open the Trade Compliance Management tile in the "My products" and "My test systems" section. The URLs will be displayed in your browser. **Please enter these in the input mask to proceed to the next step.**

If you don't know the endpoint right now, you can skip that step and we continue with default settings.
"""))
                    ]
                }

            # If user asked another question at the start prompt -> go to QA
            elif start_payload.get("decision") == "qa" and "question" in start_payload:
                question = str(start_payload["question"]).strip()
                return {
                    "pending_question": question,
                    "decision": "qa",
                    "next_node_after_qa": NodeNames.INTRO,
                    "messages": welcome_msgs + [HumanMessage(content=question)]
                }
            elif "question" in start_payload:
                # Legacy support
                question = str(start_payload["question"]).strip()
                return {
                    "pending_question": question,
                    "decision": "qa",
                    "next_node_after_qa": NodeNames.INTRO,
                    "messages": welcome_msgs + [HumanMessage(content=question)]
                }

        else:
            raise ValueError(
                f"Unexpected interrupt payload type: {type(start_payload)}")

    # If we previously showed the endpoints prompt (started=True), collect
    # the structured endpoint input via the interrupt UI and process it.
    if not has_endpoint_information(prov):
        if state.get("started"):
            endpoints_payload = interrupt({
                "type": "ask_endpoints",
                "title": "Step 1: AEB RZ Endpoints",
                "prompt": "We start with step 1. To establish an API connection to Trade Compliance Management, you will need the endpoints for the test and production environments from your AEB contact person. Please log in to https://my.aeb.com/home/ and open the Trade Compliance Management tile in the \"My products\" and \"My test systems\" section. The URLs will be displayed in your browser. Please enter these in the input mask to proceed to the next step. If you don't know the endpoint right now, you can skip that step and we continue with default settings.",
            })

            out = _handle_endpoints_payload(endpoints_payload)
            if out is not None:
                return out

            # Still waiting for valid endpoint input -> keep started flag
            return {"started": True}

        # No started flag and no endpoints -> nothing to do here
        return {}


def route_from_intro(state: ApiMappingState) -> str:
    """Route from intro based on user response and current state."""

    # TODO: Can remove this when I implement the looping in qa_mode with interrupt
    if state.get("completed", False):
        return NodeNames.PROCESS_AND_MAP_API

    messages = state.get("messages", [])
    user_input = get_last_user_message(messages)
    prov = state.get("provisioning", {})

    # If we just showed the endpoint prompt (started=True), end turn to wait for user input
    if state.get("started") and not has_endpoint_information(prov):
        return END

    # If user chose to ask a question (decision set by intro_node interrupt)
    if state.get("decision") == "qa":
        return NodeNames.QA_MODE

    # If returning from QA mode with 'continue' decision and no endpoints, route back to INTRO
    if state.get("decision") == "continue" and not has_endpoint_information(prov):
        return END

    # Check if we have endpoint information - if yes, proceed even without new user input
    # (endpoints might have been provided via interrupt)
    if has_endpoint_information(prov):
        if not prov.get("clientIdentCode"):
            return NodeNames.ASK_CLIENT
        if "wsm_user_configured" not in prov:
            return NodeNames.ASK_WSM
        # All good -> guide
        return NodeNames.GENERAL_SCREENING_INFO

    # No endpoints and no user input
    if not user_input:
        return END

    # We have user input but no endpoints yet - try to clarify
    return NodeNames.CLARIFY


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
    prov = state.get("provisioning", {})

    # Use interrupt to allow skip/question
    payload = interrupt({
        "type": "ask_client",
        "title": "Step 2: Client Name (clientIdentCode)",
        "prompt": "We start with step 2. In each API call, a **client (technical field name clientIdentCode)** must be transferred in the `screeningParameters`. The client is displayed in the 'Trade Compliance Management' tiles. **Please enter this client now in the input mask to proceed to the next step**.\n\nIf you don't know the client right now, you can skip that step and we continue with default settings.",
    })

    skip_client = None  # None means proceed with data, True means use default, False means loop
    messages_to_add = []

    if isinstance(payload, dict):
        # Check if user asked a question
        if "question" in payload and payload["question"]:
            question = str(payload["question"]).strip()

            # Use RAG for answering
            Config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            Config.KNOWLEDGE_BASE_VECTOR_STORE.mkdir(
                parents=True, exist_ok=True)
            ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(
            ), Config.KNOWLEDGE_BASE_VECTOR_STORE)

            snippets = rag_search(
                f"Question about Screening API: {question}", k=5)
            snippets_text = "\n\n".join([f"Document {i+1}:\n{snippet}" for i, snippet in enumerate(
                snippets)]) if snippets else '[No relevant documentation excerpts found]'

            sys = SystemMessage(content=(
                "You are an AEB Trade Compliance API expert. "
                "Answer questions about the TCM Screening API precisely and helpfully in English. "
                "ALWAYS use the available documentation excerpts."
            ))

            human = HumanMessage(
                content=f"User question: {question}\n\nDocumentation:\n{snippets_text}")
            resp = llm.invoke([sys, human])

            messages_to_add.append(HumanMessage(content=question))
            messages_to_add.append(resp)
            # Loop back to ask again
            skip_client = False

        # Check if user wants to skip
        elif "response" in payload:
            response = str(payload.get("response", "")).strip().lower()
            if response in {"skip", "no", "false", "0", "default"}:
                prov["clientIdentCode"] = "APITEST"
                messages_to_add.append(
                    AIMessage(content="Using default clientIdentCode: APITEST")
                )
                skip_client = True

        # If user provided client code directly
        elif "client_code" in payload:
            client_code = str(payload["client_code"]).strip()
            if client_code:
                prov["clientIdentCode"] = client_code
                messages_to_add.append(
                    AIMessage(
                        content=f"Thank you! Client recorded: clientIdentCode={client_code}")
                )
                skip_client = None  # Proceed with the data

    return {"skip_client": skip_client, "provisioning": prov, "messages": messages_to_add}


def route_from_client(state: ApiMappingState) -> str:
    """Route from client based on current provisioning state."""
    prov = state.get("provisioning", {})
    skip_client = state.get("skip_client")

    # If a question was answered, loop back to show the interrupt again
    if skip_client is False:
        return NodeNames.ASK_CLIENT

    # If we have client code (even without new user input), proceed to next step
    if prov.get("clientIdentCode"):
        return NodeNames.ASK_WSM

    # No client code
    return END


def ask_wsm_node(state: ApiMappingState) -> dict:
    prov = state.get("provisioning", {})

    # Use interrupt to allow skip/question (tri-state handling)
    payload = interrupt({
        "type": "ask_wsm",
        "title": "Step 3: WSM User for Authentication",
        "prompt": "We start with step 3. Depending on the technology (REST or SOAP) different authentication methods could be used:\n - HTTP Basic Authentication: This can be used with REST and SOAP and requires authentication data to be provided with each call.\n - Token Authentication: This can only be used with REST and requires an additional call to request a token, that can then be used for subsequent calls for a limited time. \nYou can find further technical documentation about setting up the authentication here: https://trade-compliance.docs.developers.aeb.com/docs/setting-up-your-environment-1#token-authentication \n\nBoth methods require a **technical user ID and password** that must be provided by AEB. **Did you have this access credentials?**\n\n If you don't have it yet, we can continue without it and go to the next step.",
    })

    skip_wsm = None  # None means proceed with data, True means set default/no, False means loop
    messages_to_add = []

    if isinstance(payload, dict):
        # Check if user asked a question
        if "question" in payload and payload["question"]:
            question = str(payload["question"]).strip()

            # Use RAG for answering
            Config.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
            Config.KNOWLEDGE_BASE_VECTOR_STORE.mkdir(
                parents=True, exist_ok=True)
            ensure_index_built(Config.KNOWLEDGE_BASE_DIR.as_posix(),
                               Config.KNOWLEDGE_BASE_VECTOR_STORE)

            snippets = rag_search(
                f"Question about Screening API: {question}", k=5)
            snippets_text = "\n\n".join([f"Document {i+1}:\n{snippet}" for i, snippet in enumerate(
                snippets)]) if snippets else '[No relevant documentation excerpts found]'

            sys = SystemMessage(content=(
                "You are an AEB Trade Compliance API expert. "
                "Answer questions about the TCM Screening API precisely and helpfully in English. "
                "ALWAYS use the available documentation excerpts."
            ))

            human = HumanMessage(
                content=f"User question: {question}\n\nDocumentation:\n{snippets_text}")
            resp = llm.invoke([sys, human])

            messages_to_add.append(HumanMessage(content=question))
            messages_to_add.append(resp)
            # Loop back to ask again
            skip_wsm = False

        # Check if user wants to skip or provided response
        elif "response" in payload:
            response = str(payload.get("response", "")).strip().lower()
            if response in {"skip", "no", "false", "0"}:
                prov["wsm_user_configured"] = False
                messages_to_add.append(
                    AIMessage(
                        content="No worries! You can set up the WSM user later. WSM user available: No")
                )
                skip_wsm = True
            elif response in {"yes", "true", "1"}:
                prov["wsm_user_configured"] = True
                messages_to_add.append(
                    AIMessage(content="Great! WSM user available: Yes")
                )
                skip_wsm = None

    return {"skip_wsm": skip_wsm, "provisioning": prov, "messages": messages_to_add}


def route_from_wsm(state: ApiMappingState) -> str:
    """Route from WSM based on current provisioning state."""
    prov = state.get("provisioning", {})
    skip_wsm = state.get("skip_wsm")

    # If a question was answered, loop back to show the interrupt again
    if skip_wsm is False:
        return NodeNames.ASK_WSM

    # If we have a definitive wsm config, proceed
    if prov.get("wsm_user_configured") is not None:
        return NodeNames.ASK_GENERAL_INFO

    # Otherwise wait for user input
    return END


def ask_general_info_node(state: ApiMappingState) -> dict:
    """Ask user if they want to see general screening information."""
    payload = interrupt({
        "type": "show_general_info",
        "title": "Step 4: Initial Integration Guide for Sanctions List Screening",
        "prompt": "We start with step 4. Before starting to develop the API, there is helpful general information about the **supported interface architectures, objects relevant for screening**, and the grouping of **name and address fields**, whether they are required or optional.\n\n**Would you like to see this information?**",
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
#### 1. Supported interface architectures
- JSON/REST
- XML/SOAP
#### 2. Trade Compliance relevant business objects
- Business partner master data records: Individual screening or bulk check of customers and vendors (max. 100 entries per request).
- Transactional movement data: Orders, deliveries, purchase documents, shipments with multiple addresses´.
- Employees: Individual screening or bulk check.
-Bank accounts: Individual screening or bulk check.
- Financial and payment transactions: Individual screening or bulk check with multiple addresses.
#### 3. Common triggers and processes that could initiate a screening check
- Online check:  creation or change of a master data record or other relevant business objects (in terms of name or address fields. Business objects are checked whenever they are actively used in business processes. This allows processes to be designed to ensure consistent compliance without the need to recheck all master data records daily.
- Batch checks: Periodic monitoring of master data records. The Batch check can be used to determine whether a previously checked partner has since been relisted – even if it hasn't been changed or used for a while. This prevents critical matches from only becoming apparent during the usage in business processes.
- Milestone checks: In addition to change-based checks, the system performs milestone-based screening at defined process checkpoints. Each milestone acts as a screening checkpoint within the transaction lifecycle, such as before inventory reservation, picking, customs declaration, or goods issue.
- Manual check: A user can manually initiate a check from a partner system, e.g., to correct a previous incorrect check.

Our recommendation:
- The online check should generally be implemented for all compliance-relevant business objects.
- For logistics and transactional movement data, we recommend at least one check before goods are dispatched.
- Regular batch checks are particularly useful if a huge number of master data records exists or if there are rarely used in movement data.
#### 4. Specification of mandatory, check relevant and optional fields
- mandatory fields: name
- check relevant fields: name, name1, name2, name3, name4, addressType, street, pc, city, countryISO, postbox, pcPostbox, condition and ids
- recommended optional fields: referenceId, referenceComment, info
"""

    return {
        "messages": [AIMessage(content=response_content)],
    }


def ask_screening_variants_node(state: ApiMappingState) -> dict:
    """Ask user if they want to see screening variants explanation."""
    payload = interrupt({
        "type": "show_screening_variants",
        "title": "Step 5: Recommended Options for API Usage",
        "prompt": "We start with step 5. The Compliance Screening API can be integrated into the processes of a partner system in **three different scenarios**.\n\n**Would you like to see this information?**",
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


# 1. One-way transfer without rechecks
In the first option, data is transferred from a partner system to Trade Compliance Management on a one-way basis only. The API request can contain certain relevant business partners(customers, suppliers, employees, etc.) or transactional data(e.g., orders with multiple business partners). The data set should include the name, address information, a unique reference, IDs, conditions, and the address type.

A business partner check is then performed and logged in TCM. The result of the check can be a match or non-match, which is reported directly in the API Response message. If necessary, the object can be blocked or stopped in the partner system or a notification can be displayed directly to a user if a potential match is detected("matchFound": true, "wasGoodGuy": false).
In the event of a match, an email is also sent to an email recipient configured in TCM(company's compliance officer), who then processes the matches in TCM (defines a good guy for false positives or marks them as true matches). This procedure only requires the REST API screenAddresses (or SOAP API RexBF-batchMatch) that must be called once per business object (master data record or transactional data). The object must be released in the partner system or finally stopped or deleted manually by a user after the match handling in Trade Compliance Management.

#### 2. Transfer with response evaluation and periodic rechecks
In the second variant, data is transferred from the partner system and, in addition, open matches are regularly checked so that they can not only be blocked but also unblocked in the partner system. The API request can contain certain relevant business partners (customers, suppliers, employees, etc.) or transactional data (e.g., orders with multiple business partners). The data set should include the name, address information, a unique reference, IDs, conditions, and the address type.

A business partner check is then performed, which is logged in TCM. The result of the check can be a match or a non-match, which is reported directly in the response. If necessary, the object can be blocked or stopped in the partner system or a notification can be displayed directly to a user if a potential match is detected ("matchFound": true, "wasGoodGuy": false).

In the event of a match, an email is also sent to an email recipient configured in TCM (company's compliance officer), who then processes the matches in Trade Compliance Management (defines a good guy for false positives or marks them as true matches). This procedure requires the REST API screenAddresses (or SOAP API RexBF-batchMatch) that have to be used several times.
- First, the initial check must be performed.
- For business objects that received a match during the initial check ("matchFound": true, "wasGoodGuy": false), a periodic recheck must be performed so that a subsequent noncritical check result can be determined in the partner system after the match processing in TCM.
- This recheck must be done until the check result gets uncritical ("matchFound": false, "wasGoodGuy": true).
This enables an automatic unblocking of the business object in the partner system after the good guy definition. The partner system must save the critical check results for address matches. The suggested frequency for the recheck is every 60 minutes. In addition, the parameter suppressLogging of the REST API screenAddresses (or SOAP API RexBF-batchMatch) should be sent with the value true for periodic rechecks so that the periodic checks are not counted in addition to the invoiceable check volume.

#### 3. Transfer with direct access to match handling from partner system
The third option can be implemented as a supplement to the first or second variant. After a compliance screening check of a business objects with the REST API screenAddresses (or SOAP API RexBF-batchMatch), the response can be evaluated in the partner system if there are potential matches ("matchFound": true, "wasGoodGuy": false). This use case assumes that a user accesses the match handling directly from the partner system. In the partner system, the user should not only be shown the match, but there should also be a button or menu function to call up the match handling in Trade Compliance Management. 

There are two ways to embed the match handling UI of Trade Compliance Management so that users can open it from partner systems:

The first option is to open the match handling UI for a specific address match if users want to access a specific business object in order to process or define the Good Guy just for this one address.  Therefore the screeningLogEntry API can be used to generate and open a web link to the match handling UI for one specific address match. Since the web link is only valid temporarily, the API should only be called when the user wants to start the match handling by clicking on the function introduced in the partner system.

The second option is to open the match handling UI which displays an overview of all open matches (worklist). This integration is ideal for making a central function or tile available to users in the partner system. Two APIs are available for integrating the match handling overview. The countMatchHandlingMatches API can be used to determine the number of open matches. Therefore, the API should be called periodically (e.g., once per minute). This allows the partner system to display whether and how many open matches need to be processed. In addition, the matchHandlingView API can then be used to open the match handling overview, which displays all open matches from the last compliance screening checks.  That API API can be used to generate and open a web link to the access the match handling UI. Since the web link is only valid temporarily, the matchHandlingView API should only be called when the user wants to start the match handling by clicking on the function introduced in the partner system. Both APIs (countMatchHandlingMatches and matchHandlingView) supports transmitting a stored view as parameter. Individual views can be configured in the match handling UI before the API is used (e.g., if a separation of address matches and good guy alert events is preferred or if specific compliance profiles or organizational units shall be enabled).

Our recommendation: 
#### For Simple Implementations choose variant 1 if you have:
- Basic compliance requirements
- Limited development resources
- Low transaction volumes
- Acceptable manual compliance workflow
#### For Automated workflows choose variant 2 if you have:
- High compliance requirements for seamless process integration, including blocking and unblocking behavior of business objects
- High transaction volumes
- Need for automated unblocking
- Dedicated compliance team
- Advanced integration capabilities
#### For optimal User Experience add variant 3 to either variant 1 or 2 if you want:
- Useful if compliance match processing is performed by the same user who is also responsible for the business object in the partner system (e.g., creator of a sales order)
- Seamless user experience in the partner system
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
        "title": "Step 6: Response Scenarios Explanation",
        "prompt": "We start with step 6. The response messages from the Compliance Screening API differ depending on whether the check result has identified a potential match or an uncritical check result.\n\n**Would you like to see an explanation of the detailed response scenarios?**",
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

The following response message describes the scenario where a potential address match has been detected. A match handling in Trade Compliance Management is required and the object in the partner system should be blocked. The check will be logged in Trade Compliance Management for further audit purposes. If process blocks are used, users should be able to see the compliance status (critical/non-critical) of the business objects in the partner system. You can configure an email distribution list in Trade Compliance Management to notify a compliance officer:

```json
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "VEN_4714",
    "referenceComment": "Vendor 4714"
  }
```

#### Scenario 2: No match found (uncritical check result)

The following scenario detects an uncritical address where no further action in Trade Compliance Management is required. The check will be logged for further audit purposes. The business object in the partner system can be further processed and used (no stop required):

```json
  {
    "matchFound": false,
    "wasGoodGuy": false,
    "referenceId": "VEN_4715",
    "referenceComment": "Vendor 4715"
  }
```

#### Scenario 3: No match due to good guy definition

The third scenario detects an uncritical address due to a previous good guy definition in Trade Compliance Management. The check will be logged for further audit purposes. The business object in the partner system can be further processed and used:

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
We can now start with step 7. This step will help you to map your existing object model onto the AEB TCM Compliance Screening API. After uploading the metadata for the business object to be checked from your partner system, the assistant can perform a mapping to the AEB API, creating a mapping table including transformation logic and implementation notes, as well as a complete REST call.
### What we need to start the mapping:
#### 1. Context Information
Please describe:

Partner System (name or type): Which system do you want to connect (e.g. SAP, Salesforce, Custom ERP)?  Relevant Business object:Which business objects you want to check (e.g. business partner master data records, bank accounts, orders, deliveries, Bank accounts)  Business process: Which business process should be integrated? (e.g. Online check, batch check)

#### 2. Business Object Metadata

You could upload your existing object model in one of the following formats:
- JSON Schema of your address/partner data
- XML Example of a typical data request
- CSV Structure with field names and descriptions
- OpenAPI/Swagger definition

Example format:
```json
{
    "id": "GUID",
    "number": "string",
    "customerName": "string",
    "addressLine": "string",
    "city": "string",
    "country": "string",
    "phoneNumber": "string",
    "email": "string"
}
```

Next Step: Please first **provide** your partner system name, business object** and the **process to be integrated**. You can then **upload a file** containing your metadata and start the mapping request by clicking the **Perform mapping with uploaded data button.**
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

    # Check if customer API data is too large for direct inclusion
    user_input_token_estimate = len(user_input) // 4 if user_input else 0
    MAX_DIRECT_INCLUSION_TOKENS = 100_000

    # Only build vectorstore if we need RAG (file is large)
    if user_input_token_estimate > MAX_DIRECT_INCLUSION_TOKENS:
        print(
            f"Customer API data too large ({user_input_token_estimate} estimated tokens), using RAG search")
        print("🔄 Building vectorstore for RAG search...")

        # Ensure directories exist
        Config.API_DATA_DIR.mkdir(parents=True, exist_ok=True)
        Config.API_DATA_VECTOR_STORE.mkdir(parents=True, exist_ok=True)

        # Build vectorstore fresh to only include current session's data
        build_index_fresh(Config.API_DATA_DIR.as_posix(),
                          Config.API_DATA_VECTOR_STORE, clear_existing=True)

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
4. **A complete REST request **
- Example API request with mapped data. The REST request must contain the request header and the body.
- You must also write a example request with a cURL syntax like this, where the headers and the links are included:
```bash
curl --request POST \
     --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses \
     --header 'X-XNSG_WEB_TOKEN: YOUR_TOKEN' \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --data '
```
where you use the test-endpoint provided by the user as URL (Test endpoint: {prov.get('test_endpoint', 'N/A')})

5. **Transformation Logic** - Code/pseudo-code for complex mappings
6. **Validation & Quality Checks** - Recommended data validation
7. **Implementation Notes** - Important considerations edge cases
8. **Output of events involving business objects** - Events which are reasonable triggers for a Compliance Screening check


## Specification of mandatory, check relevant fields an optional fields for Field Mapping Table
- Mantatory fields:
    - `name` -> ONLY the name field is mandatory.
- Check relevant fields:
- `name` -> is check relevant AND mandatory
- `name1` -> is check relevant
- `name2` -> is check relevant
- `name3` -> is check relevant
- `name4` -> is check relevant
- `addressType` -> is check relevant
- `street` -> is check relevant
- `pc` -> is check relevant
- `city` -> is check relevant
- `countryISO` -> is check relevant
- `postbox` -> is check relevant
- `pcPostbox` -> is check relevant
- `condition` with `value` -> is check relevant
- `description` and `ids` with `idType` and `idValue` -> are check relevant
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

    # Debug: log incoming QA state
    try:
        print(
            f"DEBUG qa_mode_node ENTRY: pending_question={state.get('pending_question')} next_node_after_qa={state.get('next_node_after_qa')} resume_after_qa={state.get('resume_after_qa')}")
    except Exception:
        pass

    # Determine where to go after QA if not already set
    if not state.get("next_node_after_qa"):
        if not has_endpoint_information(prov):
            next_node = NodeNames.INTRO
        else:
            next_node = NodeNames.ASK_GENERAL_INFO
    else:
        next_node = state.get("next_node_after_qa")

    if not question:
        payload = interrupt({
            "type": "question_or_continue",
            "prompt": "Press `continue` to proceed with the guide or ask another question.",
        })
        if isinstance(payload, dict):
            if payload.get("continue") is True or str(payload.get("continue")).lower() in {"true", "1", "yes"}:
                return {
                    "decision": "continue",
                    "next_node_after_qa": next_node,
                    "pending_question": "",
                    "resume_after_qa": state.get("resume_after_qa"),
                }
            elif "question" in payload:
                decision = "qa"
                question = str(payload["question"]).strip()
        else:
            raise ValueError(
                f"Unexpected interrupt payload type: {type(payload)}")

    # If still no question stay here
    if not question:
        return {
            "decision": "qa",
            "next_node_after_qa": next_node,
            "resume_after_qa": state.get("resume_after_qa"),
        }

    # Check for debug commands
    if question.lower().strip() in ["debug", "debug rag", "debug vectorstore"]:
        debug_knowledge_base_files(Config.KNOWLEDGE_BASE_DIR.as_posix())
        debug_vectorstore_contents(Config.KNOWLEDGE_BASE_VECTOR_STORE)
        return {
            "messages": [AIMessage(content="Debug information has been printed to the console. Check the server logs for detailed RAG system status.")],
            "decision": "qa",
            "pending_question": "",
            "resume_after_qa": state.get("resume_after_qa"),
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

    # Preserve any resume flag so the next node can restore the proper
    # interrupt (for example, the ask_endpoints interrupt).
    return {
        "messages": [resp],
        "decision": "continue",
        "pending_question": "",
        "next_node_after_qa": next_node,
        "resume_after_qa": state.get("resume_after_qa"),
    }


def route_from_qa_mode(state: ApiMappingState, config: RunnableConfig) -> str:
    decision = state.get("decision")
    if decision == "continue":
        return state.get("next_node_after_qa")
    return NodeNames.QA_MODE                                                                
