"""
Test NLP với RL - Fresh model reload
"""
import sys
import os

# Restart Python interpreter để clear singleton cache
if __name__ == "__main__":
    from app.services.nlp_service import process_nlp_tasks
    from app.services.rl_threshold_tuner import get_tuner
    from app.services import model_manager
    
    print("=" * 60)
    print("Test NLP với RL - Model V3 (11 intents)")
    print("=" * 60)
    
    # Load model v3
    model, tokenizer = model_manager.get_model()
    print(f"\n✓ Model loaded from: {model_manager._manager._model_path}")
    
    # Khởi tạo RL tuner
    tuner = get_tuner()
    print(f"✓ RL tuner initialized: {len(tuner.states)} intents, epsilon={tuner.epsilon:.3f}\n")
    
    # Test cases với expected intents
    test_cases = [
        ("Tôi muốn đặt lịch khám bệnh vào thứ 2 tuần sau", "dat_lich"),
        ("Mấy giờ phòng khám các bạn làm việc?", "hoi_gio_lam_viec"),
        ("Địa chỉ phòng khám của các bạn ở đâu?", "hoi_dia_chi"),
        ("OK tôi đồng ý đặt lịch", "xac_nhan"),
        ("Không, tôi không muốn đặt", "tu_choi"),
        ("Cảm ơn bạn đã hỗ trợ", "cam_on"),
        ("Tạm biệt", "tam_biet"),
        ("Tôi cần hỗ trợ về dịch vụ", "yeu_cau_ho_tro"),
        ("Tôi muốn khiếu nại về dịch vụ", "khieu_nai"),
        ("Cho tôi thông tin về gói khám sức khỏe", "hoi_thong_tin"),
    ]
    
    results = []
    for i, (text, expected_intent) in enumerate(test_cases, 1):
        # Call NLP với RL enabled
        call_id = f"test_fresh_{i}"
        result = process_nlp_tasks(text, call_id=call_id, use_rl_threshold=True)
        
        predicted_intent = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0.0)
        is_correct = (predicted_intent == expected_intent)
        
        print(f"\n[Test {i}] Text: '{text}'")
        print(f"  Expected: {expected_intent}")
        print(f"  Predicted: {predicted_intent} (conf={confidence:.3f}) {'✓' if is_correct else '✗'}")
        
        # Auto feedback: +1 nếu đúng, -1 nếu sai
        reward = 1.0 if is_correct else -1.0
        tuner.update_from_feedback(
            call_id=call_id,
            reward=reward,
            final_intent=expected_intent
        )
        print(f"  Feedback sent: reward={reward:+.1f}")
        
        results.append({
            'text': text,
            'expected': expected_intent,
            'predicted': predicted_intent,
            'confidence': confidence,
            'correct': is_correct
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    correct_count = sum(1 for r in results if r['correct'])
    accuracy = correct_count / len(results) * 100
    print(f"Accuracy: {correct_count}/{len(results)} = {accuracy:.1f}%")
    
    # RL stats
    print(f"\nRL Tuner Final State:")
    print(f"  Epsilon: {tuner.epsilon:.3f}")
    best_thresholds = tuner.get_best_thresholds()
    print(f"  Best thresholds:")
    for intent, threshold in sorted(best_thresholds.items()):
        state = tuner.states.get(intent)
        if state:
            best_arm = max(state.arms, key=lambda a: a.total_reward / max(a.pulls, 1))
            print(f"    {intent}: {threshold:.3f} (pulls={best_arm.pulls}, avg_reward={best_arm.total_reward/max(best_arm.pulls,1):.2f})")
    
    # Confidence distribution
    confidences = [r['confidence'] for r in results]
    avg_conf = sum(confidences) / len(confidences)
    print(f"\nConfidence Distribution:")
    print(f"  Average: {avg_conf:.3f}")
    print(f"  Min: {min(confidences):.3f}")
    print(f"  Max: {max(confidences):.3f}")
    
    print("\n✓ Test completed!")
