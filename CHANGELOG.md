# Changelog

All notable changes for this phase (2025-10-24) are documented here.

## Phase: RL Threshold Tuning + Retrained Model

- Added RL Threshold Tuner (contextual epsilon-greedy + UCB1)
  - Arms: thresholds [0.80..0.95]
  - Epsilon decay with persistence to `models/rl_threshold_state.json`
- Integrated RL into `nlp_service.process_nlp_tasks` and feedback endpoints
- Implemented RL Monitoring router `/api/rl-monitor/*` and a terminal dashboard
- Retrained PhoBERT intent classifier with augmented data
  - Improved weak intents: `yeu_cau_ho_tro`, `tu_choi`, `khieu_nai`
  - Default model path now points to latest retrained folder
- Added testing scripts:
  - `test_retrained_model.py` (HF direct inference)
  - `test_api_retrained.py` (FastAPI pipeline)
  - `quick_test.py` (sanity)
  - `test_production.py` (comprehensive E2E)
- Fixed routing and status issues:
  - RL monitor router prefix consistency
  - RL status attribute mismatch (epsilon_min → min_epsilon)
  - Webhook schema uses `speech_to_text`
- Updated README (full replacement) and `.gitignore` to exclude `models/`
