"""
Centralized logging configuration
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Tạo thư mục logs nếu chưa có
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Format cho log
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Tạo logger với cấu hình đầy đủ
    
    Args:
        name: Tên của logger (thường là __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Tránh duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler - lưu tất cả logs
    log_file = LOG_DIR / f"voiceai_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log tất cả vào file
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Error file handler - chỉ lưu errors
    error_file = LOG_DIR / f"voiceai_error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)
    
    return logger


# Pre-configured loggers cho các services
api_logger = setup_logger("api")
nlp_logger = setup_logger("nlp")
dialog_logger = setup_logger("dialog")
asterisk_logger = setup_logger("asterisk")
db_logger = setup_logger("database")
