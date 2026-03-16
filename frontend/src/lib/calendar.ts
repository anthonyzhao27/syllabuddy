import type { ParsedEvent } from "@/types";

export function generateIcs(events: ParsedEvent[]): string {
  const lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Syllabus Parser//EN",
  ];

  for (const event of events) {
    const dateStr = event.date.replace(/-/g, "");
    lines.push(
      "BEGIN:VEVENT",
      `DTSTART;VALUE=DATE:${dateStr}`,
      `SUMMARY:${event.title}`,
      `DESCRIPTION:${event.description || ""}`,
      "END:VEVENT"
    );
  }

  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}

export function downloadIcs(events: ParsedEvent[], filename = "syllabus.ics") {
  const ics = generateIcs(events);
  const blob = new Blob([ics], { type: "text/calendar" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
