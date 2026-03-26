"use client";

import { useState } from "react";
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
    <div className="space-y-3 mt-8">
      <div className="flex flex-wrap gap-3">
        <button
          className="px-4 py-2 rounded-md bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors shadow-sm hover:shadow-md"
          disabled={isDisabled || googleStatus === "loading"}
          onClick={handleGoogleExport}
        >
          {googleStatus === "loading" ? "Exporting..." : "Google Calendar"}
        </button>

        <button
          className="px-4 py-2 rounded-md bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors shadow-sm hover:shadow-md"
          disabled={isDisabled || icsStatus === "loading"}
          onClick={handleIcsExport}
        >
          {icsStatus === "loading" ? "Downloading..." : "Apple Calendar (.ics)"}
        </button>

        <button
          className="px-4 py-2 rounded-md bg-sky-600 hover:bg-sky-700 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors shadow-sm hover:shadow-md"
          disabled={isDisabled || outlookStatus === "loading"}
          onClick={handleOutlookExport}
        >
          {outlookStatus === "loading" ? "Downloading..." : "Outlook (.ics)"}
        </button>
      </div>

      {successMessage && (
        <p className="text-sm text-green-600">{successMessage}</p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  );
}
