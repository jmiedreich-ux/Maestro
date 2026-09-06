import { afterEach, describe, expect, it, vi } from "vitest";
import { redispatchCrash, resolveCrashHold } from "./realCrashCommands";

const ACTOR = { actor_type: "Owner", actor_id: "owner-1", correlation_id: "correlation-1" };

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("resolveCrashHold", () => {
  it("posts a real resolve-crash command", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ packet: { state: "Cancelled" } }) });
    vi.stubGlobal("fetch", fetchMock);

    const result = await resolveCrashHold({ packetId: "packet-1", expectedVersion: 1, actor: ACTOR });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/command/resolve-crash",
      expect.objectContaining({ method: "POST" })
    );
    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body as string);
    expect(body.packet_id).toBe("packet-1");
    expect(result).toEqual({ packet: { state: "Cancelled" } });
  });

  it("throws with the real server error detail on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ error: "stale_state" }) })
    );

    await expect(
      resolveCrashHold({ packetId: "packet-1", expectedVersion: 1, actor: ACTOR })
    ).rejects.toThrow("stale_state");
  });
});

describe("redispatchCrash", () => {
  it("posts a real redispatch-crash command", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ closed_packet: { state: "Cancelled" }, redispatched_packet: { state: "Planned" } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await redispatchCrash({ packetId: "packet-1", expectedVersion: 1, actor: ACTOR });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/command/redispatch-crash",
      expect.objectContaining({ method: "POST" })
    );
    expect(result).toEqual({ closed_packet: { state: "Cancelled" }, redispatched_packet: { state: "Planned" } });
  });

  it("throws with the real server error detail on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ error: "invalid_command" }) })
    );

    await expect(
      redispatchCrash({ packetId: "packet-1", expectedVersion: 1, actor: ACTOR })
    ).rejects.toThrow("invalid_command");
  });
});
