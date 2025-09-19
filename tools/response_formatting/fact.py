from typing import List, Dict, Any

def _format_fact_response(search_results: List[Dict[str, Any]], depth: str = "standard") -> str:
    """Format response for fact queries - concise and direct."""
    if not search_results:
        return "I couldn't find any relevant factual information for your query."

    if depth == "quick":
        top_result = search_results[0]
        content = top_result.get("content", "")[:150]
        return f"{content}...\n\nSource: {top_result.get('title', 'Unknown')}"
    elif depth == "comprehensive":
        # Combine multiple sources for more complete answer
        facts = []
        for result in search_results[:4]:
            content = result.get("content", "")[:300]
            if content:
                facts.append(f"• {content}")

        sources = [f"• {r.get('title', 'Unknown')}" for r in search_results[:4]]
        facts_text = "\n".join(facts)
        sources_text = "\n".join(sources)
        return f"{facts_text}\n\nSources:\n{sources_text}"
    else:  # standard
        top_result = search_results[0]
        content = top_result.get("content", "")[:300]
        sources = [f"• {r.get('title', 'Unknown')}" for r in search_results[:2]]
        sources_text = "\n".join(sources)
        return f"{content}...\n\nSources:\n{sources_text}"