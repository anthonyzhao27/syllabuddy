import { vi } from "vitest";
import {
  ApiError,
  deleteEvent,
  downloadSyllabusFiles,
  exportToGoogleCalendar,
  getSyllabi,
  parseSyllabus,
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
            events: [],
          }),
          { status: 200 }
        )
      )
    );

    const formData = new FormData();
    formData.append("files", new File(["content"], "syllabus.pdf"));

    await expect(parseSyllabus(formData)).resolves.toEqual({
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

  it("keeps Google export using the GIS token plus the app bearer token", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(
        JSON.stringify({
          created_count: 1,
          created: [
            {
              title: "Midterm",
              id: "calendar-event",
              link: "https://calendar.google.com/event",
            },
          ],
          errors: [],
          calendar_name: "CSC209",
        }),
        { status: 200 }
      )
    );

    vi.stubGlobal("fetch", fetchMock);

    await exportToGoogleCalendar([sampleEvent], "google-token", "America/Toronto");

    expect(fetchMock.mock.calls[0][1]?.body).toBe(
      JSON.stringify({
        events: [
          {
            title: "Midterm",
            due_date: "2026-04-20T13:30:00",
            course: "CSC209",
            event_type: "exam",
            description: "In-person",
            time_specified: true,
            duration_minutes: 90,
          },
        ],
        access_token: "google-token",
        timezone: "America/Toronto",
      })
    );
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
