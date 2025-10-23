# HƯỚNG DẪN FIX LỖI WORKFLOWS

## 🔴 Vấn đề gặp phải:
```
❌ Tạo workflow - RLS policy violation
❌ Lấy workflows - APIResponse has no attribute 'error'  
❌ Tạo version - Lỗi cascade
❌ Xem versions - Lỗi cascade
❌ Bắt đầu cuộc gọi - Lỗi cascade
❌ Test hội thoại - Lỗi cascade
```

## ✅ Đã fix:

### 1. Fix code (workflows.py)
- ✅ Thay `response.error` → `try/except` (supabase-py v2 không có `.error`)
- ✅ Thêm error handling chi tiết bằng tiếng Việt
- ✅ Loại bỏ kiểm tra `.error` đã deprecated

### 2. Fix database (RLS policies)
**Vấn đề**: Backend dùng service_role key → RLS vẫn block vì không có JWT token của user

**Giải pháp**: Tắt RLS cho các bảng backend-managed, chỉ giữ RLS cho `accounts`

## 📝 BƯỚC THỰC HIỆN:

### Bước 1: Chạy SQL trong Supabase SQL Editor
```sql
-- Mở: https://supabase.com/dashboard/project/YOUR_PROJECT/sql
-- Copy & paste nội dung file: sql/disable_rls_for_app_tables.sql
-- Hoặc copy đoạn dưới đây:

ALTER TABLE workflows DISABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_intents DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_entities DISABLE ROW LEVEL SECURITY;
ALTER TABLE feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE reports DISABLE ROW LEVEL SECURITY;
```

### Bước 2: Restart server
Server đã tự động reload khi bạn lưu file workflows.py.
Nếu chưa reload, Ctrl+C và chạy lại:
```powershell
python -X utf8 -m uvicorn app.main:app --reload
```

### Bước 3: Test lại
```powershell
python test_full_system.py
```

## 🎯 Kết quả mong đợi:
```
✅ Đăng ký
✅ Đăng nhập  
✅ Tạo workflow
✅ Lấy workflows
✅ Tạo version
✅ Xem versions
✅ Bắt đầu cuộc gọi
✅ Test hội thoại
```

## 🔐 Bảo mật:
- **RLS TẮT** cho workflows/calls: Backend FastAPI đã check `current_user_id` qua JWT
- **RLS BẬT** cho accounts: Cho phép đăng ký công khai nhưng chỉ xem được tài khoản của mình

## 📚 Lý do:
1. Supabase-py v2 thay đổi API: không còn `response.error`, dùng exception
2. Backend dùng service_role key → RLS cần JWT token riêng cho mỗi user
3. Đơn giản hóa: Backend đã check authorization rồi, không cần RLS 2 lớp
