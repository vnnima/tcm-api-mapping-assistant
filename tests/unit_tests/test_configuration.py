from langgraph.pregel import Pregel

from agent.api_mapping_graph.graph import api_mapping_graph


def test_placeholder() -> None:
    # TODO: You can add actual unit tests
    # for your graph and other logic here.
    assert isinstance(api_mapping_graph, Pregel)
