from __future__ import annotations

from enum import Enum
from typing import Dict, List, Any, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ValidationNodeNames(str, Enum):
    GET_REQUEST = "get_request"
    VALIDATE_REQUEST = "validate_request"
    SHOW_RESULTS = "show_results"


class RequestValidationState(TypedDict):
    """State for the request validation subgraph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_request: str | None
    validation_results: Dict[str, Any] | None
    syntax_valid: bool | None
    required_fields_present: bool | None
    field_quality_issues: List[str] | None
    improvement_suggestions: List[str] | None
    completed: bool
