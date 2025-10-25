"""
VoiceAI System Integration Test Suite
Tổng hợp tất cả tests: API, Model, RL, RAG, Production E2E
Chạy: python test_system.py
"""
import sys
import time
import json
from typing import Dict, List, Optional
from datetime import datetime

import httpx
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ============================================================================
# CONFIG
# ============================================================================

API_BASE = "http://localhost:8000"
TIMEOUT = 10.0

TEST_INTENTS = [
    ("Tôi cần hỗ trợ gấp", "yeu_cau_ho_tro"),
    ("Tôi từ chối đề xuất này", "tu_choi"),
    ("Tôi muốn khiếu nại về dịch vụ", "khieu_nai"),
    ("Tôi muốn đặt lịch hẹn", "dat_lich"),
    ("Cảm ơn bạn nhiều", "cam_on"),
    ("Tôi đồng ý", "dong_y"),
]

# ============================================================================
# TEST RESULTS TRACKER
# ============================================================================

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests: List[Dict] = []
        
    def add_pass(self, name: str, details: Optional[Dict] = None):
        self.passed += 1
        self.tests.append({
            "name": name,
            "status": "PASS",
            "details": details or {}
        })
        print(f"  ✅ {name}")
        
    def add_fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({
            "name": name,
            "status": "FAIL",
            "error": error
        })
        print(f"  ❌ {name}: {error}")
        
    def summary(self):
        total = self.passed + self.failed
        rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n{'='*60}")
        print(f"  TỔNG KẾT: {self.passed}/{total} tests passed ({rate:.1f}%)")
        print(f"{'='*60}")
        
        if self.failed > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.tests:
                if test["status"] == "FAIL":
                    print(f"  - {test['name']}: {test['error']}")
        
        return self.passed, self.failed

results = TestResults()

# ============================================================================
# SECTION 1: API HEALTH & MONITORING
# ============================================================================

def test_api_health():
    """Test basic API health endpoints"""
    print("\n" + "="*60)
    print("1️⃣  API HEALTH & MONITORING")
    print("="*60)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Root endpoint
            resp = client.get(f"{API_BASE}/")
            if resp.status_code == 200:
                results.add_pass("Root endpoint", {"response": resp.json()})
            else:
                results.add_fail("Root endpoint", f"Status {resp.status_code}")
                
            # RL Monitor Status
            resp = client.get(f"{API_BASE}/api/rl-monitor/status")
            if resp.status_code == 200:
                data = resp.json()
                results.add_pass("RL Monitor Status", {
                    "epsilon": data.get("epsilon"),
                    "total_updates": data.get("total_updates")
                })
            else:
                results.add_fail("RL Monitor Status", f"Status {resp.status_code}")
                
            # RL Thresholds
            resp = client.get(f"{API_BASE}/api/rl-monitor/thresholds")
            if resp.status_code == 200:
                data = resp.json()
                results.add_pass("RL Thresholds", {"count": len(data.get("thresholds", []))})
            else:
                results.add_fail("RL Thresholds", f"Status {resp.status_code}")
                
    except Exception as e:
        results.add_fail("API Health Tests", str(e))

# ============================================================================
# SECTION 2: MODEL DIRECT INFERENCE
# ============================================================================

def test_model_inference():
    """Test PhoBERT model direct inference"""
    print("\n" + "="*60)
    print("2️⃣  MODEL DIRECT INFERENCE (PhoBERT)")
    print("="*60)
    
    try:
        # Try latest retrained model first
        model_paths = [
            "models/phobert-intent-v3-retrain-20251023_232548/final",
            "models/phobert-intent-v3/final",
            "models/phobert-intent-classifier"
        ]
        
        model = None
        tokenizer = None
        model_path = None
        
        for path in model_paths:
            try:
                tokenizer = AutoTokenizer.from_pretrained(path)
                model = AutoModelForSequenceClassification.from_pretrained(path)
                model_path = path
                break
            except:
                continue
                
        if model is None:
            results.add_fail("Model Loading", "No model found")
            return
            
        results.add_pass("Model Loading", {"path": model_path})
        
        # Test predictions
        model.eval()
        correct = 0
        total = 0
        
        for text, expected_intent in TEST_INTENTS:
            inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=256)
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)
                predicted_idx = torch.argmax(probs, dim=-1).item()
                confidence = probs[0, predicted_idx].item()
                
                # Get label
                id2label = model.config.id2label
                predicted_label = id2label.get(predicted_idx, "unknown")
                
                total += 1
                if predicted_label == expected_intent:
                    correct += 1
                    results.add_pass(f"Intent: {expected_intent}", {
                        "text": text[:40] + "...",
                        "confidence": f"{confidence:.3f}"
                    })
                else:
                    results.add_fail(f"Intent: {expected_intent}", 
                                   f"Predicted {predicted_label} (conf={confidence:.3f})")
        
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"\n  📊 Model Accuracy: {correct}/{total} ({accuracy:.1f}%)")
        
    except Exception as e:
        results.add_fail("Model Inference Tests", str(e))

