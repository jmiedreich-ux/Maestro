/**
 * M3 E5 — real command calls for the owner-decision card's two options.
 * "Allow a sentinel version" maps to the already-wired D2 command
 * (/command/resolve-decision, target_state="Ready" — the real, honest
 * backend counterpart of "resumes now" per read_api.py's own D2
 * comment). "Amend the A.1 contract" maps to the newly-wired
 * dispatch-correction command (D3's real gap, closed this session):
 * record_and_dispatch_correction, an already-existing, already-tested
 * M1 command with zero real callers until now.
 */

const READ_API_BASE_URL = "http://127.0.0.1:8765";

export interface RealActor {
  actor_type: string;
  actor_id: string;
  correlation_id: string;
}

export interface RealDecisionContext {
  packetId: string;
  expectedVersion: number;
  actor: RealActor;
}

export interface RealCorrectionContext extends RealDecisionContext {
  reviewId: string;
}

async function postCommand(path: string, body: Record<string, unknown>): Promise<unknown> {
  const response = await fetch(`${READ_API_BASE_URL}${path}`, {
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

export function resolveDecisionSentinel(context: RealDecisionContext): Promise<unknown> {
  return postCommand("/command/resolve-decision", {
    idempotency_key: `atlas-sentinel-${context.packetId}-${context.expectedVersion}`,
    actor: context.actor,
    packet_id: context.packetId,
    expected_version: context.expectedVersion,
    target_state: "Ready",
    reason_payload: { kind: "reason", reason_code: "OWNER_ALLOWED_SENTINEL", detail_reference: null },
  });
}

export function dispatchCorrection(context: RealCorrectionContext): Promise<unknown> {
  return postCommand("/command/dispatch-correction", {
    idempotency_key: `atlas-amend-${context.packetId}-${context.expectedVersion}`,
    actor: context.actor,
    packet_id: context.packetId,
    expected_version: context.expectedVersion,
    review_id: context.reviewId,
    reason_payload: { kind: "reason", reason_code: "OWNER_AMENDED_CONTRACT", detail_reference: null },
  });
}
