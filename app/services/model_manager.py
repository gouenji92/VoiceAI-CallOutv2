import threading
import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class ModelManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelManager, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._model = None
            self._tokenizer = None
            self._model_path = os.path.abspath('./models/phobert-intent-classifier')
            self._model_lock = threading.Lock()
            self._version = 0
            # Lưu trữ phiên bản trước để rollback
            self._previous_model = None
            self._previous_tokenizer = None
            self._previous_path = None
            self._initialized = True
            self.load_model()
    
    def load_model(self, path: Optional[str] = None) -> Tuple[AutoModelForSequenceClassification, AutoTokenizer]:
        """
        Tải mô hình và tokenizer một cách an toàn với thread
        """
        try:
            p = path or self._model_path
            if not os.path.exists(p):
                raise FileNotFoundError(f"Không tìm thấy mô hình tại {p}")
            
            with self._model_lock:
                # Tải tokenizer và mô hình
                tokenizer = AutoTokenizer.from_pretrained(p)
                model = AutoModelForSequenceClassification.from_pretrained(p)
                
                # Chuyển mô hình sang GPU nếu có
                if torch.cuda.is_available():
                    model = model.cuda()
                model.eval()
                
                # Cập nhật state
                self._tokenizer = tokenizer
                self._model = model
                self._model_path = p
                self._version += 1
                
                logger.info(f"Đã tải mô hình thành công (version {self._version})")
                return model, tokenizer
                
        except Exception as e:
            logger.error(f"Lỗi khi tải mô hình: {str(e)}")
            raise
    
    def get_model(self) -> Tuple[Optional[AutoModelForSequenceClassification], Optional[AutoTokenizer]]:
        """
        Lấy mô hình và tokenizer hiện tại một cách an toàn với thread
        """
        with self._model_lock:
            if self._model is None or self._tokenizer is None:
                try:
                    return self.load_model()
                except Exception as e:
                    logger.error(f"Lỗi khi tải mô hình: {str(e)}")
                    return None, None
            return self._model, self._tokenizer
    
    def reload_model(self, path: Optional[str] = None) -> bool:
        """
        Tải lại mô hình một cách an toàn với thread và khả năng rollback
        """
        try:
            with self._model_lock:
                # Lưu trạng thái hiện tại để rollback
                self._previous_model = self._model
                self._previous_tokenizer = self._tokenizer
                self._previous_path = self._model_path
                
                # Thử tải mô hình mới
                self.load_model(path)
                return True
                
        except Exception as e:
            logger.error(f"Lỗi khi tải lại mô hình: {str(e)}")
            # Thử rollback về phiên bản trước
            if self._previous_model is not None:
                logger.info("Đang rollback về phiên bản trước...")
                try:
                    with self._model_lock:
                        self._model = self._previous_model
                        self._tokenizer = self._previous_tokenizer
                        self._model_path = self._previous_path
                        self._version -= 1
                    logger.info("Rollback thành công")
                    return True
                except Exception as rollback_error:
                    logger.error(f"Lỗi khi rollback: {str(rollback_error)}")
            return False
    
    def get_version(self) -> int:
        """
        Lấy version hiện tại của mô hình
        """
        return self._version

# Singleton instance
_manager = ModelManager()

# Module level functions for backwards compatibility
def load_model(path: Optional[str] = None):
    return _manager.load_model(path)

def get_model():
    return _manager.get_model()

def reload_model(path: Optional[str] = None):
    return _manager.reload_model(path)
