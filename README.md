# LLM-Driven Generative Visualisation Pipeline

An MSc dissertation project at the University of Edinburgh, School of Informatics.

## What is this?

A web-based tool that transforms natural language questions about global fraud and cybercrime data into interactive, multi-chart dashboards. Ask a question in plain English, and the system generates a complete dashboard with live data.

## How does it work?

The system uses a large language model to convert your natural language query into both a database query and a set of visualisation specifications. These are validated, executed against a live database, and rendered into an interactive dashboard — all in a single request.

Key architectural choices:

- **Single-call generation** — The LLM generates both the SQL query and the visualisation specification together, ensuring they stay consistent with each other
- **Template-constrained layout** — Dashboards use one of two predefined templates (Focused or Informative) rather than free-form generation, improving reliability
- **Self-healing validation** — If the LLM produces an invalid output, the system automatically re-prompts it with the error details, up to three attempts
- **Vega-Lite** — Charts use a declarative JSON specification that can be validated programmatically before rendering

## How to use it

### Boot App

- **Database** (from repo root): `docker compose up -d`
- **Backend** (run from the **repo root**, not inside `backend/`, so `backend.*` imports resolve):
  - `python3 -m venv backend/.venv`
  - `backend/.venv/bin/python -m pip install -r backend/requirements.txt`
  - `backend/.venv/bin/python -m uvicorn backend.main:app --reload`
- **Frontend**: `cd frontend && npm install && npm run dev`

1. Navigate to the application URL below
2. Enter a natural language query about fraud or cybercrime data (e.g. *"Show me phishing incidents in Southeast Asia over the past year"*)
3. The system generates and displays an interactive dashboard
4. Refine your query to explore the data further

# URLs

- Frontend: http://localhost:5173 (Vite default)
- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs


## Tech Stack

- **Frontend**: React, Vega-Lite
- **Backend**: FastAPI (Python)
- **LLM Access**: ELM (University of Edinburgh)
- **Database**: PostgreSQL (GDELT-sourced data)

## Author

Jonathan — MSc Informatics, University of Edinburgh

Supervised by Professor Jingjie Li