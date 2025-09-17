from __future__ import annotations
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph, END
from typing import Any, Dict, List, Optional, TypedDict
from pathlib import Path
import warnings
import re
import argparse
import os


try:
    from langchain_chroma import Chroma  # pip install langchain-chroma
except Exception:
    from langchain_community.vectorstores import Chroma

warnings.filterwarnings("ignore", category=SyntaxWarning, module="chromadb")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDINGS_MODEL = os.getenv(
    "OPENAI_EMBEDDINGS_MODEL", "text-embedding-3-small")
INDEX_DIR = Path(os.getenv("VECTORSTORE_PATH", "./vectorstore_min"))
ALLOWED_EXTS = {".md", ".txt", ".json", ".yaml", ".yml"}
ENDPOINTS_HELP_URL = os.getenv(
    "AEB_ENDPOINTS_HELP_URL", "<link-zu-Erläuterungen-für-Endpoints>")


def _embedder() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=OPENAI_EMBEDDINGS_MODEL)


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1", errors="ignore")
        except Exception:
            return None


def build_index(docs_dir: str, store_dir: Path = INDEX_DIR):
    root = Path(docs_dir)
    store_dir.mkdir(parents=True, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150)
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []

    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in ALLOWED_EXTS:
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


def rag_search(query: str, k: int = 4, store_dir: Path = INDEX_DIR) -> List[str]:
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


URL_RE = re.compile(r"https?://[^\s]+", re.I)


def parse_endpoints(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not text:
        return out
    urls = URL_RE.findall(text)
    # TODO: Dont assume order
    if len(urls) == 2:
        out["test_endpoint"] = urls[0]
        out["prod_endpoint"] = urls[1]
        return out
    # Look for keywords
    for line in text.splitlines():
        low = line.lower()
        m = URL_RE.search(line)
        if not m:
            continue
        if "test" in low:
            out["test_endpoint"] = m.group(0)
        if "prod" in low or "production" in low:
            out["prod_endpoint"] = m.group(0)
    return out


def parse_client_ident(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"clientIdentCode\s*[:=]\s*([A-Za-z0-9_\-]+)", text, re.I)
    if m:
        return m.group(1)
    m = re.search(r"mandant(?:enname)?\s*[:=]\s*([A-Za-z0-9_\-]+)", text, re.I)
    if m:
        return m.group(1)
    tokens = re.findall(r"\b[A-Z0-9_]{3,12}\b", text)
    return tokens[0] if tokens else None


def parse_wsm_user(text: str) -> Optional[bool]:
    if not text:
        return None
    low = text.strip().lower()
    if any(w in low for w in ["yes", "ja", "y", "configured", "done", "gesetzt", "vorhanden"]):
        return True
    if any(w in low for w in ["no", "nein", "n", "not yet", "nicht", "fehlt"]):
        return False
    return None


def parse_yes_no(text: str) -> Optional[bool]:
    if not text:
        return None
    low = text.strip().lower()

    if low in {"yes", "y", "ja", "j", "1", "true", "ok"}:
        return True
    if low in {"no", "n", "nein", "0", "false"}:
        return False

    if any(word in low for word in ["ja", "yes", "okay", "klar"]):
        return True
    if any(word in low for word in ["nein", "no", "nicht"]):
        return False

    return None


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=OPENAI_MODEL, temperature=0.2)


class State(TypedDict, total=False):
    started: bool                     # whether user agreed to start
    completed: bool                   # whether the initial flow is completed
    # {test_endpoint, prod_endpoint, clientIdentCode, wsm_user_configured}
    provisioning: Dict[str, Any]
    user_input: Optional[str]
    messages: List[Dict[str, str]]
    rag_snippets: List[str]


