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

@router.post("/", response_model=Workflow, status_code=status.HTTP_201_CREATED, tags=["Workflows"])
async def create_workflow(
    workflow: WorkflowCreate,
    current_user_id: str = Depends(get_current_user_id) 
):
    workflow_dict = workflow.dict()
    workflow_dict['user_id'] = current_user_id
    response = supabase.table("workflows").insert(workflow_dict).execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return response.data[0]

@router.get("/", response_model=List[Workflow], tags=["Workflows"])
async def get_user_workflows(
    current_user_id: str = Depends(get_current_user_id)
):
    response = supabase.table("workflows").select("*").eq("user_id", current_user_id).execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return response.data

@router.get("/{workflow_id}", response_model=WorkflowWithCurrentVersion, tags=["Workflows"])
async def get_workflow_with_current_version(
    workflow_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    wf_res = supabase.table("workflows").select("*").eq("id", workflow_id).eq("user_id", current_user_id).single().execute()
    if wf_res.error or not wf_res.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow_data = wf_res.data
    
    if workflow_data.get("current_version_id"):
        ver_res = supabase.table("workflow_versions").select("*").eq("id", workflow_data["current_version_id"]).single().execute()
        if ver_res.data:
            workflow_data["workflow_json"] = ver_res.data.get("workflow_json")
            workflow_data["current_version"] = ver_res.data
            
    return workflow_data

@router.put("/{workflow_id}", response_model=WorkflowVersion, tags=["Workflows"])
async def create_new_workflow_version(
    workflow_id: uuid.UUID,
    version_data: WorkflowVersionCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Lưu thay đổi = TẠO PHIÊN BẢN MỚI
    """
    new_version_dict = {
        "workflow_id": str(workflow_id),
        "user_id": current_user_id,
        "workflow_json": version_data.workflow_json,
        "change_description": version_data.change_description
    }
    ver_res = supabase.table("workflow_versions").insert(new_version_dict).execute()
    if ver_res.error or not ver_res.data:
        raise HTTPException(status_code=500, detail=f"Could not create version: {ver_res.error.message}")
        
    new_version = ver_res.data[0]
    new_version_id = new_version["id"]
    
    update_res = supabase.table("workflows").update({
        "current_version_id": new_version_id
    }).eq("id", workflow_id).execute()
    
    if update_res.error:
        supabase.table("workflow_versions").delete().eq("id", new_version_id).execute()
        raise HTTPException(status_code=500, detail=f"Could not update workflow pointer: {update_res.error.message}")

    return new_version

@router.get("/{workflow_id}/versions", response_model=List[WorkflowVersion], tags=["Workflows"])
async def get_workflow_version_history(
    workflow_id: uuid.UUID,
    current_user_id: str = Depends(get_current_user_id)
):
    response = supabase.table("workflow_versions") \
        .select("id, workflow_id, user_id, change_description, created_at") \
        .eq("workflow_id", workflow_id) \
        .order("created_at", desc=True) \
        .execute()
    if response.error:
        raise HTTPException(status_code=400, detail=response.error.message)
    return response.data

@router.post("/{workflow_id}/rollback", response_model=Workflow, tags=["Workflows"])
async def rollback_to_version(
    workflow_id: uuid.UUID,
    rollback_data: WorkflowRollback,
    current_user_id: str = Depends(get_current_user_id)
):
    version_id_to_rollback = str(rollback_data.version_id)
    
    ver_res = supabase.table("workflow_versions").select("id").eq("id", version_id_to_rollback).eq("workflow_id", workflow_id).single().execute()
    if ver_res.error or not ver_res.data:
        raise HTTPException(status_code=404, detail="Version not found or does not belong to this workflow")

    update_res = supabase.table("workflows").update({
        "current_version_id": version_id_to_rollback
    }).eq("id", workflow_id).eq("user_id", current_user_id).execute()
    
    if update_res.error:
        raise HTTPException(status_code=500, detail=f"Could not rollback: {update_res.error.message}")
        
    return update_res.data[0]