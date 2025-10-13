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
from agent.rag import rag_search, build_index, ensure_index_built, debug_vectorstore_contents, debug_knowledge_base_files, build_index_fresh
from .utils import get_screen_addresses_spec, get_general_information_about_screening_api


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
                    "Hello! I'm your **AEB API Mapping Assistant**. "
                    "I help you cleanly integrate the **TCM Screening API** into your system.\n\n"
                    "Would you like to start with the integration? (Yes/No)"
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
                    "All right! If you need help with the TCM Screening API integration later, I'm happy to assist. "
                    "Good luck!"
                ))
            ]
        }
    else:
        return {
            "started": True,
            "messages": [
                AIMessage(content=(
                    "Great! Let's start with the TCM Screening API integration. "
                    "First, I need some information from you.\n\n"
                ))
            ]
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
        messages) or "Would you like to start with the API mapping integration? (Yes/No)"
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

Analyze the response and explain kindly:
1. What the problem with the answer is
2. How they should answer correctly (with concrete examples)
3. Then ask the question again

Keep it brief, helpful and friendly.
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
                    "Please first provide the **AEB RZ Endpoints** (at least one URL). "
                    "These are required for API integration.\n"
                    f"Note: {Config.ENDPOINTS_HELP_URL}\n\n"
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
            AIMessage(content="Thank you! Endpoints recorded:\n" +
                      "\n".join(lines))
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
                    "2) **Client Name (clientIdentCode)**:\n"
                    "- A separate client is available for each customer.\n"
                    "Please share your **clientIdentCode** (e.g. ACME01).\n\n"
                    "Format: `clientIdentCode=ACME01` or `Client: ACME01`"
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
                    "2) **Client Name (clientIdentCode)**:\n"
                    "- A separate client is available for each customer.\n"
                    "Please share your **clientIdentCode** (e.g. ACME01).\n\n"
                    "Format: `clientIdentCode=ACME01` or `Client: ACME01`"
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
                    "3) **WSM User for Authentication**:\n"
                    "- In addition to the client, there is a **technical WSM user** including password for API connection.\n"
                    "Is this user already set up? (Yes/No)"
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

    if user_input.strip() and not prov.get("wsm_user_configured"):
        return NodeNames.CLARIFY

    if not prov.get("wsm_user_configured"):
        return END

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
        "next_node_after_qa": NodeNames.EXPLAIN_SCREENING_VARIANTS,
    }


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
        "next_node_after_qa": NodeNames.EXPLAIN_RESPONSES,
    }


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
        "next_node_after_qa": NodeNames.API_MAPPING_INTRO,
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

    system_name, process, api_file_path = None, None, None
    if isinstance(payload, dict):
        if payload.get("system_name"):
            system_name = str(payload["system_name"]).strip()
        if payload.get("process"):
            process = str(payload["process"]).strip()
        if payload.get("api_metadata"):
            api_file_path = payload.get("api_metadata")
    else:
        raise ValueError(f"Unexpected interrupt payload type: {type(payload)}")

    out: dict = {}
    if system_name:
        out["system_name"] = system_name
    if process:
        out["process"] = process
    if api_file_path:
        out["api_file_path"] = api_file_path
    return out


def process_and_map_api_node(state: ApiMappingState) -> dict:
    """Process customer API metadata and generate mapping suggestions."""
    messages = state.get("messages", [])
    prov = state.get("provisioning", {})
    api_file_path = state.get("api_file_path", "")
    if not api_file_path:
        raise Exception(
            f"Api data has no filename. Something went wrong with storing it. Api metadata: {api_file_path}")

    with open(Config.API_DATA_DIR / api_file_path) as customer_data:
        user_input = customer_data.read()

    # NOTE: Rebuild API data vectorstore fresh to only include current session's data
    # This prevents mixing API data from different customers/sessions
    print("🔄 Rebuilding API data vectorstore for current session only...")
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
You are **AEB’s API Mapping Assistant**. Your job is to propose a field mapping from a customer’s source data model to AEB’s **Compliance Screening – Address Screening** REST API.

## Objectives

1. Produce a precise mapping table from **customer fields** → **AEB API fields**.
2. Ask clarifying questions when the mapping is ambiguous.
3. **Never hallucinate** fields that are not present in the customer input or AEB spec.
4. Respect entity vs. person nuances (e.g., companies shouldn’t fill `surname`/`prenames`).
5. Output must be **deterministic**, concise, and easy to implement.

## General Information about AEB TCM Screening API

{get_general_information_about_screening_api()}

## AEB endpoint (api_screen_addresses_spec)

{get_screen_addresses_spec()}

### Request shape 

