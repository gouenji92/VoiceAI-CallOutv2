# 📊 Tài Liệu Database Schema - VoiceAI-CallOutv2

> **Cập nhật**: 24/10/2025  
> **Phiên bản**: v1.2.0-rl  
> **Database**: PostgreSQL (Supabase)

---

## 🎯 TỔNG QUAN HỆ THỐNG

VoiceAI-CallOutv2 sử dụng PostgreSQL với 10 bảng chính để quản lý:
1. **Quản lý tài khoản** (accounts)
2. **Quản lý quy trình gọi** (workflows + workflow_versions)
3. **Xử lý cuộc gọi** (calls + conversation_logs)
4. **Trích xuất thông tin** (call_intents + call_entities)
5. **Học tăng cường** (feedback + rl_feedback)
6. **Báo cáo phân tích** (reports)

---

## 📋 SƠ ĐỒ QUAN HỆ

```
accounts (người dùng)
    ↓
workflows (quy trình gọi)
    ↓
workflow_versions (lịch sử phiên bản)
    
workflows
    ↓
calls (cuộc gọi)
    ↓
    ├── conversation_logs (chi tiết hội thoại)
    ├── call_intents (thống kê intent)
    ├── call_entities (thực thể trích xuất)
    ├── feedback (đánh giá chất lượng)
    └── rl_feedback (học tăng cường)
    
workflows
    ↓
reports (báo cáo thống kê)
```

---

## 📊 CHI TIẾT CÁC BẢNG

### 1️⃣ `accounts` - Bảng Tài Khoản
**Mục đích**: Quản lý người dùng và phân quyền

| Cột | Kiểu dữ liệu | Bắt buộc | Mặc định | Giải thích |
|-----|-------------|----------|----------|------------|
| `id` | uuid | ✅ | `gen_random_uuid()` | Mã định danh duy nhất |
| `email` | text | ✅ | - | Email đăng nhập (không trùng) |
| `password_hash` | text | ✅ | - | Mật khẩu mã hóa (bcrypt) |
| `role` | text | ❌ | `'user'` | Vai trò: `user` hoặc `admin` |
| `created_at` | timestamptz | ❌ | `now()` | Thời điểm tạo tài khoản |

**Đặc điểm**:
- ✅ Bật RLS (Row Level Security) cho đăng ký công khai
- ✅ Email là UNIQUE constraint
- ✅ Khi xóa account → SET NULL cho các bảng liên quan

**Ví dụ**:
```sql
INSERT INTO accounts (email, password_hash, role) 
VALUES ('admin@voiceai.vn', '$2b$12$...', 'admin');
```

---

### 2️⃣ `workflows` - Bảng Quy Trình Gọi
**Mục đích**: Lưu trữ các workflow/kịch bản gọi

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã workflow |
| `user_id` | uuid | ❌ | `accounts(id)` | Người tạo workflow |
| `name` | text | ✅ | - | Tên workflow (VD: "Telesale bảo hiểm") |
| `description` | text | ❌ | - | Mô tả mục đích |
| `current_version_id` | uuid | ❌ | `workflow_versions(id)` | Con trỏ tới version hiện tại |
| `created_at` | timestamptz | ❌ | - | Thời điểm tạo |

**Đặc điểm**:
- 🔗 Một user có thể tạo nhiều workflows
- 📌 `current_version_id` trỏ tới phiên bản đang active
- 🔄 Hỗ trợ version control (xem `workflow_versions`)

**Ví dụ**:
```sql
INSERT INTO workflows (user_id, name, description) 
VALUES ('uuid-user-123', 'Telesale Bảo Hiểm Xe', 'Workflow gọi khách hàng bán bảo hiểm ô tô');
```

---

### 3️⃣ `workflow_versions` - Bảng Phiên Bản Workflow
**Mục đích**: Lưu lịch sử các phiên bản workflow (version control)

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã phiên bản |
| `workflow_id` | uuid | ✅ | `workflows(id)` CASCADE | Workflow cha |
| `user_id` | uuid | ❌ | `accounts(id)` | Người tạo version |
| `workflow_json` | jsonb | ✅ | - | Nội dung workflow (JSON) |
| `change_description` | text | ❌ | - | Mô tả thay đổi |
| `created_at` | timestamptz | ❌ | - | Thời điểm tạo version |

