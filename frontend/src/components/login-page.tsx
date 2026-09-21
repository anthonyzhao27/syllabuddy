"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Header } from "./header";
import { useAuth } from "@/contexts/auth-context";
import { getSafeNext } from "@/lib/auth-redirect";

type LoginMode = "sign-in" | "sign-up";

export function LoginPage() {
  const { loading, session, signIn, signUp } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const safeNext = getSafeNext(searchParams.get("next"));

  const initialMode = searchParams.get("mode") === "sign-up" ? "sign-up" : "sign-in";
  const [mode, setMode] = useState<LoginMode>(initialMode);

  // Sign-up goes to /upload, sign-in goes to /dashboard
  const redirectPath = mode === "sign-up" ? "/upload" : "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // If already logged in, redirect based on explicit next param (if valid) or mode
  // Only use safeNext if it's a real path, not the fallback "/dashboard"
  const hasValidNext = searchParams.get("next") && safeNext !== "/dashboard";
  const sessionRedirect = hasValidNext ? safeNext : redirectPath;

  useEffect(() => {
    if (!loading && session) {
      router.replace(sessionRedirect);
    }
  }, [loading, router, sessionRedirect, session]);

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    setInfo(null);

    const result =
      mode === "sign-in"
        ? await signIn({ email, password })
        : await signUp({
            email,
            password,
            emailRedirectTo: `${window.location.origin}/login?next=${encodeURIComponent("/upload")}`,
          });

    setSubmitting(false);

    if (result.error) {
      setError(result.error.message);
      return;
    }

    if (mode === "sign-up" && result.requiresEmailConfirmation) {
      setInfo("Check your email to confirm your account, then sign in.");
      return;
    }

    // Redirect is handled by useEffect when session changes
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex flex-1 items-center justify-center px-6 pb-16 pt-28 md:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="w-full max-w-md rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-lg shadow-mint-100/40"
        >
          <div className="mb-8 text-center">
            <h1 className="mt-3 text-3xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
              {mode === "sign-in" ? "Sign in" : "Create account"}
            </h1>
            <p className="mt-2 text-sm text-warm-500">
              Sign in to upload, save, and manage your parsed syllabi.
            </p>
          </div>

          <div className="mb-6 grid grid-cols-2 rounded-full border border-warm-200 bg-warm-50 p-1">
            <button
              type="button"
              onClick={() => setMode("sign-in")}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                mode === "sign-in"
                  ? "bg-white text-warm-700 shadow-sm"
                  : "text-warm-500"
              }`}
            >
              Sign in
            </button>
            <button
              type="button"
              onClick={() => setMode("sign-up")}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                mode === "sign-up"
                  ? "bg-white text-warm-700 shadow-sm"
                  : "text-warm-500"
              }`}
            >
              Sign up
            </button>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label
                htmlFor="login-email"
                className="block text-sm font-medium text-warm-500"
              >
                Email
              </label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="off"
                autoCorrect="off"
                autoCapitalize="off"
                spellCheck="false"
                data-form-type="other"
                className="w-full rounded-xl border border-warm-200 bg-white px-4 py-3 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
              />
            </div>

            <div className="space-y-2">
              <label
                htmlFor="login-password"
                className="block text-sm font-medium text-warm-500"
              >
                Password
              </label>
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="new-password"
                data-form-type="other"
                className="w-full rounded-xl border border-warm-200 bg-white px-4 py-3 text-sm text-warm-700 focus:border-mint-400 focus:outline-none focus:ring-2 focus:ring-mint-100"
              />
            </div>

            {error ? (
              <div className="rounded-xl border border-error/20 bg-error-light px-4 py-3">
                <p className="text-sm font-medium text-error">{error}</p>
              </div>
            ) : null}

            {info ? (
              <div className="rounded-xl border border-mint-200 bg-mint-50 px-4 py-3">
                <p className="text-sm font-medium text-mint-700">{info}</p>
              </div>
            ) : null}

            <button
              type="button"
              onClick={() => void handleSubmit()}
              disabled={submitting || loading}
              className="w-full rounded-xl py-3 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
              style={{
                background: "linear-gradient(to bottom, #4ade80, #22c55e)",
              }}
            >
              {submitting
                ? mode === "sign-in"
                  ? "Signing in..."
                  : "Creating account..."
                : mode === "sign-in"
                ? "Sign in"
                : "Create account"}
            </button>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
