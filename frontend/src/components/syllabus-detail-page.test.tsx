import { render, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { ApiError } from "@/lib/api";
import { SyllabusDetailPage } from "@/components/syllabus-detail-page";

const mockGetSyllabusDetail = vi.fn();
const mockUpdateEvent = vi.fn();
const mockDeleteEvent = vi.fn();
const mockDeleteSyllabus = vi.fn();
const mockDownloadSyllabusFiles = vi.fn();
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
    const confirmMock = vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<SyllabusDetailPage />);

    expect(await screen.findByText("Midterm")).toBeInTheDocument();

    await user.click(screen.getByTitle("Edit"));
    await user.clear(screen.getByDisplayValue("Midterm"));
    await user.type(screen.getByDisplayValue(""), "Updated midterm");
    await user.click(screen.getByRole("button", { name: /^save$/i }));

    await waitFor(() => {
      expect(mockUpdateEvent).toHaveBeenCalled();
    });

    expect(await screen.findByText("Updated midterm")).toBeInTheDocument();

    await user.click(screen.getByTitle("Delete"));

    await waitFor(() => {
      expect(confirmMock).toHaveBeenCalled();
      expect(mockDeleteEvent).toHaveBeenCalledWith("syllabus-1", "event-1");
    });
  });
});
