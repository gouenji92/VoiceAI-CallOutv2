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
from app.services.rl_threshold_tuner import get_tuner

router = APIRouter()

FEEDBACK_CSV = Path('data/feedback.csv')
FEEDBACK_CSV.parent.mkdir(parents=True, exist_ok=True)

class FeedbackIn(BaseModel):
    session_id: str
    text: str
    label: str | None = None
    corrected: bool = False

class RewardFeedback(BaseModel):
    """Feedback for RL threshold tuning"""
    call_id: str
    reward: float  # +1 (success), 0 (neutral), -1 (fail)
    final_intent: str | None = None  # If user corrected the intent
    notes: str | None = None


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


@router.post('/rl-reward', status_code=status.HTTP_200_OK)
async def submit_rl_reward(feedback: RewardFeedback):
    """
    Submit reward feedback for RL threshold tuning.
    
    Reward signals:
    - +1.0: User confirmed/proceeded successfully (intent correct)
    - 0.0: Required clarification (uncertain)
    - -1.0: User rejected/escalated (intent wrong or low quality)
    """
    try:
        tuner = get_tuner()
        tuner.update_from_feedback(
            call_id=feedback.call_id,
            reward=feedback.reward,
            final_intent=feedback.final_intent
        )
        
        # Also log to database for analytics
        log_data = {
            'call_id': feedback.call_id,
            'reward': feedback.reward,
            'final_intent': feedback.final_intent,
            'notes': feedback.notes
        }
        
        try:
            supabase.table('rl_feedback').insert(log_data).execute()
        except Exception as db_err:
            print(f"[Feedback] Failed to log to DB: {db_err}")
        
        return {
            'ok': True,
            'message': f'Reward {feedback.reward:+.1f} recorded for call {feedback.call_id}',
            'current_epsilon': tuner.epsilon
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'RL update failed: {str(e)}')


@router.get('/rl-stats')
async def get_rl_stats(current_user_id: str = Depends(get_current_user_id)):
    """Get current RL tuner statistics and best thresholds"""
    try:
        tuner = get_tuner()
        stats = tuner.get_stats()
        best_thresholds = tuner.get_best_thresholds()
        
        return {
            'ok': True,
            'stats': stats,
            'best_thresholds': best_thresholds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
