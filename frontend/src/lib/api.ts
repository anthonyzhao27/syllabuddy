import type { ApiParseResponse, ParsedEvent, ParseResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const VALID_TYPES: ParsedEvent["type"][] = [
  "assignment",
  "exam",
  "quiz",
  "project",
  "other",
];

function transformEvent(raw: ApiParseResponse["events"][number], index: number): ParsedEvent {
  const date = raw.due_date.slice(0, 10);
  const dt = new Date(raw.due_date);
  const hours = dt.getUTCHours();
  const minutes = dt.getUTCMinutes();
  const time =
    hours === 0 && minutes === 0
      ? undefined
      : `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;

  const type = VALID_TYPES.includes(raw.event_type as ParsedEvent["type"])
    ? (raw.event_type as ParsedEvent["type"])
    : "other";

  return {
    id: `evt-${index}-${Date.now()}`,
    title: raw.title,
    date,
    time,
    description: raw.description || undefined,
    course: raw.course,
    type,
    isAmbiguous: false,
  };
}

export async function parseSyllabus(formData: FormData): Promise<ParseResponse> {
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
