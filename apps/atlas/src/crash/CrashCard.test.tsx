import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { CrashCard } from "./CrashCard";
import { CRASH_EXAMPLE } from "./fixtures";

afterEach(cleanup);

describe("CrashCard", () => {
  it("renders the eyebrow badge and age, and the adapted headline naming the real Failed/NeedsReplan mechanism", () => {
    render(<CrashCard />);
    expect(screen.getByText("agent stopped unexpectedly")).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.age)).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.headline)).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.lede)).toBeInTheDocument();
    expect(screen.queryByText(/still on disk/)).toBeNull();
  });

  it("renders all 4 real facts, including the corrected 'Outcome: Failed' fact in place of the reference file's unverifiable 'worktree preserved' claim", () => {
    render(<CrashCard />);
    for (const fact of CRASH_EXAMPLE.facts) {
      expect(screen.getByText(fact.k)).toBeInTheDocument();
      expect(screen.getByText(fact.v)).toBeInTheDocument();
    }
    expect(screen.queryByText(/preserved/)).toBeNull();
  });

  it("renders exactly the 3 real options, with the third's corrected body text that no longer claims locks stay held", () => {
    render(<CrashCard />);
    expect(screen.getAllByRole("button")).toHaveLength(3);
    for (const option of CRASH_EXAMPLE.options) {
      expect(screen.getByText(option.title)).toBeInTheDocument();
      expect(screen.getByText(option.cost)).toBeInTheDocument();
      expect(screen.getByText(option.body)).toBeInTheDocument();
    }
    expect(screen.queryByText(/[Ll]ocks stay held/)).toBeNull();
  });

  it("renders the corrected footer note, not the reference file's unverifiable 'Coordinator retried once' claim", () => {
    render(<CrashCard />);
    expect(screen.getByText(CRASH_EXAMPLE.footerNote)).toBeInTheDocument();
    expect(screen.queryByText(/retried once/)).toBeNull();
  });

  it("sets the card border, background, and ink CSS variables to the real colors.danger* tokens", () => {
    expect(colors.dangerBorder).toBe("#EFC9C4");
    expect(colors.dangerWash).toBe("#FEF7F6");
    expect(colors.dangerText).toBe("#A63F36");
    expect(colors.danger).toBe("#C4564A");
    const { container } = render(<CrashCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-crash-border")).toBe(colors.dangerBorder);
    expect(root.style.getPropertyValue("--atlas-crash-bg")).toBe(colors.dangerWash);
    expect(root.style.getPropertyValue("--atlas-crash-ink")).toBe(colors.dangerText);
    expect(root.style.getPropertyValue("--atlas-crash-dot")).toBe(colors.danger);
  });

  it("renders exactly 3 real <button> elements with no onClick side effect (clicking does nothing observable)", () => {
    render(<CrashCard />);
    const buttons = screen.getAllByRole("button");
    for (const button of buttons) {
      button.click();
    }
    // Still exactly 3 buttons, same text — nothing changed state.
    expect(screen.getAllByRole("button")).toHaveLength(3);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<CrashCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
