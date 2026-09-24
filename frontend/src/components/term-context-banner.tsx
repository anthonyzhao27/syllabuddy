"use client";

import { useState } from "react";
import { CalendarClock } from "lucide-react";
import { ConfirmDialog } from "@/components/confirm-dialog";
import type {
  TermAnchorSource,
  TermContext,
  TermOverride,
  TermSeason,
} from "@/types";

type TermContextBannerConfirmCopy = {
  title: string;
  message: string;
  confirmText: string;
};

type TermContextBannerProps = {
  termContext: TermContext;
  // When true, Apply asks for confirmation first.
  hasEdits: boolean;
  onApply?: (override: TermOverride) => Promise<void>;
  confirmCopy?: TermContextBannerConfirmCopy;
};

const DEFAULT_CONFIRM_COPY: TermContextBannerConfirmCopy = {
  title: "Replace edited events?",
  message:
    "Re-dating replaces the event list, so your edits and deletions will be lost.",
  confirmText: "Replace",
};

const SEASON_OPTIONS: { value: TermSeason; label: string }[] = [
  { value: "fall", label: "Fall" },
  { value: "winter", label: "Winter" },
  { value: "summer", label: "Summer" },
  { value: "full_year", label: "Full year" },
];

const ANCHOR_SOURCE_NOTES: Record<TermAnchorSource, string> = {
  user: "Set by you",
  syllabus_anchor: "Week 1 date taken from your syllabus",
  syllabus_dates: "Matched to dates in your syllabus",
  table: "From the UofT academic calendar",
  heuristic: "Best guess, please double-check",
};

const inputClassName =
  "mt-1 w-full rounded-xl border border-warm-200 bg-white px-3 py-2 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100";

function formatShortDate(value: string): string {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

export function TermContextBanner({
  termContext,
  hasEdits,
  onApply,
  confirmCopy = DEFAULT_CONFIRM_COPY,
}: TermContextBannerProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [season, setSeason] = useState<TermSeason>(termContext.season);
  const [year, setYear] = useState(String(termContext.year));
  const [week1Monday, setWeek1Monday] = useState(termContext.week1Monday);
  const [readingWeekNumbered, setReadingWeekNumbered] = useState(
    termContext.readingWeekNumbered
  );
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  // Only send what the user changed, so untouched fields stay inferred.
  const override: TermOverride = {};

  if (season !== termContext.season) {
    override.season = season;
  }

  if (Number(year) !== termContext.year) {
    override.year = Number(year);
  }

  if (week1Monday && week1Monday !== termContext.week1Monday) {
    override.week1Monday = week1Monday;
  }

  if (readingWeekNumbered !== termContext.readingWeekNumbered) {
    override.readingWeekNumbered = readingWeekNumbered;
  }

  const hasChanges = Object.keys(override).length > 0;

  function handleToggleEdit() {
    if (!isEditing) {
      setSeason(termContext.season);
      setYear(String(termContext.year));
      setWeek1Monday(termContext.week1Monday);
      setReadingWeekNumbered(termContext.readingWeekNumbered);
      setError(null);
    }

    setIsEditing((current) => !current);
  }

  async function applyOverride() {
    if (!onApply) {
      return;
    }

    setShowConfirmDialog(false);
    setApplying(true);
    setError(null);

    try {
      await onApply(override);
      setIsEditing(false);
    } catch (nextError) {
      setError(
        nextError instanceof Error ? nextError.message : "Failed to update dates"
      );
    } finally {
      setApplying(false);
    }
  }

  function handleApply() {
    const parsedYear = Number(year);

    if (!Number.isInteger(parsedYear) || parsedYear < 2000 || parsedYear > 2100) {
      setError("Enter a valid year.");
      return;
    }

    if (hasEdits) {
      setShowConfirmDialog(true);
      return;
    }

    void applyOverride();
  }

  return (
    <div className="rounded-2xl border border-mint-200 bg-mint-50 px-4 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-2">
          <CalendarClock className="mt-0.5 h-4 w-4 shrink-0 text-mint-700" />
          <div className="min-w-0">
            <p className="text-sm font-medium text-warm-700">
              Dates based on {termContext.label} · Week 1 starts{" "}
              {formatShortDate(termContext.week1Monday)}
            </p>
            <p className="mt-0.5 text-xs text-warm-500">
              {ANCHOR_SOURCE_NOTES[termContext.anchorSource]}
            </p>
          </div>
        </div>

        {onApply ? (
          <button
            type="button"
            onClick={handleToggleEdit}
            aria-expanded={isEditing}
            className="text-sm font-semibold text-mint-700 transition-colors hover:text-mint-600"
          >
            {isEditing ? "Close" : "Edit"}
          </button>
        ) : null}
      </div>

      {isEditing ? (
        <div className="mt-4 space-y-4 rounded-xl bg-white/80 p-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label
                htmlFor="term-season"
                className="block text-xs font-medium text-warm-600"
              >
                Term
              </label>
              <select
                id="term-season"
                value={season}
                onChange={(e) => setSeason(e.target.value as TermSeason)}
                className={inputClassName}
              >
                {SEASON_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label
                htmlFor="term-year"
                className="block text-xs font-medium text-warm-600"
              >
                Year
              </label>
              <input
                id="term-year"
                type="number"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className={inputClassName}
              />
            </div>
            <div>
              <label
                htmlFor="term-week1-monday"
                className="block text-xs font-medium text-warm-600"
              >
                Week 1 Monday
              </label>
              <input
                id="term-week1-monday"
                type="date"
                value={week1Monday}
                onChange={(e) => setWeek1Monday(e.target.value)}
                className={inputClassName}
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-warm-600">
            <input
              type="checkbox"
              checked={readingWeekNumbered}
              onChange={(e) => setReadingWeekNumbered(e.target.checked)}
              className="h-4 w-4 rounded border-warm-300 accent-mint-500"
            />
            Syllabus counts reading week as a week
          </label>

          {error ? <p className="text-sm text-error">{error}</p> : null}

          <button
            type="button"
            onClick={handleApply}
            disabled={applying || !hasChanges}
            className="rounded-xl px-5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-60"
            style={{
              background: "linear-gradient(to bottom, #4ade80, #22c55e)",
            }}
          >
            {applying ? "Applying..." : "Apply"}
          </button>
        </div>
      ) : null}

      <ConfirmDialog
        isOpen={showConfirmDialog}
        onCancel={() => setShowConfirmDialog(false)}
        onConfirm={() => void applyOverride()}
        title={confirmCopy.title}
        message={confirmCopy.message}
        confirmText={confirmCopy.confirmText}
      />
    </div>
  );
}
