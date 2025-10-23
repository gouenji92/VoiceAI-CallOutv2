import httpx
from typing import Dict, Any, Optional

# Địa chỉ của Deeppavlov Agent (chạy ở Hạng mục 3)
AGENT_URL = "http://localhost:4242" 

client = httpx.AsyncClient(base_url=AGENT_URL, timeout=10.0)
print("Dialog Manager (HTTP Client) da san sang goi Agent...")

async def get_bot_response(call_id: str, workflow_json: Dict, nlp_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gửi state (NLP data) và workflow (logic) đến Deeppavlov Agent.
    """
    
    # Tạo payload (dữ liệu gửi đi)
    # Agent sẽ nhận được `workflow_json` và `nlp_data` trong `state`
    payload = {
        "user_id": call_id, # Dùng call_id làm user_id cho Agent
        "payload": {
            "workflow_json": workflow_json,
            "nlp_data": nlp_data
        }
    }
    
    try:
        response = await client.post("/", json=payload)
        response.raise_for_status() # Báo lỗi nếu API trả về 4xx, 5xx
        
        agent_data = response.json()
        
        # Trích xuất câu trả lời và hành động
        bot_response_text = agent_data.get("response", "Loi: Agent khong tra loi.")
        action = agent_data.get("action", None) # vd: "hangup", "transfer"
        
        return {
            "bot_response_text": bot_response_text,
            "action": action
        }
        
    except httpx.ConnectError as e:
        print(f"LOI KET NOI: Khong the ket noi den Agent tai {AGENT_URL}.")
        print("Ban da chay 'python agent/run_agent.py' CHUA?")
        return {
            "bot_response_text": "Loi he thong: Khong the ket noi Agent.",
            "action": "hangup"
        }
    except Exception as e:
        print(f"Loi khi goi Agent: {e}")
        return {
            "bot_response_text": f"Loi he thong: {e}",
            "action": "hangup"
        }