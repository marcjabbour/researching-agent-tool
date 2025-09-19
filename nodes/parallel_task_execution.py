import os
import asyncio
import time
from typing import Dict, Any, List
# No longer using Exa
from research_transparency.types import AppState, ResearchTask, TaskResults, SearchQuery
from research_transparency.state_manager import ResearchStateManager
# No longer using _get_search_params
from tools.parallel_task_execution.helpers import _execute_tasks_parallel

def parallel_task_execution_node(state: AppState) -> AppState:
    """
    Parallel Task Execution Node - Executes all research tasks simultaneously.
    Shows progress for each task as they complete.
    """
    research_plan = state.get("research_plan")
    if not research_plan:
        return ResearchStateManager.log_reasoning_step(
            state, "executing",
            "No research plan found. Skipping task execution."
        )

    state = ResearchStateManager.log_reasoning_step(
        state, "executing",
        f"Executing {len(research_plan.tasks)} research tasks in parallel..."
    )

    state = ResearchStateManager.update_research_progress(
        state,
        current_stage="executing",
        current_reasoning=f"Running {len(research_plan.tasks)} parallel searches..."
    )

    # Execute all tasks in parallel
    try:
        # Use asyncio to run tasks concurrently
        results = asyncio.run(_execute_tasks_parallel(research_plan.tasks, state))

        # Update state with all results
        completed_tasks = 0
        total_sources = 0
        all_results = {}

        for task_id, result in results.items():
            if result:
                state = ResearchStateManager.update_task_status(state, task_id, "completed")
                all_results[task_id] = result
                completed_tasks += 1
                total_sources += result.sources_processed

                # Log completion of each task
                facts_summary = f"found {len(result.facts_found)} facts" if result.facts_found else "no facts extracted"
                state = ResearchStateManager.log_reasoning_step(
                    state, "executing",
                    f"✓ Completed task '{task_id}': {facts_summary} from {result.sources_processed} sources"
                )
            else:
                state = ResearchStateManager.update_task_status(
                    state, task_id, "failed",
                    error_message="Task execution failed"
                )

        # Update overall progress
        state = ResearchStateManager.update_research_progress(
            state,
            tasks_completed=completed_tasks,
            sources_processed=total_sources,
            current_reasoning=f"Parallel execution complete. {completed_tasks}/{len(research_plan.tasks)} tasks successful."
        )

        state = ResearchStateManager.log_reasoning_step(
            state, "extracting",
            f"All tasks complete. Compiled {total_sources} sources from {completed_tasks} research areas. Ready for synthesis."
        )

        return {
            **state,
            "intermediate_results": all_results
        }

    except Exception as e:
        state = ResearchStateManager.log_reasoning_step(
            state, "executing",
            f"Parallel task execution failed: {str(e)}"
        )

        return {
            **state,
            "intermediate_results": {}
        }