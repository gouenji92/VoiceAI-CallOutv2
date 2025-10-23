-- Row Level Security Policies cho VoiceAI
-- Chạy script này trong Supabase SQL Editor

-- Enable RLS trên bảng accounts
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

-- Cho phép đăng ký công khai (INSERT)
DROP POLICY IF EXISTS "Allow public registration" ON accounts;
CREATE POLICY "Allow public registration" 
ON accounts 
FOR INSERT 
WITH CHECK (true);

-- Cho phép kiểm tra email trùng lặp (SELECT)
DROP POLICY IF EXISTS "Allow email check" ON accounts;
CREATE POLICY "Allow email check" 
ON accounts 
FOR SELECT 
USING (true);

-- User chỉ có thể update tài khoản của chính mình
DROP POLICY IF EXISTS "Users can update own account" ON accounts;
CREATE POLICY "Users can update own account" 
ON accounts 
FOR UPDATE 
USING (id::text = current_setting('request.jwt.claims', true)::json->>'sub');

-- DELETE chỉ admin mới được phép (optional)
DROP POLICY IF EXISTS "Only admins can delete accounts" ON accounts;
CREATE POLICY "Only admins can delete accounts" 
ON accounts 
FOR DELETE 
USING (
  (current_setting('request.jwt.claims', true)::json->>'role') = 'admin'
);
