# 🧪 HƯỚNG DẪN TEST HỆ THỐNG

## ⚠️ QUAN TRỌNG: Phải chạy 2 terminal riêng biệt!

### 📍 Terminal 1: SERVER (Giữ mở - KHÔNG ĐÓNG)

1. Mở terminal trong VS Code (`` Ctrl + ` ``)
2. Chạy lệnh:
```powershell
python -X utf8 -m uvicorn app.main:app --reload
```

3. **Đợi** đến khi thấy dòng:
```
INFO:     Application startup complete.
```

4. **KHÔNG TẮT terminal này!** Để server chạy suốt.

---

### 📍 Terminal 2: TEST (Terminal mới)

1. Mở terminal MỚI: Nhấn **`Ctrl + Shift + `` `** 
2. Kích hoạt venv (nếu cần):
```powershell
.\.venv\Scripts\Activate.ps1
```

3. Chạy test:
```powershell
python test_full_system.py
```

---

## ✅ Kết quả mong đợi:

```
🚀 VOICEAI - FULL SYSTEM TEST

✅ Đăng ký
✅ Đăng nhập
✅ Tạo workflow
✅ Lấy workflows (Tìm thấy: 1)
✅ Tạo version
✅ Xem versions (Tìm thấy: 1)
✅ Bắt đầu cuộc gọi
✅ Test hội thoại (4/4 thành công)

Tổng kết: 8/8 tests passed (100%)
🎉 TẤT CẢ TESTS ĐỀU THÀNH CÔNG!
```

---

## 🔧 Nếu vẫn gặp lỗi:

### 1. Lỗi "password cannot be longer than 72 bytes"
**Nguyên nhân**: Code cũ chưa reload
**Giải pháp**: 
- Tắt server (Ctrl+C trong Terminal 1)
- Chạy lại: `python -X utf8 -m uvicorn app.main:app --reload`

### 2. Lỗi "RLS policy violation"
**Nguyên nhân**: Chưa tắt RLS trong Supabase
**Giải pháp**:
- Vào: https://supabase.com/dashboard
- SQL Editor → Chạy:
```sql
ALTER TABLE workflows DISABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_intents DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_entities DISABLE ROW LEVEL SECURITY;
ALTER TABLE feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE reports DISABLE ROW LEVEL SECURITY;
```

### 3. Lỗi "Could not validate credentials"
**Nguyên nhân**: Token không hợp lệ hoặc đăng ký thất bại
**Giải pháp**: Xóa test users cũ trong Supabase Dashboard → Table Editor → accounts

---

## 📚 Các test khác:

### Test UI trong browser:
```powershell
# Mở test_dashboard.html trong browser
# Hoặc auth_ui.html cho test đăng ký/đăng nhập đơn giản
```

### Test API bằng Swagger UI:
- Vào: http://127.0.0.1:8000/docs
- Thử các endpoint thủ công

---

## 🎓 Tips:

1. **Luôn giữ Terminal 1 (server) chạy**
2. **Chỉ chạy test trong Terminal 2**
3. **Nếu sửa code** → Server tự reload (không cần restart thủ công)
4. **Nếu test fail** → Xem log chi tiết trong Terminal 1 (server)
5. **Xóa test data** → Vào Supabase Dashboard → Table Editor
