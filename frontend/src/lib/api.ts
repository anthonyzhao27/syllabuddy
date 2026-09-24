import type {
  ApiDeleteResponse,
  ApiEvent,
  ApiEventInput,
  ApiParseResponse,
  ApiSavedEvent,
  ApiSaveResponse,
  ApiSyllabus,
  ApiSyllabusDetailResponse,
  ApiSyllabusListResponse,
  ApiTermContext,
  EventType,
  ParsedEvent,
  ParseSyllabusResult,
  SavedEvent,
  SavedEventUpdateInput,
  SavedSyllabus,
  SaveSyllabusResult,
  SyllabusDetail,
  SyllabusExtraction,
  TermContext,
  TermOverride,
} from "@/types";
import { EVENT_TYPES } from "@/types";
import { getCurrentPath, redirectToLogin } from "./auth-redirect";
import { getAccessToken, supabase } from "./supabase";

function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL;

  if (configured) {
    return configured;
  }

  if (process.env.NODE_ENV === "production") {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. It must be configured in production."
    );
  }

  return "http://localhost:8000";
}

const API_BASE = resolveApiBase();

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type ApiErrorResponse = {
  detail?: string;
};

type EventUpdatePayload = {
  title?: string;
  due_date?: string;
  course?: string;
  event_type?: EventType;
  description?: string;
  time_specified?: boolean;
  duration_minutes?: number;
};

function normalizeEventType(value: string): EventType {
  return value in EVENT_TYPES ? (value as EventType) : "other";
}

function toSavedSyllabus(raw: ApiSyllabus): SavedSyllabus {
  return {
    id: raw.id,
    name: raw.name,
    courseCode: raw.course_code,
    sourceType: raw.source_type,
    originalFilename: raw.original_filename,
    createdAt: raw.created_at,
    eventCount: raw.event_count,
    timezone: raw.timezone,
    termContext: raw.term_context ? toTermContext(raw.term_context) : null,
    canRedate: raw.can_redate ?? false,
  };
}

export function toSavedEvent(raw: ApiSavedEvent): SavedEvent {
  return {
    id: raw.id,
    title: raw.title,
    date: raw.due_date.slice(0, 10),
    time: raw.time_specified ? raw.due_date.slice(11, 16) : null,
    course: raw.course,
    type: normalizeEventType(raw.event_type),
    description: raw.description,
    durationMinutes: raw.duration_minutes,
    isEdited: raw.is_edited,
    dateConfidence: raw.date_confidence ?? null,
    dateSource: raw.date_source ?? "",
  };
}

export function toParsedEvent(raw: ApiEvent): ParsedEvent {
  return {
    title: raw.title,
    date: raw.due_date.slice(0, 10),
    time: raw.time_specified ? raw.due_date.slice(11, 16) : null,
    course: raw.course,
    type: normalizeEventType(raw.event_type),
    description: raw.description,
    durationMinutes: raw.duration_minutes,
    dateConfidence: raw.date_confidence ?? null,
    dateSource: raw.date_source ?? "",
    sourceKey: raw.source_key ?? "",
  };
}

export function toTermContext(raw: ApiTermContext): TermContext {
  return {
    termId: raw.term_id,
    label: raw.label,
    season: raw.season,
    year: raw.year,
    campus: raw.campus,
    division: raw.division,
    week1Monday: raw.week1_monday,
    readingWeekNumbered: raw.reading_week_numbered,
    classesStart: raw.classes_start,
    classesEnd: raw.classes_end,
    readingWeek: raw.reading_week,
    examPeriod: raw.exam_period,
    anchorSource: raw.anchor_source,
    yearSource: raw.year_source,
  };
}

function toApiTermContext(context: TermContext): ApiTermContext {
  return {
    term_id: context.termId,
    label: context.label,
    season: context.season,
    year: context.year,
    campus: context.campus,
    division: context.division,
    week1_monday: context.week1Monday,
    reading_week_numbered: context.readingWeekNumbered,
    classes_start: context.classesStart,
    classes_end: context.classesEnd,
    reading_week: context.readingWeek,
    exam_period: context.examPeriod,
    anchor_source: context.anchorSource,
    year_source: context.yearSource,
  };
}

