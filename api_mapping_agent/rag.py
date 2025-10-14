import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter, RecursiveJsonSplitter, MarkdownTextSplitter
from langchain_chroma import Chroma

from api_mapping_agent.config import Config

ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml"}


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


def _index_exists(store_dir: Path) -> bool:
    """Check if a Chroma index already exists in the store directory."""
    try:
        if not store_dir.exists():
            print(f"DEBUG: Store directory {store_dir} does not exist")
            return False

        # Check if there are any files that suggest a Chroma store exists
        chroma_files = list(store_dir.glob("*"))
        print(f"DEBUG: Found {len(chroma_files)} files in {store_dir}")
        for f in chroma_files[:5]:  # Show first 5 files
            print(f"DEBUG: - {f.name}")
        return len(chroma_files) > 0
    except Exception as e:
        print(f"DEBUG: Error checking index existence: {e}")
        return False


def debug_vectorstore_contents(store_dir: Path = Config.KNOWLEDGE_BASE_DIR):
    """Debug function to check vectorstore contents and configuration."""
    print(f"\n=== VECTORSTORE DEBUG ===")
    print(f"Store directory: {store_dir}")
    print(f"Store directory exists: {store_dir.exists()}")

    if store_dir.exists():
        files = list(store_dir.glob("*"))
        print(f"Files in store directory: {len(files)}")
        for f in files:
            print(f"  - {f.name} ({f.stat().st_size} bytes)")

    try:
        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())
        # Try to get collection info
        collection = vs._collection
        print(f"Collection name: {collection.name}")
        print(f"Collection count: {collection.count()}")

        # Try a simple test query
        test_results = vs.similarity_search("test", k=1)
        print(f"Test query returned {len(test_results)} results")
        if test_results:
            print(
                f"First result preview: {test_results[0].page_content[:100]}...")

    except Exception as e:
        print(f"Error accessing vectorstore: {e}")

    print(f"=== END DEBUG ===\n")


def debug_knowledge_base_files(docs_dir: str):
    """Debug function to check what files are available for indexing."""
    print(f"\n=== KNOWLEDGE BASE FILES DEBUG ===")
    root = Path(docs_dir)
    print(f"Docs directory: {root}")
    print(f"Docs directory exists: {root.exists()}")

    if not root.exists():
        print(f"ERROR: Docs directory {root} does not exist!")
        return

    all_files = list(root.rglob("*"))
    print(f"Total files found: {len(all_files)}")

    valid_files = [p for p in all_files if p.is_file(
    ) and p.suffix.lower() in ALLOWED_EXTS]
    print(f"Valid files for indexing: {len(valid_files)}")
    print(f"Allowed extensions: {ALLOWED_EXTS}")

    for p in valid_files[:10]:  # Show first 10 valid files
        try:
            content = _read_text(p)
            content_len = len(content) if content else 0
            print(f"  - {p.relative_to(root)} ({content_len} chars)")
        except Exception as e:
            print(f"  - {p.relative_to(root)} (ERROR: {e})")

    if len(valid_files) > 10:
        print(f"  ... and {len(valid_files) - 10} more files")

    print(f"=== END FILES DEBUG ===\n")


def clear_vectorstore(store_dir: Path):
    """Clear/delete an existing vectorstore to start fresh."""
    try:
        if store_dir.exists():
            import shutil
            print(f"Clearing vectorstore at {store_dir}")
            shutil.rmtree(store_dir)
            print(f"✅ Vectorstore cleared: {store_dir}")
        else:
            print(f"Vectorstore {store_dir} does not exist, nothing to clear")
    except Exception as e:
        print(f"Error clearing vectorstore {store_dir}: {e}")


