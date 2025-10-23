-- DISABLE RLS cho workflows và workflow_versions
-- Vì backend FastAPI đã kiểm tra user_id qua JWT token rồi
-- RLS chỉ cần cho bảng accounts (đăng ký công khai)

-- Tắt RLS cho workflows
ALTER TABLE workflows DISABLE ROW LEVEL SECURITY;

-- Tắt RLS cho workflow_versions  
ALTER TABLE workflow_versions DISABLE ROW LEVEL SECURITY;

-- Tắt RLS cho calls
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;

-- Tắt RLS cho các bảng khác (trừ accounts)
ALTER TABLE conversation_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_intents DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_entities DISABLE ROW LEVEL SECURITY;
ALTER TABLE feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE reports DISABLE ROW LEVEL SECURITY;

-- GIỮ RLS cho accounts (cho phép đăng ký công khai)
-- (accounts đã có policy đúng rồi)

-- Verify
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;
