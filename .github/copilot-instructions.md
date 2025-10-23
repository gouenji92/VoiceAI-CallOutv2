# Copilot Instructions for VoiceAI-CallOutv2

## Project Overview
VoiceAI-CallOutv2 is an AI-powered callbot backend built with FastAPI, Supabase (PostgreSQL), and HuggingFace Transformers. It manages user authentication, workflow versioning, call orchestration, and NLP tasks (intent, sentiment, entity extraction) for Vietnamese language voice automation.

## Architecture & Key Components
- **FastAPI app** (`app/`):
  - `main.py`: App entry, includes routers for `/auth`, `/workflows`, `/calls`.
  - `routers/`: API endpoints for authentication, workflow management, and call handling.
  - `models.py`: Pydantic models for API schemas (Token, Workflow, Call, etc.).
  - `services/`: Business logic for NLP (`nlp_service.py`), dialog management (`dialog_manager.py`), Asterisk integration, and model management.
  - `database.py`: Supabase client setup using env vars from `.env`.
- **Agent** (`agent/`):
  - `run_agent.py`, `skill.py`: Deeppavlov agent for dialog logic, receives state from FastAPI via HTTP (see `dialog_manager.py`).
- **ML Models** (`models/phobert-intent-classifier/`):
  - HuggingFace Transformers model for intent classification (Phobert-based). Trained via `train_intent_model.py`.
- **Data** (`data/`, `db/`, `sql/`):
  - Datasets, database schema (`sql/schema.sql`), and migration scripts.

## Data Flow
1. **User calls** → `/calls/start_call` creates a call record, triggers Asterisk (simulated in `asterisk_service.py`).
2. **Speech-to-text** → `/calls/webhook` receives user utterance, runs NLP pipeline (`nlp_service.py`), sends state to Deeppavlov agent (`dialog_manager.py`).
3. **Agent** returns bot response and action, which is logged and sent back to the voice gateway.
4. **All interactions** are logged in Supabase tables (`calls`, `conversation_logs`, etc.).

## Developer Workflows
- **Setup** (see `README.md`):
  1. `python -m venv .venv && .\.venv\Scripts\Activate.ps1`
  2. `python -m pip install -r requirements.txt`
  3. `python -X utf8 -m uvicorn app.main:app --reload`
- **Train intent model:** `python train_intent_model.py` (outputs to `models/phobert-intent-classifier/`)
- **Run agent:** `python agent/run_agent.py` (must be running for dialog manager to work)
- **Test API:** Use `test.py` or `test_api.py` for Supabase and API integration tests.

## Conventions & Patterns
- **Supabase integration:** All DB access via `supabase-py` client. Credentials in `.env`.
- **Workflow versioning:** Each workflow can have multiple versions (`workflow_versions`), with `current_version_id` pointer in `workflows`.
- **NLP fallback:** If model files are missing, `nlp_service.py` uses rule-based fallback logic.
- **Error handling:** Most API errors are surfaced as HTTPException with clear messages. Check logs for details.
- **Vietnamese language:** All NLP and dialog logic is tailored for Vietnamese; intent labels and responses are in Vietnamese.

## Integration Points
- **Asterisk/Voice Gateway:** Simulated in `asterisk_service.py` (replace with real AMI logic as needed).
- **Deeppavlov Agent:** Communicates via HTTP (default `localhost:4242`).
- **Supabase:** Used for all persistent storage (accounts, calls, logs, feedback, etc.).
- **HuggingFace Transformers:** Used for intent and sentiment classification.

## Example: Adding a New Intent
1. Update training data in `train_intent_model.py`.
2. Retrain model and save to `models/phobert-intent-classifier/`.
3. Update dialog logic in `agent/skill.py` to handle new intent.

## Troubleshooting
- If you see `Internal Server Error` on registration, check Supabase schema for required fields and unique constraints (see `sql/schema.sql`).
- If NLP fails, ensure model files exist and are compatible with installed `torch`/`transformers` versions.
- For real-time logs, see `test_realtime.html` for Supabase JS client example.

---
For more details, see `README.md`, `app/services/`, and `sql/schema.sql`.
