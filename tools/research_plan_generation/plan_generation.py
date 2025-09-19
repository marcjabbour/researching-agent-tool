from tools.research_plan_generation.data import _generate_research_plan_prompt
from research_transparency.types import ResearchPlan, ResearchTask, SearchQuery
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from typing import List, Dict, Any


def _generate_research_plan(llm: ChatOpenAI, intent: str, query: str, depth: str, entities: List[Dict[str, Any]]) -> ResearchPlan:
    """Generate comprehensive research plan using LLM."""

    entity_context = ""
    if entities:
        entity_names = [e.get("name", "") for e in entities if e.get("name")]
        entity_context = f"\\nKey entities mentioned: {', '.join(entity_names)}"

    system_prompt = _generate_research_plan_prompt(intent, query, depth, entities)

    user_message = f"Create a research plan for: {query}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    # Get structured response
    response = llm.invoke(messages)

    try:
        # Parse JSON response
        plan_data = json.loads(response.content)

        # Convert to ResearchPlan object
        tasks = []
        for task_data in plan_data["tasks"]:
            search_queries = [
                SearchQuery(
                    query=sq["query"],
                    search_type=sq["search_type"],
                    priority=sq["priority"]
                ) for sq in task_data["search_queries"]
            ]

            task = ResearchTask(
                id=task_data["id"],
                description=task_data["description"],
                rationale=task_data["rationale"],
                status="pending",
                search_queries=search_queries
            )
            tasks.append(task)

        research_plan = ResearchPlan(
            rationale=plan_data["rationale"],
            tasks=tasks,
            estimated_duration=plan_data.get("estimated_duration", 60),
            total_search_queries=sum(len(task.search_queries) for task in tasks),
            priority_order=[task.id for task in tasks]
        )

        return research_plan

    except (json.JSONDecodeError, KeyError) as e:
        # If LLM response parsing fails, create fallback
        return _create_fallback_plan(intent, query, depth)

def _create_fallback_plan(intent: str, query: str, depth: str) -> ResearchPlan:
    """Create a simple fallback research plan if LLM planning fails."""

    fallback_task = ResearchTask(
        id="general_research",
        description=f"Research and analyze: {query}",
        rationale=f"Comprehensive {intent} research to address the user's query.",
        status="pending",
        search_queries=[
            SearchQuery(
                query=query,
                search_type="general",
                priority=3
            )
        ]
    )

    return ResearchPlan(
        rationale=f"Conducting {intent} research to provide comprehensive information about the query.",
        tasks=[fallback_task],
        estimated_duration=30,
        total_search_queries=1,
        priority_order=["general_research"]
    )