"use client";

import type { ReactNode } from "react";
import { AuthProvider } from "@/contexts/auth-context";
import { ParsedDataProvider } from "@/contexts/parsed-data-context";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <ParsedDataProvider>{children}</ParsedDataProvider>
    </AuthProvider>
  );
}
