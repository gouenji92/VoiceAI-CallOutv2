"""
Quick Test: Retrained Model with Weak Intents
Test specifically for yeu_cau_ho_tro, tu_choi, khieu_nai
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import glob
import os

print("=" * 70)
print("TEST RETRAINED MODEL - WEAK INTENTS FOCUS")
print("=" * 70)

# Load retrained model (pick newest retrain dir; fallback to augmented)
print("\n[1] Loading retrained model...")
model_path = None

# Find latest retrained model
retrain_dirs = sorted(
    glob.glob(os.path.join('models', 'phobert-intent-v3-retrain-*', 'final')),
    key=os.path.getmtime,
    reverse=True
)
if retrain_dirs:
    model_path = retrain_dirs[0]
else:
    # Fallback to augmented path if exists
    fallback_aug = os.path.join('models', 'phobert-intent-v3-augmented', 'final')
    if os.path.exists(fallback_aug):
        model_path = fallback_aug
    else:
        model_path = 'models/phobert-intent-v3/final'

print(f"Model path: {model_path}")

# Direct load (faster than service wrapper)
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
model.eval()
print(f"OK - Device: {device}")

# Test cases focused on weak intents
test_cases = [
    # yeu_cau_ho_tro (expected confidence >0.90)
    ("Tôi cần hỗ trợ", "yeu_cau_ho_tro"),
    ("Giúp tôi với", "yeu_cau_ho_tro"),
    ("Tôi cần sự hỗ trợ về vấn đề này", "yeu_cau_ho_tro"),
    ("Support tôi được không", "yeu_cau_ho_tro"),
    ("Có ai giúp tôi không", "yeu_cau_ho_tro"),
    
    # tu_choi (expected confidence >0.90)
    ("Không", "tu_choi"),
    ("Tôi từ chối", "tu_choi"),
    ("Không đồng ý", "tu_choi"),
    ("Thôi không cần", "tu_choi"),
    ("Tôi không muốn", "tu_choi"),
    
    # khieu_nai (expected confidence >0.90)
    ("Tôi muốn khiếu nại", "khieu_nai"),
    ("Dịch vụ tệ quá", "khieu_nai"),
    ("Tôi không hài lòng", "khieu_nai"),
    ("Quá tệ", "khieu_nai"),
    ("Tôi muốn phàn nàn", "khieu_nai"),
]

print(f"\n[2] Testing {len(test_cases)} samples...\n")

results = []
for text, expected in test_cases:
    # Direct inference (faster than NLP service)
    inputs = tokenizer(text, truncation=True, padding=True, max_length=128, return_tensors='pt')
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        confidence, predicted_id = torch.max(probs, dim=-1)
    
    predicted = model.config.id2label[predicted_id.item()]
    confidence = confidence.item()
    is_correct = (predicted == expected)
    
    status = "OK" if is_correct else "FAIL"
    conf_status = "HIGH" if confidence >= 0.90 else "LOW" if confidence >= 0.80 else "VERY_LOW"
    
    print(f"[{status}] {text[:30]:30s} | pred={predicted:15s} | conf={confidence:.3f} ({conf_status})")
    
    results.append({
        'text': text,
        'expected': expected,
        'predicted': predicted,
        'confidence': confidence,
        'correct': is_correct
    })

# Summary by intent
print("\n" + "=" * 70)
print("SUMMARY BY INTENT")
print("=" * 70)

for intent in ['yeu_cau_ho_tro', 'tu_choi', 'khieu_nai']:
    intent_results = [r for r in results if r['expected'] == intent]
    correct = sum(1 for r in intent_results if r['correct'])
    total = len(intent_results)
    avg_conf = sum(r['confidence'] for r in intent_results) / total
    
    accuracy = correct / total * 100
    status = "GOOD" if accuracy >= 80 and avg_conf >= 0.90 else "POOR"
    
    print(f"\n{intent}:")
    print(f"  Accuracy: {correct}/{total} = {accuracy:.1f}%")
    print(f"  Avg confidence: {avg_conf:.3f}")
    print(f"  Status: {status}")

# Overall
overall_correct = sum(1 for r in results if r['correct'])
overall_accuracy = overall_correct / len(results) * 100
overall_avg_conf = sum(r['confidence'] for r in results) / len(results)

print("\n" + "=" * 70)
print("OVERALL RESULTS")
print("=" * 70)
print(f"Total accuracy: {overall_correct}/{len(results)} = {overall_accuracy:.1f}%")
print(f"Average confidence: {overall_avg_conf:.3f}")

if overall_accuracy >= 85 and overall_avg_conf >= 0.90:
    print("\n[SUCCESS] Retrained model performs well on weak intents!")
    print("Next: Deploy with RL tuner for production")
elif overall_accuracy >= 70:
    print("\n[PARTIAL] Model improved but needs more data or tuning")
    print("Recommendation: Collect more edge cases, continue RL learning")
else:
    print("\n[WARNING] Model still struggles with weak intents")
    print("Recommendation: Add more diverse training samples")

print("\n" + "=" * 70)
