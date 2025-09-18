from typing import List, Dict, Any

def _format_fact_response(tavily_answer: str, search_results: List[Dict[str, Any]]) -> str:
    """Format response for fact queries - concise and direct."""
    if tavily_answer:
        # For facts, keep it short and include 1-2 key sources
        sources = []
        for result in search_results[:2]:
            if result.get("title") and result.get("url"):
                sources.append(f"• {result['title']}")

        sources_text = "\n".join(sources) if sources else ""
        return f"{tavily_answer}\n\nSources:\n{sources_text}" if sources_text else tavily_answer
    elif search_results:
        # Fallback to first result, keep it brief
        top_result = search_results[0]
        content = top_result.get("content", "")
        if len(content) > 200:
            content = content[:200] + "..."
        return f"{content}\n\nSource: {top_result.get('title', 'Unknown')}"
    else:
        return "I couldn't find any relevant factual information for your query."