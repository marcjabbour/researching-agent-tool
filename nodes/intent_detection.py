import os
from typing import TypedDict, Dict, Any, List
from langchain_openai import ChatOpenAI
from tools.intent_identifying.intents import classify_intent_llm
from tools.intent_identifying.intents_data import INTENT
from research_transparency.types import AppState
from research_transparency.state_manager import ResearchStateManager

def intent_detection_node(state: AppState) -> AppState:
    """
    Intent Detection Node - First node in the Langgraph workflow.
    Uses existing intent classification system to determine user intent.
    Now includes research transparency initialization.
    """
    query = state["query"]

    # Initialize research transparency
    state = ResearchStateManager.initialize_research_state(state)
    state = ResearchStateManager.log_reasoning_step(
        state, "planning",
        f"Analyzing query: '{query}'"
    )

    # Initialize ChatOpenAI client
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    try:
        intent, confidence, extras = classify_intent_llm(query, llm)

        # Log intent detection results
        state = ResearchStateManager.log_reasoning_step(
            state, "planning",
            f"Detected intent: '{intent}' with {confidence:.1%} confidence. Depth: {extras.get('depth', 'standard')}"
        )

        return {
            **state,
            "intent": intent,
            "confidence": confidence,
            "extras": extras,
            "processed": True
        }
    except Exception as e:
        # Fallback on error
        state = ResearchStateManager.log_reasoning_step(
            state, "planning",
            f"Intent detection failed: {str(e)}. Defaulting to unknown intent."
        )

        return {
            **state,
            "intent": "unknown",
            "confidence": 0.0,
            "extras": {"error": str(e)},
            "processed": True
        }