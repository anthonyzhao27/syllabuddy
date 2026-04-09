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

export type ApiEvent = {
  title: string;
  due_date: string;
  course: string;
  event_type: string;
  description: string;
  time_specified: boolean;
  duration_minutes: number | null;
};

export type ApiParseResponse = {
  events: ApiEvent[];
  course_code: string | null;
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
};

export type ParseSyllabusResult = {
  events: ParsedEvent[];
  courseCode: string | null;
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

export type GoogleExportResponse = {
  created_count: number;
  created: Array<{ title: string; id: string; link: string }>;
  errors: Array<{ title: string; error: string }>;
  calendar_name: string;
};
