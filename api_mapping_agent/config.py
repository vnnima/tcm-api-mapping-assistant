import os
import tempfile
from pathlib import Path


# Get the project root directory (where the langgraph.json file is located)
PROJECT_ROOT = Path(__file__).parent.parent

# Use writable directories for deployment environments
# In containerized environments, use /tmp for writable storage
WRITABLE_ROOT = Path(
    os.getenv("WRITABLE_ROOT", tempfile.gettempdir())) / "api_mapping_agent"


class Config:
    # TODO: When deploying use gpt-5
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDINGS_MODEL = os.getenv(
        "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
    KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
    KNOWLEDGE_BASE_VECTOR_STORE = WRITABLE_ROOT / "vectorstore_min"
    API_DATA_DIR = WRITABLE_ROOT / "api_data"
    API_DATA_VECTOR_STORE = WRITABLE_ROOT / "api_data_vectorstore"
    ENDPOINTS_HELP_URL = os.getenv(
        "AEB_ENDPOINTS_HELP_URL", "<link-zu-Erläuterungen-für-Endpoints>")
