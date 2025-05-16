# Backend.py

import os
import re
from fastapi import FastAPI, HTTPException
import base64
from pydantic import BaseModel
from typing import List
from ai_agent import get_response_from_ai_agent
from file_operations import generate_docx_file, generate_share_link

app = FastAPI(title="Company Info AI Agent")

# Allowed model names
ALLOWED_MODELS = [
    "gpt-4.1-2025-04-14"
]

# Request schema for chat endpoint
class ChatRequest(BaseModel):
    model_name: str
    messages: List[str]
    allow_search: bool

# Extract potential company names from the query
from company_utils import extract_companies


# /chat endpoint
@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    if request.model_name not in ALLOWED_MODELS:
        raise HTTPException(status_code=400, detail="Invalid model name selected.")

    user_query = request.messages[-1] if request.messages else ""

    # Detect multiple companies in the query
    potential_companies = extract_companies(user_query)
    if len(potential_companies) > 1:
        return {"response": "⚠️ Important Notice: To ensure clarity and depth in analysis, our AI system is designed to evaluate one company at a time. Please revise your query to reference a single organization for a precise and comprehensive report. 🏢"}

    try:
        response = get_response_from_ai_agent(
            llm_id=request.model_name,
            query=user_query,
            allow_search=request.allow_search
        )

        if not response or len(response.strip()) < 10:
            raise ValueError("Empty or invalid AI response")

    except Exception as e:
       print(f"[Error] AI agent failed: {str(e)}")
       raise HTTPException(status_code=500, detail="AI agent could not generate a valid response.")

    return {"response": response}

# /download endpoint
@app.post("/download")
def download_endpoint(data: dict):
    query = data.get("query")
    response = data.get("response")

    if query and response:
        content = f"Company Query: {query}\n\nCompany Analysis: {response}"
        docx_file = generate_docx_file(content)
        base64_doc = base64.b64encode(docx_file.getvalue()).decode()
        download_link = (
            f"data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{base64_doc}"
        )
        return {"download_url": download_link}

    raise HTTPException(status_code=400, detail="No data to download.")

# /share endpoint
@app.post("/share")
def share_endpoint(data: dict):
    query = data.get("query")
    response = data.get("response")

    if query and response:
        content = f"Company Query: {query}\n\nCompany Analysis: {response}"
        share_link = generate_share_link(content)
        return {"shareable_url": share_link}

    raise HTTPException(status_code=400, detail="No data to share.")