def build_index_fresh(docs_dir: str, store_dir: Path = Config.KNOWLEDGE_BASE_VECTOR_STORE, clear_existing: bool = False):
    """
    Build a fresh Chroma store from files in `docs_dir`.
    If clear_existing=True, removes any existing vectorstore first.
    """
    print(f"\n=== BUILDING {'FRESH ' if clear_existing else ''}INDEX ===")
    print(f"Docs directory: {docs_dir}")
    print(f"Store directory: {store_dir}")
    print(f"Clear existing: {clear_existing}")

    if clear_existing:
        clear_vectorstore(store_dir)

    root = Path(docs_dir)

    # Ensure the store directory exists and is writable
    try:
        store_dir.mkdir(parents=True, exist_ok=True)
        # Test write permissions by creating a temporary file
        test_file = store_dir / "test_write"
        test_file.write_text("test")
        test_file.unlink()
    except (PermissionError, OSError) as e:
        print(f"[ERROR] Cannot write to directory {store_dir}: {e}")
        print("Using fallback temporary directory...")
        import tempfile
        store_dir = Path(tempfile.mkdtemp(prefix="chroma_"))
        print(f"Using fallback directory: {store_dir}")

    # Debug the knowledge base files first
    debug_knowledge_base_files(docs_dir)

    # Check if index already exists (unless we're clearing)
    if not clear_existing and _index_exists(store_dir):
        print(f"Index already exists at {store_dir}, skipping build.")
        debug_vectorstore_contents(store_dir)
        return

    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    print(f"Scanning for files in {root}...")
    file_count = 0
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXTS:
            continue

        file_count += 1
        print(f"Processing file {file_count}: {p.relative_to(root)}")

        content = _read_text(p)
        if not content:
            print(f"[warn] Skipping unreadable file: {p}")
            continue

        print(f"  File content length: {len(content)} characters")

        try:
            chunks = _split_file_by_suffix(p, content)
            print(f"  Split into {len(chunks)} chunks")
        except Exception as e:
            print(
                f"[warn] Split failed for {p}: {e}; falling back to plain splitter")
            chunks = _split_plain(content)
            print(f"  Fallback split into {len(chunks)} chunks")

        if not chunks:
            print(f"  No chunks generated for {p}")
            continue

        # OPTIONAL: small local dedup per file
        chunks = _dedup_texts(chunks)
        print(f"  After dedup: {len(chunks)} chunks")

        texts.extend(chunks)
        metas.extend([{"source": str(p)}] * len(chunks))

    print(f"\nTotal processing results:")
    print(f"Files processed: {file_count}")
    print(f"Total text chunks: {len(texts)}")

    if not texts:
        print("[ERROR] No documents found to index!")
        return

    print(f"Building Chroma vectorstore at {store_dir}...")

    # Build or load persistent store, then add docs with stable ids (content hash)
    try:
        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())
    except Exception as e:
        print(f"[ERROR] Failed to create ChromaDB at {store_dir}: {e}")
        # Try with a fresh temporary directory
        import tempfile
        store_dir = Path(tempfile.mkdtemp(prefix="chroma_fallback_"))
        print(f"Retrying with fresh directory: {store_dir}")
        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())

    # Chroma.add_texts allows ids, but raises on duplicates; since we only build once per process,
    # we can just add once here. If you call build_index repeatedly in the same process, hash IDs help.
    ids = [_hash_text(m["source"] + " :: " + t) for t, m in zip(texts, metas)]

    print(f"Adding {len(texts)} texts to vectorstore...")
    try:
        vs.add_texts(texts=texts, metadatas=metas, ids=ids)
    except Exception as e:
        if "readonly database" in str(e).lower():
            print(f"[ERROR] Database is readonly. Trying in-memory vector store...")
            # Fallback to in-memory ChromaDB
            vs = Chroma(embedding_function=_embedder())
            vs.add_texts(texts=texts, metadatas=metas, ids=ids)
            print(f"⚠️  Using in-memory vectorstore (data will not persist)")
        else:
            raise e

    print(f"✅ Successfully indexed {len(texts)} chunks → {store_dir}")

    # Verify the index was created
    debug_vectorstore_contents(store_dir)
    print(f"=== END INDEX BUILD ===\n")


