"""
End-to-end test for RL threshold tuning system.

Tests:
1. Tuner initialization and state persistence
2. Threshold selection (exploration vs exploitation)
3. Reward feedback and arm updates
4. Epsilon decay
5. Best threshold convergence
"""

import sys
import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from pathlib import Path
import json
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rl_threshold_tuner import RLThresholdTuner

def test_initialization():
    """Test tuner initialization"""
    print("\n" + "="*80)
    print("TEST 1: Initialization")
    print("="*80)
    
    intents = ['test_intent_1', 'test_intent_2']
    tuner = RLThresholdTuner(
        intents=intents,
        min_threshold=0.80,
        max_threshold=0.95,
        num_arms=5,
        epsilon=0.3,
        state_file="models/test_rl_state.json"
    )
    
    assert len(tuner.states) == 2, "Should have 2 intent states"
    assert len(tuner.states['test_intent_1'].arms) == 5, "Should have 5 arms per intent"
    
    # Check threshold values
    expected_thresholds = [0.80, 0.8375, 0.875, 0.9125, 0.95]
    actual_thresholds = [arm.value for arm in tuner.states['test_intent_1'].arms]
    
    for exp, act in zip(expected_thresholds, actual_thresholds):
        assert abs(exp - act) < 0.001, f"Threshold mismatch: {exp} vs {act}"
    
    print("✓ Initialization successful")
    print(f"  Intents: {intents}")
    print(f"  Arms per intent: 5")
    print(f"  Threshold range: [0.80, 0.95]")
    print(f"  Initial epsilon: {tuner.epsilon:.3f}")
    
    return tuner

def test_threshold_selection(tuner: RLThresholdTuner):
    """Test threshold selection with epsilon-greedy"""
    print("\n" + "="*80)
    print("TEST 2: Threshold Selection")
    print("="*80)
    
    intent = 'test_intent_1'
    selections = []
    
    # Run multiple selections
    for i in range(20):
        threshold = tuner.get_threshold(
            intent=intent,
            raw_confidence=0.92,
            context={'text_length': 50},
            call_id=f"test_call_{i}"
        )
        selections.append(threshold)
    
    unique_selections = set(selections)
    
    print(f"✓ Selected {len(unique_selections)} unique thresholds in 20 trials")
    print(f"  Selections: {sorted(unique_selections)}")
    print(f"  Exploration count: {tuner.states[intent].exploration_count}")
    print(f"  Exploitation count: {tuner.states[intent].exploitation_count}")
    
    assert len(unique_selections) >= 2, "Should explore multiple arms"

def test_reward_feedback(tuner: RLThresholdTuner):
    """Test reward feedback and arm updates"""
    print("\n" + "="*80)
    print("TEST 3: Reward Feedback")
    print("="*80)
    
    intent = 'test_intent_1'
    
    # Simulate feedback loop: reward higher thresholds more
    for i in range(50):
        call_id = f"feedback_call_{i}"
        threshold = tuner.get_threshold(
            intent=intent,
            raw_confidence=0.90,
            context={},
            call_id=call_id
        )
        
        # Reward scheme: higher thresholds get better rewards
        if threshold >= 0.90:
            reward = 1.0
        elif threshold >= 0.85:
            reward = 0.5
        else:
            reward = -0.5
        
        tuner.update_from_feedback(call_id, reward)
    
    # Check arm statistics
    state = tuner.states[intent]
    arms = state.arms
    
    print("\nArm Statistics:")
    print(f"{'Threshold':<12} {'Pulls':<8} {'Total Reward':<15} {'Avg Reward':<12}")
    print("-" * 50)
    
    for arm in arms:
        if arm.pulls > 0:
            print(f"{arm.value:<12.3f} {arm.pulls:<8} {arm.total_reward:<15.2f} {arm.average_reward:<12.3f}")
    
    # Verify higher thresholds have better rewards
    high_threshold_arms = [arm for arm in arms if arm.value >= 0.90 and arm.pulls > 0]
    low_threshold_arms = [arm for arm in arms if arm.value < 0.85 and arm.pulls > 0]
    
    if high_threshold_arms and low_threshold_arms:
        high_avg = np.mean([arm.average_reward for arm in high_threshold_arms])
        low_avg = np.mean([arm.average_reward for arm in low_threshold_arms])
        
        print(f"\n✓ High threshold arms (≥0.90): avg reward = {high_avg:.3f}")
        print(f"✓ Low threshold arms (<0.85): avg reward = {low_avg:.3f}")
        
        assert high_avg > low_avg, "Higher thresholds should have better average reward"

