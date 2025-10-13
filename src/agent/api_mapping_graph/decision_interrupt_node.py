from __future__ import annotations
from .state import ApiMappingState
from .nodes import NodeNames
from langgraph.types import interrupt
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

def decision_interrupt_node(state: ApiMappingState) -> dict:
    payload = interrupt({
        "type": "choice_or_question",
        "prompt": "Press `continue` to proceed or ask your question.",
    })

    decision, question = None, None

    if isinstance(payload, dict):
        if payload.get("continue") is True or str(payload.get("continue")).lower() in {"true", "1", "yes"}:
            decision = "continue"
        elif "question" in payload:
            decision = "qa"
            question = str(payload["question"]).strip()
    else:
        raise ValueError(f"Unexpected interrupt payload type: {type(payload)}")

    if decision is None:
        decision = "qa"
        question = (question or "").strip()

    out = {"decision": decision, "pending_question": question}
    if question:
        out["messages"] = [HumanMessage(content=question)]
    return out


def route_from_decision_interrupt(state: ApiMappingState) -> str:
    if state.get("decision") == "continue":
        return state.get("next_node_after_qa", NodeNames.EXPLAIN_SCREENING_VARIANTS)
    return NodeNames.QA_MODE

