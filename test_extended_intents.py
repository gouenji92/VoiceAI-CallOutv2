"""
Test script for validating extended 11-intent classification system
Tests all 6 new intents (xac_nhan, tu_choi, hoi_gio_lam_viec, hoi_dia_chi, khieu_nai, yeu_cau_ho_tro)
plus original 5 intents to ensure model works correctly
"""
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import sys
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import json

# Model paths
MODEL_PATH = "models/phobert-intent-v3/final"
CONFIG_PATH = os.path.join(MODEL_PATH, "training_config.json")

# Test cases for all 11 intents
TEST_CASES = {
    # Original 5 intents
    "dat_lich": [
        "Tôi muốn đặt lịch khám",
        "Đặt hẹn cho tôi",
        "Làm sao để đặt lịch?",
        "Tôi cần book một cuộc hẹn"
    ],
    "hoi_thong_tin": [
        "Cho tôi biết thông tin về dịch vụ",
        "Chi phí là bao nhiêu?",
        "Dịch vụ của các bạn có gì?",
        "Tôi muốn hỏi về giá cả"
    ],
    "cam_on": [
        "Cảm ơn bạn",
        "Thanks",
        "Cảm ơn nhiều nhé",
        "Tôi cảm ơn"
    ],
    "tam_biet": [
        "Tạm biệt",
        "Bye bye",
        "Hẹn gặp lại",
        "Chào tạm biệt nhé"
    ],
    "unknown": [
        "xyz abc 123",
        "blah blah",
        "asdfghjkl",
        "random text here"
    ],
    
    # 6 new intents
    "xac_nhan": [
        "Đúng rồi",
        "OK",
        "Được",
        "Tôi đồng ý",
        "Vâng ạ",
        "Chính xác",
        "Đồng ý luôn"
    ],
    "tu_choi": [
        "Không",
        "Không phải",
        "Tôi từ chối",
        "Thôi",
        "Không được",
        "Tôi không muốn",
        "Decline"
    ],
    "hoi_gio_lam_viec": [
        "Giờ làm việc của các bạn thế nào?",
        "Mấy giờ mở cửa?",
        "Lịch làm việc ra sao?",
        "Các bạn làm việc từ mấy giờ?",
        "Thứ 7 có mở cửa không?",
        "Working hours là gì?"
    ],
    "hoi_dia_chi": [
        "Địa chỉ của các bạn",
        "Các bạn ở đâu?",
        "Làm sao tìm địa chỉ?",
        "Chỉ đường cho tôi",
        "Ở phố nào?",
        "Address là gì?"
    ],
    "khieu_nai": [
        "Tôi không hài lòng",
        "Tôi muốn khiếu nại",
        "Dịch vụ tệ quá",
        "Rất thất vọng",
        "Tôi phàn nàn",
        "Không chuyên nghiệp chút nào"
    ],
    "yeu_cau_ho_tro": [
        "Tôi cần hỗ trợ",
        "Giúp tôi với",
        "Hỗ trợ khẩn cấp",
        "Tôi cần trợ giúp",
        "Xin giúp đỡ",
        "Help me please"
    ]
}

def load_model_and_tokenizer():
    """Load trained model and tokenizer"""
    print(f"Loading model from: {MODEL_PATH}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.eval()
    
    # Load training config to get label mapping
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    label2id = config['label2id']
    id2label = {int(v): k for k, v in label2id.items()}
    confidence_thresholds = config.get('confidence_thresholds', {})
    
    print(f"Loaded model with {len(id2label)} intents: {list(id2label.values())}")
    print(f"Confidence thresholds: {confidence_thresholds}")
    
    return model, tokenizer, id2label, confidence_thresholds

def predict_intent(text, model, tokenizer, id2label, confidence_thresholds):
    """Predict intent for a single text"""
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        predicted_idx = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][predicted_idx].item()
    
    predicted_intent = id2label[predicted_idx]
    # Mirror service logic: cap thresholds to avoid being overly strict
    threshold = min(confidence_thresholds.get(predicted_intent, 0.85), 0.90)
    
    # Apply threshold
    final_intent = predicted_intent if confidence >= threshold else "unknown"
    
    return final_intent, confidence, predicted_intent, threshold

