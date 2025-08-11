# app/main.py
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from typing import List, Dict
from app.runner import handle_request

app = FastAPI(title="TDS Data Analyst Agent")

@app.get("/")
def read_root():
    return {"message": "TDS Data Analyst Agent - running"}

@app.post("/api/")
async def api_endpoint(files: List[UploadFile] = File(...)):
    """
    Expects multipart/form-data where questions.txt is always present.
    Example curl:
      curl -X POST http://127.0.0.1:8000/api/ -F "questions.txt=@questions.txt"
    """
    # Collect files into map; find questions.txt
    qfile = None
    other_files: Dict[str, UploadFile] = {}
    for f in files:
        if f.filename == "questions.txt":
            qfile = f
        else:
            other_files[f.filename] = f

    if qfile is None:
        raise HTTPException(status_code=400, detail="questions.txt missing")

    qbytes = await qfile.read()
    questions_text = qbytes.decode("utf-8", errors="replace")

    # Run main handler with a timeout (170s) to respect 3-minute limit
    try:
        result = await asyncio.wait_for(handle_request(questions_text, other_files), timeout=170)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Processing timed out")

    return result