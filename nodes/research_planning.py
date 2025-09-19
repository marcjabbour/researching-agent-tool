import os
import json
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools.research_transparency.types import AppState, ResearchPlan, ResearchTask, SearchQuery
from tools.research_transparency.state_manager import ResearchStateManager
from tools.research_plan_generation.plan_generation import _generate_research_plan, _create_fallback_plan

def research_planning_node(state: AppState) -> AppState:
    """
    Research Planning Node - Uses LLM to generate research strategy and task breakdown.
    This is where the AI shows its thinking about HOW to approach the research problem.
    """
    intent = state["intent"]
    query = state["query"]
    depth = state.get("extras", {}).get("depth", "standard")
    entities = state.get("extras", {}).get("entities", [])

    state = ResearchStateManager.log_reasoning_step(
        state, "planning",
        f"Generating research strategy for {intent} query with {depth} depth..."
    )

    # Initialize ChatOpenAI for research planning
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,  # Slightly higher for creative research planning
        api_key=os.getenv("OPENAI_API_KEY")
    )

    try:
        # Generate research plan using LLM
        research_plan = _generate_research_plan(llm, intent, query, depth, entities)

        # Log the research strategy (the thinking)
        state = ResearchStateManager.log_reasoning_step(
            state, "planning",
            research_plan.rationale
        )

        # Log task breakdown
        task_descriptions = [f"{i+1}. {task.description}" for i, task in enumerate(research_plan.tasks)]
        tasks_summary = "\\n".join(task_descriptions)

        state = ResearchStateManager.log_reasoning_step(
            state, "planning",
            f"Research plan broken into {len(research_plan.tasks)} parallel tasks:\\n{tasks_summary}"
        )

        # Initialize task progress tracking
        task_progress = {}
        for task in research_plan.tasks:
            task_progress[task.id] = "pending"

        # Update state with research plan
        state = ResearchStateManager.update_research_progress(
            state,
            current_stage="planning",
            total_tasks=len(research_plan.tasks),
            current_reasoning=f"Research strategy complete. Ready to execute {len(research_plan.tasks)} tasks in parallel."
        )

        return {
            **state,
            "research_plan": research_plan,
            "task_progress": task_progress
        }

    except Exception as e:
        state = ResearchStateManager.log_reasoning_step(
            state, "planning",
            f"Research planning failed: {str(e)}. Falling back to simple search approach."
        )

        # Fallback: create simple single-task plan
        fallback_plan = _create_fallback_plan(intent, query, depth)

        return {
            **state,
            "research_plan": fallback_plan,
            "task_progress": {fallback_plan.tasks[0].id: "pending"}
        }