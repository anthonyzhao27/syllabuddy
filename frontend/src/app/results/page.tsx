"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Calendar, Save, X } from "lucide-react";
import { saveSyllabus } from "@/lib/api";
import { useParsedData } from "@/contexts/parsed-data-context";
import type { ParsedEvent } from "@/types";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { Header } from "@/components/header";
import { RequireAuth } from "@/components/require-auth";
import { LoadingScreen } from "@/components/loading-screen";
import { ParsedEventList } from "@/components/parsed-event-list";

export default function ResultsPage() {
  return (
    <Suspense fallback={<ResultsLoading />}>
      <RequireAuth>
        <ResultsContent />
      </RequireAuth>
    </Suspense>
  );
}

function ResultsLoading() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex flex-1 items-center justify-center px-6">
        <p className="text-sm font-medium text-warm-500">Loading...</p>
      </main>
    </div>
  );
}

function ResultsContent() {
  const router = useRouter();
  const { data, clear } = useParsedData();
  const [events, setEvents] = useState<ParsedEvent[]>([]);
  const [syllabusName, setSyllabusName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDiscardDialog, setShowDiscardDialog] = useState(false);

  useEffect(() => {
    if (!data) {
      router.replace("/upload");
      return;
    }

    setEvents(data.events);
    setSyllabusName(
      data.syllabusName ||
        (data.files[0]?.name ?? `Syllabus - ${data.courseCode || "Unknown"}`)
    );
  }, [data, router]);

  function handleUpdateEvent(index: number, updated: ParsedEvent) {
    setEvents((current) =>
      current.map((event, i) => (i === index ? updated : event))
    );
  }

  function handleDeleteEvent(index: number) {
    setEvents((current) => current.filter((_, i) => i !== index));
  }

  async function handleSave() {
    if (!data) {
      return;
    }

    if (events.length === 0) {
      setError("No events to save.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const result = await saveSyllabus(
        data.files,
        events,
        syllabusName.trim() || undefined
      );

      clear();
      router.push(`/dashboard/${result.syllabusId}?from=parse`);
    } catch (nextError) {
      setError(
        nextError instanceof Error ? nextError.message : "Failed to save"
      );
      setSaving(false);
    }
  }

  function handleDiscard() {
    clear();
    router.push("/upload");
  }

  if (!data) {
    return null;
  }

  return (
    <>
      <LoadingScreen isVisible={saving} />

      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 px-6 pb-16 pt-8 md:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="mx-auto w-full max-w-4xl"
          >
            <Link
              href="/upload"
              onClick={(e) => {
                e.preventDefault();
                setShowDiscardDialog(true);
              }}
              className="inline-flex items-center gap-2 text-sm font-semibold text-warm-500 transition-colors hover:text-warm-700"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to upload
            </Link>

            <div className="mt-6 rounded-[2rem] border border-mint-200 bg-mint-50 px-6 py-6 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-mint-700">
                Review parsed events
              </p>
              <h1 className="mt-2 text-3xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                {events.length} event(s) found
              </h1>
              <p className="mt-2 text-sm text-warm-600">
                Review and edit the events below, then save to your dashboard.
              </p>

              <div className="mt-5 rounded-2xl bg-white/80 p-4">
                <label className="block text-sm font-medium text-warm-600">
                  Syllabus name
                </label>
                <input
                  type="text"
                  value={syllabusName}
                  onChange={(e) => setSyllabusName(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-warm-200 bg-white px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
                />
              </div>

              {error ? (
                <p className="mt-4 text-sm text-error">{error}</p>
              ) : null}

              <div className="mt-5 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => void handleSave()}
                  disabled={saving || events.length === 0}
                  className="inline-flex items-center gap-2 rounded-full px-5 py-3 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
                  style={{
                    background: "linear-gradient(to bottom, #4ade80, #22c55e)",
                  }}
                >
                  <Save className="h-4 w-4" />
                  {saving ? "Saving..." : "Save to dashboard"}
                </button>

                <button
                  type="button"
                  onClick={() => setShowDiscardDialog(true)}
                  disabled={saving}
                  className="inline-flex items-center gap-2 rounded-full border border-warm-200 bg-white px-5 py-3 text-sm font-semibold text-warm-600 transition-colors hover:border-warm-300 hover:text-warm-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <X className="h-4 w-4" />
                  Discard
                </button>
              </div>
            </div>

            <div className="mt-6 rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-lg shadow-mint-100/30">
              <h2 className="text-xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                Parsed events
              </h2>
              <p className="mt-2 text-sm text-warm-500">
                Click the edit button to modify any event before saving.
              </p>

              {events.length === 0 ? (
                <div className="mt-8 py-12 text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-warm-50">
                    <Calendar className="h-8 w-8 text-warm-300" />
                  </div>
                  <p className="text-warm-500">
                    No events found. Try uploading a different syllabus.
                  </p>
                </div>
              ) : (
                <div className="mt-6">
                  <ParsedEventList
                    events={events}
                    onUpdate={handleUpdateEvent}
                    onDelete={handleDeleteEvent}
                  />
                </div>
              )}
            </div>
          </motion.div>
        </main>
      </div>

      <ConfirmDialog
        isOpen={showDiscardDialog}
        onCancel={() => setShowDiscardDialog(false)}
        onConfirm={handleDiscard}
        title="Discard Results"
        message="Discard parsed results and go back to upload? This cannot be undone."
        confirmText="Discard"
      />
    </>
  );
}