# ============================================================================
# SECTION 3: NLP SERVICE API
# ============================================================================

def test_nlp_service():
    """Test NLP service via API (webhook endpoint)"""
    print("\n" + "="*60)
    print("3️⃣  NLP SERVICE API (Webhook)")
    print("="*60)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            for text, expected_intent in TEST_INTENTS[:3]:  # Test first 3
                payload = {
                    "call_id": f"test-{int(time.time()*1000)}",
                    "speech_to_text": text
                }
                
                try:
                    resp = client.post(f"{API_BASE}/api/calls/webhook", json=payload)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        detected_intent = data.get("nlp_data", {}).get("intent", "unknown")
                        confidence = data.get("nlp_data", {}).get("intent_confidence", 0)
                        
                        if detected_intent == expected_intent:
                            results.add_pass(f"Webhook: {expected_intent}", {
                                "confidence": f"{confidence:.3f}"
                            })
                        else:
                            results.add_fail(f"Webhook: {expected_intent}",
                                           f"Got {detected_intent} (conf={confidence:.3f})")
                    else:
                        results.add_fail(f"Webhook: {expected_intent}", 
                                       f"Status {resp.status_code}")
                except Exception as e:
                    results.add_fail(f"Webhook: {expected_intent}", str(e))
                    
    except Exception as e:
        results.add_fail("NLP Service Tests", str(e))

# ============================================================================
# SECTION 4: RL FEEDBACK LOOP
# ============================================================================

