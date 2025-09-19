from typing import Dict, List, Any, Optional, TypedDict, Literal
from dataclasses import dataclass
from datetime import datetime
from tools.intent_identifying.intents_data import INTENT

# Task status tracking
TaskStatus = Literal["pending", "in_progress", "completed", "failed"]
ResearchStage = Literal["planning", "executing", "extracting", "aggregating", "finalizing"]

@dataclass
class SearchQuery:
    """Individual search query with metadata."""
    query: str
    search_type: str  # "company_info", "financials", "market_analysis", etc.
    priority: int  # 1-5, higher is more important
    estimated_results: int = 10

@dataclass
class TaskResults:
    """Results from executing a research task."""
    task_id: str
    facts_found: List[Dict[str, Any]]
    sources_processed: int
    confidence_score: float
    summary: str
    raw_data: Dict[str, Any]
    search_results: List[Dict[str, Any]]  # Raw search results
    execution_time: float  # seconds

@dataclass
class ResearchTask:
    """Individual research task with full lifecycle tracking."""
    id: str
    description: str  # User-facing description like "(1) Research company profile..."
    rationale: str   # Why this task is needed
    status: TaskStatus
    search_queries: List[SearchQuery]
    results: Optional[TaskResults] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None

@dataclass
class ResearchPlan:
    """Complete research plan with user-facing explanation."""
    rationale: str  # High-level explanation for the user
    tasks: List[ResearchTask]
    estimated_duration: int  # seconds
    total_search_queries: int
    priority_order: List[str]  # Task IDs in execution order

@dataclass
class ReasoningStep:
    """Individual step in the research process for UI display."""
    timestamp: datetime
    stage: ResearchStage
    reasoning: str  # Human-readable explanation
    task_id: Optional[str] = None  # Which task this relates to
    data: Optional[Dict[str, Any]] = None  # Structured data for this step

@dataclass
class ResearchProgress:
    """Real-time progress tracking for UI."""
    current_stage: ResearchStage
    current_reasoning: str
    tasks_completed: int
    total_tasks: int
    estimated_time_remaining: int  # seconds
    facts_collected: int
    sources_processed: int
    confidence_score: float = 0.0

@dataclass
class SourceInfo:
    """Information about a source used in research."""
    url: str
    title: str
    domain: str
    published_date: Optional[str]
    authority_score: float  # 0-1
    relevance_score: float  # 0-1
    content_length: int
    fact_count: int  # How many facts extracted from this source

@dataclass
class ExtractedFact:
    """Individual fact with full provenance."""
    claim: str
    confidence: float  # 0-1
    fact_type: str  # "financial", "company_info", "market_data", etc.
    sources: List[str]  # URLs
    quotes: List[str]  # Actual quotes from sources
    extraction_reasoning: str  # Why this was considered a fact

@dataclass
class ResearchBundle:
    """Final research output bundle."""
    intent: str
    depth: str
    plan_executed: ResearchPlan
    facts_by_category: Dict[str, List[ExtractedFact]]
    source_summary: Dict[str, SourceInfo]
    overall_confidence: float
    research_gaps: List[str]  # What couldn't be found
    total_sources_used: int
    total_facts_extracted: int
    all_search_results: List[Dict[str, Any]] = None  # Preserve original search results

# Enhanced AppState with full transparency
class AppState(TypedDict, total=False):
    # Original fields (required)
    query: str
    intent: INTENT
    confidence: float
    extras: Dict[str, Any]
    processed: bool
    search_query: str
    search_results: List[Dict[str, Any]]
    final_response: str

    # New research transparency fields (optional)
    research_plan: Optional[ResearchPlan]
    task_progress: Dict[str, TaskStatus]  # task_id -> status
    reasoning_log: List[ReasoningStep]
    intermediate_results: Dict[str, TaskResults]  # task_id -> results
    research_progress: Optional[ResearchProgress]
    research_bundle: Optional[ResearchBundle]

    # UI state fields (optional)
    is_research_complete: bool
    current_stage_description: str
    user_visible_progress: str