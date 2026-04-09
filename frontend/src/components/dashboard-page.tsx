"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CalendarClock, FileText, Images } from "lucide-react";
import { getSyllabi } from "@/lib/api";
import type { SavedSyllabus } from "@/types";
import { Header } from "./header";
import { RequireAuth } from "./require-auth";

function formatCreatedAt(value: string): string {
  return new Date(value).toLocaleDateString();
}

function getSourceLabel(sourceType: SavedSyllabus["sourceType"]): string {
  return sourceType === "screenshots" ? "Screenshots" : "Document";
}

export function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}

function DashboardContent() {
  const [syllabi, setSyllabi] = useState<SavedSyllabus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadSyllabi() {
      try {
        const nextSyllabi = await getSyllabi();

        if (!active) {
          return;
        }

        setSyllabi(nextSyllabi);
        setError(null);
      } catch (nextError) {
        if (!active) {
          return;
        }

        setError(
          nextError instanceof Error
            ? nextError.message
            : "Failed to load saved syllabi"
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadSyllabi();

    return () => {
      active = false;
    };
  }, []);

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
          <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-mint-600">
                Dashboard
              </p>
              <h1 className="mt-3 text-4xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                Saved syllabi
              </h1>
              <p className="mt-2 text-base text-warm-500">
                Revisit parsed uploads, review saved events, and export them any
                time.
              </p>
            </div>

            <Link
              href="/upload"
              className="inline-flex items-center gap-2 rounded-full border border-mint-200 bg-mint-50 px-4 py-2 text-sm font-semibold text-mint-700 transition-colors hover:bg-mint-100"
            >
              Upload another syllabus
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {loading ? (
            <div className="rounded-[2rem] border border-white/70 bg-white/85 px-6 py-12 text-center shadow-lg">
              <p className="text-sm font-medium text-warm-500">
                Loading saved syllabi...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-[2rem] border border-error/10 bg-white/85 px-6 py-12 text-center shadow-lg">
              <p className="text-sm font-medium text-error">{error}</p>
            </div>
          ) : syllabi.length === 0 ? (
            <div className="rounded-[2rem] border border-white/70 bg-white/85 px-6 py-12 text-center shadow-lg">
              <p className="text-lg font-semibold text-warm-700">
                No saved syllabi yet
              </p>
              <p className="mt-2 text-sm text-warm-500">
                Upload your first syllabus to create a saved dashboard record.
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {syllabi.map((syllabus) => (
                <Link
                  key={syllabus.id}
                  href={`/dashboard/${syllabus.id}`}
                  className="rounded-[1.75rem] border border-white/70 bg-white/90 p-6 shadow-lg shadow-mint-100/30 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-mint-50 px-3 py-1 text-xs font-semibold text-mint-700">
                          {syllabus.sourceType === "screenshots" ? (
                            <Images className="h-3.5 w-3.5" />
                          ) : (
                            <FileText className="h-3.5 w-3.5" />
                          )}
                          {getSourceLabel(syllabus.sourceType)}
                        </span>
                        {syllabus.courseCode ? (
                          <span className="text-xs font-semibold uppercase tracking-[0.18em] text-warm-400">
                            {syllabus.courseCode}
                          </span>
                        ) : null}
                      </div>

                      <h2 className="mt-3 text-2xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                        {syllabus.name}
                      </h2>

                      <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-warm-500">
                        <span className="inline-flex items-center gap-1.5">
                          <CalendarClock className="h-4 w-4" />
                          Created {formatCreatedAt(syllabus.createdAt)}
                        </span>
                        <span>{syllabus.eventCount} saved event(s)</span>
                      </div>
                    </div>

                    <span className="inline-flex items-center gap-2 rounded-full bg-warm-50 px-3 py-2 text-sm font-semibold text-warm-600">
                      Open
                      <ArrowRight className="h-4 w-4" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
