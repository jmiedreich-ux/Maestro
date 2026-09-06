import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useRealPacketThread } from "./useRealPacketThread";

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;
  private listeners: Record<string, ((event: MessageEvent<string>) => void)[]> = {};
  closed = false;

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(name: string, handler: (event: MessageEvent<string>) => void) {
    this.listeners[name] = [...(this.listeners[name] ?? []), handler];
  }

  emitMessage(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent<string>);
  }

  emitNamed(name: string, data: unknown) {
    for (const handler of this.listeners[name] ?? []) {
      handler({ data: JSON.stringify(data) } as MessageEvent<string>);
    }
  }

  close() {
    this.closed = true;
  }
}

function realEvent(overrides: Record<string, unknown> = {}) {
  return {
    event_id: 1,
    entity_type: "Packet",
    entity_id: "packet-foundry-cg-m4-19",
    event_type: "PacketStateChanged",
    before_json: { state: "Planned" },
    after_json: { state: "Waiting" },
    reason: { kind: "reason", reason_code: "WORK_STARTED", detail_reference: null },
    actor_type: "MaestroDeveloper",
    actor_id: "developer-1",
    created_at: "2026-09-06T19:00:00.000000Z",
    ...overrides,
  };
}

describe("useRealPacketThread", () => {
  beforeEach(() => {
    FakeEventSource.instances = [];
    // Test-only global stub — jsdom has no real EventSource.
    (globalThis as unknown as { EventSource: unknown }).EventSource = FakeEventSource;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    delete (globalThis as unknown as { EventSource?: unknown }).EventSource;
  });

  it("loads the real snapshot, reversed to oldest-first, filtered to this packet only", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        events: [
          realEvent({ event_id: 3, entity_id: "packet-other" }),
          realEvent({ event_id: 2, before_json: { state: "Waiting" }, after_json: { state: "Ready" } }),
          realEvent({ event_id: 1, before_json: { state: "Planned" }, after_json: { state: "Waiting" } }),
        ],
      }),
    });

    const { result } = renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));

    await waitFor(() => expect(result.current.entries).toHaveLength(2));
    expect(result.current.entries[0].text).toContain("Planned → Waiting");
    expect(result.current.entries[1].text).toContain("Waiting → Ready");
  });

  it("opens the real stream with after= the real max snapshot event id", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ events: [realEvent({ event_id: 7 })] }),
    });

    renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    expect(FakeEventSource.instances[0].url).toBe(
      "http://127.0.0.1:8765/stream/events?after=7"
    );
  });

  it("appends a real live event for this packet as it arrives", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: [] }) });

    const { result } = renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));

    act(() => {
      FakeEventSource.instances[0].emitMessage(
        realEvent({ event_id: 5, before_json: { state: "Ready" }, after_json: { state: "Dispatchable" } })
      );
    });

    await waitFor(() => expect(result.current.entries).toHaveLength(1));
    expect(result.current.entries[0].text).toContain("Ready → Dispatchable");
  });

  it("ignores a real live event for a different packet", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: [] }) });

    const { result } = renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));

    act(() => {
      FakeEventSource.instances[0].emitMessage(realEvent({ entity_id: "packet-other" }));
    });

    expect(result.current.entries).toHaveLength(0);
  });

  it("sets resyncRequired true on a real resync signal from the stream", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: [] }) });

    const { result } = renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));

    act(() => {
      FakeEventSource.instances[0].emitNamed("resync", { resync_required: true });
    });

    await waitFor(() => expect(result.current.resyncRequired).toBe(true));
  });

  it("closes the real stream connection on unmount", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ events: [] }) });

    const { unmount } = renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));
    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));

    unmount();
    expect(FakeEventSource.instances[0].closed).toBe(true);
  });

  it("returns a real, honest empty entries list when the snapshot fetch fails, never fabricated content", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error("network error"));

    const { result } = renderHook(() => useRealPacketThread("packet-foundry-cg-m4-19"));

    await waitFor(() => expect(FakeEventSource.instances).toHaveLength(1));
    expect(result.current.entries).toEqual([]);
  });
});
