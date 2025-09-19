from typing import Any, Dict, List, TypedDict

class State(TypedDict, total=False):
    started: bool                     # whether user agreed to start
    completed: bool                   # whether the initial flow is completed
    # {test_endpoint, prod_endpoint, clientIdentCode, wsm_user_configured}
    provisioning: Dict[str, Any]
    user_input: str | None
    messages: List[Dict[str, str]]
    rag_snippets: List[str]

class ProvisioningState(TypedDict, total=False):
    test_endpoint: str | None
    prod_endpoint: str | None
    clientIdentCode: str | None
    wsm_user_configured: bool | None