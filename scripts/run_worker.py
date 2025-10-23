import sys
import os
import time
from redis import Redis
from redis.exceptions import ConnectionError
from rq import Worker, Queue
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thêm thư mục gốc vào PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def connect_redis(max_retries=5, retry_delay=5):
    """Kết nối Redis với retry"""
    for attempt in range(max_retries):
        try:
            redis_conn = Redis(host='localhost', port=6379, db=0)
            redis_conn.ping()  # Kiểm tra kết nối
            return redis_conn
        except ConnectionError as e:
            if attempt == max_retries - 1:
                logger.error("Không thể kết nối tới Redis sau %d lần thử", max_retries)
                raise e
            logger.warning("Không thể kết nối tới Redis. Thử lại sau %d giây...", retry_delay)
            time.sleep(retry_delay)

if __name__ == '__main__':
    try:
        # Kết nối Redis với retry
        logger.info("Đang kết nối tới Redis...")
        redis_conn = connect_redis()
        
        # Tạo queue
        queue = Queue('model_tasks', connection=redis_conn)
        
        # Thiết lập worker
        worker = Worker([queue], connection=redis_conn)
        logger.info("Worker đang chạy và lắng nghe công việc...")
        worker.work()
    except Exception as e:
        logger.error("Lỗi: %s", str(e))
        logger.info("Hãy đảm bảo Redis container đang chạy bằng lệnh: docker-compose up -d")