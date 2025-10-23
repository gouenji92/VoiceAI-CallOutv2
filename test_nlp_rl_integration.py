"""
Test RL integration với NLP service thực tế.
"""

import sys
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services import nlp_service

def test_nlp_with_rl():
    print("="*80)
    print("TEST: NLP SERVICE với RL THRESHOLD TUNING")
    print("="*80)
    
    # Test cases
    test_cases = [
        ("Tôi muốn đặt lịch khám", "dat_lich"),
        ("Mấy giờ các bạn làm việc?", "hoi_gio_lam_viec"),
        ("Địa chỉ của các bạn", "hoi_dia_chi"),
        ("OK đồng ý", "xac_nhan"),
        ("Không cảm ơn", "tu_choi"),
        ("Cảm ơn bạn", "cam_on"),
        ("Tạm biệt", "tam_biet"),
    ]
    
    print("\n[1] Test với RL enabled (use_rl_threshold=True):\n")
    
    for i, (text, expected) in enumerate(test_cases, 1):
        call_id = f"test_rl_{i:03d}"
        
        result = nlp_service.process_nlp_tasks(
            text=text,
            call_id=call_id,
            use_rl_threshold=True
        )
        
        intent = result['intent']
        confidence = result['intent_confidence']
        match = "✓" if intent == expected else "✗"
        
        print(f"{match} Test {i}: '{text}'")
        print(f"   Expected: {expected}, Got: {intent} (conf: {confidence:.3f})")
        
        # Auto feedback cho demo
        reward = 1.0 if intent == expected else -1.0
        
        try:
            from app.services.rl_threshold_tuner import get_tuner
            tuner = get_tuner()
            tuner.update_from_feedback(call_id, reward)
        except Exception as e:
            print(f"   Warning: Could not send feedback: {e}")
    
    print("\n" + "="*80)
    print("TEST COMPLETED")
    print("="*80)
    
    # Show stats
    try:
        from app.services.rl_threshold_tuner import get_tuner
        tuner = get_tuner()
        best = tuner.get_best_thresholds()
        
        print("\nCurrent best thresholds:")
        for intent in ['dat_lich', 'hoi_gio_lam_viec', 'hoi_dia_chi', 'xac_nhan', 'tu_choi']:
            if intent in best:
                print(f"  {intent}: {best[intent]:.3f}")
        
        print(f"\nEpsilon: {tuner.epsilon:.3f}")
        
    except Exception as e:
        print(f"Could not get stats: {e}")

if __name__ == "__main__":
    test_nlp_with_rl()
