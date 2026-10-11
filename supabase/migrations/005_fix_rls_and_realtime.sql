-- ====================================================================
-- SOCIAL SHIELD - SUPABASE MIGRATION 005
-- Fix RLS Policies and Realtime Publication for Multi-Device Realtime Sync
-- ====================================================================

-- 1. Relax Row Level Security on public.scans
-- Allows backend (anon key or Bearer token) and web/android clients to insert and query scans
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own scans" ON public.scans;
DROP POLICY IF EXISTS "Users view own scans" ON public.scans;
DROP POLICY IF EXISTS "Sync users view own scans" ON public.scans;
DROP POLICY IF EXISTS "Users can insert own scans" ON public.scans;
DROP POLICY IF EXISTS "Users insert own scans" ON public.scans;
DROP POLICY IF EXISTS "Sync users insert own scans" ON public.scans;
DROP POLICY IF EXISTS "Users can update own scans" ON public.scans;
DROP POLICY IF EXISTS "Users can delete own scans" ON public.scans;
DROP POLICY IF EXISTS "Allow all on scans" ON public.scans;
DROP POLICY IF EXISTS "Allow all select on scans" ON public.scans;
DROP POLICY IF EXISTS "Allow all insert on scans" ON public.scans;
DROP POLICY IF EXISTS "Allow all delete on scans" ON public.scans;

CREATE POLICY "Allow all on scans" ON public.scans FOR ALL USING (true) WITH CHECK (true);

-- 2. Relax Row Level Security on public.user_stats
-- Allows backend and automated triggers to insert, query, and update user statistics
ALTER TABLE public.user_stats ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Users view own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Sync users view own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Users can update own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Users modify own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Sync users modify own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Users can insert own stats" ON public.user_stats;
DROP POLICY IF EXISTS "Allow all on user_stats" ON public.user_stats;

CREATE POLICY "Allow all on user_stats" ON public.user_stats FOR ALL USING (true) WITH CHECK (true);

-- 3. Relax Row Level Security on public.threats and public.notifications
ALTER TABLE public.threats ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on threats" ON public.threats;
CREATE POLICY "Allow all on threats" ON public.threats FOR ALL USING (true) WITH CHECK (true);

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow all on notifications" ON public.notifications;
CREATE POLICY "Allow all on notifications" ON public.notifications FOR ALL USING (true) WITH CHECK (true);

-- 4. Ensure Realtime Publication broadcasts changes across all tables
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = 'scans'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.scans;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = 'user_stats'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.user_stats;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = 'profiles'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.profiles;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = 'notifications'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;
    END IF;
END $$;

-- 5. Enable Full Replica Identity for Complete WebSocket Payloads
ALTER TABLE public.scans REPLICA IDENTITY FULL;
ALTER TABLE public.user_stats REPLICA IDENTITY FULL;
ALTER TABLE public.profiles REPLICA IDENTITY FULL;
ALTER TABLE public.notifications REPLICA IDENTITY FULL;