**Đặc điểm**:
- 📝 Mỗi lần sửa workflow → tạo version mới
- 🗂️ `workflow_json` lưu toàn bộ logic: nodes, edges, conditions
- 🗑️ Xóa workflow → xóa hết versions (CASCADE)

**Ví dụ workflow_json**:
```json
{
  "nodes": [
    {"id": "start", "type": "greeting", "text": "Xin chào, tôi là tư vấn viên..."},
    {"id": "ask_intent", "type": "question", "text": "Quý khách quan tâm loại bảo hiểm nào?"}
  ],
  "edges": [
    {"from": "start", "to": "ask_intent"}
  ]
}
```

---

### 4️⃣ `calls` - Bảng Cuộc Gọi
**Mục đích**: Lưu metadata của từng cuộc gọi

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã cuộc gọi |
| `workflow_id` | uuid | ❌ | `workflows(id)` | Workflow sử dụng |
| `customer_phone` | text | ❌ | - | SĐT khách hàng |
| `status` | text | ❌ | `'pending'` | Trạng thái: `pending`, `in_progress`, `completed`, `failed` |
| `start_time` | timestamptz | ❌ | - | Thời điểm bắt đầu |
| `end_time` | timestamptz | ❌ | - | Thời điểm kết thúc |
| `duration` | double precision | ❌ | - | Thời lượng (giây) |
| `last_intent` | text | ❌ | - | Intent cuối: `dong_y`, `tu_choi`, `yeu_cau_ho_tro`... |
| `created_at` | timestamptz | ❌ | - | Thời điểm tạo |

**Đặc điểm**:
- 📞 Mỗi cuộc gọi thuộc 1 workflow
- ⏱️ `duration` = `end_time` - `start_time`
- 🎯 `last_intent` dùng để phân loại kết quả
- 🔍 Có index `idx_calls_workflow_id` để query nhanh

**Luồng trạng thái**:
```
pending → in_progress → completed/failed
```

---

### 5️⃣ `conversation_logs` - Bảng Log Hội Thoại
**Mục đích**: Lưu toàn bộ transcript cuộc gọi + kết quả NLP

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã log |
| `call_id` | uuid | ✅ | `calls(id)` CASCADE | Cuộc gọi liên quan |
| `speaker` | text | ✅ | - | Người nói: `user` hoặc `bot` |
| `text` | text | ✅ | - | Nội dung câu nói (từ speech-to-text) |
| `intent` | text | ❌ | - | Intent nhận diện (VD: `yeu_cau_ho_tro`) |
| `confidence` | double precision | ❌ | - | Độ tin cậy intent (0.0-1.0) |
| `created_at` | timestamptz | ❌ | - | Thời điểm nói |

**Đặc điểm**:
- 💬 Lưu từng câu nói theo thứ tự thời gian
- 🤖 Câu bot → `speaker='bot'`, không có intent
- 👤 Câu user → `speaker='user'`, có intent + confidence
- 🔍 Index `idx_convlogs_call_id` để query transcript nhanh

**Ví dụ**:
```sql
-- User nói
INSERT INTO conversation_logs (call_id, speaker, text, intent, confidence)
VALUES ('call-uuid', 'user', 'Tôi muốn biết thông tin bảo hiểm', 'yeu_cau_thong_tin', 0.92);

-- Bot trả lời
INSERT INTO conversation_logs (call_id, speaker, text)
VALUES ('call-uuid', 'bot', 'Dạ, chúng tôi có các gói bảo hiểm xe hơi...');
```

---

### 6️⃣ `call_intents` - Bảng Thống Kê Intent
**Mục đích**: Đếm số lần mỗi intent xuất hiện trong cuộc gọi

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã thống kê |
| `call_id` | uuid | ✅ | `calls(id)` CASCADE | Cuộc gọi |
| `intent_name` | text | ✅ | - | Tên intent (VD: `dong_y`) |
| `count` | integer | ❌ | `1` | Số lần xuất hiện |
| `accuracy` | double precision | ❌ | - | Độ chính xác TB của intent |

**Đặc điểm**:
- 📊 Tổng hợp intent trong cuộc gọi
- 🔢 Dùng để phân tích xu hướng khách hàng
- 📈 `accuracy` = trung bình `confidence` của intent

