"""
RL-based adaptive threshold tuner using contextual epsilon-greedy bandit.

Adjusts per-intent confidence thresholds dynamically based on user feedback:
- Reward +1: User confirms/proceeds (intent correct)
- Reward 0: Requires clarification (uncertain)
- Reward -1: User rejects/escalates (intent wrong or low quality)

Context features: intent, raw_confidence, text_length, sentiment
Actions: Threshold values in range [min_threshold, max_threshold]
"""

import json
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

@dataclass
class ThresholdArm:
    """Represents a threshold value (arm) for an intent"""
    value: float
    pulls: int = 0
    total_reward: float = 0.0
    
    @property
    def average_reward(self) -> float:
        return self.total_reward / self.pulls if self.pulls > 0 else 0.0

@dataclass
class ThresholdState:
    """State for one intent's threshold optimization"""
    intent: str
    arms: List[ThresholdArm]
    exploration_count: int = 0
    exploitation_count: int = 0
    last_updated: str = ""
    
    def to_dict(self) -> dict:
        return {
            'intent': self.intent,
            'arms': [asdict(arm) for arm in self.arms],
            'exploration_count': self.exploration_count,
            'exploitation_count': self.exploitation_count,
            'last_updated': self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ThresholdState':
        arms = [ThresholdArm(**arm_data) for arm_data in data['arms']]
        return cls(
            intent=data['intent'],
            arms=arms,
            exploration_count=data.get('exploration_count', 0),
            exploitation_count=data.get('exploitation_count', 0),
            last_updated=data.get('last_updated', '')
        )

class RLThresholdTuner:
    """
    Contextual epsilon-greedy bandit for adaptive intent threshold tuning.
    
    Each intent has discrete threshold options (arms) in [min, max] range.
    Epsilon-greedy: explore random arm with probability epsilon, else exploit best arm.
    """
    
    def __init__(
        self,
        intents: List[str],
        min_threshold: float = 0.80,
        max_threshold: float = 0.95,
        num_arms: int = 8,  # Discrete threshold options
        epsilon: float = 0.15,  # Exploration rate
        epsilon_decay: float = 0.995,  # Decay per update
        min_epsilon: float = 0.05,
        state_file: str = "models/rl_threshold_state.json"
    ):
        self.intents = intents
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.num_arms = num_arms
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.min_epsilon = min_epsilon
        self.state_file = Path(state_file)
        
        # Create discrete threshold arms
        self.threshold_values = np.linspace(min_threshold, max_threshold, num_arms).tolist()
        
        # State per intent
        self.states: Dict[str, ThresholdState] = {}
        
        # Pending experiences (not yet rewarded)
        self.pending_experiences: Dict[str, Tuple[str, float, dict]] = {}  # call_id -> (intent, threshold, context)
        
        # Load or initialize
        self._load_state()
        
        print(f"[RL Tuner] Initialized with {len(intents)} intents, {num_arms} arms per intent")
        print(f"[RL Tuner] Threshold range: [{min_threshold:.2f}, {max_threshold:.2f}]")
        print(f"[RL Tuner] Epsilon: {epsilon:.3f} (decay: {epsilon_decay}, min: {min_epsilon})")
    
    def _load_state(self):
        """Load saved state or initialize fresh"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.epsilon = data.get('epsilon', self.epsilon)
                
                for intent_data in data.get('states', []):
                    state = ThresholdState.from_dict(intent_data)
                    self.states[state.intent] = state
                
                print(f"[RL Tuner] Loaded state from {self.state_file}")
                print(f"[RL Tuner] Current epsilon: {self.epsilon:.3f}")
            except Exception as e:
                print(f"[RL Tuner] Failed to load state: {e}, initializing fresh")
                self._initialize_states()
        else:
            self._initialize_states()
    
    def _initialize_states(self):
        """Initialize fresh state for all intents"""
        for intent in self.intents:
            arms = [ThresholdArm(value=val) for val in self.threshold_values]
            self.states[intent] = ThresholdState(
                intent=intent,
                arms=arms,
                last_updated=datetime.now().isoformat()
            )
        print(f"[RL Tuner] Initialized fresh state for {len(self.intents)} intents")
    
    def save_state(self):
        """Persist current state to disk"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'epsilon': self.epsilon,
                'last_saved': datetime.now().isoformat(),
                'states': [state.to_dict() for state in self.states.values()]
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[RL Tuner] State saved to {self.state_file}")
        except Exception as e:
            print(f"[RL Tuner] Failed to save state: {e}")
    
    def get_threshold(
        self,
        intent: str,
        raw_confidence: float,
        context: Optional[dict] = None,
        call_id: Optional[str] = None
    ) -> float:
        """
        Select threshold for this intent using epsilon-greedy strategy.
        
        Args:
            intent: Predicted intent
            raw_confidence: Model's confidence score
            context: Additional context (text_length, sentiment, etc.)
            call_id: Unique call ID for tracking pending reward
        
        Returns:
            Selected threshold value
        """
        if intent not in self.states:
            # Fallback for unknown intent
            return 0.85
        
        state = self.states[intent]
        
        # Epsilon-greedy selection
        if np.random.random() < self.epsilon:
            # Explore: random arm
            arm_idx = np.random.randint(0, len(state.arms))
            state.exploration_count += 1
            strategy = "explore"
        else:
            # Exploit: best average reward
            arm_idx = self._select_best_arm(state)
            state.exploitation_count += 1
            strategy = "exploit"
        
        selected_threshold = state.arms[arm_idx].value
        
        # Store pending experience for later reward
        if call_id:
            self.pending_experiences[call_id] = (intent, selected_threshold, context or {})
        
        print(f"[RL Tuner] {intent}: threshold={selected_threshold:.3f} ({strategy}), "
              f"epsilon={self.epsilon:.3f}, raw_conf={raw_confidence:.3f}")
        
        return selected_threshold
    
    def _select_best_arm(self, state: ThresholdState) -> int:
        """Select arm with highest average reward (with UCB tie-breaking)"""
        if all(arm.pulls == 0 for arm in state.arms):
            # All arms untried, pick middle
            return len(state.arms) // 2
        
        # Use UCB1 for exploration bonus
        total_pulls = sum(arm.pulls for arm in state.arms) + 1
        
        best_idx = 0
        best_score = -float('inf')
        
        for idx, arm in enumerate(state.arms):
            if arm.pulls == 0:
                # Untried arm: give high exploration bonus
                score = float('inf')
            else:
                # UCB1: avg_reward + sqrt(2 * log(total) / pulls)
                exploration_bonus = np.sqrt(2 * np.log(total_pulls) / arm.pulls)
                score = arm.average_reward + 0.1 * exploration_bonus
            
            if score > best_score:
                best_score = score
                best_idx = idx
        
        return best_idx
    
    def update_from_feedback(
        self,
        call_id: str,
        reward: float,
        final_intent: Optional[str] = None
    ):
        """
        Update bandit with reward signal.
        
        Args:
            call_id: Call ID that generated the prediction
            reward: +1 (success), 0 (neutral/clarify), -1 (fail)
            final_intent: Actual intent if different from predicted
        """
        if call_id not in self.pending_experiences:
            print(f"[RL Tuner] No pending experience for call_id={call_id}")
            return
        
        intent, threshold, context = self.pending_experiences.pop(call_id)
        
        # Use final_intent if provided (user correction)
        if final_intent and final_intent != intent:
            print(f"[RL Tuner] Intent corrected: {intent} -> {final_intent}")
            intent = final_intent
        
        if intent not in self.states:
            print(f"[RL Tuner] Unknown intent: {intent}")
            return
        
        state = self.states[intent]
        
        # Find which arm was used
        arm_idx = None
        for idx, arm in enumerate(state.arms):
            if abs(arm.value - threshold) < 0.001:  # Float comparison
                arm_idx = idx
                break
        
        if arm_idx is None:
            print(f"[RL Tuner] Could not find arm for threshold={threshold:.3f}")
            return
        
        # Update arm statistics
        arm = state.arms[arm_idx]
        arm.pulls += 1
        arm.total_reward += reward
        state.last_updated = datetime.now().isoformat()
        
        # Decay epsilon
        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        
        print(f"[RL Tuner] Updated {intent} arm[{arm_idx}] (threshold={threshold:.3f}): "
              f"reward={reward:+.1f}, pulls={arm.pulls}, avg_reward={arm.average_reward:.3f}, "
              f"new_epsilon={self.epsilon:.3f}")
        
        # Periodic save (every 10 updates)
        total_updates = sum(state.exploration_count + state.exploitation_count 
                           for state in self.states.values())
        if total_updates % 10 == 0:
            self.save_state()
    
    def get_best_thresholds(self) -> Dict[str, float]:
        """Get current best threshold for each intent (for inspection)"""
        best_thresholds = {}
        for intent, state in self.states.items():
            best_idx = self._select_best_arm(state)
            best_thresholds[intent] = state.arms[best_idx].value
        return best_thresholds
    
    def get_stats(self) -> Dict[str, dict]:
        """Get detailed statistics for monitoring"""
        stats = {}
        for intent, state in self.states.items():
            total_pulls = sum(arm.pulls for arm in state.arms)
            best_idx = self._select_best_arm(state)
            
            stats[intent] = {
                'best_threshold': state.arms[best_idx].value,
                'best_avg_reward': state.arms[best_idx].average_reward,
                'total_pulls': total_pulls,
                'exploration_ratio': state.exploration_count / max(1, total_pulls),
                'arms': [
                    {
                        'threshold': arm.value,
                        'pulls': arm.pulls,
                        'avg_reward': arm.average_reward
                    }
                    for arm in state.arms
                ]
            }
        
        stats['_global'] = {
            'epsilon': self.epsilon,
            'total_intents': len(self.states),
            'total_pending': len(self.pending_experiences)
        }
        
        return stats


# Global instance (lazy initialization)
_tuner_instance: Optional[RLThresholdTuner] = None

def get_tuner() -> RLThresholdTuner:
    """Get or create global tuner instance"""
    global _tuner_instance
    if _tuner_instance is None:
        # Initialize with all known intents
        intents = [
            'dat_lich', 'hoi_thong_tin', 'cam_on', 'tam_biet', 'unknown',
            'xac_nhan', 'tu_choi', 'hoi_gio_lam_viec', 'hoi_dia_chi', 
            'khieu_nai', 'yeu_cau_ho_tro'
        ]
        _tuner_instance = RLThresholdTuner(intents=intents)
    return _tuner_instance

def shutdown_tuner():
    """Save state before shutdown"""
    global _tuner_instance
    if _tuner_instance:
        _tuner_instance.save_state()
        print("[RL Tuner] Shutdown complete")
