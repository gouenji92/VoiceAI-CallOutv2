"""Quick test script - chỉ test 3 API bị lỗi"""
import requests
import json

API_URL = "http://127.0.0.1:8000/api"

# Dùng account đã có
print("=== ĐĂNG NHẬP ===")
response = requests.post(
    f"{API_URL}/auth/token",
    data={
        "username": "test_1761216438@gmail.com",  # Email từ lần test trước
        "password": "Test123456"
    }
)
if response.status_code != 200:
    print(f"❌ Login fail: {response.json()}")
    exit(1)

token = response.json()["access_token"]
print(f"✅ Login OK: {token[:20]}...")

# Lấy workflows hiện có
print("\n=== LẤY WORKFLOWS ===")
response = requests.get(
    f"{API_URL}/workflows/",
    headers={"Authorization": f"Bearer {token}"}
)
workflows = response.json()
if not workflows:
    print("❌ Không có workflow nào")
    exit(1)

workflow_id = workflows[0]["id"]
print(f"✅ Workflow ID: {workflow_id}")

# TEST 1: Tạo version
print("\n=== TEST TẠO VERSION ===")
response = requests.put(
    f"{API_URL}/workflows/{workflow_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "workflow_json": {"nodes": [{"id": "start", "text": "Hello"}]},
        "change_description": "Test version"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if response.status_code == 200:
    print("✅ Tạo version thành công!")
else:
    print(f"❌ Tạo version thất bại")

# TEST 2: Start call
print("\n=== TEST START CALL ===")
response = requests.post(
    f"{API_URL}/calls/start_call",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "workflow_id": workflow_id,
        "customer_phone": "0909123456"
    }
)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if response.status_code == 200:
    call_id = response.json()["call_id"]
    print(f"✅ Start call thành công! Call ID: {call_id}")
    
    # TEST 3: Webhook
    print("\n=== TEST WEBHOOK ===")
    response = requests.post(
        f"{API_URL}/calls/webhook",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "call_id": call_id,
            "speech_to_text": "Xin chào"
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
else:
    print("❌ Start call thất bại")
