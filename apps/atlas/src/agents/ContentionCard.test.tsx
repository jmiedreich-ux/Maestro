import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { ContentionCard } from "./ContentionCard";
import { CONTENTION, CONTENTION_CAVEAT } from "./contention";

afterEach(cleanup);

describe("ContentionCard", () => {
  it("renders the real header label and 'no overlap' status", () => {
    render(<ContentionCard />);
    expect(screen.getByText("contention")).toBeInTheDocument();
    expect(screen.getByText("no overlap")).toBeInTheDocument();
  });

  it("renders all 3 real contention rows with their path, note, and holder", () => {
    render(<ContentionCard />);
    for (const entry of CONTENTION) {
      const path = screen.getByText(entry.path);
      const row = path.closest('[class*="row"]') as HTMLElement;
      expect(row).not.toBeNull();
      const rowScope = within(row);
      expect(rowScope.getByText(entry.note)).toBeInTheDocument();
      expect(rowScope.getByText(entry.holder)).toBeInTheDocument();
    }
  });

  it("renders the real trailing caveat", () => {
    render(<ContentionCard />);
    expect(screen.getByText(CONTENTION_CAVEAT)).toBeInTheDocument();
  });

  it("colors the 'Terra' holder badge with the real accent wash, and the 'frozen'/'reserved' badges with the real neutral chip, matching the reference file's real per-row mapping", () => {
    render(<ContentionCard />);
    const terra = screen.getByText("Terra");
    const frozen = screen.getByText("frozen");
    const reserved = screen.getByText("reserved");
    expect(terra.className).toContain("badgeRun");
    expect(frozen.className).toContain("badgeWait");
    expect(reserved.className).toContain("badgeWait");
  });

  it("sets the card border/surface and status CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.successText).toBe("#1F6B4E");
    expect(colors.accentWash[0]).toBe("#EBE4FF");
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<ContentionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-ct-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-ct-status")).toBe(colors.successText);
    expect(root.style.getPropertyValue("--atlas-ct-badge-run-bg")).toBe(colors.accentWash[0]);
    expect(root.style.getPropertyValue("--atlas-ct-badge-wait-bg")).toBe(colors.neutralChip);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ContentionCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
