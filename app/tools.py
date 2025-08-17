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
from .scraper import fetch_tables_from_url

warnings.filterwarnings("ignore")

# Global REPL state
repl_globals = {
    'pd': pd,
    'np': np,
    'plt': plt,
    'duckdb': duckdb,
    'requests': requests,
    'fetch_tables_from_url': fetch_tables_from_url,
}

@tool
def code_execution(code: str) -> str:
    """
    Execute Python code in a stateful REPL for data analysis and plotting.
    Use fetch_tables_from_url(url) to scrape tables as DataFrames.
    For plots, generate fig, save to BytesIO as PNG, return base64 URI <100KB.
    Set output['result'] to the final answer (list for JSON array, dict for JSON object).
    Check DataFrame columns with .columns; use df['column_name'] (e.g., df['Title']).
    Avoid integer indices (e.g., df[0]) unless verified as column names.
    Example for Wikipedia table:
        tables = fetch_tables_from_url(url)
        df = tables[0]  # Main table
        print(df.columns)  # ['Rank', 'Peak', 'Title', 'Worldwide gross', 'Year', 'Ref']
        output['result'] = [...]  # Set result
    Debug: Print the code being executed.
    """
    try:
        print("Executing code:", code)  # Debug
        output = {}
        exec(code, repl_globals, output)
        if 'result' in output:
            return str(output['result'])
        return "Code executed successfully. No 'result' defined—define output['result']."
    except Exception as e:
        return f"Error in code_execution: {str(e)}"

@tool
def browse_page(url: str, instructions: str) -> str:
    """
    Fetch webpage tables, clean 'Worldwide gross' column, and return as string.
    """
    try:
        tables = fetch_tables_from_url(url)
        if not tables:
            return "No tables found on the page."
        result = []
        for i, table in enumerate(tables):
            # Clean column names
            table.columns = [str(col).replace('\n', ' ').strip() for col in table.columns]
            # For main table, set expected columns and clean 'Worldwide gross'
            if i == 0:
                expected_columns = ['Rank', 'Peak', 'Title', 'Worldwide gross', 'Year', 'Ref']
                table.columns = expected_columns[:len(table.columns)] if len(table.columns) >= len(expected_columns) else table.columns
                # Clean 'Worldwide gross': remove $, commas, and annotations (e.g., T, RK, [note])
                table['Worldwide gross'] = table['Worldwide gross'].astype(str).str.replace(r'[$,]', '', regex=True)
                table['Worldwide gross'] = table['Worldwide gross'].str.replace(r'[TRK]\[.*?\]|\[.*?\]', '', regex=True).str.strip()
                table['Worldwide gross'] = pd.to_numeric(table['Worldwide gross'], errors='coerce')
                # Convert Year to numeric
                table['Year'] = pd.to_numeric(table['Year'], errors='coerce')
            result.append(f"Table {i+1}:\n{table.to_string()[:2000]}...")
        return "\n".join(result)
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
    if file_name not in attachment_files:
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

# Global for attachments
attachment_files: Dict[str, bytes] = {}