def _prepare_search_query(intent: str, query: str, entities: List[Dict[str, Any]]) -> str:
    """
    Prepare search query based on intent and extracted entities.
    """
    entity_names = [entity.get("name", "") for entity in entities if entity.get("name")]

    if intent == "fact":
        # For facts, keep it simple and direct
        return query
    elif intent == "profile":
        # For profiles, add context for comprehensive information
        if entity_names:
            return f"{query} profile background information about {' '.join(entity_names)}"
        return f"{query} profile background information"
    elif intent == "compare":
        # For comparisons, ensure we're looking for comparative information
        return f"{query} comparison analysis differences similarities"
    elif intent == "memo":
        # For memos, focus on investment-relevant information
        return f"{query} investment analysis market opportunity financials"
    else:
        # Unknown intent, use original query
        return query

def _get_search_params(intent: str) -> Dict[str, Any]:
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