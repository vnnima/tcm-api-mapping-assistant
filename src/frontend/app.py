"""
Chat App for Langgraph Agents using Streamlit.

This is a basic chat app/UI for interacting with Langgraph Agents via the Langgraph Server API. The app allows you to connect any Langgraph agents to a web UI, manage conversations, stream responses, and more.

This is a great starting point for learning how to build a full-stack AI application.
"""
import json
import streamlit as st
from pathlib import Path
from api import (
    get_assistants,
    create_thread,
    search_threads,
    get_thread_state,
    delete_thread,
    run_thread_events,
)

#################################
# Session State Management
#################################


def initialize_session_state(user_id: str):
    """
    Initialize the session state with the user ID and other data we need to manage the chat app.
    """

    if "user_id" not in st.session_state:
        st.session_state.user_id = user_id

    if "assistants" not in st.session_state:
        assistants_list = get_assistants()
        st.session_state.assistants = {
            a["name"]: a["assistant_id"] for a in assistants_list
        }

    if "active_assistant_id" not in st.session_state:
        assistant_ids = list(st.session_state.assistants.values())
        st.session_state.active_assistant_id = assistant_ids[0] if assistant_ids else None

    if "thread_ids" not in st.session_state:
        st.session_state.thread_ids = []
        threads = search_threads(st.session_state.user_id)
        for thread in threads:
            st.session_state.thread_ids.append(thread["thread_id"])

    if "selected_thread_id" not in st.session_state:
        if st.session_state.thread_ids:
            st.session_state.selected_thread_id = st.session_state.thread_ids[-1]
        else:
            st.session_state.selected_thread_id = None

    if "thread_state" not in st.session_state:
        st.session_state.thread_state = {}

    if "pending_interrupt" not in st.session_state:
        st.session_state.pending_interrupt = None
    if "pending_payload" not in st.session_state:
        st.session_state.pending_payload = None

    if "is_resuming" not in st.session_state:
        st.session_state.is_resuming = False
    if "resume_payload" not in st.session_state:
        st.session_state.resume_payload = None

    # Generic rerun trigger for callbacks (avoid calling st.rerun() inside them)
    if "trigger_rerun" not in st.session_state:
        st.session_state.trigger_rerun = False


def create_new_thread(user_id: str):
    thread = create_thread(user_id)
    st.session_state.thread_ids.append(thread["thread_id"])
    st.session_state.thread_state = get_thread_state(thread["thread_id"])
    st.session_state.selected_thread_id = thread["thread_id"]
    st.session_state.trigger_rerun = True


def delete_thread_and_update_state(thread_id: str):
    delete_thread(thread_id)
    if thread_id in st.session_state.thread_ids:
        st.session_state.thread_ids.remove(thread_id)
    st.session_state.thread_state = {}
    # If we deleted the selected thread, pick a new one
    if st.session_state.thread_ids:
        st.session_state.selected_thread_id = st.session_state.thread_ids[-1]
    else:
        st.session_state.selected_thread_id = None
    st.session_state.trigger_rerun = True


initialize_session_state(user_id="valdrin")

# Perform deferred rerun if requested by a callback
if st.session_state.get("trigger_rerun", False):
    st.session_state.trigger_rerun = False
    st.rerun()


#################################
# Interrupt Handling
#################################

def handle_resume_if_needed():
    """
    If a resume is in progress, perform it (using Command(resume=...)),
    and then rerun to refresh the thread state and UI.
    """
    if not st.session_state.is_resuming:
        return

    resume_payload = st.session_state.resume_payload or {}

    # Clear interrupt BEFORE resuming so we don't gate the UI during the streaming pass
    st.session_state.pending_interrupt = None
    st.session_state.pending_payload = None
    st.session_state.is_resuming = False
    st.session_state.resume_payload = None

    with st.chat_message("assistant"):
        buffer = ""
        placeholder = st.empty()
        for kind, data in run_thread_events(
            st.session_state.active_assistant_id,
            st.session_state.selected_thread_id,
            initial_input=None,
            resume_payload=resume_payload,
        ):
            if kind == "ai_chunk":
                buffer += data or ""
                placeholder.markdown(buffer)
            elif kind == "interrupt":
                # New interrupt: stash & rerun so the controls show next run
                val = (data or {}).get(
                    "value", {}) if isinstance(data, dict) else {}
                st.session_state.pending_interrupt = data
                st.session_state.pending_payload = val
                st.rerun()
            elif kind == "done":
                break
            else:
                pass

    # After finishing resume streaming, rerun to refresh thread state & normal UI
    st.rerun()