**Ví dụ**:
```sql
-- Trong cuộc gọi, "yeu_cau_ho_tro" xuất hiện 3 lần
INSERT INTO call_intents (call_id, intent_name, count, accuracy)
VALUES ('call-uuid', 'yeu_cau_ho_tro', 3, 0.88);
```

---

### 7️⃣ `call_entities` - Bảng Thực Thể Trích Xuất
**Mục đích**: Lưu thông tin quan trọng trích xuất từ cuộc gọi (NER)

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã entity |
| `call_id` | uuid | ✅ | `calls(id)` CASCADE | Cuộc gọi |
| `entity_name` | text | ✅ | - | Loại entity: `product_name`, `price`, `date` |
| `value` | text | ❌ | - | Giá trị entity |

**Đặc điểm**:
- 🏷️ Trích xuất thông tin có cấu trúc từ text tự do
- 💰 VD: Giá sản phẩm, tên sản phẩm, ngày hẹn

**Ví dụ**:
```sql
-- Khách nói: "Tôi muốn mua bảo hiểm xe hơi giá 5 triệu"
INSERT INTO call_entities (call_id, entity_name, value) VALUES
('call-uuid', 'product_name', 'Bảo hiểm xe hơi'),
('call-uuid', 'price', '5 triệu');
```

---

### 8️⃣ `feedback` - Bảng Feedback Chất Lượng
**Mục đích**: Thu thập feedback từ user/admin để cải thiện model

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã feedback |
| `call_id` | uuid | ❌ | `calls(id)` | Cuộc gọi liên quan |
| `user_id` | uuid | ❌ | `accounts(id)` | Người đánh giá |
| `text` | text | ✅ | - | Câu nói cần feedback |
| `intent` | text | ❌ | - | Intent dự đoán |
| `confidence` | double precision | ❌ | - | Độ tin cậy |
| `corrected` | boolean | ❌ | `false` | Đã sửa chưa |
| `approved` | boolean | ❌ | `false` | Đã duyệt chưa |
| `reviewed` | boolean | ❌ | `false` | Đã xem xét chưa |
| `created_at` | timestamptz | ❌ | - | Thời điểm tạo |

**Đặc điểm**:
- ✏️ User đánh dấu intent sai → `corrected=true`
- ✅ Admin duyệt → `approved=true`, `reviewed=true`
- 🔄 Dữ liệu dùng để retrain model
- 🔍 Index `idx_feedback_call_id`

**Workflow**:
```
1. Model dự đoán sai
   ↓
2. User mark corrected=true
   ↓
3. Admin review → approved=true
   ↓
4. Dùng để retrain model PhoBERT
```

---

### 9️⃣ `reports` - Bảng Báo Cáo Thống Kê
**Mục đích**: Lưu báo cáo định kỳ về hiệu suất workflow

| Cột | Kiểu dữ liệu | Bắt buộc | Khóa ngoại | Giải thích |
|-----|-------------|----------|------------|------------|
| `id` | uuid | ✅ | - | Mã báo cáo |
| `workflow_id` | uuid | ✅ | `workflows(id)` CASCADE | Workflow |
| `total_calls` | integer | ❌ | `0` | Tổng số cuộc gọi |
| `success_rate` | double precision | ❌ | - | Tỷ lệ thành công (%) |
| `avg_duration` | double precision | ❌ | - | Thời lượng TB (giây) |
| `positive_intent_rate` | double precision | ❌ | - | Tỷ lệ intent tích cực (%) |
| `created_at` | timestamptz | ❌ | - | Thời điểm tạo |

**Đặc điểm**:
- 📅 Tạo báo cáo định kỳ (ngày/tuần/tháng)
- 📊 Metrics quan trọng cho business

**Công thức**:
```python
success_rate = (calls với status='completed') / total_calls * 100
positive_intent_rate = (calls có intent='dong_y' hoặc 'quan_tam') / total_calls * 100
avg_duration = AVERAGE(duration) từ bảng calls
```

---

### 🔟 `rl_feedback` - Bảng Học Tăng Cường (RL)
**Mục đích**: Lưu reward/penalty để RL Tuner điều chỉnh threshold

