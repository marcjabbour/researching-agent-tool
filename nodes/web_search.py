import os
from typing import TypedDict, Dict, Any, List
from tavily import TavilyClient
from tools.intent_identifying.intents_data import INTENT
from tools.web_searching.helpers import _prepare_search_query, _get_search_params

class AppState(TypedDict):
    query: str
    intent: INTENT
    confidence: float
    extras: Dict[str, Any]
    processed: bool
    search_query: str
    search_results: List[Dict[str, Any]]
    final_response: str

def web_search_node(state: AppState) -> AppState:
    """
    Web Search Node - Uses Tavily to search for information based on intent and query.
    Handles all intents with appropriate search strategies.
    """
    intent = state["intent"]
    original_query = state["query"]
    entities = state.get("extras", {}).get("entities", [])

    # Prepare search query based on intent
    search_query = _prepare_search_query(intent, original_query, entities)

    try:
        # Initialize Tavily client
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        # Adjust search parameters based on intent
        search_params = _get_search_params(intent)

        # Perform search
        search_response = tavily_client.search(
            query=search_query,
            **search_params
        )

        # Extract relevant information
        results = search_response.get("results", [])

        # Format results for easier processing
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0)
            })

        return {
            **state,
            "search_query": search_query,
            "search_results": formatted_results,
            "extras": {
                **state.get("extras", {}),
                "tavily_answer": search_response.get("answer", ""),
                "search_successful": True
            }
        }

    except Exception as e:
        # Handle search errors gracefully
        return {
            **state,
            "search_query": search_query,
            "search_results": [],
            "extras": {
                **state.get("extras", {}),
                "search_error": str(e),
                "search_successful": False
            }
        }
    """
    Get search parameters optimized for each intent type.
    """
    base_params = {
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False
    }

    if intent == "fact":
        return {
            **base_params,
            "search_depth": "basic",
            "max_results": 3
        }
    elif intent == "profile":
        return {
            **base_params,
            "search_depth": "advanced",
            "max_results": 7
        }
    elif intent == "compare":
        return {
            **base_params,
            "search_depth": "advanced",
            "max_results": 8
        }
    elif intent == "memo":
        return {
            **base_params,
            "search_depth": "advanced",
            "max_results": 10
        }
    else:
        return {
            **base_params,
            "search_depth": "basic",
            "max_results": 5
        }