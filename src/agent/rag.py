import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, RecursiveJsonSplitter, MarkdownTextSplitter
from langchain_chroma import Chroma

from agent.config import Config

_BUILT = False


def _normalize_text(s: str) -> str:
    return " ".join(s.lower().split())


def _hash_text(s: str) -> str:
    return hashlib.sha1(_normalize_text(s).encode("utf-8")).hexdigest()


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


def _split_markdown(content: str) -> List[str]:
    splitter = MarkdownTextSplitter(chunk_size=1200, chunk_overlap=100)
    return splitter.split_text(content)


def _split_json(content: str) -> List[str]:
    json_content = json.loads(content)
    try:
        rjs = RecursiveJsonSplitter(max_chunk_size=1000)
        return rjs.split_text(json_content)
    except Exception:
        pass
    # Fallback: treat as plain text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150)
    return splitter.split_text(content)


def _split_plain(content: str) -> List[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150)
    return splitter.split_text(content)


def _split_file_by_suffix(path: Path, content: str) -> List[str]:
    suf = path.suffix.lower().strip()
    if suf in {".md", ".markdown"}:
        return _split_markdown(content)
    elif suf == ".json":
        return _split_json(content)
    else:
        # TODO: Maybe add CSV splitter
        return _split_plain(content)


def _dedup_texts(texts: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for t in texts:
        key = _normalize_text(t)
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out


def build_index(docs_dir: str, store_dir: Path = Config.KNOWLEDGE_BASE_DIR):
    """
    Build a Chroma store from files in `docs_dir`, using a splitter chosen by file ending.
    Safe to call multiple times per *process* thanks to _BUILT, to avoid duplicates.
    """
    global _BUILT
    if _BUILT:
        print("Index already built in this session, skipping.")
        return

    root = Path(docs_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in Config.ALLOWED_EXTS:
            continue

        content = _read_text(p)
        if not content:
            print(f"[warn] Skipping unreadable file: {p}")
            continue

        try:
            chunks = _split_file_by_suffix(p, content)
        except Exception as e:
            print(
                f"[warn] Split failed for {p}: {e}; falling back to plain splitter")
            chunks = _split_plain(content)

        if not chunks:
            continue

        # OPTIONAL: small local dedup per file
        chunks = _dedup_texts(chunks)

        texts.extend(chunks)
        metas.extend([{"source": str(p)}] * len(chunks))

    if not texts:
        print("[warn] No documents found to index.")
        return

    # Build or load persistent store, then add docs with stable ids (content hash)
    vs = Chroma(persist_directory=str(store_dir),
                embedding_function=_embedder())

    # Chroma.add_texts allows ids, but raises on duplicates; since we only build once per process,
    # we can just add once here. If you call build_index repeatedly in the same process, hash IDs help.
    ids = [_hash_text(m["source"] + " :: " + t) for t, m in zip(texts, metas)]
    vs.add_texts(texts=texts, metadatas=metas, ids=ids)

    print(f"Indexed {len(texts)} chunks → {store_dir}")
    _BUILT = True


def rag_search(
    query: str,
    k: int = 5,
    store_dir: Path = Config.KNOWLEDGE_BASE_DIR,
    mmr: bool = True,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
) -> List[str]:
    """
    MMR retrieval to reduce duplicate results. Falls back to similarity if mmr=False.
    """
    try:
        print(f"DEBUG RAG: Searching for '{query}' in {store_dir}")
        if not store_dir.exists():
            print(
                f"DEBUG RAG: Vector store directory {store_dir} does not exist")
            return []

        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())

        if mmr:
            retriever = vs.as_retriever(
                search_type="mmr",
                search_kwargs={"k": k, "fetch_k": fetch_k,
                               "lambda_mult": lambda_mult},
            )
            docs = retriever.get_relevant_documents(query)
        else:
            docs = vs.similarity_search(query, k=k)

        # Post-dedup by normalized text
        snippets = _dedup_texts([d.page_content[:1200] for d in docs])[:k]

        print(
            f"DEBUG RAG: Retrieved {len(docs)} docs, returning {len(snippets)} unique snippets")
        for i, s in enumerate(snippets):
            print(f"DEBUG RAG: Snippet {i}: {s[:120]}...")
        return snippets

    except Exception as e:
        print(f"DEBUG RAG: Error in rag_search: {e}")
        return []
