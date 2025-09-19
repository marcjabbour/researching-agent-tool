import os
from typing import TypedDict, Dict, Any, List
from tavily import TavilyClient
from tools.intent_identifying.intents_data import INTENT
from tools.web_searching.helpers import _prepare_search_query
from tools.research_transparency.types import AppState
from tools.research_transparency.state_manager import ResearchStateManager

def web_search_node(state: AppState) -> AppState:
    """
    Web Search Node - Uses Tavily for quick fact searches.
    Designed for fact intent queries that need fast, concise answers.
    """
    intent = state["intent"]
    original_query = state["query"]

    # Log start of search phase
    state = ResearchStateManager.log_reasoning_step(
        state, "executing",
        f"Performing quick Tavily search for fact query: '{original_query}'"
    )

    try:
        # Initialize Tavily client
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        # Perform search with Tavily
        search_response = tavily.search(
            query=original_query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
            include_raw_content=False
        )

        # Extract the answer and top results
        answer = search_response.get("answer", "")
        results = search_response.get("results", [])

        # Format results for compatibility
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.5),
                "published_date": None,
                "author": None
            })

        # Log search success
        state = ResearchStateManager.log_reasoning_step(
            state, "extracting",
            f"Tavily search complete. Found answer: {answer[:100]}..." if answer else f"Found {len(formatted_results)} sources"
        )

        # Create final response using Tavily's answer
        if answer:
            final_response = answer
        elif formatted_results:
            # Fallback to first result content if no answer
            final_response = formatted_results[0].get("content", "")[:500] + "..."
        else:
            final_response = "No information found for the query."

        return {
            **state,
            "search_query": original_query,
            "search_results": formatted_results,
            "final_response": final_response,
            "processed": True,
            "extras": {
                **state.get("extras", {}),
                "search_successful": True,
                "tavily_answer": answer
            }
        }

    except Exception as e:
        # Handle search errors gracefully
        state = ResearchStateManager.log_reasoning_step(
            state, "executing",
            f"Tavily search failed: {str(e)}. Using fallback response."
        )

        return {
            **state,
            "search_query": original_query,
            "search_results": [],
            "final_response": f"Unable to retrieve information: {str(e)}",
            "processed": True,
            "extras": {
                **state.get("extras", {}),
                "search_error": str(e),
                "search_successful": False
            }
        }