def test_rl_feedback():
    """Test RL feedback submission and state update"""
    print("\n" + "="*60)
    print("4️⃣  RL FEEDBACK LOOP")
    print("="*60)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Get initial state
            resp = client.get(f"{API_BASE}/api/rl-monitor/status")
            if resp.status_code == 200:
                initial_epsilon = resp.json().get("epsilon")
                initial_updates = resp.json().get("total_updates", 0)
                results.add_pass("RL Initial State", {
                    "epsilon": f"{initial_epsilon:.4f}",
                    "updates": initial_updates
                })
            else:
                results.add_fail("RL Initial State", f"Status {resp.status_code}")
                return
            
            # Submit positive reward
            payload = {
                "call_id": f"test-rl-{int(time.time())}",
                "reward": 1.0,
                "final_intent": "dong_y",
                "notes": "Test positive feedback"
            }
            
            resp = client.post(f"{API_BASE}/api/feedback/rl-reward", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                new_epsilon = data.get("current_epsilon")
                results.add_pass("RL Feedback Submission", {
                    "reward": "+1.0",
                    "new_epsilon": f"{new_epsilon:.4f}"
                })
            else:
                results.add_fail("RL Feedback Submission", f"Status {resp.status_code}")
                return
            
            # Verify state updated
            time.sleep(0.5)
            resp = client.get(f"{API_BASE}/api/rl-monitor/status")
            if resp.status_code == 200:
                final_updates = resp.json().get("total_updates", 0)
                if final_updates > initial_updates:
                    results.add_pass("RL State Update", {
                        "updates": f"{initial_updates} → {final_updates}"
                    })
                else:
                    results.add_fail("RL State Update", "Update count not increased")
            else:
                results.add_fail("RL State Update", f"Status {resp.status_code}")
                
    except Exception as e:
        results.add_fail("RL Feedback Tests", str(e))

# ============================================================================
# SECTION 5: RAG SERVICE
# ============================================================================

def test_rag_service():
    """Test RAG search and ingest"""
    print("\n" + "="*60)
    print("5️⃣  RAG SERVICE (Retrieval-Augmented Generation)")
    print("="*60)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Test search (may return empty if no data)
            resp = client.get(f"{API_BASE}/api/rag/search", params={
                "q": "bảo hiểm",
                "k": 3
            })
            
            if resp.status_code == 200:
                data = resp.json()
                results_count = len(data.get("results", []))
                results.add_pass("RAG Search", {
                    "query": "bảo hiểm",
                    "results": results_count
                })
            else:
                results.add_fail("RAG Search", f"Status {resp.status_code}")
                
            # Test ingest would require auth token, skip for now
            # Just verify endpoint exists
            resp = client.post(f"{API_BASE}/api/rag/ingest", json={
                "content": "test"
            })
            
            if resp.status_code in [401, 403]:  # Expected without auth
                results.add_pass("RAG Ingest Endpoint", {"note": "Auth required (expected)"})
            elif resp.status_code == 200:
                results.add_pass("RAG Ingest Endpoint", {"note": "Success"})
            else:
                results.add_fail("RAG Ingest Endpoint", f"Unexpected status {resp.status_code}")
                
    except Exception as e:
        results.add_fail("RAG Service Tests", str(e))

# ============================================================================
# SECTION 6: AUTHENTICATION & AUTHORIZATION
# ============================================================================

def test_auth():
    """Test authentication endpoints"""
    print("\n" + "="*60)
    print("6️⃣  AUTHENTICATION & AUTHORIZATION")
    print("="*60)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Test protected endpoint without auth
            resp = client.get(f"{API_BASE}/api/feedback/rl-stats")
            
            if resp.status_code == 401:
                results.add_pass("Auth Protection", {"note": "401 without token (expected)"})
            else:
                results.add_fail("Auth Protection", f"Expected 401, got {resp.status_code}")
                
            # Test login with dummy credentials (will fail, that's ok)
            resp = client.post(f"{API_BASE}/api/auth/login", json={
                "email": "test@test.com",
                "password": "wrongpassword"
            })
            
            if resp.status_code in [401, 404]:
                results.add_pass("Auth Login Endpoint", {"note": "Rejects invalid credentials"})
            elif resp.status_code == 200:
                results.add_pass("Auth Login Endpoint", {"note": "Login successful"})
            else:
                results.add_fail("Auth Login Endpoint", f"Unexpected status {resp.status_code}")
                
    except Exception as e:
        results.add_fail("Auth Tests", str(e))

# ============================================================================
# SECTION 7: AGENT INTEGRATION
# ============================================================================

def test_agent_integration():
    """Test agent dialog management integration"""
    print("\n" + "="*60)
    print("7️⃣  AGENT INTEGRATION (Dialog Manager)")
    print("="*60)
    
    try:
        with httpx.Client(timeout=TIMEOUT) as client:
            # Test webhook with different intents to trigger agent
            test_cases = [
                ("Tôi muốn biết thông tin sản phẩm", "hoi_thong_tin"),
                ("Cảm ơn bạn", "cam_on"),
            ]
            
            for text, expected_intent in test_cases:
                payload = {
                    "call_id": f"test-agent-{int(time.time()*1000)}",
                    "speech_to_text": text
                }
                
                try:
                    resp = client.post(f"{API_BASE}/api/calls/webhook", json=payload)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        bot_response = data.get("bot_response", "")
                        action = data.get("action")
                        
                        if bot_response:
                            results.add_pass(f"Agent Response: {expected_intent}", {
                                "response": bot_response[:60] + "...",
                                "action": action or "none"
                            })
                        else:
                            results.add_fail(f"Agent Response: {expected_intent}", 
                                           "No bot response returned")
                    else:
                        results.add_fail(f"Agent Response: {expected_intent}", 
                                       f"Status {resp.status_code}")
                except Exception as e:
                    results.add_fail(f"Agent Response: {expected_intent}", str(e))
                    
    except Exception as e:
        results.add_fail("Agent Integration Tests", str(e))

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "="*60)
    print("  🚀 VOICEAI SYSTEM TEST SUITE")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    print(f"\n📡 Testing API at: {API_BASE}")
    print(f"⏱️  Timeout: {TIMEOUT}s")
    
    # Run all test sections
    test_api_health()
    test_model_inference()
    test_nlp_service()
    test_rl_feedback()
    test_rag_service()
    test_auth()
    test_agent_integration()
    
    # Print summary
    passed, failed = results.summary()
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "success_rate": f"{(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "0%"
        },
        "tests": results.tests
    }
    
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: test_results.json")
    
    # Exit code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
