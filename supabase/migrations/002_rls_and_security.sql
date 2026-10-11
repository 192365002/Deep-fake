-- ====================================================================
-- SOCIAL SHIELD - SUPABASE RLS SECURITY POLICIES (MIGRATION 002)
-- Least-Privilege Row Level Security Across All User Records
-- ====================================================================

-- 1. Enable Row Level Security on All Tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- --------------------------------------------------------------------
-- 2. Profiles Table Policies
-- --------------------------------------------------------------------

-- Users can read their own profile
CREATE POLICY "Users can view own profile"
    ON public.profiles
    FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles
    FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- Insert policy for user self-registration or service role
CREATE POLICY "Users can insert own profile"
    ON public.profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Admins can view all profiles
CREATE POLICY "Admins can view all profiles"
    ON public.profiles
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role = 'admin'
        )
    );

-- --------------------------------------------------------------------
-- 3. User Stats Table Policies
-- --------------------------------------------------------------------

-- Users can read their own aggregate statistics
CREATE POLICY "Users can view own stats"
    ON public.user_stats
    FOR SELECT
    USING (auth.uid() = user_id);

-- System triggers / backend can update user stats; users can initialize their row
CREATE POLICY "Users can update own stats"
    ON public.user_stats
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can insert own stats"
    ON public.user_stats
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- --------------------------------------------------------------------
-- 4. Scans Table Policies
-- --------------------------------------------------------------------

-- Users can read only their own scans
CREATE POLICY "Users can view own scans"
    ON public.scans
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own scans
CREATE POLICY "Users can insert own scans"
    ON public.scans
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own scans
CREATE POLICY "Users can update own scans"
    ON public.scans
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own scans
CREATE POLICY "Users can delete own scans"
    ON public.scans
    FOR DELETE
    USING (auth.uid() = user_id);

-- --------------------------------------------------------------------
-- 5. Threats Table Policies (Community Threat Intelligence)
-- --------------------------------------------------------------------

-- Authenticated users can read threat reports (public community safety feed)
CREATE POLICY "Authenticated users can view threats"
    ON public.threats
    FOR SELECT
    TO authenticated
    USING (true);

-- Authenticated users can submit a threat report
CREATE POLICY "Authenticated users can submit threats"
    ON public.threats
    FOR INSERT
    TO authenticated
    WITH CHECK (
        auth.uid() IS NOT NULL AND
        (reporter_id IS NULL OR reporter_id = auth.uid())
    );

-- Admins and analysts can update threat status
CREATE POLICY "Admins and analysts can update threats"
    ON public.threats
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role IN ('admin', 'analyst')
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.role IN ('admin', 'analyst')
        )
    );

-- --------------------------------------------------------------------
-- 6. Notifications Table Policies
-- --------------------------------------------------------------------

-- Users can view their own notifications
CREATE POLICY "Users can view own notifications"
    ON public.notifications
    FOR SELECT
    USING (auth.uid() = user_id);

-- Users can mark their notifications as read
CREATE POLICY "Users can update own notifications"
    ON public.notifications
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own notifications
CREATE POLICY "Users can delete own notifications"
    ON public.notifications
    FOR DELETE
    USING (auth.uid() = user_id);

-- System can insert notifications for users
CREATE POLICY "Users can receive notifications"
    ON public.notifications
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);