| Cột | Kiểu dữ liệu | Bắt buộc | Giải thích |
|-----|-------------|----------|------------|
| `id` | uuid | ✅ | Mã feedback |
| `call_id` | text | ✅ | ID cuộc gọi (text, không FK) |
| `reward` | double precision | ✅ | Phần thưởng: `+1` (tốt), `-1` (xấu), `0` (TB) |
| `final_intent` | text | ❌ | Intent cuối cùng |
| `notes` | text | ❌ | Ghi chú |
| `created_at` | timestamptz | ❌ | Thời điểm ghi nhận |

**Đặc điểm**:
- 🤖 **Reinforcement Learning** cho threshold tuning
- 🎯 Thuật toán: **Contextual Epsilon-Greedy + UCB1**
- 📈 Tự động điều chỉnh threshold cho từng intent

**Logic RL**:
```python
# Intent có nhiều reward âm → tăng threshold (yêu cầu model tự tin hơn)
if intent_rewards < 0:
    threshold += 0.05  # Từ 0.85 → 0.90

# Intent có nhiều reward dương → giảm threshold (model đã chính xác)
if intent_rewards > 0:
    threshold -= 0.02  # Từ 0.90 → 0.88
```

**Indexes**:
- `idx_rl_feedback_call_id` → Query theo call
- `idx_rl_feedback_created_at` → Query theo thời gian
- `idx_rl_feedback_reward` → Filter theo reward

**Ví dụ**:
```sql
-- Cuộc gọi thành công, intent chính xác
INSERT INTO rl_feedback (call_id, reward, final_intent, notes)
VALUES ('call-123', 1.0, 'dong_y', 'Khách đồng ý mua bảo hiểm');

-- Cuộc gọi thất bại, intent sai
INSERT INTO rl_feedback (call_id, reward, final_intent, notes)
VALUES ('call-456', -1.0, 'tu_choi', 'Model dự đoán sai, khách thực sự muốn hỗ trợ');
```

---

## 🔒 BẢO MẬT VÀ PHÂN QUYỀN

### Row Level Security (RLS)

| Bảng | RLS Status | Lý do |
|------|-----------|-------|
| `accounts` | ✅ **BẬT** | Cho phép đăng ký công khai, kiểm tra email |
| Các bảng khác | ❌ **TẮT** | Backend FastAPI tự check quyền qua JWT token |

**Policies cho accounts**:
```sql
-- Cho phép đăng ký công khai
CREATE POLICY "Allow public registration" 
ON accounts FOR INSERT WITH CHECK (true);

-- Cho phép kiểm tra email trùng
CREATE POLICY "Allow email check" 
ON accounts FOR SELECT USING (true);
```

**Lý do tắt RLS các bảng khác**:
- ⚡ Giảm overhead, tăng performance
- 🔐 Backend FastAPI đã check quyền qua JWT
- 🔧 Linh hoạt hơn trong xử lý logic phức tạp

---

## 🗑️ CHIẾN LƯỢC XÓA DỮ LIỆU (CASCADE)

```sql
Xóa workflow
  ↓ CASCADE
  ├── Xóa hết workflow_versions
  └── SET NULL cho reports

Xóa call
  ↓ CASCADE
  ├── Xóa hết conversation_logs
  ├── Xóa hết call_intents
  └── Xóa hết call_entities

Xóa account
  ↓ SET NULL
  ├── workflows.user_id → NULL (giữ workflow)
  ├── calls.user_id → NULL (giữ call data)
  └── feedback.user_id → NULL (giữ feedback)
```

**Lý do SET NULL thay vì CASCADE**:
- 📊 Giữ lại dữ liệu lịch sử cho phân tích
- 🔍 Không mất thông tin cuộc gọi khi user nghỉ việc

---

## 🚀 INDEXES TỐI ƯU HÓA

| Index | Bảng | Cột | Mục đích |
|-------|------|-----|----------|
| `idx_calls_workflow_id` | calls | workflow_id | Query "cuộc gọi của workflow X" |
| `idx_convlogs_call_id` | conversation_logs | call_id | Query "transcript của call Y" |
| `idx_feedback_call_id` | feedback | call_id | Query "feedback của call Z" |
| `idx_rl_feedback_call_id` | rl_feedback | call_id | Query RL feedback theo call |
| `idx_rl_feedback_created_at` | rl_feedback | created_at | Lọc theo thời gian |
| `idx_rl_feedback_reward` | rl_feedback | reward | Lọc theo +1/-1 |

