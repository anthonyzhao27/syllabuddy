"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import { Header } from "./header";
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
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex flex-col items-center px-8 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="w-full max-w-3xl"
        >
          <div className="text-center mb-8">
            <h1 className="text-3xl font-semibold text-warm-700 mb-2 font-[family-name:var(--font-quicksand)]">
              Your Assignments
            </h1>
            <p className="text-warm-500">
              {events.length} assignment{events.length !== 1 ? "s" : ""} found.
              Edit any details below.
            </p>
          </div>

          <EventList
            events={events}
            onUpdate={handleUpdateEvent}
            onDelete={handleDeleteEvent}
          />

          <div className="mt-8 p-4 bg-white rounded-xl border border-warm-100">
            <label className="block text-sm font-medium text-warm-600 mb-2">
              Event timezone
            </label>
            <input
              type="text"
              value={exportTimezone}
              onChange={(e) => setExportTimezone(e.target.value)}
              placeholder="e.g. America/Toronto"
              className="w-full max-w-xs bg-warm-50 border border-warm-200 rounded-lg px-3 py-2 text-sm text-warm-700 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100 transition-all duration-200"
            />
            <p className="text-xs text-warm-400 mt-1.5">
              Timed events will be exported in this timezone
            </p>
          </div>

          <ExportButtons events={events} timezone={exportTimezone} />

          <button
            onClick={() => router.push("/")}
            className="mt-8 flex items-center gap-2 text-sm text-warm-500 hover:text-warm-700 cursor-pointer transition-colors mx-auto"
          >
            <ArrowLeft className="w-4 h-4" />
            Upload another syllabus
          </button>
        </motion.div>
      </main>
    </div>
  );
}
