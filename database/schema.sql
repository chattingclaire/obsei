-- ============================================================================
-- Multi-Agent Intelligence System - Supabase Database Schema
-- ============================================================================
-- Version: 1.0.0
-- Description: Complete database schema for multi-agent AI pipeline

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- TABLE: raw_items
-- Purpose: Store raw ingested data from all sources
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL,  -- github, twitter, reddit, producthunt, etc.
    source_id VARCHAR(255),  -- Original ID from source
    source_url TEXT,
    title TEXT,
    description TEXT,
    content TEXT,
    author VARCHAR(255),
    author_url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,  -- Flexible storage for source-specific fields
    media JSONB,  -- Images, videos, attachments
    raw_data JSONB,  -- Complete raw response from API
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for raw_items
CREATE INDEX IF NOT EXISTS idx_raw_items_source ON raw_items(source);
CREATE INDEX IF NOT EXISTS idx_raw_items_source_id ON raw_items(source, source_id);
CREATE INDEX IF NOT EXISTS idx_raw_items_processed ON raw_items(processed);
CREATE INDEX IF NOT EXISTS idx_raw_items_ingested_at ON raw_items(ingested_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_items_metadata ON raw_items USING GIN(metadata);

-- ============================================================================
-- TABLE: classified_items
-- Purpose: Store classified and categorized items
-- ============================================================================
CREATE TABLE IF NOT EXISTS classified_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_item_id UUID REFERENCES raw_items(id) ON DELETE CASCADE,

    -- Classification results
    category_l1 VARCHAR(50),  -- e.g., TECH, BIZ, CONS, EMERG
    category_l2 VARCHAR(50),  -- e.g., AI_ML, WEB3, FINTECH
    category_l3 VARCHAR(50),  -- e.g., GEN_AI, DEFI, PAY

    -- Multi-category support
    categories JSONB,  -- Array of {l1, l2, l3, confidence}

    confidence FLOAT,
    classification_metadata JSONB,

    -- Enriched fields
    title TEXT,
    summary TEXT,
    keywords TEXT[],
    tags TEXT[],

    -- Source reference
    source VARCHAR(50),
    source_url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,

    -- Processing metadata
    classified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    classifier_version VARCHAR(20),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for classified_items
CREATE INDEX IF NOT EXISTS idx_classified_items_raw_item_id ON classified_items(raw_item_id);
CREATE INDEX IF NOT EXISTS idx_classified_items_categories ON classified_items(category_l1, category_l2, category_l3);
CREATE INDEX IF NOT EXISTS idx_classified_items_confidence ON classified_items(confidence);
CREATE INDEX IF NOT EXISTS idx_classified_items_classified_at ON classified_items(classified_at DESC);
CREATE INDEX IF NOT EXISTS idx_classified_items_categories_jsonb ON classified_items USING GIN(categories);
CREATE INDEX IF NOT EXISTS idx_classified_items_keywords ON classified_items USING GIN(keywords);

-- ============================================================================
-- TABLE: founders
-- Purpose: Track founder information and profiles
-- ============================================================================
CREATE TABLE IF NOT EXISTS founders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),

    -- Background
    ethnicity VARCHAR(100),  -- e.g., Chinese, Overseas Chinese
    nationality VARCHAR(100),
    location VARCHAR(255),

    -- Professional info
    current_company VARCHAR(255),
    current_role VARCHAR(255),
    linkedin_url TEXT,
    twitter_url TEXT,
    github_url TEXT,

    -- Experience
    previous_companies JSONB,  -- Array of {company, role, years}
    education JSONB,  -- Array of {school, degree, year}

    -- Reputation metrics
    github_stars INTEGER DEFAULT 0,
    twitter_followers INTEGER DEFAULT 0,
    linkedin_connections INTEGER DEFAULT 0,

    -- Metadata
    bio TEXT,
    expertise TEXT[],
    notable_projects JSONB,

    -- Tracking
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(email)
);

-- Indexes for founders
CREATE INDEX IF NOT EXISTS idx_founders_ethnicity ON founders(ethnicity);
CREATE INDEX IF NOT EXISTS idx_founders_current_company ON founders(current_company);
CREATE INDEX IF NOT EXISTS idx_founders_github_stars ON founders(github_stars DESC);
CREATE INDEX IF NOT EXISTS idx_founders_expertise ON founders USING GIN(expertise);

