import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { History } from "./History";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "./fixtures";
import { HISTORY_KIND_STYLE } from "./historyStyle";

afterEach(cleanup);

describe("History", () => {
  it("renders the real eyebrow, title, and all 4 real stats", () => {
    render(<History />);
    expect(screen.getByText("m1-a · history")).toBeInTheDocument();
    expect(screen.getByText("Everything that happened, in order")).toBeInTheDocument();
    // Two real stats ("Corrections spent" and "Decisions recorded")
    // share the identical real value "1", so each value is checked
    // scoped to its own label's container, not with a bare, ambiguous
    // getByText.
    for (const stat of HISTORY_STATS) {
      const label = screen.getByText(stat.label);
      const statScope = within(label.closest("span[class*='stat']") as HTMLElement);
      expect(statScope.getByText(stat.value)).toBeInTheDocument();
    }
  });

  it("renders all 10 real entries with their title, packet, kind tag, and who/detail line", () => {
    render(<History />);
    for (const entry of HISTORY_ENTRIES) {
      const title = screen.getByText(entry.title);
      const row = title.closest("div[class*='row']") as HTMLElement;
      expect(row).not.toBeNull();
      const rowScope = within(row);
      expect(rowScope.getByText(entry.time)).toBeInTheDocument();
      expect(rowScope.getByText(entry.kind)).toBeInTheDocument();
      expect(rowScope.getByText(`${entry.who} — ${entry.detail}`)).toBeInTheDocument();
    }
  });

  it("renders exactly 2 real, inert 'Open ... thread' buttons, for the 2 entries with a real ref", () => {
    render(<History />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(2);
    expect(screen.getByText("Open A.1 thread")).toBeInTheDocument();
    expect(screen.getByText("Open A.2 thread")).toBeInTheDocument();
  });

  it("renders the timeline's own real trailing placeholder note", () => {
    render(<History />);
    expect(screen.getByText(HISTORY_EMPTY_NOTE)).toBeInTheDocument();
  });

  it("marks blocked/escalated entries as urgent (filled dot, warning color) and every other kind as non-urgent", () => {
    expect(HISTORY_KIND_STYLE.blocked.urgent).toBe(true);
    expect(HISTORY_KIND_STYLE.escalated.urgent).toBe(true);
    expect(HISTORY_KIND_STYLE.dispatch.urgent).toBe(false);
    expect(HISTORY_KIND_STYLE.accepted.urgent).toBe(false);
    expect(HISTORY_KIND_STYLE.blocked.dotColor).toBe(colors.warning);
  });

  it("gives review and correction kinds the identical real review-colored tag, matching the reference file's shared style entry", () => {
    expect(HISTORY_KIND_STYLE.review).toEqual(HISTORY_KIND_STYLE.correction);
    expect(HISTORY_KIND_STYLE.review.tagColor).toBe(colors.reviewText);
  });

  it("discloses the report kind's dot color as a literal distinct from colors.navText's real, unrelated usage context", () => {
    expect(colors.navText).toBe("#CFC6D6");
    expect(HISTORY_KIND_STYLE.report.dotColor).toBe("#CFC6D6");
  });

  it("sets the header border and rail CSS variables to the real, checked values", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    const { container } = render(<History />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-hist-header-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-hist-rail")).toBe("#EDE8F2");
    expect(root.style.getPropertyValue("--atlas-hist-rail")).not.toBe(colors.borderDivider[0]);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<History />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
