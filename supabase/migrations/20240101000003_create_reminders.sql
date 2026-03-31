CREATE TABLE public.reminder_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    phone_number TEXT,
    text_samples TEXT[],
    learned_style JSONB,
    reminder_hours_before INTEGER[] DEFAULT ARRAY[24, 2],
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);

ALTER TABLE public.reminder_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own reminder preferences"
    ON public.reminder_preferences FOR ALL
    TO authenticated
    USING (auth.uid() IS NOT NULL AND auth.uid() = user_id)
    WITH CHECK (auth.uid() IS NOT NULL AND auth.uid() = user_id);

CREATE TRIGGER set_reminder_preferences_updated_at
    BEFORE UPDATE ON public.reminder_preferences
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
