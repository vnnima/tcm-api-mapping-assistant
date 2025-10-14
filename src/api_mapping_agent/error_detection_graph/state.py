from __future__ import annotations

from enum import Enum
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ErrorDetectionNodeNames(str, Enum):
    CHAT = "chat"


class ErrorDetectionState(TypedDict):
    """State for the error detection subgraph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    completed: bool
