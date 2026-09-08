"""M4.14 (N3) — real trigger wiring.

Decides which real state changes actually create a notification, and
calls the already-real `record_notification` from those real facts —
a thin composition layer over already-built M4 commands (R3's
`auto_timeout`, V3/V4's `review_dispatch`), matching the established
`owner_acceptance.py`/`merge_observation.py` wiring-module shape,
rather than editing those already-tested modules in place.

**Real, disclosed constraint found while building this** (per the
fidelity review): `notifications` has no natural-key uniqueness (unlike
`reviews`' own `UNIQUE(...)`), so `record_notification`'s idempotency-
key/replay protection only guards the *exact same call* repeating, not
a crashed/restarted trigger re-firing with a fresh `notification_id`.
Every function here derives `notification_id` deterministically from
the real triggering `event_id` (`f"notification-event-{event_id}"`) —
never a freshly generated id — so a restarted trigger for the same
real event collides on the table's own real primary key instead of
silently double-notifying.
"""

from __future__ import annotations

from .operational_state import Actor, OperationalStateStore


def _reason_free_notification_id(event_id: int) -> str:
    return f"notification-event-{event_id}"


def _latest_event_id(store: OperationalStateStore, entity_type: str, entity_id: str) -> int:
    """The real, most recent event for one entity -- used to derive a
    deterministic notification_id and to satisfy `notifications.event_id`'s
    own real foreign key. Real, not cached: scans the real event log."""
    matches = [
        event for event in store.events_after(0, 1000)
        if event["entity_type"] == entity_type and event["entity_id"] == entity_id
    ]
    if not matches:
        raise ValueError(f"no real event found for {entity_type}:{entity_id}")
    return max(event["event_id"] for event in matches)


def _notify(
    store: OperationalStateStore, *, run_id: str, packet_id: str, event_id: int,
    severity: str, message_type: str, next_action_reference: str, actor: Actor, now: str,
) -> dict:
    notification_id = _reason_free_notification_id(event_id)
    payload = {
        "kind": "notification", "event_id": event_id, "audience": "ProjectArchitect",
        "severity": severity, "subject_reference": packet_id,
        "evidence_references": [], "next_action_reference": next_action_reference,
    }
    return store.record_notification(
        {
            "notification_id": notification_id, "event_id": event_id, "run_id": run_id,
            "packet_id": packet_id, "channel": "LocalDurable", "destination_reference": "local-db",
            "audience": "ProjectArchitect", "severity": severity, "message_type": message_type,
            "grouping_key": run_id, "escalation_at": None, "payload_json": payload,
            "state": "Pending", "attempt_count": 0, "last_error_payload_json": None,
            "next_attempt_at": None,
        },
        f"notify-{notification_id}", actor, now,
    )


def notify_attempt_timed_out(
    store: OperationalStateStore, *, run_id: str, packet_id: str, actor: Actor, now: str,
) -> dict:
    """Real trigger: R3 (`auto_timeout`) applied a real `TimedOut`
    outcome. Fires from the real `PacketStateChanged` event that
    transition produced (`Running -> NeedsReplan`)."""
    event_id = _latest_event_id(store, "Packet", packet_id)
    return _notify(
        store, run_id=run_id, packet_id=packet_id, event_id=event_id,
        severity="ActionNeeded", message_type="AttemptTimedOut",
        next_action_reference="recovery", actor=actor, now=now,
    )


def notify_awaiting_architect(
    store: OperationalStateStore, *, run_id: str, packet_id: str, actor: Actor, now: str,
) -> dict:
    """Real trigger: V3/V4 routed a real `RequestChanges` review
    (`AwaitingReview -> AwaitingArchitect`)."""
    event_id = _latest_event_id(store, "Packet", packet_id)
    return _notify(
        store, run_id=run_id, packet_id=packet_id, event_id=event_id,
        severity="ActionNeeded", message_type="PacketAwaitingArchitect",
        next_action_reference="architect-ruling", actor=actor, now=now,
    )


def notify_coverage_not_ready(
    store: OperationalStateStore, *, run_id: str, packet_id: str, actor: Actor, now: str,
) -> dict:
    """Real trigger: the development-manager loop (M4's own driver)
    found a real attempt's coverage not ready (an out-of-scope path, a
    failing check) -- since no review of any kind can be recorded
    against non-ready coverage (`_validate_review_coverage`'s own
    unconditional requirement), the loop cannot route anything further
    on its own; this is a real, honest stopping point for a human."""
    event_id = _latest_event_id(store, "Packet", packet_id)
    return _notify(
        store, run_id=run_id, packet_id=packet_id, event_id=event_id,
        severity="ActionNeeded", message_type="CoverageNotReady",
        next_action_reference="human-review", actor=actor, now=now,
    )


def notify_merge_ready(
    store: OperationalStateStore, *, run_id: str, packet_id: str, actor: Actor, now: str,
) -> dict:
    """Real trigger: V3/V4 routed a real `Approve` review
    (`AwaitingReview -> MergeReady`)."""
    event_id = _latest_event_id(store, "Packet", packet_id)
    return _notify(
        store, run_id=run_id, packet_id=packet_id, event_id=event_id,
        severity="CompletionReady", message_type="PacketMergeReady",
        next_action_reference="owner-acceptance", actor=actor, now=now,
    )
