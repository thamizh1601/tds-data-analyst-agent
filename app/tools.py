# app/tools.py
import requests
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from PIL import Image
from pypdf import PdfReader
from pdf2image import convert_from_bytes
from langchain.tools import tool
from typing import Dict, Any
import re
import html
import warnings
warnings.filterwarnings("ignore")

# Global REPL state (dict for variables)
repl_globals = {
    'pd': pd,
    'np': np,
    'plt': plt,
    'duckdb': duckdb,
    'requests': requests,
    # Add more if needed from your original libs
}

@tool
def code_execution(code: str) -> str:
    """
    Execute Python code in a stateful REPL. Use for data analysis, plotting, DuckDB queries, etc.
    For plots, generate fig, save to BytesIO as PNG, return base64 URI.
    """
    try:
        output = {}
        exec(code, repl_globals, output)
        if 'result' in output:
            return str(output['result'])
        return "Code executed successfully. No 'result' defined—define output['result'] for return."
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def browse_page(url: str, instructions: str) -> str:
    """
    Fetch webpage and summarize based on instructions.
    """
    try:
        headers = {"User-Agent": "tds-data-analyst-agent/1.0"}
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        text = resp.text[:20000]  # Truncate to avoid token limits
        # Summarize with LLM
        from .agent import get_llm
        llm = get_llm()
        prompt = f"Summarize/extract from this content based on: {instructions}\nContent: {text}"
        summary = llm.invoke(prompt).content
        return summary
    except Exception as e:
        return f"Error browsing: {str(e)}"

@tool
def web_search(query: str, num_results: int = 10) -> str:
    """
    Search web using DuckDuckGo.
    """
    from duckduckgo_search import DDGS
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=num_results)]
        return str(results)
    except Exception as e:
        return f"Error searching: {str(e)}"

@tool
def search_pdf_attachment(file_name: str, query: str, mode: str = "keyword") -> str:
    """
    Search PDF for relevant pages/snippets.
    """
    if file_name not in attachment_files:  # Global attachments from runner
        return "File not attached."
    try:
        file = attachment_files[file_name]
        reader = PdfReader(io.BytesIO(file))
        results = []
        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            if mode == "keyword" and query.lower() in text.lower():
                results.append(f"Page {page_num}: {text[:200]}...")
            elif mode == "regex" and re.search(query, text):
                results.append(f"Page {page_num}: {text[:200]}...")
        return str(results)
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def browse_pdf_attachment(file_name: str, pages: str) -> str:
    """
    Extract text and image base64 for pages (e.g., '1,3-5').
    """
    if file_name not in attachment_files:
        return "File not attached."
    try:
        file = attachment_files[file_name]
        reader = PdfReader(io.BytesIO(file))
        images = convert_from_bytes(file)
        results = {}
        page_list = []
        for p in pages.split(','):
            if '-' in p:
                start, end = map(int, p.split('-'))
                page_list.extend(range(start, end+1))
            else:
                page_list.append(int(p))
        for pg in page_list:
            text = reader.pages[pg-1].extract_text() or ""
            img_buf = io.BytesIO()
            images[pg-1].save(img_buf, format="PNG")
            img_b64 = base64.b64encode(img_buf.getvalue()).decode()
            results[pg] = {"text": text[:500], "image": f"data:image/png;base64,{img_b64}"}
        return str(results)
    except Exception as e:
        return f"Error: {str(e)}"

# Global for attachments (set in runner.py)
attachment_files: Dict[str, bytes] = {}