-- Fix remaining database advisor warnings
-- 1. Function search_path_mutable (security)
-- 2. Unindexed foreign keys (performance)
-- 3. Unused indexes (performance)

-- ============================================================================
-- Fix function search_path issues
-- Using empty search_path with fully qualified schema names for security
-- See: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable
-- ============================================================================

-- Fix handle_new_user: use empty search_path + qualified names
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- Fix set_updated_at: add search_path
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';

-- Fix handle_auth_user_updated: use empty search_path + qualified names
CREATE OR REPLACE FUNCTION public.handle_auth_user_updated()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE public.profiles
    SET email = NEW.email,
        updated_at = NOW()
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = '';

-- ============================================================================
-- Fix unindexed foreign key
-- The events_syllabus_user_fk constraint on (syllabus_id, user_id) needs an index
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_events_syllabus_user ON public.events(syllabus_id, user_id);

-- ============================================================================
-- Remove unused indexes
-- These indexes have never been used and add unnecessary overhead
-- ============================================================================

DROP INDEX IF EXISTS public.idx_syllabi_created_at;
DROP INDEX IF EXISTS public.idx_events_due_date;
