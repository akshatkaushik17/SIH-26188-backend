# SIH-26188 Backend API Handoff

## Backend

FastAPI-based document verification backend for SIH-26188.

## Start the Backend

From the project directory:

```bash
cd ~/SIH-26188-backend
source venv/bin/activate
uvicorn AI.api:app --host 127.0.0.1 --port 8000
