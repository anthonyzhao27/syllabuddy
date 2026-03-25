"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { EventList } from "./event-list";
import { ExportButtons } from "./export-buttons";
import type { ParsedEvent } from "@/types";

function loadEvents(): ParsedEvent[] | null {
  if (typeof window === "undefined") return null;
  const stored = sessionStorage.getItem("parseResult");
  if (!stored) return null;
  const parsed = JSON.parse(stored) as { events: ParsedEvent[] };
  return parsed.events;
}

function getDefaultTimezone(): string {
  if (typeof window === "undefined") return "UTC";
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

export function ResultsPage() {
  const router = useRouter();
  const [events, setEvents] = useState<ParsedEvent[]>(() => loadEvents() ?? []);
  const [exportTimezone, setExportTimezone] = useState(getDefaultTimezone);
  const hasData = loadEvents() !== null;

  if (!hasData) {
    router.replace("/");
    return null;
  }

  function handleUpdateEvent(id: string, updates: Partial<ParsedEvent>) {
    setEvents((prev) =>
      prev.map((e) => (e.id === id ? { ...e, ...updates } : e))
    );
  }

  function handleDeleteEvent(id: string) {
    setEvents((prev) => prev.filter((e) => e.id !== id));
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-8 pt-12">
      <h1 className="text-3xl font-bold mb-2 text-sage-800">Parsed Assignments</h1>
      <p className="text-sage-600 mb-8">
        {events.length} assignment{events.length !== 1 ? "s" : ""} found. Edit
        any details below.
      </p>
      <EventList
        events={events}
        onUpdate={handleUpdateEvent}
        onDelete={handleDeleteEvent}
      />
      <div className="mt-6 w-full max-w-2xl">
        <label className="block text-sm font-medium text-sage-700 mb-1">
          Event timezone
        </label>
        <input
          type="text"
          value={exportTimezone}
          onChange={(e) => setExportTimezone(e.target.value)}
          placeholder="e.g. America/Toronto"
          className="w-full max-w-xs bg-sage-50 border border-sage-300 rounded-md px-3 py-1.5 text-sm text-sage-800 focus:outline-none focus:border-sage-500"
        />
        <p className="text-xs text-sage-500 mt-1">
          Timed events will be exported in this timezone
        </p>
      </div>
      <ExportButtons events={events} timezone={exportTimezone} />
      <button
        onClick={() => router.push("/")}
        className="mt-6 text-sm text-sage-600 hover:text-sage-800 cursor-pointer transition-colors"
      >
        ← Upload another syllabus
      </button>
    </main>
  );
}
