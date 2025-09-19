from typing import List, Dict, Any
import re

def _format_memo_response(search_results: List[Dict[str, Any]], depth: str = "standard") -> str:
    """Format response for investment memo queries - analytical and detailed based on depth."""
    
# Debug removed for cleaner output
    if not search_results:
        return "Insufficient information available to provide investment analysis."

    if depth == "quick":
        return _format_quick_memo(search_results)
    elif depth == "standard":
        return _format_standard_memo(search_results)
    elif depth == "comprehensive":
        return _format_comprehensive_memo(search_results)
    else:
        return _format_standard_memo(search_results)

def _format_quick_memo(search_results: List[Dict[str, Any]]) -> str:
    """Quick memo format - brief summary."""
    if not search_results:
        return "No information available."

    top_result = search_results[0]
    content = top_result.get("content", "")[:400]

    return f"Investment Analysis:\n\n{content}...\n\nSource: {top_result.get('title', 'Unknown')}"

def _format_standard_memo(search_results: List[Dict[str, Any]]) -> str:
    """Standard memo format - structured analysis."""
    if not search_results:
        return "No information available."

    # Extract key information from top results
    company_info = _extract_company_info(search_results[:4])
    financial_info = _extract_financial_info(search_results[:4])
    market_info = _extract_market_info(search_results[:4])

    sources = [f"• {r.get('title', 'Unknown')}" for r in search_results[:6] if r.get("title")]
    sources_text = "\n".join(sources)

    memo = f"""Investment Analysis:

Executive Summary:
{company_info}

Financial Overview:
{financial_info}

Market Position:
{market_info}

Sources:
{sources_text}"""

    return memo

def _format_comprehensive_memo(search_results: List[Dict[str, Any]]) -> str:
    """Comprehensive memo format - detailed multi-section analysis."""
    if not search_results:
        return "No information available."

    # Extract detailed information from more sources
    company_info = _extract_company_info(search_results[:6])
    financial_info = _extract_financial_info(search_results[:8])
    market_info = _extract_market_info(search_results[:6])
    risk_info = _extract_risk_info(search_results[:5])
    competitive_info = _extract_competitive_info(search_results[:5])

    sources = []
    for r in search_results[:12]:
        if r.get("title") and r.get("url"):
            sources.append(f"• {r['title']} ({r['url']})")

    sources_text = "\n".join(sources)

    memo = f"""Investment Analysis:

Executive Summary:
{company_info}

Financial Analysis:
{financial_info}

Market Opportunity:
{market_info}

Competitive Landscape:
{competitive_info}

Risk Assessment:
{risk_info}

Investment Recommendation:
Based on the analysis above, this represents a compelling investment opportunity with strong fundamentals and growth potential.

Detailed Sources:
{sources_text}"""

    return memo

def _extract_company_info(results: List[Dict[str, Any]]) -> str:
    """Extract company overview information."""
    info_pieces = []
    for result in results:
        content = _clean_content(result.get("content", ""))
        if any(keyword in content.lower() for keyword in ["founded", "company", "business", "startup", "revenue"]):
            # Extract relevant sentences
            sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
            for sentence in sentences[:3]:
                if any(keyword in sentence.lower() for keyword in ["founded", "company", "business", "startup", "revenue"]):
                    info_pieces.append(sentence)

    return ". ".join(info_pieces[:3]) + "." if info_pieces else "Company information not available in search results."

def _extract_financial_info(results: List[Dict[str, Any]]) -> str:
    """Extract financial information."""
    info_pieces = []
    for result in results:
        content = _clean_content(result.get("content", ""))
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
        for sentence in sentences[:5]:
            if any(keyword in sentence.lower() for keyword in ["revenue", "funding", "valuation", "profit", "million", "billion", "investment", "raised"]):
                info_pieces.append(sentence)

    return ". ".join(info_pieces[:3]) + "." if info_pieces else "Financial information not available in search results."

def _extract_market_info(results: List[Dict[str, Any]]) -> str:
    """Extract market and competitive information."""
    info_pieces = []
    for result in results:
        content = _clean_content(result.get("content", ""))
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
        for sentence in sentences[:5]:
            if any(keyword in sentence.lower() for keyword in ["market", "industry", "growth", "opportunity", "sector"]):
                info_pieces.append(sentence)

    return ". ".join(info_pieces[:2]) + "." if info_pieces else "Market information not available in search results."

def _extract_risk_info(results: List[Dict[str, Any]]) -> str:
    """Extract risk and challenge information."""
    info_pieces = []
    for result in results:
        content = _clean_content(result.get("content", ""))
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
        for sentence in sentences[:5]:
            if any(keyword in sentence.lower() for keyword in ["risk", "challenge", "competition", "threat", "concern"]):
                info_pieces.append(sentence)

    return ". ".join(info_pieces[:2]) + "." if info_pieces else "Risk assessment requires additional analysis."

def _extract_competitive_info(results: List[Dict[str, Any]]) -> str:
    """Extract competitive landscape information."""
    info_pieces = []
    for result in results:
        content = _clean_content(result.get("content", ""))
        sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 20]
        for sentence in sentences[:5]:
            if any(keyword in sentence.lower() for keyword in ["competitor", "versus", "compared", "alternative", "rival"]):
                info_pieces.append(sentence)

    return ". ".join(info_pieces[:2]) + "." if info_pieces else "Competitive analysis requires additional research."

def _clean_content(content: str) -> str:
    """Clean HTML, markdown, and other formatting from content."""
    if not content:
        return ""

    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)

    # Remove markdown links [text](url)
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

    # Remove markdown images ![alt](url)
    content = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', content)

    # Remove URLs
    content = re.sub(r'https?://[^\s]+', '', content)

    # Remove email addresses
    content = re.sub(r'\S+@\S+\.\S+', '', content)

    # Remove extra whitespace and special characters
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'[#*_`]', '', content)

    # Remove tracking pixels and weird characters
    content = re.sub(r'!\[\]\([^)]+\)', '', content)
    content = re.sub(r'mmMwWLliI0fiflO&1', '', content)
    content = re.sub(r'word\s+', '', content)

    # Remove iframe references
    content = re.sub(r'\[iframe\][^[]*', '', content)

    return content.strip()