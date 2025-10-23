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
        intent_confidence = nlp_data.get("intent_confidence", 0.0)
        sentiment = nlp_data.get("sentiment", "neutral")
        entities = nlp_data.get("entities", {})

        print(f"[Agent] Nhan duoc State: Intent={intent}, Sentiment={sentiment}")
        # print(f"[Agent] Dang su dung workflow: {workflow_json.get('name')}") # Lấy tên từ JSON

        # --- 2. Logic Định tuyến (Routing Logic) ---
        
        # TODO: Đây là nơi bạn dùng `workflow_json` để quyết định câu trả lời
        # (Ví dụ: "if intent == 'dat_lich' AND node_hien_tai == 'node_chao_hoi': ...")
        
        # Logic xử lý dựa trên intent và confidence
        confidence_threshold = 0.6  # Ngưỡng tin cậy cho intent

        # Xử lý sentiment tiêu cực trước
        if sentiment == "negative":
            bot_response = "Toi xin loi neu co trai nghiem khong tot. Ban co muon ket noi voi nhan vien khong?"
            return {"response": bot_response, "action": "transfer"}

        # Xử lý các intent chính
        if intent == "dat_lich":
            if intent_confidence >= confidence_threshold:
                if "time" in entities:
                    bot_response = f"Vang, toi se giup ban dat lich vao luc {entities['time']}. Ban xac nhan nhe?"
                else:
                    bot_response = "Vang. Ban muon dat lich vao thoi gian nao a?"
            else:
                bot_response = "Toi hieu ban muon dat lich. Ban co the cho toi biet cu the thoi gian duoc khong?"
            return {"response": bot_response}

        elif intent == "hoi_thong_tin":
            print("[Agent] Dang goi RAG API...")
            if intent_confidence >= confidence_threshold:
                bot_response = f"Toi da tim thay thong tin lien quan den: {user_input}"
            else:
                bot_response = "Ban co the cho toi biet cu the hon ve thong tin ban can tim hieu duoc khong?"
            return {"response": bot_response}

        elif intent == "tam_biet":
            if intent_confidence >= confidence_threshold:
                bot_response = "Cam on ban da lien he. Chuc ban mot ngay tot lanh!"
            else:
                bot_response = "Ban muon ket thuc cuoc goi phai khong a? Cam on ban da lien he."
            return {"response": bot_response, "action": "hangup"}
        
        else: # intent == "unknown" hoặc confidence thấp
            if "unknown" in intent:
                bot_response = "Xin loi, toi chua hieu ro y cua ban. Ban co the noi ro hon duoc khong?"
            else:
                bot_response = f"Toi khong chac chan lam ve yeu cau cua ban. Ban co the giai thich them duoc khong?"
            return {"response": bot_response}