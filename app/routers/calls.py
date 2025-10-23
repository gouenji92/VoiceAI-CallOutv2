from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.database import supabase
from app.models import CallStartRequest, CallStartResponse, WebhookInput, WebhookResponse
from app.services import asterisk_service, nlp_service, dialog_manager
import uuid

router = APIRouter()

@router.post("/start_call", response_model=CallStartResponse, tags=["Calls"])
async def start_call(
    request: CallStartRequest,
    background_tasks: BackgroundTasks
):
    new_call_id = str(uuid.uuid4())
    call_record = {
        "id": new_call_id,
        "workflow_id": str(request.workflow_id),
        "customer_phone": request.customer_phone,
        "status": "pending"
    }
    db_response = supabase.table("calls").insert(call_record).execute()
    
    if db_response.error:
        raise HTTPException(status_code=500, detail=f"DB Error: {db_response.error.message}")

    background_tasks.add_task(
        asterisk_service.initiate_callout,
        call_id=new_call_id,
        phone_number=request.customer_phone,
        workflow_id=str(request.workflow_id)
    )
    
    return {
        "call_id": new_call_id,
        "status": "pending",
        "message": "Call initiated successfully."
    }

@router.post("/webhook", response_model=WebhookResponse, tags=["Calls"])
async def handle_voice_webhook(
    request: WebhookInput,
    background_tasks: BackgroundTasks
):
    call_id = request.call_id
    user_text = request.speech_to_text
    
    # 1. Lấy thông tin cuộc gọi VÀ workflow VÀ phiên bản active
    call_res = supabase.table("calls").select(
        "*, workflows(*, workflow_versions(*))" # Join 3 bảng
    ).eq("id", call_id).single().execute()
    
    if call_res.error or not call_res.data:
        raise HTTPException(status_code=404, detail="Call ID not found")
    
    call_data = call_res.data
    workflow_data = call_data.get('workflows')
    if not workflow_data:
         raise HTTPException(status_code=404, detail="Workflow for this call not found")
         
    active_version = workflow_data.get('workflow_versions')
    if not active_version or not active_version.get('workflow_json'):
        raise HTTPException(status_code=404, detail="This workflow has no active version (workflow_json)")

    # 2. (AI) Tích hợp Phobert/Sentiment (Hạng mục 3)
    nlp_data = nlp_service.process_nlp_tasks(user_text)
    
    # 3. (AI) Tích hợp Deeppavlov (Hạng mục 3)
    # Gửi (workflow_json, intent, entities...) đến Agent
    agent_response = await dialog_manager.get_bot_response(
        call_id=call_id,
        workflow_json=active_version.get('workflow_json'),
        nlp_data=nlp_data
    )
    
    # 4. Lưu log hội thoại vào DB (chạy nền)
    background_tasks.add_task(
        supabase.table("conversation_logs").insert,
        {
            "call_id": call_id,
            "speaker": "user",
            "text": user_text,
            "intent": nlp_data.get("intent"),
            "confidence": nlp_data.get("intent_confidence")
        }
    )
    background_tasks.add_task(
        supabase.table("conversation_logs").insert,
        {
            "call_id": call_id,
            "speaker": "bot",
            "text": agent_response.get("bot_response_text")
        }
    )
    
    # 5. Trả về text cho Voice Gateway (Asterisk)
    return agent_response