function toApiTermOverride(override: TermOverride) {
  return {
    season: override.season,
    year: override.year,
    campus: override.campus,
    week1_monday: override.week1Monday,
    reading_week_numbered: override.readingWeekNumbered,
  };
}

function toSyllabusDetail(data: ApiSyllabusDetailResponse): SyllabusDetail {
  return {
    syllabus: toSavedSyllabus(data.syllabus),
    events: data.events.map(toSavedEvent),
  };
}

function toParseSyllabusResult(data: ApiParseResponse): ParseSyllabusResult {
  return {
    events: data.events.map(toParsedEvent),
    courseCode: data.course_code,
    termContext: data.term_context ? toTermContext(data.term_context) : null,
    extraction: data.extraction ?? null,
  };
}

function toApiEvent(event: ParsedEvent): ApiEventInput {
  const apiEvent: ApiEventInput = {
    title: event.title,
    due_date: event.time
      ? `${event.date}T${event.time}:00`
      : `${event.date}T23:59:00`,
    course: event.course,
    event_type: event.type,
    description: event.description,
    time_specified: event.time !== null,
    duration_minutes: event.durationMinutes,
  };

  if (event.dateConfidence) {
    apiEvent.date_confidence = event.dateConfidence;
  }

  if (event.dateSource) {
    apiEvent.date_source = event.dateSource;
  }

  if (event.sourceKey) {
    apiEvent.source_key = event.sourceKey;
  }

  return apiEvent;
}

function toApiExportEvent(event: SavedEvent): ApiEventInput {
  return {
    title: event.title,
    due_date: event.time
      ? `${event.date}T${event.time}:00`
      : `${event.date}T23:59:00`,
    course: event.course,
    event_type: event.type,
    description: event.description,
    time_specified: event.time !== null,
    duration_minutes: event.durationMinutes,
  };
}

export function toApiEventUpdate(
  input: SavedEventUpdateInput,
  existing: SavedEvent
): EventUpdatePayload {
  const body: EventUpdatePayload = {};

  if (input.title !== undefined) {
    body.title = input.title;
  }

  if (input.course !== undefined) {
    body.course = input.course;
  }

  if (input.description !== undefined) {
    body.description = input.description;
  }

  if (input.type !== undefined) {
    body.event_type = input.type;
  }

  if (input.durationMinutes !== undefined) {
    body.duration_minutes = input.durationMinutes;
  }

  if (input.time !== undefined) {
    const date = input.date ?? existing.date;

    if (input.time === null) {
      body.due_date = date;
      body.time_specified = false;
    } else {
      body.due_date = `${date}T${input.time}:00`;
      body.time_specified = true;
    }
  } else if (input.date !== undefined) {
    body.due_date = input.date;
  }

  return body;
}

async function getAuthHeaders(): Promise<{ Authorization: string }> {
  const token = await getAccessToken();

  if (!token) {
    redirectToLogin(getCurrentPath());
    throw new ApiError("You must be signed in to continue.", 401);
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

async function getErrorMessage(response: Response): Promise<string> {
  const body = (await response.json().catch(() => null)) as ApiErrorResponse | null;
  return body?.detail ?? `Request failed (${response.status})`;
}

async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const authHeaders = await getAuthHeaders();

  headers.set("Authorization", authHeaders.Authorization);

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (response.status === 401) {
    await supabase.auth.signOut();
    redirectToLogin(getCurrentPath());
    throw new ApiError("Your session expired. Please sign in again.", 401);
  }

  if (!response.ok) {
    throw new ApiError(await getErrorMessage(response), response.status);
  }

  return response;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function getFilenameFromResponse(response: Response, fallback: string): string {
  const contentDisposition = response.headers.get("content-disposition") || "";
  const filenameMatch = contentDisposition.match(/filename="(.+)"/);
  return filenameMatch ? filenameMatch[1] : fallback;
}

export async function parseSyllabus(
  formData: FormData
): Promise<ParseSyllabusResult> {
  const response = await apiFetch("/parse/", {
    method: "POST",
    body: formData,
  });
  const data = (await response.json()) as ApiParseResponse;
  return toParseSyllabusResult(data);
}

export async function resolveSyllabusDates(
  extraction: SyllabusExtraction,
  override: TermOverride
): Promise<ParseSyllabusResult> {
  const response = await apiFetch("/parse/resolve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      extraction,
      override: toApiTermOverride(override),
    }),
  });
  const data = (await response.json()) as ApiParseResponse;
  return toParseSyllabusResult(data);
}

