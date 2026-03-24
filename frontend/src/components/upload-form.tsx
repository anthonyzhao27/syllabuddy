"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { parseSyllabus } from "@/lib/api";
import type { UploadMode } from "@/types";

const ACCEPTED_TYPES = ".pdf,.docx,.html,.htm,.png,.jpg,.jpeg,.webp";

const MODES: { key: UploadMode; label: string }[] = [
  { key: "file", label: "File Upload" },
  { key: "url", label: "Google Docs URL" },
  { key: "paste", label: "Paste HTML" },
];

export function UploadForm() {
  const router = useRouter();

  const [mode, setMode] = useState<UploadMode>("file");
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [html, setHtml] = useState("");
  const [semesterStart, setSemesterStart] = useState("");
  const [semesterEnd, setSemesterEnd] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleDrag(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    if (e.type === "dragleave") setDragActive(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  }

  async function handleSubmit() {
    setError(null);
    setLoading(true);

    try {
      const formData = new FormData();

      if (mode === "file" && file) {
        formData.append("files", file);
      } else if (mode === "url" && url.trim()) {
        formData.append("google_doc_url", url.trim());
      } else if (mode === "paste" && html.trim()) {
        const blob = new Blob([html], { type: "text/html" });
        formData.append("files", blob, "pasted.html");
      } else {
        setError("Please provide a file, URL, or pasted content.");
        setLoading(false);
        return;
      }

      const result = await parseSyllabus(formData);

      sessionStorage.setItem(
        "parseResult",
        JSON.stringify({
          ...result,
          semesterStart: semesterStart || undefined,
          semesterEnd: semesterEnd || undefined,
        })
      );
      router.push("/results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-lg space-y-6">
      {/* Mode tabs */}
      <div className="flex gap-2 p-1 bg-white/50 rounded-lg">
        {MODES.map((m) => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-all cursor-pointer ${
              mode === m.key
                ? "bg-white text-sage-800 shadow-sm"
                : "text-sage-600/70 hover:text-sage-800 hover:bg-white/50"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* File upload drop zone */}
      {mode === "file" && (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-all ${
            dragActive
              ? "border-sage-500 bg-sage-100/50"
              : "border-sage-400 bg-white/60 hover:border-sage-500 hover:bg-white/80"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
          {file ? (
            <p className="text-sm text-sage-800">
              {file.name}{" "}
              <span className="text-sage-600">
                ({(file.size / 1024).toFixed(1)} KB)
              </span>
            </p>
          ) : (
            <>
              <p className="text-sage-700 mb-1 font-medium">
                Drop a file here or click to browse
              </p>
              <p className="text-xs text-sage-600/70">
                PDF, DOCX, HTML, or image (PNG, JPG, WebP)
              </p>
            </>
          )}
        </div>
      )}

      {/* URL input */}
      {mode === "url" && (
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://docs.google.com/document/d/..."
          className="w-full bg-white/70 border border-sage-300 rounded-lg px-4 py-3 text-sm text-sage-800 placeholder:text-sage-500 focus:outline-none focus:border-sage-500 focus:bg-white/90 transition-colors"
        />
      )}

      {/* HTML paste textarea */}
      {mode === "paste" && (
        <textarea
          value={html}
          onChange={(e) => setHtml(e.target.value)}
          placeholder="Paste your syllabus HTML content here..."
          rows={6}
          className="w-full bg-white/70 border border-sage-300 rounded-lg px-4 py-3 text-sm text-sage-800 placeholder:text-sage-500 focus:outline-none focus:border-sage-500 focus:bg-white/90 transition-colors resize-none"
        />
      )}

      {/* Semester date inputs */}
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="block text-xs text-sage-600 mb-1">
            Semester start (optional)
          </label>
          <input
            type="date"
            value={semesterStart}
            onChange={(e) => setSemesterStart(e.target.value)}
            className="w-full bg-white/60 border border-sage-300 rounded-md px-3 py-2 text-sm text-sage-800 focus:outline-none focus:border-sage-500 transition-colors"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs text-sage-600 mb-1">
            Semester end (optional)
          </label>
          <input
            type="date"
            value={semesterEnd}
            onChange={(e) => setSemesterEnd(e.target.value)}
            className="w-full bg-white/60 border border-sage-300 rounded-md px-3 py-2 text-sm text-sage-800 focus:outline-none focus:border-sage-500 transition-colors"
          />
        </div>
      </div>

      {/* Error message */}
      {error && (
        <p className="text-sm text-red-600 text-center font-medium">{error}</p>
      )}

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full py-3 rounded-lg bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold disabled:opacity-50 transition-colors cursor-pointer shadow-sm hover:shadow-md"
      >
        {loading ? "Parsing..." : "Parse Syllabus"}
      </button>
    </div>
  );
}
