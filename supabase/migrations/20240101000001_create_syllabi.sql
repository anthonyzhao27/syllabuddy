CREATE TABLE public.syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Metadata
    name TEXT NOT NULL,
    course_code TEXT,

    -- Source type: 'file' (PDF/DOCX) or 'screenshots' (images)
    source_type TEXT NOT NULL CHECK (source_type IN ('file', 'screenshots')),
    original_filename TEXT,

    -- Storage reference (array supports multiple screenshots)
    storage_paths TEXT[],
    total_file_size_bytes INTEGER CHECK (total_file_size_bytes IS NULL OR total_file_size_bytes >= 0),

    -- Parsing info
    parsed_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure child tables can enforce that a row belongs to the same user
ALTER TABLE public.syllabi
    ADD CONSTRAINT syllabi_id_user_id_unique UNIQUE (id, user_id);

-- Indexes
CREATE INDEX idx_syllabi_user_id ON public.syllabi(user_id);
CREATE INDEX idx_syllabi_created_at ON public.syllabi(created_at DESC);

-- Row Level Security
ALTER TABLE public.syllabi ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own syllabi"
    ON public.syllabi FOR SELECT
    TO authenticated
    USING (auth.uid() IS NOT NULL AND auth.uid() = user_id);

CREATE POLICY "Users can insert own syllabi"
    ON public.syllabi FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() IS NOT NULL AND auth.uid() = user_id);

CREATE POLICY "Users can update own syllabi"
    ON public.syllabi FOR UPDATE
    TO authenticated
    USING (auth.uid() IS NOT NULL AND auth.uid() = user_id)
    WITH CHECK (auth.uid() IS NOT NULL AND auth.uid() = user_id);

CREATE POLICY "Users can delete own syllabi"
    ON public.syllabi FOR DELETE
    TO authenticated
    USING (auth.uid() IS NOT NULL AND auth.uid() = user_id);

CREATE TRIGGER set_syllabi_updated_at
    BEFORE UPDATE ON public.syllabi
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