**Ví dụ query tối ưu**:
```sql
-- NHANH: Có index
SELECT * FROM calls WHERE workflow_id = 'uuid-123';

-- NHANH: Có index
SELECT * FROM conversation_logs WHERE call_id = 'call-uuid' ORDER BY created_at;

-- NHANH: Có index
SELECT * FROM rl_feedback 
WHERE created_at > '2025-10-01' AND reward > 0;
```

---

## 🔄 LUỒNG DỮ LIỆU THỰC TẾ

### Kịch bản: Cuộc gọi telesale bảo hiểm thành công

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User tạo tài khoản                                       │
│    → accounts (email, password_hash)                        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. User tạo workflow "Telesale Bảo Hiểm Xe"                 │
│    → workflows (name, description)                          │
│    → workflow_versions (workflow_json chứa logic)           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Hệ thống bắt đầu cuộc gọi                                │
│    → calls (workflow_id, customer_phone, status='pending')  │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Trong cuộc gọi (status='in_progress')                    │
│                                                              │
│ 👤 Khách: "Tôi muốn biết thông tin bảo hiểm"                │
│    → conversation_logs (speaker='user', intent='yeu_cau_..') │
│    → NLP phân tích: intent, confidence                      │
│                                                              │
│ 🤖 Bot: "Dạ, chúng tôi có gói bảo hiểm xe hơi..."           │
│    → conversation_logs (speaker='bot', text='...')          │
│                                                              │
│ 👤 Khách: "Bảo hiểm xe hơi giá 5 triệu có không?"           │
│    → conversation_logs + NLP                                │
│    → call_entities (product_name='Bảo hiểm xe hơi')         │
│    → call_entities (price='5 triệu')                        │
│                                                              │
│ 👤 Khách: "Được, tôi đồng ý mua"                            │
│    → conversation_logs (intent='dong_y', confidence=0.95)   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Kết thúc cuộc gọi                                        │
│    → calls (status='completed', end_time, duration)         │
│    → calls (last_intent='dong_y')                           │
│    → call_intents (intent_name='dong_y', count=1)           │
│    → call_intents (intent_name='yeu_cau_thong_tin', count=2)│
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Admin/System đánh giá                                    │
│    → rl_feedback (reward=+1, notes='Thành công')           │
│    → RL Tuner cập nhật threshold cho intent 'dong_y'        │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Tạo báo cáo định kỳ (cuối ngày/tuần)                     │
│    → reports (total_calls, success_rate, avg_duration)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 QUERIES MẪU HỮU ÍCH

### Query 1: Lấy transcript đầy đủ của cuộc gọi
```sql
SELECT 
    cl.created_at,
    cl.speaker,
    cl.text,
    cl.intent,
    cl.confidence
FROM conversation_logs cl
WHERE cl.call_id = 'your-call-uuid'
ORDER BY cl.created_at ASC;
```

### Query 2: Thống kê intent của workflow trong tháng
```sql
SELECT 
    ci.intent_name,
    COUNT(*) as total_occurrences,
    AVG(ci.accuracy) as avg_confidence
FROM call_intents ci
JOIN calls c ON ci.call_id = c.id
WHERE c.workflow_id = 'workflow-uuid'
  AND c.created_at >= '2025-10-01'
  AND c.created_at < '2025-11-01'
GROUP BY ci.intent_name
ORDER BY total_occurrences DESC;
```

### Query 3: Tính success rate của workflow
```sql
SELECT 
    w.name,
    COUNT(c.id) as total_calls,
    COUNT(CASE WHEN c.status = 'completed' THEN 1 END) as completed_calls,
    ROUND(
        COUNT(CASE WHEN c.status = 'completed' THEN 1 END)::numeric / 
        NULLIF(COUNT(c.id), 0) * 100, 
        2
    ) as success_rate_percent
FROM workflows w
LEFT JOIN calls c ON c.workflow_id = w.id
WHERE w.id = 'workflow-uuid'
GROUP BY w.id, w.name;
```

### Query 4: Lấy feedback chưa review
```sql
SELECT 
    f.id,
    f.text,
    f.intent,
    f.confidence,
    c.customer_phone,
    u.email as reviewer_email
FROM feedback f
LEFT JOIN calls c ON f.call_id = c.id
LEFT JOIN accounts u ON f.user_id = u.id
WHERE f.reviewed = false
ORDER BY f.created_at DESC
LIMIT 50;
```

