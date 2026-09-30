-- Supabase Migration: Initial Schema for Social Intelligence & Risk Scoring Platform
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. PROFILES & ROLES
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'analyst' CHECK (role IN ('analyst', 'reviewer', 'admin')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. AUTHORS (Salted SHA-256 Identifiers)
CREATE TABLE IF NOT EXISTS public.authors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author_id_hash TEXT UNIQUE NOT NULL,
    author_handle_hash TEXT,
    platform TEXT NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    post_count INT NOT NULL DEFAULT 1,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_authors_platform ON public.authors(platform);
CREATE INDEX IF NOT EXISTS idx_authors_id_hash ON public.authors(author_id_hash);

-- 3. POSTS (Canonical Normalized Clean Post Store)
CREATE TABLE IF NOT EXISTS public.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform TEXT NOT NULL,
    post_id TEXT NOT NULL,
    author_id_hash TEXT NOT NULL,
    author_handle_hash TEXT,
    text TEXT NOT NULL,
    lang TEXT,
    tokens JSONB NOT NULL DEFAULT '[]'::jsonb,
    entities JSONB NOT NULL DEFAULT '[]'::jsonb,
    spam_score FLOAT NOT NULL DEFAULT 0.0,
    text_hash TEXT,
    is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
    url TEXT,
    engagement JSONB NOT NULL DEFAULT '{"likes": 0, "shares": 0, "replies": 0}'::jsonb,
    parent_id TEXT,
    raw_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_posts_platform_post_id UNIQUE (platform, post_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_platform_created ON public.posts(platform, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_created_brin ON public.posts USING brin(created_at);
CREATE INDEX IF NOT EXISTS idx_posts_text_hash ON public.posts(text_hash);
CREATE INDEX IF NOT EXISTS idx_posts_author_hash ON public.posts(author_id_hash);
CREATE INDEX IF NOT EXISTS idx_posts_fts ON public.posts USING gin(to_tsvector('english', text));

-- 4. POST FEATURES & PGVECTOR EMBEDDINGS
CREATE TABLE IF NOT EXISTS public.post_features (
    post_id UUID PRIMARY KEY REFERENCES public.posts(id) ON DELETE CASCADE,
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'post_features' AND indexname = 'idx_post_features_embedding'
    ) THEN
        CREATE INDEX idx_post_features_embedding ON public.post_features USING hnsw (embedding vector_cosine_ops);
    END IF;
EXCEPTION WHEN OTHERS THEN
    -- Fallback to ivfflat if hnsw is unavailable in older pgvector versions
    CREATE INDEX IF NOT EXISTS idx_post_features_embedding ON public.post_features USING ivfflat (embedding vector_cosine_ops);
END $$;

-- 5. ANALYSIS RESULTS (Engines: sentiment, demographics, trend, network)
CREATE TABLE IF NOT EXISTS public.analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    engine_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_analysis_results_post_engine ON public.analysis_results(post_id, engine_type);
CREATE INDEX IF NOT EXISTS idx_analysis_results_created ON public.analysis_results(created_at DESC);

-- 6. RISK SCORES & SHAP EXPLANATIONS
CREATE TABLE IF NOT EXISTS public.risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('post', 'author', 'cluster')),
    entity_id TEXT NOT NULL,
    risk_score FLOAT NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_band TEXT NOT NULL CHECK (risk_band IN ('Low', 'Medium', 'High')),
    confidence FLOAT NOT NULL,
    shap_drivers JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation TEXT,
    model_version TEXT NOT NULL DEFAULT 'v1.0.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_risk_scores_entity ON public.risk_scores(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_risk_scores_band_created ON public.risk_scores(risk_band, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_scores_score_desc ON public.risk_scores(risk_score DESC);

-- 7. CASES & INVESTIGATION WORKFLOW
CREATE TABLE IF NOT EXISTS public.cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'investigating', 'review', 'closed_confirmed', 'closed_dismissed')),
    priority TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    created_by UUID,
    assigned_to UUID,
    reviewer_approved BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cases_status ON public.cases(status);
CREATE INDEX IF NOT EXISTS idx_cases_updated ON public.cases(updated_at DESC);

CREATE TABLE IF NOT EXISTS public.case_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
    item_type TEXT NOT NULL CHECK (item_type IN ('post', 'author', 'cluster', 'evidence')),
    item_id TEXT NOT NULL,
    added_by UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_case_items UNIQUE (case_id, item_type, item_id)
);

CREATE TABLE IF NOT EXISTS public.case_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES public.cases(id) ON DELETE CASCADE,
    author_id UUID,
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. EVIDENCE INTEGRITY & TAMPER CHECKS
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    source_url TEXT,
    content_snapshot TEXT,
    sha256 TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_evidence_sha256 ON public.evidence_items(sha256);
CREATE INDEX IF NOT EXISTS idx_evidence_entity ON public.evidence_items(entity_type, entity_id);

