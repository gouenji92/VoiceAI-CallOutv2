"""
Entity Extractor Service
Trích xuất các entities như thời gian, ngày tháng, số điện thoại từ text tiếng Việt
"""

import re
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EntityExtractor:
    """Class để trích xuất entities từ text tiếng Việt"""
    
    def __init__(self):
        # Patterns cho thời gian
        self.time_patterns = [
            r'(\d{1,2})\s*giờ\s*(\d{1,2})?\s*(phút)?',  # 9 giờ 30 phút
            r'(\d{1,2})[hH](\d{2})?',  # 9h30
            r'(\d{1,2})\s*:\s*(\d{2})',  # 9:30
            r'(sáng|chiều|tối|trưa)\s*(\d{1,2})\s*giờ',  # sáng 9 giờ
        ]
        
        # Patterns cho ngày tháng
        self.date_patterns = [
            r'ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})',  # ngày 15 tháng 10
            r'(\d{1,2})/(\d{1,2})/(\d{4})?',  # 15/10/2025
            r'(hôm nay|ngày mai|ngày kia)',  # relative dates
            r'(thứ\s*(hai|ba|tư|năm|sáu|bảy)|chủ nhật)\s*tuần\s*(này|sau)',
        ]
        
        # Patterns cho số điện thoại Việt Nam
        self.phone_patterns = [
            r'(0|\+84)\s*\d{9,10}',  # 0909123456 hoặc +84909123456
            r'(0|\+84)\s*\d{2,3}\s*\d{3}\s*\d{4}',  # 090 912 3456
        ]
        
        # Patterns cho email
        self.email_patterns = [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        ]
        
        # Từ điển chuyển đổi
        self.weekday_map = {
            'hai': 'Monday', 'ba': 'Tuesday', 'tư': 'Wednesday',
            'năm': 'Thursday', 'sáu': 'Friday', 'bảy': 'Saturday',
            'chủ nhật': 'Sunday'
        }
        
    def extract_time(self, text: str) -> List[Dict[str, Any]]:
        """Trích xuất thông tin thời gian"""
        times = []
        text_lower = text.lower()
        
        for pattern in self.time_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                groups = match.groups()
                
                # Parse giờ và phút
                if len(groups) >= 1:
                    hour = int(groups[0]) if groups[0] else None
                    minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                    
                    if hour is not None:
                        # Điều chỉnh cho sáng/chiều/tối
                        if 'chiều' in text_lower and hour < 12:
                            hour += 12
                        elif 'tối' in text_lower and hour < 12:
                            hour += 12
                        
                        times.append({
                            'type': 'time',
                            'hour': hour,
                            'minute': minute,
                            'formatted': f"{hour:02d}:{minute:02d}",
                            'original': match.group(0)
                        })
        
        return times
    
    def extract_date(self, text: str) -> List[Dict[str, Any]]:
        """Trích xuất thông tin ngày tháng"""
        dates = []
        text_lower = text.lower()
        
        # Xử lý relative dates
        if 'hôm nay' in text_lower:
            today = datetime.now()
            dates.append({
                'type': 'date',
                'date': today.strftime('%Y-%m-%d'),
                'relative': 'today',
                'original': 'hôm nay'
            })
        
        if 'ngày mai' in text_lower or 'mai' in text_lower:
            tomorrow = datetime.now() + timedelta(days=1)
            dates.append({
                'type': 'date',
                'date': tomorrow.strftime('%Y-%m-%d'),
                'relative': 'tomorrow',
                'original': 'ngày mai'
            })
        
        if 'ngày kia' in text_lower:
            day_after = datetime.now() + timedelta(days=2)
            dates.append({
                'type': 'date',
                'date': day_after.strftime('%Y-%m-%d'),
                'relative': 'day_after_tomorrow',
                'original': 'ngày kia'
            })
        
        # Xử lý ngày tháng cụ thể
        for pattern in self.date_patterns:
            if pattern == r'(hôm nay|ngày mai|ngày kia)':
                continue  # Đã xử lý ở trên
            
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 2 and groups[0].isdigit():
                    day = int(groups[0])
                    month = int(groups[1])
                    year = int(groups[2]) if len(groups) > 2 and groups[2] else datetime.now().year
                    
                    try:
                        date_obj = datetime(year, month, day)
                        dates.append({
                            'type': 'date',
                            'date': date_obj.strftime('%Y-%m-%d'),
                            'day': day,
                            'month': month,
                            'year': year,
                            'original': match.group(0)
                        })
                    except ValueError:
                        logger.warning(f"Invalid date: {day}/{month}/{year}")
        
        return dates
    
    def extract_phone(self, text: str) -> List[Dict[str, Any]]:
        """Trích xuất số điện thoại"""
        phones = []
        
        for pattern in self.phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                phone = re.sub(r'\s+', '', match.group(0))  # Loại bỏ khoảng trắng
                phones.append({
                    'type': 'phone',
                    'value': phone,
                    'original': match.group(0)
                })
        
        return phones
    
    def extract_email(self, text: str) -> List[Dict[str, Any]]:
        """Trích xuất email"""
        emails = []
        
        for pattern in self.email_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                emails.append({
                    'type': 'email',
                    'value': match.group(0),
                    'original': match.group(0)
                })
        
        return emails
    
    def extract_all(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Trích xuất tất cả entities"""
        entities = {
            'times': self.extract_time(text),
            'dates': self.extract_date(text),
            'phones': self.extract_phone(text),
            'emails': self.extract_email(text)
        }
        
        # Log kết quả
        logger.info(f"[Entity Extractor] Extracted from '{text}':")
        for entity_type, values in entities.items():
            if values:
                logger.info(f"  {entity_type}: {values}")
        
        return entities


# Singleton instance
_extractor = EntityExtractor()

def extract_entities(text: str) -> Dict[str, Any]:
    """
    Hàm tiện ích để trích xuất entities
    
    Args:
        text: Text cần trích xuất
    
    Returns:
        Dictionary chứa các entities đã trích xuất
    """
    return _extractor.extract_all(text)
