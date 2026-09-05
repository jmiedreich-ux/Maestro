import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { FidelityRecord } from "./FidelityRecord";
import { FIDELITY_RECORD_EXAMPLE } from "./fidelityFixtures";

afterEach(cleanup);

describe("FidelityRecord", () => {
  it("renders the real record id, subject, and evidence citation — not the reference file's fictional DF-2 sentinel-version narrative", () => {
    render(<FidelityRecord />);
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.id)).toBeInTheDocument();
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.subject)).toBeInTheDocument();
    expect(screen.getByText(`verified against ${FIDELITY_RECORD_EXAMPLE.against}`)).toBeInTheDocument();
    // Not a substring check for "Architect agent" — one of this record's
    // own real claims is honestly ABOUT the absence of that persona and
    // names it explicitly. What must be absent is the reference file's
    // fictional sentinel-version ruling narrative and record id.
    expect(screen.queryByText(/theme-free|theme-less|sentinel version/)).toBeNull();
    expect(screen.queryByText("DF-2")).toBeNull();
  });

  it("renders all 4 real claim rows with their evidence and verdicts", () => {
    render(<FidelityRecord />);
    for (const row of FIDELITY_RECORD_EXAMPLE.rows) {
      expect(screen.getByText(row.claim)).toBeInTheDocument();
      expect(screen.getByText(row.evidence)).toBeInTheDocument();
    }
    expect(screen.getAllByText("matches")).toHaveLength(3);
    expect(screen.getAllByText("n/a")).toHaveLength(1);
    expect(screen.queryByText("drifts")).toBeNull();
  });

  it("renders the overall verdict and binding note", () => {
    render(<FidelityRecord />);
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.verdict)).toBeInTheDocument();
    expect(screen.getByText(FIDELITY_RECORD_EXAMPLE.note)).toBeInTheDocument();
  });

  it("sets the card border, background, and eyebrow-ink CSS variables to the real, checked reference values", () => {
    expect(colors.borderStrong[1]).toBe("#DAD2EC");
    expect(colors.accentHover).toBe("#4A28CC");
    const { container } = render(<FidelityRecord />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-df-border")).toBe(colors.borderStrong[1]);
    expect(root.style.getPropertyValue("--atlas-df-bg")).toBe("#FBFAFE");
    expect(root.style.getPropertyValue("--atlas-df-ink")).toBe(colors.accentHover);
  });

  it("sets the matches/n/a verdict tag CSS variables to the real success/neutral tokens", () => {
    expect(colors.successWash).toBe("#E4F6EE");
    expect(colors.successText).toBe("#1F6B4E");
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<FidelityRecord />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-df-verdict-matches-bg")).toBe(colors.successWash);
    expect(root.style.getPropertyValue("--atlas-df-verdict-matches-color")).toBe(colors.successText);
    expect(root.style.getPropertyValue("--atlas-df-verdict-na-bg")).toBe(colors.neutralChip);
  });

  it("sets the overall-verdict bar CSS variables to the real accent-wash and accent-deepest tokens", () => {
    expect(colors.accentWash[4]).toBe("#F4F0FE");
    expect(colors.accentDeepest).toBe("#3F1FC0");
    const { container } = render(<FidelityRecord />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-df-bar-bg")).toBe(colors.accentWash[4]);
    expect(root.style.getPropertyValue("--atlas-df-verdict-text")).toBe(colors.accentDeepest);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<FidelityRecord />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
