"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { Apple, Calendar, CheckCircle, Mail } from "lucide-react";
import {
  exportToGoogleCalendar,
  exportToIcs,
  exportToOutlook,
} from "@/lib/api";
import { getGoogleAccessToken } from "@/lib/google-auth";
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
  variant: "google" | "apple" | "outlook";
};

const VARIANT_STYLES = {
  google: {
    gradient: "linear-gradient(to bottom, #60a5fa, #3b82f6)",
  },
  apple: {
    gradient: "linear-gradient(to bottom, #4ade80, #22c55e)",
  },
  outlook: {
    gradient: "linear-gradient(to bottom, #38bdf8, #0ea5e9)",
  },
} as const;

export function ExportButtons({ events, timezone }: ExportButtonsProps) {
  const [icsStatus, setIcsStatus] = useState<ExportStatus>("idle");
  const [outlookStatus, setOutlookStatus] = useState<ExportStatus>("idle");
  const [googleStatus, setGoogleStatus] = useState<ExportStatus>("idle");
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

  async function handleOutlookExport() {
    setOutlookStatus("loading");
    setError(null);
    setSuccessMessage(null);

    try {
      await exportToOutlook(events, timezone);
      setOutlookStatus("success");
      setSuccessMessage("Calendar file downloaded for Outlook");
    } catch (nextError) {
      setOutlookStatus("error");
      setError(
        nextError instanceof Error ? nextError.message : "Export failed"
      );
    }
  }

  async function handleGoogleExport() {
    setGoogleStatus("loading");
    setError(null);
    setSuccessMessage(null);

    try {
      const accessToken = await getGoogleAccessToken();
      const result = await exportToGoogleCalendar(events, accessToken, timezone);

      setGoogleStatus("success");
      setSuccessMessage(
        `${result.created_count} event(s) added to "${result.calendar_name}"`
      );

      if (result.errors.length > 0) {
        setError(`${result.errors.length} event(s) failed to export`);
      }
    } catch (nextError) {
      setGoogleStatus("error");
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
          onClick={() => void handleGoogleExport()}
          disabled={disabled}
          loading={googleStatus === "loading"}
          success={googleStatus === "success"}
          icon={<Calendar className="h-4 w-4" />}
          label="Google Calendar"
          variant="google"
        />

        <ExportButton
          onClick={() => void handleIcsExport()}
          disabled={disabled}
          loading={icsStatus === "loading"}
          success={icsStatus === "success"}
          icon={<Apple className="h-4 w-4" />}
          label="Apple Calendar"
          variant="apple"
        />

        <ExportButton
          onClick={() => void handleOutlookExport()}
          disabled={disabled}
          loading={outlookStatus === "loading"}
          success={outlookStatus === "success"}
          icon={<Mail className="h-4 w-4" />}
          label="Outlook"
          variant="outlook"
        />
      </div>

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
  variant,
}: ExportButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled || loading}
      className="inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
      style={{ background: VARIANT_STYLES[variant].gradient }}
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
