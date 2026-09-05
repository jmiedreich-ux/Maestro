import { render, screen, cleanup, within, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PerfBreakdownCard } from "./PerfBreakdownCard";
import { SPLIT } from "./perfBreakdown";

afterEach(cleanup);

// Every role/work label is unique on screen for a given basis (actor
// names never collide with work-kind names), but pct/abs VALUES do
// repeat across the two groups (e.g. cost's Reviewer role and Review
// work both show "$0.52"/"19%") — so every check below is scoped to
// the specific row found via its own unique label, not a bare,
// ambiguous `getByText` on the shared value.
function legendRow(label: string): HTMLElement {
  return screen.getByText(label).closest("div") as HTMLElement;
}

describe("PerfBreakdownCard", () => {
  it("defaults to the real 'cost' basis: header note, all 4 real role rows, all 4 real work rows, and the real caveat", () => {
    render(<PerfBreakdownCard />);
    expect(screen.getByText(`share of ${SPLIT.cost.note}`)).toBeInTheDocument();
    for (const part of [...SPLIT.cost.role, ...SPLIT.cost.work]) {
      const row = within(legendRow(part.label));
      expect(row.getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(row.getByText(part.abs)).toBeInTheDocument();
    }
    expect(screen.getByText(SPLIT.cost.caveat)).toBeInTheDocument();
  });

  it("substitutes the fictional 'Architect agent' persona with the real Local Qwen actor in cost.role, with no fictional persona anywhere", () => {
    render(<PerfBreakdownCard />);
    expect(screen.queryByText("Architect agent")).toBeNull();
    const localQwenRow = within(legendRow("Local Qwen"));
    expect(localQwenRow.getByText("0%")).toBeInTheDocument();
    expect(localQwenRow.getByText("local compute")).toBeInTheDocument();
  });

  it("clicking the Tokens button switches to the real 'tokens' basis: note, rows, and caveat all change; the prior cost caveat is gone", () => {
    render(<PerfBreakdownCard />);
    fireEvent.click(screen.getByRole("button", { name: "Tokens" }));

    expect(screen.getByText(`share of ${SPLIT.tokens.note}`)).toBeInTheDocument();
    expect(screen.queryByText(SPLIT.cost.caveat)).toBeNull();
    expect(screen.getByText(SPLIT.tokens.caveat)).toBeInTheDocument();
    for (const part of [...SPLIT.tokens.role, ...SPLIT.tokens.work]) {
      const row = within(legendRow(part.label));
      expect(row.getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(row.getByText(part.abs)).toBeInTheDocument();
    }
  });

  it("clicking the Time button switches to the real 'time' basis", () => {
    render(<PerfBreakdownCard />);
    fireEvent.click(screen.getByRole("button", { name: "Time" }));
    expect(screen.getByText(`share of ${SPLIT.time.note}`)).toBeInTheDocument();
    expect(screen.getByText(SPLIT.time.caveat)).toBeInTheDocument();
  });

  it("applies the selected-segment class only to the currently active basis button", () => {
    render(<PerfBreakdownCard />);
    const costButton = screen.getByRole("button", { name: "Cost" });
    const tokensButton = screen.getByRole("button", { name: "Tokens" });
    expect(costButton.className).toContain("segSelected");
    expect(tokensButton.className).not.toContain("segSelected");

    fireEvent.click(tokensButton);
    expect(costButton.className).not.toContain("segSelected");
    expect(tokensButton.className).toContain("segSelected");
  });

  it("renders a bar segment for a real 0%-share part with the reference file's own minimum-visible-sliver width (0.6%), never 0%", () => {
    render(<PerfBreakdownCard />);
    const zeroPart = SPLIT.cost.role.find((part) => part.pct === 0);
    expect(zeroPart).toBeDefined();
    // the bar segment has no visible text; find it via its real
    // `title` attribute (`label · pct% · abs`), transcribed verbatim
    // from the reference file's own `p.title` derivation.
    const segment = document.querySelector(
      `[title="${zeroPart!.label} · ${zeroPart!.pct}% · ${zeroPart!.abs}"]`,
    ) as HTMLElement;
    expect(segment).not.toBeNull();
    expect(segment.style.width).toBe("0.6%");
  });

  it("colors bar segments and legend dots with the real, checked B2 tokens, in the reference file's own real per-index order", () => {
    expect(colors.accent).toBe("#5B34E8");
    expect(colors.review).toBe("#D08A63");
    expect(colors.success).toBe("#2E9B72");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");

    render(<PerfBreakdownCard />);
    // cost.role's 4 real entries, in order: Implementor (index 0),
    // Reviewer (index 1), Coordinator (index 2), Local Qwen (index 3).
    const dotClass = (label: string) => (legendRow(label).firstElementChild as HTMLElement).className;
    expect(dotClass("Implementor")).toContain("segColor0");
    expect(dotClass("Reviewer")).toContain("segColor1");
    expect(dotClass("Coordinator")).toContain("segColor2");
    expect(dotClass("Local Qwen")).toContain("segColor3");
  });

  it("sets the card border/surface and segmented-track CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.segmentedTrack[1]).toBe("#F4F1F8");
    expect(colors.segmentedSelected).toBe("#FFFFFF");
    const { container } = render(<PerfBreakdownCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-brk-card-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-brk-track-bg")).toBe(colors.segmentedTrack[1]);
    expect(root.style.getPropertyValue("--atlas-brk-seg-selected-bg")).toBe(colors.segmentedSelected);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PerfBreakdownCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
