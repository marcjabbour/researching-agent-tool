from typing import Tuple, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from tools.intent_identifying.intents_data import INTENT,INTENT_JSON_SCHEMA, INTENT_SYSTEM_PROMPT

def classify_intent_llm(query: str, llm: ChatOpenAI) -> Tuple[INTENT, float, Dict[str, Any]]:
    """
    Classify query intent using ChatOpenAI with structured JSON output.

    Args:
        query: The user query to classify
        llm: ChatOpenAI instance

    Returns:
        Tuple of (intent, confidence, extras_dict)
        where extras_dict includes entities, attributes, depth, rationale when present

    Raises:
        Exception: Any LLM-related errors (caller should handle fallback)
    """
    system_prompt = INTENT_SYSTEM_PROMPT
    user_prompt = f"Classify this VC research query: '{query}'"

    # Configure LLM for structured output - add title and description for OpenAI
    schema_with_metadata = {
        "title": "IntentClassification",
        "description": "Classification of user query intent for VC research",
        **INTENT_JSON_SCHEMA
    }

    structured_llm = llm.with_structured_output(schema_with_metadata)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = structured_llm.invoke(messages)

    intent = response.get("intent", "unknown")
    confidence = response.get("confidence", 0.0)

    # Build extras dict with all additional fields
    extras = {}
    if "entities" in response:
        extras["entities"] = response["entities"]
    if "attributes" in response:
        extras["attributes"] = response["attributes"]
    if "depth" in response:
        extras["depth"] = response["depth"]
    if "rationale" in response:
        extras["rationale"] = response["rationale"]

    # If confidence is too low, force intent to unknown
    if confidence < 0.65:
        intent = "unknown"

    return (intent, confidence, extras)