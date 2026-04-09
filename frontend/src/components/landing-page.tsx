"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Calendar, FileText, CalendarCheck, Sparkles } from "lucide-react";

export function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="w-full px-6 py-6 md:px-8">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <Calendar className="h-7 w-7 text-mint-500" />
            <span className="text-2xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
              Syllabuddy
            </span>
          </Link>

          <Link
            href="/login"
            className="rounded-full border border-warm-200 bg-white px-4 py-2 text-sm font-semibold text-warm-600 transition-colors hover:border-mint-300 hover:text-warm-700"
          >
            Sign in
          </Link>
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-6 pb-16 pt-8 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mx-auto w-full max-w-2xl text-center"
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-mint-200 bg-mint-50 px-4 py-2">
            <Sparkles className="h-4 w-4 text-mint-600" />
            <span className="text-sm font-semibold text-mint-700">
              AI-powered syllabus parsing
            </span>
          </div>

          <h1 className="text-5xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)] md:text-6xl">
            Your syllabus,{" "}
            <span className="text-mint-500">organized</span>
          </h1>

          <p className="mt-6 text-lg text-warm-500 font-[family-name:var(--font-nunito)] md:text-xl">
            Upload your course syllabus and let Syllabuddy extract all the
            important dates. Export to Google Calendar, Outlook, or any
            calendar app in seconds.
          </p>

          <div className="mt-10">
            <Link
              href="/login?mode=sign-up"
              className="inline-block rounded-full px-8 py-3 text-base font-semibold text-white shadow-md transition-all duration-200 hover:shadow-lg"
              style={{
                background: "linear-gradient(to bottom, #4ade80, #22c55e)",
              }}
            >
              Get started free
            </Link>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/70 bg-white/80 p-6 shadow-sm">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-mint-50">
                <FileText className="h-6 w-6 text-mint-600" />
              </div>
              <h3 className="font-semibold text-warm-700">Upload anything</h3>
              <p className="mt-2 text-sm text-warm-500">
                PDFs, Word docs, or screenshots of your syllabus
              </p>
            </div>

            <div className="rounded-2xl border border-white/70 bg-white/80 p-6 shadow-sm">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-mint-50">
                <Sparkles className="h-6 w-6 text-mint-600" />
              </div>
              <h3 className="font-semibold text-warm-700">AI extraction</h3>
              <p className="mt-2 text-sm text-warm-500">
                Automatically find assignments, exams, and due dates
              </p>
            </div>

            <div className="rounded-2xl border border-white/70 bg-white/80 p-6 shadow-sm">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-mint-50">
                <CalendarCheck className="h-6 w-6 text-mint-600" />
              </div>
              <h3 className="font-semibold text-warm-700">Export anywhere</h3>
              <p className="mt-2 text-sm text-warm-500">
                Google Calendar, Outlook, Apple Calendar, and more
              </p>
            </div>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
