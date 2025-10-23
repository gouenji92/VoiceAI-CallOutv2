print("Dang ket noi Asterisk AMI... (gia lap)")

def initiate_callout(call_id: str, phone_number: str, workflow_id: str) -> bool:
    print(f"[Asterisk Service] Thuc hien goi ra so: {phone_number} cho Call ID: {call_id}")
    
    # --- LOGIC GIẢ LẬP ---
    # TODO: Đây là nơi bạn điền code thật để kết nối Asterisk AMI
    # (ví dụ: dùng thư viện 'pami' hoặc 'panoramisk')
    # Gửi action Originate...
    
    print("[Asterisk Service] Gui lenh Originate thanh cong (gia lap).")
    return True