import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { AGENT_STYLE } from "../agents/agentStyle";
import { GateHeader } from "./GateHeader";
import { GATE_CRITERIA } from "./fixtures";

afterEach(cleanup);

describe("GateHeader", () => {
  it("renders the real breadcrumb and title", () => {
    render(<GateHeader />);
    expect(screen.getByText("m1-b")).toBeInTheDocument();
    expect(screen.getByText("milestone gate")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
  });

  it("derives the state line and button note directly from the real GATE_CRITERIA counts, not a second hardcoded literal", () => {
    const counts = { yes: 0, part: 0, no: 0 };
    for (const criterion of GATE_CRITERIA) {
      counts[criterion.met] += 1;
    }
    expect(counts).toEqual({ yes: 2, part: 1, no: 2 });

    render(<GateHeader />);
    expect(
      screen.getByText(`Closed · ${counts.yes} of ${GATE_CRITERIA.length} criteria met, ${counts.part} partly`),
    ).toBeInTheDocument();
    expect(screen.getByText(`Blocked by ${counts.no} open criteria`)).toBeInTheDocument();
  });

  it("renders a genuinely disabled 'Open gate' button", () => {
    render(<GateHeader />);
    const button = screen.getByRole("button", { name: "Open gate" });
    expect(button).toBeDisabled();
  });

  it("renders the real, corrected lede naming the Coordinator, not the fictional 'Architect agent'", () => {
    render(<GateHeader />);
    expect(
      screen.getByText(
        "A gate is not a status. Every criterion has to be true before M1-B packets can be dispatched, and the Coordinator verifies them against records — not against anyone's summary.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Architect agent/)).toBeNull();
  });

  it("renders the real approver panel naming the Coordinator, with the real Coordinator avatar identity from E4's own AGENT_STYLE", () => {
    const { container } = render(<GateHeader />);
    expect(screen.getByText("approver")).toBeInTheDocument();
    expect(screen.getByText("Coordinator")).toBeInTheDocument();
    expect(screen.getByText("rules on the gate · records fidelity")).toBeInTheDocument();
    expect(screen.getByText("CO")).toBeInTheDocument();

    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-approver-avatar-bg")).toBe(AGENT_STYLE.rule.avBg);
    expect(root.style.getPropertyValue("--atlas-gate-approver-avatar-ink")).toBe(AGENT_STYLE.rule.avColor);
  });

  it("renders the real, corrected approver note disclosing no automated gate-opening exists yet", () => {
    render(<GateHeader />);
    expect(
      screen.getByText(
        "No automated gate-opening exists in Maestro today — opening the gate remains a manual, owner-reviewed action. This becomes an automatic Coordinator decision once M4's own autonomous Architect loop exists.",
      ),
    ).toBeInTheDocument();
    // The reference file's own fictional-automation claim must not survive.
    expect(screen.queryByText(/opens the gate on its own/)).toBeNull();
    expect(screen.queryByText(/no human step/)).toBeNull();
  });

  it("renders the real 'what opening releases' panel with all 3 real items", () => {
    render(<GateHeader />);
    expect(screen.getByText("what opening releases")).toBeInTheDocument();
    expect(screen.getByText("B.0 through B.4 become dispatchable")).toBeInTheDocument();
    expect(screen.getByText("Overlay files unlock for write")).toBeInTheDocument();
    expect(screen.getByText("M1-A packets become read-only records")).toBeInTheDocument();
  });

  it("sets the real, checked B2 tokens and the two disclosed literals", () => {
    expect(colors.inkFaint).toBe("#A79BB4");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");
    expect(colors.inkMuted).toBe("#8E8299");
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.inkSecondary).toBe("#6C6376");

    const { container } = render(<GateHeader />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-breadcrumb")).toBe(colors.inkFaint);
    expect(root.style.getPropertyValue("--atlas-gate-state-dot-border")).toBe(colors.borderDashed[2]);
    expect(root.style.getPropertyValue("--atlas-gate-state")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-gate-button-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-gate-lede")).toBe(colors.inkSecondary);
    // Two disclosed literals with no real token match.
    expect(root.style.getPropertyValue("--atlas-gate-breadcrumb-dot")).toBe("#CFC6D6");
    expect(root.style.getPropertyValue("--atlas-gate-button-bg")).toBe("#F6F4F9");
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<GateHeader />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
