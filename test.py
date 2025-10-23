import os
import time
from supabase import create_client, Client
from datetime import datetime, timezone

# --- 1. PHẦN KHỞI TẠO ---
SUPABASE_URL = "https://vmffnryqvntucusjqhoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZtZmZucnlxdm50dWN1c2pxaG95Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1MTE2MDYsImV4cCI6MjA3NjA4NzYwNn0.uy11_QL1WiS1yg5RRqKOZBgz6vh1yFqM8iwmYYAYdw8"

# 🛑 ĐIỀN ID WORKFLOW THẬT CỦA BẠN (Đã lấy từ DB)
MY_WORKFLOW_ID = "caf4e4e1-b093-4275-997a-ab2769f58ce7" # VÍ DỤ: "f47ac10b-58cc-4372-a567-0e02b2c3d479"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ [PYTHON] Khởi tạo Supabase client thành công!")
except Exception as e:
    print(f"❌ [PYTHON] Lỗi khi khởi tạo Supabase: {e}")
    exit()

# --- 2. CÁC HÀM TƯƠNG TÁC API ---

def create_new_call(workflow_id: str, customer_phone: str):
    print("📞 [PYTHON] Đang tạo cuộc gọi...")
    try:
        response = supabase.table('calls').insert({
            'workflow_id': workflow_id,
            'customer_phone': customer_phone,
            'status': 'active',
            'start_time': datetime.now(timezone.utc).isoformat()
        }).execute()
        call_data = response.data[0]
        print(f"📞 [PYTHON] Tạo cuộc gọi thành công, ID: {call_data['id']}")
        return call_data
    except Exception as e:
        print(f"❌ [PYTHON] Lỗi khi tạo cuộc gọi: {e}")
        return None

def add_conversation_log(call_id: str, speaker: str, text: str, intent: str = None, confidence: float = None):
    print(f"💬 [PYTHON] Đang thêm log [{speaker}]: {text}")
    supabase.table('conversation_logs').insert({
        'call_id': call_id, 'speaker': speaker, 'text': text,
        'intent': intent, 'confidence': confidence
    }).execute()

def end_call(call_id: str, last_intent: str):
    print(f"🏁 [PYTHON] Đang kết thúc cuộc gọi: {call_id}")
    try:
        # 1. Lấy start_time
        call_response = supabase.table('calls').select('start_time').eq('id', call_id).single().execute()
        if not call_response.data:
            print("❌ Lỗi: Không tìm thấy cuộc gọi để kết thúc.")
            return

        # 2. Sửa lỗi Datetime: Chuyển đổi naive datetime từ DB sang aware
        start_time_str = call_response.data['start_time']
        start_time_naive = datetime.fromisoformat(start_time_str)
        start_time = start_time_naive.replace(tzinfo=timezone.utc)
        
        # 3. Lấy end_time (đã là aware)
        end_time = datetime.now(timezone.utc)
        
        # 4. Tính toán
        duration_in_seconds = (end_time - start_time).total_seconds()
        
        # 5. Cập nhật
        supabase.table('calls').update({
            'status': 'completed',
            'end_time': end_time.isoformat(),
            'last_intent': last_intent,
            'duration': duration_in_seconds
        }).eq('id', call_id).execute()
        print("🏁 [PYTHON] Kết thúc cuộc gọi thành công.")
    except Exception as e:
        print(f"❌ [PYTHON] Ngoại lệ khi kết thúc cuộc gọi: {e}")

# --- 3. HÀM MAIN ĐỂ CHẠY ---
if __name__ == "__main__":
    
    if MY_WORKFLOW_ID == "...":
        print("❌ LỖI: Vui lòng cập nhật biến 'MY_WORKFLOW_ID' (dòng 10) bằng ID workflow của bạn.")
    else:
        call_data = create_new_call(MY_WORKFLOW_ID, "0909111222")
        
        if call_data:
            call_id = call_data['id']
            print("🤖 [PYTHON] Bắt đầu giả lập cuộc gọi sau 3 giây...")
            time.sleep(3) # Chờ 3 giây để bạn kịp nhìn
            
            add_conversation_log(call_id, 'bot', 'Xin chào, đây là tổng đài AI.', None, None)
            time.sleep(2) # Chờ 2 giây
            
            add_conversation_log(call_id, 'user', 'Tôi muốn đặt lịch.', 'dat_lich', 0.95)
            time.sleep(2)
            
            add_conversation_log(call_id, 'bot', 'Vâng, bạn muốn đặt lịch khi nào?', None, None)
            time.sleep(2)
            
            add_conversation_log(call_id, 'user', '9h sáng mai.', 'cung_cap_thoi_gian', 0.98)
            time.sleep(1)
            
            end_call(call_id, 'cung_cap_thoi_gian')
            print("\n🎉 === TEST API (PYTHON) HOÀN TẤT ===")
        else:
            print("❌ [PYTHON] Không thể tạo cuộc gọi, dừng test.")