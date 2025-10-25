# 📚 Hướng dẫn sử dụng RAG Knowledge Base

## Tổng quan

Hệ thống RAG (Retrieval-Augmented Generation) cho phép callbot truy xuất thông tin từ cơ sở tri thức để trả lời câu hỏi khách hàng chính xác hơn.

**RAG hiện tại là một "engine" sẵn sàng** - bạn chỉ cần đưa dữ liệu vào.

---

## 🚀 Quick Start

### 1. Kiểm tra trạng thái RAG

```bash
GET http://localhost:8000/api/rag/status
```

**Response khi chưa có data:**
```json
{
  "provider": "local",
  "corpus_size": 0,
  "is_indexed": true,
  "corpus_dir": "C:\\Users\\Admin\\VoiceAI\\data\\knowledge_base",
  "cache_enabled": false,
  "message": "Add knowledge files to data/knowledge_base/ or use /ingest API"
}
```

### 2. Thêm dữ liệu - Cách 1: File trực tiếp (Khuyến nghị)

**Bước 1:** Tạo file trong `data/knowledge_base/`

**Ví dụ - company_info.txt:**
```txt
Thông tin công ty ABC
Địa chỉ: 123 Đường Nguyễn Huệ, Quận 1, TP.HCM
Điện thoại: 028-1234-5678
Email: contact@abc.com.vn
Website: www.abc.com.vn

Giờ làm việc:
- Thứ 2 - Thứ 6: 08:00 - 17:30
- Thứ 7: 08:00 - 12:00
- Chủ nhật: Nghỉ

Chi nhánh:
- TP.HCM: 123 Đường Nguyễn Huệ, Quận 1
- Hà Nội: 456 Đường Hoàn Kiếm, Quận Hoàn Kiếm
- Đà Nẵng: 789 Đường Bạch Đằng, Quận Hải Châu
```

**Ví dụ - faq.md:**
```markdown
# Câu hỏi thường gặp

## Làm thế nào để đặt lịch hẹn?

Bạn có thể đặt lịch hẹn qua các cách sau:
1. Gọi điện thoại: 028-1234-5678
2. Website: www.abc.com.vn/booking
3. Ứng dụng di động ABC App
4. Trực tiếp tại văn phòng

Thời gian xử lý: Trong vòng 2 giờ làm việc.

## Chính sách hủy lịch hẹn là gì?

- Hủy trước 24h: Miễn phí
- Hủy trong vòng 24h: Phí 50.000 VND
- Hủy trong vòng 2h: Phí 100.000 VND
- Không đến mà không báo: Phí 200.000 VND

## Các hình thức thanh toán được chấp nhận?

Chúng tôi chấp nhận:
- Tiền mặt
- Thẻ ATM nội địa
- Thẻ tín dụng Visa, Mastercard
- Chuyển khoản ngân hàng
- Ví điện tử: Momo, ZaloPay, VNPay
```

**Ví dụ - products.json:**
```json
[
  {
    "name": "Gói dịch vụ Basic",
    "price": "500.000 VND/tháng",
    "description": "Phù hợp với cá nhân và doanh nghiệp nhỏ",
    "features": [
      "Hỗ trợ 24/7",
      "Tối đa 10 người dùng",
      "10GB lưu trữ",
      "Báo cáo cơ bản"
    ]
  },
  {
    "name": "Gói dịch vụ Professional",
    "price": "1.500.000 VND/tháng",
    "description": "Dành cho doanh nghiệp vừa và lớn",
    "features": [
      "Hỗ trợ ưu tiên 24/7",
      "Không giới hạn người dùng",
      "100GB lưu trữ",
      "Báo cáo nâng cao",
      "API tích hợp",
      "Tùy chỉnh giao diện"
    ]
  }
]
```

**Bước 2:** Restart server để load data

```powershell
STOP.bat
START.bat
```

Hoặc chỉ restart API (nếu đang chạy manual):
```powershell
# Press Ctrl+C to stop
python -X utf8 -m uvicorn app.main:app --reload
```

**Bước 3:** Kiểm tra lại status

```bash
GET http://localhost:8000/api/rag/status
```

**Response sau khi thêm data:**
```json
{
  "provider": "local",
  "corpus_size": 3,
  "is_indexed": true,
  "corpus_dir": "...",
  "cache_enabled": false,
  "message": "RAG is ready"
}
```

---

### 3. Thêm dữ liệu - Cách 2: Qua API (Không cần restart)

**Bước 1:** Lấy JWT token

```bash
POST http://localhost:8000/api/auth/token
Content-Type: application/x-www-form-urlencoded

username=your_email@example.com&password=your_password
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Bước 2:** Ingest knowledge

```bash
POST http://localhost:8000/api/rag/ingest
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "content": "Chính sách bảo hành sản phẩm:\n- Bảo hành 12 tháng với lỗi nhà sản xuất\n- Bảo hành 6 tháng với phụ kiện\n- Miễn phí vận chuyển trong phạm vi nội thành\n- Đổi mới trong 7 ngày nếu có lỗi",
  "source": "warranty_policy"
}
```

**Response:**
```json
{
  "message": "ingested",
  "corpus_size": 4
}
```

**Python script để ingest nhiều data:**
```python
import requests

API_URL = "http://localhost:8000"
TOKEN = "your_jwt_token_here"

headers = {"Authorization": f"Bearer {TOKEN}"}

