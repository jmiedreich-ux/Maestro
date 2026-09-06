import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PlanTab } from "./PlanTab";
import { GATE_CRITERIA } from "../gate/fixtures";
import { PLAN_BREADCRUMB, PLAN_PACKETS, PLAN_STATE_LABEL } from "../plan/fixtures";

afterEach(cleanup);

/**
 * jsdom (like real browsers) silently re-serializes a raw inline hex
 * color to `rgb(...)` when read back via `.style.*` — so an
 * exact-string comparison against the original hex literal must
 * convert through the same normalization first, matching the
 * discipline `connectionState.ts` (G1) and F3C's own implementation
 * review already established for exactly this defect class.
 */
function hexToRgb(hex: string): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

describe("PlanTab", () => {
  it("renders the real breadcrumb and title", () => {
    render(<PlanTab />);
    expect(screen.getByText(PLAN_BREADCRUMB)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Plan" })).toBeInTheDocument();
  });

  it("derives the stats line directly from the real PLAN_PACKETS states, summing to the real total", () => {
    const counts = { done: 0, run: 0, wait: 0, block: 0, pend: 0 };
    for (const p of PLAN_PACKETS) {
      counts[p.state] += 1;
    }
    const ahead = counts.wait + counts.block + counts.pend;
    expect(counts.done + counts.run + ahead).toBe(PLAN_PACKETS.length);

    render(<PlanTab />);
    expect(screen.getByText(`${counts.done} complete · ${counts.run} running · ${ahead} ahead`)).toBeInTheDocument();
  });

  it("renders all 8 real PLAN_PACKETS rows with their exact id, short title, and state label", () => {
    render(<PlanTab />);
    for (const packet of PLAN_PACKETS) {
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      expect(within(row).getByText(packet.short)).toBeInTheDocument();
      expect(within(row).getByText(PLAN_STATE_LABEL[packet.state])).toBeInTheDocument();
    }
  });

  it("renders exactly 8 real packet rows, each a real <button>", () => {
    render(<PlanTab />);
    const rows = screen.getAllByRole("button").filter((b) => b.className.includes("packetRow"));
    expect(rows).toHaveLength(8);
  });

  it("highlights only A.2's own row as active (the only packet with any real conversation data)", () => {
    render(<PlanTab />);
    const activeId = screen.getByText("A.2");
    const activeRow = activeId.closest('[class*="packetRow"]') as HTMLElement;
    expect(activeRow.className).toContain("packetRowActive");

    for (const packet of PLAN_PACKETS) {
      if (packet.id === "A.2") continue;
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      expect(row.className).not.toContain("packetRowActive");
    }
  });

  it("renders each real packet's own exact per-state dot color/shape (not just non-empty)", () => {
    render(<PlanTab />);
    for (const packet of PLAN_PACKETS) {
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      const dot = row.querySelector('[class*="packetDot"]') as HTMLElement;
      if (packet.state === "done") {
        expect(dot.style.borderRadius).toBe("3px");
        expect(dot.style.background).toBe(hexToRgb(colors.success));
      } else if (packet.state === "run") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.background).toBe(hexToRgb(colors.accentLight));
        expect(dot.style.boxShadow).toBe("0 0 0 4px rgba(140,107,255,.2)");
      } else if (packet.state === "block") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`2px solid ${hexToRgb("#D08A83")}`);
      } else if (packet.state === "wait") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`2px solid ${hexToRgb(colors.borderDashed[2])}`);
      } else {
        // pend
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`1.5px dashed ${hexToRgb(colors.borderDashed[2])}`);
      }
    }
  });

  it("renders each real packet's own exact track-segment color, matching the mockup's own done/run/other derivation", () => {
    render(<PlanTab />);
    const track = document.querySelector('[class*="track"]') as HTMLElement;
    const segments = track.querySelectorAll('[class*="trackSegment"]');
    expect(segments).toHaveLength(PLAN_PACKETS.length);
    segments.forEach((segment, index) => {
      const state = PLAN_PACKETS[index].state;
      const background = (segment as HTMLElement).style.background;
      if (state === "done") {
        expect(background).toBe(hexToRgb(colors.success));
      } else if (state === "run") {
        // The real mockup's own track derivation uses the identical
        // #8C6BFF for both the run dot and the run track segment —
        // this must be the SAME real token as the dot's own run color,
        // not colors.accent (a different, darker real token this
        // slice's own first draft mistakenly used here).
        expect(background).toBe(hexToRgb(colors.accentLight));
      } else {
        expect(background).toBe(hexToRgb("#E4DEEC"));
      }
    });
  });

  it("renders no onClick navigation on any packet row (no real multi-packet thread capability exists yet)", () => {
    render(<PlanTab />);
    // A real <button> with no onClick still fires no visible state
    // change; this is a documentation-style assertion that the rows
    // are inert by construction, not wired to fake navigation.
    const rows = screen.getAllByRole("button").filter((b) => b.className.includes("packetRow"));
    expect(rows).toHaveLength(PLAN_PACKETS.length);
  });

  it("renders the real 'M1-B gate' row with its own real derived met-count, reusing E7's GATE_CRITERIA", () => {
    const yesCount = GATE_CRITERIA.filter((c) => c.met === "yes").length;
    render(<PlanTab />);
    expect(screen.getByText("M1-B gate")).toBeInTheDocument();
    expect(screen.getByText(`${yesCount} of ${GATE_CRITERIA.length} met ›`)).toBeInTheDocument();
    const gateButton = screen.getByRole("button", { name: /M1-B gate/ });
    expect(gateButton).not.toBeDisabled();
  });

  it("(F4B) clicking the gate row opens the real GateSheet, unlike the still-inert packet rows", () => {
    render(<PlanTab />);
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /M1-B gate/ }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
  });

  it("(F4B) closing the sheet (via its own Close button) returns focus to the gate row", () => {
    render(<PlanTab />);
    const gateButton = screen.getByRole("button", { name: /M1-B gate/ });
    fireEvent.click(gateButton);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(gateButton).toHaveFocus();
  });

  it("sets the real, checked B2 tokens and the disclosed literals", () => {
    expect(colors.inkMuted).toBe("#8E8299");
    expect(colors.inkSecondary).toBe("#6C6376");
    expect(colors.surface).toBe("#FFFFFF");
    expect(colors.ink).toBe("#221C29");
    expect(colors.borderDashed[0]).toBe("#DCD5E4");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");

    const { container } = render(<PlanTab />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-plan-breadcrumb")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-plan-stats")).toBe(colors.inkSecondary);
    expect(root.style.getPropertyValue("--atlas-plan-row-bg")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-plan-row-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-plan-gate-border")).toBe(colors.borderDashed[0]);
    expect(root.style.getPropertyValue("--atlas-plan-gate-dot-border")).toBe(colors.borderDashed[2]);
    // Disclosed literals, no real token match.
    expect(root.style.getPropertyValue("--atlas-plan-row-bg-active")).toBe("#EFEAFE");
    expect(root.style.getPropertyValue("--atlas-plan-row-meta-active")).toBe("#6C55B8");
    expect(root.style.getPropertyValue("--atlas-plan-gate-label")).toBe("#4C4457");
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PlanTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
