from typing import List, Dict, Any

def _format_profile_response(search_results: List[Dict[str, Any]], depth: str = "standard") -> str:
    """Format response for profile queries - comprehensive information."""
    if not search_results:
        return "I couldn't find comprehensive profile information for your query."

    if depth == "quick":
        top_result = search_results[0]
        content = top_result.get("content", "")[:300]
        return f"{content}...\n\nSource: {top_result.get('title', 'Unknown')}"
    else:
        # Combine multiple sources for richer profile
        num_sources = 3 if depth == "standard" else 6
        content_pieces = []
        for result in search_results[:num_sources]:
            content = result.get("content", "")
            if content and len(content) > 50:
                if len(content) > 400:
                    content = content[:400] + "..."
                content_pieces.append(f"• {content}")

        sources = [f"• {r.get('title', 'Unknown')}" for r in search_results[:num_sources]]
        combined_content = "\n".join(content_pieces) if content_pieces else "Limited information available."
        sources_text = "\n".join(sources)
        return f"{combined_content}\n\nSources:\n{sources_text}"