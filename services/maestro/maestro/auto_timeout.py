"""M4.03 — real auto-timeout.

Small, real wiring: for each real `StaleAttempt` M4.02 finds, call the
already-real, already-tested `finish_attempt_execution(outcome=
"TimedOut")` — which correctly routes the packet to `NeedsReplan` (real,
tested M1 logic) and releases the lease. This is only "call it for real
instead of a human doing it," per this session's own real manual
precedent (the redispatch this session performed by hand for the
original CG-M4-20 attempt).
"""

from __future__ import annotations

from dataclasses import dataclass

from .dispatch_orchestrator import now_iso
from .operational_state import Actor, OperationalStateStore, StaleState
from .staleness_detector import StaleAttempt


def _reason(code: str) -> dict:
    return {"kind": "reason", "reason_code": code, "detail_reference": None}


@dataclass(frozen=True)
class TimeoutResult:
    attempt_id: str
    packet_id: str
    applied: bool
    """``False`` when a real race already resolved the attempt first
    (a real `StaleState`) — not an error, this side honestly lost a
    real race rather than silently overwriting the winner."""


def timeout_stale_attempt(
    store: OperationalStateStore, stale: StaleAttempt, actor: Actor,
) -> TimeoutResult:
    reason = _reason("WORKER_WENT_SILENT")
    idempotency_key = f"auto-timeout-{stale.attempt_id}-{stale.execution_handle}"
    try:
        store.finish_attempt_execution(
            stale.attempt_id,
            stale.attempt_version,
            stale.packet_version,
            stale.lease_version,
            stale.execution_handle,
            "TimedOut",
            None,
            f"lease {stale.lease_id} expired at {stale.expires_at}, no real completion observed",
            reason,
            idempotency_key,
            actor,
            now_iso(),
        )
        return TimeoutResult(attempt_id=stale.attempt_id, packet_id=stale.packet_id, applied=True)
    except StaleState:
        return TimeoutResult(attempt_id=stale.attempt_id, packet_id=stale.packet_id, applied=False)


def timeout_all_stale_attempts(
    store: OperationalStateStore, stale_attempts: list[StaleAttempt], actor: Actor,
) -> list[TimeoutResult]:
    """Real, sequential — one real `StaleState` loss for one attempt
    must never abort the rest of a real recovery sweep."""
    return [timeout_stale_attempt(store, stale, actor) for stale in stale_attempts]
