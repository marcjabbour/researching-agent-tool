from typing import List, Dict, Any

def _format_profile_response(tavily_answer: str, search_results: List[Dict[str, Any]]) -> str:
    """Format response for profile queries - comprehensive information."""
    if tavily_answer:
        # For profiles, include more sources for comprehensive view
        sources = []
        for result in search_results[:4]:
            if result.get("title") and result.get("url"):
                sources.append(f"• {result['title']} ({result['url']})")

        sources_text = "\n".join(sources) if sources else ""
        return f"{tavily_answer}\n\nSources:\n{sources_text}" if sources_text else tavily_answer
    elif search_results:
        # Combine multiple sources for richer profile
        content_pieces = []
        for result in search_results[:3]:
            content = result.get("content", "")
            if content and len(content) > 50:
                if len(content) > 300:
                    content = content[:300] + "..."
                content_pieces.append(f"• {content}")

        combined_content = "\n".join(content_pieces) if content_pieces else "Limited information available."
        return f"{combined_content}\n\nBased on multiple sources"
    else:
        return "I couldn't find comprehensive profile information for your query."