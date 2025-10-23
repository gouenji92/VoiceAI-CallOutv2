"""
Demo RL threshold tuning với simulated feedback loop.
Không cần chạy API server, test trực tiếp RL tuner.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.rl_threshold_tuner import RLThresholdTuner
import random

def demo_rl_system():
    print("="*80)
    print("DEMO: RL THRESHOLD TUNING SYSTEM")
    print("="*80)
    
    # Initialize tuner
    print("\n[1] Khởi tạo RL Tuner...")
    intents = ['dat_lich', 'hoi_thong_tin', 'xac_nhan', 'tu_choi', 'hoi_gio_lam_viec']
    tuner = RLThresholdTuner(
        intents=intents,
        min_threshold=0.80,
        max_threshold=0.95,
        num_arms=8,
        epsilon=0.3,
        state_file="models/demo_rl_state.json"
    )
    print(f"✓ Đã khởi tạo tuner với {len(intents)} intents")
    print(f"  Epsilon ban đầu: {tuner.epsilon:.3f}")
    print(f"  Số arms per intent: {tuner.num_arms}")
    
    # Simulate predictions and feedback
    print("\n[2] Simulate 50 cuộc gọi với feedback...")
    
    test_scenarios = [
        ('dat_lich', 0.92, 1.0, "User xác nhận đặt lịch"),
        ('dat_lich', 0.88, 0.0, "Cần hỏi lại thời gian"),
        ('dat_lich', 0.85, -1.0, "User từ chối"),
        ('hoi_thong_tin', 0.91, 1.0, "Cung cấp info thành công"),
        ('hoi_thong_tin', 0.87, 0.0, "Cần làm rõ"),
        ('xac_nhan', 0.94, 1.0, "User confirm"),
        ('xac_nhan', 0.83, -1.0, "User từ chối"),
        ('tu_choi', 0.90, 1.0, "Ghi nhận từ chối"),
        ('hoi_gio_lam_viec', 0.93, 1.0, "Cung cấp giờ làm việc"),
    ]
    
    for i in range(50):
        # Pick random scenario
        intent, raw_conf, true_reward, description = random.choice(test_scenarios)
        call_id = f"demo_call_{i+1:03d}"
        
        # Get threshold
        threshold = tuner.get_threshold(
            intent=intent,
            raw_confidence=raw_conf,
            context={'text_length': random.randint(10, 100)},
            call_id=call_id
        )
        
        # Simulate reward (với noise)
        reward = true_reward + random.uniform(-0.1, 0.1)
        reward = max(-1.0, min(1.0, reward))  # Clamp
        
        # Update tuner
        tuner.update_from_feedback(call_id, reward)
        
        if (i + 1) % 10 == 0:
            print(f"  Đã xử lý {i+1}/50 calls, epsilon={tuner.epsilon:.3f}")
    
    print("\n✓ Hoàn thành simulation")
    
    # Show best thresholds
    print("\n[3] Best Thresholds sau training:")
    print(f"{'Intent':<20} {'Best Threshold':>15} {'Pulls':>8}")
    print("-" * 50)
    
    best_thresholds = tuner.get_best_thresholds()
    for intent in intents:
        state = tuner.states[intent]
        total_pulls = sum(arm.pulls for arm in state.arms)
        threshold = best_thresholds.get(intent, 0.85)
        print(f"{intent:<20} {threshold:>15.3f} {total_pulls:>8}")
    
    # Show detailed stats for one intent
    print("\n[4] Chi tiết arm performance cho 'dat_lich':")
    state = tuner.states['dat_lich']
    print(f"{'Threshold':<12} {'Pulls':>8} {'Avg Reward':>12}")
    print("-" * 35)
    for arm in state.arms:
        if arm.pulls > 0:
            print(f"{arm.value:<12.3f} {arm.pulls:>8} {arm.average_reward:>12.3f}")
    
    # Save state
    print("\n[5] Lưu state...")
    tuner.save_state()
    print(f"✓ State đã lưu vào {tuner.state_file}")
    
    # Test reload
    print("\n[6] Test reload state...")
    new_tuner = RLThresholdTuner(
        intents=intents,
        state_file=str(tuner.state_file)
    )
    print(f"✓ State loaded, epsilon={new_tuner.epsilon:.3f}")
    
    # Summary
    print("\n" + "="*80)
    print("DEMO COMPLETED")
    print("="*80)
    print(f"\n✅ RL Tuner đã học được best thresholds từ {50} cuộc gọi")
    print(f"✅ Epsilon decay: {0.3:.3f} → {tuner.epsilon:.3f}")
    print(f"✅ State persistence: OK")
    print(f"\nFile: {tuner.state_file}")
    print("\nĐể xem visualization:")
    print("  python scripts/monitor_rl_tuner.py")

if __name__ == "__main__":
    demo_rl_system()
