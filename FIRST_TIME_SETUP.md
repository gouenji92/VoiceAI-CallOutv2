# 🚀 First Time Setup Guide

Hướng dẫn chi tiết cho người mới clone repository lần đầu.

## ⚠️ Lưu Ý Quan Trọng

**PhoBERT models KHÔNG có trong Git!**
- Models quá lớn (~500MB) → không thể push lên GitHub
- ✅ **Giải pháp:** Chạy `python setup_models.py` để tự động train

---

## 📋 Bước 1: Clone Repository

```powershell
git clone https://github.com/gouenji92/VoiceAI-CallOutv2.git
cd VoiceAI-CallOutv2
```

---

## 🐍 Bước 2: Tạo Virtual Environment

```powershell
# Tạo venv
python -m venv .venv

# Kích hoạt venv (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Nếu gặp lỗi ExecutionPolicy, chạy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📦 Bước 3: Cài Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Thời gian:** ~2-3 phút

**Packages chính:**
- FastAPI 0.115.12
- transformers 4.30.0
- torch 2.0.1
- supabase-py 2.10.0
- bcrypt 4.0.1

---

## 🤖 Bước 4: Setup PhoBERT Models (QUAN TRỌNG!)

```powershell
python setup_models.py
```

**Script này sẽ:**
1. ✅ Kiểm tra xem model đã có chưa
2. ✅ Nếu chưa → tự động train từ đầu (~5-10 phút)
3. ✅ Lưu vào `models/phobert-intent-classifier/`
4. ✅ Verify tất cả files cần thiết

**Output mong đợi:**
```
🚀 VOICEAI - AUTO SETUP SCRIPT
============================================================
📋 Bước 1: Kiểm tra dependencies...
   ✅ fastapi
   ✅ transformers
   ✅ torch
   ...

📋 Bước 2: Setup PhoBERT models...
🔥 Bắt đầu train model...
✅ Train model thành công!

🎉 HOÀN TẤT! Hệ thống sẵn sàng!
```

**Lưu ý:**
- Chạy **1 lần duy nhất** sau khi clone
- Cần **~1GB RAM** và **~500MB disk**
- Model được lưu local, không sync với Git

---

## 🔐 Bước 5: Configure Environment Variables

### 5.1. Copy file mẫu
```powershell
cp .env.example .env
```

### 5.2. Lấy thông tin Supabase

1. Truy cập https://supabase.com/dashboard
2. Chọn project của bạn
3. Vào **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role key** → `SUPABASE_KEY` (⚠️ Giữ bí mật!)

### 5.3. Edit `.env`

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# JWT Secret (tạo random string)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Environment
ENVIRONMENT=development
```

**Tạo SECRET_KEY ngẫu nhiên:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🗄️ Bước 6: Setup Database (Supabase)

### 6.1. Tạo tables
1. Mở **Supabase Dashboard** → **SQL Editor**
2. Copy nội dung file `sql/schema_complete.sql`
3. Paste và chạy

### 6.2. Disable RLS (Row Level Security)
```sql
-- Chạy trong Supabase SQL Editor
\i sql/disable_rls_for_app_tables.sql
```

**Lý do:** Backend FastAPI tự check authorization qua JWT, không cần RLS gây phức tạp.

---

## ✅ Bước 7: Verify Installation

```powershell
python setup_models.py
```

**Checklist:**
- ✅ Python packages installed
- ✅ Model files exist (config.json, model.safetensors, tokenizer_config.json)
- ✅ .env file configured
- ✅ Supabase connection OK

---

## 🚀 Bước 8: Run System

### Cách 1: Chạy riêng từng component (Recommended)

**Terminal 1: Agent Server**
```powershell
python agent/http_agent.py
```
Output:
```
🤖 DEEPPAVLOV AGENT SERVER (HTTP)
Running on: http://localhost:4242
```

**Terminal 2: Backend API**
```powershell
python -X utf8 -m uvicorn app.main:app --reload
```
Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Terminal 3: Test**
```powershell
python test_with_agent.py
```

### Cách 2: Auto-start script
```powershell
.\start_server.ps1
```

---

## 🧪 Bước 9: Test Hệ Thống

### Test 1: Full System (8 API tests)
```powershell
python test_full_system.py
```

**Kết quả mong đợi:**
```
✅ Đăng ký
✅ Đăng nhập
✅ Tạo workflow
✅ Lấy workflows
✅ Tạo version
✅ Xem versions
✅ Bắt đầu cuộc gọi
✅ Test hội thoại

Tổng kết: 8/8 tests passed (100%)
🎉 TẤT CẢ TESTS ĐỀU THÀNH CÔNG!
```

### Test 2: Agent Integration (4 conversations)
```powershell
python test_with_agent.py
```

**Kết quả mong đợi:**
```
✅ Agent server đang chạy tại port 4242
✅ Kết quả: 4/4 responses thành công
🎉 THÀNH CÔNG! Hệ thống hoạt động hoàn chỉnh 100%
```

---

## 🎉 HOÀN TẤT!

System đã sẵn sàng! Bạn có thể:

1. **Test API:** http://127.0.0.1:8000/docs (Swagger UI)
2. **Test Dashboard:** Mở `test_dashboard.html` trong browser
3. **Develop:** Xem [TONG_HOP_CONG_VIEC.txt](./TONG_HOP_CONG_VIEC.txt) để hiểu cấu trúc code

---

## 🚨 Troubleshooting

### Lỗi: "Model not found"
```powershell
# Re-run setup
python setup_models.py
```

### Lỗi: "SUPABASE_URL not found"
```powershell
# Check .env file exists
ls .env

# Nếu không có, copy từ mẫu
cp .env.example .env
# Rồi edit .env và điền thông tin
```

### Lỗi: "Agent connection refused"
```powershell
# Start Agent server trước
python agent/http_agent.py

# Rồi mới chạy API
python -X utf8 -m uvicorn app.main:app --reload
```

### Lỗi: "new row violates row-level security policy"
```sql
-- Chạy trong Supabase SQL Editor
\i sql/disable_rls_for_app_tables.sql
```

### Lỗi: ModuleNotFoundError
```powershell
# Đảm bảo venv được activate
.\.venv\Scripts\Activate.ps1

# Re-install requirements
python -m pip install -r requirements.txt
```

---

## 📚 Next Steps

1. **Đọc docs:** [HUONG_DAN_CHAY_PROJECT_V2.txt](./HUONG_DAN_CHAY_PROJECT_V2.txt)
2. **Xem architecture:** [TONG_HOP_CONG_VIEC.txt](./TONG_HOP_CONG_VIEC.txt)
3. **Custom workflows:** Edit `agent/skill.py` cho dialog logic
4. **Add intents:** Edit `train_intent_model.py` và re-train

---

## 💡 Tips

- **Auto reload:** Backend tự động reload khi edit code (nhờ `--reload` flag)
- **Debug logs:** Check terminal output của backend và agent
- **Test nhanh:** Dùng `quick_test.py` để test 1 API cụ thể
- **Production:** Đổi `ENVIRONMENT=production` trong `.env`

---

**Happy Coding! 🚀**
