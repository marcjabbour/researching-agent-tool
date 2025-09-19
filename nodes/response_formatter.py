import os
from typing import TypedDict, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from research_transparency.types import AppState
from research_transparency.state_manager import ResearchStateManager
from tools.response_formatter.helpers import generate_prompt_for_memo, generate_prompt_for_profile, generate_prompt_for_compare, generate_prompt_for_default

def response_formatter_node(state: AppState) -> AppState:
    """
    Simplified Response Formatter Node - Extracts claims and sources from task results,
    then uses LLM to generate the final response based on intent.
    """
    intent = state["intent"]
    depth = state.get("extras", {}).get("depth", "standard")
    intermediate_results = state.get("intermediate_results", {})
    query = state["query"]

    # Log start of response formatting
    state = ResearchStateManager.log_reasoning_step(
        state, "finalizing",
        f"Generating {intent} response using LLM with extracted facts"
    )

    # Check if we already have a final response (from quick search)
    if state.get("final_response"):
        final_response = state["final_response"]

        state = ResearchStateManager.log_reasoning_step(
            state, "finalizing",
            f"Using pre-generated {intent} response from quick search"
        )
    elif not intermediate_results:
        # Handle missing research data
        final_response = "No research data available to format response."

        state = ResearchStateManager.log_reasoning_step(
            state, "finalizing",
            "No task results found, providing error response."
        )
    else:
        # Extract claims and sources from task results
        claims_and_sources = _extract_claims_from_task_results(intermediate_results)

        # Generate response using LLM
        final_response = _generate_response_with_llm(intent, query, claims_and_sources, depth)

        state = ResearchStateManager.log_reasoning_step(
            state, "finalizing",
            f"Generated {intent} response using {len(claims_and_sources)} claims"
        )

        # Calculate stats for UI
        total_facts = len(claims_and_sources)
        total_sources = sum(len(result.search_results) for result in intermediate_results.values() if result)
        avg_confidence = sum(result.confidence_score for result in intermediate_results.values() if result) / len(intermediate_results) if intermediate_results else 0.0

        # Update final progress
        state = ResearchStateManager.update_research_progress(
            state,
            current_stage="finalizing",
            facts_collected=total_facts,
            sources_processed=total_sources,
            confidence_score=avg_confidence
        )

    # Mark research as complete
    state = ResearchStateManager.mark_research_complete(state, None)

    return {
        **state,
        "final_response": final_response,
        "processed": True
    }

def _extract_claims_from_task_results(intermediate_results) -> List[Dict[str, Any]]:
    """Extract simple claims and sources from task results."""
    claims_and_sources = []

    for task_id, result in intermediate_results.items():
        if not result or not result.facts_found:
            continue

        # Convert task_id to readable category name
        category = task_id.replace("_", " ").title()

        for fact in result.facts_found:
            claim_data = {
                "claim": fact["claim"],
                "sources": [fact.get("source_url")] if fact.get("source_url") else [],
                "category": category
            }
            claims_and_sources.append(claim_data)

    return claims_and_sources

def _generate_response_with_llm(intent: str, query: str, claims_and_sources: List[Dict[str, Any]], depth: str) -> str:
    """Generate response using LLM based on intent and extracted claims."""

    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Format claims for LLM
    claims_text = ""
    for i, item in enumerate(claims_and_sources, 1):
        sources_text = ", ".join(item["sources"][:2]) if item["sources"] else "No source"
        claims_text += f"{i}. {item['claim']} (Source: {sources_text})\n"

    # Create system prompt based on intent
    system_prompt = _get_system_prompt(intent, depth)

    # Create user prompt
    user_prompt = f"""Query: {query}

Research findings:
{claims_text}

Please generate a {intent} response using the research findings above."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

def _get_system_prompt(intent: str, depth: str) -> str:
    """Get system prompt based on intent type."""
    if intent == "memo":
        return generate_prompt_for_memo(depth)
    elif intent == "profile":
        return generate_prompt_for_profile()
    elif intent == "compare":
        return generate_prompt_for_compare()
    else:
        return generate_prompt_for_default()