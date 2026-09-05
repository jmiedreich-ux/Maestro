import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { GateCriteriaList } from "./GateCriteriaList";
import { GATE_CRITERIA, GATE_FOOTER_NOTE, GATE_MET_LABEL } from "./fixtures";

afterEach(cleanup);

describe("GateCriteriaList", () => {
  it("renders the header label and the real met-count summary", () => {
    render(<GateCriteriaList />);
    expect(screen.getByText("entry criteria")).toBeInTheDocument();
    expect(screen.getByText(GATE_MET_LABEL)).toBeInTheDocument();
  });

  it("renders all 5 real criteria with their title, detail, and evidence", () => {
    render(<GateCriteriaList />);
    for (const criterion of GATE_CRITERIA) {
      expect(screen.getByText(criterion.title)).toBeInTheDocument();
      expect(screen.getByText(criterion.detail)).toBeInTheDocument();
      expect(screen.getByText(criterion.evidence)).toBeInTheDocument();
    }
  });

  it("renders the card's own real footer note", () => {
    render(<GateCriteriaList />);
    expect(screen.getByText(GATE_FOOTER_NOTE)).toBeInTheDocument();
  });

  it("matches the real met-count breakdown: 2 yes, 1 part, 2 no", () => {
    const counts = { yes: 0, part: 0, no: 0 };
    for (const criterion of GATE_CRITERIA) {
      counts[criterion.met] += 1;
    }
    expect(counts).toEqual({ yes: 2, part: 1, no: 2 });
  });

  it("dims the title only for unmet ('no') criteria; met and partial criteria use the default ink title color", () => {
    render(<GateCriteriaList />);
    const unmet = screen.getByText("A.0 through A.7 accepted");
    const met = screen.getByText("Frozen-presentation contract holds");
    const partial = screen.getByText("Every owner decision carries a fidelity check");
    expect(unmet.className).toContain("titleUnmet");
    expect(met.className).toContain("titleDefault");
    expect(partial.className).toContain("titleDefault");
  });

  it("colors evidence text by met status: yes -> successText, part -> warningText, no -> inkFaint", () => {
    render(<GateCriteriaList />);
    const yesEvidence = screen.getByText("A.1 · 9d3e1a2");
    const partEvidence = screen.getByText("DF-2 pending");
    const noEvidence = screen.getByText("2 of 8 accepted");
    expect(yesEvidence.className).toContain("evidenceYes");
    expect(partEvidence.className).toContain("evidencePart");
    expect(noEvidence.className).toContain("evidenceNo");
  });

  it("sets the border, success-mark, and warning-mark CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.success).toBe("#2E9B72");
    expect(colors.warning).toBe("#E0A32E");
    const { container } = render(<GateCriteriaList />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-gate-mark-yes")).toBe(colors.success);
    expect(root.style.getPropertyValue("--atlas-gate-mark-part")).toBe(colors.warning);
  });

  it("disclosed literal's identity: colors.navText really does equal the mark-no-border literal, and colors.border (a different token) is really different from it", () => {
    // Guards against the exact class of defect the -01 candidate's
    // correction introduced: assert the two token facts this
    // component's own disclosure depends on, not just eyeball them.
    expect(colors.navText).toBe("#CFC6D6");
    expect(colors.border).not.toBe(colors.navText);
    const { container } = render(<GateCriteriaList />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-mark-no-border")).toBe(colors.navText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<GateCriteriaList />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
