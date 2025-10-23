from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional, Dict, Any
import os
import json
from app.services.model_manager import get_model, reload_model
from app.services.rl_threshold_tuner import get_tuner
from pathlib import Path

# We'll import `pipeline` lazily because importing it at module import time
# can pull optional heavy dependencies (torch/torchvision) that may not be
# available or compatible in the runtime where the FastAPI app starts.
try:
    from transformers import pipeline as hf_pipeline
except Exception as e:
    hf_pipeline = None
    print(f"Warning: transformers.pipeline not available at import time: {e}")

print("Initializing NLP service and trying to load intent model from model_manager...")

# Load per-intent confidence thresholds
CONFIDENCE_THRESHOLDS = {}
try:
    config_path = Path("models/phobert-intent-v3/final/training_config.json")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            CONFIDENCE_THRESHOLDS = config.get('confidence_thresholds', {})
        print(f"Loaded confidence thresholds: {CONFIDENCE_THRESHOLDS}")
    else:
        # Fallback thresholds if config not found
        CONFIDENCE_THRESHOLDS = {
              'dat_lich': 0.85,
              'hoi_thong_tin': 0.85,
              'unknown': 0.60,
              'cam_on': 0.85,
              'tam_biet': 0.90,
              'xac_nhan': 0.85,
              'tu_choi': 0.85,
              'hoi_gio_lam_viec': 0.85,
              'hoi_dia_chi': 0.85,
              'khieu_nai': 0.85,
              'yeu_cau_ho_tro': 0.85
        }
        print(f"Using default confidence thresholds")
except Exception as e:
    print(f"Error loading confidence thresholds: {e}")
    CONFIDENCE_THRESHOLDS = {
        'dat_lich': 0.70,
        'hoi_thong_tin': 0.65,
        'unknown': 0.60,
        'cam_on': 0.75,
        'tam_biet': 0.75
    }

# helper to get a callable classifier (pipeline) from the live model
def _get_intent_classifier():
    model, tokenizer = get_model()
    if model is None or tokenizer is None:
        return None
    if hf_pipeline is None:
        return None
    return hf_pipeline("text-classification", model=model, tokenizer=tokenizer)

intent_classifier = _get_intent_classifier()

def reload_intent_model(path: str = None):
    """Reload model from disk (or given path) and refresh pipeline."""
    try:
        reload_model(path)
        global intent_classifier
        intent_classifier = _get_intent_classifier()
        return True
    except Exception as e:
        print(f"Failed to reload model: {e}")
        return False


# --- 2. Tải Model Sentiment (Từ HuggingFace) ---
print("Dang tai model Vietnamese Sentiment...")
try:
    if hf_pipeline is None:
        raise RuntimeError("transformers.pipeline is not available")
    sentiment_classifier = hf_pipeline(
        "text-classification",
        model="vinai/phobert-base-vietnamese-sentiment"
    )
    print("Tai model Sentiment thanh cong!")
except Exception as e:
    print(f"LOI KHI TAI MODEL SENTIMENT: {e}. Chuyen sang fallback.")
    sentiment_classifier = None


import asyncio
from datetime import datetime
from app.database import supabase

