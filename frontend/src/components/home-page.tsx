import { UploadForm } from "./upload-form";

export function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-8">Syllabus Parser</h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-400 mb-8 text-center max-w-md">
        Upload your course syllabus and we&apos;ll extract all your assignments and due dates.
      </p>
      <UploadForm />
    </main>
  );
}
