export const EVENT_TYPES = {
  assignment: true,
  exam: true,
  quiz: true,
  project: true,
  lab: true,
  presentation: true,
  milestone: true,
  deadline: true,
  discussion: true,
  other: true,
} as const;

export type EventType = keyof typeof EVENT_TYPES;
export type SourceType = "file" | "screenshots";
export type DateConfidence = "exact" | "inferred" | "estimated";
export type TermSeason = "fall" | "winter" | "summer" | "full_year";
export type TermAnchorSource =
  | "user"
  | "syllabus_anchor"
  | "syllabus_dates"
  | "table"
  | "heuristic";
export type TermYearSource = "user" | "stated" | "weekday_votes" | "upload_date";

export type ApiEvent = {
  title: string;
  due_date: string;
  course: string;
  event_type: string;
  description: string;
  time_specified: boolean;
  duration_minutes: number | null;
  date_confidence: DateConfidence | null;
  date_source: string;
  // Stable id of the syllabus item (survives re-dating); absent on fallback parses
  source_key?: string;
};

// Event shape accepted by the save and export endpoints. Confidence fields
// are only sent on save, and only when known.
export type ApiEventInput = Omit<
  ApiEvent,
  "date_confidence" | "date_source" | "source_key"
> & {
  date_confidence?: DateConfidence;
  date_source?: string;
  source_key?: string;
};

export type ApiTermContext = {
  term_id: string;
  label: string;
  season: TermSeason;
  year: number;
  campus: string;
  division: string;
  week1_monday: string;
  reading_week_numbered: boolean;
  classes_start: string;
  classes_end: string;
  reading_week: [string, string] | null;
  exam_period: [string, string] | null;
  anchor_source: TermAnchorSource;
  year_source: TermYearSource;
};

// Opaque LLM transcription; sent back verbatim to /parse/resolve.
export type SyllabusExtraction = Record<string, unknown>;

export type ApiParseResponse = {
  events: ApiEvent[];
  course_code: string | null;
  term_context: ApiTermContext | null;
  extraction: SyllabusExtraction | null;
};

export type ApiSaveResponse = {
  syllabus_id: string;
};

export type ParsedEvent = {
  title: string;
  date: string;
  time: string | null;
  course: string;
  type: EventType;
  description: string;
  durationMinutes: number | null;
  dateConfidence: DateConfidence | null;
  dateSource: string;
  sourceKey?: string;
};

export type TermContext = {
  termId: string;
  label: string;
  season: TermSeason;
  year: number;
  campus: string;
  division: string;
  week1Monday: string;
  readingWeekNumbered: boolean;
  classesStart: string;
  classesEnd: string;
  readingWeek: [string, string] | null;
  examPeriod: [string, string] | null;
  anchorSource: TermAnchorSource;
  yearSource: TermYearSource;
};

export type TermOverride = {
  season?: TermSeason;
  year?: number;
  campus?: string;
  week1Monday?: string;
  readingWeekNumbered?: boolean;
};

export type ParseSyllabusResult = {
  events: ParsedEvent[];
  courseCode: string | null;
  termContext: TermContext | null;
  extraction: SyllabusExtraction | null;
};

export type SaveSyllabusResult = {
  syllabusId: string;
};

export type ApiSyllabus = {
  id: string;
  name: string;
  course_code: string | null;
  source_type: SourceType;
  original_filename: string | null;
  created_at: string;
  event_count: number;
  timezone: string | null;
  term_context: ApiTermContext | null;
  can_redate: boolean;
};

export type ApiSyllabusListResponse = {
  syllabi: ApiSyllabus[];
};

export type ApiSavedEvent = {
  id: string;
  title: string;
  due_date: string;
  course: string;
  event_type: string;
  description: string;
  time_specified: boolean;
  duration_minutes: number | null;
  is_edited: boolean;
  date_confidence: DateConfidence | null;
  date_source: string;
};

export type ApiSyllabusDetailResponse = {
  syllabus: ApiSyllabus;
  events: ApiSavedEvent[];
};

export type ApiDeleteResponse = {
  message: string;
};

export type SavedSyllabus = {
  id: string;
  name: string;
  courseCode: string | null;
  sourceType: SourceType;
  originalFilename: string | null;
  createdAt: string;
  eventCount: number;
  timezone: string | null;
  termContext: TermContext | null;
  canRedate: boolean;
};

export type SavedEvent = {
  id: string;
  title: string;
  date: string;
  time: string | null;
  course: string;
  type: EventType;
  description: string;
  durationMinutes: number | null;
  isEdited: boolean;
  dateConfidence: DateConfidence | null;
  dateSource: string;
};

export type SyllabusDetail = {
  syllabus: SavedSyllabus;
  events: SavedEvent[];
};

export type SavedEventUpdateInput = {
  title?: string;
  date?: string;
  time?: string | null;
  course?: string;
  type?: EventType;
  description?: string;
  durationMinutes?: number;
};

