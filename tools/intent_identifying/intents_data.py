from typing import Literal

INTENT = Literal["fact", "profile", "compare", "memo", "unknown"]

INTENT_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"enum": ["fact", "profile", "compare", "memo", "unknown"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"enum": ["company", "person", "market", "unknown"]}
                },
                "required": ["name", "type"],
                "additionalProperties": False
            }
        },
        "attributes": {"type": "array", "items": {"type": "string"}},
        "depth": {"enum": ["quick", "standard", "comprehensive"]},
        "rationale": {"type": "string"}
    },
    "required": ["intent", "confidence", "entities", "attributes", "depth", "rationale"],
    "additionalProperties": False
}

INTENT_SYSTEM_PROMPT = """You are an expert VC research assistant that classifies queries into research intents.

Classify the query into one of these intents:
- fact: Simple factual questions (Who founded X? When was X founded? What is X's funding?)
- profile: Comprehensive information requests (Tell me about X, Profile of founder Y)
- compare: Comparative analysis (Compare X vs Y, How does X stack up against Y?)
- memo: Investment analysis requests (Should we invest in X? Investment memo for X)
- unknown: Queries outside VC research scope or ambiguous requests

Extract entities mentioned in the query and classify them as company, person, market, or unknown.
Identify relevant attributes being requested (founders, funding, team, etc.).
Suggest research depth: quick (basic facts), standard (moderate detail), comprehensive (full analysis).

If you're not confident (confidence < 0.65), set intent="unknown" and explain why in rationale.
Provide clear rationale for your classification."""