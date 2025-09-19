import os
from typing import TypedDict, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools.research_transparency.types import AppState
from tools.research_transparency.state_manager import ResearchStateManager

def response_formatter_node(state: AppState) -> AppState:
    """
    Simplified Response Formatter Node - Extracts claims and sources from research bundle,
    then uses LLM to generate the final response based on intent.
    """
    intent = state["intent"]
    depth = state.get("extras", {}).get("depth", "standard")
    research_bundle = state.get("research_bundle")
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
    elif not research_bundle:
        # Handle missing research data
        final_response = "No research data available to format response."

        state = ResearchStateManager.log_reasoning_step(
            state, "finalizing",
            "No research bundle found, providing error response."
        )
    else:
        # Extract claims and sources from research bundle
        claims_and_sources = _extract_claims_and_sources(research_bundle)

        # Generate response using LLM
        final_response = _generate_response_with_llm(intent, query, claims_and_sources, depth)

        state = ResearchStateManager.log_reasoning_step(
            state, "finalizing",
            f"Generated {intent} response using {len(claims_and_sources)} claims"
        )

        # Update final progress
        state = ResearchStateManager.update_research_progress(
            state,
            current_stage="finalizing",
            facts_collected=research_bundle.total_facts_extracted,
            confidence_score=research_bundle.overall_confidence
        )

    # Mark research as complete
    state = ResearchStateManager.mark_research_complete(state, research_bundle)

    return {
        **state,
        "final_response": final_response,
        "processed": True
    }

def _extract_claims_and_sources(research_bundle) -> List[Dict[str, Any]]:
    """Extract simple claims and sources from research bundle."""
    claims_and_sources = []

    for category, facts in research_bundle.facts_by_category.items():
        for fact in facts:
            claim_data = {
                "claim": fact.claim,
                "sources": fact.sources if fact.sources else [],
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

    if intent == "fact":
        return """You are a factual information assistant. Provide a direct, accurate answer to the user's question based on the research findings. Keep it concise and cite sources when possible."""

    elif intent == "memo":
        return f"""You are an investment analyst. Create a comprehensive investment memo with the following structure:

# Investment Analysis

## Executive Summary
Brief overview of the investment opportunity

## Financial Overview
Key financial metrics, funding, valuation

## Market Opportunity
Market size, trends, growth potential

## Competitive Landscape
Key competitors and differentiation

## Risk Assessment
Main risks and challenges

## Investment Recommendation
Clear recommendation with reasoning

Use the research findings to populate each section. Keep the analysis {"detailed" if depth == "comprehensive" else "concise"}."""

    elif intent == "profile":
        return """You are a business analyst. Create a comprehensive company profile including background, business model, key metrics, recent developments, and strategic position. Structure the information clearly and cite sources."""

    elif intent == "compare":
        return """You are a comparative analyst. Create a detailed comparison highlighting similarities, differences, strengths, and weaknesses of the entities mentioned. Structure your analysis with clear sections and objective assessments."""

    else:
        return """You are a helpful research assistant. Provide a well-structured, informative response based on the research findings. Organize the information logically and cite sources when relevant."""
