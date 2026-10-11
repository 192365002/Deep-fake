-- ====================================================================
-- SOCIAL SHIELD - SUPABASE STORAGE & REALTIME CONFIG (MIGRATION 003)
-- Private Storage Buckets & Realtime Webhook Subscriptions
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. Realtime Publication Setup
-- --------------------------------------------------------------------

-- Ensure full replica identity for accurate change payloads (including old records on delete)
ALTER TABLE public.scans REPLICA IDENTITY FULL;
ALTER TABLE public.user_stats REPLICA IDENTITY FULL;
ALTER TABLE public.notifications REPLICA IDENTITY FULL;
ALTER TABLE public.profiles REPLICA IDENTITY FULL;

-- Add tables to the supabase_realtime publication
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
        WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = 'notifications'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_publication_tables
        WHERE pubname = 'supabase_realtime' AND schemaname = 'public' AND tablename = 'profiles'
    ) THEN
        ALTER PUBLICATION supabase_realtime ADD TABLE public.profiles;
    END IF;
END $$;

-- --------------------------------------------------------------------
-- 2. Storage Bucket Creation: scan-media
-- --------------------------------------------------------------------

-- Insert private bucket if not already present
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'scan-media',
    'scan-media',
    FALSE,
    20971520, -- 20 MB max file size
    ARRAY[
        'image/jpeg',
        'image/png',
        'image/webp',
        'image/gif',
        'video/mp4',
        'video/quicktime',
        'audio/mpeg',
        'audio/wav',
        'audio/ogg'
    ]
)
ON CONFLICT (id) DO UPDATE
SET public = FALSE,
    file_size_limit = 20971520;

-- --------------------------------------------------------------------
-- 3. Storage RLS Policies (User-Scoped Isolation)
-- User uploads must strictly reside under: {auth.uid()}/...
-- --------------------------------------------------------------------

-- Allow authenticated users to upload files into their own user folder
CREATE POLICY "Users can upload their own scan media"
    ON storage.objects
    FOR INSERT
    TO authenticated
    WITH CHECK (
        bucket_id = 'scan-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to view/download their own scan media
CREATE POLICY "Users can view their own scan media"
    ON storage.objects
    FOR SELECT
    TO authenticated
    USING (
        bucket_id = 'scan-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow users to delete their own scan media
CREATE POLICY "Users can delete their own scan media"
    ON storage.objects
    FOR DELETE
    TO authenticated
    USING (
        bucket_id = 'scan-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Backend Service Role has full access for administrative tasks & processing
-- (Default in Supabase: service_role bypasses RLS)
