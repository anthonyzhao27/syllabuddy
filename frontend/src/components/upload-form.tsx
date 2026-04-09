"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileImage, FileText, Upload } from "lucide-react";
import { parseSyllabus } from "@/lib/api";
import { useParsedData } from "@/contexts/parsed-data-context";
import { LoadingScreen } from "./loading-screen";

const ACCEPTED_TYPES = ".pdf,.docx,.png,.jpg,.jpeg,.webp";
const IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp"];
const DOCUMENT_EXTENSIONS = [".pdf", ".docx"];

function getExtension(filename: string): string {
  const lastDot = filename.lastIndexOf(".");
  return lastDot === -1 ? "" : filename.slice(lastDot).toLowerCase();
}

function isImageFile(file: File): boolean {
  return (
    file.type.startsWith("image/") || IMAGE_EXTENSIONS.includes(getExtension(file.name))
  );
}

function isDocumentFile(file: File): boolean {
  return (
    file.type === "application/pdf" ||
    file.type ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
    DOCUMENT_EXTENSIONS.includes(getExtension(file.name))
  );
}

function validateFiles(files: File[]): string | null {
  if (files.length === 0) {
    return "Please select a file.";
  }

  if (files.every(isImageFile)) {
    return null;
  }

  if (files.length > 1) {
    return "Multiple files are only supported when every file is an image.";
  }

  if (!isDocumentFile(files[0]) && !isImageFile(files[0])) {
    return "Please upload a PDF, DOCX, or image file.";
  }

  return null;
}

export function UploadForm() {
  const router = useRouter();
  const { setData } = useParsedData();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [syllabusName, setSyllabusName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  function updateFiles(nextFiles: File[]) {
    setFiles(nextFiles);
    setError(validateFiles(nextFiles));
  }

  function handleDrag(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();

    if (event.type === "dragenter" || event.type === "dragover") {
      setDragActive(true);
    }

    if (event.type === "dragleave") {
      setDragActive(false);
    }
  }

  function handleDrop(event: React.DragEvent<HTMLDivElement>) {
    event.preventDefault();
    event.stopPropagation();
    setDragActive(false);
    updateFiles(Array.from(event.dataTransfer.files));
  }

  async function handleSubmit() {
    const validationError = validateFiles(files);

    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();

      files.forEach((file) => {
        formData.append("files", file);
      });

      const result = await parseSyllabus(formData);

      setData({
        files,
        events: result.events,
        courseCode: result.courseCode,
        syllabusName: syllabusName.trim(),
      });

      router.push("/results");
    } catch (nextError) {
      setError(
        nextError instanceof Error ? nextError.message : "Something went wrong"
      );
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
          className={`cursor-pointer rounded-[1.75rem] border-2 border-dashed p-8 text-center transition-all duration-200 md:p-12 ${
            dragActive
              ? "border-mint-400 bg-mint-50"
              : "border-warm-200 bg-white hover:border-mint-300 hover:bg-mint-50/30"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            multiple
            onChange={(event) =>
              updateFiles(Array.from(event.target.files ?? []))
            }
            className="hidden"
          />

          {files.length > 0 ? (
            <div className="flex flex-col items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-full bg-mint-100">
                {files.every(isImageFile) ? (
                  <FileImage className="h-7 w-7 text-mint-600" />
                ) : (
                  <FileText className="h-7 w-7 text-mint-600" />
                )}
              </div>

              <div>
                <p className="text-base font-semibold text-warm-700">
                  {files.length === 1
                    ? files[0].name
                    : `${files.length} screenshot files selected`}
                </p>
                <p className="mt-1 text-sm text-warm-400">
                  {files.every(isImageFile)
                    ? "Screenshot parsing"
                    : "Single document parsing"}
                </p>
              </div>

              <ul className="w-full max-w-md space-y-2 text-left">
                {files.map((file) => (
                  <li
                    key={`${file.name}-${file.size}`}
                    className="truncate rounded-xl bg-warm-50 px-3 py-2 text-sm text-warm-500"
                  >
                    {file.name}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-mint-100">
                <Upload className="h-8 w-8 text-mint-500" />
              </div>
              <div>
                <p className="mb-1 font-medium text-warm-700">
                  Drop a syllabus or screenshots here
                </p>
                <p className="text-sm text-warm-400">
                  One PDF or DOCX, or multiple image screenshots
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <label
            htmlFor="syllabus-name"
            className="block text-sm font-medium text-warm-500"
          >
            Syllabus name (optional)
          </label>
          <input
            id="syllabus-name"
            type="text"
            value={syllabusName}
            onChange={(event) => setSyllabusName(event.target.value)}
            placeholder="e.g. CSC 209 Winter 2026"
            className="w-full rounded-xl border border-warm-200 bg-white px-4 py-3 text-sm text-warm-700 transition-all duration-200 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
          />
        </div>

        {error ? (
          <div className="rounded-xl border border-error/20 bg-error-light px-4 py-3">
            <p className="text-sm font-medium text-error">{error}</p>
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => void handleSubmit()}
          disabled={loading}
          className="w-full rounded-2xl py-3.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: "linear-gradient(to bottom, #4ade80, #22c55e)",
          }}
        >
          {loading ? "Parsing..." : "Parse syllabus"}
        </button>
      </div>
    </>
  );
}
