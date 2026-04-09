"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { getLoginHref } from "@/lib/auth-redirect";

type RequireAuthProps = {
  children: ReactNode;
};

export function RequireAuth({ children }: RequireAuthProps) {
  const { user, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();

  const next = searchParams.toString()
    ? `${pathname}?${searchParams.toString()}`
    : pathname;

  useEffect(() => {
    if (!loading && !user) {
      // Don't add ?next= if already heading to /login
      if (pathname === "/login") {
        return;
      }
      router.replace(getLoginHref(next));
    }
  }, [loading, next, pathname, router, user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center px-6">
        <p className="text-sm font-medium text-warm-500">Checking session...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
}