def build_index(docs_dir: str, store_dir: Path = Config.KNOWLEDGE_BASE_VECTOR_STORE):
    """
    Build a Chroma store from files in `docs_dir`, using a splitter chosen by file ending.
    Checks if index already exists to avoid rebuilding unnecessarily.
    """
    print(f"\n=== BUILDING INDEX ===")
    print(f"Docs directory: {docs_dir}")
    print(f"Store directory: {store_dir}")

    root = Path(docs_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    # Debug the knowledge base files first
    debug_knowledge_base_files(docs_dir)

    # Check if index already exists
    if _index_exists(store_dir):
        print(f"Index already exists at {store_dir}, skipping build.")
        debug_vectorstore_contents(store_dir)
        return

    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    print(f"Scanning for files in {root}...")
    file_count = 0
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXTS:
            continue

        file_count += 1
        print(f"Processing file {file_count}: {p.relative_to(root)}")

        content = _read_text(p)
        if not content:
            print(f"[warn] Skipping unreadable file: {p}")
            continue

        print(f"  File content length: {len(content)} characters")

        try:
            chunks = _split_file_by_suffix(p, content)
            print(f"  Split into {len(chunks)} chunks")
        except Exception as e:
            print(
                f"[warn] Split failed for {p}: {e}; falling back to plain splitter")
            chunks = _split_plain(content)
            print(f"  Fallback split into {len(chunks)} chunks")

        if not chunks:
            print(f"  No chunks generated for {p}")
            continue

        # OPTIONAL: small local dedup per file
        chunks = _dedup_texts(chunks)
        print(f"  After dedup: {len(chunks)} chunks")

        texts.extend(chunks)
        metas.extend([{"source": str(p)}] * len(chunks))

    print(f"\nTotal processing results:")
    print(f"Files processed: {file_count}")
    print(f"Total text chunks: {len(texts)}")

    if not texts:
        print("[ERROR] No documents found to index!")
        return

    print(f"Building Chroma vectorstore at {store_dir}...")

    # Build or load persistent store, then add docs with stable ids (content hash)
    try:
        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())
    except Exception as e:
        print(f"[ERROR] Failed to create ChromaDB at {store_dir}: {e}")
        # Try with a fresh temporary directory
        import tempfile
        store_dir = Path(tempfile.mkdtemp(prefix="chroma_fallback_"))
        print(f"Retrying with fresh directory: {store_dir}")
        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())

    # Chroma.add_texts allows ids, but raises on duplicates; since we only build once per process,
    # we can just add once here. If you call build_index repeatedly in the same process, hash IDs help.
    ids = [_hash_text(m["source"] + " :: " + t) for t, m in zip(texts, metas)]

    print(f"Adding {len(texts)} texts to vectorstore...")
    try:
        vs.add_texts(texts=texts, metadatas=metas, ids=ids)
    except Exception as e:
        if "readonly database" in str(e).lower():
            print(f"[ERROR] Database is readonly. Trying in-memory vector store...")
            # Fallback to in-memory ChromaDB
            vs = Chroma(embedding_function=_embedder())
            vs.add_texts(texts=texts, metadatas=metas, ids=ids)
            print(f"⚠️  Using in-memory vectorstore (data will not persist)")
        else:
            raise e

    print(f"✅ Successfully indexed {len(texts)} chunks → {store_dir}")

    # Verify the index was created
    debug_vectorstore_contents(store_dir)
    print(f"=== END INDEX BUILD ===\n")


def ensure_index_built(docs_dir: str, store_dir: Path = Config.KNOWLEDGE_BASE_VECTOR_STORE):
    """
    Ensure that the index is built for the given docs directory.
    This is a convenience function that can be called before any RAG search.
    """
    if not _index_exists(store_dir):
        print(f"Building index for {docs_dir}...")
        build_index(docs_dir, store_dir)
    else:
        print(f"Index already exists at {store_dir}")


def rag_search(
    query: str,
    k: int = 5,
    store_dir: Path = Config.KNOWLEDGE_BASE_VECTOR_STORE,
    mmr: bool = True,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
) -> List[str]:
    """
    MMR retrieval to reduce duplicate results. Falls back to similarity if mmr=False.
    Ensures index exists before searching.
    """
    try:
        print(f"\n=== RAG SEARCH ===")
        print(f"Query: '{query}'")
        print(f"Store directory: {store_dir}")
        print(f"K: {k}, MMR: {mmr}")

        if not _index_exists(store_dir):
            print(f"Index not found at {store_dir}, building it now...")
            # Try to build from knowledge base or docs directory
            docs_dir = Config.KNOWLEDGE_BASE_DIR.as_posix(
            ) if store_dir == Config.KNOWLEDGE_BASE_VECTOR_STORE else Config.API_DATA_DIR.as_posix()
            print(f"Building index from docs directory: {docs_dir}")
            build_index(docs_dir, store_dir)

        if not store_dir.exists():
            print(
                f"ERROR: Vector store directory {store_dir} does not exist after build attempt")
            return []

        print(f"Loading vectorstore from {store_dir}...")
        vs = Chroma(persist_directory=str(store_dir),
                    embedding_function=_embedder())

        # Check collection stats
        try:
            collection_count = vs._collection.count()
            print(f"Collection contains {collection_count} documents")
            if collection_count == 0:
                print("ERROR: Vectorstore is empty!")
                return []
        except Exception as e:
            print(f"Warning: Could not get collection count: {e}")

        print(f"Performing {'MMR' if mmr else 'similarity'} search...")

        if mmr:
            retriever = vs.as_retriever(
                search_type="mmr",
                search_kwargs={"k": k, "fetch_k": fetch_k,
                               "lambda_mult": lambda_mult},
            )
            docs = retriever.get_relevant_documents(query)
        else:
            docs = vs.similarity_search(query, k=k)

        print(f"Raw search returned {len(docs)} documents")

        if docs:
            print("Sample results:")
            for i, doc in enumerate(docs[:3]):
                print(f"  Doc {i+1}: {doc.page_content[:100]}...")
                print(f"           Metadata: {doc.metadata}")

        # Post-dedup by normalized text
        snippets = _dedup_texts([d.page_content[:1200] for d in docs])[:k]

        print(f"After dedup and truncation: {len(snippets)} snippets")
        print(f"=== END RAG SEARCH ===\n")

        return snippets

    except Exception as e:
        print(f"ERROR in rag_search: {e}")
        import traceback
        traceback.print_exc()
        return []
