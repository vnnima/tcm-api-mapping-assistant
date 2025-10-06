from __future__ import annotations
from agent.error_detection_graph.state import ErrorDetectionState, ErrorDetectionNodeNames
from agent.error_detection_graph.nodes import (
    chat_node,
    route_chat
)
from langgraph.graph import StateGraph, START, END


def create_error_detection_graph() -> StateGraph:
    """Create the error detection subgraph."""

    g = StateGraph(ErrorDetectionState)
    g.add_node(ErrorDetectionNodeNames.CHAT, chat_node)
    g.add_edge(START, ErrorDetectionNodeNames.CHAT)
    g.add_conditional_edges(
        ErrorDetectionNodeNames.CHAT, route_chat, {END: END})

    return g


error_detection_graph = create_error_detection_graph().compile()
