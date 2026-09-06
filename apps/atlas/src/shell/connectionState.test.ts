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

  it("(G2) crashed: live indicator stays 'idle' (this app has no real live connection to claim, even mid-crash)", () => {
    const state = deriveConnectionState("crashed", "desktop");
    expect(state.liveLabel).toBe("idle");
    expect(state.liveDotColor).toBe(colors.inkMuted);
    expect(state.liveTextColor).toBe(colors.inkFaint);
  });

  it("(G2) crashed: strip is shown with the real danger-token colors, matching CrashCard's own mapping", () => {
    const state = deriveConnectionState("crashed", "desktop");
    expect(state.strip.show).toBe(true);
    expect(state.strip.bg).toBe(colors.dangerWash);
    expect(state.strip.border).toBe(colors.dangerBorder);
    expect(state.strip.ink).toBe(colors.dangerText);
    expect(state.strip.dot).toBe(colors.danger);
    expect(state.strip.title).toBe("Terra is not running");
    expect(state.strip.meta).toBe("stopped 14:58");
  });

  it("(G2) crashed: desktop and mobile strips have different real copy, not a shared string", () => {
    const desktop = deriveConnectionState("crashed", "desktop");
    const mobile = deriveConnectionState("crashed", "mobile");
    expect(desktop.strip.body).toBe(
      "A.2 stopped without a handoff. Its worktree and locks are held, so A.3 stays undispatchable until this is resolved.",
    );
    expect(mobile.strip.body).toBe(
      "A.2 stopped without a handoff. Worktree and locks are held, so A.3 stays undispatchable.",
    );
    expect(desktop.strip.body).not.toBe(mobile.strip.body);
  });

  it("(G3) empty: derives identically to 'normal' — a real, checked fact, not an unhandled state", () => {
    for (const surface of ["desktop", "mobile"] as const) {
      const empty = deriveConnectionState("empty", surface);
      const normal = deriveConnectionState("normal", surface);
      expect(empty).toEqual(normal);
      expect(empty.liveLabel).toBe("idle");
      expect(empty.strip.show).toBe(false);
    }
  });
});
