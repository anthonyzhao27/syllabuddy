"use client";

import { downloadIcs } from "@/lib/calendar";
import type { ParsedEvent } from "@/types";

type ExportButtonsProps = {
  events: ParsedEvent[];
};

export function ExportButtons({ events }: ExportButtonsProps) {
  return (
    <div className="flex flex-wrap gap-3 mt-8">
      <button
        className="px-4 py-2 rounded-md bg-sage-200/60 text-sage-500 text-sm font-medium cursor-not-allowed"
        disabled
      >
        Google Calendar
      </button>
      <button
        className="px-4 py-2 rounded-md bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium disabled:opacity-50 cursor-pointer transition-colors shadow-sm hover:shadow-md"
        disabled={events.length === 0}
        onClick={() => downloadIcs(events)}
      >
        Apple Calendar (.ics)
      </button>
      <button
        className="px-4 py-2 rounded-md bg-sage-200/60 text-sage-500 text-sm font-medium cursor-not-allowed"
        disabled
      >
        Outlook
      </button>
    </div>
  );
}
