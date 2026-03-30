CREATE TABLE public.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    syllabus_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Event data (matches ParsedEvent schema)
    title TEXT NOT NULL,
    due_date TIMESTAMPTZ NOT NULL,
    course TEXT NOT NULL DEFAULT '',
    event_type TEXT NOT NULL DEFAULT 'other',
    description TEXT DEFAULT '',
    time_specified BOOLEAN DEFAULT TRUE,
    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes > 0),  -- Event duration in minutes

    -- User modifications
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enforce ownership integrity: an event can only reference a syllabus
-- owned by the same user_id.
ALTER TABLE public.events
    ADD CONSTRAINT events_syllabus_user_fk
    FOREIGN KEY (syllabus_id, user_id)
    REFERENCES public.syllabi(id, user_id)
    ON DELETE CASCADE;

-- Indexes
CREATE INDEX idx_events_syllabus_id ON public.events(syllabus_id);
CREATE INDEX idx_events_user_id ON public.events(user_id);
CREATE INDEX idx_events_due_date ON public.events(due_date);

-- Row Level Security
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own events"
    ON public.events FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own events"
    ON public.events FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own events"
    ON public.events FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own events"
    ON public.events FOR DELETE
    USING (auth.uid() = user_id);

CREATE TRIGGER set_events_updated_at
    BEFORE UPDATE ON public.events
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
