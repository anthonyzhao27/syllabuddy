import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { Header } from "@/components/header";

const mockUseAuth = vi.fn();
const mockPathname = vi.fn();
const mockReplace = vi.fn<(href: string) => void>();
const mockSignOut = vi.fn<() => Promise<{ error: null }>>();

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => mockPathname(),
  useRouter: () => ({
    replace: mockReplace,
  }),
}));

describe("Header", () => {
  beforeEach(() => {
    mockPathname.mockReturnValue("/dashboard");
    mockSignOut.mockResolvedValue({ error: null });
    mockUseAuth.mockReturnValue({
      user: {
        email: "student@example.com",
      },
      signOut: mockSignOut,
    });
  });

  it("renders authenticated navigation", () => {
    render(<Header />);

    expect(screen.getByRole("link", { name: /upload/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /my syllabi/i })
    ).toBeInTheDocument();
  });

  it("opens the account menu and signs out", async () => {
    const user = userEvent.setup();

    render(<Header />);

    await user.click(screen.getByRole("button", { name: /open account menu/i }));
    expect(screen.getAllByText("student@example.com")).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    expect(mockSignOut).toHaveBeenCalled();
    expect(mockReplace).toHaveBeenCalledWith("/login");
  });
});
