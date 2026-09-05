import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PacketHeader } from "./PacketHeader";
import { derivePacketHeaderState } from "./headerState";
import { PACKET_A2_ENTRIES, type ThreadEntry } from "./fixtures";

afterEach(cleanup);

describe("derivePacketHeaderState", () => {
  it("derives the real blocked/escalated state from C1's frozen A.2 entries, every field from one function", () => {
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.isBlocked).toBe(true);
    expect(state.stateLine).toBe("Terra is blocked and waiting on your decision");
    expect(state.lastReport).toBe("14:52");
    expect(state.blocker).toBe("theme version for theme-free outputs");
    expect(state.nextLabel).toBe("Waiting on you");
    expect(state.next).toBe("41m");
  });

  it("reports unavailable, not a fabricated value, for a synthetic non-escalated thread (no real fixture backs this branch yet)", () => {
    const synthetic: ThreadEntry[] = [
      { k: "co", who: "Coordinator", text: "Go.", time: "10:00" },
      { k: "wk", who: "Terra", text: "On it.", time: "10:05" },
    ];
    const state = derivePacketHeaderState(synthetic);
    expect(state.isBlocked).toBe(false);
    expect(state.stateLine).toBe("unavailable");
    expect(state.lastReport).toBe("10:05");
    expect(state.blocker).toBe("none");
    expect(state.nextLabel).toBe("unavailable");
    expect(state.next).toBe("unavailable");
  });

  it("(F1) derives a real 40% progress from PACKET_A2_ENTRIES' own real plan.steps (2 of 5 marked done), not the reference file's fabricated 41%", () => {
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    const planEntry = PACKET_A2_ENTRIES.find((entry) => entry.plan !== undefined);
    expect(planEntry?.plan?.steps.filter((step) => step.status === "done")).toHaveLength(2);
    expect(planEntry?.plan?.steps).toHaveLength(5);
    expect(state.progressPercent).toBe(40);
  });

  it("(F1) derives real boundary timestamps from the first and last real Terra (wk) entries", () => {
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.boundaryBegin).toBe("13:51");
    expect(state.boundaryHeld).toBe("14:52");
  });

  it("(F1) reports headline/subline/progress/boundaries/next-panel as unavailable for a synthetic non-escalated thread", () => {
    const synthetic: ThreadEntry[] = [
      { k: "co", who: "Coordinator", text: "Go.", time: "10:00" },
      { k: "wk", who: "Terra", text: "On it.", time: "10:05" },
    ];
    const state = derivePacketHeaderState(synthetic);
    expect(state.headline).toBe("unavailable");
    expect(state.subline).toBe("unavailable");
    expect(state.progressPercent).toBe("unavailable");
    expect(state.boundaryBegin).toBe("unavailable");
    expect(state.boundaryHeld).toBe("unavailable");
    expect(state.nextPanelText).toBe("unavailable");
    expect(state.nextPanelHeading).toBe("what happens next");
  });

  it("finds the last implementor (wk) report, not simply the last entry overall", () => {
    // Real property of PACKET_A2_ENTRIES: its very last entry is the
    // Coordinator's escalation (14:56), but the last report FROM
    // Terra is the earlier blocked message (14:52) — these differ,
    // and lastReport must track the implementor, not the last entry.
    expect(PACKET_A2_ENTRIES.at(-1)?.who).toBe("Coordinator");
    expect(PACKET_A2_ENTRIES.at(-1)?.time).toBe("14:56");
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.lastReport).toBe("14:52");
  });
});

describe("PacketHeader", () => {
  it("renders the real eyebrow and title, never the mockup's own unverifiable 'issue #970' segment", () => {
    render(<PacketHeader />);
    expect(screen.getByText("m1-a · a.2")).toBeInTheDocument();
    expect(screen.getByText("Add output-specific Runtime Package creation")).toBeInTheDocument();
    expect(screen.queryByText(/issue #970/)).toBeNull();
  });

  it("renders the state line and the three summary pairs, all consistent with one derived state object", () => {
    render(<PacketHeader />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText(state.stateLine)).toBeInTheDocument();
    expect(screen.getByText("Last report")).toBeInTheDocument();
    expect(screen.getByText(state.lastReport)).toBeInTheDocument();
    expect(screen.getByText("Blocker")).toBeInTheDocument();
    expect(screen.getByText(state.blocker)).toBeInTheDocument();
    expect(screen.getByText(state.nextLabel)).toBeInTheDocument();
    expect(screen.getByText(state.next)).toBeInTheDocument();
  });

  it("sets the header surface, border, and warning-state CSS variables to the real, checked tokens", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    expect(colors.borderDivider[1]).toBe("#F3F0F6");
    expect(colors.warning).toBe("#E0A32E");
    expect(colors.warningText).toBe("#8A5A08");
    const { container } = render(<PacketHeader />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-header-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-header-summary-border")).toBe(colors.borderDivider[1]);
    expect(root.style.getPropertyValue("--atlas-header-dot")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-header-state-color")).toBe(colors.warningText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PacketHeader />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
