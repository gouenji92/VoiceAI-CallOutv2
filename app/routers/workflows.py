from fastapi import APIRouter, Depends, HTTPException, status
from app.database import supabase
from app.models import (
    Workflow, WorkflowCreate, WorkflowWithCurrentVersion, 
    WorkflowVersionCreate, WorkflowVersion, WorkflowRollback
)
from app.dependencies import get_current_user_id
import uuid
from typing import List

router = APIRouter()

@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user_id: str = Depends(get_current_user_id) 
):
    workflow_dict = workflow.dict()
    workflow_dict['user_id'] = current_user_id
    try:
        response = supabase.table("workflows").insert(workflow_dict).execute()
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tạo workflow: {str(e)}")

@router.get("/", response_model=List[Workflow])
async def get_user_workflows(
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        response = supabase.table("workflows").select("*").eq("user_id", current_user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy workflows: {str(e)}")

@router.get("/{workflow_id}", response_model=WorkflowWithCurrentVersion)
async def get_workflow_with_current_version(
    workflow_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        wf_res = supabase.table("workflows").select("*").eq("id", workflow_id).eq("user_id", current_user_id).single().execute()
        if not wf_res.data:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow_data = wf_res.data
        
        if workflow_data.get("current_version_id"):
            ver_res = supabase.table("workflow_versions").select("*").eq("id", workflow_data["current_version_id"]).single().execute()
            if ver_res.data:
                workflow_data["workflow_json"] = ver_res.data.get("workflow_json")
                workflow_data["current_version"] = ver_res.data
                
        return workflow_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy workflow: {str(e)}")

@router.put("/{workflow_id}", response_model=WorkflowVersion)
async def create_new_workflow_version(
    workflow_id: uuid.UUID,
    version_data: WorkflowVersionCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Lưu thay đổi = TẠO PHIÊN BẢN MỚI
    """
    try:
        new_version_dict = {
            "workflow_id": str(workflow_id),
            "user_id": current_user_id,
            "workflow_json": version_data.workflow_json,
            "change_description": version_data.change_description
        }
        print(f"[DEBUG] Tạo version cho workflow {workflow_id}: {new_version_dict}")
        ver_res = supabase.table("workflow_versions").insert(new_version_dict).execute()
        print(f"[DEBUG] Supabase response: {ver_res}")
        
        if not ver_res.data:
            raise HTTPException(status_code=500, detail="Không thể tạo version")
            
        new_version = ver_res.data[0]
        new_version_id = new_version["id"]
        
        update_res = supabase.table("workflows").update({
            "current_version_id": new_version_id
        }).eq("id", workflow_id).execute()
        
        if not update_res.data:
            supabase.table("workflow_versions").delete().eq("id", new_version_id).execute()
            raise HTTPException(status_code=500, detail="Không thể cập nhật workflow pointer")

        return new_version
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Lỗi tạo version: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi tạo version: {str(e)}")

@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersion])
async def get_workflow_version_history(
    workflow_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        response = supabase.table("workflow_versions") \
            .select("id, workflow_id, user_id, change_description, created_at") \
            .eq("workflow_id", workflow_id) \
            .order("created_at", desc=True) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy versions: {str(e)}")

@router.post("/{workflow_id}/rollback", response_model=Workflow)
async def rollback_to_version(
    workflow_id: uuid.UUID,
    rollback_data: WorkflowRollback,
    current_user_id: str = Depends(get_current_user_id)
):
    try:
        version_id_to_rollback = str(rollback_data.version_id)
        
        ver_res = supabase.table("workflow_versions").select("id").eq("id", version_id_to_rollback).eq("workflow_id", workflow_id).single().execute()
        if not ver_res.data:
            raise HTTPException(status_code=404, detail="Version not found or does not belong to this workflow")

        update_res = supabase.table("workflows").update({
            "current_version_id": version_id_to_rollback
        }).eq("id", workflow_id).eq("user_id", current_user_id).execute()
        
        if not update_res.data:
            raise HTTPException(status_code=500, detail="Không thể rollback")
            
        return update_res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi rollback: {str(e)}")