-- ============================================================================
-- TABLE: signals
-- Purpose: Store generated signals (Xiaohongshu format + RSS)
-- ============================================================================
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    classified_item_id UUID REFERENCES classified_items(id) ON DELETE CASCADE,

    -- Signal content
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,

    -- Xiaohongshu format
    xhs_title VARCHAR(100),
    xhs_content TEXT,
    xhs_hashtags TEXT[],
    xhs_images TEXT[],

    -- RSS fields
    rss_guid VARCHAR(255) UNIQUE,
    rss_link TEXT,
    rss_pub_date TIMESTAMP WITH TIME ZONE,

    -- Enrichment data
    verified_info JSONB,  -- Browser search verification results
    founder_id UUID REFERENCES founders(id),
    github_metadata JSONB,
    producthunt_metadata JSONB,
    twitter_metadata JSONB,
    crunchbase_metadata JSONB,

    -- Signal quality
    signal_score FLOAT,  -- 0-1 score of signal quality
    signal_type VARCHAR(50),  -- trending, funding, launch, etc.

    -- Metadata
    enrichment_sources TEXT[],
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for signals
CREATE INDEX IF NOT EXISTS idx_signals_classified_item_id ON signals(classified_item_id);
CREATE INDEX IF NOT EXISTS idx_signals_founder_id ON signals(founder_id);
CREATE INDEX IF NOT EXISTS idx_signals_signal_type ON signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_signal_score ON signals(signal_score DESC);
CREATE INDEX IF NOT EXISTS idx_signals_published ON signals(published);
CREATE INDEX IF NOT EXISTS idx_signals_generated_at ON signals(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_signals_xhs_hashtags ON signals USING GIN(xhs_hashtags);

-- ============================================================================
-- TABLE: insights
-- Purpose: Store weekly/periodic long-form insights
-- ============================================================================
CREATE TABLE IF NOT EXISTS insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Insight metadata
    title TEXT NOT NULL,
    subtitle TEXT,
    insight_type VARCHAR(50),  -- weekly, monthly, quarterly, thematic

    -- Content
    content TEXT NOT NULL,  -- Full markdown content
    executive_summary TEXT,
    key_findings JSONB,  -- Array of key findings

    -- Data analysis
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    items_analyzed INTEGER,
    categories_covered JSONB,

    -- Trends
    trending_topics TEXT[],
    emerging_patterns JSONB,
    notable_mentions JSONB,  -- Companies, founders, technologies

    -- USD fund style
    investment_themes JSONB,
    market_opportunities JSONB,

    -- Metadata
    generated_by VARCHAR(50) DEFAULT 'insight_agent',
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP WITH TIME ZONE,

    -- Analytics
    view_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for insights
CREATE INDEX IF NOT EXISTS idx_insights_insight_type ON insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_period ON insights(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_insights_generated_at ON insights(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_insights_published ON insights(published);
CREATE INDEX IF NOT EXISTS idx_insights_trending_topics ON insights USING GIN(trending_topics);

-- ============================================================================
-- TABLE: investments
-- Purpose: Track investment intelligence and opportunities
-- ============================================================================
CREATE TABLE IF NOT EXISTS investments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Company info
    company_name VARCHAR(255) NOT NULL,
    company_url TEXT,
    company_description TEXT,

    -- Founder info
    founder_id UUID REFERENCES founders(id),
    founder_names TEXT[],
    founder_backgrounds JSONB,  -- Array of {name, ethnicity, background}

    -- Funding details
    funding_stage VARCHAR(50),  -- pre-seed, seed, series-a, etc.
    funding_amount_usd DECIMAL(15, 2),
    funding_date TIMESTAMP WITH TIME ZONE,
    lead_investors TEXT[],
    all_investors TEXT[],

    -- Market analysis
    category_l1 VARCHAR(50),
    category_l2 VARCHAR(50),
    category_l3 VARCHAR(50),
    market_size_usd DECIMAL(15, 2),

    -- Scoring
    investability_score FLOAT,  -- 0-1 composite score
    scoring_factors JSONB,  -- Breakdown of scoring

    -- Intelligence
    unique_insights TEXT[],
    competitive_landscape JSONB,
    technology_assessment TEXT,
    team_assessment TEXT,
    traction_metrics JSONB,

    -- Benchmarking
    similar_companies JSONB,  -- Array of comparable companies
    benchmark_metrics JSONB,

    -- Metadata
    data_sources TEXT[],
    confidence_level VARCHAR(20),  -- high, medium, low
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Tracking
    flagged_for_review BOOLEAN DEFAULT FALSE,
    review_notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for investments
CREATE INDEX IF NOT EXISTS idx_investments_founder_id ON investments(founder_id);
CREATE INDEX IF NOT EXISTS idx_investments_funding_stage ON investments(funding_stage);
CREATE INDEX IF NOT EXISTS idx_investments_investability_score ON investments(investability_score DESC);
CREATE INDEX IF NOT EXISTS idx_investments_funding_date ON investments(funding_date DESC);
CREATE INDEX IF NOT EXISTS idx_investments_category ON investments(category_l1, category_l2, category_l3);
CREATE INDEX IF NOT EXISTS idx_investments_flagged ON investments(flagged_for_review);

-- ============================================================================
-- TABLE: agent_status
-- Purpose: Track agent health, heartbeats, and metrics
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(50) NOT NULL,

    -- Status
    status VARCHAR(20) NOT NULL,  -- running, idle, error, stopped
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metrics
    processed_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,

    -- Timing
    last_run_timestamp TIMESTAMP WITH TIME ZONE,
    last_run_duration_seconds INTEGER,
    average_run_duration_seconds INTEGER,

    -- Errors
    last_error TEXT,
    error_message TEXT,
    error_stack TEXT,

    -- Payload
    payload JSONB,  -- Agent-specific metadata and state

    -- Performance
    items_per_second FLOAT,
    cache_hit_rate FLOAT,
    api_calls_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(agent_name)
);

-- Indexes for agent_status
CREATE INDEX IF NOT EXISTS idx_agent_status_agent_name ON agent_status(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_status_status ON agent_status(status);
CREATE INDEX IF NOT EXISTS idx_agent_status_last_heartbeat ON agent_status(last_heartbeat DESC);

-- ============================================================================
-- TABLE: agent_logs
-- Purpose: Detailed logging for all agent activities
-- ============================================================================
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_name VARCHAR(50) NOT NULL,

    -- Log details
    log_level VARCHAR(20),  -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    message TEXT NOT NULL,

    -- Context
    operation VARCHAR(100),  -- e.g., fetch_github, classify_item, generate_signal
    item_id UUID,  -- Reference to related item

    -- Metadata
    metadata JSONB,
    duration_ms INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for agent_logs
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_name ON agent_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_log_level ON agent_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_agent_logs_created_at ON agent_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_operation ON agent_logs(operation);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_raw_items_updated_at BEFORE UPDATE ON raw_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classified_items_updated_at BEFORE UPDATE ON classified_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_founders_updated_at BEFORE UPDATE ON founders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_signals_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_insights_updated_at BEFORE UPDATE ON insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_investments_updated_at BEFORE UPDATE ON investments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_status_updated_at BEFORE UPDATE ON agent_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) - Optional but recommended
-- ============================================================================

-- Enable RLS on tables
ALTER TABLE raw_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE classified_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE founders ENABLE ROW LEVEL SECURITY;
ALTER TABLE signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE investments ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Create policies (allow all for service role, restrict for anon)
CREATE POLICY "Allow service role all" ON raw_items FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON classified_items FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON founders FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON signals FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON insights FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON investments FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON agent_status FOR ALL TO service_role USING (true);
CREATE POLICY "Allow service role all" ON agent_logs FOR ALL TO service_role USING (true);

-- Public read-only policies for published content
CREATE POLICY "Public read published signals" ON signals FOR SELECT TO anon USING (published = true);
CREATE POLICY "Public read published insights" ON insights FOR SELECT TO anon USING (published = true);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View: Recent signals with full context
CREATE OR REPLACE VIEW v_recent_signals AS
SELECT
    s.*,
    ci.category_l1,
    ci.category_l2,
    ci.category_l3,
    ci.summary AS classified_summary,
    f.name AS founder_name,
    f.ethnicity AS founder_ethnicity
FROM signals s
LEFT JOIN classified_items ci ON s.classified_item_id = ci.id
LEFT JOIN founders f ON s.founder_id = f.id
ORDER BY s.generated_at DESC;

-- View: Agent health dashboard
CREATE OR REPLACE VIEW v_agent_health AS
SELECT
    agent_name,
    status,
    last_heartbeat,
    NOW() - last_heartbeat AS time_since_heartbeat,
    processed_count,
    error_count,
    success_count,
    CASE
        WHEN success_count + error_count > 0
        THEN (success_count::FLOAT / (success_count + error_count)) * 100
        ELSE 0
    END AS success_rate_percent,
    last_run_duration_seconds,
    items_per_second,
    cache_hit_rate
FROM agent_status
ORDER BY agent_name;

-- View: Investment pipeline
CREATE OR REPLACE VIEW v_investment_pipeline AS
SELECT
    i.*,
    f.name AS founder_name,
    f.linkedin_url AS founder_linkedin,
    f.github_url AS founder_github
FROM investments i
LEFT JOIN founders f ON i.founder_id = f.id
WHERE i.investability_score >= 0.7
ORDER BY i.investability_score DESC, i.funding_date DESC;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Initialize agent_status entries for all agents
INSERT INTO agent_status (agent_name, status, processed_count) VALUES
    ('data_agent', 'idle', 0),
    ('classify_agent', 'idle', 0),
    ('signal_agent', 'idle', 0),
    ('insight_agent', 'idle', 0),
    ('venture_agent', 'idle', 0)
ON CONFLICT (agent_name) DO NOTHING;

-- ============================================================================
-- MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to cleanup old logs
CREATE OR REPLACE FUNCTION cleanup_old_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM agent_logs
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to archive old raw_items
CREATE OR REPLACE FUNCTION archive_old_raw_items(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- In production, move to archive table instead of delete
    DELETE FROM raw_items
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND processed = true;

    GET DIAGNOSTICS archived_count = ROW_COUNT;
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- GRANTS (adjust based on your security requirements)
-- ============================================================================

-- Grant appropriate permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON v_recent_signals, v_investment_pipeline TO anon;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
