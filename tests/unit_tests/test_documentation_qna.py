#!/usr/bin/env python3
"""
Test script for the documentation Q&A subgraph.

This script demonstrates how to use the documentation Q&A subgraph
to answer questions about the AEB TCM Screening API documentation.
"""

from langchain_core.messages import HumanMessage
from agent.documentation_qna_graph.graph import documentation_qna_graph


def test_documentation_qna():
    """Test the documentation Q&A subgraph with sample questions."""

    print("🧪 Testing Documentation Q&A Subgraph")
    print("=" * 50)

    # Test questions about the API
    test_questions = [
        "Wie ist die Request-Struktur für screenAddresses aufgebaut?",
        "Was bedeutet der Parameter suppressLogging?",
        "Welche Response-Codes gibt es und was bedeuten sie?",
        "Wie implementiere ich eine Batch-Prüfung?",
        "Was ist der Unterschied zwischen matchFound und wasGoodGuy?"
    ]

    for i, question in enumerate(test_questions, 1):
        print(f"\n🔍 Test {i}: {question}")
        print("-" * 60)

        try:
            # Initialize the state
            initial_state = {
                "messages": [],
                "current_question": None,
                "search_results": None,
                "completed": False
            }

            # First run - should show welcome message
            result = documentation_qna_graph.invoke(initial_state)
            print("📝 Welcome Message:")
            if result.get("messages"):
                print(result["messages"][-1].content[:200] + "..." if len(
                    result["messages"][-1].content) > 200 else result["messages"][-1].content)

            # Second run - ask the question
            state_with_question = {
                **result,
                "messages": result.get("messages", []) + [HumanMessage(content=question)]
            }

            result = documentation_qna_graph.invoke(state_with_question)

            print(f"\n💬 Answer:")
            if result.get("messages"):
                # Get the last AI message (our answer)
                ai_messages = [msg for msg in result["messages"] if hasattr(
                    msg, 'content') and msg.__class__.__name__ == 'AIMessage']
                if ai_messages:
                    answer = ai_messages[-1].content
                    # Truncate for readability
                    print(answer[:500] + "..." if len(answer)
                          > 500 else answer)

            print(
                f"\n📊 Search Results Found: {len(result.get('search_results', []))}")

        except Exception as e:
            print(f"❌ Error testing question '{question}': {str(e)}")

        print("\n" + "="*60)


def test_interactive_mode():
    """Test interactive mode where user can ask multiple questions."""

    print("\n🤖 Interactive Documentation Q&A")
    print("Type 'quit' to exit")
    print("=" * 50)

    # Initialize state
    state = {
        "messages": [],
        "current_question": None,
        "search_results": None,
        "completed": False
    }

    # Show welcome message
    result = documentation_qna_graph.invoke(state)
    if result.get("messages"):
        print("\n🤖 Assistant:")
        print(result["messages"][-1].content)

    state = result

    while True:
        try:
            user_input = input("\n👤 Ihre Frage: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Auf Wiedersehen!")
                break

            if not user_input:
                continue

            # Add user message to state
            state["messages"] = state.get(
                "messages", []) + [HumanMessage(content=user_input)]

            # Process the question
            result = documentation_qna_graph.invoke(state)

            # Show the answer
            if result.get("messages"):
                ai_messages = [msg for msg in result["messages"] if hasattr(
                    msg, 'content') and msg.__class__.__name__ == 'AIMessage']
                if ai_messages:
                    print(f"\n🤖 Assistant:")
                    print(ai_messages[-1].content)

            # Update state for next iteration
            state = result

        except KeyboardInterrupt:
            print("\n👋 Auf Wiedersehen!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")


def main():
    """Main function to run the tests."""

    # Test with predefined questions
    test_documentation_qna()

    # Ask if user wants to try interactive mode
    try:
        user_choice = input(
            "\n🤔 Möchten Sie den interaktiven Modus testen? (j/n): ").strip().lower()
        if user_choice in ['j', 'ja', 'y', 'yes']:
            test_interactive_mode()
    except KeyboardInterrupt:
        print("\n👋 Auf Wiedersehen!")


if __name__ == "__main__":
    main()
