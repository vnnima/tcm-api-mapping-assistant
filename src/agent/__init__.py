"""AEB API Mapping Agent.

This module provides the main API mapping graph.
"""
from agent.api_mapping_graph.graph import api_mapping_graph
from agent.documentation_qna_graph.graph import documentation_qna_graph
from agent.error_detection_graph.graph import error_detection_graph
from agent.request_validation_graph.graph import request_validation_graph
import sys
from pathlib import Path

# Add src directory to Python path to ensure imports work in LangGraph deployment
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent  # Go up to src directory
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


__all__ = ["api_mapping_graph", "documentation_qna_graph",
           "error_detection_graph", "request_validation_graph"]
