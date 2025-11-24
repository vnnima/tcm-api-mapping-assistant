from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from api_mapping_agent.api_mapping_graph.decision_interrupt_node import decision_interrupt_node, route_from_decision_interrupt
from api_mapping_agent.api_mapping_graph.nodes import (
    NodeNames,
    api_mapping_intro_node,
    explain_responses_node,
    explain_screening_variants_node,
    intro_node,
    clarify_node,
    ask_client_node,
    ask_wsm_node,
    ask_general_info_node,
    general_screening_info_node,
    ask_screening_variants_node,
    ask_responses_node,
    process_and_map_api_node,
    qa_mode_node,
    route_from_intro,
    route_from_clarify,
    route_from_client,
    route_from_wsm,
    route_from_ask_general_info,
    route_from_ask_screening_variants,
    route_from_ask_responses,
    get_api_data_interrupt_node,
    route_from_qa_mode
)
from api_mapping_agent.api_mapping_graph.state import ApiMappingState


def build_graph():
    """Build the graph with conditional edges and persistence."""
    # checkpointer = InMemorySaver() # TODO: Don't need this with Langgraph API

    g = StateGraph(ApiMappingState)

    g.add_node(NodeNames.INTRO, intro_node)
    g.add_node(NodeNames.CLARIFY, clarify_node)
    g.add_node(NodeNames.ASK_CLIENT, ask_client_node)
    g.add_node(NodeNames.ASK_WSM, ask_wsm_node)
    g.add_node(NodeNames.ASK_GENERAL_INFO, ask_general_info_node)
    g.add_node(NodeNames.GENERAL_SCREENING_INFO, general_screening_info_node)
    g.add_node(NodeNames.ASK_SCREENING_VARIANTS, ask_screening_variants_node)
    g.add_node(NodeNames.EXPLAIN_SCREENING_VARIANTS,
               explain_screening_variants_node)
    g.add_node(NodeNames.ASK_RESPONSES, ask_responses_node)
    g.add_node(NodeNames.EXPLAIN_RESPONSES, explain_responses_node)
    g.add_node(NodeNames.API_MAPPING_INTRO, api_mapping_intro_node)
    g.add_node(NodeNames.DECISION_INTERRUPT, decision_interrupt_node)
    g.add_node(NodeNames.GET_API_DATA_INTERRUPT, get_api_data_interrupt_node)
    g.add_node(NodeNames.PROCESS_AND_MAP_API, process_and_map_api_node)

    g.add_node(NodeNames.QA_MODE, qa_mode_node)

    g.add_edge(START, NodeNames.INTRO)

    g.add_conditional_edges(NodeNames.INTRO, route_from_intro, {
        NodeNames.QA_MODE: NodeNames.QA_MODE,
        NodeNames.ASK_CLIENT: NodeNames.ASK_CLIENT,
        NodeNames.ASK_WSM: NodeNames.ASK_WSM,
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.ASK_GENERAL_INFO: NodeNames.ASK_GENERAL_INFO,
        NodeNames.PROCESS_AND_MAP_API: NodeNames.PROCESS_AND_MAP_API,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.CLARIFY, route_from_clarify, {
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.INTRO: NodeNames.INTRO,
        NodeNames.ASK_CLIENT: NodeNames.ASK_CLIENT,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.ASK_CLIENT, route_from_client, {
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.ASK_WSM: NodeNames.ASK_WSM,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.ASK_WSM, route_from_wsm, {
        NodeNames.CLARIFY: NodeNames.CLARIFY,
        NodeNames.ASK_GENERAL_INFO: NodeNames.ASK_GENERAL_INFO,
        "__end__": END
    })
    g.add_conditional_edges(NodeNames.ASK_GENERAL_INFO, route_from_ask_general_info, {
        NodeNames.GENERAL_SCREENING_INFO: NodeNames.GENERAL_SCREENING_INFO,
        NodeNames.ASK_SCREENING_VARIANTS: NodeNames.ASK_SCREENING_VARIANTS,
        NodeNames.ASK_GENERAL_INFO: NodeNames.ASK_GENERAL_INFO,  # Loop back for questions
    })
    g.add_edge(NodeNames.GENERAL_SCREENING_INFO,
               NodeNames.ASK_SCREENING_VARIANTS)

    g.add_conditional_edges(NodeNames.ASK_SCREENING_VARIANTS, route_from_ask_screening_variants, {
        NodeNames.EXPLAIN_SCREENING_VARIANTS: NodeNames.EXPLAIN_SCREENING_VARIANTS,
        NodeNames.ASK_RESPONSES: NodeNames.ASK_RESPONSES,
        # Loop back for questions
        NodeNames.ASK_SCREENING_VARIANTS: NodeNames.ASK_SCREENING_VARIANTS,
    })
    g.add_edge(NodeNames.EXPLAIN_SCREENING_VARIANTS, NodeNames.ASK_RESPONSES)

    g.add_conditional_edges(NodeNames.ASK_RESPONSES, route_from_ask_responses, {
        NodeNames.EXPLAIN_RESPONSES: NodeNames.EXPLAIN_RESPONSES,
        NodeNames.API_MAPPING_INTRO: NodeNames.API_MAPPING_INTRO,
        NodeNames.ASK_RESPONSES: NodeNames.ASK_RESPONSES,  # Loop back for questions
    })
    g.add_edge(NodeNames.EXPLAIN_RESPONSES, NodeNames.API_MAPPING_INTRO)
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
