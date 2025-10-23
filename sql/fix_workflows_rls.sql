-- Fix RLS policies cho workflows và workflow_versions
-- Chạy script này trong Supabase SQL Editor

-- 1. Enable RLS (nếu chưa enable)
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_versions ENABLE ROW LEVEL SECURITY;

-- 2. Drop policies cũ (nếu có)
DROP POLICY IF EXISTS "workflows_insert_own" ON workflows;
DROP POLICY IF EXISTS "workflows_select_own" ON workflows;
DROP POLICY IF EXISTS "workflows_update_own" ON workflows;
DROP POLICY IF EXISTS "workflows_delete_own" ON workflows;

DROP POLICY IF EXISTS "workflow_versions_insert_own" ON workflow_versions;
DROP POLICY IF EXISTS "workflow_versions_select_own" ON workflow_versions;
DROP POLICY IF EXISTS "workflow_versions_update_own" ON workflow_versions;
DROP POLICY IF EXISTS "workflow_versions_delete_own" ON workflow_versions;

-- 3. Tạo policies mới cho workflows
CREATE POLICY "workflows_insert_own" 
ON workflows FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "workflows_select_own" 
ON workflows FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "workflows_update_own" 
ON workflows FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "workflows_delete_own" 
ON workflows FOR DELETE 
USING (auth.uid() = user_id);

-- 4. Tạo policies mới cho workflow_versions
CREATE POLICY "workflow_versions_insert_own" 
ON workflow_versions FOR INSERT 
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "workflow_versions_select_own" 
ON workflow_versions FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "workflow_versions_update_own" 
ON workflow_versions FOR UPDATE 
USING (auth.uid() = user_id);

CREATE POLICY "workflow_versions_delete_own" 
ON workflow_versions FOR DELETE 
USING (auth.uid() = user_id);

-- 5. Kiểm tra lại
SELECT schemaname, tablename, policyname 
FROM pg_policies 
WHERE tablename IN ('workflows', 'workflow_versions')
ORDER BY tablename, policyname;
