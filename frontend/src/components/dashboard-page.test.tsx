import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { DashboardPage } from "@/components/dashboard-page";

const mockGetSyllabi = vi.fn();
const mockUseAuth = vi.fn();
const mockReplace = vi.fn<(href: string) => void>();
const mockUsePathname = vi.fn();
const mockUseSearchParams = vi.fn();

vi.mock("@/components/header", () => ({
  Header: () => <div>Header</div>,
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("@/lib/api", () => ({
  getSyllabi: (...args: Parameters<typeof mockGetSyllabi>) =>
    mockGetSyllabi(...args),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
  usePathname: () => mockUsePathname(),
  useSearchParams: () => mockUseSearchParams(),
}));

describe("DashboardPage", () => {
  beforeEach(() => {
    mockUsePathname.mockReturnValue("/dashboard");
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
  });

  it("waits for auth hydration before loading saved syllabi", () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
    });

    render(<DashboardPage />);

    expect(screen.getByText("Checking session...")).toBeInTheDocument();
    expect(mockGetSyllabi).not.toHaveBeenCalled();
  });

  it("renders saved syllabus rows from /files/", async () => {
    mockUseAuth.mockReturnValue({
      user: {
        id: "user-1",
        email: "student@example.com",
      },
      loading: false,
    });
    mockGetSyllabi.mockResolvedValue([
      {
        id: "syllabus-1",
        name: "CSC209 Winter 2026",
        courseCode: "CSC209",
        sourceType: "file",
        originalFilename: "syllabus.pdf",
        createdAt: "2026-04-01T12:00:00",
        eventCount: 4,
      },
    ]);

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("CSC209 Winter 2026")).toBeInTheDocument();
    });

    expect(mockGetSyllabi).toHaveBeenCalled();
    expect(screen.getByText("4 saved event(s)")).toBeInTheDocument();
  });
});
