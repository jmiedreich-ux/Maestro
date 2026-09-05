import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { WeeklyWindowStrip } from "./WeeklyWindowStrip";
import { WEEKLY_WINDOW } from "./weeklyWindow";

afterEach(cleanup);

describe("WeeklyWindowStrip", () => {
  it("renders the real label and all 4 real reconciliation figures", () => {
    render(<WeeklyWindowStrip />);
    expect(screen.getByText("openai weekly window")).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.reconciledPercent)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.coarsePercent)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.unattributedPercent)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.observedChangePercent)).toBeInTheDocument();
  });

  it("renders the real meta text and caption", () => {
    render(<WeeklyWindowStrip />);
    expect(screen.getByText(WEEKLY_WINDOW.meta)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.caption)).toBeInTheDocument();
  });

  it("colors only the unattributed figure amber (warningText); every other figure is ink", () => {
    render(<WeeklyWindowStrip />);
    const unattributed = screen.getByText(WEEKLY_WINDOW.unattributedPercent);
    const reconciled = screen.getByText(WEEKLY_WINDOW.reconciledPercent);
    expect(unattributed.className).toContain("figureWarning");
    expect(reconciled.className).toContain("figureInk");
  });

  it("sets the border, surface, and warning CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.warningText).toBe("#8A5A08");
    const { container } = render(<WeeklyWindowStrip />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-week-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-week-warning")).toBe(colors.warningText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<WeeklyWindowStrip />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