def test_epsilon_decay(tuner: RLThresholdTuner):
    """Test epsilon decay over updates"""
    print("\n" + "="*80)
    print("TEST 4: Epsilon Decay")
    print("="*80)
    
    initial_epsilon = tuner.epsilon
    
    # Run many feedback cycles
    for i in range(100):
        call_id = f"decay_call_{i}"
        threshold = tuner.get_threshold(
            intent='test_intent_2',
            raw_confidence=0.88,
            context={},
            call_id=call_id
        )
        tuner.update_from_feedback(call_id, reward=1.0)
    
    final_epsilon = tuner.epsilon
    
    print(f"✓ Epsilon decayed from {initial_epsilon:.4f} to {final_epsilon:.4f}")
    print(f"  Decay rate: {tuner.epsilon_decay}")
    print(f"  Min epsilon: {tuner.min_epsilon}")
    
    assert final_epsilon < initial_epsilon, "Epsilon should decay"
    assert final_epsilon >= tuner.min_epsilon, "Epsilon should not go below minimum"

def test_best_threshold_convergence(tuner: RLThresholdTuner):
    """Test convergence to best threshold"""
    print("\n" + "="*80)
    print("TEST 5: Best Threshold Convergence")
    print("="*80)
    
    best_thresholds = tuner.get_best_thresholds()
    
    print("\nBest Thresholds per Intent:")
    for intent, threshold in best_thresholds.items():
        state = tuner.states[intent]
        total_pulls = sum(arm.pulls for arm in state.arms)
        
        print(f"  {intent}: {threshold:.3f} (total pulls: {total_pulls})")
    
    print("\n✓ Best thresholds computed successfully")

def test_state_persistence(tuner: RLThresholdTuner):
    """Test state save/load"""
    print("\n" + "="*80)
    print("TEST 6: State Persistence")
    print("="*80)
    
    # Save state
    tuner.save_state()
    print(f"✓ State saved to {tuner.state_file}")
    
    # Load state into new tuner
    new_tuner = RLThresholdTuner(
        intents=['test_intent_1', 'test_intent_2'],
        state_file=str(tuner.state_file)
    )
    
    # Verify state loaded correctly
    original_state = tuner.states['test_intent_1']
    loaded_state = new_tuner.states['test_intent_1']
    
    assert len(original_state.arms) == len(loaded_state.arms), "Arm count should match"
    
    for orig_arm, load_arm in zip(original_state.arms, loaded_state.arms):
        assert abs(orig_arm.value - load_arm.value) < 0.001, "Threshold values should match"
        assert orig_arm.pulls == load_arm.pulls, "Pull counts should match"
        assert abs(orig_arm.total_reward - load_arm.total_reward) < 0.001, "Total rewards should match"
    
    print("✓ State loaded correctly")
    print(f"  Epsilon preserved: {new_tuner.epsilon:.4f}")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("RL THRESHOLD TUNER - END-TO-END TEST SUITE")
    print("="*80)
    
    try:
        # Run tests
        tuner = test_initialization()
        test_threshold_selection(tuner)
        test_reward_feedback(tuner)
        test_epsilon_decay(tuner)
        test_best_threshold_convergence(tuner)
        test_state_persistence(tuner)
        
        # Cleanup
        if tuner.state_file.exists():
            tuner.state_file.unlink()
            print(f"\n✓ Cleaned up test state file: {tuner.state_file}")
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80)
        
        return True
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
