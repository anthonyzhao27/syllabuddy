import {
  getCurrentPath,
  getLoginHref,
  getSafeNext,
} from "@/lib/auth-redirect";

describe("auth redirect helpers", () => {
  it("keeps safe internal paths", () => {
    expect(getSafeNext("/dashboard/123?from=parse")).toBe(
      "/dashboard/123?from=parse"
    );
  });

  it("falls back to root for invalid next values", () => {
    expect(getSafeNext("https://example.com")).toBe("/");
    expect(getSafeNext("//evil.example.com")).toBe("/");
    expect(getSafeNext("dashboard")).toBe("/");
    expect(getSafeNext(null)).toBe("/");
  });

  it("builds login redirects with encoded next params", () => {
    expect(getLoginHref("/dashboard/123?from=parse")).toBe(
      "/login?next=%2Fdashboard%2F123%3Ffrom%3Dparse"
    );
  });

  it("reads the current path from window.location", () => {
    window.history.replaceState({}, "", "/dashboard/123?from=parse");
    expect(getCurrentPath()).toBe("/dashboard/123?from=parse");
  });
});
