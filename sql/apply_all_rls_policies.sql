-- =====================================================
-- RLS POLICIES CHO TẤT CẢ CÁC BẢNG
-- Chạy script này trong Supabase SQL Editor
-- =====================================================

-- ACCOUNTS
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public registration" ON accounts;
CREATE POLICY "Allow public registration" 
ON accounts FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow email check" ON accounts;
CREATE POLICY "Allow email check" 
ON accounts FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can update own account" ON accounts;
CREATE POLICY "Users can update own account" 
ON accounts FOR UPDATE 
USING (id::text = current_setting('request.jwt.claims', true)::json->>'sub');

DROP POLICY IF EXISTS "Only admins can delete accounts" ON accounts;
CREATE POLICY "Only admins can delete accounts" 
ON accounts FOR DELETE 
USING ((current_setting('request.jwt.claims', true)::json->>'role') = 'admin');

-- WORKFLOWS
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

-- WORKFLOW_VERSIONS
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

-- CALLS
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

-- CONVERSATION_LOGS
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
ON conversation_logs FOR INSERT WITH CHECK (true);

-- CALL_INTENTS
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
ON call_intents FOR INSERT WITH CHECK (true);

-- CALL_ENTITIES
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
ON call_entities FOR INSERT WITH CHECK (true);

-- FEEDBACK
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

-- REPORTS
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
ON reports FOR INSERT WITH CHECK (true);
