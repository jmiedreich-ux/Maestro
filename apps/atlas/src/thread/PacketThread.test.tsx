import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { computeShowAvatar, PacketThread } from "./PacketThread";
import { PACKET_A2_ENTRIES, type ThreadEntry } from "./fixtures";

afterEach(cleanup);

describe("PacketThread", () => {
  it("renders all six real fixture messages, in order, with their exact body text", () => {
    render(<PacketThread />);
    const bodies = screen.getAllByText(/./, { selector: "p" }).map((p) => p.textContent);
    expect(bodies).toEqual(PACKET_A2_ENTRIES.map((e) => e.text));
  });

  it("shows the avatar and name row on every entry in this fixture (no consecutive same-author pair without an intervening plan/cadence entry)", () => {
    render(<PacketThread />);
    // Every one of the 6 fixture entries in A.2 is either a different
    // author than the previous one, or immediately follows a
    // plan/cadence-bearing entry from the same author — so all 6 show
    // their own avatar and name row. This is a real, checked property
    // of the actual fixture data, not an assumption.
    expect(screen.getAllByText("Coordinator")).toHaveLength(3);
    expect(screen.getAllByText("Terra")).toHaveLength(3);
  });

  it("shows the correct role label next to each name (Coordinator: none, Terra: Implementor)", () => {
    render(<PacketThread />);
    expect(screen.getAllByText("Implementor")).toHaveLength(3);
  });

  it("renders the Coordinator avatar with the reference file's real background, not the neutralChip token's value", () => {
    // colors.neutralChip is "#F2EEF8" — a real, different token this
    // avatar must NOT use. jsdom reports computed inline styles as
    // rgb(...); #F2EEF8 = rgb(242,238,248), #EFEBF2 (the correct,
    // reference-file value) = rgb(239,235,242) — both spelled out
    // explicitly so this assertion actually distinguishes them, rather
    // than comparing an rgb() string to a hex string that could never
    // match either way.
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<PacketThread />);
    const avatars = Array.from(container.querySelectorAll('[aria-hidden="true"]')).filter(
      (el) => el.textContent === "CO",
    );
    expect(avatars.length).toBeGreaterThan(0);
    for (const avatar of avatars) {
      expect((avatar as HTMLElement).style.background).toBe("rgb(239, 235, 242)");
      expect((avatar as HTMLElement).style.background).not.toBe("rgb(242, 238, 248)");
    }
  });

  it("computeShowAvatar: a real consecutive same-author pair with no intervening card groups (avatar omitted)", () => {
    // Synthetic data, for algorithm verification only — not product
    // fixture content. Two plain messages from the same author with
    // nothing between them.
    const synthetic: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00" },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(synthetic, 0)).toBe(true);
    expect(computeShowAvatar(synthetic, 1)).toBe(false);
  });

  it("computeShowAvatar: never groups across a plan- or cadence-bearing entry, even with the same author", () => {
    const syntheticPlan: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00", plan: { name: "x", summary: "y", steps: [] } },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(syntheticPlan, 1)).toBe(true);

    const syntheticCadence: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00", cadence: true },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(syntheticCadence, 1)).toBe(true);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PacketThread />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
