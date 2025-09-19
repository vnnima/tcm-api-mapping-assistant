import os
from pathlib import Path

class Config:
    # TODO: When deploying use gpt-5
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDINGS_MODEL = os.getenv(
        "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
    INDEX_DIR = Path(os.getenv("VECTORSTORE_PATH", "./vectorstore_min"))
    # TODO: Probably also csv and XML. DO we need this as an env?
    ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml"}
    # TODO: Do we need this? Do we need this as an env?
    ENDPOINTS_HELP_URL = os.getenv(
        "AEB_ENDPOINTS_HELP_URL", "<link-zu-Erläuterungen-für-Endpoints>")
