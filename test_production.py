"""
Production Test Suite - Full E2E Testing
Test all critical endpoints with retrained model + RL
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("=" * 80)
print("PRODUCTION TEST SUITE - VOICEAI CALLOUT V2")
print("=" * 80)
print(f"Testing against: {BASE_URL}")
print(f"Timestamp: {datetime.now()}\n")

# Test results
results = {
    'passed': 0,
    'failed': 0,
    'tests': []
}

def test_endpoint(name, method, endpoint, data=None, expected_status=200):
    """Generic endpoint tester"""
    try:
        url = f"{BASE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        success = response.status_code == expected_status
        
        result = {
            'name': name,
            'endpoint': endpoint,
            'status': response.status_code,
            'success': success,
            'response': response.json() if response.status_code < 500 else None
        }
        
        if success:
            results['passed'] += 1
            print(f"✓ {name}")
        else:
            results['failed'] += 1
            print(f"✗ {name} (expected {expected_status}, got {response.status_code})")
        
        results['tests'].append(result)
        return result
        
    except Exception as e:
        results['failed'] += 1
        print(f"✗ {name} - ERROR: {str(e)}")
        results['tests'].append({
            'name': name,
            'endpoint': endpoint,
            'success': False,
            'error': str(e)
        })
        return None

print("\n[1] BASIC HEALTH CHECKS")
print("-" * 80)

# Root endpoint
test_endpoint("Root endpoint", "GET", "/")

# Docs (just check if accessible)
try:
    response = requests.get(f"{BASE_URL}/docs", timeout=5)
    if response.status_code == 200:
        results['passed'] += 1
        print("✓ Swagger docs accessible")
    else:
        results['failed'] += 1
        print("✗ Swagger docs not accessible")
except:
    results['failed'] += 1
    print("✗ Swagger docs error")

print("\n[2] RL MONITORING ENDPOINTS")
print("-" * 80)

# RL Status
status_result = test_endpoint("RL Monitor Status", "GET", "/api/rl-monitor/status")

# RL Thresholds
test_endpoint("RL Thresholds", "GET", "/api/rl-monitor/thresholds")

# RL Convergence
test_endpoint("RL Convergence", "GET", "/api/rl-monitor/convergence")

# RL Performance
test_endpoint("RL Performance", "GET", "/api/rl-monitor/performance")

print("\n[3] NLP SERVICE TESTS - WEAK INTENTS")
print("-" * 80)

# Test weak intents với retrained model
weak_intent_tests = [
    {
        "text": "Tôi cần hỗ trợ gấp",
        "expected_intent": "yeu_cau_ho_tro",
        "description": "yeu_cau_ho_tro test"
    },
    {
        "text": "Tôi từ chối đề xuất này",
        "expected_intent": "tu_choi",
        "description": "tu_choi test"
    },
    {
        "text": "Tôi muốn khiếu nại về dịch vụ",
        "expected_intent": "khieu_nai",
        "description": "khieu_nai test"
    },
    {
        "text": "Tôi muốn đặt lịch hẹn",
        "expected_intent": "dat_lich",
        "description": "dat_lich test"
    },
    {
        "text": "Cảm ơn bạn nhiều",
        "expected_intent": "cam_on",
        "description": "cam_on test"
    }
]

nlp_passed = 0
nlp_total = len(weak_intent_tests)

for test_case in weak_intent_tests:
    # Use proper webhook schema
    result = test_endpoint(
        test_case['description'],
        "POST",
        "/api/calls/webhook",
        data={
            "call_id": f"test-{int(time.time() * 1000)}",
            "speech_to_text": test_case['text']  # Fixed: use speech_to_text
        },
        expected_status=200  # May be 400/500 due to DB constraints
    )
    
    if result and result.get('response'):
        resp = result['response']
        intent = resp.get('nlp_result', {}).get('intent', 'unknown')
        confidence = resp.get('nlp_result', {}).get('intent_confidence', 0)
        
        if intent == test_case['expected_intent']:
            nlp_passed += 1
            print(f"  → Intent: {intent} (conf: {confidence:.3f}) ✓")
        else:
            print(f"  → Intent: {intent} (expected: {test_case['expected_intent']}) ✗")

print(f"\nNLP Accuracy: {nlp_passed}/{nlp_total} = {nlp_passed/nlp_total*100:.1f}%")

print("\n[4] RL FEEDBACK SIMULATION")
print("-" * 80)

# Simulate positive feedback
feedback_result = test_endpoint(
    "Submit RL feedback",
    "POST",
    "/api/feedback/rl-reward",
    data={
        "call_id": "test-feedback-001",
        "reward": 1.0,
        "final_intent": "dat_lich",
        "notes": "Production test - positive feedback"
    }
)

# Get RL stats after feedback
stats_result = test_endpoint("Get RL stats", "GET", "/api/feedback/rl-stats")

if stats_result and stats_result.get('response'):
    stats = stats_result['response']
    print(f"  → Epsilon: {stats.get('_global', {}).get('epsilon', 'N/A')}")
    print(f"  → Total pending: {stats.get('_global', {}).get('total_pending', 'N/A')}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✓ Passed: {results['passed']}")
print(f"✗ Failed: {results['failed']}")
print(f"Total: {results['passed'] + results['failed']}")
print(f"Success Rate: {results['passed']/(results['passed']+results['failed'])*100:.1f}%")

if results['failed'] == 0:
    print("\n🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION!")
elif results['passed'] > results['failed']:
    print("\n⚠️  PARTIAL SUCCESS - Some issues detected but core functionality works")
else:
    print("\n❌ CRITICAL ISSUES - Review failed tests before production")

# Save detailed results
with open('test_production_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nDetailed results saved to: test_production_results.json")

print("=" * 80)
