import { vi } from "vitest";

const mockGetSession = vi.fn();

vi.mock("@supabase/supabase-js", () => ({
  createClient: () => ({
    auth: {
      getSession: mockGetSession,
    },
  }),
}));

describe("supabase helpers", () => {
  it("returns the current session", async () => {
    mockGetSession.mockResolvedValueOnce({
      data: {
        session: {
          access_token: "token",
          user: {
            id: "user-1",
          },
        },
      },
    });

    const { getSession } = await import("@/lib/supabase");

    await expect(getSession()).resolves.toEqual({
      access_token: "token",
      user: {
        id: "user-1",
      },
    });
  });

  it("returns the current access token", async () => {
    mockGetSession.mockResolvedValueOnce({
      data: {
        session: {
          access_token: "token-2",
          user: {
            id: "user-2",
          },
        },
      },
    });

    const { getAccessToken } = await import("@/lib/supabase");

    await expect(getAccessToken()).resolves.toBe("token-2");
  });
});
