import os
from typing import TypedDict, Dict, Any, List
from langchain_openai import ChatOpenAI
from tools.intent_identifying.intents import classify_intent_llm
from tools.intent_identifying.intents_data import INTENT

class AppState(TypedDict):
    query: str
    intent: INTENT
    confidence: float
    extras: Dict[str, Any]
    processed: bool
    search_query: str
    search_results: List[Dict[str, Any]]
    final_response: str

def intent_detection_node(state: AppState) -> AppState:
    """
    Intent Detection Node - First node in the Langgraph workflow.
    Uses existing intent classification system to determine user intent.
    """
    query = state["query"]

    # Initialize ChatOpenAI client
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    try:
        intent, confidence, extras = classify_intent_llm(query, llm)

        return {
            **state,
            "intent": intent,
            "confidence": confidence,
            "extras": extras,
            "processed": True
        }
    except Exception as e:
        # Fallback on error
        return {
            **state,
            "intent": "unknown",
            "confidence": 0.0,
            "extras": {"error": str(e)},
            "processed": True
        }