def intro_node(state: State) -> State:
    state.setdefault("messages", [])
    state.setdefault("provisioning", {})
    state["messages"].append({
        "role": "assistant",
        "meta": "intro",
        "content": (
            "Hallo! Ich bin dein **AEB API Mapping Assistant**. "
            "Ich helfe dir dabei, die **TCM Screening API** sauber in dein System zu integrieren.\n\n"
            "Möchtest du mit der Integration beginnen? (Ja/Nein)"
        )
    })
    return state


def ask_endpoints_node(state: State) -> State:
    print(
        f"DEBUG: ask_endpoints_node called with user_input='{state.get('user_input', '')}'")
    prov = state.setdefault("provisioning", {})
    ui = state.get("user_input") or ""

    found = parse_endpoints(ui)

    # If exactly one URL and no prior endpoints, accept as test by default
    single = URL_RE.findall(ui)
    if single and len(single) == 1 and not found and not (prov.get("test_endpoint") or prov.get("prod_endpoint")):
        found = {"test_endpoint": single[0]}

    prov.update(found)

    if not (prov.get("test_endpoint") or prov.get("prod_endpoint")):
        new_message = {
            "role": "assistant",
            "content": (
                "Bitte zuerst die **AEB RZ Endpoints** angeben (mindestens eine URL). "
                "Diese sind für die API-Integration erforderlich.\n"
                f"Hinweis: {ENDPOINTS_HELP_URL}\n\n"
                "Format:\n"
                "Test: https://...\n"
                "Prod:  https://..."
            )
        }
        print(
            f"DEBUG: Adding endpoints request message: {new_message['content'][:50]}...")
        state["messages"].append(new_message)
        print(
            f"DEBUG: ask_endpoints_node returning state with {len(state['messages'])} messages")
        print(
            f"DEBUG: Last message in state: {state['messages'][-1]['content'][:50]}...")
        return state

    # If we get here, we have at least one endpoint
    lines = []
    if prov.get("test_endpoint"):
        lines.append(f"- Test: {prov['test_endpoint']}")
    if prov.get("prod_endpoint"):
        lines.append(f"- Prod:  {prov['prod_endpoint']}")
    if len(lines) == 1:
        lines.append(
            "Hinweis: Den zweiten Endpoint (Test/Prod) können Sie später ergänzen.")

    confirmation_message = {
        "role": "assistant",
        "content": "Danke! Endpoints erfasst:\n" + "\n".join(lines)
    }
    state["messages"].append(confirmation_message)

    # Ask for client code after you get the URL
    state["user_input"] = ""  # Clear input for next step
    client_state = ask_client_node(state)

    print(
        f"DEBUG: ask_endpoints_node completed and proceeded to client question")
    return client_state


def ask_client_node(state: State) -> State:
    prov = state.setdefault("provisioning", {})
    ui = state.get("user_input") or ""

    if not prov.get("clientIdentCode"):
        guess = parse_client_ident(ui)
        if guess:
            prov["clientIdentCode"] = guess

    if not prov.get("clientIdentCode"):
        state["messages"].append({
            "role": "assistant",
            "content": (
                "2) **Mandantenname (clientIdentCode)**:\n"
                "- Für jeden Kunden steht ein eigener Mandant zur Verfügung.\n"
                "Bitte teilen Sie Ihren **clientIdentCode** mit (z. B. ACME01).\n\n"
                "Format: `clientIdentCode=ACME01` oder `Mandant: ACME01`"
            )
        })
        return state

    # If we get here, we have the client code. Confirm and go to the WSM question
    state["messages"].append({
        "role": "assistant",
        "content": f"Danke! Mandant erfasst: clientIdentCode={prov['clientIdentCode']}"
    })

    state["user_input"] = ""  # Clear input for next step
    wsm_state = ask_wsm_node(state)
    return wsm_state


