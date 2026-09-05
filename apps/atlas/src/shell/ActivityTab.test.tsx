import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";

afterEach(cleanup);

describe("ActivityTab", () => {
  it("renders the real page title and defaults to the History segment selected", () => {
    render(<ActivityTab />);
    expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
  });

  it("renders exactly three segments, in the reference file's own order", () => {
    render(<ActivityTab />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual(["History", "Agents", "Cost"]);
  });

  it("renders all 4 real HISTORY_STATS", () => {
    const { container } = render(<ActivityTab />);
    // Two real stats ("Corrections spent" and "Decisions recorded")
    // share the same real value ("1"), so each stat's label+value pair
    // is checked as one concatenated text run (each label is unique,
    // even though two values collide) rather than querying the value
    // alone document-wide.
    for (const stat of HISTORY_STATS) {
      const label = screen.getByText(stat.label);
      expect(label.textContent).toBe(`${stat.label}${stat.value}`);
    }
    expect(container.textContent).toContain(HISTORY_STATS[0].label);
  });

  it("renders all 10 real HISTORY_ENTRIES, in order, with their exact titles", () => {
    render(<ActivityTab />);
    const titles = screen.getAllByText(/./, { selector: "[class*='entryTitle']" });
    expect(titles.map((t) => t.textContent)).toEqual(HISTORY_ENTRIES.map((e) => e.title));
  });

  it("renders the real trailing empty-timeline note, reusing E6's own established constant", () => {
    render(<ActivityTab />);
    expect(screen.getByText(HISTORY_EMPTY_NOTE)).toBeInTheDocument();
  });

  it("renders no 'Open ... thread' button, unlike desktop History (the real mobile markup has no such control here)", () => {
    render(<ActivityTab />);
    expect(screen.queryByRole("button", { name: /open .* thread/i })).toBeNull();
  });

  it("tapping Agents or Cost switches the segmented control's own selection and shows a placeholder", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    let current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Agents");
    expect(screen.getByText("Agents segment")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cost" }));
    current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Cost");
    expect(screen.getByText("Cost segment")).toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ActivityTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
