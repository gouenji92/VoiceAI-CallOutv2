from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.database import supabase
from app.dependencies import get_current_user_id
from pathlib import Path
import csv
import subprocess
import os
from fastapi import BackgroundTasks
from app.services import nlp_service

router = APIRouter()

FEEDBACK_CSV = Path('data/feedback.csv')
FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)

class FeedbackIn(BaseModel):
    session_id: str
    text: str
    label: str | None = None
    corrected: bool = False


@router.post('/', status_code=status.HTTP_201_CREATED)
async def submit_feedback(feedback: FeedbackIn, current_user_id: str = Depends(get_current_user_id)):
    # Save to Supabase table 'feedback' (if exists)
    fb = feedback.dict()
    fb['user_id'] = current_user_id
    try:
        res = supabase.table('feedback').insert(fb).execute()
    except Exception:
        res = None

    # Always append to local CSV as backup
    with FEEDBACK_CSV.open('a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([feedback.session_id, feedback.text, feedback.label or '', str(feedback.corrected)])

    return {'ok': True, 'saved_to_supabase': (res is not None and not getattr(res,'error',None))}


@router.post('/retrain')
async def trigger_retrain(current_user_id: str = Depends(get_current_user_id)):
    """Kích hoạt huấn luyện lại mô hình qua hệ thống hàng đợi."""
    from app.workers.model_worker import enqueue_retrain_job
    
    try:
        # Đưa công việc vào hàng đợi
        job_id = enqueue_retrain_job(
            feedback_data_path=str(FEEDBACK_CSV),
            base_model_path="models/phobert-intent-classifier"
        )
        
        if job_id:
            return {'ok': True, 'message': 'Đã thêm công việc huấn luyện vào hàng đợi', 'job_id': job_id}
        else:
            raise HTTPException(status_code=500, detail='Không thể tạo công việc huấn luyện')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/reload')
async def reload_model_endpoint(current_user_id: str = Depends(get_current_user_id)):
    """Trigger the running process to reload the intent model from disk."""
    ok = nlp_service.reload_intent_model()
    if not ok:
        raise HTTPException(status_code=500, detail='Failed to reload model')
    return {'ok': True, 'message': 'model reloaded in memory'}
