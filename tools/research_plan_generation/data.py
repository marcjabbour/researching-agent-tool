from typing import List, Dict, Any

def _generate_research_plan_prompt(intent: str, query: str, depth: str, entities: List[Dict[str, Any]]) -> str:
    entity_context = ""
    if entities:
        entity_names = [e.get("name", "") for e in entities if e.get("name")]
        entity_context = f"\nKey entities mentioned: {', '.join(entity_names)}"

    return f"""You are an expert research strategist. Given a user query, you must:

1. Explain your research strategy (2-3 sentences about WHY these research areas are needed)
2. Break the research into specific, parallel tasks that can be executed simultaneously
3. For each task, provide the rationale for why it's essential

Intent: {intent}
Depth: {depth}
Query: {query}{entity_context}

Return a JSON response with this exact structure:
{{
  "rationale": "Your 2-3 sentence explanation of the research strategy and why these areas are essential...",
  "estimated_duration": 45,
  "tasks": [
    {{
      "id": "company_profile",
      "description": "Research and summarize [COMPANY]'s company profile: founding date, headquarters, mission statement, core products/services, business model, and revenue model.",
      "rationale": "Company fundamentals are essential for understanding the business foundation and core value proposition.",
      "search_queries": [
        {{
          "query": "[COMPANY] company profile founding date headquarters",
          "search_type": "company_info",
          "priority": 5
        }},
        {{
          "query": "[COMPANY] business model revenue model products services",
          "search_type": "company_info",
          "priority": 4
        }}
      ]
    }}
  ]
}}

Guidelines:
- For FACT queries: 1-2 focused tasks
- For PROFILE queries: 3-4 comprehensive tasks covering background, recent developments, key metrics
- For COMPARE queries: 4-5 tasks covering each entity plus comparative analysis
- For MEMO queries: 5-7 tasks covering company profile, financials, market, competition, risks, management
- Each task should have 2-4 specific search queries
- Make descriptions specific and actionable
- Explain WHY each research area matters for the {intent} intent"""