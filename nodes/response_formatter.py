from typing import TypedDict, Dict, Any, List
from tools.intent_identifying.intents_data import INTENT
from tools.response_formatting.fact import _format_fact_response
from tools.response_formatting.profile import _format_profile_response
from tools.response_formatting.compare import _format_compare_response
from tools.response_formatting.memo import _format_memo_response
from tools.response_formatting.default import _format_default_response

class AppState(TypedDict):
    query: str
    intent: INTENT
    confidence: float
    extras: Dict[str, Any]
    processed: bool
    search_query: str
    search_results: List[Dict[str, Any]]
    final_response: str

def response_formatter_node(state: AppState) -> AppState:
    """
    Response Formatter Node - Synthesizes search results into intent-specific responses.
    """
    intent = state["intent"]
    search_results = state.get("search_results", [])
    tavily_answer = state.get("extras", {}).get("tavily_answer", "")
    search_successful = state.get("extras", {}).get("search_successful", False)

    if not search_successful:
        # Handle search failure
        error_msg = state.get("extras", {}).get("search_error", "Unknown error")
        final_response = f"I encountered an error while searching: {error_msg}"
    else:
        # Format response based on intent
        final_response = _format_response_by_intent(
            intent, tavily_answer, search_results
        )

    return {
        **state,
        "final_response": final_response,
        "processed": True
    }

def _format_response_by_intent(intent: str, tavily_answer: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Format response based on detected intent.
    """
    if intent == "fact":
        return _format_fact_response(tavily_answer, search_results)
    elif intent == "profile":
        return _format_profile_response(tavily_answer, search_results)
    elif intent == "compare":
        return _format_compare_response(tavily_answer, search_results)
    elif intent == "memo":
        return _format_memo_response(tavily_answer, search_results)
    else:
        return _format_default_response(tavily_answer, search_results)