def render_interrupt_controls_if_pending() -> bool:
    """
    Render interrupt controls (Continue + Ask) if an interrupt is pending.
    Returns True if controls were rendered (i.e., an interrupt is active).
    """
    if st.session_state.pending_interrupt is None:
        return False

    if not st.session_state.pending_payload:
        st.error("Interrupt payload is missing or invalid.")
        return False

    if st.session_state.pending_payload['type'] == "get_api_data":
        prompt_text = st.session_state.pending_payload[
            'prompt'] or "Bitte geben Sie Ihren Systemnamen, Prozess und bestehenden API-Metadaten an (z.B. JSON-Schema, XML-Beispiel, CSV-Struktur, OpenAPI/Swagger Definition)."
        st.info(f"**Interrupt**\n\n{prompt_text}")

        col = st.container()

        def _resume_with_api_data():
            system_name = st.session_state.get("system_name", "").strip()
            process = st.session_state.get("process", "").strip()
            api_metadata_file = st.session_state.get("api_metadata_file")

            if not system_name or not process or not api_metadata_file:
                st.error(
                    "Bitte füllen Sie alle Felder aus und laden Sie eine Datei hoch.")
                return

            project_root = Path(__file__).resolve().parents[2]
            api_data_dir = project_root / "api_data"
            api_data_dir.mkdir(parents=True, exist_ok=True)

            file_path = api_data_dir / api_metadata_file.name
            with open(file_path, "wb") as f:
                f.write(api_metadata_file.getvalue())

            api_metadata = file_path
            payload = {
                "system_name": system_name,
                "process": process,
                "api_metadata": api_metadata.as_posix(),
            }
            st.session_state.resume_payload = payload
            st.session_state.is_resuming = True
            st.session_state.trigger_rerun = True

        with col:
            st.text_input("Systemname:", key="system_name")
            st.text_input("Prozess:", key="process")
            st.file_uploader("Bestehende API-Metadaten hochladen:",
                             type=["json", "xml", "csv", "yaml", "txt"], key="api_metadata_file")
            st.button("Daten senden 💬", on_click=_resume_with_api_data)

        return True
    else:
        prompt_text = st.session_state.pending_payload[
            'prompt'] or "Eingabe benötigt: Drücken sie `weiter` oder stellen sie eine Frage."
        st.info(f"**Interrupt**\n\n{prompt_text}")

        col1, col2 = st.columns([1, 3])

        def _resume_continue():
            st.session_state.resume_payload = {"continue": True}
            st.session_state.is_resuming = True
            st.session_state.trigger_rerun = True

        with col1:
            st.button("Weiter ▶️", key="interrupt_continue",
                      on_click=_resume_continue)

        def _resume_question():
            q = st.session_state.get("interrupt_question_text", "")
            if q.strip():
                st.session_state.resume_payload = {"question": q.strip()}
                st.session_state.is_resuming = True
                st.session_state.trigger_rerun = True

        with col2:
            st.text_input("Frage stellen:", key="interrupt_question_text")
            st.button("Frage senden 💬", on_click=_resume_question)

        return True


#################################
# Sidebar
#################################

