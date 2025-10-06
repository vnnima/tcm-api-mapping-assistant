#!/usr/bin/env python3
"""
Test script for the error detection subgraph.

This script demonstrates how to use the error detection subgraph
to analyze API requests and error responses for common issues.
"""

from langchain_core.messages import HumanMessage
from agent.error_detection_graph.graph import error_detection_graph
import sys
import os

# Add the src directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def test_error_detection():
    """Test the error detection subgraph with sample error scenarios."""

    print("🔍 Testing Error Detection Subgraph")
    print("=" * 50)

    # Test scenarios with common API errors
    test_scenarios = [
        {
            "name": "Typo in field name",
            "input": '''REQUEST:
{
  "addresse": [
    {
      "name": "Test Company",
      "street": "Main Street 123"
    }
  ]
}

ERROR RESPONSE:
{
  "error": "Invalid field name",
  "code": 400
}'''
        },
        {
            "name": "Missing required field",
            "input": '''REQUEST:
{
  "addresses": [
    {
      "street": "Main Street 123"
    }
  ]
}

ERROR RESPONSE:
{
  "error": "Missing required field: name",
  "code": 400
}'''
        },
        {
            "name": "Missing clientIdentCode",
            "input": '''REQUEST:
{
  "addresses": [
    {
      "name": "Test Company",
      "street": "Main Street 123",
      "addressType": "COMPANY"
    }
  ]
}

ERROR RESPONSE:
{
  "error": "Missing clientIdentCode",
  "code": 400
}'''
        },
        {
            "name": "JSON syntax error",
            "input": '''REQUEST:
{
  "addresses": [
    {
      "name": "Test Company"
      "street": "Main Street 123"
    }
  ]
}

ERROR RESPONSE:
{
  "error": "JSON parse error",
  "code": 400
}'''
        },
        {
            "name": "Wrong data type",
            "input": '''REQUEST:
{
  "clientIdentCode": "TEST01",
  "addresses": [
    {
      "name": "Test Company",
      "street": "Main Street 123",
      "addressType": "COMPANY"
    }
  ],
  "suppressLogging": "true"
}

ERROR RESPONSE:
{
  "error": "Invalid type for suppressLogging, expected boolean",
  "code": 400
}'''
        }
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 Test {i}: {scenario['name']}")
        print("-" * 60)

        try:
            # Initialize the state
            initial_state = {
                "messages": [],
                "user_request": None,
                "error_response": None,
                "error_analysis": None,
                "detected_issues": None,
                "suggestions": None,
                "completed": False
            }

            # First run - should show welcome message
            result = error_detection_graph.invoke(initial_state)
            print("📝 Welcome Message:")
            if result.get("messages"):
                print(result["messages"][-1].content[:200] + "..." if len(
                    result["messages"][-1].content) > 200 else result["messages"][-1].content)

            # Second run - provide the error scenario
            state_with_error = {
                **result,
                "messages": result.get("messages", []) + [HumanMessage(content=scenario["input"])]
            }

            result = error_detection_graph.invoke(state_with_error)

            print(f"\n🔍 Error Analysis:")
            if result.get("messages"):
                # Get the last AI message (our analysis)
                ai_messages = [msg for msg in result["messages"] if hasattr(
                    msg, 'content') and msg.__class__.__name__ == 'AIMessage']
                if ai_messages:
                    analysis = ai_messages[-1].content
                    # Truncate for readability
                    print(analysis[:800] + "..." if len(analysis)
                          > 800 else analysis)

            print(f"\n📊 Detected Issues: {result.get('detected_issues', [])}")
            print(f"💡 Suggestions: {result.get('suggestions', [])}")

        except Exception as e:
            print(f"❌ Error testing scenario '{scenario['name']}': {str(e)}")

        print("\n" + "="*60)


def test_interactive_mode():
    """Test interactive mode where user can input their own errors."""

    print("\n🔍 Interactive Error Detection")
    print("Type 'quit' to exit")
    print("=" * 50)

    print("\n📋 Format Guidelines:")
    print("REQUEST:")
    print("{ your json request }")
    print()
    print("ERROR RESPONSE:")
    print("{ error response from server }")
    print()

    # Initialize state
    state = {
        "messages": [],
        "user_request": None,
        "error_response": None,
        "error_analysis": None,
        "detected_issues": None,
        "suggestions": None,
        "completed": False
    }

    # Show welcome message
    result = error_detection_graph.invoke(state)
    if result.get("messages"):
        print("\n🤖 Assistant:")
        print(result["messages"][-1].content)

    state = result

    while True:
        try:
            print("\n📝 Enter your API request and error response:")
            print("(You can paste multiple lines, press Enter twice when done)")

            lines = []
            while True:
                line = input()
                if line.strip() == "" and lines:
                    break
                if line.lower().strip() in ['quit', 'exit', 'q']:
                    print("👋 Auf Wiedersehen!")
                    return
                lines.append(line)

            user_input = "\n".join(lines).strip()

            if not user_input:
                continue

            # Add user message to state
            state["messages"] = state.get(
                "messages", []) + [HumanMessage(content=user_input)]

            # Process the error analysis
            result = error_detection_graph.invoke(state)

            # Show the analysis
            if result.get("messages"):
                ai_messages = [msg for msg in result["messages"] if hasattr(
                    msg, 'content') and msg.__class__.__name__ == 'AIMessage']
                if ai_messages:
                    print(f"\n🔍 Error Analysis:")
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

    # Test with predefined error scenarios
    test_error_detection()

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
