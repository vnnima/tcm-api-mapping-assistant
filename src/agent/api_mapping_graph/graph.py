from __future__ import annotations
from pathlib import Path
from agent.api_mapping_graph.state import ApiMappingState
from agent.api_mapping_graph.nodes import (
    NodeNames,
    api_mapping_intro_node,
    explain_responses_node,
    explain_screening_variants_node,
    intro_node,
    clarify_node,
    ask_endpoints_node,
    ask_client_node,
    ask_wsm_node,
    general_screening_info_node,
    process_and_map_api_node,
    qa_mode_node,
    route_from_intro,
    route_from_clarify,
    route_from_endpoints,
    route_from_client,
    route_from_wsm,
    get_api_data_interrupt_node,
    route_from_qa_mode
)
from agent.api_mapping_graph.decision_interrupt_node import decision_interrupt_node, route_from_decision_interrupt
from langgraph.graph import StateGraph, START, END
import sys
import os
# Add the src directory to Python path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '..'))


# Add src directory to Python path to ensure imports work in LangGraph deployment
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # Go up to src directory
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


def build_graph():
    """Build the graph with conditional edges and persistence."""
    # checkpointer = InMemorySaver() # TODO: Don't need this with Langgraph API

    g = StateGraph(ApiMappingState)

    g.add_node(NodeNames.INTRO, intro_node)
    g.add_node(NodeNames.CLARIFY, clarify_node)
    g.add_node(NodeNames.ASK_ENDPOINTS, ask_endpoints_node)
    g.add_node(NodeNames.ASK_CLIENT, ask_client_node)
    g.add_node(NodeNames.ASK_WSM, ask_wsm_node)
    g.add_node(NodeNames.GENERAL_SCREENING_INFO, general_screening_info_node)
    g.add_node(NodeNames.EXPLAIN_SCREENING_VARIANTS,
               explain_screening_variants_node)
    g.add_node(NodeNames.EXPLAIN_RESPONSES, explain_responses_node)
    g.add_node(NodeNames.API_MAPPING_INTRO, api_mapping_intro_node)
    g.add_node(NodeNames.DECISION_INTERRUPT, decision_interrupt_node)
    g.add_node(NodeNames.GET_API_DATA_INTERRUPT, get_api_data_interrupt_node)
    g.add_node(NodeNames.PROCESS_AND_MAP_API, process_and_map_api_node)

    g.add_node(NodeNames.QA_MODE, qa_mode_node)

    g.add_edge(START, NodeNames.INTRO)

    g.add_conditional_edges(NodeNames.INTRO, route_from_intro, {
        NodeNames.QA_MODE: NodeNames.QA_MODE,
        NodeNames.ASK_ENDPOINTS: NodeNames.ASK_ENDPOINTS,
        NodeNames.ASK_CLIENT: NodeNames.ASK_CLIENT,
        NodeNames.ASK_WSM: NodeNames.ASK_WSM,
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.GENERAL_SCREENING_INFO: NodeNames.GENERAL_SCREENING_INFO,
        NodeNames.PROCESS_AND_MAP_API: NodeNames.PROCESS_AND_MAP_API,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.CLARIFY, route_from_clarify, {
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.INTRO: NodeNames.INTRO,
        NodeNames.ASK_ENDPOINTS: NodeNames.ASK_ENDPOINTS,
        NodeNames.ASK_CLIENT: NodeNames.ASK_CLIENT,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.ASK_ENDPOINTS, route_from_endpoints, {
        NodeNames.ASK_CLIENT: NodeNames.ASK_CLIENT,
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.ASK_CLIENT, route_from_client, {
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.ASK_WSM: NodeNames.ASK_WSM,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.ASK_WSM, route_from_wsm, {
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.GENERAL_SCREENING_INFO: NodeNames.GENERAL_SCREENING_INFO,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.DECISION_INTERRUPT,
                            route_from_decision_interrupt, {
                                NodeNames.EXPLAIN_SCREENING_VARIANTS: NodeNames.EXPLAIN_SCREENING_VARIANTS,
                                NodeNames.EXPLAIN_RESPONSES: NodeNames.EXPLAIN_RESPONSES,
                                NodeNames.API_MAPPING_INTRO: NodeNames.API_MAPPING_INTRO,
                                NodeNames.PROCESS_AND_MAP_API: NodeNames.PROCESS_AND_MAP_API,
                                NodeNames.QA_MODE: NodeNames.QA_MODE,
                            })

    g.add_edge(NodeNames.GENERAL_SCREENING_INFO, NodeNames.DECISION_INTERRUPT)
    g.add_edge(NodeNames.EXPLAIN_SCREENING_VARIANTS,
               NodeNames.DECISION_INTERRUPT)
    g.add_edge(NodeNames.EXPLAIN_RESPONSES, NodeNames.DECISION_INTERRUPT)
    g.add_edge(NodeNames.API_MAPPING_INTRO, NodeNames.GET_API_DATA_INTERRUPT)
    g.add_edge(NodeNames.GET_API_DATA_INTERRUPT, NodeNames.PROCESS_AND_MAP_API)
    g.add_edge(NodeNames.PROCESS_AND_MAP_API, END)

    g.add_conditional_edges(NodeNames.QA_MODE, route_from_qa_mode, {
        NodeNames.EXPLAIN_SCREENING_VARIANTS: NodeNames.EXPLAIN_SCREENING_VARIANTS,
        NodeNames.EXPLAIN_RESPONSES: NodeNames.EXPLAIN_RESPONSES,
        NodeNames.API_MAPPING_INTRO: NodeNames.API_MAPPING_INTRO,
        NodeNames.PROCESS_AND_MAP_API: NodeNames.PROCESS_AND_MAP_API,
        NodeNames.QA_MODE: NodeNames.QA_MODE,
    })

    # return g.compile(checkpointer=checkpointer) # TODO: Don't need this with Langgraph API
    return g.compile()


api_mapping_graph = build_graph()
