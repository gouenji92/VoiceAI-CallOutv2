"""
Visualization and monitoring for RL threshold tuner.
Shows threshold evolution, arm performance, and intent accuracy trends.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Dict, List
import seaborn as sns

sns.set_style("whitegrid")

STATE_FILE = Path("models/rl_threshold_state.json")

def load_state() -> dict:
    """Load current RL tuner state"""
    if not STATE_FILE.exists():
        print(f"State file not found: {STATE_FILE}")
        return {}
    
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_threshold_distribution(state_data: dict):
    """Plot current best threshold for each intent"""
    if not state_data or 'states' not in state_data:
        print("No state data available")
        return
    
    intents = []
    best_thresholds = []
    avg_rewards = []
    
    for intent_state in state_data['states']:
        intent = intent_state['intent']
        arms = intent_state['arms']
        
        # Find best arm
        best_arm = max(arms, key=lambda a: a.get('average_reward', 0) if a['pulls'] > 0 else -999)
        
        if best_arm['pulls'] > 0:
            intents.append(intent)
            best_thresholds.append(best_arm['value'])
            avg_rewards.append(best_arm.get('average_reward', 0))
    
    if not intents:
        print("No arms have been pulled yet")
        return
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Plot 1: Best thresholds
    colors = ['green' if r > 0.5 else 'orange' if r > 0 else 'red' for r in avg_rewards]
    bars1 = ax1.barh(intents, best_thresholds, color=colors, alpha=0.7)
    ax1.set_xlabel('Best Threshold', fontsize=12)
    ax1.set_ylabel('Intent', fontsize=12)
    ax1.set_title('Current Best Thresholds per Intent', fontsize=14, fontweight='bold')
    ax1.axvline(x=0.85, color='gray', linestyle='--', alpha=0.5, label='Baseline (0.85)')
    ax1.axvline(x=0.90, color='red', linestyle='--', alpha=0.5, label='Cap (0.90)')
    ax1.set_xlim(0.75, 1.0)
    ax1.legend()
    ax1.grid(axis='x', alpha=0.3)
    
    # Plot 2: Average rewards
    bars2 = ax2.barh(intents, avg_rewards, color=colors, alpha=0.7)
    ax2.set_xlabel('Average Reward', fontsize=12)
    ax2.set_ylabel('Intent', fontsize=12)
    ax2.set_title('Average Reward per Intent', fontsize=14, fontweight='bold')
    ax2.axvline(x=0, color='gray', linestyle='-', alpha=0.5)
    ax2.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('models/rl_threshold_visualization.png', dpi=150, bbox_inches='tight')
    print("Saved visualization to models/rl_threshold_visualization.png")
    plt.show()

def plot_arm_performance(state_data: dict, intent: str):
    """Plot performance of all arms for a specific intent"""
    if not state_data or 'states' not in state_data:
        print("No state data available")
        return
    
    # Find intent state
    intent_state = None
    for state in state_data['states']:
        if state['intent'] == intent:
            intent_state = state
            break
    
    if not intent_state:
        print(f"Intent '{intent}' not found")
        return
    
    arms = intent_state['arms']
    
    thresholds = [arm['value'] for arm in arms]
    pulls = [arm['pulls'] for arm in arms]
    avg_rewards = [arm.get('average_reward', 0) if arm['pulls'] > 0 else 0 for arm in arms]
    total_rewards = [arm.get('total_reward', 0) for arm in arms]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Pulls per arm
    axes[0, 0].bar(range(len(thresholds)), pulls, color='skyblue', alpha=0.7)
    axes[0, 0].set_xticks(range(len(thresholds)))
    axes[0, 0].set_xticklabels([f"{t:.3f}" for t in thresholds], rotation=45)
    axes[0, 0].set_xlabel('Threshold Value')
    axes[0, 0].set_ylabel('Number of Pulls')
    axes[0, 0].set_title(f'Arm Exploration: {intent}')
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # Plot 2: Average reward per arm
    colors = ['green' if r > 0.5 else 'orange' if r > 0 else 'red' for r in avg_rewards]
    axes[0, 1].bar(range(len(thresholds)), avg_rewards, color=colors, alpha=0.7)
    axes[0, 1].set_xticks(range(len(thresholds)))
    axes[0, 1].set_xticklabels([f"{t:.3f}" for t in thresholds], rotation=45)
    axes[0, 1].set_xlabel('Threshold Value')
    axes[0, 1].set_ylabel('Average Reward')
    axes[0, 1].set_title(f'Average Reward per Arm: {intent}')
    axes[0, 1].axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    axes[0, 1].grid(axis='y', alpha=0.3)
    
    # Plot 3: Total reward per arm
    axes[1, 0].bar(range(len(thresholds)), total_rewards, color='purple', alpha=0.7)
    axes[1, 0].set_xticks(range(len(thresholds)))
    axes[1, 0].set_xticklabels([f"{t:.3f}" for t in thresholds], rotation=45)
    axes[1, 0].set_xlabel('Threshold Value')
    axes[1, 0].set_ylabel('Total Reward')
    axes[1, 0].set_title(f'Total Reward per Arm: {intent}')
    axes[1, 0].axhline(y=0, color='gray', linestyle='-', alpha=0.5)
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # Plot 4: Reward rate (avg_reward with error bars based on pulls)
    valid_indices = [i for i, p in enumerate(pulls) if p > 0]
    if valid_indices:
        valid_thresholds = [thresholds[i] for i in valid_indices]
        valid_avg_rewards = [avg_rewards[i] for i in valid_indices]
        valid_pulls = [pulls[i] for i in valid_indices]
        
        # Confidence intervals (simplified as 1/sqrt(n))
        errors = [1.0 / np.sqrt(p) if p > 0 else 0 for p in valid_pulls]
        
        axes[1, 1].errorbar(valid_thresholds, valid_avg_rewards, yerr=errors, 
                           fmt='o-', capsize=5, capthick=2, markersize=8, alpha=0.7)
        axes[1, 1].axhline(y=0, color='gray', linestyle='-', alpha=0.5)
        axes[1, 1].set_xlabel('Threshold Value')
        axes[1, 1].set_ylabel('Average Reward')
        axes[1, 1].set_title(f'Reward Trend with Confidence: {intent}')
        axes[1, 1].grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'models/rl_arm_performance_{intent}.png', dpi=150, bbox_inches='tight')
    print(f"Saved arm performance plot to models/rl_arm_performance_{intent}.png")
    plt.show()

def print_summary(state_data: dict):
    """Print text summary of RL tuner state"""
    if not state_data or 'states' not in state_data:
        print("No state data available")
        return
    
    print("=" * 80)
    print("RL THRESHOLD TUNER SUMMARY")
    print("=" * 80)
    
    epsilon = state_data.get('epsilon', 'N/A')
    last_saved = state_data.get('last_saved', 'N/A')
    
    print(f"\nGlobal State:")
    print(f"  Current Epsilon: {epsilon:.4f}" if isinstance(epsilon, float) else f"  Current Epsilon: {epsilon}")
    print(f"  Last Saved: {last_saved}")
    print(f"  Total Intents: {len(state_data.get('states', []))}")
    
    print("\nPer-Intent Summary:")
    print(f"{'Intent':<20} {'Best Threshold':>15} {'Avg Reward':>12} {'Total Pulls':>12} {'Explore/Exploit'}")
    print("-" * 80)
    
    for intent_state in state_data['states']:
        intent = intent_state['intent']
        arms = intent_state['arms']
        exploration = intent_state.get('exploration_count', 0)
        exploitation = intent_state.get('exploitation_count', 0)
        
        # Find best arm
        best_arm = max(arms, key=lambda a: a.get('average_reward', 0) if a['pulls'] > 0 else -999)
        total_pulls = sum(arm['pulls'] for arm in arms)
        
        if best_arm['pulls'] > 0:
            print(f"{intent:<20} {best_arm['value']:>15.3f} {best_arm.get('average_reward', 0):>12.3f} "
                  f"{total_pulls:>12} {exploration:>6}/{exploitation:<6}")
        else:
            print(f"{intent:<20} {'N/A':>15} {'N/A':>12} {total_pulls:>12} {exploration:>6}/{exploitation:<6}")
    
    print("=" * 80)

def main():
    """Main monitoring function"""
    state = load_state()
    
    if not state:
        print("No RL state found. Run the system to generate data.")
        return
    
    # Print summary
    print_summary(state)
    
    # Plot threshold distribution
    plot_threshold_distribution(state)
    
    # Plot detailed arm performance for selected intents
    intents_to_plot = ['dat_lich', 'hoi_thong_tin', 'xac_nhan', 'tu_choi']
    for intent in intents_to_plot:
        try:
            plot_arm_performance(state, intent)
        except Exception as e:
            print(f"Failed to plot {intent}: {e}")

if __name__ == "__main__":
    main()
