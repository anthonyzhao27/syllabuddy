import { vi } from "vitest";
import {
  ApiError,
  deleteEvent,
  downloadSyllabusFiles,
  getSyllabi,
  parseSyllabus,
  resolveSavedSyllabusDates,
  resolveSyllabusDates,
  saveSyllabus,
  toApiEventUpdate,
  toSavedEvent,
  toTermContext,
} from "@/lib/api";
import type {
  ApiParseResponse,
  ApiSyllabusDetailResponse,
  ParsedEvent,
  SavedEvent,
} from "@/types";

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
  dateConfidence: null,
  dateSource: "",
};

const sampleParseResponse: ApiParseResponse = {
  events: [
    {
      title: "Problem Set 3",
      due_date: "2026-10-02T23:59:00",
      course: "STA304",
      event_type: "assignment",
      description: "",
      time_specified: false,
      duration_minutes: null,
      date_confidence: "inferred",
      date_source: "Week 4 Friday",
      source_key: "e2",
    },
  ],
  course_code: "STA304",
  term_context: {
    term_id: "2026-fall-stg",
    label: "Fall 2026 · St. George",
    season: "fall",
    year: 2026,
    campus: "St. George",
    division: "ArtSci",
    week1_monday: "2026-09-07",
    reading_week_numbered: false,
    classes_start: "2026-09-08",
    classes_end: "2026-12-07",
    reading_week: ["2026-10-26", "2026-10-30"],
    exam_period: null,
    anchor_source: "table",
    year_source: "stated",
  },
  extraction: { course_code: "STA304", events: [] },
};

const sampleDetailResponse: ApiSyllabusDetailResponse = {
  syllabus: {
    id: "syllabus-1",
    name: "STA304 Fall 2026",
    course_code: "STA304",
    source_type: "file",
    original_filename: "syllabus.pdf",
    created_at: "2026-09-01T12:00:00",
    event_count: 1,
    timezone: "America/Toronto",
    term_context: sampleParseResponse.term_context,
    can_redate: true,
  },
  events: [
    {
      id: "event-1",
      title: "Problem Set 3",
      due_date: "2026-10-09T23:59:00",
      course: "STA304",
      event_type: "assignment",
      description: "",
      time_specified: false,
      duration_minutes: null,
      is_edited: false,
      date_confidence: "inferred",
      date_source: "Week 5 Friday",
    },
  ],
};

