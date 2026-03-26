"use client";

import { useState } from "react";
import { Calendar, Apple, Mail, CheckCircle } from "lucide-react";
import {
  exportToIcs,
  exportToOutlook,
  exportToGoogleCalendar,
} from "@/lib/api";
import { getGoogleAccessToken } from "@/lib/google-auth";
import type { ParsedEvent } from "@/types";

type ExportButtonsProps = {
  events: ParsedEvent[];
  timezone: string;
};

type ExportStatus = "idle" | "loading" | "success" | "error";

export function ExportButtons({ events, timezone }: ExportButtonsProps) {
  const [icsStatus, setIcsStatus] = useState<ExportStatus>("idle");
  const [outlookStatus, setOutlookStatus] = useState<ExportStatus>("idle");
  const [googleStatus, setGoogleStatus] = useState<ExportStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const isDisabled = events.length === 0;

  const handleIcsExport = async () => {
    setIcsStatus("loading");
    setError(null);
    setSuccessMessage(null);
    try {
      await exportToIcs(events, timezone);
      setIcsStatus("success");
      setSuccessMessage("Calendar file downloaded");
    } catch (err) {
      setIcsStatus("error");
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  const handleOutlookExport = async () => {
    setOutlookStatus("loading");
    setError(null);
    setSuccessMessage(null);

    try {
      await exportToOutlook(events, timezone);
      setOutlookStatus("success");
      setSuccessMessage("Calendar file downloaded for Outlook");
    } catch (err) {
      setOutlookStatus("error");
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  const handleGoogleExport = async () => {
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
    } catch (err) {
      setGoogleStatus("error");
      setError(err instanceof Error ? err.message : "Export failed");
    }
  };

  return (
    <div className="mt-6 space-y-4">
      <p className="text-sm font-medium text-warm-600 text-center">
        Export to your calendar
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        <ExportButton
          onClick={handleGoogleExport}
          disabled={isDisabled}
          loading={googleStatus === "loading"}
          success={googleStatus === "success"}
          icon={<Calendar className="w-4 h-4" />}
          label="Google Calendar"
          variant="google"
        />

        <ExportButton
          onClick={handleIcsExport}
          disabled={isDisabled}
          loading={icsStatus === "loading"}
          success={icsStatus === "success"}
          icon={<Apple className="w-4 h-4" />}
          label="Apple Calendar"
          variant="apple"
        />

        <ExportButton
          onClick={handleOutlookExport}
          disabled={isDisabled}
          loading={outlookStatus === "loading"}
          success={outlookStatus === "success"}
          icon={<Mail className="w-4 h-4" />}
          label="Outlook"
          variant="outlook"
        />
      </div>

      {successMessage && (
        <div className="flex items-center justify-center gap-2 text-sm text-success font-medium">
          <CheckCircle className="w-4 h-4" />
          {successMessage}
        </div>
      )}
      {error && (
        <p className="text-sm text-error text-center font-medium">{error}</p>
      )}
    </div>
  );
}

type ExportButtonProps = {
  onClick: () => void;
  disabled: boolean;
  loading: boolean;
  success: boolean;
  icon: React.ReactNode;
  label: string;
  variant: "google" | "apple" | "outlook";
};

const VARIANT_STYLES = {
  google: {
    gradient: "linear-gradient(to bottom, #60a5fa, #3b82f6)",
    hoverGradient: "linear-gradient(to bottom, #3b82f6, #2563eb)",
  },
  apple: {
    gradient: "linear-gradient(to bottom, #4ade80, #22c55e)",
    hoverGradient: "linear-gradient(to bottom, #22c55e, #16a34a)",
  },
  outlook: {
    gradient: "linear-gradient(to bottom, #38bdf8, #0ea5e9)",
    hoverGradient: "linear-gradient(to bottom, #0ea5e9, #0284c7)",
  },
};

function ExportButton({
  onClick,
  disabled,
  loading,
  success,
  icon,
  label,
  variant,
}: ExportButtonProps) {
  const styles = VARIANT_STYLES[variant];

  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-white text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98]"
      style={{ background: styles.gradient }}
      onMouseEnter={(e) => {
        if (!disabled && !loading) {
          e.currentTarget.style.background = styles.hoverGradient;
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = styles.gradient;
      }}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
      ) : success ? (
        <CheckCircle className="w-4 h-4" />
      ) : (
        icon
      )}
      {loading ? "Exporting..." : label}
    </button>
  );
}
