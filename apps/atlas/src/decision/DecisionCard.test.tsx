import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { DecisionCard } from "./DecisionCard";
import { RULING_EXAMPLE } from "./fixtures";

afterEach(cleanup);

describe("DecisionCard (ruling variant)", () => {
  it("renders the real routing-table evidence in the chain-chip row, not the reference file's fictional persona chain", () => {
    render(<DecisionCard />);
    const { attemptId, route } = RULING_EXAMPLE;
    expect(screen.getByText(`${attemptId} · ${route.fromState}`)).toBeInTheDocument();
    expect(screen.getByText(`${route.reviewKind} · ${route.verdict}`)).toBeInTheDocument();
    expect(screen.getByText(route.toState)).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent/)).toBeNull();
    expect(screen.queryByText(/Terra/)).toBeNull();
  });

  it("cites the exact fired rule as text evidence — the roadmap's 'link to the rule that fired' requirement, satisfied as a precise citation rather than an unbuildable hyperlink", () => {
    render(<DecisionCard />);
    const { route } = RULING_EXAMPLE;
    expect(
      screen.getByText(
        (_, node) =>
          node?.textContent ===
          `rule: _REVIEW_ROUTES["${route.fromState}","${route.reviewKind}","${route.verdict}"] → "${route.toState}"`,
      ),
    ).toBeInTheDocument();
  });

  it("labels the eyebrow badge by the real mechanism, not a simulated ruling persona", () => {
    render(<DecisionCard />);
    expect(screen.getByText("resolved by routing policy")).toBeInTheDocument();
    expect(screen.queryByText(/architect agent ruling/i)).toBeNull();
  });

  it("shows a recorded timestamp, not an in-progress ruling duration", () => {
    render(<DecisionCard />);
    expect(screen.getByText(`recorded ${RULING_EXAMPLE.recordedAt}`)).toBeInTheDocument();
    expect(screen.queryByText(/ruling \d/)).toBeNull();
  });

  it("renders no option list and no footer action button — read-only, per this slice's scope", () => {
    render(<DecisionCard />);
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.queryByText(/Decide this myself/)).toBeNull();
    expect(screen.queryByText(/Allow a sentinel version/)).toBeNull();
  });

  it("sets the card border and background CSS variables to the reference file's real, disclosed literal values, not an existing but wrong token", () => {
    // Matches the established DesktopShell/MobileShell test pattern:
    // jsdom does not apply this project's CSS Modules stylesheet, so
    // these values are asserted on the CSS custom property itself
    // (set inline, on the root element, by SHELL_VARS), not on a
    // child element's resolved/computed style.
    expect(colors.borderStrong[1]).toBe("#DAD2EC");
    const { container } = render(<DecisionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-decision-border")).toBe("#DFD8EE");
    expect(root.style.getPropertyValue("--atlas-decision-border")).not.toBe(colors.borderStrong[1]);
    expect(root.style.getPropertyValue("--atlas-decision-bg")).toBe("#FBFAFE");
  });

  it("sets the dot and highlighted-chip CSS variables to colors.accent, not colors.accentHover", () => {
    expect(colors.accent).toBe("#5B34E8");
    expect(colors.accentHover).toBe("#4A28CC");
    const { container } = render(<DecisionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-decision-dot")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-decision-chip-on")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-decision-chip-on-ink")).toBe(colors.surface);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<DecisionCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
