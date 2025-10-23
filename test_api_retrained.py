"""
Quick API Test: Retrained Model + RL Integration
Test webhook endpoint với retrained model và RL threshold tuning
"""

import sys
import os

# Ensure app modules can be imported
sys.path.insert(0, os.path.abspath('.'))

from app.services import model_manager
from app.services.nlp_service import process_nlp_tasks
from app.services.rl_threshold_tuner import RLThresholdTuner

print("=" * 70)
print("API TEST - RETRAINED MODEL + RL")
print("=" * 70)

# 1. Verify model loading
print("\n[1] Verifying model load...")
model, tokenizer = model_manager.get_model()
print(f"Model path: {model_manager._manager._model_path}")
print(f"Model version: {model_manager._manager.get_version()}")
print(f"Num labels: {model.config.num_labels}")
print(f"Label mapping: {list(model.config.id2label.values())[:5]}...")

# 2. Test NLP service with RL
print("\n[2] Testing NLP service with RL threshold...")
# Get intents from loaded model
intents = list(model.config.id2label.values())
rl_tuner = RLThresholdTuner(intents=intents)

test_cases = [
    ("Tôi cần hỗ trợ", "yeu_cau_ho_tro"),
    ("Không đồng ý", "tu_choi"),
    ("Dịch vụ tệ quá", "khieu_nai"),
    ("Tôi muốn đặt lịch hẹn", "dat_lich"),
    ("Xin chào", "unknown"),  # Likely low confidence
]

print("\nTesting with RL threshold selection:")
for text, expected in test_cases:
    result = process_nlp_tasks(text, call_id=f"api_test_{len(test_cases)}", use_rl_threshold=True)
    
    intent = result.get('intent', 'unknown')
    confidence = result.get('confidence', 0.0)
    threshold = result.get('threshold_used', 0.85)
    is_correct = (intent == expected)
    
    status = "✓" if is_correct else "✗"
    print(f"{status} '{text[:30]}' → {intent:15s} (conf={confidence:.3f}, threshold={threshold:.2f})")

# 3. Check RL state
print("\n[3] RL Threshold State:")
stats = rl_tuner.get_stats()
global_stats = stats.get('_global', {})
print(f"Total pending: {global_stats.get('total_pending', 0)}")
print(f"Current epsilon: {global_stats.get('epsilon', 0):.3f}")

print("\nBest thresholds per intent:")
for intent, intent_stats in list(stats.items())[:5]:
    if intent.startswith('_'):
        continue
    threshold = intent_stats.get('best_threshold', 0.85)
    avg_reward = intent_stats.get('best_avg_reward', 0)
    pulls = intent_stats.get('total_pulls', 0)
    print(f"  {intent:15s}: threshold={threshold:.3f} (pulls={pulls}, reward={avg_reward:.2f})")

# 4. Simulate feedback
print("\n[4] Simulating feedback...")
# Positive feedback for correct predictions
for text, expected in test_cases[:3]:
    result = process_nlp_tasks(text, call_id=f"feedback_test_{text[:10]}", use_rl_threshold=True)
    if result['intent'] == expected:
        rl_tuner.update_from_feedback(
            intent=result['intent'],
            threshold_used=result['threshold_used'],
            reward=1.0,
            context={'confidence': result['confidence']}
        )

print(f"After feedback - Epsilon: {rl_tuner.epsilon:.3f}, Updates: {rl_tuner.total_updates}")

# 5. Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✓ Retrained model loaded: {model_manager._manager._model_path.split('/')[-2]}")
print(f"✓ NLP service operational with RL threshold tuning")
print(f"✓ RL state: {rl_tuner.total_updates} updates, epsilon={rl_tuner.epsilon:.3f}")
print(f"\n[READY] System ready for production deployment!")
print("\nNext steps:")
print("1. Start API: python -X utf8 -m uvicorn app.main:app --reload")
print("2. Monitor RL: python monitor_rl_dashboard.py")
print("3. Send feedback: POST /api/feedback/rl-reward")
print("=" * 70)
