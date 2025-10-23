# 🧹 CLEANUP REPORT - Files & Code Dư Thừa

Phân tích toàn bộ codebase để tối ưu hóa.

---

## ❌ FILES CẦN XÓA (Duplicate/Deprecated)

### 1. Test Files Duplicate

#### 🗑️ `test_register.py` - **XÓA**
**Lý do:** Duplicate logic, đã có trong `test_full_system.py`
```python
# File chỉ test 1 API register
# Đã được cover bởi test_full_system.py (test 8 APIs)
```
**Action:** `rm test_register.py`

#### 🗑️ `quick_test.py` - **XÓA** 
**Lý do:** Debug file tạm, không cần trong production
```python
# Script debug 3 APIs cụ thể
# Đã có test_full_system.py comprehensive hơn
```
**Action:** `rm quick_test.py`

#### 🗑️ `test.py` - **XÓA**
**Lý do:** Test file cũ, chứa credentials hardcoded ⚠️
```python
# SUPABASE_KEY hardcoded trong code → security risk!
# MY_WORKFLOW_ID hardcoded → không reusable
```
**Action:** `rm test.py`

#### 🗑️ `test_api.py` - **GIỮ hoặc XÓA?**
**Phân tích:**
- Async version của test_full_system.py
- Comprehensive (có HTTPx client)
- **Nhưng:** Chưa được sử dụng, test_full_system.py đơn giản hơn

**Recommendation:** ❓ **GIỮ** nếu cần async testing trong tương lai, **XÓA** nếu chỉ dùng sync

---

### 2. Agent Files Deprecated

#### 🗑️ `agent/run_agent.py` - **XÓA**
**Lý do:** Old ZMQ-based agent, không còn dùng
```python
# Dùng dp_agent.agent với ZMQ ports 4242/4243
# ĐÃ DEPRECATED, thay bằng agent/http_agent.py (HTTP-based)
```
**Action:** `rm agent/run_agent.py`

#### 🗑️ `agent/http_agent_wrapper.py` - **XÓA**
**Lý do:** Wrapper không cần thiết, có `http_agent.py` rồi
```python
# Simple wrapper với TODO comment
# Không được sử dụng trong system
```
**Action:** `rm agent/http_agent_wrapper.py`

---

### 3. SQL Files Redundant

#### 🗑️ `sql/add_workflow_json_column.sql` - **XÓA**
**Lý do:** File rỗng (0 bytes)
```sql
-- Empty file, no content
```
**Action:** `rm sql/add_workflow_json_column.sql`

#### 🗑️ `sql/schema.sql` - **XÓA**
**Lý do:** Duplicate, đã có `schema_complete.sql` tốt hơn
- `schema.sql`: Schema cơ bản + RLS policies
- `schema_complete.sql`: Schema + RLS disabled + workflow_json fix
**Recommendation:** Giữ `schema_complete.sql`, xóa `schema.sql`

#### 🗑️ `sql/schema_clean.sql` - **XÓA**
**Lý do:** Duplicate `schema_complete.sql` (nội dung tương tự)
- Cả 2 đều disable RLS cho app tables
- `schema_complete.sql` có thêm DO block fix workflow_json

#### 🗑️ `sql/rls_policies.sql` - **XÓA hoặc GIỮ Archive**
**Lý do:** RLS policies cho accounts only
- Đã được include trong `schema_complete.sql`
- Không cần file riêng

#### 🗑️ `sql/fix_workflows_rls.sql` - **XÓA**
**Lý do:** Old fix, không còn áp dụng (đã disable RLS)
```sql
-- Script fix RLS policies cho workflows
-- Nhưng hiện tại RLS đã DISABLED → không cần nữa
```

#### 🗑️ `sql/apply_all_rls_policies.sql` - **XÓA**
**Lý do:** Áp dụng RLS cho tất cả tables, nhưng production dùng DISABLE RLS
- File này enable RLS
- Production dùng `disable_rls_for_app_tables.sql`
- Mâu thuẫn logic

---

### 4. Training Script Duplicate

