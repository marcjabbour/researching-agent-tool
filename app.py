from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from tools.research_transparency.types import AppState
from nodes.intent_detection import intent_detection_node
from nodes.research_planning import research_planning_node
from nodes.parallel_task_execution import parallel_task_execution_node
from nodes.data_compilation import data_compilation_node
from nodes.response_formatter import response_formatter_node
from nodes.web_search import web_search_node
from tools.research_transparency.state_manager import ResearchStateManager

# Load environment variables
load_dotenv()

def create_app() -> StateGraph:
    """
    Create and configure the Langgraph application with conditional routing based on intent.

    New Flow:
    - Intent Detection → (if fact) → Quick Web Search → Response Formatting
    - Intent Detection → (if not fact) → Research Planning → Parallel Task Execution → Data Compilation → Response Formatting
    """
    # Create the state graph
    workflow = StateGraph(AppState)

    # Add all nodes
    workflow.add_node("intent_detection", intent_detection_node)
    workflow.add_node("web_search", web_search_node)  # For quick fact queries
    workflow.add_node("research_planning", research_planning_node)
    workflow.add_node("parallel_task_execution", parallel_task_execution_node)
    workflow.add_node("data_compilation", data_compilation_node)
    workflow.add_node("response_formatter", response_formatter_node)

    # Set the entry point
    workflow.set_entry_point("intent_detection")

    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "intent_detection",
        route_based_on_intent,
        {
            "fact": "web_search",
            "research": "research_planning"
        }
    )

    # Quick fact flow
    workflow.add_edge("web_search", "response_formatter")

    # Research flow
    workflow.add_edge("research_planning", "parallel_task_execution")
    workflow.add_edge("parallel_task_execution", "data_compilation")
    workflow.add_edge("data_compilation", "response_formatter")

    # End
    workflow.add_edge("response_formatter", END)

    return workflow.compile()

def route_based_on_intent(state: AppState) -> str:
    """Route to different workflows based on detected intent."""
    intent = state.get("intent", "unknown")

    if intent == "fact":
        return "fact"
    else:
        return "research"

def run_query(query: str) -> AppState:
    """
    Run a query through the Langgraph workflow.
    """
    app = create_app()

    initial_state = AppState(
        query=query,
        intent="unknown",
        confidence=0.0,
        extras={},
        processed=False,
        search_query="",
        search_results=[],
        final_response="",

        # Research transparency fields (will be initialized by intent_detection_node)
        research_plan=None,
        task_progress={},
        reasoning_log=[],
        intermediate_results={},
        research_progress=None,
        research_bundle=None,
        is_research_complete=False,
        current_stage_description="",
        user_visible_progress=""
    )

    result = app.invoke(initial_state)
    return result

def display_research_results(result: AppState):
    """Display comprehensive research results and transparency information."""

    # Display basic results
    print(f"Query: {result['query']}")
    print(f"Intent: {result['intent']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Final Response: {result['final_response']}")

    # Display research transparency information
    print("\n" + "="*50)
    print("RESEARCH STRATEGY & TRANSPARENCY")
    print("="*50)

    _display_research_plan(result.get('research_plan'))
    _display_execution_log(result.get('reasoning_log', []))
    _display_research_bundle(result.get('research_bundle'))
    _display_final_stats(result.get('research_progress'))

    print(f"\nResearch Complete: {result.get('is_research_complete', False)}")

def _display_research_plan(research_plan):
    """Display research strategy and task breakdown."""
    if not research_plan:
        return

    print(f"\nRESEARCH STRATEGY:")
    print(f"{research_plan.rationale}")

    print(f"\nTASK BREAKDOWN ({len(research_plan.tasks)} tasks):")
    for i, task in enumerate(research_plan.tasks, 1):
        print(f"{i}. {task.description}")
        print(f"   Rationale: {task.rationale}")

def _display_execution_log(reasoning_log):
    """Display step-by-step execution log."""
    print(f"\nEXECUTION LOG:")
    for i, step in enumerate(reasoning_log, 1):
        print(f"{i}. [{step.stage.upper()}] {step.reasoning}")

def _display_research_bundle(research_bundle):
    """Display research results summary."""
    if not research_bundle:
        return

    print(f"\nRESEARCH RESULTS:")
    print(f"- Total sources: {research_bundle.total_sources_used}")
    print(f"- Total facts extracted: {research_bundle.total_facts_extracted}")
    print(f"- Overall confidence: {research_bundle.overall_confidence:.2f}")

    if research_bundle.research_gaps:
        print(f"- Research gaps: {len(research_bundle.research_gaps)}")
        for gap in research_bundle.research_gaps[:2]:  # Show first 2
            print(f"  • {gap}")

def _display_final_stats(progress):
    """Display final statistics."""
    if not progress:
        return

    print(f"\nFINAL STATS:")
    print(f"- Sources processed: {progress.sources_processed}")
    print(f"- Facts collected: {progress.facts_collected}")
    print(f"- Confidence score: {progress.confidence_score:.2f}")

if __name__ == "__main__":
    # Example usage - test fact query
    # print("=== TESTING FACT QUERY ===")
    # fact_query = "Who founded Harmonic (https://harmonic.ai/)?"
    # fact_result = run_query(fact_query)
    # print(f"Fact Response: {fact_result['final_response']}")

    print("\n=== TESTING MEMO QUERY ===")
    memo_query = "Compare OpenAI and Perplexity AI"
    memo_result = run_query(memo_query)

    display_research_results(memo_result)