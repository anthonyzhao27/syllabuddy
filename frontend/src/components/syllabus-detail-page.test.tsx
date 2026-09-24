import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ApiError } from "@/lib/api";
import { SyllabusDetailPage } from "@/components/syllabus-detail-page";
import type { SyllabusDetail, TermContext } from "@/types";

const mockGetSyllabusDetail = vi.fn();
const mockUpdateEvent = vi.fn();
const mockDeleteEvent = vi.fn();
const mockDeleteSyllabus = vi.fn();
const mockDownloadSyllabusFiles = vi.fn();
const mockResolveSavedSyllabusDates = vi.fn();
const mockUseParams = vi.fn();
const mockUseSearchParams = vi.fn();
const mockReplace = vi.fn<(href: string) => void>();

vi.mock("@/components/header", () => ({
  Header: () => <div>Header</div>,
}));

vi.mock("@/components/require-auth", () => ({
  RequireAuth: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("@/components/export-buttons", () => ({
  ExportButtons: ({ events }: { events: Array<{ id: string }> }) => (
    <div>ExportButtons {events.length}</div>
  ),
}));

vi.mock("@/lib/api", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api")>("@/lib/api");

  return {
    ...actual,
    getSyllabusDetail: (...args: Parameters<typeof mockGetSyllabusDetail>) =>
      mockGetSyllabusDetail(...args),
    updateEvent: (...args: Parameters<typeof mockUpdateEvent>) =>
      mockUpdateEvent(...args),
    deleteEvent: (...args: Parameters<typeof mockDeleteEvent>) =>
      mockDeleteEvent(...args),
    deleteSyllabus: (...args: Parameters<typeof mockDeleteSyllabus>) =>
      mockDeleteSyllabus(...args),
    downloadSyllabusFiles: (
      ...args: Parameters<typeof mockDownloadSyllabusFiles>
    ) => mockDownloadSyllabusFiles(...args),
    resolveSavedSyllabusDates: (
      ...args: Parameters<typeof mockResolveSavedSyllabusDates>
    ) => mockResolveSavedSyllabusDates(...args),
  };
});

vi.mock("next/navigation", () => ({
  useParams: () => mockUseParams(),
  useSearchParams: () => mockUseSearchParams(),
  useRouter: () => ({
    replace: mockReplace,
  }),
}));

const detailResponse = {
  syllabus: {
    id: "syllabus-1",
    name: "CSC209 Winter 2026",
    courseCode: "CSC209",
    sourceType: "file" as const,
    originalFilename: "syllabus.pdf",
    createdAt: "2026-04-01T12:00:00",
    eventCount: 1,
  },
  events: [
    {
      id: "event-1",
      title: "Midterm",
      date: "2026-04-20",
      time: "13:30",
      course: "CSC209",
      type: "exam" as const,
      description: "In-person",
      durationMinutes: 90,
      isEdited: false,
    },
  ],
};

const termContext: TermContext = {
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
};

const datedDetailResponse: SyllabusDetail = {
  syllabus: {
    ...detailResponse.syllabus,
    timezone: "America/Toronto",
    termContext,
    canRedate: true,
  },
  events: [
    {
      ...detailResponse.events[0],
      title: "Problem Set 3",
      date: "2026-10-02",
      time: null,
      type: "assignment",
      durationMinutes: null,
      dateConfidence: "inferred",
      dateSource: "Week 4 Friday",
    },
    {
      ...detailResponse.events[0],
      id: "event-2",
      dateConfidence: "exact",
      dateSource: "Oct 20",
    },
  ],
};

describe("SyllabusDetailPage", () => {
  beforeEach(() => {
    mockUseParams.mockReturnValue({
      id: "syllabus-1",
    });
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    mockGetSyllabusDetail.mockResolvedValue(detailResponse);
    mockUpdateEvent.mockResolvedValue({
      ...detailResponse.events[0],
      title: "Updated midterm",
      isEdited: true,
    });
    mockDeleteEvent.mockResolvedValue({
      message: "Event deleted",
    });
    mockDeleteSyllabus.mockResolvedValue({
      message: "Syllabus deleted",
    });
    mockDownloadSyllabusFiles.mockResolvedValue(undefined);
    mockResolveSavedSyllabusDates.mockReset();
  });

  it("hydrates from /files/{id} on direct visit", async () => {
    render(<SyllabusDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("CSC209 Winter 2026")).toBeInTheDocument();
    });

    expect(mockGetSyllabusDetail).toHaveBeenCalledWith("syllabus-1");
    expect(screen.getByText("Midterm")).toBeInTheDocument();
  });

  it("shows the saved-success state after parse redirects", async () => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams("from=parse"));

    render(<SyllabusDetailPage />);

    expect(await screen.findByText(/saved successfully/i)).toBeInTheDocument();
    expect(screen.getByText("ExportButtons 1")).toBeInTheDocument();
  });

  it("handles missing syllabi with a not-found state", async () => {
    mockGetSyllabusDetail.mockRejectedValue(
      new ApiError("Syllabus not found", 404)
    );

    render(<SyllabusDetailPage />);

    expect(
      await screen.findByText(/this syllabus is no longer available/i)
    ).toBeInTheDocument();
  });

  it("persists event edits and deletes from the canonical detail page", async () => {
    const user = userEvent.setup();

    render(<SyllabusDetailPage />);

    expect(await screen.findByText("Midterm")).toBeInTheDocument();

    await user.click(screen.getByTitle("Edit"));
    await user.clear(screen.getByDisplayValue("Midterm"));
    await user.type(screen.getByDisplayValue(""), "Updated midterm");
    const saveButtons = screen.getAllByRole("button", { name: /^save$/i });
    await user.click(saveButtons[saveButtons.length - 1]);

    await waitFor(() => {
      expect(mockUpdateEvent).toHaveBeenCalled();
    });

    expect(await screen.findByText("Updated midterm")).toBeInTheDocument();

    await user.click(screen.getByTitle("Delete"));

    // ConfirmDialog is a custom modal — click the confirm Delete button inside it.
    // The dialog button has the text "Delete" and is in the portal (last in DOM).
    await waitFor(() => {
      const deleteButtons = screen.getAllByRole("button", { name: /^delete$/i });
      // The dialog's confirm button is the last one rendered (in the body portal)
      void user.click(deleteButtons[deleteButtons.length - 1]);
    });

    await waitFor(() => {
      expect(mockDeleteEvent).toHaveBeenCalledWith("syllabus-1", "event-1");
    });
  });

  it("shows the term banner and date confidence badges for saved events", async () => {
    mockGetSyllabusDetail.mockResolvedValue({
      ...datedDetailResponse,
      syllabus: { ...datedDetailResponse.syllabus, canRedate: false },
    });

    render(<SyllabusDetailPage />);

    expect(
      await screen.findByText(
        "Dates based on Fall 2026 · St. George · Week 1 starts Mon, Sep 7"
      )
    ).toBeInTheDocument();
    expect(screen.getByText("from week #")).toHaveAttribute(
      "title",
      "Week 4 Friday"
    );
    // Exact dates get no badge.
    expect(screen.queryByText("estimated")).not.toBeInTheDocument();
    expect(screen.getAllByText(/from week #|estimated/)).toHaveLength(1);
    // Without a stored extraction the anchor can't be changed.
    // Only the banner's Edit toggle carries aria-expanded.
    expect(
      screen.queryByRole("button", { name: "Edit", expanded: false })
    ).not.toBeInTheDocument();
  });

  it("re-dates a saved syllabus after confirming", async () => {
    const user = userEvent.setup();
    mockGetSyllabusDetail.mockResolvedValue(datedDetailResponse);
    mockResolveSavedSyllabusDates.mockResolvedValue({
      syllabus: {
        ...datedDetailResponse.syllabus,
        termContext: { ...termContext, label: "Fall 2027 · St. George", year: 2027 },
      },
      events: [
        {
          ...datedDetailResponse.events[0],
          id: "event-3",
          title: "Problem Set 3 (re-dated)",
          date: "2027-10-01",
        },
      ],
    });

    render(<SyllabusDetailPage />);

    await user.click(await screen.findByRole("button", { name: "Edit", expanded: false }));
    await user.clear(screen.getByLabelText("Year"));
    await user.type(screen.getByLabelText("Year"), "2027");
    await user.click(screen.getByRole("button", { name: "Apply" }));

    expect(mockResolveSavedSyllabusDates).not.toHaveBeenCalled();
    expect(screen.getByText("Recalculate event dates?")).toBeInTheDocument();
    expect(
      screen.getByText(/events you edited are kept as they are/i)
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Recalculate" }));

    expect(mockResolveSavedSyllabusDates).toHaveBeenCalledWith("syllabus-1", {
      year: 2027,
    });
    expect(
      await screen.findByText("Problem Set 3 (re-dated)")
    ).toBeInTheDocument();
    expect(screen.queryByText("Midterm")).not.toBeInTheDocument();
    expect(screen.getByText(/Dates based on Fall 2027/)).toBeInTheDocument();
  });
});
