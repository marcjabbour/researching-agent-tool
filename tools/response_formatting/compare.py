from typing import List, Dict, Any

def _format_compare_response(search_results: List[Dict[str, Any]], depth: str = "standard") -> str:
    """Format response for comparison queries - structured comparison."""
    if not search_results:
        return "I couldn't find sufficient information to make a meaningful comparison."

    if depth == "quick":
        content = search_results[0].get("content", "")[:300]
        return f"Comparison Summary:\n\n{content}...\n\nSource: {search_results[0].get('title', 'Unknown')}"
    else:
        num_sources = 3 if depth == "standard" else 6
        content_pieces = []
        for result in search_results[:num_sources]:
            content = result.get("content", "")[:350]
            if content:
                content_pieces.append(content)

        combined_content = " ".join(content_pieces)
        sources = [f"• {r.get('title', 'Unknown')}" for r in search_results[:num_sources]]
        sources_text = "\n".join(sources)
        return f"Comparison Analysis:\n\n{combined_content}\n\nBased on:\n{sources_text}"