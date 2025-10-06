import streamlit as st
from api import get_thread_state, create_thread, delete_thread


def render_sidebar():
    global flag
    st.write("User ID: " + st.session_state.user_id)

    # Track previous assistant to detect changes
    previous_assistant = st.session_state.get("previous_assistant", None)

    assistant = st.selectbox("Select Assistant", sorted(list(
        st.session_state.assistants.keys())))
    st.session_state.active_assistant = assistant

    # Check if assistant changed
    if previous_assistant != assistant and previous_assistant is not None:
        # Assistant changed - clear current conversation, interrupts, and create new thread
        st.session_state.thread_state = {}
        st.session_state.pending_interrupt = None
        st.session_state.pending_payload = None
        st.session_state.is_resuming = False
        st.session_state.resume_payload = None
        _create_new_thread(user_id=st.session_state.user_id)
        st.session_state.trigger_rerun = True

    # Update the active assistant and track the previous one
    st.session_state.active_assistant_id = st.session_state.assistants.get(
        assistant)
    st.session_state.previous_assistant = assistant

    st.title("Conversations")
    st.caption("A TCM chatbot to assist with API mapping.")

    if st.button("Create New Conversation"):
        _create_new_thread(user_id=st.session_state.user_id)

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
            format_func=format_thread_name,
            key="selected_thread_id",
            on_change=_on_select_thread,
        )

    if st.button("Delete Conversation", type="primary"):
        if st.session_state.selected_thread_id:
            _delete_thread_and_update_state(
                st.session_state.selected_thread_id)


def format_thread_name(thread_id: str) -> str:
    """Format thread name for display in conversation selector."""
    # Find the thread object in our stored threads
    thread = next(
        (t for t in st.session_state.threads if t["thread_id"] == thread_id), None)

    if thread:
        # Try to use creation time if available
        if "created_at" in thread:
            try:
                import datetime
                # Assume created_at is an ISO string or timestamp
                if isinstance(thread["created_at"], str):
                    dt = datetime.datetime.fromisoformat(
                        thread["created_at"].replace("Z", "+00:00"))
                else:
                    dt = datetime.datetime.fromtimestamp(thread["created_at"])
                date_str = dt.strftime("%m/%d %H:%M")
                return f"{date_str} ({thread_id[:8]})"
            except (ValueError, TypeError, KeyError):
                pass

        # Try to use thread metadata for a better name
        if "metadata" in thread and thread["metadata"]:
            metadata = thread["metadata"]
            if "title" in metadata:
                return f"{metadata['title']} ({thread_id[:8]})"
            if "name" in metadata:
                return f"{metadata['name']} ({thread_id[:8]})"

    # Fallback to just the short ID
    return thread_id[:8]


def _create_new_thread(user_id: str):
    thread = create_thread(user_id)
    st.session_state.threads.append(thread)
    st.session_state.thread_ids.append(thread["thread_id"])
    st.session_state.thread_state = get_thread_state(thread["thread_id"])
    st.session_state.selected_thread_id = thread["thread_id"]
    # Clear any pending interrupts when creating new thread
    st.session_state.pending_interrupt = None
    st.session_state.pending_payload = None
    st.session_state.is_resuming = False
    st.session_state.resume_payload = None
    st.session_state.trigger_rerun = True


def _delete_thread_and_update_state(thread_id: str):
    delete_thread(thread_id)
    if thread_id in st.session_state.thread_ids:
        st.session_state.thread_ids.remove(thread_id)
    # Also remove from threads list
    st.session_state.threads = [
        t for t in st.session_state.threads if t["thread_id"] != thread_id]
    st.session_state.thread_state = {}
    # Clear any pending interrupts when deleting thread
    st.session_state.pending_interrupt = None
    st.session_state.pending_payload = None
    st.session_state.is_resuming = False
    st.session_state.resume_payload = None
    # If we deleted the selected thread, pick a new one
    if st.session_state.thread_ids:
        st.session_state.selected_thread_id = st.session_state.thread_ids[-1]
    else:
        st.session_state.selected_thread_id = None
    st.session_state.trigger_rerun = True
