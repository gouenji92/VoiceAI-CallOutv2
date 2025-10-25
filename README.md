# VoiceAI-CallOutv2 — FastAPI + RL Threshold Tuning (Production Phase)

AI-powered Vietnamese callbot backend with PhoBERT intent classification, Deeppavlov agent, Supabase logging, and a reinforcement-learning (RL) module that learns per-intent confidence thresholds online.

This README replaces previous docs to avoid confusion. It reflects the current, working setup verified on Windows (PowerShell) with Python 3.11.

## What’s new in this phase

- Retrained intent model with augmented data (3 weak intents improved)
- Model manager defaults to the latest retrained model
- RL Threshold Tuner (epsilon-greedy + UCB1) integrated into NLP pipeline
- RL Monitoring router and a terminal dashboard
- End-to-end tests and quick sanity scripts
- Fixed routing and stability issues (0.0.0.0 vs localhost, RL status)

## Quick start (Windows PowerShell)

1) Create environment and install deps
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

2) Configure environment
```powershell
cp .env.example .env
# Edit .env with your Supabase project URL and service role key
```

3) Start API (use localhost, not 0.0.0.0 in the browser)
```powershell
python -X utf8 -m uvicorn app.main:app --reload --port 8000
# Visit: http://localhost:8000/docs
```

4) Optional: Start Agent (if your dialog manager needs it)
```powershell
python agent/run_agent.py
```

## RL monitoring

- Status: GET http://localhost:8000/api/rl-monitor/status
- Thresholds: GET http://localhost:8000/api/rl-monitor/thresholds

Terminal dashboard (optional):
```powershell
python monitor_rl_dashboard.py
```

## Testing

Run comprehensive system test suite (API health, model inference, NLP service, RL feedback, RAG, auth, agent):
```powershell
python test_system.py
```

Test results are saved to `test_results.json` with detailed diagnostics for each component.

For quick startup testing, use:
```powershell
START.bat
# Then run test_system.py in another terminal
```

## Endpoints (high level)

- Health: GET `/`
- Auth: `/api/auth/*` (requires Supabase + JWT)
- Workflows: `/api/workflows/*` (requires auth)
- Calls: `/api/calls/start_call`, `/api/calls/webhook`
	- Webhook body schema:
		- `call_id` (UUID in DB)
		- `speech_to_text` (string)
- Feedback: `/api/feedback/rl-reward` (no auth) and `/api/feedback/rl-stats` (auth)
- RL Monitor: `/api/rl-monitor/status`, `/api/rl-monitor/thresholds`, ...

## Models

- Default model path is set to the latest retrained folder in `app/services/model_manager.py`.
- Large model files are not tracked by Git. See `.gitignore`.

## Troubleshooting

- Browser cannot open 0.0.0.0: Use http://localhost:8000 or http://127.0.0.1:8000
- RL status 500: has been fixed (attribute name mismatch). Pull latest.
- Supabase errors with UUID: Webhook requires a real `call_id` present in `calls` table.
- Sentiment model warning: The service falls back if the public model is unavailable.

## 📚 Documentation

- **Database Schema**: [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md) - Tài liệu chi tiết về cấu trúc database (tiếng Việt)
- **Phase Summary**: [`PHASE_SUMMARY.md`](PHASE_SUMMARY.md) - Tổng kết giai đoạn RL + Retrain
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md) - Chi tiết thay đổi theo phiên bản

## License

MIT
