import streamlit as st
import base64
import requests
from PIL import Image
from io import BytesIO
from docx import Document
import re
import openai
 
# --- Setup OpenAI API Key ---
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")
 
# --- Utility Functions ---
 
def clean_response(text):
    cleaned_text = re.sub(
        r"(🧠 Company Analysis\s*)(.*?)(?=\n\s*1\.\s*[🔍A-Z])",
        r"\1\n",
        text,
        flags=re.DOTALL
    )
    return cleaned_text.strip()
 
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
 
def call_openai_api(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1200,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"❌ OpenAI API error: {e}"
 
def show_download_buttons(query, response, key_prefix="main"):
    st.markdown("### 🧠 Company Analysis")
    if contains_multiple_companies(query):
        # Display warning only once
        if not st.session_state.get('multiple_companies_warned', False):
            st.warning("⚠️ Important Notice: To ensure clarity and depth in analysis, our AI system is designed to evaluate one company at a time. Please revise your query to reference a single organization for a precise and comprehensive report. 🏢")
            st.session_state.multiple_companies_warned = True
        st.write(response)
    else:
        file_name = f"{slugify(query)}.docx"
        docx_file = generate_docx(query, response)
        st.download_button(
            label="📥 Download Analysis",
            data=docx_file,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"{key_prefix}_download"
        )
        st.write(response)
 
# --- Page config ---
st.set_page_config(
    page_title="CustomerBrief AI-powered insights for sharper sales conversations.",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
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
 
# --- Load Logo from GitHub ---
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
    # Logo in sidebar header
    st.markdown(
        f"""
<div style="
            background-color: white;
            padding: 3px 0px 3px 0px;
            width: 100%;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            box-sizing: border-box;
        ">
<img src="data:image/png;base64,{logo_base64}" width="100" style="display: block;"/>
</div>
        """, unsafe_allow_html=True
    )
 
    st.markdown("---")
    st.markdown("""
<h3 style="color: white; text-decoration: underline; margin-bottom: 10px;">
            Chat History
</h3>
    """, unsafe_allow_html=True)
 
    # List chat history in sidebar
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
            btn_cols = st.columns([1,1,1])
            with btn_cols[0]:
                if st.button("👁 View", key=f"view_{i}", help="View"):
                    st.session_state.last_query = q
                    st.session_state.selected_menu = None
                    st.experimental_rerun()
            with btn_cols[1]:
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
            with btn_cols[2]:
                if st.button("🗑 Delete", key=f"delete_{i}", help="Delete"):
                    st.session_state.chat_history.pop(index)
                    if st.session_state.last_query == q:
                        st.session_state.last_query = ""
                    st.session_state.selected_menu = None
                    st.experimental_rerun()
 
# --- Logo top-right ---
if logo_base64:
    st.markdown(
        f"""
<div class="top-right-logo">
<img src="data:image/png;base64,{logo_base64}" alt="Logo" />
</div>
        """, unsafe_allow_html=True
    )
 
# --- Welcome Message ---
st.markdown("""
<div style='background-color: #f4f4f4; padding: 25px; border-radius: 10px; margin-bottom: 30px;'>
<h1 style='color: #333; margin: 0;'>Welcome to CustomerBrief</h1>
<p style='font-size: 16px; color: #444; margin-top: 10px;'>
            AI-powered insights for sharper sales conversations.
</p>
</div>
""", unsafe_allow_html=True)
 
# --- Input and Search ---
 
query = st.text_input(
    "Enter Company Name or Query:",
    placeholder="e.g., Tesla Inc",
    value=st.session_state.last_query
)
 
if st.button("Search"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        # Reset warning flag
        st.session_state.multiple_companies_warned = False
 
        if contains_multiple_companies(query):
            if not st.session_state.multiple_companies_warned:
                st.warning(
                    "⚠️ To ensure clarity and depth, please analyze one company at a time."
                )
                st.session_state.multiple_companies_warned = True
        else:
            with st.spinner("Generating analysis..."):
                result = call_openai_api(query)
                st.session_state.chat_history.append((query, result))
                st.session_state.last_query = query
                st.experimental_rerun()
 
# --- Display latest analysis ---
if st.session_state.chat_history:
    last_q, last_a = st.session_state.chat_history
