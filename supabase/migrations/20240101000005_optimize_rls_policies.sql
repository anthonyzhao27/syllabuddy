-- Optimize RLS policies by wrapping auth.uid() in (select auth.uid())
-- This ensures the function is evaluated once per query instead of once per row,
-- significantly improving performance at scale.
-- See: https://supabase.com/docs/guides/database/database-advisors?queryGroups=lint&lint=0003_auth_rls_initplan

-- ============================================================================
-- profiles table
-- ============================================================================
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;

CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = id)
    WITH CHECK ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = id);

-- ============================================================================
-- syllabi table
-- ============================================================================
DROP POLICY IF EXISTS "Users can view own syllabi" ON public.syllabi;
DROP POLICY IF EXISTS "Users can insert own syllabi" ON public.syllabi;
DROP POLICY IF EXISTS "Users can update own syllabi" ON public.syllabi;
DROP POLICY IF EXISTS "Users can delete own syllabi" ON public.syllabi;

CREATE POLICY "Users can view own syllabi"
    ON public.syllabi FOR SELECT
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

CREATE POLICY "Users can insert own syllabi"
    ON public.syllabi FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

CREATE POLICY "Users can update own syllabi"
    ON public.syllabi FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

CREATE POLICY "Users can delete own syllabi"
    ON public.syllabi FOR DELETE
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

-- ============================================================================
-- events table
-- ============================================================================
DROP POLICY IF EXISTS "Users can view own events" ON public.events;
DROP POLICY IF EXISTS "Users can insert own events" ON public.events;
DROP POLICY IF EXISTS "Users can update own events" ON public.events;
DROP POLICY IF EXISTS "Users can delete own events" ON public.events;

CREATE POLICY "Users can view own events"
    ON public.events FOR SELECT
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

CREATE POLICY "Users can insert own events"
    ON public.events FOR INSERT
    TO authenticated
    WITH CHECK ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

CREATE POLICY "Users can update own events"
    ON public.events FOR UPDATE
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

CREATE POLICY "Users can delete own events"
    ON public.events FOR DELETE
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

-- ============================================================================
-- reminder_preferences table
-- ============================================================================
DROP POLICY IF EXISTS "Users can manage own reminder preferences" ON public.reminder_preferences;

CREATE POLICY "Users can manage own reminder preferences"
    ON public.reminder_preferences FOR ALL
    TO authenticated
    USING ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id)
    WITH CHECK ((select auth.uid()) IS NOT NULL AND (select auth.uid()) = user_id);

-- ============================================================================
-- storage.objects (syllabi bucket)
-- ============================================================================
DROP POLICY IF EXISTS "Users can upload own files" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own files" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own files" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own files" ON storage.objects;

CREATE POLICY "Users can upload own files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    (select auth.uid()) IS NOT NULL AND
    bucket_id = 'syllabi' AND
    (select auth.uid())::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view own files"
ON storage.objects FOR SELECT
TO authenticated
USING (
    (select auth.uid()) IS NOT NULL AND
    bucket_id = 'syllabi' AND
    (select auth.uid())::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can update own files"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    (select auth.uid()) IS NOT NULL AND
    bucket_id = 'syllabi' AND
    (select auth.uid())::text = (storage.foldername(name))[1]
)
WITH CHECK (
    (select auth.uid()) IS NOT NULL AND
    bucket_id = 'syllabi' AND
    (select auth.uid())::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
TO authenticated
USING (
    (select auth.uid()) IS NOT NULL AND
    bucket_id = 'syllabi' AND
    (select auth.uid())::text = (storage.foldername(name))[1]
);
