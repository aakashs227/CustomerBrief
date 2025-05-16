import streamlit as st
import base64
import requests
from PIL import Image
from io import BytesIO
from docx import Document
import re

# Import your ai_agent logic (adjust import if ai_agent.py is in a different folder)
from ai_agent import run_agent

# --- Custom Styling ---
st.markdown("""
    <style>
        #MainMenu, header, footer {
            visibility: hidden;
            height: 0px;
        }
        section[data-testid="stSidebar"] {
            background-color: #002b5c;
        }
        .stButton button {
            background-color: white !important;
            color: black !important;
            border: 1px solid #999 !important;
        }
        .chat-history-item {
            color: yellow !important;
            font-size: 16px !important;
        }
        .top-right-logo {
            position: absolute;
            top: 10px;
            right: 30px;
            z-index: 1000;
        }
        .top-right-logo img {
            width: 150px;
            height: auto;
            display: block;
            border: none;
        }
    </style>
""", unsafe_allow_html=True)

# --- Load Logo ---
logo_url = "https://raw.githubusercontent.com/aakashs227/CustomerBrief/main/WORLDWIDE_Logo%207.png"
try:
    response = requests.get(logo_url)
    response.raise_for_status()
    logo = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    logo.save(buffered, format="PNG")
    logo_base64 = base64.b64encode(buffered.getvalue()).decode()
except Exception as e:
    st.error(f"❌ Error loading logo image: {e}")
    logo_base64 = ""

# --- Initialize session state ---
for key in ["chat_history", "last_query", "multiple_companies_warned", "selected_menu"]:
    if key not in st.session_state:
        if key == "chat_history":
            st.session_state[key] = []
        elif key == "multiple_companies_warned":
            st.session_state[key] = False
        else:
            st.session_state[key] = ""

# --- Sidebar ---
with st.sidebar:
    col_logo, col_button = st.columns([0.6, 0.4])
    with col_logo:
        st.markdown(
            f"""
            <div style="
                background-color: white;
                padding: 3px 0px;
                width: 100%;
                display: flex;
                justify-content: flex-start;
                align-items: center;
                box-sizing: border-box;
            ">
                <img src="data:image/png;base64,{logo_base64}" width="100" />
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown("""
        <h3 style="color: white; text-decoration: underline; margin-bottom: 10px;">
            Chat History
        </h3>
    """, unsafe_allow_html=True)

    for i, (q, a) in enumerate(reversed(st.session_state.chat_history)):
        index = len(st.session_state.chat_history) - 1 - i
        col1, col2 = st.columns([0.85, 0.15])
        with col1:
            st.markdown(
                f"<div class='chat-history-item'>• {q[:50]}</div>",
                unsafe_allow_html=True
            )
        with col2:
            if st.button("⋮", key=f"menu_{i}"):
                st.session_state.selected_menu = index

        if st.session_state.get("selected_menu") == index:
            button_cols = st.columns([1, 1, 1])
            with button_cols[0]:
                if st.button("👁 View", key=f"view_{i}", help="View"):
                    st.session_state.last_query = q
                    st.session_state.selected_menu = None

            with button_cols[1]:
                doc_buffer = BytesIO()
                doc = Document()
                doc.add_heading("MIRA Company Analysis", level=1)
                doc.add_paragraph(f"Query: {q}")
                doc.add_paragraph("Response:")
                doc.add_paragraph(a)
                doc.save(doc_buffer)
                doc_buffer.seek(0)
                st.download_button(
                    label="⬇️",
                    data=doc_buffer,
                    file_name=f"chat_history_{index+1}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"download_btn_{i}",
                    help="Download"
                )
            with button_cols[2]:
                if st.button("🗑 Delete", key=f"delete_{i}", help="Delete"):
                    st.session_state.chat_history.pop(index)
                    st.session_state.selected_menu = None

# --- Main UI ---
st.markdown("""
    <div style='background-color: #f4f4f4; padding: 25px; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: #333; margin: 0;'>Welcome to CustomerBrief</h1>
        <p style='font-size: 16px; color: #444; margin-top: 10px;'>
            AI-powered insights for sharper sales conversations.
        </p>
    </div>
""", unsafe_allow_html=True)

query = st.text_input(
    "Enter Company Name or Query:",
    placeholder="e.g., Tesla Inc",
    value=st.session_state.last_query
)

# --- Utility Functions ---
def slugify(text):
    return "".join(c if c.isalnum() else "_" for c in text.lower()).strip("_")

def generate_docx(query, response):
    doc = Document()
    doc.add_heading("MIRA Company Analysis", level=1)
    doc.add_paragraph(f"Query: {query}")
    doc.add_paragraph("Response:")
    doc.add_paragraph(response)
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def contains_multiple_companies(query):
    delimiters = [",", "&", " and ", "/", " vs ", " versus ", ";"]
    count = sum([query.lower().count(d) for d in delimiters])
    return count >= 1

def show_download_buttons(query, response, key_prefix="main"):
    st.markdown("### 🧠 Company Analysis")
    if contains_multiple_companies(query):
        if not st.session_state.multiple_companies_warned:
            st.warning(
                "⚠️ Important Notice: To ensure clarity and depth in analysis, our AI system is designed to evaluate one company at a time. Please revise your query to reference a single organization for a precise and comprehensive report. 🏢"
            )
            st.session_state.multiple_companies_warned = True
        st.write(response)
    else:
        file_name = f"{slugify(query)}.docx"
        docx_file_top = generate_docx(query, response)
        st.download_button(
            label="📥 Download Analysis",
            data=docx_file_top,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{key_prefix}_download_top"
        )
        st.write(response)
        docx_file_bottom = generate_docx(query, response)
        st.download_button(
            label="📥 Download Analysis",
            data=docx_file_bottom,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{key_prefix}_download_bottom"
        )

# --- Process Query ---
if st.button("Search"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        st.session_state.multiple_companies_warned = False
        if contains_multiple_companies(query):
            st.warning(
                "⚠️ To ensure clarity and depth, please analyze one company at a time."
            )
        else:
            with st.spinner("Generating analysis..."):
                # Use your ai_agent.py logic here instead of direct OpenAI call
                try:
                    answer = run_agent(query)  # Your custom AI agent function
                except Exception as e:
                    answer = f"❌ Error running AI agent: {e}"

                st.session_state.chat_history.append((query, answer))
                st.session_state.last_query = query
                st.experimental_rerun()

# --- Show last analysis ---
if st.session_state.chat_history:
    last_q, last_a = st.session_state.chat_history[-1]
    st.markdown(f"## Analysis for: **{last_q}**")
    show_download_buttons(last_q, last_a, key_prefix="current")
