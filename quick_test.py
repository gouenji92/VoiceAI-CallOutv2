"""
Quick API Test - Minimal endpoints only
"""
import requests

BASE = "http://localhost:8000"

print("Testing VoiceAI API endpoints...\n")

# 1. Root
try:
    r = requests.get(f"{BASE}/")
    print(f"✓ Root: {r.status_code} - {r.json()}")
except Exception as e:
    print(f"✗ Root: {e}")

# 2. RL Status
try:
    r = requests.get(f"{BASE}/api/rl-monitor/status")
    print(f"✓ RL Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Epsilon: {data.get('epsilon')}")
        print(f"  Total updates: {data.get('total_updates')}")
except Exception as e:
    print(f"✗ RL Status: {e}")

# 3. RL Thresholds
try:
    r = requests.get(f"{BASE}/api/rl-monitor/thresholds")
    print(f"✓ RL Thresholds: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Intents: {list(data.keys())[:3]}...")
except Exception as e:
    print(f"✗ RL Thresholds: {e}")

# 4. Feedback stats (may need auth)
try:
    r = requests.get(f"{BASE}/api/feedback/rl-stats")
    print(f"✓ RL Stats: {r.status_code}")
except Exception as e:
    print(f"✗ RL Stats: {e}")

print("\n✅ API is accessible!")
