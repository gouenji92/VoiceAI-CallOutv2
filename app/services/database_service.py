from typing import Optional, List, Dict, Any
from datetime import datetime
from app.database import supabase
from app.models.database import ConversationLog, FeedbackEntry, CallIntent

class DatabaseService:
    @staticmethod
    async def save_conversation_log(log: ConversationLog) -> bool:
        """Lưu log hội thoại với validation"""
        try:
            if log.created_at is None:
                log.created_at = datetime.now()
                
            response = supabase.table('conversation_logs').insert(log.model_dump()).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"[DB Service] Lỗi khi lưu conversation log: {response.error}")
                return False
                
            return True
            
        except Exception as e:
            print(f"[DB Service] Exception khi lưu conversation log: {str(e)}")
            return False
    
    @staticmethod
    async def save_feedback(feedback: FeedbackEntry) -> bool:
        """Lưu feedback với validation"""
        try:
            if feedback.created_at is None:
                feedback.created_at = datetime.now()
                
            response = supabase.table('feedback').insert(feedback.model_dump()).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"[DB Service] Lỗi khi lưu feedback: {response.error}")
                return False
                
            return True
            
        except Exception as e:
            print(f"[DB Service] Exception khi lưu feedback: {str(e)}")
            return False

    @staticmethod
    async def get_pending_feedback() -> List[FeedbackEntry]:
        """Lấy danh sách feedback chưa review"""
        try:
            response = supabase.table('feedback').select('*').eq('reviewed', False).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"[DB Service] Lỗi khi lấy pending feedback: {response.error}")
                return []
                
            return [FeedbackEntry(**item) for item in response.data]
            
        except Exception as e:
            print(f"[DB Service] Exception khi lấy pending feedback: {str(e)}")
            return []

    @staticmethod
    async def update_feedback_status(feedback_ids: List[str], approved: bool) -> bool:
        """Cập nhật trạng thái của feedback"""
        try:
            response = supabase.table('feedback').update({
                'reviewed': True,
                'approved': approved
            }).in_('id', feedback_ids).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"[DB Service] Lỗi khi cập nhật feedback: {response.error}")
                return False
                
            return True
            
        except Exception as e:
            print(f"[DB Service] Exception khi cập nhật feedback: {str(e)}")
            return False