from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from agent.config import Config


def _embedder() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=Config.OPENAI_EMBEDDINGS_MODEL)


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return None


# TODO: Add support for PDF and Word
# TODO: Add another build_index for the customer data
def build_index(docs_dir: str, store_dir: Path = Config.INDEX_DIR):
    root = Path(docs_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Play around with these settings or even make a custom chunker/splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150)
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in Config.ALLOWED_EXTS:
            continue
        content = _read_text(p)
        if not content:
            print(f"[warn] Skipping unreadable file: {p}")
            continue
        chunks = splitter.split_text(content)
        texts.extend(chunks)
        metas.extend([{"source": str(p)}] * len(chunks))

    if not texts:
        print("[warn] No documents found to index.")
        return

    Chroma.from_texts(
        texts=texts,
        embedding=_embedder(),
        metadatas=metas,
        persist_directory=str(store_dir),
    )
    print(f"Indexed {len(texts)} chunks → {store_dir}")


def rag_search(query: str, k: int = 4, store_dir: Path = Config.INDEX_DIR) -> List[str]:
    try:
        print(f"DEBUG RAG: Searching for '{query}' in {store_dir}")
        if not store_dir.exists():
            print(
                f"DEBUG RAG: Vector store directory {store_dir} does not exist")
            return []

        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())
        docs = vs.similarity_search(query, k=k)
        print(f"DEBUG RAG: Found {len(docs)} documents")
        results = [d.page_content[:800] for d in docs]
        for i, result in enumerate(results):
            print(f"DEBUG RAG: Doc {i}: {result[:100]}...")
        return results
    except Exception as e:
        print(f"DEBUG RAG: Error in rag_search: {e}")
        return []
