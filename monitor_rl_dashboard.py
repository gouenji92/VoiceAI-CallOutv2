"""
RL Monitor - Interactive Dashboard (Terminal UI)
Real-time monitoring của RL Threshold Tuner
"""

import requests
import time
import os
from datetime import datetime
from typing import Dict, Any

API_BASE = "http://localhost:8000/api/rl-monitor"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 80)
    print("🤖 RL THRESHOLD TUNER - LIVE MONITORING DASHBOARD")
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_status(status: Dict[str, Any]):
    print("📊 SYSTEM STATUS")
    print("-" * 80)
    print(f"  Epsilon (exploration rate): {status['epsilon']:.4f}")
    print(f"  Total updates: {status['total_updates']}")
    print(f"  Exploration: {status['exploration_count']} ({status['exploration_ratio']:.1%})")
    print(f"  Exploitation: {status['exploitation_count']} ({1-status['exploration_ratio']:.1%})")
    print(f"  Intents tracked: {status['num_intents']}")
    print(f"  Threshold range: [{status['threshold_range'][0]:.2f}, {status['threshold_range'][1]:.2f}]")
    print()

def print_thresholds(thresholds: Dict[str, float]):
    print("🎯 BEST THRESHOLDS PER INTENT")
    print("-" * 80)
    
    # Sort by intent name
    sorted_intents = sorted(thresholds.items())
    
    for intent, threshold in sorted_intents:
        bar_length = int(threshold * 50)  # Scale to 50 chars
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"  {intent:20s} {threshold:.3f} │{bar}│")
    print()

def print_convergence(convergence: Dict[str, Any]):
    print("🔄 CONVERGENCE STATUS")
    print("-" * 80)
    print(f"  Overall convergence: {convergence['overall_convergence']:.1%}")
    print(f"  Converged intents: {convergence['converged_intents']}/{convergence['total_intents']}")
    print(f"  Recommendation: {convergence['recommendation']}")
    print()
    
    print("  Per-intent convergence:")
    for intent, data in sorted(convergence['intents'].items()):
        status = "✅" if data.get('converged', False) else "⏳"
        confidence = data.get('confidence', 0)
        pulls = data.get('total_pulls', 0)
        best = data.get('best_threshold', 0)
        
        if pulls > 0:
            print(f"    {status} {intent:20s} confidence={confidence:.2%} pulls={pulls:3d} best={best:.3f}")
        else:
            print(f"    ⚪ {intent:20s} {data.get('reason', 'No data')}")
    print()

def print_performance(performance: Dict[str, Any]):
    print("📈 PERFORMANCE METRICS")
    print("-" * 80)
    
    if 'overall' in performance:
        overall = performance['overall']
        print(f"  Overall avg reward: {overall['avg_reward']:+.4f}")
        print(f"  Total pulls: {overall['total_pulls']}")
        print(f"  Avg exploration rate: {overall['avg_exploration_rate']:.1%}")
        print()
    
    print("  Top 5 performers:")
    # Sort by avg_reward
    sorted_intents = sorted(
        [(k, v) for k, v in performance['intents'].items() if v.get('total_pulls', 0) > 0],
        key=lambda x: x[1].get('avg_reward', -999),
        reverse=True
    )[:5]
    
    for intent, metrics in sorted_intents:
        reward = metrics['avg_reward']
        pulls = metrics['total_pulls']
        best = metrics['best_threshold']
        color = "🟢" if reward > 0.5 else "🟡" if reward > 0 else "🔴"
        print(f"    {color} {intent:20s} reward={reward:+.4f} pulls={pulls:3d} best={best:.3f}")
    print()

def fetch_data(endpoint: str) -> Dict[str, Any]:
    """Fetch data from API endpoint"""
    try:
        response = requests.get(f"{API_BASE}/{endpoint}", timeout=2)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🚀 Starting RL Monitor Dashboard...")
    print(f"📡 Connecting to API at {API_BASE}")
    print("Press Ctrl+C to exit")
    time.sleep(2)
    
    try:
        while True:
            clear_screen()
            
            # Fetch all data
            status = fetch_data("status")
            thresholds = fetch_data("thresholds")
            convergence = fetch_data("convergence")
            performance = fetch_data("performance")
            
            # Display
            print_header()
            
            if "error" in status:
                print(f"❌ ERROR: {status['error']}")
                print("\n💡 Make sure FastAPI server is running:")
                print("   python -X utf8 -m uvicorn app.main:app --reload")
                time.sleep(5)
                continue
            
            print_status(status)
            print_thresholds(thresholds)
            print_convergence(convergence)
            print_performance(performance)
            
            print("-" * 80)
            print("🔄 Refreshing in 10 seconds... (Ctrl+C to exit)")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
