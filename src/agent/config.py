import os
from pathlib import Path


class Config:
    # TODO: When deploying use gpt-5
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDINGS_MODEL = os.getenv(
        "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
    KNOWLEDGE_BASE_DIR = Path("./vectorstore_min")
    API_DATA_DIR = Path("./api_data")
    API_DATA_VECTOR_STORE = Path("./api_data_vectorstore")
    ENDPOINTS_HELP_URL = os.getenv(
        "AEB_ENDPOINTS_HELP_URL", "<link-zu-Erläuterungen-für-Endpoints>")
