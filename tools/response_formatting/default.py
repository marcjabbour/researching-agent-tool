from typing import List, Dict, Any

def _format_default_response(search_results: List[Dict[str, Any]], depth: str = "standard") -> str:
    """Default formatting for unknown intents."""
    if not search_results:
        return "I couldn't find any relevant information for your query."

    top_result = search_results[0]
    content = top_result.get("content", "")

    if depth == "quick":
        content = content[:200] + "..." if len(content) > 200 else content
        return f"{content}\n\nSource: {top_result.get('title', 'Unknown')}"
    else:
        num_sources = 2 if depth == "standard" else 4
        sources = [f"• {r.get('title', 'Unknown')}" for r in search_results[:num_sources]]
        sources_text = "\n".join(sources)
        content = content[:400] + "..." if len(content) > 400 else content
        return f"{content}\n\nSources:\n{sources_text}"