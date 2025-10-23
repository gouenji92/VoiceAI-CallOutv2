-- Migration: Add RL feedback tracking table
-- Purpose: Store reward signals for reinforcement learning threshold tuning

-- RL feedback table for threshold optimization
CREATE TABLE IF NOT EXISTS rl_feedback (
    id BIGSERIAL PRIMARY KEY,
    call_id TEXT NOT NULL,
    reward FLOAT NOT NULL,  -- +1 (success), 0 (neutral), -1 (fail)
    final_intent TEXT,      -- Corrected intent if user provided feedback
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS idx_rl_feedback_call_id ON rl_feedback(call_id);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_created_at ON rl_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_rl_feedback_reward ON rl_feedback(reward);

-- Comments
COMMENT ON TABLE rl_feedback IS 'Reward feedback for RL-based threshold tuning';
COMMENT ON COLUMN rl_feedback.reward IS 'Reward signal: +1=success, 0=neutral, -1=fail';
COMMENT ON COLUMN rl_feedback.final_intent IS 'User-corrected intent if different from predicted';
