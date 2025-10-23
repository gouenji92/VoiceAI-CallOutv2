from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ConversationLog(BaseModel):
    """Model cho bảng conversation_logs"""
    call_id: str
    speaker: str
    text: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime = None

    class Config:
        from_attributes = True

class FeedbackEntry(BaseModel):
    """Model cho bảng feedback"""
    call_id: str
    text: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    reviewed: bool = False
    created_at: datetime = None

    class Config:
        from_attributes = True

class CallIntent(BaseModel):
    """Model cho bảng call_intents"""
    call_id: str
    intent_name: str
    count: int = 1
    accuracy: Optional[float] = None

    class Config:
        from_attributes = True