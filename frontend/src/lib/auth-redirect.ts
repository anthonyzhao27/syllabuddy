export function getSafeNext(next: string | null | undefined): string {
  if (!next) {
    return "/dashboard";
  }

  if (!next.startsWith("/")) {
    return "/dashboard";
  }

  if (next.startsWith("//")) {
    return "/dashboard";
  }

  return next;
}

export function getLoginHref(next: string | null | undefined): string {
  return `/login?next=${encodeURIComponent(getSafeNext(next))}`;
}

export function getCurrentPath(): string {
  if (typeof window === "undefined") {
    return "/";
  }

  const { pathname, search } = window.location;
  return getSafeNext(search ? `${pathname}${search}` : pathname);
}

export function redirectToLogin(next: string | null | undefined): void {
  if (typeof window === "undefined") {
    return;
  }

  window.location.assign(getLoginHref(next));
}
