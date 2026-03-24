import { UploadForm } from "./upload-form";

export function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-4 text-emerald-900">Syllabus Parser</h1>
      <p className="text-lg text-emerald-800/90 mb-10 text-center max-w-md">
        Upload your course syllabus and we&apos;ll extract all your assignments and due dates.
      </p>
      <UploadForm />
    </main>
  );
}
