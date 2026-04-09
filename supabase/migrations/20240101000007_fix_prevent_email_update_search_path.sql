-- Fix prevent_email_update: add search_path
-- See: https://supabase.com/docs/guides/database/database-linter?lint=0011_function_search_path_mutable

CREATE OR REPLACE FUNCTION public.prevent_email_update()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.email IS DISTINCT FROM OLD.email THEN
        -- Allow if called from SECURITY DEFINER context (sync trigger runs as postgres)
        IF current_setting('role', true) IS DISTINCT FROM 'authenticated'
           AND current_setting('role', true) IS DISTINCT FROM 'anon' THEN
            RETURN NEW;
        END IF;
        RAISE EXCEPTION 'Cannot update email directly. Email is synced from auth.users.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = '';
