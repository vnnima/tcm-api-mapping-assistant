from __future__ import annotations
from agent.documentation_qna_graph.nodes import (
    welcome_node,
    answer_question_node,
    route_from_welcome,
    route_from_answer
)
from agent.documentation_qna_graph.state import DocumentationQnaState, QnaNodeNames
from langgraph.graph import StateGraph, START, END


def create_documentation_qna_graph() -> StateGraph:
    """Create the documentation Q&A subgraph."""

    g = StateGraph(DocumentationQnaState)

    g.add_node(QnaNodeNames.ANSWER_QUESTION, answer_question_node)

    g.add_edge(START, QnaNodeNames.ANSWER_QUESTION)
    g.add_conditional_edges(QnaNodeNames.ANSWER_QUESTION, route_from_answer)

    return g


documentation_qna_graph = create_documentation_qna_graph().compile()