def ask_wsm_node(state: State) -> State:
    prov = state.setdefault("provisioning", {})
    ui = state.get("user_input") or ""

    if "wsm_user_configured" not in prov:
        guess = parse_wsm_user(ui)
        if guess is not None:
            prov["wsm_user_configured"] = guess

    if "wsm_user_configured" not in prov:
        state["messages"].append({
            "role": "assistant",
            "content": (
                "3) **WSM Benutzer für Authentifizierung**:\n"
                "- Zusätzlich zum Mandanten gibt es einen **technischen WSM-Benutzer** inkl. Passwort für die API-Anbindung.\n"
                "Ist dieser Benutzer bereits eingerichtet? (Ja/Nein)"
            )
        })
        return state

    # If we get here, we have the WSM answer. Confirm and proceed to guide
    yn = "Ja" if prov["wsm_user_configured"] else "Nein"
    state["messages"].append(
        {"role": "assistant", "content": f"WSM-Benutzer vorhanden: {yn}."})

    # Immediately proceed to generate the guide
    state["user_input"] = ""  # Clear input for next step
    guide_state = guide_use_cases_node(state)
    return guide_state


def guide_use_cases_node(state: State) -> State:
    prov = state.get("provisioning", {})
    snippets = rag_search(
        "AEB screening API endpoints auth clientIdentCode suppressLogging screeningLogEntry batch 100", k=3
    )
    llm = get_llm()

    sys = SystemMessage(content=(
        "Du bist ein AEB-Trade-Compliance Onboarding-Assistent. "
        "Antworte präzise auf Deutsch, stichpunktartig, ohne Marketingfloskeln."
    ))
    human = HumanMessage(content=f"""
Erzeuge eine kurze Anleitung für die Erst-Integration der Sanktionslistenprüfung.

Kontext:
- Test-Endpoint: {prov.get('test_endpoint') or '<fehlt>'}
- Prod-Endpoint: {prov.get('prod_endpoint') or '<fehlt>'}
- Mandant (clientIdentCode): {prov.get('clientIdentCode') or '<fehlt>'}
- WSM Benutzer vorhanden: {('Ja' if prov.get('wsm_user_configured') else 'Nein' if prov.get('wsm_user_configured') is not None else '<unbekannt>')}

Bitte decke ab:
1) Formate (JSON/REST).
2) Prüfrelevante Objekte (Stammdaten einzeln/Bulk ≤100; Transaktionen).
3) Felder: Pflicht / prüfrelevant / optional (Name, Adresse, eindeutige Referenz, Adresstyp).
4) Trigger: Anlage/Änderung Stammdaten & Transaktionen; periodische Batchprüfung (z. B. 1×/Monat).
5) Drei Anbindungsvarianten:
   a) Einseitige Übergabe via screenAddresses (Response → Treffer/Nichttreffer; E-Mail an TCM-Empfänger; manuelles (Ent-)Sperren).
   b) Übergabe + regelmäßige Nachprüfung mit suppressLogging=true (z. B. alle 60 Min.) zur automatischen Entsperrung nach Good-Guy.
   c) Optionaler Deep-Link via screeningLogEntry (temporärer Link; Button/Menu im Partnersystem).
6) Response-Szenarien:
   - matchFound=true & wasGoodGuy=false → Treffer → (optional) Sperre/Benachrichtigung.
   - matchFound=false & wasGoodGuy=false → kein Treffer → keine Aktion.
   - matchFound=false & wasGoodGuy=true → kein Treffer (bereits Good-Guy) → keine Aktion.

Berücksichtige (falls vorhanden) Doku-Auszüge:
{snippets if snippets else '[keine RAG-Snippets gefunden]'}
""")
    resp = llm.invoke([sys, human])
    state["messages"].append({"role": "assistant", "content": resp.content})

    # Mark the flow as completed
    state["completed"] = True

    return state


