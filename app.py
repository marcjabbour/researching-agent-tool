from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from nodes.intent_detection import AppState, intent_detection_node
from nodes.web_search import web_search_node
from nodes.response_formatter import response_formatter_node

# Load environment variables
load_dotenv()

def create_app() -> StateGraph:
    """
    Create and configure the Langgraph application.
    """
    # Create the state graph
    workflow = StateGraph(AppState)

    # Add nodes: Intent Detection -> Web Search -> Response Formatter
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("response_formatter", response_formatter_node)

    # Set the entry point
    workflow.set_entry_point("intent_detection")

    # Simple linear flow: Intent Detection -> Web Search -> Response Formatter -> END
    workflow.add_edge("intent_detection", "web_search")
    workflow.add_edge("web_search", "response_formatter")
    workflow.add_edge("response_formatter", END)

    return workflow.compile()

def run_query(query: str) -> AppState:
    """
    Run a query through the Langgraph workflow.
    """
    app = create_app()

    initial_state = AppState(
        query=query,
        intent="unknown",
        confidence=0.0,
        extras={},
        processed=False,
        search_query="",
        search_results=[],
        final_response=""
    )

    result = app.invoke(initial_state)
    return result

if __name__ == "__main__":
    # Example usage
    test_query = "Generate a memo for investing in Perplexity"
    result = run_query(test_query)
    print(f"Query: {result['query']}")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Final Response: {result['final_response']}")
    print(f"Search Query Used: {result['search_query']}")