def save_conversation_log(call_id: str, speaker: str, text: str, intent: str = None, confidence: float = None):
    """Lưu log cuộc hội thoại theo cấu trúc database"""
    try:
        # Kiểm tra và định dạng dữ liệu theo cấu trúc DB
        log_data = {
            'call_id': call_id,
            'speaker': speaker,
            'text': text,
            'intent': intent,
            'confidence': confidence,
            'created_at': datetime.now().isoformat()
        }
        
        # Validate required fields theo schema
        required_fields = ['call_id', 'speaker', 'text']
        for field in required_fields:
            if not log_data.get(field):
                raise ValueError(f"Thiếu trường bắt buộc: {field}")
        
        # Insert với error handling
        try:
            response = supabase.table('conversation_logs').insert(log_data).execute()
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Supabase error: {response.error}")
            print(f"[NLP Service] Đã lưu log hội thoại: {text}")
        except Exception as db_error:
            print(f"[NLP Service] Lỗi database: {str(db_error)}")
            return False
        
        # Lưu feedback cho trường hợp confidence thấp
        if confidence and confidence < 0.7:
            try:
                feedback_data = {
                    'call_id': call_id,
                    'text': text,
                    'intent': intent,
                    'confidence': confidence,
                    'created_at': datetime.now().isoformat(),
                    'reviewed': False
                }
                feedback_response = supabase.table('feedback').insert(feedback_data).execute()
                if hasattr(feedback_response, 'error') and feedback_response.error:
                    raise Exception(f"Supabase error: {feedback_response.error}")
                print(f"[NLP Service] Đã lưu feedback cho text có độ tin cậy thấp")
            except Exception as fb_error:
                print(f"[NLP Service] Lỗi khi lưu feedback: {str(fb_error)}")
                # Không return False ở đây vì log chính đã được lưu thành công
        
        return True
        
    except Exception as e:
        print(f"[NLP Service] Lỗi khi lưu dữ liệu: {str(e)}")
        return False

