-- Reference PostgreSQL 16 Schema for Real-Time Multi-Modal Trade Intelligence Platform
-- (The app creates these tables automatically via SQLAlchemy on startup; this file is for reference/DBA review.)

CREATE TABLE IF NOT EXISTS stakeholder_configs (
    id SERIAL PRIMARY KEY,
    stakeholder_code VARCHAR(64) UNIQUE NOT NULL,
    ministry_name VARCHAR(255) NOT NULL,
    priority_sectors JSONB NOT NULL DEFAULT '[]'::jsonb,
    key_counterpart_markets JSONB NOT NULL DEFAULT '[]'::jsonb,
    bilateral_goals JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_tolerance VARCHAR(32) NOT NULL DEFAULT 'MODERATE',
    min_confidence_for_escalation DOUBLE PRECISION NOT NULL DEFAULT 0.65,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_signals (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    raw_content TEXT NOT NULL,
    feed_source VARCHAR(120) NOT NULL,
    commodity VARCHAR(120),
    hs_chapter VARCHAR(32),
    affected_market VARCHAR(120),
    precursor_type VARCHAR(120),
    prob_30d DOUBLE PRECISION,
    prob_90d DOUBLE PRECISION,
    source_links JSONB NOT NULL DEFAULT '[]'::jsonb,
    implication_summary TEXT,
    preliminary_confidence DOUBLE PRECISION,
    status VARCHAR(48) NOT NULL DEFAULT 'INGESTED',
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS multimodal_evidence (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES raw_signals(id) ON DELETE CASCADE,
    modality VARCHAR(48) NOT NULL,
    mime_type VARCHAR(64) NOT NULL DEFAULT 'image/png',
    uri_or_path TEXT NOT NULL,
    caption TEXT,
    sha256_hash VARCHAR(64),
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS satellite_metadata (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES raw_signals(id) ON DELETE CASCADE,
    provider VARCHAR(64) NOT NULL,
    region_name VARCHAR(160) NOT NULL,
    bbox JSONB NOT NULL,
    metric_type VARCHAR(64) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    baseline_delta_pct DOUBLE PRECISION NOT NULL,
    cloud_cover_pct DOUBLE PRECISION NOT NULL DEFAULT 5.0,
    imagery_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.85,
    preview_image_url TEXT,
    acquired_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS verification_results (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER UNIQUE NOT NULL REFERENCES raw_signals(id) ON DELETE CASCADE,
    core_claims JSONB NOT NULL DEFAULT '[]'::jsonb,
    verified_status VARCHAR(48) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    key_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    multimodal_evaluation TEXT NOT NULL,
    remaining_uncertainties JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendation VARCHAR(32) NOT NULL,
    verified_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS executive_briefs (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES raw_signals(id) ON DELETE CASCADE,
    stakeholder_code VARCHAR(64) NOT NULL,
    headline VARCHAR(300) NOT NULL,
    alignment_score INTEGER NOT NULL,
    priority_level VARCHAR(32) NOT NULL,
    matching_strategic_elements JSONB NOT NULL DEFAULT '[]'::jsonb,
    alignment_rationale TEXT NOT NULL,
    what_changed TEXT NOT NULL,
    quantified_window TEXT NOT NULL,
    strategic_alignment_section TEXT NOT NULL,
    recommended_next_steps JSONB NOT NULL DEFAULT '{}'::jsonb,
    risks_and_mitigations JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_score DOUBLE PRECISION NOT NULL,
    main_uncertainties JSONB NOT NULL DEFAULT '[]'::jsonb,
    provenance JSONB NOT NULL DEFAULT '[]'::jsonb,
    markdown_brief TEXT NOT NULL,
    requires_human_review BOOLEAN NOT NULL DEFAULT TRUE,
    review_status VARCHAR(48) NOT NULL DEFAULT 'PENDING_HUMAN_REVIEW',
    reviewed_by VARCHAR(120),
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    actor VARCHAR(120) NOT NULL,
    action VARCHAR(120) NOT NULL,
    entity_type VARCHAR(64) NOT NULL,
    entity_id INTEGER NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
