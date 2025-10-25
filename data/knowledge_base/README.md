# Knowledge Base - Cơ sở tri thức cho RAG

Thư mục này chứa dữ liệu tri thức để hệ thống RAG (Retrieval-Augmented Generation) truy xuất và trả lời câu hỏi.

## 📁 Cấu trúc thư mục

Bạn có thể đưa file vào đây theo các định dạng:

```
data/knowledge_base/
├── README.md (file này)
├── company_info.txt           # Thông tin công ty
├── products_services.json     # Danh sách sản phẩm/dịch vụ
├── faq.md                     # Câu hỏi thường gặp
├── policies.txt               # Chính sách, quy định
└── custom/                    # Thư mục con tùy ý
    └── specialized_info.txt
```

## 📝 Các định dạng được hỗ trợ

### 1. **Plain Text (.txt)**
```txt
Thông tin công ty XYZ
Địa chỉ: 123 Đường ABC, Quận 1, TP.HCM
Giờ làm việc: 08:00 - 17:00 (Thứ 2 - Thứ 6)
Hotline: 1900-xxxx
```

### 2. **Markdown (.md)**
```markdown
# Câu hỏi thường gặp

## Làm sao để đặt lịch hẹn?
Bạn có thể đặt lịch qua:
- Gọi điện: 1900-xxxx
- Website: example.com/booking
- App mobile

## Chính sách hủy lịch?
...
```

### 3. **JSON (.json)**
```json
{
  "content": "Danh sách sản phẩm của chúng tôi bao gồm...",
  "category": "products",
  "metadata": {
    "updated": "2025-10-25"
  }
}
```

hoặc array:
```json
[
  {
    "product_name": "Sản phẩm A",
    "description": "Mô tả chi tiết...",
    "price": "500.000 VND"
  }
]
```

## 🔄 Cách thêm dữ liệu

### **Cách 1: Copy file trực tiếp** (Đơn giản nhất)

1. Tạo file .txt, .md, hoặc .json trong thư mục này
2. Restart API server để rebuild index:
   ```powershell
   STOP.bat
   START.bat
   ```

### **Cách 2: Qua API** (Động, không cần restart)

```bash
POST http://localhost:8000/api/rag/ingest
Headers: Authorization: Bearer <your_token>
Body:
{
  "content": "Nội dung tri thức mới...",
  "source": "manual_input_2025-10-25"
}
```

**Python example:**
```python
import requests

token = "your_jwt_token"
data = {
    "content": "Công ty chúng tôi chuyên về AI và automation...",
    "source": "company_overview"
}

response = requests.post(
    "http://localhost:8000/api/rag/ingest",
    json=data,
    headers={"Authorization": f"Bearer {token}"}
)
print(response.json())  # {"message": "ingested", "corpus_size": 1}
```

## 🔍 Test RAG Search

Sau khi thêm data, test bằng:

```bash
GET http://localhost:8000/api/rag/search?q=giờ làm việc&k=3
```

Response:
```json
{
  "query": "giờ làm việc",
  "k": 3,
  "results": [
    {
      "score": 0.85,
      "content": "Giờ làm việc: 08:00 - 17:00 (Thứ 2 - Thứ 6)...",
      "source": "company_info.txt",
      "id": "..."
    }
  ]
}
```

## ⚙️ Cấu hình RAG Provider

Mặc định: **Local TF-IDF** (không cần API key, hoạt động offline)

Nếu muốn dùng embeddings cao cấp hơn, set trong `.env`:

```bash
# OpenAI Embeddings (text-embedding-3-small)
RAG_PROVIDER=openai
OPENAI_API_KEY=sk-...

# hoặc Google Gemini
RAG_PROVIDER=gemini
GEMINI_API_KEY=...
```

## 📊 Kiểm tra trạng thái RAG

```bash
GET http://localhost:8000/api/rag/status
```

Response:
```json
{
  "provider": "local",
  "corpus_size": 5,
  "is_indexed": true
}
```

## 💡 Tips cho dữ liệu chất lượng

1. **Ngắn gọn**: Mỗi file nên tập trung vào 1 chủ đề
2. **Cấu trúc rõ ràng**: Dùng heading, bullet points
3. **Ngôn ngữ tự nhiên**: Viết như đang trả lời khách hàng
4. **Cập nhật thường xuyên**: Xóa info cũ, thêm info mới
5. **Tránh trùng lặp**: Không lặp lại thông tin ở nhiều file

## 🚀 Best Practices

- Tổ chức theo category (company/, products/, support/, policies/)
- Đặt tên file rõ ràng (không dùng file1.txt, file2.txt)
- Thêm metadata trong JSON để filter sau này
- Backup knowledge base thường xuyên
- Test search sau mỗi lần thêm data lớn

---

**Lưu ý:** Thư mục này được gitignore nếu chứa dữ liệu nhạy cảm. Chỉ README.md được track.
