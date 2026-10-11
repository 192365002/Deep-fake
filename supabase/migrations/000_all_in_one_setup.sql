-- ====================================================================
-- SOCIAL SHIELD - ALL-IN-ONE SUPABASE SETUP & BIDIRECTIONAL SYNC
-- ====================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 2. CREATE TABLES
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'analyst', 'admin')),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    sync_version BIGINT NOT NULL DEFAULT 1,
    preferences JSONB NOT NULL DEFAULT '{"theme": "system", "notifications": true, "auto_scan": false}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.user_stats (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    total_scans INTEGER NOT NULL DEFAULT 0 CHECK (total_scans >= 0),
    fake_detected INTEGER NOT NULL DEFAULT 0 CHECK (fake_detected >= 0),
    suspicious_detected INTEGER NOT NULL DEFAULT 0 CHECK (suspicious_detected >= 0),
    safe_detected INTEGER NOT NULL DEFAULT 0 CHECK (safe_detected >= 0),
    trust_score INTEGER NOT NULL DEFAULT 100 CHECK (trust_score BETWEEN 0 AND 100),
    sync_version BIGINT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    media_type TEXT NOT NULL,
    verdict TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    fake_probability DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    real_probability DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    risk_level TEXT NOT NULL DEFAULT 'Low',
    explanations JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    heatmap_base64 TEXT,
    storage_path TEXT,
    storage_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    sync_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.threats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    reporter_email TEXT,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    sync_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    sync_version BIGINT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 3. INDEXES
CREATE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON public.scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON public.scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scans_user_media ON public.scans(user_id, media_type);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id, is_read);

-- 4. REPLICA IDENTITY FULL
ALTER TABLE public.scans REPLICA IDENTITY FULL;
ALTER TABLE public.user_stats REPLICA IDENTITY FULL;
ALTER TABLE public.profiles REPLICA IDENTITY FULL;
ALTER TABLE public.notifications REPLICA IDENTITY FULL;

-- 5. REALTIME PUBLICATION SETUP
DO $$
BEGIN
    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.scans;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.user_stats;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.profiles;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;

    BEGIN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;
    EXCEPTION WHEN duplicate_object THEN NULL;
    END;
END $$;

-- 6. AUTOMATED FUNCTIONS & TRIGGERS
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

    INSERT INTO public.user_stats (user_id, total_scans, fake_detected, suspicious_detected, safe_detected, trust_score, sync_version)
    VALUES (NEW.id, 0, 0, 0, 0, 100, 1)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

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

    SELECT
        COUNT(*),
        COUNT(*) FILTER (WHERE UPPER(verdict) IN ('FAKE', 'DANGEROUS', 'DEEPFAKE')),
        COUNT(*) FILTER (WHERE UPPER(verdict) IN ('SUSPICIOUS', 'MANIPULATED')),
        COUNT(*) FILTER (WHERE UPPER(verdict) IN ('SAFE', 'REAL'))
    INTO v_total, v_fake, v_suspicious, v_safe
    FROM public.scans
    WHERE user_id = target_user_id;

    IF v_total > 0 THEN
        v_score := ROUND(((v_safe::FLOAT + 0.5 * v_suspicious::FLOAT) / v_total::FLOAT) * 100)::INTEGER;
    ELSE
        v_score := 100;
    END IF;

    INSERT INTO public.user_stats (
        user_id, total_scans, fake_detected, suspicious_detected, safe_detected, trust_score, sync_version, updated_at
    )
    VALUES (
        target_user_id, v_total, v_fake, v_suspicious, v_safe, v_score, 1, timezone('utc'::text, now())
    )
    ON CONFLICT (user_id) DO UPDATE
    SET total_scans = EXCLUDED.total_scans,
        fake_detected = EXCLUDED.fake_detected,
        suspicious_detected = EXCLUDED.suspicious_detected,
        safe_detected = EXCLUDED.safe_detected,
        trust_score = EXCLUDED.trust_score,
        sync_version = public.user_stats.sync_version + 1,
        updated_at = timezone('utc'::text, now());

    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_scan_mutation_recalculate_stats ON public.scans;
CREATE TRIGGER on_scan_mutation_recalculate_stats
    AFTER INSERT OR UPDATE OR DELETE ON public.scans
    FOR EACH ROW EXECUTE FUNCTION public.recalculate_user_stats();

CREATE OR REPLACE FUNCTION public.increment_sync_version()
RETURNS TRIGGER AS $$
BEGIN
    NEW.sync_version = COALESCE(OLD.sync_version, 0) + 1;
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS bump_scan_sync_version ON public.scans;
CREATE TRIGGER bump_scan_sync_version
    BEFORE UPDATE ON public.scans
    FOR EACH ROW EXECUTE FUNCTION public.increment_sync_version();

-- 7. ROW-LEVEL SECURITY (RLS) POLICIES
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users view own profile" ON public.profiles;
CREATE POLICY "Users view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users update own profile" ON public.profiles;
CREATE POLICY "Users update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users insert own profile" ON public.profiles;
CREATE POLICY "Users insert own profile" ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users view own stats" ON public.user_stats;
CREATE POLICY "Users view own stats" ON public.user_stats FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users modify own stats" ON public.user_stats;
CREATE POLICY "Users modify own stats" ON public.user_stats FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users view own scans" ON public.scans;
CREATE POLICY "Users view own scans" ON public.scans FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users insert own scans" ON public.scans;
CREATE POLICY "Users insert own scans" ON public.scans FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users update own scans" ON public.scans;
CREATE POLICY "Users update own scans" ON public.scans FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users delete own scans" ON public.scans;
CREATE POLICY "Users delete own scans" ON public.scans FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users view threats" ON public.threats;
CREATE POLICY "Users view threats" ON public.threats FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "Users submit threats" ON public.threats;
CREATE POLICY "Users submit threats" ON public.threats FOR INSERT TO authenticated WITH CHECK (auth.uid() IS NOT NULL);

DROP POLICY IF EXISTS "Users view own notifications" ON public.notifications;
CREATE POLICY "Users view own notifications" ON public.notifications FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users update own notifications" ON public.notifications;
CREATE POLICY "Users update own notifications" ON public.notifications FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users delete own notifications" ON public.notifications;
CREATE POLICY "Users delete own notifications" ON public.notifications FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users receive notifications" ON public.notifications;
CREATE POLICY "Users receive notifications" ON public.notifications FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 8. PRIVATE STORAGE BUCKET & ACCESS POLICIES
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'scan-media',
    'scan-media',
    FALSE,
    20971520,
    ARRAY[
        'image/jpeg', 'image/png', 'image/webp', 'image/gif',
        'video/mp4', 'video/quicktime',
        'audio/mpeg', 'audio/wav', 'audio/ogg'
    ]
)
ON CONFLICT (id) DO UPDATE
SET public = FALSE, file_size_limit = 20971520;

DROP POLICY IF EXISTS "Users upload own scan media" ON storage.objects;
CREATE POLICY "Users upload own scan media"
    ON storage.objects FOR INSERT TO authenticated
    WITH CHECK (
        bucket_id = 'scan-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

DROP POLICY IF EXISTS "Users view own scan media" ON storage.objects;
CREATE POLICY "Users view own scan media"
    ON storage.objects FOR SELECT TO authenticated
    USING (
        bucket_id = 'scan-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

DROP POLICY IF EXISTS "Users delete own scan media" ON storage.objects;
CREATE POLICY "Users delete own scan media"
    ON storage.objects FOR DELETE TO authenticated
    USING (
        bucket_id = 'scan-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );
