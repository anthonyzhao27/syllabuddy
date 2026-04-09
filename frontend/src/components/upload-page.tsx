"use client";

import { motion } from "framer-motion";
import { Header } from "./header";
import { RequireAuth } from "./require-auth";
import { UploadForm } from "./upload-form";

export function UploadPage() {
  return (
    <RequireAuth>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 px-6 pb-16 pt-8 md:px-8 md:pt-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="mx-auto w-full max-w-3xl"
          >
            <div className="rounded-[2rem] border border-white/70 bg-white/85 px-6 py-10 shadow-lg shadow-mint-100/40 backdrop-blur md:px-10">
              <div className="text-center mb-10">
                <h1 className="mt-3 text-4xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
                  Upload your syllabus
                </h1>
                <p className="mt-3 text-lg text-warm-500 font-[family-name:var(--font-nunito)]">
                  Upload a PDF document or a batch of screenshots, then review the
                  saved result in the dashboard.
                </p>
              </div>

              <UploadForm />
            </div>
          </motion.div>
        </main>
      </div>
    </RequireAuth>
  );
}
