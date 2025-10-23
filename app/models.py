from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
import uuid

# --- Auth Models ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    account_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"

# --- Workflow Models (ĐÃ CẬP NHẬT VERSIONING) ---

# Model cơ bản (trả về khi GET list)
class Workflow(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    current_version_id: Optional[uuid.UUID] = None
    created_at: Any
    
    class Config:
        from_attributes = True

# Model dùng khi TẠO "Dự án" (cái hộp)
class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None

# Model dùng khi "LƯU" (tạo phiên bản mới)
class WorkflowVersionCreate(BaseModel):
    workflow_json: dict
    change_description: str # "Commit message"

# Model để hiển thị 1 phiên bản (trong lịch sử)
class WorkflowVersion(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    user_id: Optional[uuid.UUID]
    change_description: Optional[str]
    created_at: Any
    
    class Config:
        from_attributes = True

# Model để hiển thị Workflow (bao gồm cả JSON của phiên bản hiện tại)
class WorkflowWithCurrentVersion(Workflow):
    current_version: Optional[WorkflowVersion] = None
    workflow_json: Optional[dict] = None # JSON của phiên bản hiện tại

# Model cho Rollback
class WorkflowRollback(BaseModel):
    version_id: uuid.UUID

# --- Call Models ---
class CallStartRequest(BaseModel):
    workflow_id: uuid.UUID
    customer_phone: str

class CallStartResponse(BaseModel):
    call_id: uuid.UUID
    status: str
    message: str

class WebhookInput(BaseModel):
    call_id: str
    speech_to_text: str

class WebhookResponse(BaseModel):
    bot_response_text: str
    action: Optional[str] = None # vd: "hangup", "transfer"