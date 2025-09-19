import os
import asyncio
import time
from typing import Dict, List, Any
from tavily import TavilyClient
from tools.research_transparency.types import AppState, ResearchTask, TaskResults
from tools.web_searching.helpers import _get_search_params

async def _execute_tasks_parallel(tasks: List[ResearchTask], state: AppState) -> Dict[str, TaskResults]:
    """Execute multiple research tasks in parallel using asyncio."""
    # Create async tasks for parallel execution
    async_tasks = []
    for task in tasks:
        async_task = _execute_single_task(task, state)
        async_tasks.append(async_task)

    # Wait for all tasks to complete
    results = await asyncio.gather(*async_tasks, return_exceptions=True)

    # Process results
    task_results = {}
    for i, result in enumerate(results):
        task_id = tasks[i].id
        if isinstance(result, Exception):
            print(f"Task {task_id} failed: {result}")
            task_results[task_id] = None
        else:
            task_results[task_id] = result

    return task_results

async def _execute_single_task(task: ResearchTask, state: AppState) -> TaskResults:
    """Execute a single research task with all its search queries."""
    start_time = time.time()

    try:
        # Initialize Tavily client
        tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

        all_results = []
        total_sources = 0

        # Execute all search queries for this task
        all_answers = []

        for search_query in task.search_queries:
            # Execute Tavily search
            search_response = tavily.search(
                query=search_query.query,
                search_depth="basic",
                max_results=5,
                include_answer="advanced",
                include_raw_content=False
            )

            # Get the answer and results
            answer = search_response.get("answer", "")
            results = search_response.get("results", [])
            # print(f"ANSWER: {answer}")
            if answer:
                all_answers.append(answer)

            # Process results
            for result in results:
                all_results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0.5),
                    "published_date": result.get("published_date"),
                    "author": None,
                    "search_type": search_query.search_type,
                    "query_used": search_query.query
                })

        total_sources = len(all_results)

        # Create structured facts from Tavily answers
        facts = []
        for i, answer in enumerate(all_answers):
            if answer and len(answer.strip()) > 20:
                fact = {
                    "claim": answer.strip(),
                    "source_url": all_results[0].get("url", "") if all_results else "",
                    "source_title": f"Tavily Answer {i+1}",
                    "confidence": 0.8,
                    "task_id": task.id,
                    "fact_type": task.search_queries[i].search_type if i < len(task.search_queries) else "general"
                }
                facts.append(fact)

        print(f"Task {task.id}: Generated {len(facts)} facts from {len(all_answers)} answers")
        # Calculate execution time
        execution_time = time.time() - start_time

        # Generate summary
        summary = f"Found {total_sources} sources for {task.description[:50]}..."

        return TaskResults(
            task_id=task.id,
            facts_found=facts,
            sources_processed=total_sources,
            confidence_score=0.8 if facts else 0.0,
            summary=summary,
            raw_data={"task_description": task.description, "rationale": task.rationale, "tavily_answers": all_answers},
            search_results=all_results,
            execution_time=execution_time
        )

    except Exception as e:
        execution_time = time.time() - start_time
        return TaskResults(
            task_id=task.id,
            facts_found=[],
            sources_processed=0,
            confidence_score=0.0,
            summary=f"Task failed: {str(e)}",
            raw_data={"error": str(e)},
            search_results=[],
            execution_time=execution_time
        )

def _extract_facts_from_results(results: List[Dict[str, Any]], task_id: str) -> List[Dict[str, Any]]:
    """Extract key facts from search results (simplified version)."""
    facts = []

    for result in results[:3]:  # Process top 3 results
        content = result.get("content", "")
        if len(content) > 100:  # Only process substantial content

            # Simple fact extraction - split into sentences and take meaningful ones
            sentences = content.split(".")
            for sentence in sentences[:3]:  # Top 3 sentences per result
                sentence = sentence.strip()
                if len(sentence) > 30 and any(keyword in sentence.lower() for keyword in
                    ["founded", "ceo", "revenue", "funding", "million", "billion", "company", "business"]):

                    fact = {
                        "claim": sentence,
                        "source_url": result.get("url"),
                        "source_title": result.get("title"),
                        "confidence": 0.7,  # Simplified confidence
                        "task_id": task_id,
                        "fact_type": result.get("search_type", "general")
                    }
                    facts.append(fact)

    return facts[:5]  # Return top 5 facts per task