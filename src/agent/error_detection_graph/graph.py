from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from agent.error_detection_graph.nodes import (
    chat_node,
    route_chat
)
from agent.error_detection_graph.state import ErrorDetectionState, ErrorDetectionNodeNames
import sys
import os
from pathlib import Path

# Add src directory to Python path to ensure imports work in LangGraph deployment
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # Go up to src directory
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def create_error_detection_graph() -> StateGraph:
    """Create the error detection subgraph."""

    g = StateGraph(ErrorDetectionState)
    g.add_node(ErrorDetectionNodeNames.CHAT, chat_node)
    g.add_edge(START, ErrorDetectionNodeNames.CHAT)
    g.add_conditional_edges(
        ErrorDetectionNodeNames.CHAT, route_chat, {END: END})

    return g


error_detection_graph = create_error_detection_graph().compile()
