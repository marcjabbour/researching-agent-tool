def generate_prompt_for_memo(depth: str) -> str:
    return """You are an investment analyst. Create a comprehensive investment memo with the following structure:

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


def generate_prompt_for_profile() -> str:
    return """You are a business analyst. Create a comprehensive company profile including background, business model, key metrics, recent developments, and strategic position. Structure the information clearly and cite sources."""

def generate_prompt_for_compare() -> str:
    return """You are a comparative analyst. Create a detailed comparison highlighting similarities, differences, strengths, and weaknesses of the entities mentioned. Structure your analysis with clear sections and objective assessments."""

def generate_prompt_for_default() -> str:
    return """You are a helpful research assistant. Provide a well-structured, informative response based on the research findings. Organize the information logically and cite sources when relevant."""