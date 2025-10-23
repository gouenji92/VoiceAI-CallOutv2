"""
HTTP-based Deeppavlov Agent Server
Thay thế ZMQ channel bằng FastAPI để dễ tích hợp
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn

app = FastAPI(title="Deeppavlov Agent Server", version="1.0")

class AgentRequest(BaseModel):
    user_id: str
    state: Dict[str, Any]

class AgentResponse(BaseModel):
    response: str
    action: str = None

@app.post("/", response_model=AgentResponse)
async def process_dialog(request: AgentRequest):
    """
    Nhận state từ Dialog Manager, xử lý và trả về response
    """
    state = request.state
    workflow_json = state.get("workflow_json", {})
    nlp_data = state.get("nlp_data", {})
    
    user_input = nlp_data.get("text", "")
    intent = nlp_data.get("intent", "unknown")
    intent_confidence = nlp_data.get("intent_confidence", 0.0)
    sentiment = nlp_data.get("sentiment", "neutral")
    entities = nlp_data.get("entities", {})

    print(f"\n[Agent] Nhận request:")
    print(f"  - User: {request.user_id}")
    print(f"  - Text: {user_input}")
    print(f"  - Intent: {intent} (confidence: {intent_confidence:.2f})")
    print(f"  - Sentiment: {sentiment}")
    print(f"  - Entities: {entities}")

    # --- LOGIC ĐỊNH TUYẾN DỰA TRÊN INTENT ---
    confidence_threshold = 0.6

    # 1. Xử lý sentiment tiêu cực
    if sentiment == "negative":
        return AgentResponse(
            response="Tôi xin lỗi nếu có trải nghiệm không tốt. Bạn có muốn kết nối với nhân viên không?",
            action="transfer"
        )

    # 2. Xử lý các intent chính
    if intent == "dat_lich":
        if intent_confidence >= confidence_threshold:
            if "time" in entities and entities["time"]:
                time_val = entities["time"]
                return AgentResponse(
                    response=f"Vâng, tôi sẽ giúp bạn đặt lịch vào lúc {time_val}. Bạn xác nhận nhé?"
                )
            else:
                return AgentResponse(
                    response="Vâng. Bạn muốn đặt lịch vào thời gian nào ạ?"
                )
        else:
            return AgentResponse(
                response="Tôi hiểu bạn muốn đặt lịch. Bạn có thể cho tôi biết cụ thể thời gian được không?"
            )

    elif intent == "hoi_thong_tin":
        print("[Agent] Đang xử lý truy vấn thông tin...")
        if intent_confidence >= confidence_threshold:
            return AgentResponse(
                response=f"Tôi đã tìm thấy thông tin liên quan đến: {user_input}. Bạn cần biết thêm gì không?"
            )
        else:
            return AgentResponse(
                response="Bạn có thể cho tôi biết cụ thể hơn về thông tin bạn cần tìm hiểu được không?"
            )

    elif intent == "tam_biet" or intent == "ket_thuc":
        if intent_confidence >= confidence_threshold:
            return AgentResponse(
                response="Cảm ơn bạn đã liên hệ. Chúc bạn một ngày tốt lành!",
                action="hangup"
            )
        else:
            return AgentResponse(
                response="Bạn muốn kết thúc cuộc gọi phải không ạ? Cảm ơn bạn đã liên hệ.",
                action="hangup"
            )
    
    elif intent == "chao_hoi":
        return AgentResponse(
            response="Xin chào! Tôi là trợ lý ảo. Tôi có thể giúp gì cho bạn hôm nay?"
        )

    # 3. Intent không xác định hoặc confidence thấp
    else:
        if intent_confidence < confidence_threshold:
            return AgentResponse(
                response="Tôi không chắc chắn lắm về yêu cầu của bạn. Bạn có thể giải thích thêm được không?"
            )
        else:
            return AgentResponse(
                response="Xin lỗi, tôi chưa hiểu rõ ý của bạn. Bạn có thể nói rõ hơn được không?"
            )

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Agent server is running"}

if __name__ == "__main__":
    print("=" * 60)
    print("  🤖 DEEPPAVLOV AGENT SERVER (HTTP)")
    print("  Running on: http://localhost:4242")
    print("  Press CTRL+C to stop")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=4242, log_level="info")