with st.sidebar:
    st.write("User ID: " + st.session_state.user_id)

    assistant = st.selectbox("Select Assistant", list(
        st.session_state.assistants.keys()))
    st.session_state.active_assistant_id = st.session_state.assistants.get(
        assistant)

    st.title("Conversations")
    st.caption("A TCM chatbot to assist with API mapping.")

    if st.button("Create New Conversation"):
        create_new_thread(user_id=st.session_state.user_id)

    if st.session_state.thread_ids:
        def _on_select_thread():
            st.session_state.thread_state = get_thread_state(
                st.session_state.selected_thread_id)

        # Ensure selected thread exists
        if (
            "selected_thread_id" not in st.session_state
            or st.session_state.selected_thread_id not in st.session_state.thread_ids
        ):
            # Use latest thread (last in list)
            st.session_state.selected_thread_id = st.session_state.thread_ids[-1]

        st.radio(
            "Select Conversation",
            options=st.session_state.thread_ids,
            format_func=lambda tid: tid[:8],
            key="selected_thread_id",
            on_change=_on_select_thread,
        )

    if st.button("Delete Conversation", type="primary"):
        if st.session_state.selected_thread_id:
            delete_thread_and_update_state(st.session_state.selected_thread_id)


#################################
# Main Chat Area
#################################

st.title(f"Chatting with {assistant}")

# 1) If we’re resuming, do it first (streams assistant + may set a new interrupt)
handle_resume_if_needed()

with st.chat_message("assistant"):
    st.markdown("Hallo! Ich bin dein **AEB API Mapping Assistant**. "
                "Ich helfe dir dabei, die **TCM Screening API** sauber in dein System zu integrieren.\n\n"
                "Möchtest du mit der Integration beginnen? (Ja/Nein)"
                )

# 2) Always load latest thread state and render full history (so it never “disappears”)
if st.session_state.selected_thread_id and st.session_state.selected_thread_id in st.session_state.thread_ids:
    st.session_state.thread_state = get_thread_state(
        st.session_state.selected_thread_id)

if st.session_state.thread_state:
    for message in st.session_state.thread_state["values"].get("messages", []):
        if message.get("type") == "tool":
            with st.expander(f"🛠️ {message.get('name', 'tool')} < RESULTS > "):
                try:
                    json_message = json.loads(message.get("content") or "{}")
                    st.json(json_message)
                except Exception:
                    st.write(message.get("content") or "")
        elif message.get("type") == "ai" and message.get("tool_calls"):
            with st.chat_message("ai"):
                first_call = message["tool_calls"][0]
                st.markdown(f"🛠️ {first_call.get('name', 'tool')} < CALL >")
                st.json(first_call.get("args", {}))
        else:
            with st.chat_message(message.get("type", "ai")):
                st.markdown(message.get("content") or "")
else:
    st.write("Create a new conversation to start chatting...")

# 3) If an interrupt is pending, show the controls *below the history*.
interrupt_active = render_interrupt_controls_if_pending()

# 4) Normal chat input is disabled while an interrupt is active
chat_disabled = interrupt_active
prompt = st.chat_input("Send a message...", disabled=chat_disabled)

if prompt and not interrupt_active:
    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant response and capture interrupts
    with st.chat_message("assistant"):
        buffer = ""
        placeholder = st.empty()
        for kind, data in run_thread_events(
            st.session_state.active_assistant_id,
            st.session_state.selected_thread_id,
            # FIRST call in a turn uses input=...
            initial_input={"messages": [prompt]},
            resume_payload=None,                   # ...not a resume command
        ):
            if kind == "ai_chunk":
                buffer += data or ""
                placeholder.markdown(buffer)
            elif kind == "interrupt":
                # Persist interrupt and rerun so the gate shows controls next run
                val = (data or {}).get(
                    "value", {}) if isinstance(data, dict) else {}
                st.session_state.pending_interrupt = data
                st.session_state.pending_payload = val
                st.rerun()
            elif kind == "done":
                break
            else:
                pass

    # Rerun to load updated thread_state (messages appended by server)
    st.rerun()

with st.expander("<DEBUG> Session State"):
    st.write(st.session_state)
