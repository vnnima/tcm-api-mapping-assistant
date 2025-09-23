from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from agent.nodes import State, api_mapping_intro_node, decision_interrupt_node, explain_responses_node, explain_screening_variants_node, intro_node, clarify_node, ask_endpoints_node, ask_client_node, ask_wsm_node, general_screening_info_node, qa_mode_node, route_from_explain_responses, route_from_explain_responses, route_from_explain_screening_variants, route_from_intro, route_from_clarify, route_from_endpoints, route_from_client, route_from_qa_mode, route_from_wsm, route_from_general_screening_info, route_from_qa_mode, route_from_decision_interrupt


def build_graph():
    """Build the graph with conditional edges and persistence."""
    # checkpointer = InMemorySaver() # TODO: Don't need this with Langgraph API

    g = StateGraph(State)

    g.add_node("intro", intro_node)
    g.add_node("clarify", clarify_node)
    g.add_node("ask_endpoints", ask_endpoints_node)
    g.add_node("ask_client", ask_client_node)
    g.add_node("ask_wsm", ask_wsm_node)
    g.add_node("general_screening_info", general_screening_info_node)
    g.add_node("explain_screening_variants", explain_screening_variants_node)
    g.add_node("explain_responses", explain_responses_node)
    g.add_node("api_mapping_intro", api_mapping_intro_node)
    g.add_node("decision_interrupt", decision_interrupt_node)

    g.add_node("qa_mode", qa_mode_node)

    g.add_edge(START, "intro")

    g.add_conditional_edges("intro", route_from_intro, {
        "qa_mode": "qa_mode",
        "ask_endpoints": "ask_endpoints",
        "ask_client": "ask_client",
        "ask_wsm": "ask_wsm",
        "clarify": "clarify",
        "general_screening_info": "general_screening_info",
        "__end__": END
    })
    g.add_conditional_edges("clarify", route_from_clarify, {
        "clarify": "clarify",
        "intro": "intro",
        "ask_endpoints": "ask_endpoints",
        "ask_client": "ask_client",
        "__end__": END
    })
    g.add_conditional_edges("ask_endpoints", route_from_endpoints, {
        "ask_client": "ask_client",
        "clarify": "clarify",
        "__end__": END
    })
    g.add_conditional_edges("ask_client", route_from_client, {
        "clarify": "clarify",
        "ask_wsm": "ask_wsm",
        "__end__": END
    })
    g.add_conditional_edges("ask_wsm", route_from_wsm, {
        "clarify": "clarify",
        "general_screening_info": "general_screening_info",
        "__end__": END
    })
    g.add_conditional_edges("decision_interrupt",
                            route_from_decision_interrupt)

    # TODO: No need to make this conditional
    g.add_conditional_edges("general_screening_info", route_from_general_screening_info, {
        "decision_interrupt": "decision_interrupt",
    })
    # TODO: No need to make this conditional
    g.add_conditional_edges("explain_screening_variants", route_from_explain_screening_variants, {
        "decision_interrupt": "decision_interrupt",
    })
    # TODO: No need to make this conditional
    g.add_conditional_edges("explain_responses", route_from_explain_responses, {
        "decision_interrupt": "decision_interrupt",
    })

    g.add_conditional_edges("qa_mode", route_from_qa_mode)

    # return g.compile(checkpointer=checkpointer) # TODO: Don't need this with Langgraph API
    return g.compile()


api_mapping_graph = build_graph()