def process_nlp_tasks(text: str, call_id: Optional[str] = None, use_rl_threshold: bool = True) -> Dict[str, Any]:
    print(f"[NLP Service] Dang xu ly text: '{text}' (call_id={call_id})")
    
    # --- 3. Nhận diện Intent với Per-Intent Confidence Thresholds ---
    intent = "unknown"
    intent_confidence = 0.0
    raw_intent = None
    raw_confidence = 0.0
    
    if intent_classifier:
        try:
            intent_result = intent_classifier(text)[0]
            raw_intent = intent_result['label']
            raw_confidence = intent_result['score']
            
            # Apply per-intent threshold
            # Option 1: Use RL tuner (adaptive threshold)
            # Option 2: Use static configured threshold
            if use_rl_threshold:
                tuner = get_tuner()
                context = {
                    'text_length': len(text),
                    'raw_confidence': raw_confidence,
                    'sentiment': 'unknown'  # Will be filled later
                }
                threshold = tuner.get_threshold(
                    intent=raw_intent,
                    raw_confidence=raw_confidence,
                    context=context,
                    call_id=call_id
                )
            else:
                # Static threshold (fallback)
                configured = CONFIDENCE_THRESHOLDS.get(raw_intent, 0.85)
                threshold = min(configured, 0.90)
            
            if raw_confidence >= threshold:
                intent = raw_intent
                intent_confidence = raw_confidence
                print(f"[NLP Service] Intent = {intent} (confidence: {intent_confidence:.2f}, threshold: {threshold:.2f}) ✓")
            else:
                # Confidence below threshold, mark as low_confidence
                intent = "unknown"
                intent_confidence = raw_confidence
                print(f"[NLP Service] Intent = {raw_intent} rejected (confidence: {raw_confidence:.2f} < threshold: {threshold:.2f})")
                print(f"[NLP Service] Falling back to 'unknown'")
        except Exception as e:
            print(f"[NLP Service] Loi khi nhan dien intent: {str(e)}")
            print("[NLP Service] Chuyen sang fallback intent")
            # Fallback khi có lỗi
            if "đặt lịch" in text or "hẹn" in text:
                intent = "dat_lich"
                intent_confidence = 0.6
            elif "hỏi" in text or "thông tin" in text:
                intent = "hoi_thong_tin"
                intent_confidence = 0.6
            elif "đồng ý" in text or "OK" in text or "được" in text or "xác nhận" in text:
                intent = "xac_nhan"
                intent_confidence = 0.6
            elif "không" in text or "từ chối" in text or "thôi" in text:
                intent = "tu_choi"
                intent_confidence = 0.6
            elif "giờ làm việc" in text or "mở cửa" in text or "lịch làm việc" in text:
                intent = "hoi_gio_lam_viec"
                intent_confidence = 0.6
            elif "địa chỉ" in text or "ở đâu" in text or "cách tìm" in text:
                intent = "hoi_dia_chi"
                intent_confidence = 0.6
            elif "khiếu nại" in text or "không hài lòng" in text or "tệ" in text or "thất vọng" in text:
                intent = "khieu_nai"
                intent_confidence = 0.6
            elif "hỗ trợ" in text or "giúp" in text or "trợ giúp" in text:
                intent = "yeu_cau_ho_tro"
                intent_confidence = 0.6
            else:
                intent = "unknown"
                intent_confidence = 0.5
    else:
        # Fallback (nếu chưa train model)
        if "đặt lịch" in text or "hẹn" in text: 
            intent = "dat_lich"
            intent_confidence = 0.6
        elif "hỏi" in text or "thông tin" in text: 
            intent = "hoi_thong_tin"
            intent_confidence = 0.6
        elif "đồng ý" in text or "OK" in text or "được" in text or "xác nhận" in text:
            intent = "xac_nhan"
            intent_confidence = 0.6
        elif "không" in text or "từ chối" in text or "thôi" in text:
            intent = "tu_choi"
            intent_confidence = 0.6
        elif "giờ làm việc" in text or "mở cửa" in text or "lịch làm việc" in text:
            intent = "hoi_gio_lam_viec"
            intent_confidence = 0.6
        elif "địa chỉ" in text or "ở đâu" in text or "cách tìm" in text:
            intent = "hoi_dia_chi"
            intent_confidence = 0.6
        elif "khiếu nại" in text or "không hài lòng" in text or "tệ" in text or "thất vọng" in text:
            intent = "khieu_nai"
            intent_confidence = 0.6
        elif "hỗ trợ" in text or "giúp" in text or "trợ giúp" in text:
            intent = "yeu_cau_ho_tro"
            intent_confidence = 0.6
        else:
            intent = "unknown"
            intent_confidence = 0.5
        print("[NLP Service] Su dung fallback Intent.")

    # --- 4. Nhận diện Sentiment ---
    if sentiment_classifier:
        sentiment_result = sentiment_classifier(text)[0]
        sentiment = sentiment_result['label'].lower()
    else:
        sentiment = "neutral"
        print("[NLP Service] Su dung fallback Sentiment.")
    
    # --- 5. Nhận diện Entity (Slot) ---
    from app.services.entity_extractor import extract_entities
    
    try:
        entities = extract_entities(text)
        # Flatten entities cho dễ sử dụng
        formatted_entities = {}
        
        if entities.get('times'):
            formatted_entities['time'] = entities['times'][0]['formatted']
            formatted_entities['time_details'] = entities['times']
        
        if entities.get('dates'):
            formatted_entities['date'] = entities['dates'][0]['date']
            formatted_entities['date_details'] = entities['dates']
        
        if entities.get('phones'):
            formatted_entities['phone'] = entities['phones'][0]['value']
            formatted_entities['phone_details'] = entities['phones']
        
        if entities.get('emails'):
            formatted_entities['email'] = entities['emails'][0]['value']
            formatted_entities['email_details'] = entities['emails']
        
        entities = formatted_entities
    except Exception as e:
        print(f"[NLP Service] Lỗi khi trích xuất entities: {e}")
        entities = {}

    result = {
        "text": text,
        "intent": intent,
        "intent_confidence": intent_confidence,
        "sentiment": sentiment,
        "entities": entities
    }
    
    # Add raw prediction info if available
    if raw_intent:
        result["raw_intent"] = raw_intent
        result["raw_confidence"] = raw_confidence
        result["threshold_applied"] = CONFIDENCE_THRESHOLDS.get(raw_intent, 0.65)
    
    print(f"[NLP Service] Ket qua: {result}")
    
    # Nếu caller truyền call_id thì lưu log user
    if call_id:
        save_conversation_log(
            call_id=call_id,
            speaker='user',
            text=text,
            intent=intent,
            confidence=intent_confidence
        )
    
    return result


async def process_nlp_tasks_async(text: str, call_id: Optional[str] = None) -> Dict[str, Any]:
    """Async wrapper around the sync `process_nlp_tasks` to avoid blocking the event loop.

    This runs the synchronous inference in a threadpool executor.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, process_nlp_tasks, text, call_id)