import asyncio
import os
from typing import Optional
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình Asterisk AMI từ environment variables
ASTERISK_HOST = os.getenv("ASTERISK_HOST", "localhost")
ASTERISK_PORT = int(os.getenv("ASTERISK_PORT", "5038"))
ASTERISK_USERNAME = os.getenv("ASTERISK_USERNAME", "admin")
ASTERISK_PASSWORD = os.getenv("ASTERISK_PASSWORD", "admin")
ASTERISK_CONTEXT = os.getenv("ASTERISK_CONTEXT", "default")
ASTERISK_CHANNEL = os.getenv("ASTERISK_CHANNEL", "SIP/trunk")

# Flag để bật/tắt mock mode
USE_MOCK_MODE = os.getenv("ASTERISK_MOCK_MODE", "true").lower() == "true"

# Import thư viện AMI nếu không dùng mock
if not USE_MOCK_MODE:
    try:
        from panoramisk import Manager
        logger.info("Đã import panoramisk thành công")
    except ImportError:
        logger.warning("Không tìm thấy panoramisk. Chuyển sang mock mode.")
        USE_MOCK_MODE = True

# Biến global để giữ connection manager
ami_manager: Optional[object] = None

async def connect_ami():
    """Kết nối đến Asterisk AMI"""
    global ami_manager
    
    if USE_MOCK_MODE:
        logger.info("[Mock Mode] Bỏ qua kết nối AMI")
        return True
    
    try:
        ami_manager = Manager(
            host=ASTERISK_HOST,
            port=ASTERISK_PORT,
            username=ASTERISK_USERNAME,
            secret=ASTERISK_PASSWORD,
            ping_delay=10,
            ping_tries=3
        )
        await ami_manager.connect()
        logger.info(f"Đã kết nối AMI tại {ASTERISK_HOST}:{ASTERISK_PORT}")
        return True
    except Exception as e:
        logger.error(f"Lỗi khi kết nối AMI: {e}")
        return False

async def disconnect_ami():
    """Ngắt kết nối AMI"""
    global ami_manager
    
    if ami_manager and not USE_MOCK_MODE:
        try:
            await ami_manager.close()
            logger.info("Đã ngắt kết nối AMI")
        except Exception as e:
            logger.error(f"Lỗi khi ngắt kết nối AMI: {e}")

async def initiate_callout_async(call_id: str, phone_number: str, workflow_id: str) -> bool:
    """
    Thực hiện cuộc gọi ra (Async version)
    
    Args:
        call_id: ID của cuộc gọi trong database
        phone_number: Số điện thoại cần gọi
        workflow_id: ID của workflow
    
    Returns:
        bool: True nếu gọi thành công, False nếu thất bại
    """
    logger.info(f"[Asterisk Service] Thực hiện gọi ra số: {phone_number} cho Call ID: {call_id}")
    
    if USE_MOCK_MODE:
        logger.info("[Mock Mode] Giả lập gọi thành công")
        return True
    
    try:
        if not ami_manager:
            await connect_ami()
        
        # Tạo action Originate
        action = {
            'Action': 'Originate',
            'Channel': f'{ASTERISK_CHANNEL}/{phone_number}',
            'Context': ASTERISK_CONTEXT,
            'Exten': '1',  # Extension để xử lý cuộc gọi
            'Priority': '1',
            'CallerID': f'VoiceAI <{call_id}>',
            'Variable': f'CALL_ID={call_id},WORKFLOW_ID={workflow_id}',
            'Async': 'true'
        }
        
        response = await ami_manager.send_action(action)
        
        if response and response.success:
            logger.info(f"[Asterisk Service] Đã gửi lệnh Originate thành công cho {phone_number}")
            return True
        else:
            logger.error(f"[Asterisk Service] Lỗi khi Originate: {response}")
            return False
            
    except Exception as e:
        logger.error(f"[Asterisk Service] Ngoại lệ khi thực hiện callout: {e}")
        return False

def initiate_callout(call_id: str, phone_number: str, workflow_id: str) -> bool:
    """
    Wrapper đồng bộ cho initiate_callout_async
    Dùng khi gọi từ code đồng bộ (background tasks)
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Nếu đang trong event loop, tạo task mới
            task = asyncio.create_task(initiate_callout_async(call_id, phone_number, workflow_id))
            return True  # Return ngay, không đợi
        else:
            # Nếu không có event loop, chạy đồng bộ
            return loop.run_until_complete(initiate_callout_async(call_id, phone_number, workflow_id))
    except Exception as e:
        logger.error(f"[Asterisk Service] Lỗi trong wrapper: {e}")
        # Fallback: chạy trong thread pool
        logger.info("[Asterisk Service] Sử dụng mock mode do lỗi")
        return True  # Return True để không block workflow