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

/**
 * The read API's real `/snapshot/events` response encodes
 * `before_json`/`after_json`/`reason` as JSON-encoded *strings*
 * (confirmed against a live packet's own real events), not parsed
 * objects — a genuine gap this module used to silently fail on: every
 * `event.before_json["state"]` lookup below was reading a string
 * index, always `undefined`, so every real transition fell through to
 * the generic event_type fallback ("State changed" x3, with no
 * before/after ever shown). These three fields accept either shape so
 * a real backend response and a test's own plain-object fixture both
 * work.
 */
export interface RealEvent {
  event_id: number;
  entity_type: string;
  entity_id: string;
  event_type: string;
  before_json: Record<string, unknown> | string;
  after_json: Record<string, unknown> | string;
  reason: { kind: string; reason_code: string; detail_reference: string | null } | string;
  actor_type: string;
  actor_id: string;
  created_at: string;
}

function parseMaybeJson(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object") return value as Record<string, unknown>;
  if (typeof value === "string" && value.length > 0) {
    try {
      const parsed: unknown = JSON.parse(value);
      return parsed && typeof parsed === "object" ? (parsed as Record<string, unknown>) : {};
    } catch {
      return {};
    }
  }
  return {};
}

/**
 * A packet state usually lives at the top level (`{state: "..."}`),
 * but a compound command envelope (e.g. claim_packet_assignment's own
 * real `after_json`, which carries `attempt`/`lease`/`locks`/`claim`
 * alongside the packet) nests it under `packet.state` instead — read
 * whichever one is actually present, never guess a value neither
 * carries.
 */
function readState(parsed: Record<string, unknown>): string | null {
  if (typeof parsed["state"] === "string") return parsed["state"] as string;
  const nestedPacket = parsed["packet"];
  if (nestedPacket && typeof nestedPacket === "object" && typeof (nestedPacket as Record<string, unknown>)["state"] === "string") {
    return (nestedPacket as Record<string, unknown>)["state"] as string;
  }
  return null;
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

/**
 * `created_at` is a real UTC timestamp — but not one fixed separator:
 * the read API's own `/snapshot/events` response uses a space
 * ("2026-09-06 19:00:00"), while an SSE `/stream/events` frame or a
 * hand-built test fixture may use "T" (ISO 8601, "2026-09-06T19:00:00").
 * Assuming only "T" was a real bug — every real snapshot event's time
 * silently fell through to the raw, un-formatted string. Render as a
 * real 12-hour clock time with am/pm either way.
 */
function formatTime(createdAt: string): string {
  const match = /[T ](\d{2}):(\d{2})/.exec(createdAt);
  if (!match) return createdAt;
  const hour24 = Number(match[1]);
  const period = hour24 >= 12 ? "PM" : "AM";
  const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12;
  return `${hour12}:${match[2]} ${period}`;
}

/**
 * Turns a real machine identifier (a PascalCase event_type like
 * "PacketMaterialized", or a SCREAMING_SNAKE reason_code like
 * "WORK_STARTED") into plain, lowercase words — "packet materialized",
 * "work started". Never invents new words: every character it outputs
 * came from the real identifier, only re-cased and re-spaced.
 */
function humanizeWords(identifier: string): string {
  return identifier
    .replace(/_/g, " ")
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .toLowerCase()
    .trim();
}

/** Same word-splitting as `humanizeWords`, capitalized for use as the start of a sentence. */
function humanizeIdentifier(identifier: string): string {
  const words = humanizeWords(identifier);
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/**
 * Same word-splitting as `humanizeWords`, but every word capitalized —
 * for a real actor_type shown as a name ("MaestroDeveloper" ->
 * "Maestro Developer"), not a sentence.
 */
function titleCaseIdentifier(identifier: string): string {
  return humanizeWords(identifier)
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Plain, user-facing labels for the real operational states this
 * program's own state machine (`operational_state.py`) actually emits
 * — never a guessed or expanded set. Names not in this table (a future
 * real state this UI hasn't been taught yet) fall back to their own
 * humanized identifier rather than a guess.
 */
const STATE_LABELS: Record<string, string> = {
  Planned: "Queued",
  Waiting: "Waiting",
  Ready: "Ready to start",
  Dispatchable: "Ready to start",
  Leased: "Assigned",
  Running: "In progress",
  NeedsReplan: "Needs a decision",
  MergeReady: "Ready to merge",
  Cancelled: "Cancelled",
};

export function labelForState(state: string): string {
  return STATE_LABELS[state] ?? humanizeIdentifier(state);
}

/**
 * Drops a leading, redundant `entity_type` word from an `event_type`
 * before humanizing it — every event this thread renders already
 * belongs to the one entity its own header identifies (e.g.
 * "PacketMaterialized" on a Packet event reads as "Materialized", not
 * "Packet materialized").
 */
function humanizeEventType(eventType: string, entityType: string): string {
  const withoutEntityPrefix = eventType.startsWith(entityType) ? eventType.slice(entityType.length) : eventType;
  return humanizeIdentifier(withoutEntityPrefix || eventType);
}

/**
 * One honest, plain-language description of a real state transition —
 * never invented dialogue. Cites the real before/after state (when
 * present) and the real reason_code, in concise, humanized words
 * rather than raw identifiers. Omits `entity_type`/`entity_id`: every
 * event a real thread renders already belongs to the one packet its
 * own header identifies, so repeating the id on every line is clutter,
 * not information.
 */
function describeEvent(event: RealEvent): string {
  const before = readState(parseMaybeJson(event.before_json));
  const after = readState(parseMaybeJson(event.after_json));
  const reasonCode = parseMaybeJson(event.reason)["reason_code"];
  const reasonCodeText = typeof reasonCode === "string" ? reasonCode : undefined;

  let body: string;
  if (before && after) {
    const beforeLabel = labelForState(before);
    const afterLabel = labelForState(after);
    // Two distinct real internal states (e.g. Ready/Dispatchable) can
    // share one plain label — showing "X → X" would look like nothing
    // happened, so collapse to the single label instead of a false arrow.
    body = beforeLabel === afterLabel ? afterLabel : `${beforeLabel} → ${afterLabel}`;
  } else {
    body = humanizeEventType(event.event_type, event.entity_type);
  }
  return reasonCodeText ? `${body} — ${humanizeWords(reasonCodeText)}` : body;
}

export function synthesizeThreadEntry(event: RealEvent): ThreadEntry {
  const after = readState(parseMaybeJson(event.after_json)) ?? undefined;
  return {
    k: roleKeyForActorType(event.actor_type),
    who: titleCaseIdentifier(event.actor_type),
    text: describeEvent(event),
    time: formatTime(event.created_at),
    afterState: after,
  };
}

/**
 * `describeEvent` joins a state transition (or humanized event type)
 * and a humanized reason code with " — " when a reason is present.
 * Splitting on that same separator lets a caller show them as a
 * title/detail pair (ChatTab's timeline row) or pick just the detail
 * (the header's own "what actually just happened" line) instead of
 * always reading the one dense joined line.
 */
export function splitEntryText(text: string): { title: string; detail: string | null } {
  const separatorIndex = text.indexOf(" — ");
  if (separatorIndex === -1) return { title: text, detail: null };
  return { title: text.slice(0, separatorIndex), detail: text.slice(separatorIndex + 3) };
}

export function synthesizeThreadEntries(events: RealEvent[]): ThreadEntry[] {
  return events.map(synthesizeThreadEntry);
}