-- 9. INSERT-ONLY HASH-CHAINED AUDIT LOG
CREATE TABLE IF NOT EXISTS public.audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    prev_hash TEXT,
    row_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_audit_log_target ON public.audit_log(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON public.audit_log(created_at DESC);

-- Revoke UPDATE and DELETE on audit_log for security
REVOKE UPDATE, DELETE, TRUNCATE ON public.audit_log FROM PUBLIC;
REVOKE UPDATE, DELETE, TRUNCATE ON public.audit_log FROM anon, authenticated;

-- Hard trigger to prevent UPDATE/DELETE on audit_log even if permissions bypass
CREATE OR REPLACE FUNCTION public.block_audit_log_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log entries are strictly immutable and cannot be updated or deleted.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_log_immutable ON public.audit_log;
CREATE TRIGGER trg_audit_log_immutable
BEFORE UPDATE OR DELETE ON public.audit_log
FOR EACH ROW EXECUTE FUNCTION public.block_audit_log_mutation();

-- 10. MERKLE ROOTS
CREATE TABLE IF NOT EXISTS public.merkle_roots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    root_hash TEXT NOT NULL,
    leaf_count INT NOT NULL,
    case_id UUID REFERENCES public.cases(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_merkle_roots_case ON public.merkle_roots(case_id);

-- 11. MATERIALIZED VIEWS (Continuous Aggregate Replacements)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_hourly_post_volume AS
SELECT
    date_trunc('hour', created_at) AS hour_bucket,
    platform,
    count(*)::int AS post_count,
    sum(case when spam_score > 0.7 then 1 else 0 end)::int AS spam_count,
    sum(case when is_duplicate then 1 else 0 end)::int AS duplicate_count
FROM public.posts
GROUP BY 1, 2
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_hourly_post_volume ON public.mv_hourly_post_volume(hour_bucket, platform);

CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_hourly_sentiment AS
SELECT
    date_trunc('hour', p.created_at) AS hour_bucket,
    p.platform,
    coalesce(ar.payload->>'sentiment', 'neutral') AS sentiment_label,
    count(*)::int AS count
FROM public.posts p
LEFT JOIN public.analysis_results ar ON ar.post_id = p.id AND ar.engine_type = 'sentiment'
GROUP BY 1, 2, 3
WITH NO DATA;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_hourly_sentiment ON public.mv_hourly_sentiment(hour_bucket, platform, sentiment_label);

-- 12. VECTOR SIMILARITY SEARCH FUNCTION
CREATE OR REPLACE FUNCTION public.match_posts(
    query_embedding vector(384),
    match_threshold float,
    match_count int
)
RETURNS TABLE (
    post_id UUID,
    similarity float,
    platform TEXT,
    text TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
    SELECT
        p.id AS post_id,
        1 - (pf.embedding <=> query_embedding) AS similarity,
        p.platform,
        p.text,
        p.created_at
    FROM public.post_features pf
    JOIN public.posts p ON p.id = pf.post_id
    WHERE pf.embedding IS NOT NULL
      AND 1 - (pf.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;

-- 13. ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.authors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.post_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.merkle_roots ENABLE ROW LEVEL SECURITY;

-- Helper to extract current user role from JWT or profiles table
CREATE OR REPLACE FUNCTION public.get_auth_role()
RETURNS TEXT AS $$
    SELECT coalesce(
        nullif(current_setting('request.jwt.claim.role', true), ''),
        (SELECT role FROM public.profiles WHERE id = auth.uid()),
        'anon'
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- Profiles: Authenticated users can view; users can update own profile
CREATE POLICY "Profiles viewable by authenticated users"
ON public.profiles FOR SELECT TO authenticated USING (true);

CREATE POLICY "Users can update own profile"
ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id);

-- Posts, Authors, Features, Analytics, Risk Scores: Analysts, Reviewers, Admins can read
CREATE POLICY "Posts viewable by analysts"
ON public.posts FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

CREATE POLICY "Authors viewable by analysts"
ON public.authors FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

CREATE POLICY "Features viewable by analysts"
ON public.post_features FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

CREATE POLICY "Analytics viewable by analysts"
ON public.analysis_results FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

CREATE POLICY "Risk scores viewable by analysts"
ON public.risk_scores FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

-- Cases & Notes: Read by analysts/reviewers/admins; create/update by assigned or reviewer/admin
CREATE POLICY "Cases readable by authenticated team"
ON public.cases FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

CREATE POLICY "Cases creatable by analysts"
ON public.cases FOR INSERT TO authenticated
WITH CHECK (public.get_auth_role() IN ('analyst', 'reviewer', 'admin'));

CREATE POLICY "Cases updatable by team"
ON public.cases FOR UPDATE TO authenticated
USING (
    public.get_auth_role() IN ('admin', 'reviewer') 
    OR (public.get_auth_role() = 'analyst' AND assigned_to = auth.uid())
);

CREATE POLICY "Case items readable by team"
ON public.case_items FOR SELECT TO authenticated USING (true);

CREATE POLICY "Case items insertable by team"
ON public.case_items FOR INSERT TO authenticated WITH CHECK (true);

CREATE POLICY "Case notes readable by team"
ON public.case_notes FOR SELECT TO authenticated USING (true);

CREATE POLICY "Case notes insertable by team"
ON public.case_notes FOR INSERT TO authenticated WITH CHECK (true);

-- Evidence & Merkle: Read only by authenticated team
CREATE POLICY "Evidence readable by team"
ON public.evidence_items FOR SELECT TO authenticated USING (true);

CREATE POLICY "Merkle roots readable by team"
ON public.merkle_roots FOR SELECT TO authenticated USING (true);

-- Audit log: Read only by reviewers and admins; insert allowed by authenticated
CREATE POLICY "Audit log readable by reviewers and admins"
ON public.audit_log FOR SELECT TO authenticated
USING (public.get_auth_role() IN ('reviewer', 'admin'));

CREATE POLICY "Audit log insertable by authenticated users"
ON public.audit_log FOR INSERT TO authenticated
WITH CHECK (true);
