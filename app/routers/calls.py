from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.database import supabase
from app.models import CallStartRequest, CallStartResponse, WebhookInput, WebhookResponse
from app.services import asterisk_service, nlp_service, dialog_manager
import uuid

router = APIRouter()

@router.post("/start_call", response_model=CallStartResponse)
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
    
    try:
        db_response = supabase.table("calls").insert(call_record).execute()
        
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo cuộc gọi: {str(e)}")

@router.post("/webhook", response_model=WebhookResponse)
async def handle_voice_webhook(
    request: WebhookInput,
    background_tasks: BackgroundTasks
):
    try:
        call_id = request.call_id
        user_text = request.speech_to_text
        
        print(f"[Webhook] Nhan input tu call {call_id}: {user_text}")
        
        # 1. Lấy thông tin cuộc gọi VÀ workflow VÀ phiên bản active
        try:
            # Fix: Chỉ định rõ CẢNH 2 relationships để tránh "more than one relationship" error
            call_res = supabase.table("calls").select(
                "*, workflows!calls_workflow_id_fkey(*, workflow_versions!workflow_versions_workflow_id_fkey(*))"
            ).eq("id", call_id).single().execute()
            
            if not call_res.data:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Khong tim thay thong tin cuoc goi: {call_id}"
                )
            
            call_data = call_res.data
            workflow_data = call_data.get('workflows')
            if not workflow_data:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Khong tim thay workflow cho cuoc goi: {call_id}"
                )
                
            # workflow_versions trả về array, lấy phần tử đầu tiên
            versions = workflow_data.get('workflow_versions', [])
            if not versions or not isinstance(versions, list) or len(versions) == 0:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Khong tim thay workflow_versions cho cuoc goi: {call_id}"
                )
            
            active_version = versions[0]  # Lấy version đầu tiên (newest)
            if not active_version.get('workflow_json'):
                raise HTTPException(
                    status_code=404, 
                    detail=f"Khong tim thay workflow_json cho cuoc goi: {call_id}"
                )
        except HTTPException as he:
            raise he
        except Exception as e:
            print(f"[Webhook] Loi khi truy van DB: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Loi he thong khi truy van thong tin cuoc goi"
            )

        # 2. Xử lý NLP (async wrapper để không block event loop)
        try:
            nlp_data = await nlp_service.process_nlp_tasks_async(user_text, call_id=call_id)
            print(f"[Webhook] Ket qua NLP: {nlp_data}")
        except Exception as e:
            print(f"[Webhook] Loi khi xu ly NLP: {str(e)}")
            nlp_data = {
                "text": user_text,
                "intent": "unknown",
                "intent_confidence": 0.0,
                "sentiment": "neutral",
                "entities": {}
            }
        
        # 3. Gọi Agent để lấy phản hồi
        try:
            agent_response = await dialog_manager.get_bot_response(
                call_id=call_id,
                workflow_json=active_version.get('workflow_json'),
                nlp_data=nlp_data
            )
        except Exception as e:
            print(f"[Webhook] Loi khi goi Agent: {str(e)}")
            return {
                "bot_response_text": "Xin loi, he thong dang gap su co. Vui long thu lai sau.",
                "action": "hangup"
            }
        
        # 4. Lưu log hội thoại (bot) — user log đã được lưu bởi nlp_service nếu call_id có truyền
        try:
            background_tasks.add_task(
                supabase.table("conversation_logs").insert,
                {
                    "call_id": call_id,
                    "speaker": "bot",
                    "text": agent_response.get("bot_response_text")
                }
            )
        except Exception as e:
            print(f"[Webhook] Loi khi luu log: {str(e)}")
            # Không raise exception vì đây là background task
        
        # 5. Trả về phản hồi cho Voice Gateway
        return agent_response
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"[Webhook] Loi khong mong muon: {str(e)}")
        return {
            "bot_response_text": "Xin loi, he thong dang gap su co. Vui long thu lai sau.",
            "action": "hangup"
        }