# app/runner.py
import asyncio
from typing import Dict
from fastapi import UploadFile
from .agent import run_agent
from .tools import attachment_files  # Global

async def handle_request(questions_text: str, other_files: Dict[str, UploadFile]):
    """
    Handle request with LLM agent.
    """
    # Read attachments to bytes
    attachments = []
    global attachment_files
    attachment_files = {}
    for fname, file in other_files.items():
        attachments.append(fname)
        bytes_data = await file.read()
        attachment_files[fname] = bytes_data

    # Run agent
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(run_agent, questions_text, attachments),
            timeout=170
        )
    except asyncio.TimeoutError:
        result = "Error: Timeout"
    except Exception as e:
        result = f"Error: {str(e)}"

    # Return as {"response": result} — evaluator expects this
    return {"response": result}