#### 🗑️ `train_intent_v2.py` - **XÓA hoặc RENAME**
**Lý do:** Duplicate `train_intent_model.py` với minor changes
- Cả 2 file đều train PhoBERT intent classifier
- `train_intent_v2.py` có data augmentation tốt hơn
- Nhưng `train_intent_model.py` được sử dụng trong `setup_models.py`

**Recommendation:** 
- **Option A:** Xóa `train_intent_v2.py`, keep simple version
- **Option B:** Rename `train_intent_v2.py` → `train_intent_model.py` (replace)
- **Option C:** Giữ cả 2, rename `train_intent_v2.py` → `train_intent_advanced.py`

---

### 5. UI Files Không Dùng

#### 🗑️ `auth_ui.html` - **XÓA hoặc MOVE**
**Lý do:** Simple auth UI, không được integrate
```html
<!-- Standalone HTML file -->
<!-- Không được link từ test_dashboard.html hay API -->
```
**Recommendation:** Xóa hoặc move vào `/docs` folder

#### 🗑️ `test_realtime.html` - **XÓA hoặc MOVE**
**Lý do:** Test Supabase realtime subscriptions
- Demo file, không phải production code
- Có thể move vào `/examples` folder

---

### 6. Documentation Duplicate/Outdated

#### 🗑️ `FIX_WORKFLOWS_README.md` - **XÓA**
**Lý do:** Outdated, đã fix xong vấn đề workflows
```markdown
# Hướng dẫn fix workflows API issues
# ĐÃ FIX XONG → không cần nữa
```

#### 🗑️ `HOAN_THANH_100_PHAN_TRAM.txt` - **XÓA hoặc ARCHIVE**
**Lý do:** Checkpoint doc khi hoàn thành 100%
- Nội dung đã được include trong `TONG_HOP_CONG_VIEC.txt`
- Có thể archive vào `/docs/history/`

#### 🗑️ `HOW_TO_TEST.md` - **MERGE vào README**
**Lý do:** Testing guide ngắn
- Có thể merge vào README.md section "Testing"
- Giảm số lượng docs files

#### 🗑️ `HUONG_DAN_CHAY_PROJECT.txt` (old version) - **XÓA**
**Lý do:** Đã có `HUONG_DAN_CHAY_PROJECT_V2.txt` comprehensive hơn

---

### 7. Config/Setup Duplicates

#### 🗑️ `setup_env.ps1` - **GIỮ**
**Lý do:** PowerShell script tạo venv
- Hữu ích cho Windows users
- Khác với `setup_models.py` (models setup)
**Action:** **KEEP**

#### 🗑️ `start_server.ps1` - **GIỮ**
**Lý do:** Auto-start script convenience
- Check port trước khi start
- Hữu ích cho beginners
**Action:** **KEEP**

#### 🗑️ `environment.yml` - **XÓA hoặc UPDATE**
**Lý do:** Conda environment file
- Project dùng venv + requirements.txt
- Nếu không support conda → xóa
- Nếu support → update cho đúng

---

### 8. Empty/Unused Folders

#### 🗑️ `db/` - **XÓA nếu rỗng**
**Check:**
```powershell
ls db/
```

#### 🗑️ `results/` - **XÓA nếu rỗng**
**Lý do:** Có thể là output folder từ training
- Nếu rỗng → xóa
- Nếu có files → add vào .gitignore

---

## ✅ SUMMARY - ACTION ITEMS

### 🔴 HIGH PRIORITY - XÓA NGAY

```powershell
# Test files duplicate
rm test_register.py
rm quick_test.py
rm test.py              # ⚠️ SECURITY: Hardcoded credentials!

# Agent deprecated
rm agent/run_agent.py
rm agent/http_agent_wrapper.py

# SQL empty/redundant
rm sql/add_workflow_json_column.sql
rm sql/schema.sql
rm sql/schema_clean.sql
rm sql/rls_policies.sql
rm sql/fix_workflows_rls.sql
rm sql/apply_all_rls_policies.sql

# Docs outdated
rm FIX_WORKFLOWS_README.md
```

### 🟡 MEDIUM PRIORITY - CÂN NHẮC