type SaveSyllabusTermData = {
  termContext?: TermContext | null;
  extraction?: SyllabusExtraction | null;
};

export async function saveSyllabus(
  files: File[],
  events: ParsedEvent[],
  syllabusName?: string,
  timezone?: string,
  termData: SaveSyllabusTermData = {}
): Promise<SaveSyllabusResult> {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  formData.append("events_json", JSON.stringify(events.map(toApiEvent)));

  if (syllabusName) {
    formData.append("syllabus_name", syllabusName);
  }

  if (timezone) {
    formData.append("timezone", timezone);
  }

  // Lets the saved syllabus be re-dated later without another LLM call.
  if (termData.termContext) {
    formData.append(
      "term_context_json",
      JSON.stringify(toApiTermContext(termData.termContext))
    );
  }

  if (termData.extraction) {
    formData.append("extraction_json", JSON.stringify(termData.extraction));
  }

  const response = await apiFetch("/files/", {
    method: "POST",
    body: formData,
  });
  const data = (await response.json()) as ApiSaveResponse;

  return {
    syllabusId: data.syllabus_id,
  };
}

export async function getSyllabi(): Promise<SavedSyllabus[]> {
  const response = await apiFetch("/files/");
  const data = (await response.json()) as ApiSyllabusListResponse;
  return data.syllabi.map(toSavedSyllabus);
}

export async function getSyllabusDetail(id: string): Promise<SyllabusDetail> {
  const response = await apiFetch(`/files/${id}`);
  const data = (await response.json()) as ApiSyllabusDetailResponse;
  return toSyllabusDetail(data);
}

export async function resolveSavedSyllabusDates(
  syllabusId: string,
  override: TermOverride
): Promise<SyllabusDetail> {
  const response = await apiFetch(`/files/${syllabusId}/resolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      override: toApiTermOverride(override),
    }),
  });
  const data = (await response.json()) as ApiSyllabusDetailResponse;
  return toSyllabusDetail(data);
}

export async function deleteSyllabus(id: string): Promise<ApiDeleteResponse> {
  const response = await apiFetch(`/files/${id}`, {
    method: "DELETE",
  });
  return (await response.json()) as ApiDeleteResponse;
}

export async function downloadSyllabusFiles(id: string): Promise<void> {
  const response = await apiFetch(`/files/${id}/download`);
  const blob = await response.blob();
  downloadBlob(blob, getFilenameFromResponse(response, "syllabus-download"));
}

export async function updateEvent(
  syllabusId: string,
  eventId: string,
  input: SavedEventUpdateInput,
  existing: SavedEvent
): Promise<SavedEvent> {
  const body = toApiEventUpdate(input, existing);

  if (Object.keys(body).length === 0) {
    return existing;
  }

  const response = await apiFetch(`/files/${syllabusId}/events/${eventId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  const data = (await response.json()) as ApiSavedEvent;
  return toSavedEvent(data);
}

export async function deleteEvent(
  syllabusId: string,
  eventId: string
): Promise<ApiDeleteResponse> {
  const response = await apiFetch(`/files/${syllabusId}/events/${eventId}`, {
    method: "DELETE",
  });
  return (await response.json()) as ApiDeleteResponse;
}

export async function exportToIcs(
  events: SavedEvent[],
  timezone: string
): Promise<void> {
  const response = await apiFetch("/export/ics", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      events: events.map(toApiExportEvent),
      filename: "syllabus.ics",
      timezone,
    }),
  });

  const blob = await response.blob();
  downloadBlob(blob, getFilenameFromResponse(response, "calendar.ics"));
}

export async function updateSyllabusTimezone(
  syllabusId: string,
  timezone: string
): Promise<SavedSyllabus> {
  const response = await apiFetch(`/files/${syllabusId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ timezone }),
  });
  const data = (await response.json()) as ApiSyllabus;
  return toSavedSyllabus(data);
}

export async function deleteAccount(): Promise<void> {
  // Backend returns 204 No Content; cascade + storage purge happen server-side.
  await apiFetch("/account/", {
    method: "DELETE",
  });
}
