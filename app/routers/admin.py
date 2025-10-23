from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from redis import Redis
from rq import Queue
from rq.job import Job
from app.dependencies import get_current_user_id

router = APIRouter()
redis_conn = Redis(host='localhost', port=6379, db=0)
q = Queue('model_tasks', connection=redis_conn)

@router.get("/jobs/status")
async def get_jobs_status(current_user_id: str = Depends(get_current_user_id)):
    """
    Lấy trạng thái của tất cả các công việc huấn luyện trong hàng đợi
    """
    try:
        # Lấy danh sách job
        jobs = q.jobs
        
        job_list = []
        for job in jobs:
            job_info = {
                "id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "exc_info": job.exc_info if job.exc_info else None
            }
            job_list.append(job_info)
            
        return {
            "total_jobs": len(job_list),
            "jobs": job_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, current_user_id: str = Depends(get_current_user_id)):
    """
    Lấy thông tin chi tiết về một công việc cụ thể
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        return {
            "id": job.id,
            "status": job.get_status(),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "result": job.result,
            "exc_info": job.exc_info if job.exc_info else None
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy công việc với ID {job_id}")

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str, current_user_id: str = Depends(get_current_user_id)):
    """
    Hủy một công việc đang chờ trong hàng đợi
    """
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        
        if job.is_finished:
            raise HTTPException(status_code=400, detail="Công việc đã hoàn thành")
            
        job.cancel()
        return {"message": f"Đã hủy công việc {job_id}"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy công việc với ID {job_id}")