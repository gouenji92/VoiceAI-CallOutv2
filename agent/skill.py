from dp_agent.skill import Skill
from typing import Dict, Any

class CallbotSkill(Skill):
    def __init__(self, **kwargs):
        super(CallbotSkill, self).__init__(**kwargs)
        print("Callbot Skill da duoc khoi tao!")

    def __call__(self, state: Dict, history: Dict, **kwargs) -> Dict:
        # 1. Lấy thông tin từ payload (do FastAPI gửi qua)
        # `state` là `payload` từ `dialog_manager.py`
        workflow_json = state.get("workflow_json", {})
        nlp_data = state.get("nlp_data", {})
        
        user_input = nlp_data.get("text", "")
        intent = nlp_data.get("intent", "unknown")
        sentiment = nlp_data.get("sentiment", "neutral")

        print(f"[Agent] Nhan duoc State: Intent={intent}, Sentiment={sentiment}")
        # print(f"[Agent] Dang su dung workflow: {workflow_json.get('name')}") # Lấy tên từ JSON

        # --- 2. Logic Định tuyến (Routing Logic) ---
        
        # TODO: Đây là nơi bạn dùng `workflow_json` để quyết định câu trả lời
        # (Ví dụ: "if intent == 'dat_lich' AND node_hien_tai == 'node_chao_hoi': ...")
        
        # Logic giả lập (thay thế bằng logic đọc workflow_json)
        if sentiment == "negative":
            bot_response = "Toi xin loi neu co trai nghiem khong tot. Ban co muon ket noi voi nhan vien không?"
            return {"response": bot_response, "action": "transfer"}

        if intent == "dat_lich":
            bot_response = "Vang a. Ban muon dat lich vao thoi gian nao?"
            return {"response": bot_response}

        elif intent == "hoi_thong_tin":
            # --- 3. Tích hợp RAG (Placeholder) ---
            print("[Agent] Dang goi RAG API (placeholder)...")
            bot_response = f"Toi da tim thay thong tin (gia lap RAG): {user_input}"
            return {"response": bot_response}

        elif intent == "tam_biet":
            bot_response = "Cam on ban da goi. Tam biet!"
            return {"response": bot_response, "action": "hangup"}
        
        else: # (intent == "unknown" hoặc các intent khác)
            bot_response = "Toi xin loi, toi chua hieu ro y cua ban."
            return {"response": bot_response}