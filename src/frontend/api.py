"""
This file contains the API functions for the streamlit UI.

The easiest way to work with a Langgraph Server API in a frontend client is to use the langgraph_sdk: there are both python and javascript SDKs. Of course all of this can be done without the SDK by making requests via the requests or httpx libraries, but it's a convenient wrapper. In this example, we'll implement some of the core functions we need for a basic chat app. The complexity would grow if you want to add additional features such as human-in-the-loop.

To see the full API documentation, see your API docs at `http://localhost:2024/docs` once you've started the Langgraph Server.
"""
from langgraph_sdk import get_sync_client
from langgraph_sdk.schema import Command
from dotenv import load_dotenv
from typing import Iterator, Tuple, Literal, Dict, Any

load_dotenv()

# This can be a local or remote deployment URL, but it must point to a Langgraph Server
langgraph_api = "http://localhost:2024"

# Initialize the client that will handle all API requests to the Langgraph Server
client = get_sync_client(url=langgraph_api)

EventKind = Literal["ai_chunk", "interrupt", "tool", "done", "other"]


def get_assistants():
    response = client.assistants.search()
    return response


def create_thread(user_id: str):
    response = client.threads.create(
        metadata={
            "user_id": user_id,
        }
    )
    return response


def search_threads(user_id: str):
    response = client.threads.search(
        metadata={
            "user_id": user_id,
        }
    )
    return response


def delete_thread(thread_id: str):
    response = client.threads.delete(thread_id)
    return response


def delete_all_threads(user_id: str):
    threads = search_threads(user_id)
    for thread in threads:
        delete_thread(thread["thread_id"])


def get_thread_state(thread_id: str):
    response = client.threads.get_state(thread_id)
    return response


def run_thread_stream(assistant_id: str, thread_id: str, input: dict[str, Any]):
    """
    This function processes the raw stream from the graph, yielding a string that can be rendered in the UI.

    Args:
        assistant_id (str): The assistant ID
        thread_id (str): The thread ID
        input (dict[str, Any]): The input to the graph

    Yields:
        str: The processed response from the graph
    """
    for chunk in client.runs.stream(
        thread_id=thread_id,
        assistant_id=assistant_id,
        input=input,
        stream_mode="messages-tuple",
    ):

        # We're only interested in the messages event
        # You can add additional logic to handle other events such as metadata
        # Note that the payload of the chunk depends on the stream_mode
        if chunk.event == "messages":
            # yield chunk

            # We only want to yield AI messages
            # If you want to see the raw chunks, uncomment the `yield chunk` line above
            if chunk.data[0]["type"] == "AIMessageChunk":
                # If the AI message contains tool calls, we want to yield the tool call name and arguments
                if chunk.data[0]["tool_call_chunks"]:
                    tool_chunk = chunk.data[0]["tool_call_chunks"][0]
                    if tool_chunk["name"]:
                        yield tool_chunk["name"]
                    else:
                        yield tool_chunk["args"]
                # If the AI message does not contain tool calls, we want to yield the content
                else:
                    yield chunk.data[0]["content"]


def run_thread_events(
    assistant_id: str,
    thread_id: str,
    initial_input: Dict[str, Any] | None = None,
    resume_payload: Dict[str, Any] | None = None,
) -> Iterator[Tuple[EventKind, Any]]:
    kwargs = {"thread_id": thread_id,
              "assistant_id": assistant_id, "stream_mode": "updates"}
    if resume_payload is not None:
        # RESUME PATH
        print("DEBUG: Run thread with payload:", resume_payload)
        kwargs["command"] = Command(resume=resume_payload)
    else:
        # FIRST CALL PATH
        print("DEBUG: Starting fresh run with initial input:", initial_input)
        kwargs["input"] = initial_input or {}

    for chunk in client.runs.stream(**kwargs):
        if chunk.event != "updates":
            yield ("other", {"event": chunk.event, "data": chunk.data})
            continue

        data = chunk.data or {}
        if "__interrupt__" in data:
            items = data["__interrupt__"]
            if isinstance(items, list) and items:
                yield ("interrupt", items[0])   # {'value': {...}, 'id': '...'}
            else:
                yield ("interrupt", items)
            continue

        # surface AI text
        for node_name, node_payload in data.items():
            if isinstance(node_payload, dict):
                for m in node_payload.get("messages") or []:
                    if m.get("type") == "ai":
                        yield ("ai_chunk", m.get("content", ""))


async def main():
    """
    Convenience function to cleanup all threads for a user. You can use this to manage your Langgraph Server environment while you're testing and developing.
    """

    user_id = "valdrin"
    delete_all_threads(user_id)


if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()

    asyncio.run(main())
