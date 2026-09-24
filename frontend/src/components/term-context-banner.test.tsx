import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { TermContextBanner } from "@/components/term-context-banner";
import type { TermContext, TermOverride } from "@/types";

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

describe("TermContextBanner", () => {
  it("summarizes the term anchor and where it came from", () => {
    render(<TermContextBanner termContext={termContext} hasEdits={false} />);

    expect(
      screen.getByText(
        "Dates based on Fall 2026 · St. George · Week 1 starts Mon, Sep 7"
      )
    ).toBeInTheDocument();
    expect(
      screen.getByText("From the UofT academic calendar")
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Edit" })
    ).not.toBeInTheDocument();
  });

  it("applies only the fields the user changed", async () => {
    const user = userEvent.setup();
    const onApply = vi
      .fn<(override: TermOverride) => Promise<void>>()
      .mockResolvedValue();

    render(
      <TermContextBanner
        termContext={termContext}
        hasEdits={false}
        onApply={onApply}
      />
    );

    await user.click(screen.getByRole("button", { name: "Edit" }));

    const applyButton = screen.getByRole("button", { name: "Apply" });
    expect(applyButton).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Week 1 Monday"), {
      target: { value: "2026-09-14" },
    });
    await user.click(
      screen.getByLabelText("Syllabus counts reading week as a week")
    );
    await user.click(applyButton);

    expect(onApply).toHaveBeenCalledWith({
      week1Monday: "2026-09-14",
      readingWeekNumbered: true,
    });
    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: "Apply" })
      ).not.toBeInTheDocument();
    });
  });

  it("asks before replacing events the user already edited", async () => {
    const user = userEvent.setup();
    const onApply = vi
      .fn<(override: TermOverride) => Promise<void>>()
      .mockResolvedValue();

    render(
      <TermContextBanner termContext={termContext} hasEdits onApply={onApply} />
    );

    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.selectOptions(screen.getByLabelText("Term"), "winter");
    await user.click(screen.getByRole("button", { name: "Apply" }));

    expect(onApply).not.toHaveBeenCalled();
    expect(screen.getByText("Replace edited events?")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Replace" }));

    expect(onApply).toHaveBeenCalledWith({ season: "winter" });
  });

  it("shows the error when re-dating fails", async () => {
    const user = userEvent.setup();
    const onApply = vi
      .fn<(override: TermOverride) => Promise<void>>()
      .mockRejectedValue(new Error("Invalid extraction payload."));

    render(
      <TermContextBanner
        termContext={termContext}
        hasEdits={false}
        onApply={onApply}
      />
    );

    await user.click(screen.getByRole("button", { name: "Edit" }));
    await user.clear(screen.getByLabelText("Year"));
    await user.type(screen.getByLabelText("Year"), "2027");
    await user.click(screen.getByRole("button", { name: "Apply" }));

    expect(onApply).toHaveBeenCalledWith({ year: 2027 });
    expect(
      await screen.findByText("Invalid extraction payload.")
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Apply" })).toBeEnabled();
  });
});
