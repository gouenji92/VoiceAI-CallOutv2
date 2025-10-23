# VoiceAI-CallOutv2 — Quick setup

Basic steps to get the project running (Windows PowerShell):

1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install requirements

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# If you need CPU-only torch, use PyTorch's CPU wheels (example):
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

3. Run the API

```powershell
python -X utf8 -m uvicorn app.main:app --reload
```

4. Train intent model (optional)

```powershell
python train_intent_model.py
```

Notes:
- If `transformers.pipeline` import fails due to torch/torchvision mismatches, the app uses a fallback in `app/services/nlp_service.py` so the API can start. To enable full pipeline functionality, install compatible `torch` and `torchvision` versions.
- For training on large datasets or GPUs, consider using Hugging Face Accelerate or running in a GPU-enabled environment (Colab / AWS / GCP).
