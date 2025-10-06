from langchain_core.tools import tool


@tool
def get_tcm_api_documentation_url():
    """If you need to point the user to the TCM Documentation, use this URL."""
    return "https://example.com/tcm-api-docs"
