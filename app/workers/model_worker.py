from rq import Queue
from redis import Redis
from pathlib import Path
import logging
from ..services.model_manager import ModelManager
from ..services.nlp_service import NLPService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kết nối Redis
redis_conn = Redis(host='localhost', port=6379, db=0)
q = Queue('model_tasks', connection=redis_conn)

def retrain_model(feedback_data_path: str, base_model_path: str):
    """
    Hàm huấn luyện lại mô hình với dữ liệu feedback mới
    
    Note: This is a placeholder for incremental retraining.
    For now, use manual_train.py for model retraining with feedback data.
    Future implementation should integrate with the feedback loop.
    """
    try:
        logger.info(f"Bắt đầu huấn luyện lại mô hình với dữ liệu từ {feedback_data_path}")
        
        # Implementation plan:
        # 1. Load feedback data from CSV
        # 2. Merge with existing training data
        # 3. Run fine-tuning with manual_train.py logic
        # 4. Save new model checkpoint
        # 5. Reload model in NLPService
        
        logger.warning("Retraining logic not yet implemented. Use manual_train.py instead.")
        
        return False
    except Exception as e:
        logger.error(f"Lỗi trong quá trình huấn luyện lại: {str(e)}")
        return False

def enqueue_retrain_job(feedback_data_path: str, base_model_path: str):
    """
    Đưa công việc huấn luyện vào hàng đợi
    """
    try:
        job = q.enqueue(
            retrain_model,
            args=(feedback_data_path, base_model_path),
            job_timeout='1h'  # Giới hạn thời gian chạy tối đa
        )
        logger.info(f"Đã thêm công việc huấn luyện vào hàng đợi. Job ID: {job.id}")
        return job.id
    except Exception as e:
        logger.error(f"Lỗi khi thêm công việc vào hàng đợi: {str(e)}")
        return None