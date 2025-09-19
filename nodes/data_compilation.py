from typing import Dict, Any, List
from tools.research_transparency.types import AppState, TaskResults, ResearchBundle, ExtractedFact, SourceInfo
from tools.research_transparency.state_manager import ResearchStateManager
from tools.data_compilation.helpers import _deduplicate_facts, _calculate_overall_confidence, _identify_research_gaps, _extract_domain

def data_compilation_node(state: AppState) -> AppState:
    """
    Data Compilation Node - Aggregates, deduplicates, and synthesizes all task results.
    Prepares structured data bundle for response formatting.
    """
    intermediate_results = state.get("intermediate_results", {})
    research_plan = state.get("research_plan")

    if not intermediate_results:
        state = ResearchStateManager.log_reasoning_step(
            state, "aggregating",
            "No task results found. Skipping data compilation."
        )
        return state

    state = ResearchStateManager.log_reasoning_step(
        state, "aggregating",
        f"Compiling and synthesizing data from {len(intermediate_results)} completed research tasks..."
    )

    try:
        # Aggregate all facts, sources, and search results
        all_facts = []
        all_sources = {}
        all_search_results = []
        facts_by_category = {}
        total_sources_processed = 0

        for task_id, results in intermediate_results.items():
            if not results:
                continue

            task_name = task_id.replace("_", " ").title()
            facts_by_category[task_name] = []

            # Process facts from this task
            for fact_data in results.facts_found:
                extracted_fact = ExtractedFact(
                    claim=fact_data["claim"],
                    confidence=fact_data["confidence"],
                    fact_type=fact_data.get("fact_type", "general"),
                    sources=[fact_data["source_url"]] if fact_data.get("source_url") else [],
                    quotes=[fact_data["claim"]],  # Simplified - using claim as quote
                    extraction_reasoning=f"Extracted from {task_name} research task"
                )
                all_facts.append(extracted_fact)
                facts_by_category[task_name].append(extracted_fact)

            # Process sources from this task and preserve search results
            for source_data in results.search_results:
                # Add to all search results for response formatting
                all_search_results.append(source_data)

                url = source_data.get("url", "")
                if url and url not in all_sources:
                    source_info = SourceInfo(
                        url=url,
                        title=source_data.get("title", "Unknown"),
                        domain=_extract_domain(url),
                        published_date=source_data.get("published_date"),
                        authority_score=source_data.get("score", 0.5),
                        relevance_score=source_data.get("score", 0.5),
                        content_length=len(source_data.get("content", "")),
                        fact_count=len([f for f in results.facts_found if f.get("source_url") == url])
                    )
                    all_sources[url] = source_info

            total_sources_processed += results.sources_processed

        # Deduplicate facts (simplified - by claim similarity)
        unique_facts = _deduplicate_facts(all_facts)

        # Calculate overall confidence
        overall_confidence = _calculate_overall_confidence(unique_facts, all_sources)

        # Identify research gaps
        research_gaps = _identify_research_gaps(research_plan, facts_by_category)

        # Create research bundle
        research_bundle = ResearchBundle(
            intent=state.get("intent", "unknown"),
            depth=state.get("extras", {}).get("depth", "standard"),
            plan_executed=research_plan,
            facts_by_category=facts_by_category,
            source_summary=all_sources,
            overall_confidence=overall_confidence,
            research_gaps=research_gaps,
            total_sources_used=len(all_sources),
            total_facts_extracted=len(unique_facts),
            all_search_results=all_search_results
        )

        # Log compilation results with debug info
        state = ResearchStateManager.log_reasoning_step(
            state, "aggregating",
            f"Data compilation complete: {len(unique_facts)} unique facts from {len(all_sources)} sources across {len(facts_by_category)} research areas."
        )

        state = ResearchStateManager.log_reasoning_step(
            state, "aggregating",
            f"DEBUG: Categories found: {list(facts_by_category.keys())}, Search results preserved: {len(all_search_results)}"
        )

        # Update progress
        state = ResearchStateManager.update_research_progress(
            state,
            current_stage="aggregating",
            facts_collected=len(unique_facts),
            sources_processed=total_sources_processed,
            confidence_score=overall_confidence,
            current_reasoning="All research data compiled and ready for response formatting."
        )

        return {
            **state,
            "research_bundle": research_bundle
        }

    except Exception as e:
        state = ResearchStateManager.log_reasoning_step(
            state, "aggregating",
            f"Data compilation failed: {str(e)}"
        )

        return state

