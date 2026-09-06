import type { EntryRoleKey, ThreadEntry } from "./fixtures";

/**
 * M3 E3 — the real-event synthesis layer, decided (not left as an open
 * question) during M3 roadmap scoping per master-plan operating
 * principle #3 ("there must never be two independently writable truths
 * for the same fact"): `events` stays the single writer, this module
 * only adds a read-time transform, never a new written record.
 *
 * A genuine finding from building this: `ThreadEntry`'s own fixture
 * shape (`PACKET_A2_ENTRIES` in `./fixtures.ts`) is rich, authored
 * fictional dialogue — named participants ("Terra"), task plans with
 * ETAs, escalation prose. Real backend `events` rows carry none of
 * that; they are mechanical facts only: `event_type`, `entity_type`,
 * `before_json`/`after_json`, a `reason` code, and a real actor
 * identity. This module deliberately does **not** fabricate narrative
 * content to fill that gap — doing so would misrepresent synthetic
 * text as something a real participant said. It produces an honest,
 * plain description of what actually, mechanically happened, in the
 * same `ThreadEntry` shape so `PacketThread` can render it, but never
 * claims a plan, an ETA, or a quoted remark that no real event
 * recorded.
 */

export interface RealEvent {
  event_id: number;
  entity_type: string;
  entity_id: string;
  event_type: string;
  before_json: Record<string, unknown>;
  after_json: Record<string, unknown>;
  reason: { kind: string; reason_code: string; detail_reference: string | null };
  actor_type: string;
  actor_id: string;
  created_at: string;
}

/**
 * Real actor_type values observed in this codebase's own tests and
 * commands are free-form text (no closed enum in operational_state.py),
 * e.g. "MaestroDeveloper", "IntegrationAgent",
 * "IndependentImplementationReviewer", "system", "Owner". This maps the
 * ones this program has actually seen to the closest honest
 * `EntryRoleKey` — never a fictional role. Anything unrecognized falls
 * back to "co" (Coordinator), the same neutral, no-role-label bucket
 * `ROLE_LABEL` already uses for the coordinator itself, since an
 * unattributed mechanical fact is closest in kind to a coordinator
 * observation, not a worker/reviewer/owner claim this session has no
 * real evidence for.
 */
function roleKeyForActorType(actorType: string): EntryRoleKey {
  const normalized = actorType.toLowerCase();
  if (normalized.includes("owner")) return "ow";
  if (normalized.includes("review")) return "rv";
  if (normalized.includes("architect")) return "ar";
  if (normalized.includes("integration")) return "co";
  if (normalized.includes("developer") || normalized.includes("worker") || normalized.includes("qwen")) {
    return "wk";
  }
  return "co";
}

/** `created_at` is a canonical UTC timestamp (e.g. "2026-09-06T19:00:00.000000Z"); render just HH:MM, matching every other real time value already shown in this program. */
function formatTime(createdAt: string): string {
  const match = /T(\d{2}):(\d{2})/.exec(createdAt);
  return match ? `${match[1]}:${match[2]}` : createdAt;
}

/**
 * One honest, plain-English description of a real state transition —
 * never invented dialogue. Cites the real event_type, the real
 * before/after state (when present), and the real reason_code.
 */
function describeEvent(event: RealEvent): string {
  const before = typeof event.before_json?.["state"] === "string" ? (event.before_json["state"] as string) : null;
  const after = typeof event.after_json?.["state"] === "string" ? (event.after_json["state"] as string) : null;
  const reasonCode = event.reason?.reason_code;

  let body: string;
  if (before && after) {
    body = `${event.entity_type} ${event.entity_id}: ${before} → ${after}`;
  } else {
    body = `${event.entity_type} ${event.entity_id}: ${event.event_type}`;
  }
  return reasonCode ? `${body} (${reasonCode})` : body;
}

export function synthesizeThreadEntry(event: RealEvent): ThreadEntry {
  return {
    k: roleKeyForActorType(event.actor_type),
    who: event.actor_type,
    text: describeEvent(event),
    time: formatTime(event.created_at),
  };
}

export function synthesizeThreadEntries(events: RealEvent[]): ThreadEntry[] {
  return events.map(synthesizeThreadEntry);
}
