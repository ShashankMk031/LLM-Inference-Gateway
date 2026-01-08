-- Migration: Add owner_id column (nullable) to api_keys table
-- Step 1 of 2: Safe migration that doesn't break existing data
-- Date: 2026-01-08

-- Add the owner_id column as nullable first
ALTER TABLE api_keys 
ADD COLUMN owner_id INTEGER NULL;

-- Add foreign key constraint
ALTER TABLE api_keys 
ADD CONSTRAINT fk_api_keys_owner_id 
FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add index for performance
CREATE INDEX ix_api_keys_owner_id ON api_keys(owner_id);

-- ============================================================================
-- BACKFILL STEP (run this before step 2)
-- ============================================================================
-- Option A: Assign all existing keys to a specific admin user (e.g., user_id = 1)
-- UPDATE api_keys SET owner_id = 1 WHERE owner_id IS NULL;

-- Option B: Delete orphaned keys (if they should not exist without an owner)
-- DELETE FROM api_keys WHERE owner_id IS NULL;

-- Option C: Assign based on some business logic (e.g., first active user)
-- UPDATE api_keys SET owner_id = (SELECT id FROM users WHERE is_active = true LIMIT 1) WHERE owner_id IS NULL;

-- After backfill, run 002_make_owner_id_not_null.sql
