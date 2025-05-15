
# ai_agent.py

import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Custom system prompt
DEFAULT_PROMPT = (
    "You are an expert business intelligence analyst. When given a company name, provide a detailed report with the following structure:\n\n"
    "1. 🔍 Company Overview\n"
    "2. 💰 Financial Summary (Revenue, Profit, Funding, etc.)\n"
    "3. 📦 Import Activity\n"
    "4. 🚢 Export Activity\n"
    "5. 🌍 Global Presence & Offices\n"
    "6. 🚛 Freight Forwarding History\n"
    "7. 📌 Actionable Insights\n"
    "8. 🔗 List of References (with clickable links)\n\n"
    "In detail business overview ,Be clear, concise, and use bullet points or headings for readability. Ensure references are provided within each category itself."
)

def clean_ai_response(response_text: str) -> str:
    """
    Removes the initial disclaimer paragraph from the AI response if it contains fallback indicators.
    """
    # Split the response into paragraphs
    paragraphs = response_text.strip().split("\n\n")

    # Define keywords that identify fallback/disclaimer text
    fallback_indicators = [
        "issue retrieving real-time data",
        "based on my expert knowledge",
        "latest publicly available information",
        "compiled from public sources",
        "prior to june 2024",
        "i can provide a report",
        "real-time data isn't available"
    ]

    # Check if the first paragraph contains any fallback indicators
    first_paragraph = paragraphs[0].lower()
    if any(keyword in first_paragraph for keyword in fallback_indicators):
        # Remove the first paragraph
        paragraphs = paragraphs[1:]

    # Reconstruct the response without the disclaimer
    return "\n\n".join(paragraphs).strip()





def get_response_from_ai_agent(llm_id, query, allow_search):
    # Define a list of common company suffixes
    company_suffixes = ['Inc', 'Ltd', 'LLC', 'PLC', 'GmbH','Industries', 'AG', 'Corp', 'Corporation', 'Co', 'Pvt', 'Limited', 'Group', 'S.A.', 'S.A.S.', 'S.L.', 'S.L.U.']

    # Create a regex pattern to detect company names with the defined suffixes
    suffix_pattern = r'\b(?:[A-Z][a-zA-Z&.\'-]*\s?)+(?:' + '|'.join(company_suffixes) + r')\b'
    # Also, detect standalone capitalized words (assuming they might be company names)
    capitalized_pattern = r'\b[A-Z][a-zA-Z&.\'-]{2,}\b'

    # Find all matches for company names in the query
    from company_utils import extract_companies
    potential_companies = extract_companies(query)


    # If more than one potential company is detected, prompt the user to specify one
    if len(potential_companies) > 1:
        return "⚠️ Important Notice: To ensure clarity and depth in analysis, our AI system is designed to evaluate one company at a time. Please revise your query to reference a single organization for a precise and comprehensive report. 🏢"

    # Proceed with generating the response if only one company is detected
    llm = ChatOpenAI(model=llm_id)

    tools = [TavilySearchResults(max_results=5)] if allow_search else []

    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=DEFAULT_PROMPT
    )

    state = {"messages": query}
    response = agent.invoke(state)

    messages = response.get("messages")
    ai_messages = [msg.content for msg in messages if isinstance(msg, AIMessage)]
    return ai_messages[-1] if ai_messages else "No response generated."

    


    