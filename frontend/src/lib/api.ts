import type {
  ApiParseResponse,
  EventType,
  ParsedEvent,
  ParseResponse,
} from "@/types";
import { EVENT_TYPES } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function normalizeEventType(value: string): EventType {
  return value in EVENT_TYPES ? (value as EventType) : "other";
}

function transformEvent(
  raw: ApiParseResponse["events"][number],
  index: number
): ParsedEvent {
  const date = raw.due_date.slice(0, 10);
  const time = raw.due_date.slice(11, 16);

  const displayTime = raw.time_specified ? time : undefined;
  const type = normalizeEventType(raw.event_type);

  return {
    id: `evt-${index}-${Date.now()}`,
    title: raw.title,
    date,
    time: displayTime,
    description: raw.description || undefined,
    course: raw.course,
    type,
    isAmbiguous: false,
  };
}

function toApiEvents(events: ParsedEvent[]) {
  return events.map((e) => ({
    title: e.title,
    due_date: e.time ? `${e.date}T${e.time}:00` : `${e.date}T23:59:00`,
    course: e.course,
    event_type: e.type,
    description: e.description || "",
    time_specified: Boolean(e.time),
  }));
}

export async function parseSyllabus(
  formData: FormData
): Promise<ParseResponse> {
  const res = await fetch(`${API_BASE}/parse/`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      (body as { detail?: string } | null)?.detail ||
      `Parse failed (${res.status})`;
    throw new Error(message);
  }

  const data: ApiParseResponse = await res.json();
  return {
    events: data.events.map((e, i) => transformEvent(e, i)),
  };
}

export async function exportToIcs(
  events: ParsedEvent[],
  timezone: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/export/ics`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      events: toApiEvents(events),
      filename: "syllabus.ics",
      timezone,
    }),
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail || `Export failed (${res.status})`);
  }

  const blob = await res.blob();
  const contentDisposition = res.headers.get("content-disposition") || "";
  const filenameMatch = contentDisposition.match(/filename="(.+)"/);
  const filename = filenameMatch ? filenameMatch[1] : "calendar.ics";

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function exportToOutlook(
  events: ParsedEvent[],
  timezone: string
): Promise<void> {
  const res = await fetch(`${API_BASE}/export/outlook`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      events: toApiEvents(events),
      timezone,
    }),
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail || `Export failed (${res.status})`);
  }

  const blob = await res.blob();
  const contentDisposition = res.headers.get("content-disposition") || "";
  const filenameMatch = contentDisposition.match(/filename="(.+)"/);
  const filename = filenameMatch ? filenameMatch[1] : "calendar.ics";

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export type GoogleExportResponse = {
  created_count: number;
  created: Array<{ title: string; id: string; link: string }>;
  errors: Array<{ title: string; error: string }>;
  calendar_name: string;
};

export async function exportToGoogleCalendar(
  events: ParsedEvent[],
  accessToken: string,
  timezone: string
): Promise<GoogleExportResponse> {
  const res = await fetch(`${API_BASE}/export/google`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      events: toApiEvents(events),
      access_token: accessToken,
      timezone,
    }),
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as {
      detail?: string;
    } | null;
    throw new Error(body?.detail || `Export failed (${res.status})`);
  }

  return res.json();
}
