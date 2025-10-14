
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import List, TypedDict, Annotated, Sequence

class ProvisioningState(TypedDict, total=False):
    test_endpoint: str | None
    prod_endpoint: str | None
    clientIdentCode: str | None
    wsm_user_configured: bool | None


class ApiMappingState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    provisioning: ProvisioningState

    decision: str | None  # continue or qa
    pending_question: str | None  # the user's question to feed into qa_mode
    next_node_after_qa: str

    # API Mapping Stuff
    system_name: str | None
    process: str | None
    api_file_path: str | None

    started: bool
    completed: bool
    rag_snippets: List[str]
