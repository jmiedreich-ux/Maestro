import { describe, expect, it } from "vitest";
import { synthesizeThreadEntries, synthesizeThreadEntry, type RealEvent } from "./realEventSynthesis";

function event(overrides: Partial<RealEvent> = {}): RealEvent {
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

describe("synthesizeThreadEntry", () => {
  it("describes a real before/after state transition honestly, never inventing dialogue", () => {
    const entry = synthesizeThreadEntry(event());
    expect(entry.text).toBe("Planned → Waiting — work started");
  });

  it("falls back to a humanized real event_type when before/after state is absent", () => {
    const entry = synthesizeThreadEntry(
      event({
        event_type: "SecretReferenceObserved",
        before_json: {},
        after_json: { status: "Active" },
        reason: { kind: "reason", reason_code: "SECRET_STORED", detail_reference: null },
      })
    );
    expect(entry.text).toBe("Secret reference observed — secret stored");
  });

  it("sets afterState from the real after_json.state field, for the header to read", () => {
    const withState = synthesizeThreadEntry(event());
    expect(withState.afterState).toBe("Waiting");
    const withoutState = synthesizeThreadEntry(event({ after_json: { status: "Active" } }));
    expect(withoutState.afterState).toBeUndefined();
  });

  it("formats the real created_at timestamp as HH:MM", () => {
    const entry = synthesizeThreadEntry(event({ created_at: "2026-09-06T14:52:30.000000Z" }));
    expect(entry.time).toBe("14:52");
  });

  it("maps a real Owner actor_type to the ow role key", () => {
    const entry = synthesizeThreadEntry(event({ actor_type: "Owner" }));
    expect(entry.k).toBe("ow");
  });

  it("maps a real IndependentImplementationReviewer actor_type to the rv role key", () => {
    const entry = synthesizeThreadEntry(event({ actor_type: "IndependentImplementationReviewer" }));
    expect(entry.k).toBe("rv");
  });

  it("maps a real IntegrationAgent actor_type to the co role key", () => {
    const entry = synthesizeThreadEntry(event({ actor_type: "IntegrationAgent" }));
    expect(entry.k).toBe("co");
  });

  it("maps a real MaestroDeveloper actor_type to the wk role key", () => {
    const entry = synthesizeThreadEntry(event({ actor_type: "MaestroDeveloper" }));
    expect(entry.k).toBe("wk");
  });

  it("falls back to the neutral co role key for an unrecognized real actor_type", () => {
    const entry = synthesizeThreadEntry(event({ actor_type: "system" }));
    expect(entry.k).toBe("co");
  });

  it("never sets plan, cadence, escalate, or closure — those are fixture-only narrative fields with no real backend source", () => {
    const entry = synthesizeThreadEntry(event());
    expect(entry.plan).toBeUndefined();
    expect(entry.cadence).toBeUndefined();
    expect(entry.escalate).toBeUndefined();
    expect(entry.closure).toBeUndefined();
  });

  it("uses the real actor_type verbatim as who, never a fictional name", () => {
    const entry = synthesizeThreadEntry(event({ actor_type: "MaestroDeveloper" }));
    expect(entry.who).toBe("MaestroDeveloper");
  });
});

describe("synthesizeThreadEntries", () => {
  it("maps a real event list in order", () => {
    const events = [
      event({ event_id: 1, before_json: { state: "Planned" }, after_json: { state: "Waiting" } }),
      event({ event_id: 2, before_json: { state: "Waiting" }, after_json: { state: "Ready" } }),
    ];
    const entries = synthesizeThreadEntries(events);
    expect(entries).toHaveLength(2);
    expect(entries[0].text).toContain("Planned → Waiting");
    expect(entries[1].text).toContain("Waiting → Ready");
  });

  it("returns an empty array for no real events, never inventing placeholder content", () => {
    expect(synthesizeThreadEntries([])).toEqual([]);
  });
});
