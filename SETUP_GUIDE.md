# VoiceAI CallOut v2 - Setup & Deployment Guide

## 📋 Tổng quan các thay đổi

### ✅ Đã khắc phục và cải thiện:

1. **Sửa lỗi trong dialog_manager.py**
   - Loại bỏ lỗi sử dụng biến `response_text` trước khi định nghĩa
   - Code flow hiện đã chính xác

2. **Asterisk AMI Integration hoàn chỉnh**
   - File: `app/services/asterisk_service.py`
   - Tích hợp thư viện `panoramisk` cho kết nối AMI thực tế
   - Hỗ trợ mock mode để test mà không cần Asterisk
   - Async support đầy đủ
   - Configuration qua environment variables

3. **Entity Recognition nâng cao**
   - File: `app/services/entity_extractor.py`
   - Trích xuất thời gian: "9h", "9 giờ 30", "sáng 9 giờ"
   - Trích xuất ngày: "hôm nay", "ngày mai", "25/12/2025"
   - Trích xuất số điện thoại: "0909123456", "+84909123456"
   - Trích xuất email: "test@example.com"
   - Tích hợp vào `nlp_service.py`

4. **Logging và Error Handling**
   - File: `app/utils/logger.py` - Centralized logging
   - File: `app/utils/exceptions.py` - Custom exceptions
   - Logs được lưu vào thư mục `logs/`
   - Separate error logs cho debug dễ dàng

5. **Comprehensive Testing**
   - File: `test_api.py` - Test suite hoàn chỉnh
   - Test tất cả endpoints: Auth, Workflows, Calls, Webhook
   - Test NLP entity extraction
   - Automated test với báo cáo chi tiết

6. **Dependencies đầy đủ**
   - File: `requirements.txt` đã được làm sạch và organize
   - Thêm `panoramisk` cho Asterisk
   - Thêm `python-multipart` cho form uploads
   - Comments rõ ràng cho từng nhóm dependencies

---

## 🚀 Hướng dẫn Setup

### 1. Clone repository và cài đặt dependencies

```powershell
# Clone repo
git clone https://github.com/gouenji92/VoiceAI-CallOutv2.git
cd VoiceAI-CallOutv2

# Tạo virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Cấu hình Environment Variables

```powershell
# Copy file .env.example
copy .env.example .env

# Chỉnh sửa .env với thông tin của bạn
notepad .env
```

**Các biến quan trọng cần cấu hình:**
- `SUPABASE_URL` và `SUPABASE_KEY`: Thông tin Supabase
- `JWT_SECRET_KEY`: Key bí mật cho JWT (generate mới!)
- `ASTERISK_*`: Thông tin Asterisk AMI
- `ASTERISK_MOCK_MODE=true`: Để test mà không cần Asterisk thực

### 3. Train Intent Model (lần đầu)

```powershell
python train_intent_model.py
```

Model sẽ được lưu vào `models/phobert-intent-classifier/`

### 4. Chạy các services

**Terminal 1: FastAPI Backend**
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2: Deeppavlov Agent (HTTP wrapper)**
```powershell
python agent/http_agent_wrapper.py
```

**Terminal 3 (Optional): Model Worker**
```powershell
python scripts/run_worker.py
```

---

## 🧪 Testing

### Chạy test tự động

```powershell
# Đảm bảo server đang chạy ở terminal khác
python test_api.py
```

### Test thủ công với Swagger UI

Mở trình duyệt: http://localhost:8000/docs

### Test entity extraction

```python
from app.services.entity_extractor import extract_entities

text = "Tôi muốn đặt lịch vào 9h sáng mai, số điện thoại 0909123456"
entities = extract_entities(text)
print(entities)
```

---

## 📁 Cấu trúc Project

```
VoiceAI/
├── agent/                      # Deeppavlov Agent
│   ├── http_agent_wrapper.py  # HTTP wrapper cho agent
│   ├── skill.py               # Skill definition
│   └── run_agent.py           # ZMQ agent (legacy)
│
├── app/                        # FastAPI Application
│   ├── main.py                # App entry point
│   ├── config.py              # Configuration
│   ├── database.py            # Supabase connection
│   ├── dependencies.py        # Auth dependencies
│   ├── models.py              # Pydantic models
│   │
│   ├── routers/               # API Routes
│   │   ├── auth.py           # Auth endpoints
│   │   ├── workflows.py      # Workflow CRUD
│   │   ├── calls.py          # Call management
│   │   ├── feedback.py       # Feedback collection
│   │   └── admin.py          # Admin endpoints
│   │
│   ├── services/              # Business Logic
│   │   ├── nlp_service.py           # NLP processing
│   │   ├── entity_extractor.py     # Entity extraction (NEW)
│   │   ├── dialog_manager.py       # Dialog management
│   │   ├── asterisk_service.py     # Asterisk integration (UPDATED)
│   │   ├── model_manager.py        # Model loading
│   │   └── database_service.py     # DB operations
│   │
│   ├── utils/                 # Utilities (NEW)
│   │   ├── logger.py         # Logging configuration
│   │   └── exceptions.py     # Custom exceptions
│   │
│   └── workers/               # Background Workers
│       └── model_worker.py
│
├── models/                     # Trained Models
│   └── phobert-intent-classifier/
│
├── logs/                       # Application Logs (auto-created)
│
├── test_api.py                # Comprehensive test suite (NEW)
├── requirements.txt           # Dependencies (UPDATED)
└── .env.example              # Environment template
```

---

## 🔧 Troubleshooting

### Lỗi: "Import panoramisk could not be resolved"
```powershell
pip install panoramisk
```

### Lỗi: "Unable to connect to Agent"
Đảm bảo agent đang chạy:
```powershell
python agent/http_agent_wrapper.py
```

### Lỗi: Database connection failed
Kiểm tra `.env`:
- `SUPABASE_URL` và `SUPABASE_KEY` đúng chưa?
- Internet connection ổn định?

### Lỗi: Model not found
Train model:
```powershell
python train_intent_model.py
```

---

## 📊 Monitoring

Logs được lưu tự động vào thư mục `logs/`:
- `voiceai_YYYYMMDD.log`: Tất cả logs
- `voiceai_error_YYYYMMDD.log`: Chỉ errors

```powershell
# Xem logs realtime
Get-Content logs\voiceai_20251023.log -Wait -Tail 50
```

---

## 🎯 Next Steps

1. **Production Deployment**
   - Setup Asterisk server thực
   - Đổi `ASTERISK_MOCK_MODE=false`
   - Configure firewall cho port 5038

2. **Model Improvement**
   - Thu thập feedback từ users
   - Chạy incremental retraining:
     ```powershell
     python scripts/incremental_retrain.py
     ```

3. **Monitoring**
   - Setup monitoring dashboard
   - Alert system cho errors
   - Performance metrics

---

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Console logs
2. File logs trong `logs/`
3. Swagger UI errors tại `/docs`

---

**Phiên bản:** 1.1.0  
**Ngày cập nhật:** 2025-10-23  
**Tác giả:** VoiceAI Team
