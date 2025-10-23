"""
Script test tự động toàn bộ APIs của VoiceAI
Chạy: python test_full_system.py
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api"
TEST_EMAIL = f"test_{int(time.time())}@gmail.com"
TEST_PASSWORD = "Test123456"

# Biến global để lưu token và IDs
token = None
workflow_id = None
call_id = None

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_result(test_name, success, data=None):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} | {test_name}")
    if data:
        print(f"  └─ {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")

# ============ TEST AUTH ============
def test_register():
    print_section("TEST 1: ĐĂNG KÝ TÀI KHOẢN")
    
    response = requests.post(
        f"{API_URL}/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": "user"
        }
    )
    
    success = response.status_code == 201
    print_result("Đăng ký tài khoản", success, response.json())
    return success

def test_login():
    global token
    print_section("TEST 2: ĐĂNG NHẬP")
    
    response = requests.post(
        f"{API_URL}/auth/token",
        data={
            "username": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_result("Đăng nhập", True, {"token": token[:50] + "..."})
        return True
    else:
        print_result("Đăng nhập", False, response.json())
        return False

# ============ TEST WORKFLOWS ============
def test_create_workflow():
    global workflow_id
    print_section("TEST 3: TẠO WORKFLOW")
    
    response = requests.post(
        f"{API_URL}/workflows/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": f"Test Workflow {datetime.now().strftime('%H:%M:%S')}",
            "description": "Workflow test tự động"
        }
    )
    
    if response.status_code == 201:
        workflow_id = response.json()["id"]
        print_result("Tạo workflow", True, response.json())
        return True
    else:
        print_result("Tạo workflow", False, response.json())
        return False

def test_get_workflows():
    print_section("TEST 4: LẤY DANH SÁCH WORKFLOWS")
    
    response = requests.get(
        f"{API_URL}/workflows/",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    success = response.status_code == 200
    data = response.json()
    if success and isinstance(data, list):
        print_result(f"Lấy workflows (Tìm thấy: {len(data)})", success, data[:2] if data else [])
    else:
        print_result("Lấy workflows", success, data)
    return success

def test_create_version():
    print_section("TEST 5: TẠO VERSION CHO WORKFLOW")
    
    workflow_json = {
        "nodes": [
            {"id": "start", "type": "greeting", "text": "Xin chào"},
            {"id": "ask_intent", "type": "question", "text": "Bạn cần gì?"}
        ],
        "edges": [
            {"from": "start", "to": "ask_intent"}
        ]
    }
    
    response = requests.put(
        f"{API_URL}/workflows/{workflow_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workflow_json": workflow_json,
            "change_description": "Version đầu tiên - khởi tạo flow"
        }
    )
    
    success = response.status_code == 200
    print_result("Tạo version", success, response.json())
    return success

def test_get_versions():
    print_section("TEST 6: XEM LỊCH SỬ VERSIONS")
    
    response = requests.get(
        f"{API_URL}/workflows/{workflow_id}/versions",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    success = response.status_code == 200
    data = response.json()
    if success and isinstance(data, list):
        print_result(f"Lấy versions (Tìm thấy: {len(data)})", success, data[:2] if data else [])
    else:
        print_result("Lấy versions", success, data)
    return success

# ============ TEST CALLS ============
def test_start_call():
    global call_id
    print_section("TEST 7: BẮT ĐẦU CUỘC GỌI")
    
    response = requests.post(
        f"{API_URL}/calls/start_call",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "workflow_id": workflow_id,
            "customer_phone": "0909123456"
        }
    )
    
    if response.status_code == 200:
        call_id = response.json()["call_id"]
        print_result("Bắt đầu cuộc gọi", True, response.json())
        return True
    else:
        print_result("Bắt đầu cuộc gọi", False, response.json())
        return False

def test_webhook():
    print_section("TEST 8: GỬI WEBHOOK (CONVERSATION)")
    
    test_inputs = [
        "Tôi muốn đặt lịch",
        "9h sáng mai",
        "Số điện thoại 0909123456",
        "Cảm ơn, tạm biệt"
    ]
    
    results = []
    for i, text in enumerate(test_inputs, 1):
        print(f"\n  [{i}] User: {text}")
        
        response = requests.post(
            f"{API_URL}/calls/webhook",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "call_id": call_id,
                "speech_to_text": text
            }
        )
        
        if response.status_code == 200:
            bot_response = response.json().get("bot_response_text")
            print(f"      Bot: {bot_response}")
            results.append(True)
        else:
            print(f"      ❌ Error: {response.json()}")
            results.append(False)
        
        time.sleep(0.5)  # Chờ chút giữa các request
    
    success = all(results)
    print_result(f"Webhook conversation ({len(results)}/{len(test_inputs)} thành công)", success)
    return success

# ============ MAIN ============
def run_all_tests():
    print("\n" + "🚀"*30)
    print("  VOICEAI - FULL SYSTEM TEST")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("🚀"*30)
    
    tests = [
        ("Đăng ký", test_register),
        ("Đăng nhập", test_login),
        ("Tạo workflow", test_create_workflow),
        ("Lấy workflows", test_get_workflows),
        ("Tạo version", test_create_version),
        ("Xem versions", test_get_versions),
        ("Bắt đầu cuộc gọi", test_start_call),
        ("Test hội thoại", test_webhook),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ FAIL | {name} - Exception: {e}")
            results.append((name, False))
        
        time.sleep(0.3)  # Chờ giữa các test
    
    # Summary
    print_section("📊 KẾT QUẢ TỔNG HỢP")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {name}")
    
    print(f"\n{'='*60}")
    print(f"  Tổng kết: {passed}/{total} tests passed ({passed*100//total}%)")
    print('='*60)
    
    if passed == total:
        print("\n🎉 TẤT CẢ TESTS ĐỀU THÀNH CÔNG! HỆ THỐNG HOẠT ĐỘNG HOÀN HẢO!")
    else:
        print(f"\n⚠️  Có {total - passed} tests thất bại. Kiểm tra lại!")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test bị dừng bởi người dùng")
    except requests.exceptions.ConnectionError:
        print("\n❌ Không thể kết nối đến server!")
        print("   Đảm bảo server đang chạy: python -X utf8 -m uvicorn app.main:app --reload")
