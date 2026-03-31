-- Decision: uploads go directly from the authenticated client to Storage
-- using the anon key plus the user's JWT. Files must live under the
-- `<user_id>/...` prefix so Storage RLS can enforce per-user isolation.
--
-- Backend uploads with the service_role key are out of scope for this plan.
-- service_role bypasses Storage RLS, so switching to backend-managed uploads
-- would require separate application-level path validation or signed upload URLs.
INSERT INTO storage.buckets (id, name, public)
VALUES ('syllabi', 'syllabi', false);

CREATE POLICY "Users can upload own files"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    auth.uid() IS NOT NULL AND
    bucket_id = 'syllabi' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can view own files"
ON storage.objects FOR SELECT
TO authenticated
USING (
    auth.uid() IS NOT NULL AND
    bucket_id = 'syllabi' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can update own files"
ON storage.objects FOR UPDATE
TO authenticated
USING (
    auth.uid() IS NOT NULL AND
    bucket_id = 'syllabi' AND
    auth.uid()::text = (storage.foldername(name))[1]
)
WITH CHECK (
    auth.uid() IS NOT NULL AND
    bucket_id = 'syllabi' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
TO authenticated
USING (
    auth.uid() IS NOT NULL AND
    bucket_id = 'syllabi' AND
    auth.uid()::text = (storage.foldername(name))[1]
);
