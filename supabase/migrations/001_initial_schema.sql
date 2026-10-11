-- ====================================================================
-- SOCIAL SHIELD - SUPABASE POSTGRESQL SCHEMA MIGRATION 001
-- Multi-Modal AI Fraud & Deepfake Detection Platform
-- ====================================================================

-- 1. Enable Required Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. User Profiles Table
-- Maps directly from MongoDB users collection and auth.users
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'analyst', 'admin')),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    preferences JSONB NOT NULL DEFAULT '{"theme": "system", "notifications": true, "auto_scan": false}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);

-- 3. User Aggregate Statistics Table
-- Replaces Firestore users/{uid} aggregate counter documents
CREATE TABLE IF NOT EXISTS public.user_stats (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    total_scans INTEGER NOT NULL DEFAULT 0,
    fake_detected INTEGER NOT NULL DEFAULT 0,
    suspicious_detected INTEGER NOT NULL DEFAULT 0,
    safe_detected INTEGER NOT NULL DEFAULT 0,
    trust_score INTEGER NOT NULL DEFAULT 100,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 4. Scans Table
-- Replaces MongoDB scans collection & Firestore users/{uid}/scans subcollection
CREATE TABLE IF NOT EXISTS public.scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    media_type TEXT NOT NULL CHECK (media_type IN ('IMAGE', 'VIDEO', 'AUDIO', 'TEXT', 'URL', 'PROFILE')),
    verdict TEXT NOT NULL CHECK (verdict IN ('SAFE', 'REAL', 'SUSPICIOUS', 'FAKE')),
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    fake_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    real_probability DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    explanations JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    heatmap_base64 TEXT,
    storage_path TEXT,
    storage_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON public.scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON public.scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scans_user_media ON public.scans(user_id, media_type);
CREATE INDEX IF NOT EXISTS idx_scans_verdict ON public.scans(verdict);

-- 5. Threats Table
-- Community Threat Intelligence (replaces MongoDB threats collection)
CREATE TABLE IF NOT EXISTS public.threats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reporter_email TEXT,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_threats_status ON public.threats(status);
CREATE INDEX IF NOT EXISTS idx_threats_created_at ON public.threats(created_at DESC);

-- 6. Notifications Table
-- Replaces MongoDB notifications collection
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id, is_read);

-- ====================================================================
-- AUTOMATED TRIGGERS & FUNCTIONS
-- ====================================================================

-- Function: Handle New Supabase Auth User
-- Automatically provisions profiles and user_stats on registration
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url, role, is_verified)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url',
        COALESCE(NEW.raw_user_meta_data->>'role', 'user'),
        COALESCE((NEW.email_confirmed_at IS NOT NULL), FALSE)
    )
    ON CONFLICT (id) DO UPDATE
    SET email = EXCLUDED.email,
        updated_at = timezone('utc'::text, now());

    INSERT INTO public.user_stats (user_id, total_scans, fake_detected, suspicious_detected, safe_detected, trust_score)
    VALUES (NEW.id, 0, 0, 0, 0, 100)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function: Recalculate User Stats on Scan Changes
-- Ensures accurate aggregate metrics without client-side race conditions
CREATE OR REPLACE FUNCTION public.recalculate_user_stats()
RETURNS TRIGGER AS $$
DECLARE
    target_user_id UUID;
    v_total INTEGER;
    v_fake INTEGER;
    v_suspicious INTEGER;
    v_safe INTEGER;
    v_score INTEGER;
BEGIN
    IF (TG_OP = 'DELETE') THEN
        target_user_id := OLD.user_id;
    ELSE
        target_user_id := NEW.user_id;
    END IF;

    -- Compute aggregates
    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE verdict = 'FAKE'),
        COUNT(*) FILTER (WHERE verdict = 'SUSPICIOUS'),
        COUNT(*) FILTER (WHERE verdict IN ('SAFE', 'REAL'))
    INTO v_total, v_fake, v_suspicious, v_safe
    FROM public.scans
    WHERE user_id = target_user_id;

    -- Calculate Trust Score: 100 base, weighted formula
    IF v_total > 0 THEN
        v_score := ROUND(((v_safe::FLOAT + 0.5 * v_suspicious::FLOAT) / v_total::FLOAT) * 100)::INTEGER;
    ELSE
        v_score := 100;
    END IF;

    -- Update or Insert into user_stats
    INSERT INTO public.user_stats (
        user_id,
        total_scans,
        fake_detected,
        suspicious_detected,
        safe_detected,
        trust_score,
        updated_at
    )
    VALUES (
        target_user_id,
        v_total,
        v_fake,
        v_suspicious,
        v_safe,
        v_score,
        timezone('utc'::text, now())
    )
    ON CONFLICT (user_id) DO UPDATE
    SET total_scans = EXCLUDED.total_scans,
        fake_detected = EXCLUDED.fake_detected,
        suspicious_detected = EXCLUDED.suspicious_detected,
        safe_detected = EXCLUDED.safe_detected,
        trust_score = EXCLUDED.trust_score,
        updated_at = EXCLUDED.updated_at;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger on scans mutation
DROP TRIGGER IF EXISTS on_scan_mutation_recalculate_stats ON public.scans;
CREATE TRIGGER on_scan_mutation_recalculate_stats
    AFTER INSERT OR UPDATE OR DELETE ON public.scans
    FOR EACH ROW EXECUTE FUNCTION public.recalculate_user_stats();

-- Function: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_timestamp
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();

CREATE TRIGGER update_threats_timestamp
    BEFORE UPDATE ON public.threats
    FOR EACH ROW EXECUTE FUNCTION public.update_timestamp();