def test_all_intents():
    """Test all 11 intents with sample inputs"""
    print("\n" + "="*80)
    print("TESTING EXTENDED 11-INTENT CLASSIFICATION SYSTEM")
    print("="*80 + "\n")
    
    # Load model
    model, tokenizer, id2label, confidence_thresholds = load_model_and_tokenizer()
    
    # Statistics
    total_tests = 0
    correct_predictions = 0
    results_by_intent = {}
    
    # Test each intent
    for expected_intent, test_texts in TEST_CASES.items():
        print(f"\n{'='*80}")
        print(f"Testing Intent: {expected_intent.upper()}")
        print(f"{'='*80}")
        
        intent_correct = 0
        intent_total = len(test_texts)
        
        for i, text in enumerate(test_texts, 1):
            final_intent, confidence, raw_intent, threshold = predict_intent(
                text, model, tokenizer, id2label, confidence_thresholds
            )
            
            is_correct = (final_intent == expected_intent)
            status = "✓" if is_correct else "✗"
            
            print(f"\n  Test {i}/{intent_total}: {text}")
            print(f"    Raw Prediction: {raw_intent} (confidence: {confidence:.4f})")
            print(f"    Threshold: {threshold:.4f}")
            print(f"    Final Intent: {final_intent}")
            print(f"    Expected: {expected_intent}")
            print(f"    Result: {status}")
            
            if is_correct:
                intent_correct += 1
                correct_predictions += 1
            
            total_tests += 1
        
        accuracy = (intent_correct / intent_total * 100) if intent_total > 0 else 0
        results_by_intent[expected_intent] = {
            'correct': intent_correct,
            'total': intent_total,
            'accuracy': accuracy
        }
        
        print(f"\n  Intent Summary: {intent_correct}/{intent_total} correct ({accuracy:.1f}%)")
    
    # Overall summary
    print(f"\n\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    
    overall_accuracy = (correct_predictions / total_tests * 100) if total_tests > 0 else 0
    print(f"\nTotal Tests: {total_tests}")
    print(f"Correct Predictions: {correct_predictions}")
    print(f"Overall Accuracy: {overall_accuracy:.2f}%")
    
    print(f"\n{'='*80}")
    print("ACCURACY BY INTENT")
    print(f"{'='*80}")
    
    # Sort by intent name for readability
    for intent in sorted(results_by_intent.keys()):
        stats = results_by_intent[intent]
        print(f"  {intent:20s}: {stats['correct']:2d}/{stats['total']:2d} ({stats['accuracy']:5.1f}%)")
    
    # Identify problematic intents
    print(f"\n{'='*80}")
    print("ANALYSIS")
    print(f"{'='*80}")
    
    low_accuracy_intents = [intent for intent, stats in results_by_intent.items() 
                            if stats['accuracy'] < 80]
    
    if low_accuracy_intents:
        print("\n⚠ Intents with accuracy < 80%:")
        for intent in low_accuracy_intents:
            stats = results_by_intent[intent]
            print(f"  - {intent}: {stats['accuracy']:.1f}%")
    else:
        print("\n✓ All intents achieve ≥80% accuracy")
    
    # Check new intents specifically
    new_intents = ['xac_nhan', 'tu_choi', 'hoi_gio_lam_viec', 'hoi_dia_chi', 'khieu_nai', 'yeu_cau_ho_tro']
    print(f"\n{'='*80}")
    print("NEW INTENTS PERFORMANCE")
    print(f"{'='*80}")
    
    for intent in new_intents:
        if intent in results_by_intent:
            stats = results_by_intent[intent]
            status = "✓" if stats['accuracy'] >= 80 else "✗"
            print(f"  {status} {intent:20s}: {stats['accuracy']:5.1f}%")
    
    print(f"\n{'='*80}\n")
    
    return overall_accuracy >= 80

if __name__ == "__main__":
    try:
        success = test_all_intents()
        if success:
            print("✓ Testing completed successfully - All intents validated")
            sys.exit(0)
        else:
            print("✗ Testing completed with warnings - Some intents below 80% accuracy")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Testing failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
