from typing import Dict, Any, List

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

def _get_search_params(intent: str, depth: str = "standard") -> Dict[str, Any]:
    """
    Get search parameters optimized for each intent type and depth level.
    Uses Exa-specific parameters for better research results.
    """
    # Base Exa search parameters
    base_params = {
        "type": "neural",  # Use neural search for better semantic understanding
        "use_autoprompt": True,  # Let Exa optimize the query
        "text": True,  # Get full text content
    }

    # Determine number of results based on depth and intent
    result_counts = {
        "quick": {"fact": 3, "profile": 4, "compare": 5, "memo": 6},
        "standard": {"fact": 5, "profile": 8, "compare": 10, "memo": 12},
        "comprehensive": {"fact": 8, "profile": 15, "compare": 20, "memo": 25}
    }

    num_results = result_counts.get(depth, result_counts["standard"]).get(intent, 8)

    params = {
        **base_params,
        "num_results": num_results,
    }

    # Add intent-specific parameters
    if intent == "fact":
        params.update({
            "category": "company",  # Focus on authoritative sources
            "start_published_date": "2020-01-01",  # Recent information
        })
    elif intent == "profile":
        params.update({
            "category": "company",
            "include_domains": ["crunchbase.com", "bloomberg.com", "reuters.com", "forbes.com"],
        })
    elif intent == "compare":
        params.update({
            "category": "company",
            "start_published_date": "2022-01-01",  # More recent for comparisons
        })
    elif intent == "memo":
        params.update({
            "category": "company",
            "include_domains": ["pitchbook.com", "crunchbase.com", "sec.gov", "bloomberg.com", "techcrunch.com"],
            "start_published_date": "2021-01-01",
        })

    return params