import streamlit as st
import os
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage

# Load environment variables (make sure .env file exists with keys if needed)
load_dotenv()

# --- Constants ---
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
    "In detailed business overview, be clear, concise, and use bullet points or headings for readability. Ensure references are provided within each category itself."
)

# For simplicity, get keys from Streamlit secrets (set in your Streamlit Cloud or local .streamlit/secrets.toml)
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", None)

if OPENAI_API_KEY is None or TAVILY_API_KEY is None:
    st.error("API keys for OpenAI or Tavily not found! Please set them in Streamlit secrets.")
    st.stop()

# --- AI Agent Logic ---

def clean_ai_response(response_text: str) -> str:
    paragraphs = response_text.strip().split("\n\n")
    fallback_indicators = [
        "issue retrieving real-time data",
        "based on my expert knowledge",
        "latest publicly available information",
        "compiled from public sources",
        "prior to june 2024",
        "i can provide a report",
        "real-time data isn't available"
    ]
    first_paragraph = paragraphs[0].lower()
    if any(keyword in first_paragraph for keyword in fallback_indicators):
        paragraphs = paragraphs[1:]
    return "\n\n".join(paragraphs).strip()


# Dummy function to simulate `extract_companies` from company_utils, basic version
def extract_companies(text):
    company_suffixes = ['Inc', 'Ltd', 'LLC', 'PLC', 'GmbH','Industries', 'AG', 'Corp', 'Corporation', 'Co', 'Pvt', 'Limited', 'Group', 'S.A.', 'S.A.S.', 'S.L.', 'S.L.U.']
    suffix_pattern = r'\b(?:[A-Z][a-zA-Z&.\'-]*\s?)+(?:' + '|'.join(company_suffixes) + r')\b'
    matches = re.findall(suffix_pattern, text)
    # If no suffix matches, fallback to capitalized words longer than 3 chars
    if not matches:
        matches = re.findall(r'\b[A-Z][a-zA-Z&.\'-]{2,}\b', text)
    return matches

def get_response_from_ai_agent(llm_id, query, allow_search):
    potential_companies = extract_companies(query)

    if len(potential_companies) > 1:
        return ("⚠️ Important Notice: To ensure clarity and depth in analysis, our AI system is designed to evaluate one company at a time. "
                "Please revise your query to reference a single organization for a precise and comprehensive report. 🏢")

    # Set environment variables for API keys (required by langchain)
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY

    llm = ChatOpenAI(model=llm_id)

    tools = [TavilySearchResults(max_results=5)] if allow_search else []

    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=DEFAULT_PROMPT
    )

    state = {"messages": query}
    response = agent.invoke(state)

    messages = response.get("messages", [])
    ai_messages = [msg.content for msg in messages if isinstance(msg, AIMessage)]
    if ai_messages:
        cleaned = clean_ai_response(ai_messages[-1])
        return cleaned
    else:
        return "No response generated."


# --- Streamlit App UI ---

st.set_page_config(page_title="MIRA - Business Intelligence Chatbot", page_icon="🤖")

st.title("🤖 MIRA - Company Business Intelligence Chatbot")

# Session State for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

query = st.text_area("Enter your company query here:", height=120)

col1, col2 = st.columns([1,1])
with col1:
    if st.button("Analyze"):
        if not query.strip():
            st.warning("Please enter a company query first.")
        else:
            # Call AI Agent
            with st.spinner("Analyzing..."):
                response = get_response_from_ai_agent("gpt-4o", query, allow_search=True)
                st.session_state.chat_history.append((query, response))

with col2:
    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.experimental_rerun()

# Display chat history
for i, (user_q, ai_a) in enumerate(st.session_state.chat_history):
    st.markdown(f"### 🗣️ You:\n{user_q}")
    st.markdown(f"### 🤖 MIRA:\n{ai_a}")
    st.markdown("---")
