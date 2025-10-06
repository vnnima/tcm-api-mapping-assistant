#!/usr/bin/env python3
"""
Simple test script for the request validation subgraph
"""

from agent.request_validation_graph.graph import request_validation_graph, RequestValidationState


def test_request_validation():
    """Test the request validation subgraph with a sample request."""

    # Sample API request for testing
    sample_request = '''
    {
        "addresses": [
            {
                "name": "Test Company GmbH",
                "addressType": "entity",
                "street": "Hauptstraße 123",
                "pc": "10115",
                "city": "Berlin",
                "countryISO": "DE",
                "referenceId": "COMP-001"
            }
        ],
        "clientIdentCode": "TESTCLIENT",
        "threshold": 70
    }
    '''

    # Initial state
    initial_state = RequestValidationState(
        messages=[],
        user_request=sample_request.strip(),
        validation_results=None,
        syntax_valid=None,
        required_fields_present=None,
        field_quality_issues=None,
        improvement_suggestions=None,
        completed=False
    )

    print("🧪 Testing Request Validation Subgraph")
    print("=" * 50)
    print(f"📝 Sample Request:")
    print(sample_request)
    print()

    try:
        # Run the graph
        result = request_validation_graph.invoke(initial_state)

        print("✅ Graph execution completed!")
        print(f"📊 Completed: {result.get('completed', False)}")
        print(f"🔍 Syntax Valid: {result.get('syntax_valid', 'Unknown')}")
        print(
            f"📋 Required Fields Present: {result.get('required_fields_present', 'Unknown')}")

        if result.get('validation_results'):
            print("\n📋 Validation Results:")
            analysis = result['validation_results'].get(
                'analysis', 'No analysis available')
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)

        print("\n🎯 Test completed successfully!")

    except Exception as e:
        print(f"❌ Error during graph execution: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    test_request_validation()
