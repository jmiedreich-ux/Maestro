import { describe, expect, it } from "vitest";
import { deriveRealHeaderState } from "./realHeaderState";
import type { ThreadEntry } from "./fixtures";

function entry(overrides: Partial<ThreadEntry> = {}): ThreadEntry {
  return {
    k: "wk",
    who: "Maestro Developer",
    text: "Ready to start → Assigned — work started",
    time: "1:51 PM",
    afterState: "Leased",
    ...overrides,
  };
}

describe("deriveRealHeaderState", () => {
  it("prefers the real authoritative packet state over inferring from entries", () => {
    const state = deriveRealHeaderState("packet-foundry-cg-m4-19", [entry({ afterState: "Leased" })], "Running");
    expect(state.title).toBe("In progress");
  });

  it("falls back to inferring the latest state from entries when no authoritative state has loaded yet", () => {
    const state = deriveRealHeaderState("packet-foundry-cg-m4-19", [entry({ afterState: "Leased" })], null);
    expect(state.title).toBe("Assigned");
  });

  it("reports 'Waiting for events' when there is neither an authoritative state nor any entry with a state", () => {
    const state = deriveRealHeaderState("packet-foundry-cg-m4-19", [], null);
    expect(state.title).toBe("Waiting for events");
  });

  it("strips the 'packet-' prefix for the eyebrow", () => {
    const state = deriveRealHeaderState("packet-foundry-cg-m4-19", [], null);
    expect(state.eyebrow).toBe("foundry-cg-m4-19");
  });

  it("surfaces the latest entry's own detail as a separate, prominent field", () => {
    const state = deriveRealHeaderState(
      "packet-foundry-cg-m4-19",
      [entry({ text: "Ready to start → Assigned — work started" })],
      "Running",
    );
    expect(state.latestDetail).toBe("work started");
  });
});