* `addresses[]` objects support (examples):
  * `addressType`, `name`, `street`, `pc`, `city`, `district`, `countryISO`, `telNo`, `postbox`, `pcPostbox`, `cityPostbox`, `email`, `fax`, `name1..name4`, `title`, `surname`, `prenames`, `dateOfBirth`, `passportData`, `cityOfBirth`, `countryOfBirthISO`, `nationalityISO`, `position`, `niNumber`, `info`, `aliasGroupNo`, `free1..free7`, `referenceId`, `referenceComment`, `condition {{ value, description }}`
* `screeningParameters` supports:
  * `clientIdentCode`, `profileIdentCode`, `threshold`, `clientSystemId`, `suppressLogging`, `considerGoodGuys`, `userIdentification`, `addressTypeVersion`

## Output format (strict)

1. A **Markdown table** with columns:
   **Customer Data Field** | **AEB API Field** | **Explanation**

   * Use `—` (em dash) if a column is “not applicable”.
   * If a customer field maps to multiple AEB fields, add separate rows.
   * If mapping requires a transform, explain it concretely (e.g., “split by comma; take first token as street”).
2. **Unmapped / Needs Input**: bullet list of customer fields that you could not map, with 1-line reason each.
3. **Assumptions**: numbered list of assumptions you made (keep minimal).
4. **Clarifying Questions**: up to 5 short questions that would eliminate ambiguity.
5. **Validation Notes**: brief reminders (e.g., batch ≤100, `countryISO` must be ISO-2 uppercase, entity vs person field rules).

## Example

**Customer fields (excerpt):**

- `companyName` (string) – legal name
- `email` (string)
- `phone` (string)
- `address.street` (string)
- `address.city` (string)
- `address.zip` (string)
- `address.country` (string, ISO-2 expected?)
- `partner.id` (string)

**AEB fields (excerpt):** `addresses[].name`, `addresses[].email`, `addresses[].telNo`, `addresses[].street`, `addresses[].city`, `addresses[].pc`, `addresses[].countryISO`, `addresses[].referenceId`

**Entity type:** `entity`

### Expected output (format demo)

**Proposed Mapping**

| Customer Data Field | AEB API Field                       | Explanation                                                    |
| ------------------- | ----------------------------------- | -------------------------------------------------------------- |
| companyName         | addresses[].name                    | Company legal name maps directly to `name`.                    |
| email               | addresses[].email                   | Direct map.                                                    |
| phone               | addresses[].telNo                   | Direct map; keep original formatting.                          |
| isPerson            | addresses[].addressType             | Set to "individual" if `isPerson` is true, otherwise "entity". |
| address.street      | addresses[].street                  | Direct map.                                                    |
| address.city        | addresses[].city                    | Direct map.                                                    |
| address.zip         | addresses[].pc                      | Postal code to `pc`.                                           |
| address.country     | addresses[].countryISO              | Must be ISO-2 uppercase (e.g., “GB”).                          |
| partner.id          | addresses[].referenceId             | Use the partner’s ID as unique reference.                      |
| —                   | screeningParameters.clientIdentCode | Provided by AEB tenant setup; not in customer data.            |

**Unmapped / Needs Input**

- `address.country` → confirm if ISO-2 already; if not, provide a lookup or mapping rule.
- `screeningParameters.profileIdentCode` → no clear source; default “DEFAULT” if allowed by policy.

**Assumptions**

1. `address.country` is ISO-2 uppercase; if not, a mapping table will be applied.
2. `entity` type → not populating person-only fields (surname/prenames/etc.).
3. `isPerson` can be used for addressType determination.

**Clarifying Questions**

1. Is `address.country` guaranteed to be ISO-2 already?
2. Should `partner.id` be included in `referenceComment` as well?
3. Do you require `suppressLogging` to be set for re-screening flows?

**Validation Notes**

- Batch size recommended ≤ 100 per request.
- ISO-2 country codes required in `countryISO`.
- For `entity` requests, leave person fields empty.

## Rules (hard constraints)

* **No hallucinations**. Only use:

  * Customer fields provided in **{{customer_schema}}** (and/or **{{customer_example}}**).
  * AEB fields provided in **{{api_screen_addresses_spec}}**.
* If a required AEB field has **no clear source**, put AEB field in the table with **Customer Data Field = `—`** and explain what is needed.
* Prefer **simple, explicit transforms** (split, trim, concat). No vague “AI will infer”.
* If input type is **entity/company**, **do not** map person-only fields (e.g., `surname`, `prenames`) unless the customer explicitly provides a person context.
* Use **concise, implementation-ready language**.

## Decision policy for ambiguous mappings

* If multiple customer fields look plausible, **pick none** and move the field to **Clarifying Questions** rather than guessing.
* If a customer field bundles multiple values (e.g., a full address), propose a deterministic transform and state it.
* If a field looks like an ID/reference, prefer mapping to `referenceId` or `referenceComment` and explain why.

## Style

* Be concise, neutral, and technical.
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
