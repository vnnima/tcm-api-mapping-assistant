from __future__ import annotations

from enum import Enum
from typing import Dict, List, Any, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class QnaNodeNames(str, Enum):
    WELCOME = "welcome"
    ANSWER_QUESTION = "answer_question"


class DocumentationQnaState(TypedDict):
    """State for the documentation Q&A subgraph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    search_results: List[str] | None
    completed: bool
