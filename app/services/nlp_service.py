from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from typing import Optional, Dict, Any
import os

# --- 1. Tải Model Intent (Bạn đã train) ---
print("Dang tai model Phobert Intent Classifier...")
intent_model_path = "./models/phobert-intent-classifier"

# Kiểm tra xem model đã được train và lưu chưa
if not os.path.exists(intent_model_path):
    print(f"CANH BAO: Khong tim thay model Intent tai '{intent_model_path}'.")
    print("Hay chay file 'train_intent_model.py' truoc.")
    print("NLP Service se su dung logic gia lap (fallback).")
    intent_classifier = None
else:
    try:
        intent_tokenizer = AutoTokenizer.from_pretrained(intent_model_path)
        intent_model = AutoModelForSequenceClassification.from_pretrained(intent_model_path)
        intent_classifier = pipeline(
            "text-classification",
            model=intent_model,
            tokenizer=intent_tokenizer
        )
        print("Tai model Phobert Intent thanh cong!")
    except Exception as e:
        print(f"LOI KHI TAI MODEL INTENT: {e}. Chuyen sang fallback.")
        intent_classifier = None


# --- 2. Tải Model Sentiment (Từ HuggingFace) ---
print("Dang tai model Vietnamese Sentiment...")
try:
    sentiment_classifier = pipeline(
        "text-classification",
        model="lct-distilbert-base-vietnamese-sentiment"
    )
    print("Tai model Sentiment thanh cong!")
except Exception as e:
    print(f"LOI KHI TAI MODEL SENTIMENT: {e}. Chuyen sang fallback.")
    sentiment_classifier = None


def process_nlp_tasks(text: str) -> Dict[str, Any]:
    print(f"[NLP Service] Dang xu ly text: '{text}'")
    
    # --- 3. Nhận diện Intent ---
    if intent_classifier:
        intent_result = intent_classifier(text)[0]
        intent = intent_result['label']
        intent_confidence = intent_result['score']
    else:
        # Fallback (nếu chưa train model)
        if "đặt lịch" in text: intent = "dat_lich"
        elif "hỏi" in text: intent = "hoi_thong_tin"
        else: intent = "unknown"
        intent_confidence = 0.5
        print("[NLP Service] Su dung fallback Intent.")

    # --- 4. Nhận diện Sentiment ---
    if sentiment_classifier:
        sentiment_result = sentiment_classifier(text)[0]
        sentiment = sentiment_result['label'].lower()
    else:
        sentiment = "neutral"
        print("[NLP Service] Su dung fallback Sentiment.")
    
    # --- 5. TODO: Nhận diện Entity (Slot) ---
    entities = {}
    if intent == "dat_lich" and "9h" in text:
        entities = {"time": "9h"}

    result = {
        "text": text,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "sentiment": sentiment,
        "entities": entities
    }
    
    print(f"[NLP Service] Ket qua: {result}")
    return result