-- How each event's date was derived ("exact" printed date, "inferred" from a
-- week number + known day, "estimated" best guess) and a human-readable note.
ALTER TABLE public.events ADD COLUMN date_confidence TEXT
    CHECK (date_confidence IS NULL OR date_confidence IN ('exact', 'inferred', 'estimated'));
ALTER TABLE public.events ADD COLUMN date_source TEXT NOT NULL DEFAULT '';

-- The term anchor used to date the events, and the raw LLM transcription so a
-- saved syllabus can be re-dated with a corrected anchor without another LLM call.
ALTER TABLE public.syllabi ADD COLUMN term_context JSONB;
ALTER TABLE public.syllabi ADD COLUMN extraction JSONB;
