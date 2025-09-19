from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .types import AppState, ReasoningStep, ResearchProgress
from .state_manager import ResearchStateManager

class UIHelpers:
    """Helper functions for UI display of research transparency data."""

    @staticmethod
    def get_progress_percentage(state: AppState) -> int:
        """Get overall progress as a percentage (0-100)."""
        progress = state.get("research_progress")
        if not progress or progress.total_tasks == 0:
            return 0

        return min(100, int((progress.tasks_completed / progress.total_tasks) * 100))

    @staticmethod
    def get_current_activity(state: AppState) -> str:
        """Get current activity description for UI display."""
        return state.get("user_visible_progress", "Initializing...")

    @staticmethod
    def get_stage_indicator(state: AppState) -> Dict[str, Any]:
        """Get stage indicator data for UI progress bars/indicators."""
        progress = state.get("research_progress")
        if not progress:
            return {
                "current_stage": "planning",
                "stages": ["planning", "executing", "extracting", "finalizing"],
                "current_index": 0,
                "total_stages": 4
            }

        stages = ["planning", "executing", "extracting", "finalizing"]
        current_index = stages.index(progress.current_stage) if progress.current_stage in stages else 0

        return {
            "current_stage": progress.current_stage,
            "stages": stages,
            "current_index": current_index,
            "total_stages": len(stages)
        }

    @staticmethod
    def get_timeline_data(state: AppState) -> List[Dict[str, Any]]:
        """Get timeline data for UI display of research steps."""
        reasoning_log = state.get("reasoning_log", [])
        timeline = []

        for step in reasoning_log:
            timeline.append({
                "timestamp": step.timestamp.isoformat() if step.timestamp else datetime.now().isoformat(),
                "stage": step.stage,
                "message": step.reasoning,
                "task_id": step.task_id,
                "relative_time": UIHelpers._get_relative_time(step.timestamp) if step.timestamp else "just now"
            })

        return timeline

    @staticmethod
    def get_stats_summary(state: AppState) -> Dict[str, Any]:
        """Get statistical summary for UI dashboard."""
        progress = state.get("research_progress")
        if not progress:
            return {
                "sources_processed": 0,
                "facts_collected": 0,
                "confidence_score": 0.0,
                "time_elapsed": "0s",
                "completion_percentage": 0
            }

        # Calculate time elapsed from first reasoning step
        reasoning_log = state.get("reasoning_log", [])
        start_time = reasoning_log[0].timestamp if reasoning_log else datetime.now()
        elapsed = datetime.now() - start_time
        time_str = UIHelpers._format_duration(elapsed)

        return {
            "sources_processed": progress.sources_processed,
            "facts_collected": progress.facts_collected,
            "confidence_score": progress.confidence_score,
            "time_elapsed": time_str,
            "completion_percentage": UIHelpers.get_progress_percentage(state)
        }

    @staticmethod
    def get_live_updates(state: AppState, since_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get updates since a specific timestamp for live UI updates."""
        reasoning_log = state.get("reasoning_log", [])

        if since_timestamp:
            updates = [
                step for step in reasoning_log
                if step.timestamp and step.timestamp > since_timestamp
            ]
        else:
            updates = reasoning_log

        return [
            {
                "timestamp": step.timestamp.isoformat() if step.timestamp else datetime.now().isoformat(),
                "stage": step.stage,
                "message": step.reasoning,
                "type": "reasoning_step"
            }
            for step in updates
        ]

    @staticmethod
    def format_for_streaming_ui(state: AppState) -> Dict[str, Any]:
        """Format all transparency data for streaming UI consumption."""
        return {
            "current_activity": UIHelpers.get_current_activity(state),
            "progress_percentage": UIHelpers.get_progress_percentage(state),
            "stage_indicator": UIHelpers.get_stage_indicator(state),
            "stats": UIHelpers.get_stats_summary(state),
            "latest_update": UIHelpers.get_timeline_data(state)[-1] if UIHelpers.get_timeline_data(state) else None,
            "is_complete": state.get("is_research_complete", False),
            "full_timeline": UIHelpers.get_timeline_data(state)
        }

    @staticmethod
    def _get_relative_time(timestamp: datetime) -> str:
        """Get relative time string (e.g., '2 seconds ago')."""
        now = datetime.now()
        diff = now - timestamp

        if diff.total_seconds() < 60:
            return f"{int(diff.total_seconds())}s ago"
        elif diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() / 60)}m ago"
        else:
            return f"{int(diff.total_seconds() / 3600)}h ago"

    @staticmethod
    def _format_duration(duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"

class DebugHelpers:
    """Helper functions for debugging the research process."""

    @staticmethod
    def print_full_state(state: AppState, include_content: bool = False):
        """Print the complete state for debugging."""
        print("="*80)
        print("FULL RESEARCH STATE DEBUG")
        print("="*80)

        print(f"Query: {state.get('query')}")
        print(f"Intent: {state.get('intent')} (confidence: {state.get('confidence', 0):.2f})")
        print(f"Complete: {state.get('is_research_complete', False)}")

        progress = state.get('research_progress')
        if progress:
            print(f"\nProgress: {progress.current_stage} - {progress.current_reasoning}")
            print(f"Tasks: {progress.tasks_completed}/{progress.total_tasks}")
            print(f"Sources: {progress.sources_processed}, Facts: {progress.facts_collected}")

        reasoning_log = state.get('reasoning_log', [])
        print(f"\nReasoning Steps ({len(reasoning_log)}):")
        for i, step in enumerate(reasoning_log, 1):
            timestamp = step.timestamp.strftime("%H:%M:%S") if step.timestamp else "unknown"
            print(f"  {i}. [{timestamp}] {step.stage}: {step.reasoning}")

        if include_content:
            search_results = state.get('search_results', [])
            print(f"\nSearch Results ({len(search_results)}):")
            for i, result in enumerate(search_results[:3], 1):  # Show first 3
                print(f"  {i}. {result.get('title', 'No title')}")
                print(f"     URL: {result.get('url', 'No URL')}")
                content = result.get('content', '')
                print(f"     Content: {content[:100]}..." if len(content) > 100 else f"     Content: {content}")

        print("="*80)

    @staticmethod
    def export_timeline_json(state: AppState) -> str:
        """Export timeline as JSON for external analysis."""
        import json
        timeline_data = UIHelpers.get_timeline_data(state)
        return json.dumps(timeline_data, indent=2, default=str)