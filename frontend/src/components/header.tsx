"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  Calendar,
  ChevronDown,
  FolderOpen,
  LogOut,
  Upload,
  UserCircle2,
} from "lucide-react";
import { useAuth } from "@/contexts/auth-context";

type NavItem = {
  href: string;
  label: string;
  icon: ReactNode;
  isActive: (pathname: string) => boolean;
};

const NAV_ITEMS: NavItem[] = [
  {
    href: "/upload",
    label: "Upload",
    icon: <Upload className="w-4 h-4" />,
    isActive: (pathname) => pathname === "/upload",
  },
  {
    href: "/dashboard",
    label: "My syllabi",
    icon: <FolderOpen className="w-4 h-4" />,
    isActive: (pathname) => pathname.startsWith("/dashboard"),
  },
];

export function Header() {
  const { signOut, user } = useAuth();
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [menuError, setMenuError] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      const target = event.target;

      if (target instanceof Node && !menuRef.current?.contains(target)) {
        setMenuOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  async function handleSignOut() {
    setSigningOut(true);
    setMenuError(null);

    const result = await signOut();

    if (result.error) {
      setSigningOut(false);
      setMenuError(result.error.message);
      return;
    }

    // Use window.location for a full page redirect to avoid race with RequireAuth
    window.location.href = "/login";
  }

  return (
    <header className="fixed top-0 left-0 z-50 w-full bg-cream px-6 py-6 md:px-8">
      <div className="mx-auto flex w-full max-w-6xl items-center gap-4">
        <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2">
          <Calendar className="h-7 w-7 text-mint-500" />
          <span className="text-2xl font-semibold text-warm-700 font-[family-name:var(--font-quicksand)]">
            Syllabuddy
          </span>
        </Link>

        {user ? (
          <div className="ml-auto flex items-center gap-3">
            <nav className="hidden items-center gap-2 rounded-full border border-white/70 bg-white/70 p-1 shadow-sm md:flex">
              {NAV_ITEMS.map((item) => {
                const active = item.isActive(pathname);

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                      active
                        ? "bg-mint-500 text-white"
                        : "text-warm-500 hover:bg-warm-50 hover:text-warm-700"
                    }`}
                  >
                    {item.icon}
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="relative" ref={menuRef}>
              <button
                type="button"
                onClick={() => setMenuOpen((current) => !current)}
                className="inline-flex items-center gap-2 rounded-full border border-white/70 bg-white px-3 py-2 text-sm font-semibold text-warm-600 shadow-sm transition-colors hover:border-mint-200 hover:text-warm-700"
                aria-expanded={menuOpen}
                aria-label="Open account menu"
              >
                <UserCircle2 className="h-5 w-5 text-mint-500" />
                <span className="hidden max-w-40 truncate sm:block">
                  {user.email}
                </span>
                <ChevronDown className="h-4 w-4" />
              </button>

              <AnimatePresence>
                {menuOpen ? (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.16, ease: "easeOut" }}
                    className="absolute right-0 top-[calc(100%+0.75rem)] z-30 w-64 rounded-2xl border border-warm-100 bg-white p-3 shadow-lg"
                  >
                    <div className="rounded-xl bg-warm-50 px-3 py-2">
                      <p className="text-xs font-medium uppercase tracking-wide text-warm-400">
                        Signed in as
                      </p>
                      <p className="mt-1 truncate text-sm font-semibold text-warm-700">
                        {user.email}
                      </p>
                    </div>

                    <div className="mt-3 space-y-1 md:hidden">
                      {NAV_ITEMS.map((item) => {
                        const active = item.isActive(pathname);

                        return (
                          <Link
                            key={item.href}
                            href={item.href}
                            onClick={() => setMenuOpen(false)}
                            className={`flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-semibold transition-colors ${
                              active
                                ? "bg-mint-50 text-mint-700"
                                : "text-warm-500 hover:bg-warm-50 hover:text-warm-700"
                            }`}
                          >
                            {item.icon}
                            {item.label}
                          </Link>
                        );
                      })}
                    </div>

                    <button
                      type="button"
                      onClick={() => void handleSignOut()}
                      disabled={signingOut}
                      className="mt-3 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm font-semibold text-warm-600 transition-colors hover:bg-warm-50 hover:text-warm-800 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <LogOut className="h-4 w-4" />
                      {signingOut ? "Signing out..." : "Sign out"}
                    </button>

                    {menuError ? (
                      <p className="mt-2 text-sm text-error">{menuError}</p>
                    ) : null}
                  </motion.div>
                ) : null}
              </AnimatePresence>
            </div>
          </div>
        ) : null}
      </div>
    </header>
  );
}
