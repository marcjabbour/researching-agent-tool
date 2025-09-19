from typing import Dict, List
from tools.research_transparency.types import ExtractedFact, SourceInfo

def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except:
        return "unknown"

def _deduplicate_facts(facts: List[ExtractedFact]) -> List[ExtractedFact]:
    """Remove duplicate facts based on claim similarity."""
    unique_facts = []
    seen_claims = set()

    for fact in facts:
        # Simple deduplication by first 50 characters
        claim_key = fact.claim[:50].lower().strip()
        if claim_key not in seen_claims:
            seen_claims.add(claim_key)
            unique_facts.append(fact)

    return unique_facts

def _calculate_overall_confidence(facts: List[ExtractedFact], sources: Dict[str, SourceInfo]) -> float:
    """Calculate overall confidence score based on facts and source quality."""
    if not facts:
        return 0.0

    # Simple confidence calculation
    fact_confidence_avg = sum(fact.confidence for fact in facts) / len(facts)
    source_authority_avg = sum(source.authority_score for source in sources.values()) / len(sources) if sources else 0.5

    # Weighted average
    overall_confidence = (fact_confidence_avg * 0.7) + (source_authority_avg * 0.3)
    return min(1.0, max(0.0, overall_confidence))

def _identify_research_gaps(research_plan, facts_by_category: Dict[str, List[ExtractedFact]]) -> List[str]:
    """Identify areas where research was planned but insufficient data was found."""
    gaps = []

    if not research_plan:
        return gaps

    for task in research_plan.tasks:
        task_name = task.id.replace("_", " ").title()
        facts_found = len(facts_by_category.get(task_name, []))

        if facts_found == 0:
            gaps.append(f"No information found for: {task.description}")
        elif facts_found < 2:
            gaps.append(f"Limited information for: {task.description}")

    return gaps