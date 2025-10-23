-- Supabase / PostgreSQL schema for VoiceAI
-- Run in Supabase SQL editor or psql. Requires pgcrypto for gen_random_uuid().

-- Enable extension for UUID generation (Supabase usually enables pgcrypto)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Accounts / Users
CREATE TABLE IF NOT EXISTS accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    role text DEFAULT 'user',
    created_at timestamptz DEFAULT now()
);

-- Workflows (projects)
CREATE TABLE IF NOT EXISTS workflows (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES accounts(id) ON DELETE SET NULL,
    name text NOT NULL,
    description text,
    current_version_id uuid,
    created_at timestamptz DEFAULT now()
);

-- Workflow versions (history)
CREATE TABLE IF NOT EXISTS workflow_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES workflows(id) ON DELETE CASCADE,
    user_id uuid REFERENCES accounts(id) ON DELETE SET NULL,
    workflow_json jsonb NOT NULL,
    change_description text,
    created_at timestamptz DEFAULT now()
);

-- Calls
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

-- Conversation logs
CREATE TABLE IF NOT EXISTS conversation_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE CASCADE,
    speaker text NOT NULL,
    text text NOT NULL,
    intent text,
    confidence double precision,
    created_at timestamptz DEFAULT now()
);

-- Call intents summary (per call)
CREATE TABLE IF NOT EXISTS call_intents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE CASCADE,
    intent_name text NOT NULL,
    count integer DEFAULT 1,
    accuracy double precision
);

-- Call entities (extracted slots)
CREATE TABLE IF NOT EXISTS call_entities (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    call_id uuid REFERENCES calls(id) ON DELETE CASCADE,
    entity_name text NOT NULL,
    value text
);

-- Feedback (low confidence / user corrections)
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

-- Reports (aggregates)
CREATE TABLE IF NOT EXISTS reports (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id uuid REFERENCES workflows(id) ON DELETE CASCADE,
    total_calls integer DEFAULT 0,
    success_rate double precision,
    avg_duration double precision,
    positive_intent_rate double precision,
    created_at timestamptz DEFAULT now()
);

-- Indexes to speed queries
CREATE INDEX IF NOT EXISTS idx_calls_workflow_id ON calls(workflow_id);
CREATE INDEX IF NOT EXISTS idx_convlogs_call_id ON conversation_logs(call_id);
CREATE INDEX IF NOT EXISTS idx_feedback_call_id ON feedback(call_id);

-- Row Level Security Policies
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

-- =====================================================
-- RLS POLICIES CHO CÁC BẢNG KHÁC
-- =====================================================

-- WORKFLOWS: User chỉ thấy và quản lý workflow của mình
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own workflows" ON workflows;
CREATE POLICY "Users can view own workflows"
ON workflows FOR SELECT
USING (user_id::text = current_setting('request.jwt.claims', true)::json->>'sub');

DROP POLICY IF EXISTS "Users can create workflows" ON workflows;
CREATE POLICY "Users can create workflows"
ON workflows FOR INSERT
WITH CHECK (user_id::text = current_setting('request.jwt.claims', true)::json->>'sub');

DROP POLICY IF EXISTS "Users can update own workflows" ON workflows;
CREATE POLICY "Users can update own workflows"
ON workflows FOR UPDATE
USING (user_id::text = current_setting('request.jwt.claims', true)::json->>'sub');

DROP POLICY IF EXISTS "Users can delete own workflows" ON workflows;
CREATE POLICY "Users can delete own workflows"
ON workflows FOR DELETE
USING (user_id::text = current_setting('request.jwt.claims', true)::json->>'sub');

