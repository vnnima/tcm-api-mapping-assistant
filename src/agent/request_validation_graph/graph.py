from __future__ import annotations
from agent.request_validation_graph.nodes import (
    get_request_node,
    validate_request_node,
    show_results_node,
    route_from_get_request,
)
from agent.request_validation_graph.state import RequestValidationState, ValidationNodeNames
from langgraph.graph import StateGraph, START, END

def build_request_validation_graph():
    """Build the request validation subgraph."""

    g = StateGraph(RequestValidationState)

    g.add_node(ValidationNodeNames.GET_REQUEST, get_request_node)
    g.add_node(ValidationNodeNames.VALIDATE_REQUEST, validate_request_node)
    g.add_node(ValidationNodeNames.SHOW_RESULTS, show_results_node)

    g.add_edge(START, ValidationNodeNames.GET_REQUEST)
    g.add_conditional_edges(ValidationNodeNames.GET_REQUEST, route_from_get_request, {
        ValidationNodeNames.GET_REQUEST: ValidationNodeNames.GET_REQUEST,
        ValidationNodeNames.VALIDATE_REQUEST: ValidationNodeNames.VALIDATE_REQUEST,
        "__end__": END
    })
    g.add_edge(ValidationNodeNames.VALIDATE_REQUEST,
               ValidationNodeNames.SHOW_RESULTS)
    g.add_edge(ValidationNodeNames.SHOW_RESULTS, END)

    return g.compile()


request_validation_graph = build_request_validation_graph()
