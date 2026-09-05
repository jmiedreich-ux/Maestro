import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PerformanceHeader } from "./PerformanceHeader";
import { PERFORMANCE_STATS } from "./fixtures";

afterEach(cleanup);

describe("PerformanceHeader", () => {
  it("renders the real eyebrow and title", () => {
    render(<PerformanceHeader />);
    expect(screen.getByText("m1-a · performance")).toBeInTheDocument();
    expect(screen.getByText("What each action actually cost")).toBeInTheDocument();
  });

  it("renders the lede with 'unavailable' in its own <code> element, matching the reference file's inline mono styling", () => {
    render(<PerformanceHeader />);
    const code = screen.getByText("unavailable");
    expect(code.tagName).toBe("CODE");
    expect(screen.getByText(/One record per worker attempt/)).toBeInTheDocument();
    expect(screen.getByText(/never folded into the hosted allowance/)).toBeInTheDocument();
  });

  it("renders all 4 real stats with their real labels and values", () => {
    render(<PerformanceHeader />);
    for (const stat of PERFORMANCE_STATS) {
      expect(screen.getByText(stat.label)).toBeInTheDocument();
      expect(screen.getByText(stat.value)).toBeInTheDocument();
    }
  });

  it("colors the 'Estimated' stat's value amber (warningText) and every other stat's value ink, matching the reference file's real per-stat color", () => {
    render(<PerformanceHeader />);
    const estimated = screen.getByText("$0.52");
    const billed = screen.getByText("$2.27");
    expect(estimated.className).toContain("statValueWarning");
    expect(billed.className).toContain("statValueInk");
  });

  it("sets the surface, border, and warning CSS variables to the real, checked tokens", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    expect(colors.warningText).toBe("#8A5A08");
    const { container } = render(<PerformanceHeader />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-perf-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-perf-warning")).toBe(colors.warningText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PerformanceHeader />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