def qa_mode_node(state: State) -> State:
    """Handle free-flowing Q&A after the initial flow is completed."""
    prov = state.get("provisioning", {})
    user_question = state.get("user_input", "")

    # Search for relevant information with more specific terms
    print(f"DEBUG QA: User question: {user_question}")
    snippets = rag_search(
        f"screening request example JSON REST API {user_question}", k=5)
    print(f"DEBUG QA: Found {len(snippets)} snippets from RAG")

    llm = get_llm()

    # Build context from provisioning data
    context_info = []
    if prov.get("test_endpoint"):
        context_info.append(f"Test-Endpoint: {prov['test_endpoint']}")
    if prov.get("prod_endpoint"):
        context_info.append(f"Prod-Endpoint: {prov['prod_endpoint']}")
    if prov.get("clientIdentCode"):
        context_info.append(
            f"Mandant (clientIdentCode): {prov['clientIdentCode']}")
    if "wsm_user_configured" in prov:
        wsm_status = "Ja" if prov["wsm_user_configured"] else "Nein"
        context_info.append(f"WSM-Benutzer: {wsm_status}")

    context_str = "\n".join(
        context_info) if context_info else "Keine Konfigurationsdaten verfügbar."

    sys = SystemMessage(content=(
        "Du bist ein AEB-Trade-Compliance API-Experte. "
        "Beantworte Fragen zur TCM Screening API präzise und hilfreich auf Deutsch. "
        "Nutze IMMER die verfügbaren Dokumentationsauszüge und Konfigurationsdaten. "
        "Wenn Dokumentation verfügbar ist, basiere deine Antwort darauf und nicht auf allgemeinem Wissen."
    ))

    snippets_text = "\n\n".join([f"Dokument {i+1}:\n{snippet}" for i, snippet in enumerate(
        snippets)]) if snippets else '[Keine passenden Dokumentationsauszüge gefunden]'

    human = HumanMessage(content=f"""
Benutzerfrage: {user_question}

Verfügbare Konfiguration:
{context_str}

Verfügbare Dokumentationsauszüge:
{snippets_text}

Beantworte die Frage basierend auf den verfügbaren Informationen. 
WICHTIG: Nutze die Dokumentationsauszüge als primäre Quelle und verwende die korrekte API-Struktur aus der Dokumentation.
""")

    resp = llm.invoke([sys, human])
    state["messages"].append({"role": "assistant", "content": resp.content})

    return state


# TODO: Currently the routing is handled with the run_step function but
#  maybe it would be better to model this in the graph with conditional edges?
def build_graph():
    g = StateGraph(State)
    g.add_node("intro", intro_node)
    g.add_node("ask_endpoints", ask_endpoints_node)
    g.add_node("ask_client", ask_client_node)
    g.add_node("ask_wsm", ask_wsm_node)
    g.add_node("guide_use_cases", guide_use_cases_node)

    g.set_entry_point("intro")

    # Each node ends immediately (driver (run_steps) decides next)
    g.add_edge("intro", END)
    g.add_edge("ask_endpoints", END)
    g.add_edge("ask_client", END)
    g.add_edge("ask_wsm", END)
    g.add_edge("guide_use_cases", END)
    return g.compile()


APP = build_graph()

# Router


