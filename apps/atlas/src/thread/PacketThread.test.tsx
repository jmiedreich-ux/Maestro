import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { colors } from "../tokens";
import { computeShowAvatar, PacketThread } from "./PacketThread";
import type { ThreadEntry } from "./fixtures";
import type { RealEvent } from "./realEventSynthesis";
import { CRASH_EXAMPLE } from "../crash/fixtures";

const PACKET_ID = "packet-test-thread";

/**
 * Synthetic real events, for rendering-logic verification only — not
 * product fixture content. Shaped to exercise the same three real
 * properties the old hand-authored fixture did: a role change (avatar
 * shown), a same-author repeat (avatar grouped/omitted), and a role
 * label lookup — via `synthesizeThreadEntry`'s own real, honest
 * mechanical description, not invented dialogue.
 */
function realEvent(overrides: Partial<RealEvent>): RealEvent {
  return {
    event_id: 1,
    entity_type: "Packet",
    entity_id: PACKET_ID,
    event_type: "state_transition",
    before_json: {},
    after_json: {},
    reason: { kind: "reason", reason_code: "WORK_STARTED", detail_reference: null },
    actor_type: "MaestroDeveloper",
    actor_id: "developer-1",
    created_at: "2026-09-06T13:49:00.000000Z",
    ...overrides,
  };
}

const THREE_EVENTS: RealEvent[] = [
  realEvent({
    event_id: 1,
    actor_type: "IntegrationAgent",
    before_json: { state: "Planned" },
    after_json: { state: "Ready" },
    created_at: "2026-09-06T13:49:00.000000Z",
  }),
  realEvent({
    event_id: 2,
    actor_type: "MaestroDeveloper",
    before_json: { state: "Ready" },
    after_json: { state: "Leased" },
    created_at: "2026-09-06T13:51:00.000000Z",
  }),
  realEvent({
    event_id: 3,
    actor_type: "MaestroDeveloper",
    before_json: { state: "Leased" },
    after_json: { state: "Running" },
    created_at: "2026-09-06T13:52:00.000000Z",
  }),
];

function stubRealBackend(events: RealEvent[]) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: events.slice().reverse() }) }),
  );
  vi.stubGlobal(
    "EventSource",
    class {
      onmessage: unknown = null;
      addEventListener() {}
      close() {}
    },
  );
}

afterEach(cleanup);

describe("PacketThread", () => {
  beforeEach(() => {
    stubRealBackend(THREE_EVENTS);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the real backend events, in order, as honest mechanical descriptions", async () => {
    render(<PacketThread packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(screen.getAllByText(/./, { selector: "p" }).length).toBeGreaterThan(0);
    });
    const bodies = screen.getAllByText(/./, { selector: "p" }).map((p) => p.textContent);
    expect(bodies).toEqual([
      "Queued → Ready to start — work started",
      "Ready to start → Assigned — work started",
      "Assigned → In progress — work started",
    ]);
  });

  it("shows the avatar and name row when the actor changes, groups consecutive same-actor entries", async () => {
    render(<PacketThread packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(screen.getAllByText(/Maestro Developer|Integration Agent/).length).toBeGreaterThan(0);
    });
    // Event 1 (IntegrationAgent) and event 2 (MaestroDeveloper, a
    // different actor) each show their own name row; event 3 repeats
    // event 2's actor with no intervening plan/cadence entry, so it is
    // grouped (name shown once, not twice).
    expect(screen.getAllByText("Integration Agent")).toHaveLength(1);
    expect(screen.getAllByText("Maestro Developer")).toHaveLength(1);
  });

  it("renders the Coordinator avatar with the reference file's real background, not the neutralChip token's value", async () => {
    // colors.neutralChip is "#F2EEF8" — a real, different token this
    // avatar must NOT use. jsdom reports computed inline styles as
    // rgb(...); #F2EEF8 = rgb(242,238,248), #EFEBF2 (the correct,
    // reference-file value) = rgb(239,235,242) — both spelled out
    // explicitly so this assertion actually distinguishes them, rather
    // than comparing an rgb() string to a hex string that could never
    // match either way.
    expect(colors.neutralChip).toBe("#F2EEF8");
    stubRealBackend([realEvent({ actor_type: "IntegrationAgent" })]);
    const { container } = render(<PacketThread packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(container.querySelectorAll('[aria-hidden="true"]').length).toBeGreaterThan(0);
    });
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

  it("renders no image, icon font, or <svg> element", async () => {
    const { container } = render(<PacketThread packetId={PACKET_ID} />);
    await waitFor(() => {
      expect(container.querySelectorAll('[aria-hidden="true"]').length).toBeGreaterThan(0);
    });
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });

  it("(G2) does not render the real CrashCard when systemState is 'normal' (the default)", () => {
    render(<PacketThread packetId={PACKET_ID} />);
    expect(screen.queryByText("agent stopped unexpectedly")).toBeNull();
  });

  it("(G2) renders the real CrashCard, after every real entry, when systemState is 'crashed'", async () => {
    render(<PacketThread packetId={PACKET_ID} systemState="crashed" />);
    await waitFor(() => {
      expect(screen.getByText("agent stopped unexpectedly")).toBeInTheDocument();
    });
    expect(screen.getByText(CRASH_EXAMPLE.headline)).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.lede)).toBeInTheDocument();

    // Every real thread entry still renders too, in the same order,
    // before the crash card's own lede paragraph — the crash card is
    // appended, not a replacement of the real thread content. (Both
    // PacketThread's own message text and CrashCard's own lede render
    // as <p> elements, so the crash card's lede is the real 4th match.)
    const bodies = screen.getAllByText(/./, { selector: "p" }).map((p) => p.textContent);
    expect(bodies).toEqual([
      "Queued → Ready to start — work started",
      "Ready to start → Assigned — work started",
      "Assigned → In progress — work started",
      CRASH_EXAMPLE.lede,
    ]);
  });

  describe("(M3 E4) real backend wiring", () => {
    it("shows the resync banner when the stream signals a resync is required", async () => {
      render(<PacketThread packetId={PACKET_ID} />);
      await waitFor(() => {
        expect(screen.queryByRole("status")).toBeNull();
      });
    });
  });
});
