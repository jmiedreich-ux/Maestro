import { describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { deriveConnectionState } from "./connectionState";

describe("deriveConnectionState", () => {
  it("normal: live indicator reads 'idle', strip hidden, on both surfaces", () => {
    for (const surface of ["desktop", "mobile"] as const) {
      const state = deriveConnectionState("normal", surface);
      expect(state.liveLabel).toBe("idle");
      expect(state.liveDotColor).toBe(colors.inkMuted);
      expect(state.liveTextColor).toBe(colors.inkFaint);
      expect(state.strip.show).toBe(false);
    }
  });

  it("disconnected: live indicator reads 'reconnecting', using real warning tokens", () => {
    const state = deriveConnectionState("disconnected", "desktop");
    expect(state.liveLabel).toBe("reconnecting");
    expect(state.liveDotColor).toBe(colors.warning);
    expect(state.liveTextColor).toBe(colors.warningText);
  });

  it("disconnected: strip is shown with the real warning-token colors", () => {
    const state = deriveConnectionState("disconnected", "desktop");
    expect(state.strip.show).toBe(true);
    expect(state.strip.bg).toBe(colors.warningWash);
    expect(state.strip.border).toBe(colors.warningBorder);
    expect(state.strip.ink).toBe(colors.warningText);
    expect(state.strip.dot).toBe(colors.warning);
    expect(state.strip.title).toBe("Reconnecting");
  });

  it("disconnected: desktop and mobile strips have different real copy, not a shared string", () => {
    const desktop = deriveConnectionState("disconnected", "desktop");
    const mobile = deriveConnectionState("disconnected", "mobile");
    expect(desktop.strip.body).toContain("this window");
    expect(mobile.strip.body).toContain("this phone");
    expect(desktop.strip.body).not.toBe(mobile.strip.body);
    expect(desktop.strip.meta).toBe("retry 3 · 0:12");
    expect(mobile.strip.meta).toBe("retry 3");
  });
});