function getSaveForm(fetchMock: ReturnType<typeof vi.fn<typeof fetch>>) {
  const body = fetchMock.mock.calls[0][1]?.body;

  if (!(body instanceof FormData)) {
    throw new Error("Expected a FormData body");
  }

  return body;
}

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

  it("maps date confidence and term context from the parse response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(JSON.stringify(sampleParseResponse), { status: 200 })
      )
    );

    const result = await parseSyllabus(new FormData());

    expect(result.events[0]).toEqual({
      title: "Problem Set 3",
      date: "2026-10-02",
      time: null,
      course: "STA304",
      type: "assignment",
      description: "",
      durationMinutes: null,
      dateConfidence: "inferred",
      dateSource: "Week 4 Friday",
      sourceKey: "e2",
    });
    expect(result.termContext).toEqual({
      termId: "2026-fall-stg",
      label: "Fall 2026 · St. George",
      season: "fall",
      year: 2026,
      campus: "St. George",
      division: "ArtSci",
      week1Monday: "2026-09-07",
      readingWeekNumbered: false,
      classesStart: "2026-09-08",
      classesEnd: "2026-12-07",
      readingWeek: ["2026-10-26", "2026-10-30"],
      examPeriod: null,
      anchorSource: "table",
      yearSource: "stated",
    });
    expect(result.extraction).toEqual(sampleParseResponse.extraction);
  });

  it("returns null term context when the parse response has none", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>().mockResolvedValue(
        new Response(
          JSON.stringify({
            events: [],
            course_code: null,
            term_context: null,
            extraction: null,
          }),
          { status: 200 }
        )
      )
    );

    await expect(parseSyllabus(new FormData())).resolves.toEqual({
      events: [],
      courseCode: null,
      termContext: null,
      extraction: null,
    });
  });

  it("posts the extraction and snake_cased override to /parse/resolve", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(sampleParseResponse), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const extraction = { course_code: "STA304", events: [] };
    const result = await resolveSyllabusDates(extraction, {
      week1Monday: "2026-09-14",
      readingWeekNumbered: true,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/parse/resolve",
      expect.objectContaining({ method: "POST" })
    );

    const init = fetchMock.mock.calls[0][1];
    expect(JSON.parse(String(init?.body))).toEqual({
      extraction,
      override: {
        week1_monday: "2026-09-14",
        reading_week_numbered: true,
      },
    });
    expect(
      init?.headers instanceof Headers
        ? init.headers.get("Content-Type")
        : null
    ).toBe("application/json");
    expect(result.termContext?.label).toBe("Fall 2026 · St. George");
    expect(result.events[0].dateConfidence).toBe("inferred");
  });

  it("sends date confidence fields to the save endpoint only when present", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ syllabus_id: "syllabus-123" }), {
        status: 200,
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const inferredEvent: ParsedEvent = {
      title: "Problem Set 3",
      date: "2026-10-02",
      time: null,
      course: "STA304",
      type: "assignment",
      description: "",
      durationMinutes: null,
      dateConfidence: "inferred",
      dateSource: "Week 4 Friday",
      sourceKey: "r0:3",
    };

    await saveSyllabus(
      [new File(["content"], "syllabus.pdf")],
      [
        inferredEvent,
        {
          ...inferredEvent,
          title: "Final Project",
          dateConfidence: null,
          dateSource: "",
          sourceKey: "",
        },
      ]
    );

    const form = getSaveForm(fetchMock);

    expect(JSON.parse(String(form.get("events_json")))).toEqual([
      {
        title: "Problem Set 3",
        due_date: "2026-10-02T23:59:00",
        course: "STA304",
        event_type: "assignment",
        description: "",
        time_specified: false,
        duration_minutes: null,
        date_confidence: "inferred",
        date_source: "Week 4 Friday",
        source_key: "r0:3",
      },
      {
        title: "Final Project",
        due_date: "2026-10-02T23:59:00",
        course: "STA304",
        event_type: "assignment",
        description: "",
        time_specified: false,
        duration_minutes: null,
      },
    ]);
  });

  it("sends the snake_cased term context and extraction on save", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ syllabus_id: "syllabus-123" }), {
        status: 200,
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const termContext = sampleParseResponse.term_context!;
    const extraction = { course_code: "STA304", events: [] };

    await saveSyllabus(
      [new File(["content"], "syllabus.pdf")],
      [],
      "STA304",
      "America/Toronto",
      { termContext: toTermContext(termContext), extraction }
    );

    const form = getSaveForm(fetchMock);

    expect(JSON.parse(String(form.get("term_context_json")))).toEqual(
      termContext
    );
    expect(JSON.parse(String(form.get("extraction_json")))).toEqual(extraction);
  });

  it("omits term context and extraction from the save when absent", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify({ syllabus_id: "syllabus-123" }), {
        status: 200,
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await saveSyllabus([new File(["content"], "syllabus.pdf")], [], "STA304", "UTC", {
      termContext: null,
      extraction: null,
    });

    const form = getSaveForm(fetchMock);

    expect(form.has("term_context_json")).toBe(false);
    expect(form.has("extraction_json")).toBe(false);
  });

  it("maps date confidence on saved events", () => {
    expect(toSavedEvent(sampleDetailResponse.events[0])).toEqual({
      id: "event-1",
      title: "Problem Set 3",
      date: "2026-10-09",
      time: null,
      course: "STA304",
      type: "assignment",
      description: "",
      durationMinutes: null,
      isEdited: false,
      dateConfidence: "inferred",
      dateSource: "Week 5 Friday",
    });

    expect(
      toSavedEvent({
        ...sampleDetailResponse.events[0],
        date_confidence: null,
        date_source: "",
      })
    ).toMatchObject({ dateConfidence: null, dateSource: "" });
  });

  it("posts the snake_cased override to /files/{id}/resolve", async () => {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(sampleDetailResponse), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await resolveSavedSyllabusDates("syllabus-1", {
      season: "winter",
      year: 2027,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/files/syllabus-1/resolve",
      expect.objectContaining({ method: "POST" })
    );

    const init = fetchMock.mock.calls[0][1];
    expect(JSON.parse(String(init?.body))).toEqual({
      override: {
        season: "winter",
        year: 2027,
      },
    });
    expect(
      init?.headers instanceof Headers
        ? init.headers.get("Content-Type")
        : null
    ).toBe("application/json");
    expect(result.syllabus.termContext?.label).toBe("Fall 2026 · St. George");
    expect(result.syllabus.canRedate).toBe(true);
    expect(result.events[0].dateConfidence).toBe("inferred");
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
