import { vi } from "vitest";
import {
  ApiError,
  deleteEvent,
  downloadSyllabusFiles,
  getSyllabi,
  saveSyllabus,
  toApiEventUpdate,
} from "@/lib/api";
import type { SavedEvent } from "@/types";

const {
  mockGetAccessToken,
  mockSignOut,
  mockRedirectToLogin,
  mockGetCurrentPath,
} = vi.hoisted(() => ({
  mockGetAccessToken: vi.fn<() => Promise<string | null>>(),
  mockSignOut: vi.fn<() => Promise<{ error: null }>>(),
  mockRedirectToLogin: vi.fn<(next: string | null | undefined) => void>(),
  mockGetCurrentPath: vi.fn<() => string>(),
}));

vi.mock("@/lib/supabase", () => ({
  getAccessToken: mockGetAccessToken,
  supabase: {
    auth: {
      signOut: mockSignOut,
    },
  },
}));

vi.mock("@/lib/auth-redirect", () => ({
  getCurrentPath: mockGetCurrentPath,
  redirectToLogin: mockRedirectToLogin,
}));

const sampleEvent: SavedEvent = {
  id: "event-1",
  title: "Midterm",
  date: "2026-04-20",
  time: "13:30",
  course: "CSC209",
  type: "exam",
  description: "In-person",
  durationMinutes: 90,
  isEdited: false,
};

describe("api helpers", () => {
  beforeEach(() => {
    mockGetAccessToken.mockResolvedValue("supabase-token");
    mockSignOut.mockResolvedValue({ error: null });
    mockGetCurrentPath.mockReturnValue("/dashboard/event");
  });

  it("serializes event updates with omitted, cleared, and updated fields", () => {
    expect(
      toApiEventUpdate(
        {
          date: "2026-04-21",
          time: null,
          course: "",
          description: "",
        },
        sampleEvent
      )
    ).toEqual({
      due_date: "2026-04-21",
      time_specified: false,
      course: "",
      description: "",
    });

    expect(
      toApiEventUpdate(
        {
          time: "09:15",
          type: "quiz",
        },
        sampleEvent
      )
    ).toEqual({
      due_date: "2026-04-20T09:15:00",
      time_specified: true,
      event_type: "quiz",
    });
  });

  it("injects bearer auth headers into authenticated requests", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          syllabi: [],
        }),
        { status: 200 }
      )
    );

    vi.stubGlobal("fetch", fetchMock);

    await getSyllabi();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/files/",
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    );

    const headers = fetchMock.mock.calls[0][1]?.headers;
    expect(headers instanceof Headers ? headers.get("Authorization") : null).toBe(
      "Bearer supabase-token"
    );
  });

  it("signs out and redirects when the backend returns 401", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Unauthorized" }), {
          status: 401,
        })
      )
    );

    await expect(getSyllabi()).rejects.toBeInstanceOf(ApiError);
    expect(mockSignOut).toHaveBeenCalled();
    expect(mockRedirectToLogin).toHaveBeenCalledWith("/dashboard/event");
  });

  it("returns the persisted syllabus id after parse", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(
          JSON.stringify({
            syllabus_id: "syllabus-123",
          }),
          { status: 200 }
        )
      )
    );

    await expect(
      saveSyllabus([new File(["content"], "syllabus.pdf")], [])
    ).resolves.toEqual({
      syllabusId: "syllabus-123",
    });
  });

  it("downloads protected syllabus files through a blob fetch", async () => {
    const createObjectUrl = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:download");
    const revokeObjectUrl = vi.spyOn(URL, "revokeObjectURL").mockReturnValue();
    const click = vi.fn();
    const appendChild = vi.spyOn(document.body, "appendChild");
    const removeChild = vi.spyOn(document.body, "removeChild");
    const anchor = document.createElement("a");
    anchor.click = click;

    vi.spyOn(document, "createElement").mockReturnValue(anchor);
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(new Blob(["file"]), {
          status: 200,
          headers: {
            "content-disposition": 'attachment; filename="source.pdf"',
          },
        })
      )
    );

    await downloadSyllabusFiles("syllabus-123");

    expect(createObjectUrl).toHaveBeenCalled();
    expect(click).toHaveBeenCalled();
    expect(anchor.download).toBe("source.pdf");
    expect(appendChild).toHaveBeenCalledWith(anchor);
    expect(removeChild).toHaveBeenCalledWith(anchor);
    expect(revokeObjectUrl).toHaveBeenCalledWith("blob:download");
  });

  it("deletes events through the protected files endpoint", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(JSON.stringify({ message: "Event deleted" }), {
          status: 200,
        })
      )
    );

    await expect(deleteEvent("syllabus-1", "event-1")).resolves.toEqual({
      message: "Event deleted",
    });
  });
});

describe("api base url resolution", () => {
  const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;
  const originalNodeEnv = process.env.NODE_ENV;

  beforeEach(() => {
    mockGetAccessToken.mockResolvedValue("supabase-token");
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
    vi.stubEnv("NODE_ENV", originalNodeEnv);
    vi.resetModules();
  });

  it("uses the configured NEXT_PUBLIC_API_URL when set", async () => {
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_API_URL", "https://api.syllabuddy.app");
    vi.stubEnv("NODE_ENV", "production");

    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ syllabi: [] }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const { getSyllabi: getSyllabiFresh } = await import("@/lib/api");
    await getSyllabiFresh();

    expect(fetchMock).toHaveBeenCalledWith(
      "https://api.syllabuddy.app/files/",
      expect.anything()
    );
  });

  it("throws at module init in production when NEXT_PUBLIC_API_URL is missing", async () => {
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    vi.stubEnv("NODE_ENV", "production");

    await expect(import("@/lib/api")).rejects.toThrow(/NEXT_PUBLIC_API_URL/);
  });

  it("falls back to localhost outside production when NEXT_PUBLIC_API_URL is missing", async () => {
    vi.resetModules();
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    vi.stubEnv("NODE_ENV", "development");

    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ syllabi: [] }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const { getSyllabi: getSyllabiFresh } = await import("@/lib/api");
    await getSyllabiFresh();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/files/",
      expect.anything()
    );
  });
});
