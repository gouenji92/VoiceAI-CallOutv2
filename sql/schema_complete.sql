-- Supabase / PostgreSQL schema for VoiceAI
-- PHIÊN BẢN SẠCH: TẮT RLS cho tất cả (trừ accounts)
-- Backend FastAPI tự check authorization qua JWT

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =====================================================
-- TABLES
-- =====================================================

CREATE TABLE IF NOT EXISTS accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    role text DEFAULT 'user',
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflows (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES accounts(id) ON DELETE SET NULL,
    name text NOT NULL,
    description text,
    current_version_id uuid,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES workflows(id) ON DELETE CASCADE,
    user_id uuid REFERENCES accounts(id) ON DELETE SET NULL,
    workflow_json jsonb NOT NULL,
    change_description text,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS calls (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES workflows(id) ON DELETE SET NULL,
    customer_phone text,
    status text DEFAULT 'pending',
    start_time timestamptz,
    end_time timestamptz,
    duration double precision,
    last_intent text,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversation_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE CASCADE,
    speaker text NOT NULL,
    text text NOT NULL,
    intent text,
    confidence double precision,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS call_intents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE CASCADE,
    intent_name text NOT NULL,
    count integer DEFAULT 1,
    accuracy double precision
);

CREATE TABLE IF NOT EXISTS call_entities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE CASCADE,
    entity_name text NOT NULL,
    value text
);

CREATE TABLE IF NOT EXISTS feedback (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE SET NULL,
    user_id uuid REFERENCES accounts(id) ON DELETE SET NULL,
    text text NOT NULL,
    intent text,
    confidence double precision,
    corrected boolean DEFAULT false,
    approved boolean DEFAULT false,
    reviewed boolean DEFAULT false,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES workflows(id) ON DELETE CASCADE,
    total_calls integer DEFAULT 0,
    success_rate double precision,
    avg_duration double precision,
    positive_intent_rate double precision,
    created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rl_feedback (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id text NOT NULL,
    reward double precision NOT NULL,
    final_intent text,
    notes text,
    created_at timestamptz DEFAULT now()
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_calls_workflow_id ON calls(workflow_id);
CREATE INDEX IF NOT EXISTS idx_convlogs_call_id ON conversation_logs(call_id);
CREATE INDEX IF NOT EXISTS idx_feedback_call_id ON feedback(call_id);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_call_id ON rl_feedback(call_id);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_created_at ON rl_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_reward ON rl_feedback(reward);

-- =====================================================
-- RLS: CHỈ BẬT CHO ACCOUNTS (Đăng ký công khai)
-- =====================================================

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

-- Cho phép đăng ký công khai
DROP POLICY IF EXISTS "Allow public registration" ON accounts;
CREATE POLICY "Allow public registration" 
ON accounts FOR INSERT 
WITH CHECK (true);

-- Cho phép kiểm tra email trùng
DROP POLICY IF EXISTS "Allow email check" ON accounts;
CREATE POLICY "Allow email check" 
ON accounts FOR SELECT 
USING (true);

-- =====================================================
-- TẮT RLS CHO CÁC BẢNG KHÁC
-- Backend FastAPI đã kiểm tra quyền qua JWT token rồi
-- =====================================================

ALTER TABLE workflows DISABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE calls DISABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_intents DISABLE ROW LEVEL SECURITY;
ALTER TABLE call_entities DISABLE ROW LEVEL SECURITY;
ALTER TABLE feedback DISABLE ROW LEVEL SECURITY;
ALTER TABLE reports DISABLE ROW LEVEL SECURITY;
ALTER TABLE rl_feedback DISABLE ROW LEVEL SECURITY;

-- =====================================================
-- DỌN DẸP: XÓA CÁC POLICIES CŨ (nếu có)
-- =====================================================

-- Workflows
DROP POLICY IF EXISTS "Users can view own workflows" ON workflows;
DROP POLICY IF EXISTS "Users can create workflows" ON workflows;
DROP POLICY IF EXISTS "Users can update own workflows" ON workflows;
DROP POLICY IF EXISTS "Users can delete own workflows" ON workflows;

-- Workflow versions
DROP POLICY IF EXISTS "Users can view own workflow versions" ON workflow_versions;
DROP POLICY IF EXISTS "Users can create workflow versions" ON workflow_versions;

-- Calls
DROP POLICY IF EXISTS "Users can view own calls" ON calls;
DROP POLICY IF EXISTS "Users can create calls" ON calls;
DROP POLICY IF EXISTS "Users can update own calls" ON calls;

-- Conversation logs
DROP POLICY IF EXISTS "Users can view own conversation logs" ON conversation_logs;
DROP POLICY IF EXISTS "System can insert conversation logs" ON conversation_logs;

-- Call intents
DROP POLICY IF EXISTS "Users can view own call intents" ON call_intents;
DROP POLICY IF EXISTS "System can insert call intents" ON call_intents;

-- Call entities
DROP POLICY IF EXISTS "Users can view own call entities" ON call_entities;
DROP POLICY IF EXISTS "System can insert call entities" ON call_entities;

-- Feedback
DROP POLICY IF EXISTS "Users can view own feedback" ON feedback;
DROP POLICY IF EXISTS "Users can create feedback" ON feedback;
DROP POLICY IF EXISTS "Admins can update feedback" ON feedback;

-- Reports
DROP POLICY IF EXISTS "Users can view own reports" ON reports;
DROP POLICY IF EXISTS "System can insert reports" ON reports;

-- =====================================================
-- FIX: Thêm cột workflow_json (nếu thiếu)
-- =====================================================

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'workflow_versions' 
        AND column_name = 'workflow_json'
    ) THEN
        ALTER TABLE workflow_versions 
        ADD COLUMN workflow_json jsonb NOT NULL DEFAULT '{}'::jsonb;
        
        RAISE NOTICE '✅ Đã thêm cột workflow_json vào workflow_versions';
    ELSE
        RAISE NOTICE 'ℹ️  Cột workflow_json đã tồn tại';
    END IF;
END $$;

-- =====================================================
-- VERIFY: Kiểm tra kết quả
-- =====================================================

-- Kiểm tra RLS status
SELECT 
    schemaname, 
    tablename, 
    CASE WHEN rowsecurity THEN '🔒 RLS BẬT' ELSE '🔓 RLS TẮT' END as rls_status,
    (SELECT COUNT(*) FROM pg_policies WHERE pg_policies.tablename = pg_tables.tablename) as policies_count
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Kiểm tra cấu trúc workflow_versions
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'workflow_versions'
ORDER BY ordinal_position;
