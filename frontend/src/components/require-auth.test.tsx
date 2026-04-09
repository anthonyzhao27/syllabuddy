import { render, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { RequireAuth } from "@/components/require-auth";

const mockReplace = vi.fn<(href: string) => void>();
const mockUseAuth = vi.fn();
const mockUsePathname = vi.fn();
const mockUseSearchParams = vi.fn();

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
  usePathname: () => mockUsePathname(),
  useSearchParams: () => mockUseSearchParams(),
}));

describe("RequireAuth", () => {
  it("preserves query params when redirecting unauthenticated users", async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
    });
    mockUsePathname.mockReturnValue("/dashboard/123");
    mockUseSearchParams.mockReturnValue(
      new URLSearchParams("from=parse&tab=events")
    );

    render(
      <RequireAuth>
        <div>Protected</div>
      </RequireAuth>
    );

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith(
        "/login?next=%2Fdashboard%2F123%3Ffrom%3Dparse%26tab%3Devents"
      );
    });
  });

  it("renders children when authenticated", () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: "user-1",
      },
      loading: false,
    });
    mockUsePathname.mockReturnValue("/");
    mockUseSearchParams.mockReturnValue(new URLSearchParams());

    const { getByText } = render(
      <RequireAuth>
        <div>Protected</div>
      </RequireAuth>
    );

    expect(getByText("Protected")).toBeInTheDocument();
  });
});
