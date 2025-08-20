-- ArbitrageVault Database Indexes
-- Critical performance indexes for repository layer

-- ============================================================================
-- ANALYSES TABLE INDEXES
-- ============================================================================

-- Primary unique constraint (already exists via model)
-- ALTER TABLE analyses ADD CONSTRAINT uq_batch_isbn UNIQUE (batch_id, isbn_or_asin);

-- Performance indexes for filtering and sorting
CREATE INDEX IF NOT EXISTS idx_analyses_batch_id ON analyses (batch_id);
CREATE INDEX IF NOT EXISTS idx_analyses_roi_percent ON analyses (roi_percent DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_velocity_score ON analyses (velocity_score DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_profit ON analyses (profit DESC);
CREATE INDEX IF NOT EXISTS idx_analyses_bsr ON analyses (bsr ASC);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at DESC);

-- Composite index for balanced strategy (most common query)
CREATE INDEX IF NOT EXISTS idx_analyses_balanced_strategy ON analyses (batch_id, roi_percent DESC, velocity_score DESC);

-- Composite index for golden opportunities (multi-threshold queries)
CREATE INDEX IF NOT EXISTS idx_analyses_golden_ops ON analyses (batch_id, roi_percent DESC, velocity_score DESC, profit DESC);

-- ISBN lookup optimization
CREATE INDEX IF NOT EXISTS idx_analyses_isbn_lookup ON analyses (isbn_or_asin);

-- ============================================================================
-- BATCHES TABLE INDEXES  
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_batches_status ON batches (status);
CREATE INDEX IF NOT EXISTS idx_batches_created_at ON batches (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_batches_finished_at ON batches (finished_at DESC) WHERE finished_at IS NOT NULL;

-- ============================================================================
-- USERS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at DESC);

-- ============================================================================
-- QUERY OPTIMIZATION NOTES
-- ============================================================================

-- idx_analyses_balanced_strategy: Optimizes top_n_for_batch(balanced)
-- idx_analyses_golden_ops: Optimizes count_by_thresholds with multiple criteria
-- idx_analyses_batch_id: Essential for list_filtered base query
-- idx_analyses_roi_percent: Profit Hunter strategy sorting
-- idx_analyses_velocity_score: Velocity strategy sorting
