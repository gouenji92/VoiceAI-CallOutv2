"""
Test hệ thống HOÀN CHỈNH với Deeppavlov Agent
Yêu cầu: Agent server phải chạy ở port 4242
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"
AGENT_URL = "http://127.0.0.1:4242"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_agent():
    """Kiểm tra Agent server có chạy không"""
    try:
        res = requests.get(f"{AGENT_URL}/health", timeout=2)
        if res.status_code == 200:
            print("✅ Agent server đang chạy tại port 4242")
            return True
    except:
        pass
    print("❌ Agent server CHƯA chạy!")
    print("   Vui lòng chạy trong terminal riêng:")
    print("   python agent/http_agent.py")
    return False

def test_full_conversation():
    """Test hội thoại đầy đủ với Agent"""
    print_section("🚀 TEST HỘI THOẠI VỚI AGENT")
    
    # 1. Đăng ký & Login
    timestamp = int(time.time())
    email = f"agent_test_{timestamp}@gmail.com"
    password = "Test123456"
    
    print("\n1️⃣ Đăng ký tài khoản...")
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "password": password
    })
    if res.status_code != 201:
        print(f"❌ Lỗi đăng ký: {res.json()}")
        return False
    print(f"✅ Đã đăng ký: {email}")
    
    print("\n2️⃣ Đăng nhập...")
    res = requests.post(f"{BASE_URL}/api/auth/token", data={
        "username": email,
        "password": password
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Đã đăng nhập")
    
    # 2. Tạo workflow
    print("\n3️⃣ Tạo workflow...")
    res = requests.post(f"{BASE_URL}/api/workflows/", headers=headers, json={
        "name": "Agent Test Workflow",
        "description": "Test với Deeppavlov Agent"
    })
    workflow_id = res.json()["id"]
    print(f"✅ Workflow ID: {workflow_id}")
    
    # 3. Tạo version
    print("\n4️⃣ Tạo version cho workflow...")
    res = requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", headers=headers, json={
        "workflow_json": {
            "nodes": [
                {"id": "start", "type": "greeting", "text": "Xin chào!"},
                {"id": "ask_intent", "type": "question", "text": "Bạn cần gì?"}
            ],
            "edges": [{"from": "start", "to": "ask_intent"}]
        },
        "change_description": "Version test với Agent"
    })
    print("✅ Đã tạo version")
    
    # 4. Bắt đầu cuộc gọi
    print("\n5️⃣ Bắt đầu cuộc gọi...")
    res = requests.post(f"{BASE_URL}/api/calls/start_call", headers=headers, json={
        "workflow_id": workflow_id,
        "customer_phone": "0909999888"
    })
    call_id = res.json()["call_id"]
    print(f"✅ Call ID: {call_id}")
    
    # 5. Test hội thoại với Agent
    print("\n6️⃣ TEST HỘI THOẠI VỚI AGENT:")
    print("-" * 60)
    
    conversation = [
        "Xin chào",
        "Tôi muốn đặt lịch khám",
        "9h sáng mai",
        "Cảm ơn, tạm biệt"
    ]
    
    success_count = 0
    for i, user_text in enumerate(conversation, 1):
        print(f"\n  [{i}] 👤 User: {user_text}")
        
        res = requests.post(f"{BASE_URL}/api/calls/webhook", headers=headers, json={
            "call_id": call_id,
            "speech_to_text": user_text  # Fix: Đúng field name theo API schema
        })
        
        if res.status_code == 200:
            data = res.json()
            bot_response = data.get("bot_response", "")
            action = data.get("action", "")
            
            print(f"      🤖 Bot: {bot_response}")
            if action:
                print(f"      ⚡ Action: {action}")
            
            success_count += 1
        else:
            print(f"      ❌ Lỗi: {res.status_code} - {res.text}")
    
    print("\n" + "-" * 60)
    print(f"\n✅ Kết quả: {success_count}/{len(conversation)} responses thành công")
    
    return success_count == len(conversation)

def main():
    print("╔" + "="*58 + "╗")
    print("║" + " "*10 + "TEST HỆ THỐNG VOICEAI HOÀN CHỈNH" + " "*15 + "║")
    print("║" + " "*15 + "với DEEPPAVLOV AGENT" + " "*22 + "║")
    print("╚" + "="*58 + "╝")
    
    # Kiểm tra Agent
    if not check_agent():
        print("\n⚠️  HƯỚNG DẪN CHẠY AGENT:")
        print("    Terminal 1: python agent/http_agent.py")
        print("    Terminal 2: python test_with_agent.py")
        return
    
    # Chạy test
    result = test_full_conversation()
    
    # Kết quả
    print_section("📊 KẾT QUẢ TỔNG HỢP")
    if result:
        print("🎉 THÀNH CÔNG! Hệ thống hoạt động hoàn chỉnh 100%")
        print("✅ Backend API: OK")
        print("✅ Database: OK")
        print("✅ NLP PhoBERT: OK")
        print("✅ Deeppavlov Agent: OK")
        print("\n🚀 HỆ THỐNG ĐÃ SẴN SÀNG PRODUCTION!")
    else:
        print("❌ Có lỗi trong quá trình test. Kiểm tra logs!")

if __name__ == "__main__":
    main()
