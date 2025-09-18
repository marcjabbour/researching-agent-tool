from typing import List, Dict, Any

def _format_default_response(tavily_answer: str, search_results: List[Dict[str, Any]]) -> str:
    """Default formatting for unknown intents."""
    if tavily_answer:
        sources = []
        for result in search_results[:3]:
            if result.get("title") and result.get("url"):
                sources.append(f"• {result['title']}")

        sources_text = "\n".join(sources) if sources else ""
        return f"{tavily_answer}\n\nSources:\n{sources_text}" if sources_text else tavily_answer
    elif search_results:
        top_result = search_results[0]
        content = top_result.get("content", "")
        if len(content) > 300:
            content = content[:300] + "..."
        return f"{content}\n\nSource: {top_result.get('title', 'Unknown')}"
    else:
        return "I couldn't find any relevant information for your query."