-- WORKFLOW_VERSIONS: User chỉ thấy versions của workflow mình sở hữu
ALTER TABLE workflow_versions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own workflow versions" ON workflow_versions;
CREATE POLICY "Users can view own workflow versions"
ON workflow_versions FOR SELECT
USING (
  workflow_id IN (
    SELECT id FROM workflows WHERE user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "Users can create workflow versions" ON workflow_versions;
CREATE POLICY "Users can create workflow versions"
ON workflow_versions FOR INSERT
WITH CHECK (
  workflow_id IN (
    SELECT id FROM workflows WHERE user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

-- CALLS: User chỉ thấy calls của workflows mình sở hữu
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own calls" ON calls;
CREATE POLICY "Users can view own calls"
ON calls FOR SELECT
USING (
  workflow_id IN (
    SELECT id FROM workflows WHERE user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "Users can create calls" ON calls;
CREATE POLICY "Users can create calls"
ON calls FOR INSERT
WITH CHECK (
  workflow_id IN (
    SELECT id FROM workflows WHERE user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "Users can update own calls" ON calls;
CREATE POLICY "Users can update own calls"
ON calls FOR UPDATE
USING (
  workflow_id IN (
    SELECT id FROM workflows WHERE user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

-- CONVERSATION_LOGS: User chỉ thấy logs của calls thuộc workflow mình
ALTER TABLE conversation_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own conversation logs" ON conversation_logs;
CREATE POLICY "Users can view own conversation logs"
ON conversation_logs FOR SELECT
USING (
  call_id IN (
    SELECT c.id FROM calls c
    JOIN workflows w ON c.workflow_id = w.id
    WHERE w.user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "System can insert conversation logs" ON conversation_logs;
CREATE POLICY "System can insert conversation logs"
ON conversation_logs FOR INSERT
WITH CHECK (true);  -- Cho phép system tự động log

-- CALL_INTENTS: User chỉ thấy intents của calls mình
ALTER TABLE call_intents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own call intents" ON call_intents;
CREATE POLICY "Users can view own call intents"
ON call_intents FOR SELECT
USING (
  call_id IN (
    SELECT c.id FROM calls c
    JOIN workflows w ON c.workflow_id = w.id
    WHERE w.user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "System can insert call intents" ON call_intents;
CREATE POLICY "System can insert call intents"
ON call_intents FOR INSERT
WITH CHECK (true);

-- CALL_ENTITIES: User chỉ thấy entities của calls mình
ALTER TABLE call_entities ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own call entities" ON call_entities;
CREATE POLICY "Users can view own call entities"
ON call_entities FOR SELECT
USING (
  call_id IN (
    SELECT c.id FROM calls c
    JOIN workflows w ON c.workflow_id = w.id
    WHERE w.user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "System can insert call entities" ON call_entities;
CREATE POLICY "System can insert call entities"
ON call_entities FOR INSERT
WITH CHECK (true);

-- FEEDBACK: User thấy feedback của mình, Admin thấy tất cả
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own feedback" ON feedback;
CREATE POLICY "Users can view own feedback"
ON feedback FOR SELECT
USING (
  user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  OR (current_setting('request.jwt.claims', true)::json->>'role') = 'admin'
);

DROP POLICY IF EXISTS "Users can create feedback" ON feedback;
CREATE POLICY "Users can create feedback"
ON feedback FOR INSERT
WITH CHECK (user_id::text = current_setting('request.jwt.claims', true)::json->>'sub');

DROP POLICY IF EXISTS "Admins can update feedback" ON feedback;
CREATE POLICY "Admins can update feedback"
ON feedback FOR UPDATE
USING ((current_setting('request.jwt.claims', true)::json->>'role') = 'admin');

-- REPORTS: User chỉ thấy reports của workflows mình
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own reports" ON reports;
CREATE POLICY "Users can view own reports"
ON reports FOR SELECT
USING (
  workflow_id IN (
    SELECT id FROM workflows WHERE user_id::text = current_setting('request.jwt.claims', true)::json->>'sub'
  )
);

DROP POLICY IF EXISTS "System can insert reports" ON reports;
CREATE POLICY "System can insert reports"
ON reports FOR INSERT
WITH CHECK (true);

-- End of schema
