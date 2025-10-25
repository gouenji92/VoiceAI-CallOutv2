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

        # --- 2. Logic Định tuyến (Routing Logic) ---
        # workflow_json contains the workflow configuration that can be used
        # for more sophisticated routing and business logic customization
        
        # Logic xử lý dựa trên intent và confidence
        confidence_threshold = 0.6  # Ngưỡng tin cậy cho intent
        
        # Default response structure with action_success for RL feedback
        result = {"response": "", "action": None, "action_success": None}

        # Xử lý sentiment tiêu cực trước
        if sentiment == "negative":
            bot_response = "Toi xin loi neu co trai nghiem khong tot. Ban co muon ket noi voi nhan vien khong?"
            result["response"] = bot_response
            result["action"] = "transfer"
            result["action_success"] = False  # Negative sentiment = not ideal
            return result

        # Xử lý các intent chính
        if intent == "dat_lich":
            if intent_confidence >= confidence_threshold:
                if "time" in entities:
                    bot_response = f"Vang, toi se giup ban dat lich vao luc {entities['time']}. Ban xac nhan nhe?"
                    result["action_success"] = True  # Successfully extracted time
                else:
                    bot_response = "Vang. Ban muon dat lich vao thoi gian nao a?"
                    result["action_success"] = None  # Need more info (neutral)
            else:
                bot_response = "Toi hieu ban muon dat lich. Ban co the cho toi biet cu the thoi gian duoc khong?"
                result["action_success"] = None  # Low confidence, need clarification
            result["response"] = bot_response
            return result

        elif intent == "hoi_thong_tin":
            # Try querying RAG API when confidence is sufficient
            import httpx
            print("[Agent] Dang goi RAG API...")
            if intent_confidence >= confidence_threshold:
                try:
                    url = "http://127.0.0.1:8000/api/rag/search"
                    params = {"q": user_input, "k": 3}
                    with httpx.Client(timeout=4.0) as client:
                        resp = client.get(url, params=params)
                        if resp.status_code == 200:
                            data = resp.json()
                            results = data.get("results", [])
                            if results:
                                top = results[0]
                                snippet = top.get("content", "")
                                source = top.get("source", "")
                                bot_response = f"Toi tim duoc thong tin: {snippet}\n(Nguon: {source})"
                                result["action_success"] = True
                            else:
                                bot_response = "Hien chua co thong tin phu hop trong co so tri thuc. Ban mo ta cu the hon duoc khong?"
                                result["action_success"] = None
                        else:
                            bot_response = "He thong tim kiem tam thoi khong kha dung. Ban mo ta cu the hon duoc khong?"
                            result["action_success"] = None
                except Exception:
                    bot_response = "He thong tim kiem tam thoi khong kha dung. Ban mo ta cu the hon duoc khong?"
                    result["action_success"] = None
            else:
                bot_response = "Ban co the cho toi biet cu the hon ve thong tin ban can tim hieu duoc khong?"
                result["action_success"] = None  # Need clarification
            result["response"] = bot_response
            return result

        elif intent == "tam_biet":
            if intent_confidence >= confidence_threshold:
                bot_response = "Cam on ban da lien he. Chuc ban mot ngay tot lanh!"
                result["action_success"] = True  # Clean exit
            else:
                bot_response = "Ban muon ket thuc cuoc goi phai khong a? Cam on ban da lien he."
                result["action_success"] = None  # Confirming intent
            result["response"] = bot_response
            result["action"] = "hangup"
            return result
        
        elif intent == "cam_on":
            # Loi cam on
            if intent_confidence >= confidence_threshold:
                bot_response = "Rat vui duoc ho tro ban. Ban con can gi them khong?"
                result["action_success"] = True
            else:
                bot_response = "Khong co gi. Toi co the ho tro gi them cho ban?"
                result["action_success"] = True  # Polite, still positive
            result["response"] = bot_response
            return result

        elif intent == "xac_nhan":
            # Xac nhan hanh dong truoc do
            if intent_confidence >= confidence_threshold:
                bot_response = "Da xac nhan. Toi se tiep tuc buoc tiep theo."
                result["action_success"] = True  # Confirmation successful
            else:
                bot_response = "Ban vui long xac nhan lai nhe."
                result["action_success"] = None
            result["response"] = bot_response
            result["action"] = "confirm"
            return result

        elif intent == "tu_choi":
            # Tu choi - dung buoc hoac de xuat lua chon khac
            if intent_confidence >= confidence_threshold:
                bot_response = "Toi da ghi nhan yeu cau tu choi cua ban. Ban co muon thuc hien yeu cau khac khong?"
                result["action_success"] = True  # Rejection acknowledged
            else:
                bot_response = "Ban co muon tu choi khong? Neu khong, toi se tiep tuc ho tro."
                result["action_success"] = None
            result["response"] = bot_response
            result["action"] = "reject"
            return result

        elif intent == "hoi_gio_lam_viec":
            # Cung cap gio lam viec (gia tri mac dinh)
            hours = "Tu 08:00 den 17:00 (Thu 2 - Thu 6), 08:00 - 12:00 (Thu 7)"
            bot_response = f"Gio lam viec cua chung toi: {hours}. Ban can ho tro gi them khong?"
            result["response"] = bot_response
            result["action_success"] = True  # Info provided
            return result

        elif intent == "hoi_dia_chi":
            # Cung cap dia chi (gia tri mac dinh)
            address = "123 Duong ABC, Quan 1, TP.HCM"
            bot_response = f"Dia chi cua chung toi: {address}. Ban muon chi duong chi tiet khong?"
            result["response"] = bot_response
            result["action_success"] = True  # Info provided
            return result

        elif intent == "khieu_nai":
            # Khuyen nghi chuyen sang nhan vien
            bot_response = "Toi xin loi ve bat tien nay. Toi se chuyen ban den nhan vien ho tro de giai quyet som nhat."
            result["response"] = bot_response
            result["action"] = "transfer"
            result["action_success"] = False  # Complaint = issue occurred
            return result

        elif intent == "yeu_cau_ho_tro":
            # Yeu cau ho tro chung
            if intent_confidence >= confidence_threshold:
                bot_response = "Vui long mo ta cu the van de ban gap phai de toi ho tro tot hon."
                result["action_success"] = None  # Gathering info
            else:
                bot_response = "Ban vui long cho biet ban can ho tro ve van de gi?"
                result["action_success"] = None
            result["response"] = bot_response
            return result
        
        else: # intent == "unknown" hoặc confidence thấp
            if "unknown" in intent:
                bot_response = "Xin loi, toi chua hieu ro y cua ban. Ban co the noi ro hon duoc khong?"
                result["action_success"] = False  # Failed to understand
            else:
                bot_response = f"Toi khong chac chan lam ve yeu cau cua ban. Ban co the giai thich them duoc khong?"
                result["action_success"] = None  # Uncertainty
            result["response"] = bot_response
            return result