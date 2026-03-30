"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText } from "lucide-react";
import { parseSyllabus } from "@/lib/api";
import { LoadingScreen } from "./loading-screen";

const ACCEPTED_TYPES = ".pdf,.docx,.png,.jpg,.jpeg,.webp";

export function UploadForm() {
  const router = useRouter();

  const [file, setFile] = useState<File | null>(null);
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

      if (!file) {
        setError("Please select a file.");
        setLoading(false);
        return;
      }
      formData.append("files", file);

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
      setLoading(false);
    }
  }

  return (
    <>
      <LoadingScreen isVisible={loading} />
      <div className="w-full space-y-6">
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-200 ${
            dragActive
              ? "border-mint-400 bg-mint-50"
              : "border-warm-200 bg-white hover:border-mint-300 hover:bg-mint-50/30"
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
            <div className="flex flex-col items-center gap-2">
              <div className="w-12 h-12 rounded-full bg-mint-100 flex items-center justify-center">
                <FileText className="w-6 h-6 text-mint-600" />
              </div>
              <p className="text-sm font-medium text-warm-700">{file.name}</p>
              <p className="text-xs text-warm-400">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-14 h-14 rounded-full bg-mint-100 flex items-center justify-center">
                <Upload className="w-7 h-7 text-mint-500" />
              </div>
              <div>
                <p className="text-warm-700 font-medium mb-1">
                  Drop a file here or click to browse
                </p>
                <p className="text-sm text-warm-400">
                  PDF, DOCX, or image (PNG, JPG, WebP)
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-warm-500 mb-1.5">
              Semester start (optional)
            </label>
            <input
              type="date"
              value={semesterStart}
              onChange={(e) => setSemesterStart(e.target.value)}
              className="w-full bg-white border border-warm-200 rounded-lg px-3 py-2.5 text-sm text-warm-700 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100 transition-all duration-200"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-warm-500 mb-1.5">
              Semester end (optional)
            </label>
            <input
              type="date"
              value={semesterEnd}
              onChange={(e) => setSemesterEnd(e.target.value)}
              className="w-full bg-white border border-warm-200 rounded-lg px-3 py-2.5 text-sm text-warm-700 focus:outline-none focus:border-mint-400 focus:ring-2 focus:ring-mint-100 transition-all duration-200"
            />
          </div>
        </div>

        {error && (
          <div className="bg-error-light border border-error/20 rounded-lg px-4 py-3">
            <p className="text-sm text-error font-medium">{error}</p>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-3.5 rounded-xl text-white text-sm font-semibold disabled:opacity-50 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-md active:scale-[0.98]"
          style={{
            background: "linear-gradient(to bottom, #4ade80, #22c55e)",
          }}
          onMouseEnter={(e) => {
            if (!loading) {
              e.currentTarget.style.background =
                "linear-gradient(to bottom, #22c55e, #16a34a)";
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background =
              "linear-gradient(to bottom, #4ade80, #22c55e)";
          }}
        >
          {loading ? "Parsing..." : "Parse Syllabus"}
        </button>
      </div>
    </>
  );
}