def run_step(state: State, user_input: Optional[str]) -> State:
    state = dict(state) if state else {}
    state.setdefault("messages", [])
    state.setdefault("provisioning", {})
    state.setdefault("started", False)
    state.setdefault("completed", False)
    state["user_input"] = user_input or ""

    prov = state["provisioning"]

    # TODO: Remove debug
    print(
        f"DEBUG: started={state['started']}, completed={state['completed']}, user_input='{user_input}'")
    print(f"DEBUG: messages count={len(state['messages'])}")
    print(f"DEBUG: provisioning={prov}")

    # If flow is completed, handle as Q&A
    if state.get("completed", False):
        print("DEBUG: Flow completed, handling as Q&A")
        return qa_mode_node(state)

    # If no intro yet, show intro and stop
    if not any(m.get("meta") == "intro" for m in state["messages"]):
        print("DEBUG: No intro found, showing intro")
        return intro_node(state)

    # If user hasn't started yet, interpret their answer (yes/no)
    if not state["started"]:
        print("DEBUG: User hasn't started yet, parsing yes/no")
        yn = parse_yes_no(state.get("user_input", ""))
        print(f"DEBUG: Parsed yes/no result: {yn}")
        if yn is None:
            # Ask again, explicitly
            state["messages"].append({
                "role": "assistant",
                "content": "Möchtest du mit der Integration beginnen? Bitte antworte mit **Ja** oder **Nein**."
            })
            return state
        if yn is False:
            state["messages"].append({
                "role": "assistant",
                "content": "Alles klar. Sag einfach **Ja**, wenn du bereit bist zu starten."
            })
            return state
        # Yes → mark started and proceed to endpoints question
        print("DEBUG: User said yes, setting started=True and proceeding to endpoints")
        state["started"] = True
        # Clear the user input so it doesn't interfere with the next step
        state["user_input"] = ""
        return ask_endpoints_node(state)

    print("DEBUG: User has started, checking gates")
    # From here on, we're in the integration flow.
    # Gate 1: Endpoints (require at least one URL)
    if not (prov.get("test_endpoint") or prov.get("prod_endpoint")):
        print("DEBUG: No endpoints, asking for endpoints")
        return ask_endpoints_node(state)

    # Gate 2: clientIdentCode
    if not prov.get("clientIdentCode"):
        print("DEBUG: No client code, asking for client")
        return ask_client_node(state)

    # Gate 3: WSM user yes/no
    if "wsm_user_configured" not in prov:
        print("DEBUG: No WSM info, asking for WSM")
        return ask_wsm_node(state)

    # All good → guide
    print("DEBUG: All gates passed, generating guide")
    return guide_use_cases_node(state)


def interactive():
    print("=" * 60)
    print("AEB API Onboarding (OpenAI + Chroma, step-by-step)")
    print("=" * 60)
    state: State = {}
    state = run_step(state, user_input=None)
    print(f"\nAssistant: {state['messages'][-1]['content']}")

    while True:
        user = input("\nYou: ")
        previous_message_count = len(state.get("messages", []))
        state = run_step(state, user)

        # Get the new messages that might come from run_step
        new_messages = state["messages"][previous_message_count:]

        print(f"\nDEBUG: Final state has {len(state['messages'])} messages")
        print(f"DEBUG: Added {len(new_messages)} new messages in this step")

        # show all new messages
        for i, message in enumerate(new_messages):
            if i == 0:
                print(f"\nAssistant: {message['content']}")
            else:
                # Add a small separator for subsequent messages
                print(f"\n{message['content']}")

        if (state.get("completed", False) and
                any("Anleitung" in msg.get("content", "") for msg in new_messages)):
            print("\n" + "="*60)
            print("✅ Integration-Setup abgeschlossen!")
            print("Sie können jetzt weitere Fragen zur TCM Screening API stellen.")
            print("="*60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--build-index", help="Directory with docs (md/txt/json/yaml) to index for RAG", default=None)
    parser.add_argument("--run", action="store_true",
                        help="Start interactive chat after building (or standalone).")
    parser.add_argument("--index-only", action="store_true",
                        help="Build the index and exit.")
    args = parser.parse_args()

    if args.build_index:
        build_index(args.build_index, INDEX_DIR)
        if args.index_only:
            print("Index built. Start chat with: uv run langgraph_assistant.py --run")
            raise SystemExit(0)

    if args.run or not args.build_index:
        interactive()
        if args.index_only and not args.run:
            print("Index built. Start chat with: uv run langgraph_assistant.py --run")
        if args.index_only and not args.run:
            interactive()
            print("Index built. Start chat with: uv run langgraph_assistant.py --run")
            raise SystemExit(0)

    if args.run or not args.build_index:
        interactive()
        if args.index_only and not args.run:
            print("Index built. Start chat with: uv run langgraph_assistant.py --run")
        if args.index_only and not args.run:
            interactive()
            print("Index built. Start chat with: uv run langgraph_assistant.py --run")
            raise SystemExit(0)

    if args.run or not args.build_index:
        interactive()
