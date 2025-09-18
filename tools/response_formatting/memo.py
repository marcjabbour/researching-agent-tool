from typing import List, Dict, Any

def _format_memo_response(tavily_answer: str, search_results: List[Dict[str, Any]]) -> str:
    """Format response for investment memo queries - analytical and detailed."""
    if tavily_answer:
        sources = []
        for result in search_results[:6]:
            if result.get("title") and result.get("url"):
                sources.append(f"• {result['title']} ({result['url']})")

        sources_text = "\n".join(sources) if sources else ""
        memo_response = f"Investment Analysis:\n\n{tavily_answer}\n\nInformation Sources:\n{sources_text}" if sources_text else f"Investment Analysis:\n\n{tavily_answer}"
        return memo_response
    elif search_results:
        return f"Investment Analysis based on available data:\n\n{search_results[0].get('content', '')[:500]}...\n\nPrimary Source: {search_results[0].get('title', 'Unknown')}"
    else:
        return "Insufficient information available to provide investment analysis."