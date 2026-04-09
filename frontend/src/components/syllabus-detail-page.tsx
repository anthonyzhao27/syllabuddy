"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Download,
  FileText,
  Images,
  Trash2,
} from "lucide-react";
import {
  ApiError,
  deleteEvent,
  deleteSyllabus,
  downloadSyllabusFiles,
  getSyllabusDetail,
  updateEvent,
} from "@/lib/api";
import type { SyllabusDetail } from "@/types";
import { ConfirmDialog } from "./confirm-dialog";
import { EventList } from "./event-list";
import { ExportButtons } from "./export-buttons";
import { Header } from "./header";
import { RequireAuth } from "./require-auth";

function getDefaultTimezone(): string {
  if (typeof window === "undefined") {
    return "UTC";
  }

  return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

function formatCreatedAt(value: string): string {
  return new Date(value).toLocaleString();
}

function getSourceLabel(sourceType: SyllabusDetail["syllabus"]["sourceType"]): string {
  return sourceType === "screenshots" ? "Screenshots" : "Document";
}

export function SyllabusDetailPage() {
  return (
    <RequireAuth>
      <SyllabusDetailContent />
    </RequireAuth>
  );
}

function SyllabusDetailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { id } = useParams<{ id: string }>();

  const [detail, setDetail] = useState<SyllabusDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [timezone, setTimezone] = useState(getDefaultTimezone);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const fromParse = searchParams.get("from") === "parse";

  useEffect(() => {
    let active = true;

    async function loadDetail() {
      try {
        const nextDetail = await getSyllabusDetail(id);

        if (!active) {
          return;
        }

        setDetail(nextDetail);
        setError(null);
        setNotFound(false);
      } catch (nextError) {
        if (!active) {
          return;
        }

        if (nextError instanceof ApiError && nextError.status === 404) {
          setNotFound(true);
          setError(null);
          return;
        }

        setError(
          nextError instanceof Error
            ? nextError.message
            : "Failed to load syllabus detail"
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadDetail();

    return () => {
      active = false;
    };
  }, [id]);

  async function handleUpdateEvent(
    eventId: string,
    updates: Parameters<typeof updateEvent>[2]
  ) {
    if (!detail) {
      return;
    }

    const existingEvent = detail.events.find((event) => event.id === eventId);

    if (!existingEvent) {
      return;
    }

    const nextEvent = await updateEvent(
      detail.syllabus.id,
      eventId,
      updates,
      existingEvent
    );

    setDetail((current) =>
      current
        ? {
            ...current,
            events: current.events.map((event) =>
              event.id === eventId ? nextEvent : event
            ),
          }
        : current
    );
  }

  async function handleDeleteEvent(eventId: string) {
    if (!detail) {
      return;
    }

    await deleteEvent(detail.syllabus.id, eventId);

    setDetail((current) =>
      current
        ? {
            ...current,
            syllabus: {
              ...current.syllabus,
              eventCount: Math.max(current.syllabus.eventCount - 1, 0),
            },
            events: current.events.filter((event) => event.id !== eventId),
          }
        : current
    );
  }

  async function handleDownload() {
    if (!detail) {
      return;
    }

    setDownloadLoading(true);

    try {
      await downloadSyllabusFiles(detail.syllabus.id);
    } catch (nextError) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Failed to download original files"
      );
      setDownloadLoading(false);
      return;
    }

    setDownloadLoading(false);
  }

  async function handleDeleteSyllabus() {
    if (!detail) {
      return;
    }

    setDeleteLoading(true);

    try {
      await deleteSyllabus(detail.syllabus.id);
      router.replace("/dashboard");
    } catch (nextError) {
      setError(
        nextError instanceof Error
          ? nextError.message
          : "Failed to delete syllabus"
      );
      setDeleteLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex flex-1 items-center justify-center px-6">
          <p className="text-sm font-medium text-warm-500">
            Loading syllabus detail...
          </p>
        </main>
      </div>
    );
  }

  if (notFound) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex flex-1 items-center justify-center px-6">
          <div className="w-full max-w-lg rounded-[2rem] border border-white/70 bg-white/90 p-8 text-center shadow-lg">
            <p className="text-sm font-semibold uppercase tracking-[0.22em] text-warm-400">
              Not found
            </p>
            <h1 className="mt-3 text-3xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
              This syllabus is no longer available
            </h1>
            <p className="mt-3 text-sm text-warm-500">
              It may have been deleted or belong to a different account.
            </p>
            <Link
              href="/dashboard"
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-mint-500 px-5 py-3 text-sm font-semibold text-white"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to dashboard
            </Link>
          </div>
        </main>
      </div>
    );
  }

  if (!detail) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 px-6 pb-16 pt-8 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="mx-auto w-full max-w-5xl"
        >
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-sm font-semibold text-warm-500 transition-colors hover:text-warm-700"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>

          {fromParse ? (
            <div className="mt-6 rounded-[2rem] border border-mint-200 bg-mint-50 px-6 py-6 shadow-sm">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-mint-700">
                Saved successfully
              </p>
              <h1 className="mt-2 text-3xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                {detail.syllabus.name}
              </h1>
              <p className="mt-2 text-sm text-warm-600">
                {detail.events.length} event(s) were saved and are ready to edit
                or export.
              </p>
              <div className="mt-5 rounded-2xl bg-white/80 p-4">
                <label className="block text-sm font-medium text-warm-600">
                  Event timezone
                </label>
                <input
                  type="text"
                  value={timezone}
                  onChange={(event) => setTimezone(event.target.value)}
                  className="mt-2 w-full rounded-xl border border-warm-200 bg-white px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
                />
                <ExportButtons events={detail.events} timezone={timezone} />
              </div>
            </div>
          ) : null}

          <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr,0.9fr]">
            <section className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-lg shadow-mint-100/30">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-mint-50 px-3 py-1 text-xs font-semibold text-mint-700">
                      {detail.syllabus.sourceType === "screenshots" ? (
                        <Images className="h-3.5 w-3.5" />
                      ) : (
                        <FileText className="h-3.5 w-3.5" />
                      )}
                      {getSourceLabel(detail.syllabus.sourceType)}
                    </span>
                    {detail.syllabus.courseCode ? (
                      <span className="text-xs font-semibold uppercase tracking-[0.18em] text-warm-400">
                        {detail.syllabus.courseCode}
                      </span>
                    ) : null}
                  </div>
                  <h2 className="mt-3 text-3xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                    {detail.syllabus.name}
                  </h2>
                  <p className="mt-2 text-sm text-warm-500">
                    Created {formatCreatedAt(detail.syllabus.createdAt)}
                  </p>
                  <p className="mt-1 text-sm text-warm-500">
                    {detail.events.length} saved event(s)
                  </p>
                  {detail.syllabus.originalFilename ? (
                    <p className="mt-1 text-sm text-warm-500">
                      Original file: {detail.syllabus.originalFilename}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => void handleDownload()}
                    disabled={downloadLoading}
                    className="inline-flex items-center gap-2 rounded-full border border-warm-200 bg-white px-4 py-2 text-sm font-semibold text-warm-600 transition-colors hover:border-mint-200 hover:text-warm-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Download className="h-4 w-4" />
                    {downloadLoading ? "Downloading..." : "Download original"}
                  </button>

                  <button
                    type="button"
                    onClick={() => setShowDeleteDialog(true)}
                    disabled={deleteLoading}
                    className="inline-flex items-center gap-2 rounded-full border border-error/20 bg-error-light px-4 py-2 text-sm font-semibold text-error transition-colors hover:border-error/40 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <Trash2 className="h-4 w-4" />
                    {deleteLoading ? "Deleting..." : "Delete syllabus"}
                  </button>
                </div>
              </div>

              {!fromParse ? (
                <div className="mt-6 rounded-2xl bg-warm-50 p-4">
                  <label className="block text-sm font-medium text-warm-600">
                    Event timezone
                  </label>
                  <input
                    type="text"
                    value={timezone}
                    onChange={(event) => setTimezone(event.target.value)}
                    className="mt-2 w-full rounded-xl border border-warm-200 bg-white px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
                  />
                  <ExportButtons events={detail.events} timezone={timezone} />
                </div>
              ) : null}

              {error ? <p className="mt-4 text-sm text-error">{error}</p> : null}
            </section>

            <section className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-lg shadow-mint-100/30">
              <h3 className="text-xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                Saved events
              </h3>
              <p className="mt-2 text-sm text-warm-500">
                Edit details in place. Changes are persisted to the backend
                immediately when you save.
              </p>
              <div className="mt-6">
                <EventList
                  events={detail.events}
                  onUpdate={handleUpdateEvent}
                  onDelete={handleDeleteEvent}
                />
              </div>
            </section>
          </div>
        </motion.div>
      </main>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onCancel={() => setShowDeleteDialog(false)}
        onConfirm={() => {
          setShowDeleteDialog(false);
          void handleDeleteSyllabus();
        }}
        title="Delete Syllabus"
        message={`Delete "${detail.syllabus.name}" and its saved events?`}
      />
    </div>
  );
}
