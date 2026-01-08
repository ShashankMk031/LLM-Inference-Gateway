-- Migration: Make owner_id NOT NULL after backfill
-- Step 2 of 2: Run ONLY after backfilling owner_id for all existing rows
-- Date: 2026-01-08

-- ============================================================================
-- DEPLOYMENT COORDINATION (CRITICAL)
-- ============================================================================
-- Before running this migration, you MUST update the SQLAlchemy model to match:
--
-- In app/db/base.py, line 23, change:
--   FROM: owner_id: Mapped[int | None] = mapped_column(..., nullable=True, ...)
--   TO:   owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
--
-- Deployment order:
--   1. Verify no NULL values: SELECT COUNT(*) FROM api_keys WHERE owner_id IS NULL; (must be 0)
--   2. Deploy code with nullable=False in the model
--   3. Run this migration immediately after deploy
--
-- OR for rolling deployments:
--   1. Backfill all NULLs (001 migration)
--   2. Deploy code with nullable=False (app tolerates NOT NULL)
--   3. Apply this migration
-- ============================================================================

-- Verify no NULL values remain (should return 0)
-- SELECT COUNT(*) FROM api_keys WHERE owner_id IS NULL;

-- Alter column to NOT NULL
ALTER TABLE api_keys 
ALTER COLUMN owner_id SET NOT NULL;
