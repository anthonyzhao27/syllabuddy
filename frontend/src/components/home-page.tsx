"use client";

import { motion } from "framer-motion";
import { Header } from "./header";
import { UploadForm } from "./upload-form";

export function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex flex-col items-center justify-center px-8 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="w-full max-w-2xl"
        >
          <div className="text-center mb-10">
            <h1 className="text-4xl font-semibold text-warm-700 mb-3 font-[family-name:var(--font-quicksand)]">
              Upload your syllabus
            </h1>
            <p className="text-lg text-warm-500 font-[family-name:var(--font-nunito)]">
              We&apos;ll extract all your assignments and due dates, ready to
              export to your calendar.
            </p>
          </div>
          <UploadForm />
        </motion.div>
      </main>
    </div>
  );
}