### Query 5: Phân tích RL performance theo intent
```sql
SELECT 
    rl.final_intent,
    COUNT(*) as total_feedback,
    AVG(rl.reward) as avg_reward,
    SUM(CASE WHEN rl.reward > 0 THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN rl.reward < 0 THEN 1 ELSE 0 END) as negative_count
FROM rl_feedback rl
WHERE rl.created_at >= NOW() - INTERVAL '7 days'
GROUP BY rl.final_intent
ORDER BY avg_reward DESC;
```

### Query 6: Top entities được trích xuất
```sql
SELECT 
    ce.entity_name,
    ce.value,
    COUNT(*) as frequency
FROM call_entities ce
JOIN calls c ON ce.call_id = c.id
WHERE c.workflow_id = 'workflow-uuid'
  AND c.created_at >= NOW() - INTERVAL '30 days'
GROUP BY ce.entity_name, ce.value
ORDER BY frequency DESC
LIMIT 20;
```

---

## 🎯 BEST PRACTICES

### 1. Khi tạo cuộc gọi mới
```python
# 1. Tạo call record
call = supabase.table("calls").insert({
    "workflow_id": workflow_id,
    "customer_phone": phone,
    "status": "pending",
    "start_time": datetime.now()
}).execute()

# 2. Update status khi bắt đầu
supabase.table("calls").update({
    "status": "in_progress"
}).eq("id", call.data[0]["id"]).execute()

# 3. Log mỗi câu nói
for turn in conversation:
    supabase.table("conversation_logs").insert({
        "call_id": call.data[0]["id"],
        "speaker": turn.speaker,
        "text": turn.text,
        "intent": turn.intent,  # nếu speaker='user'
        "confidence": turn.confidence
    }).execute()

# 4. Kết thúc cuộc gọi
supabase.table("calls").update({
    "status": "completed",
    "end_time": datetime.now(),
    "duration": duration_seconds,
    "last_intent": final_intent
}).eq("id", call.data[0]["id"]).execute()
```

### 2. Khi ghi RL feedback
```python
# Ghi reward sau mỗi cuộc gọi
supabase.table("rl_feedback").insert({
    "call_id": call_id,
    "reward": 1.0 if success else -1.0,
    "final_intent": last_intent,
    "notes": f"Call {'succeeded' if success else 'failed'}"
}).execute()

# RL Tuner sẽ đọc và update thresholds tự động
```

### 3. Khi tạo báo cáo
```python
# Chạy cronjob hàng ngày
def generate_daily_report(workflow_id, date):
    calls = get_calls_by_date(workflow_id, date)
    
    supabase.table("reports").insert({
        "workflow_id": workflow_id,
        "total_calls": len(calls),
        "success_rate": calculate_success_rate(calls),
        "avg_duration": calculate_avg_duration(calls),
        "positive_intent_rate": calculate_positive_rate(calls)
    }).execute()
```

---

## 🔧 TROUBLESHOOTING

### Vấn đề: RLS chặn query
```sql
-- Kiểm tra RLS status
SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public';

-- Tắt RLS nếu cần (chỉ cho dev/test)
ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
```

### Vấn đề: Query chậm
```sql
-- Kiểm tra có index không
SELECT * FROM pg_indexes WHERE tablename = 'your_table';

-- Tạo index nếu thiếu
CREATE INDEX idx_name ON table_name(column_name);
```

### Vấn đề: Thiếu cột workflow_json
```sql
-- Script tự động kiểm tra và thêm (đã có trong schema_complete.sql)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'workflow_versions' AND column_name = 'workflow_json'
    ) THEN
        ALTER TABLE workflow_versions ADD COLUMN workflow_json jsonb NOT NULL DEFAULT '{}'::jsonb;
    END IF;
END $$;
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **Schema SQL**: `sql/schema_complete.sql`
- **Changelog**: `CHANGELOG.md`
- **Phase Summary**: `PHASE_SUMMARY.md`
- **README**: `README.md`

---

## 📞 HỖ TRỢ

Nếu có thắc mắc về database schema, vui lòng:
1. Kiểm tra file `sql/schema_complete.sql`
2. Xem các queries mẫu trong file này
3. Liên hệ team lead để được hỗ trợ

---

**Cập nhật lần cuối**: 24/10/2025  
**Phiên bản**: v1.2.0-rl  
**Tác giả**: VoiceAI Team
