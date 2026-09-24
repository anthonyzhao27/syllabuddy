-- Stable identity of the syllabus item an event came from ("e3" = 4th one-time
-- item, "r1:5" = 6th occurrence of the 2nd recurring rule). Lets re-dating a
-- saved syllabus keep the user's edits/deletions attached to the right item.
ALTER TABLE public.events ADD COLUMN source_key TEXT NOT NULL DEFAULT '';
