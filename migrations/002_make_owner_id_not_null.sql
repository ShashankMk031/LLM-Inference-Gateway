-- Migration: Make owner_id NOT NULL after backfill
-- Step 2 of 2: Run ONLY after backfilling owner_id for all existing rows
-- Date: 2026-01-08

-- Verify no NULL values remain (should return 0)
-- SELECT COUNT(*) FROM api_keys WHERE owner_id IS NULL;

-- Alter column to NOT NULL
ALTER TABLE api_keys 
ALTER COLUMN owner_id SET NOT NULL;

-- After this migration, update the model in app/db/base.py:
-- Change: nullable=True  ->  nullable=False
-- Line 23: owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
