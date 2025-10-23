"""
Quick Test Script for Phase 1 Model
Test newly trained model on sample inputs
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import json

def test_model():
    """Test the newly trained model"""
    
    model_dir = "models/phobert-intent-v3/final"
    
    print("="*60)
    print("TESTING PHASE 1 INTENT MODEL")
    print("="*60)
    
    # Load model
    print("\nLoading model...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        classifier = pipeline("text-classification", model=model, tokenizer=tokenizer)
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return
    
    # Load config
    try:
        with open(f"{model_dir}/training_config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✓ Config loaded (Accuracy: {config['avg_accuracy']:.4f}, F1: {config['avg_f1']:.4f})")
    except Exception as e:
        print(f"⚠ Warning: Could not load config: {e}")
        config = {}
    
    # Test cases
    test_cases = [
        # dat_lich
        "Tôi muốn đặt lịch hẹn",
        "Cho tôi hẹn vào 9h sáng mai",
        "Book lịch giúp tôi",
        "Đăng ký lịch hẹn khám bệnh",
        
        # hoi_thong_tin
        "Sản phẩm này giá bao nhiêu?",
        "Cho tôi biết thêm chi tiết",
        "Tôi cần tư vấn về dịch vụ",
        "Quy trình đăng ký thế nào?",
        
        # cam_on
        "Cảm ơn bạn nhiều",
        "Tuyệt vời",
        "Rất hữu ích",
        
        # tam_biet
        "Tạm biệt",
        "Hẹn gặp lại",
        "Goodbye",
        
        # unknown
        "Tôi không hiểu",
        "Nói lại đi",
        "Hả?",
        
        # Edge cases
        "đặt lịch ạ",  # With polite word
        "ĐẶT LỊCH",  # All caps
        "Tôi muốn đặt lịch hẹn.",  # With punctuation
    ]
    
    print("\n" + "="*60)
    print("TEST PREDICTIONS")
    print("="*60)
    
    results = []
    for text in test_cases:
        result = classifier(text)[0]
        intent = result['label']
        confidence = result['score']
        
        # Get threshold if available
        threshold = "N/A"
        if config and 'confidence_thresholds' in config:
            threshold = f"{config['confidence_thresholds'].get(intent, 0.65):.3f}"
        
        # Determine if passes threshold
        status = "✓" if confidence >= 0.65 else "⚠"
        
        results.append({
            'text': text,
            'intent': intent,
            'confidence': confidence,
            'threshold': threshold,
            'status': status
        })
        
        print(f"\n{status} Text: {text}")
        print(f"  Intent: {intent}")
        print(f"  Confidence: {confidence:.3f} (threshold: {threshold})")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    # Count by intent
    intent_counts = {}
    for r in results:
        intent = r['intent']
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    
    print("\nPredictions by Intent:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")
    
    # Average confidence
    avg_conf = sum(r['confidence'] for r in results) / len(results)
    print(f"\nAverage Confidence: {avg_conf:.3f}")
    
    # High confidence rate
    high_conf = sum(1 for r in results if r['confidence'] >= 0.80) / len(results)
    print(f"High Confidence Rate (≥0.80): {high_conf:.1%}")
    
    print("\n" + "="*60)
    print("✓ TESTING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_model()
