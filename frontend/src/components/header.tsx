"use client";

import { Calendar } from "lucide-react";

export function Header() {
  return (
    <header className="w-full py-6 px-8">
      <div className="flex items-center gap-2">
        <Calendar className="w-7 h-7 text-mint-500" />
        <h1 className="text-2xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
          Syllabuddy
        </h1>
      </div>
    </header>
  );
}
