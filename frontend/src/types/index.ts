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

export type ApiEvent = {
  title: string;
  due_date: string;
  course: string;
  event_type: string;
  description: string;
  time_specified: boolean;
  duration_minutes?: number | null;
};

export type ApiParseResponse = {
  events: ApiEvent[];
};

export type ParsedEvent = {
  id: string;
  title: string;
  date: string;
  time?: string;
  description?: string;
  course: string;
  type: EventType;
  isAmbiguous: boolean;
  durationMinutes?: number;
};

export type ParseResponse = {
  events: ParsedEvent[];
};
