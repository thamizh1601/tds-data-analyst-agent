
# tds-data-analyst-agent

Data Analyst Agent API using Gemini LLM for general data tasks.

## Setup

1. `pip install -r requirements.txt`
2. Add .env with GOOGLE_API_KEY
3. Run: `uvicorn app.main:app --reload`

## API

POST /api/ with multipart/form-data:

- questions.txt (required): Task and questions.
- Optional: Other files (CSV, PDF, etc.).

Example curl:
curl -X POST http://127.0.0.1:8000/api/ -F "questions.txt=@questions.txt"

## Deployment

Docker build: `docker build -t tds-agent .`
Run: `docker run -p 8000:8000 --env-file .env tds-agent`

Deploy to Render.com.

## LLM Configuration

Uses Google Gemini API. Set GOOGLE_API_KEY in .env.