knowledge_items = [
    {
        "content": "Chương trình khuyến mãi tháng 10:\n- Giảm 20% tất cả dịch vụ\n- Tặng voucher 100k cho khách hàng mới\n- Ưu đãi combo: mua 2 tặng 1",
        "source": "promotion_oct_2025"
    },
    {
        "content": "Quy trình xử lý khiếu nại:\n1. Tiếp nhận qua hotline hoặc email\n2. Xác nhận trong 2h\n3. Điều tra và giải quyết trong 24-48h\n4. Báo cáo kết quả cho khách hàng\n5. Theo dõi hài lòng sau 7 ngày",
        "source": "complaint_process"
    }
]

for item in knowledge_items:
    resp = requests.post(
        f"{API_URL}/api/rag/ingest",
        json=item,
        headers=headers
    )
    print(f"✓ Ingested: {item['source']} - Corpus size: {resp.json()['corpus_size']}")
```

---

### 4. Test tìm kiếm

```bash
GET http://localhost:8000/api/rag/search?q=giờ làm việc&k=3
```

**Response:**
```json
{
  "query": "giờ làm việc",
  "k": 3,
  "results": [
    {
      "score": 0.8234,
      "content": "Giờ làm việc:\n- Thứ 2 - Thứ 6: 08:00 - 17:30\n- Thứ 7: 08:00 - 12:00\n- Chủ nhật: Nghỉ",
      "source": "company_info.txt",
      "id": "C:\\Users\\Admin\\VoiceAI\\data\\knowledge_base\\company_info.txt"
    }
  ],
  "corpus_size": 6,
  "message": null
}
```

---

## 🎯 Integration với Agent

RAG đã được tích hợp sẵn vào agent cho intent **"hoi_thong_tin"**.

**Ví dụ luồng hoạt động:**

1. **User nói:** "Cho tôi hỏi giờ làm việc của công ty?"
2. **NLP Service:** Phát hiện intent = `hoi_thong_tin`, confidence = 0.85
3. **Agent (skill.py):** Gọi RAG API với query user input
4. **RAG Service:** Tìm kiếm trong knowledge base, trả về top results
5. **Agent:** Format response từ RAG và trả về
6. **Bot nói:** "Tôi tìm được thông tin: Giờ làm việc: Thứ 2 - Thứ 6: 08:00 - 17:30..."

**Code trong agent/skill.py:**
```python
elif intent == "hoi_thong_tin":
    import httpx
    if intent_confidence >= confidence_threshold:
        try:
            url = "http://127.0.0.1:8000/api/rag/search"
            params = {"q": user_input, "k": 3}
            with httpx.Client(timeout=4.0) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    if results:
                        top = results[0]
                        snippet = top.get("content", "")
                        bot_response = f"Tôi tìm được thông tin: {snippet}"
                        result["action_success"] = True
```

---

## ⚙️ RAG Providers

### Local TF-IDF (Mặc định)

- ✅ Không cần API key
- ✅ Hoạt động offline
- ✅ Nhanh, miễn phí
- ⚠️ Accuracy trung bình với tiếng Việt

**Không cần config gì thêm.**

### OpenAI Embeddings (Nâng cao)

- ✅ Accuracy cao hơn
- ✅ Hiểu semantic tốt hơn
- ⚠️ Cần API key ($$$)
- ⚠️ Cần internet

**Setup trong `.env`:**
```bash
RAG_PROVIDER=openai
OPENAI_API_KEY=sk-proj-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Optional
```

**Restart server để apply.**

### Google Gemini Embeddings

- ✅ Free tier generous hơn OpenAI
- ✅ Accuracy tốt
- ⚠️ Cần API key

**Setup trong `.env`:**
```bash
RAG_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
GEMINI_EMBEDDING_MODEL=text-embedding-004  # Optional
```

---

## 📊 Monitoring & Debugging

### Check RAG status
```bash
curl http://localhost:8000/api/rag/status
```

### Test search với different queries
```bash
curl "http://localhost:8000/api/rag/search?q=địa chỉ công ty&k=5"
curl "http://localhost:8000/api/rag/search?q=chính sách hủy&k=5"
curl "http://localhost:8000/api/rag/search?q=giá dịch vụ&k=5"
```

### View corpus files
```bash
ls data/knowledge_base/
```

### Clear và rebuild index
```bash
# Delete ingested files
rm data/knowledge_base/ingested_*.txt

# Restart server
STOP.bat
START.bat
```

---

## 💡 Best Practices

### ✅ DO:
- Tổ chức file theo chủ đề (company/, products/, support/)
- Viết ngắn gọn, dễ hiểu (như đang trả lời khách)
- Cập nhật thường xuyên (xóa info cũ)
- Test search sau khi thêm data mới
- Backup knowledge_base định kỳ

### ❌ DON'T:
- Đừng đưa file quá lớn (>10MB mỗi file)
- Đừng duplicate thông tin ở nhiều nơi
- Đừng dùng technical jargon khách không hiểu
- Đừng để thông tin sai lệch/lỗi thời

---

## 🔧 Troubleshooting

### RAG trả về empty results
- Kiểm tra `corpus_size` qua `/status` endpoint
- Verify files có trong `data/knowledge_base/`
- Restart server để rebuild index
- Thử query đơn giản hơn

### Search không chính xác
- Thử dùng OpenAI/Gemini embeddings thay vì local
- Cải thiện nội dung knowledge base (ngôn ngữ tự nhiên hơn)
- Tăng `k` parameter để xem nhiều results hơn

### Ingest API lỗi 401
- Kiểm tra JWT token còn hiệu lực
- Verify `Authorization: Bearer <token>` header

---

## 📞 Support

Nếu cần hỗ trợ, check:
- `README.md` - General project info
- `data/knowledge_base/README.md` - File format details
- API docs: http://localhost:8000/docs

Happy knowledge building! 🚀
