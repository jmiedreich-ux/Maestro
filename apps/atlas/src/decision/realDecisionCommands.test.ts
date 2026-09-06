import { afterEach, describe, expect, it, vi } from "vitest";
import { dispatchCorrection, resolveDecisionSentinel } from "./realDecisionCommands";

const ACTOR = { actor_type: "Owner", actor_id: "owner-1", correlation_id: "correlation-1" };

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("resolveDecisionSentinel", () => {
  it("posts a real resolve-decision command targeting Ready", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ packet: { state: "Ready" } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await resolveDecisionSentinel({
      packetId: "packet-foundry-cg-m4-19",
      expectedVersion: 4,
      actor: ACTOR,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:8765/command/resolve-decision",
      expect.objectContaining({ method: "POST" })
    );
    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body as string);
    expect(body.packet_id).toBe("packet-foundry-cg-m4-19");
    expect(body.expected_version).toBe(4);
    expect(body.target_state).toBe("Ready");
    expect(body.actor).toEqual(ACTOR);
    expect(result).toEqual({ packet: { state: "Ready" } });
  });

  it("throws with the real server error detail on a real 409", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ error: "stale_state" }) })
    );

    await expect(
      resolveDecisionSentinel({ packetId: "packet-1", expectedVersion: 1, actor: ACTOR })
    ).rejects.toThrow("stale_state");
  });
});

describe("dispatchCorrection", () => {
  it("posts a real dispatch-correction command with the real review_id", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ packet: { state: "Leased" } }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await dispatchCorrection({
      packetId: "packet-1",
      expectedVersion: 9,
      reviewId: "review-request-changes",
      actor: ACTOR,
    });

    const [, options] = fetchMock.mock.calls[0];
    const body = JSON.parse(options.body as string);
    expect(body.review_id).toBe("review-request-changes");
    expect(body.packet_id).toBe("packet-1");
    expect(result).toEqual({ packet: { state: "Leased" } });
  });

  it("throws with the real server error detail on a real invalid_command", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 400, json: async () => ({ error: "invalid_command" }) })
    );

    await expect(
      dispatchCorrection({ packetId: "packet-1", expectedVersion: 9, reviewId: "review-1", actor: ACTOR })
    ).rejects.toThrow("invalid_command");
  });
});