```powershell
# Test async version
rm test_api.py          # Nếu không dùng async testing

# Training duplicate
rm train_intent_v2.py   # Hoặc rename thành train_intent_advanced.py

# UI demos
rm auth_ui.html
rm test_realtime.html

# Docs duplicate
rm HOAN_THANH_100_PHAN_TRAM.txt
rm HUONG_DAN_CHAY_PROJECT.txt  # Giữ V2
```

### 🟢 LOW PRIORITY - OPTIONAL

```powershell
# Merge vào README
rm HOW_TO_TEST.md       # Merge testing section vào README

# Conda support
rm environment.yml      # Nếu không dùng conda
```

---

## 📊 BEFORE vs AFTER

### Before Cleanup
```
Total files: ~60 files
- Test files: 6 (nhiều duplicate)
- SQL files: 8 (nhiều redundant)
- Agent files: 4 (2 deprecated)
- Docs: 8 (outdated/duplicate)
```

### After Cleanup
```
Total files: ~42 files (-18 files)
- Test files: 3 (core tests only)
- SQL files: 2 (schema_complete + disable_rls)
- Agent files: 2 (http_agent + skill)
- Docs: 5 (essential only)
```

**Giảm:** ~30% files → Codebase sạch hơn, dễ maintain

---

## 🚀 EXECUTION PLAN

### Step 1: Backup
```powershell
# Tạo branch backup
git checkout -b backup-before-cleanup
git push origin backup-before-cleanup
```

### Step 2: Delete High Priority
```powershell
git checkout main
git rm test_register.py quick_test.py test.py
git rm agent/run_agent.py agent/http_agent_wrapper.py
git rm sql/add_workflow_json_column.sql sql/schema.sql sql/schema_clean.sql
git rm sql/rls_policies.sql sql/fix_workflows_rls.sql sql/apply_all_rls_policies.sql
git rm FIX_WORKFLOWS_README.md
git commit -m "chore: Remove duplicate and deprecated files"
```

### Step 3: Review Medium Priority
```powershell
# Kiểm tra từng file trước khi xóa
```

### Step 4: Push
```powershell
git push origin main
```

---

## ⚠️ CRITICAL - KHÔNG XÓA

✅ **KEEP THESE FILES:**
- `setup_models.py` - Auto-setup script
- `test_full_system.py` - Main test suite
- `test_with_agent.py` - Agent integration test
- `test_dashboard.html` - Interactive testing UI
- `sql/schema_complete.sql` - Production schema
- `sql/disable_rls_for_app_tables.sql` - RLS config
- All docs in root (README, FIRST_TIME_SETUP, etc.)
- All `app/` backend code
- `agent/http_agent.py` + `agent/skill.py`

---

## 🎯 RECOMMENDATION

**Chạy lệnh này để cleanup an toàn:**

```powershell
# Tạo backup branch
git checkout -b backup-before-cleanup
git push origin backup-before-cleanup
git checkout main

# Xóa files duplicate/deprecated
git rm test_register.py quick_test.py test.py
git rm agent/run_agent.py agent/http_agent_wrapper.py  
git rm sql/add_workflow_json_column.sql sql/schema.sql sql/schema_clean.sql sql/rls_policies.sql sql/fix_workflows_rls.sql sql/apply_all_rls_policies.sql
git rm FIX_WORKFLOWS_README.md auth_ui.html test_realtime.html

# Commit
git commit -m "chore: Clean up duplicate and deprecated files

Removed:
- Test duplicates (test_register.py, quick_test.py, test.py)  
- Deprecated agents (run_agent.py, http_agent_wrapper.py)
- SQL redundant (6 files → keep only schema_complete.sql + disable_rls)
- Outdated docs (FIX_WORKFLOWS_README.md)
- Unused UI demos (auth_ui.html, test_realtime.html)

Result: -13 files, cleaner codebase"

# Push
git push origin main
```

**Sau khi cleanup:**
- Run tests: `python test_full_system.py`
- Run Agent test: `python test_with_agent.py`
- Verify: All tests pass → cleanup success ✅
