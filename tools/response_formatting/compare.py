from typing import List, Dict, Any

def _format_compare_response(tavily_answer: str, search_results: List[Dict[str, Any]]) -> str:
    """Format response for comparison queries - structured comparison."""
    if tavily_answer:
        sources = []
        for result in search_results[:5]:
            if result.get("title") and result.get("url"):
                sources.append(f"• {result['title']}")

        sources_text = "\n".join(sources) if sources else ""
        return f"{tavily_answer}\n\nComparison based on:\n{sources_text}" if sources_text else tavily_answer
    elif search_results:
        return f"Based on available information, here's what I found for your comparison:\n\n{search_results[0].get('content', '')[:400]}...\n\nSource: {search_results[0].get('title', 'Unknown')}"
    else:
        return "I couldn't find sufficient information to make a meaningful comparison."