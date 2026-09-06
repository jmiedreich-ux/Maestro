/**
 * M3 E6 — real command calls for two of the crash card's three options.
 * "Re-dispatch A.2 to another implementor" is the real, honest
 * counterpart this session's M3 packet-compiler machinery made
 * possible: close the failed packet and materialize a fresh one for
 * the same work item (redispatch-crash). "Hold A.2 and inspect the
 * worktree" was already wired in M2 (resolve-crash). "Resume Terra from
 * the last boundary" has no real backend counterpart at all — this
 * system's attempts are immutable once Failed/TimedOut/Stale, and a
 * "resumed" process would actually just be a fresh attempt from the
 * packet's own base_commit, which is exactly what re-dispatch already,
 * honestly, is — see read_api.py's own comment above
 * _handle_redispatch_crash. Faking a distinct "resume" would
 * misrepresent a capability this system does not have, so that option
 * stays deliberately unwired.
 */

import { readApiBaseUrl } from "../readApiBaseUrl";

export interface RealActor {
  actor_type: string;
  actor_id: string;
  correlation_id: string;
}

export interface RealCrashContext {
  packetId: string;
  expectedVersion: number;
  actor: RealActor;
}

async function postCommand(path: string, body: Record<string, unknown>): Promise<unknown> {
  const response = await fetch(`${readApiBaseUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `${path} failed: ${(payload as { error?: string }).error ?? response.status}`
    );
  }
  return payload;
}

export function resolveCrashHold(context: RealCrashContext): Promise<unknown> {
  return postCommand("/command/resolve-crash", {
    idempotency_key: `atlas-hold-${context.packetId}-${context.expectedVersion}`,
    actor: context.actor,
    packet_id: context.packetId,
    expected_version: context.expectedVersion,
    reason_payload: { kind: "reason", reason_code: "OWNER_HELD_FOR_INSPECTION", detail_reference: null },
  });
}

export function redispatchCrash(context: RealCrashContext): Promise<unknown> {
  return postCommand("/command/redispatch-crash", {
    idempotency_key: `atlas-redispatch-${context.packetId}-${context.expectedVersion}`,
    actor: context.actor,
    packet_id: context.packetId,
    expected_version: context.expectedVersion,
    reason_payload: { kind: "reason", reason_code: "OWNER_REDISPATCHED", detail_reference: null },
  });
}
