import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { LoginPage } from "@/components/login-page";

const mockReplace = vi.fn<(href: string) => void>();
const mockUseAuth = vi.fn();
const mockSearchParams = vi.fn();

vi.mock("@/components/header", () => ({
  Header: () => <div>Header</div>,
}));

vi.mock("@/contexts/auth-context", () => ({
  useAuth: () => mockUseAuth(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: mockReplace,
  }),
  useSearchParams: () => mockSearchParams(),
}));

describe("LoginPage", () => {
  it("redirects authenticated users to the safe next path", async () => {
    mockSearchParams.mockReturnValue(new URLSearchParams("next=/dashboard"));
    mockUseAuth.mockReturnValue({
      loading: false,
      session: {
        access_token: "token",
      },
      signIn: vi.fn(),
      signUp: vi.fn(),
      signInWithGoogle: vi.fn(),
    });

    render(<LoginPage />);

    await waitFor(() => {
      expect(mockReplace).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows the check-email state when sign-up requires confirmation", async () => {
    const user = userEvent.setup();
    const signUp = vi.fn().mockResolvedValue({
      error: null,
      hasSession: false,
      requiresEmailConfirmation: true,
    });

    mockSearchParams.mockReturnValue(new URLSearchParams());
    mockUseAuth.mockReturnValue({
      loading: false,
      session: null,
      signIn: vi.fn(),
      signUp,
      signInWithGoogle: vi.fn(),
    });

    render(<LoginPage />);

    await user.click(screen.getByRole("button", { name: /sign up/i }));
    await user.type(screen.getByLabelText(/email/i), "student@example.com");
    await user.type(screen.getByLabelText(/password/i), "password123");

    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText(/check your email/i)).toBeInTheDocument();
  });
});
