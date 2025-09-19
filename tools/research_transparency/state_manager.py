from typing import Dict, List, Any, Optional
from datetime import datetime
from .types import (
    AppState, ResearchProgress, ReasoningStep, ResearchTask,
    TaskStatus, ResearchStage, ExtractedFact, SourceInfo
)

class ResearchStateManager:
    """Manages research state updates with UI visibility."""

    @staticmethod
    def initialize_research_state(state: AppState) -> AppState:
        """Initialize research-specific fields in AppState."""
        return {
            **state,
            "research_plan": None,
            "task_progress": {},
            "reasoning_log": [],
            "intermediate_results": {},
            "research_progress": ResearchProgress(
                current_stage="planning",
                current_reasoning="Initializing research process...",
                tasks_completed=0,
                total_tasks=0,
                estimated_time_remaining=0,
                facts_collected=0,
                sources_processed=0
            ),
            "research_bundle": None,
            "is_research_complete": False,
            "current_stage_description": "Planning research approach",
            "user_visible_progress": "Analyzing query and planning research strategy..."
        }

    @staticmethod
    def log_reasoning_step(state: AppState, stage: ResearchStage, reasoning: str,
                          task_id: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> AppState:
        """Add a reasoning step to the log for UI display."""
        step = ReasoningStep(
            timestamp=datetime.now(),
            stage=stage,
            reasoning=reasoning,
            task_id=task_id,
            data=data or {}
        )

        reasoning_log = list(state.get("reasoning_log", []))
        reasoning_log.append(step)

        return {
            **state,
            "reasoning_log": reasoning_log,
            "user_visible_progress": reasoning,
            "current_stage_description": f"{stage.title()}: {reasoning}"
        }

    @staticmethod
    def update_research_progress(state: AppState, **progress_updates) -> AppState:
        """Update research progress with new values."""
        current_progress = state.get("research_progress")
        if not current_progress:
            current_progress = ResearchProgress(
                current_stage="planning",
                current_reasoning="",
                tasks_completed=0,
                total_tasks=0,
                estimated_time_remaining=0,
                facts_collected=0,
                sources_processed=0
            )

        # Update progress with new values
        updated_progress = ResearchProgress(
            current_stage=progress_updates.get("current_stage", current_progress.current_stage),
            current_reasoning=progress_updates.get("current_reasoning", current_progress.current_reasoning),
            tasks_completed=progress_updates.get("tasks_completed", current_progress.tasks_completed),
            total_tasks=progress_updates.get("total_tasks", current_progress.total_tasks),
            estimated_time_remaining=progress_updates.get("estimated_time_remaining", current_progress.estimated_time_remaining),
            facts_collected=progress_updates.get("facts_collected", current_progress.facts_collected),
            sources_processed=progress_updates.get("sources_processed", current_progress.sources_processed),
            confidence_score=progress_updates.get("confidence_score", current_progress.confidence_score)
        )

        return {
            **state,
            "research_progress": updated_progress
        }

    @staticmethod
    def update_task_status(state: AppState, task_id: str, status: TaskStatus,
                          error_message: Optional[str] = None) -> AppState:
        """Update the status of a specific research task."""
        task_progress = dict(state.get("task_progress", {}))
        task_progress[task_id] = status

        # Update overall progress
        total_tasks = len(task_progress)
        completed_tasks = sum(1 for s in task_progress.values() if s == "completed")

        updates = {
            "tasks_completed": completed_tasks,
            "total_tasks": total_tasks
        }

        if status == "failed" and error_message:
            state = ResearchStateManager.log_reasoning_step(
                state, "executing",
                f"Task {task_id} failed: {error_message}",
                task_id=task_id
            )

        state = ResearchStateManager.update_research_progress(state, **updates)

        return {
            **state,
            "task_progress": task_progress
        }

    @staticmethod
    def add_task_results(state: AppState, task_id: str, results: Dict[str, Any]) -> AppState:
        """Add results for a completed task."""
        intermediate_results = dict(state.get("intermediate_results", {}))
        intermediate_results[task_id] = results

        # Update facts collected count
        facts_count = sum(
            len(result.get("facts_found", []))
            for result in intermediate_results.values()
        )

        sources_count = sum(
            result.get("sources_processed", 0)
            for result in intermediate_results.values()
        )

        state = ResearchStateManager.update_research_progress(
            state,
            facts_collected=facts_count,
            sources_processed=sources_count
        )

        return {
            **state,
            "intermediate_results": intermediate_results
        }

    @staticmethod
    def mark_research_complete(state: AppState, final_bundle: Optional[Dict[str, Any]] = None) -> AppState:
        """Mark research as complete and finalize state."""
        state = ResearchStateManager.log_reasoning_step(
            state, "finalizing",
            "Research complete. Formatting final response..."
        )

        return {
            **state,
            "is_research_complete": True,
            "research_bundle": final_bundle,
            "current_stage_description": "Research Complete",
            "user_visible_progress": "All research tasks completed. Formatting final response..."
        }

    @staticmethod
    def get_user_friendly_summary(state: AppState) -> str:
        """Generate a user-friendly summary of current research state."""
        progress = state.get("research_progress")
        if not progress:
            return "Initializing research..."

        if progress.total_tasks == 0:
            return "Planning research approach..."

        completion_pct = int((progress.tasks_completed / progress.total_tasks) * 100)

        if progress.current_stage == "planning":
            return f"Planning research strategy (identified {progress.total_tasks} tasks)"
        elif progress.current_stage == "executing":
            return f"Executing research tasks ({progress.tasks_completed}/{progress.total_tasks} complete - {completion_pct}%)"
        elif progress.current_stage == "extracting":
            return f"Extracting facts from {progress.sources_processed} sources ({progress.facts_collected} facts found)"
        elif progress.current_stage == "aggregating":
            return f"Aggregating and validating {progress.facts_collected} facts from research"
        elif progress.current_stage == "finalizing":
            return f"Finalizing response with {progress.facts_collected} verified facts"
        else:
            return f"Research progress: {completion_pct}% complete"

    @staticmethod
    def get_detailed_progress(state: AppState) -> Dict[str, Any]:
        """Get detailed progress information for advanced UI display."""
        return {
            "overall_progress": state.get("research_progress"),
            "task_statuses": state.get("task_progress", {}),
            "reasoning_steps": state.get("reasoning_log", []),
            "current_summary": ResearchStateManager.get_user_friendly_summary(state),
            "is_complete": state.get("is_research_complete", False),
            "intermediate_results": state.get("intermediate_results", {})
        }