import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import DesktopShell from "./DesktopShell";

afterEach(cleanup);

describe("DesktopShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, not a hand-copied literal", () => {
    const { container } = render(<DesktopShell />);
    const root = container.firstChild as HTMLElement;
    // Corrected — non-blocking finding from Decision Fidelity review:
    // exhaustively checks every SHELL_VARS entry, including the two
    // disclosed non-token literals and the corrected idle-state values
    // — a prior draft spot-checked only 5 of 14 entries, which would not
    // have caught the wrong-value idle-grey defect review found by hand.
    expect(root.style.getPropertyValue("--atlas-surface")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-border-divider")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-nav-ground")).toBe(colors.navGround);
    expect(root.style.getPropertyValue("--atlas-nav-text-inactive")).toBe(colors.navTextInactive);
    expect(root.style.getPropertyValue("--atlas-nav-text-active")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-nav-active-bg")).toBe(colors.navActiveBg);
    expect(root.style.getPropertyValue("--atlas-nav-hover-bg")).toBe(colors.navHoverBg);
    expect(root.style.getPropertyValue("--atlas-nav-divider")).toBe("rgba(255,255,255,.08)");
    expect(root.style.getPropertyValue("--atlas-idle-grey")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-idle-label")).toBe(colors.inkFaint);
    expect(root.style.getPropertyValue("--atlas-page-bg-desktop")).toBe(colors.pageBgDesktop);
    expect(root.style.getPropertyValue("--atlas-font-mono")).toBe(fontFamily.mono);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
  });

  it("renders the top bar's idle live indicator", () => {
    render(<DesktopShell />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("renders exactly four static nav rows, in order", () => {
    render(<DesktopShell />);
    const rows = screen.getAllByRole("button");
    expect(rows.map((row) => row.textContent?.replace("—", "").trim())).toEqual([
      "Performance",
      "Agents",
      "History",
      "M1-B gate",
    ]);
  });

  it("defaults to Performance selected, with only one row marked current", () => {
    render(<DesktopShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Performance");
    expect(screen.getByText("Performance view")).toBeInTheDocument();
  });

  it("clicking a row makes it the sole selected row and updates the content pane", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /History/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
    expect(screen.getByText("History view")).toBeInTheDocument();
    expect(screen.queryByText("Performance view")).not.toBeInTheDocument();
  });

  it("never renders a literal 0 for the unavailable nav counts", () => {
    render(<DesktopShell />);
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(4);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<DesktopShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
