"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { Calendar, CheckCircle } from "lucide-react";
import { exportToIcs } from "@/lib/api";
import type { SavedEvent } from "@/types";

type ExportButtonsProps = {
  events: SavedEvent[];
  timezone: string;
};

type ExportStatus = "idle" | "loading" | "success" | "error";

type ExportButtonProps = {
  onClick: () => void;
  disabled: boolean;
  loading: boolean;
  success: boolean;
  icon: ReactNode;
  label: string;
};

const BUTTON_GRADIENT = "linear-gradient(to bottom, #4ade80, #22c55e)";

export function ExportButtons({ events, timezone }: ExportButtonsProps) {
  const [icsStatus, setIcsStatus] = useState<ExportStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const disabled = events.length === 0;

  async function handleIcsExport() {
    setIcsStatus("loading");
    setError(null);
    setSuccessMessage(null);

    try {
      await exportToIcs(events, timezone);
      setIcsStatus("success");
      setSuccessMessage("Calendar file downloaded");
    } catch (nextError) {
      setIcsStatus("error");
      setError(
        nextError instanceof Error ? nextError.message : "Export failed"
      );
    }
  }

  return (
    <div className="mt-6 space-y-4">
      <p className="text-center text-sm font-medium text-warm-600">
        Export to your calendar
      </p>

      <div className="flex flex-wrap justify-center gap-3">
        <ExportButton
          onClick={() => void handleIcsExport()}
          disabled={disabled}
          loading={icsStatus === "loading"}
          success={icsStatus === "success"}
          icon={<Calendar className="h-4 w-4" />}
          label="Export to calendar (.ics)"
        />
      </div>

      <p className="text-center text-xs text-warm-400">
        Works with Apple Calendar, Google Calendar, and Outlook
      </p>

      {successMessage ? (
        <div className="flex items-center justify-center gap-2 text-sm font-medium text-success">
          <CheckCircle className="h-4 w-4" />
          {successMessage}
        </div>
      ) : null}

      {error ? <p className="text-center text-sm font-medium text-error">{error}</p> : null}
    </div>
  );
}

function ExportButton({
  onClick,
  disabled,
  loading,
  success,
  icon,
  label,
}: ExportButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className="inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
      style={{ background: BUTTON_GRADIENT }}
    >
      {loading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
      ) : success ? (
        <CheckCircle className="h-4 w-4" />
      ) : (
        icon
      )}
      {loading ? "Exporting..." : label}
    </button>
  );
}
