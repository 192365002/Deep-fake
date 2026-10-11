-- ====================================================================
-- SOCIAL SHIELD - BIDIRECTIONAL REALTIME SYNCHRONIZATION CONFIG (004)
-- Enables Live Bi-directional Sync for Web (React) and Mobile (Android)
-- ====================================================================

-- 1. ADD SYNC VERSIONING & TRACKING COLUMNS
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scans' AND column_name='sync_version') THEN
        ALTER TABLE public.scans ADD COLUMN sync_version BIGINT NOT NULL DEFAULT 1;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='scans' AND column_name='client_updated_at') THEN
        ALTER TABLE public.scans ADD COLUMN client_updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now());
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='user_stats' AND column_name='sync_version') THEN
        ALTER TABLE public.user_stats ADD COLUMN sync_version BIGINT NOT NULL DEFAULT 1;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='profiles' AND column_name='sync_version') THEN
        ALTER TABLE public.profiles ADD COLUMN sync_version BIGINT NOT NULL DEFAULT 1;
    END IF;
END $$;

-- 2. AUTOMATIC SYNC VERSION INCREMENT TRIGGER
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

-- 3. REPLICA IDENTITY FULL FOR REALTIME CDC
ALTER TABLE public.scans REPLICA IDENTITY FULL;
ALTER TABLE public.user_stats REPLICA IDENTITY FULL;
ALTER TABLE public.profiles REPLICA IDENTITY FULL;
ALTER TABLE public.notifications REPLICA IDENTITY FULL;

-- 4. REALTIME PUBLICATION CONFIGURATION
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

-- 5. ATOMIC BI-DIRECTIONAL STATS RECALCULATION TRIGGER
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
