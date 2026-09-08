"""M4.12 (N1) / M4.13 (N2) — real notification delivery loop.

**New store command required and added alongside this** (not
originally scoped for M4, discovered while building N1):
`operational_state.record_notification_outcome` — `notifications` had
versioned `state`/`attempt_count`/`next_attempt_at` columns from M1,
and the schema's own closed event-type list already reserved
`NotificationStateChanged` for exactly this, but no command ever wrote
to it after the initial `record_notification` insert. Durable-state
plumbing, not new product scope, so built as part of this packet under
the Architect's own durability authority.

`LocalDurable` is the only channel this delivers today: the row is
already durable in `notifications` itself, so "delivery" for this
channel is real but trivial (no external call, no real failure mode) —
it exists to prove the real loop end-to-end before `Slack` (M4.15,
blocked on real credentials) has anything to plug into.

N2 (retry/backoff): failures use real exponential backoff
(`retry_delay_seconds` doubling from a real base, capped), computed
against the real `now` passed to each cycle rather than wall-clock
inside the loop, so backoff scheduling is exactly reproducible in
tests.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .config import RuntimeConfig
from .dispatch_orchestrator import _add_seconds
from .operational_state import InvalidTransition, OperationalStateStore, StaleState

MAX_RETRYABLE_ATTEMPTS = 5
BASE_RETRY_DELAY_SECONDS = 30
MAX_RETRY_DELAY_SECONDS = 3600


class DeliveryError(RuntimeError):
    """A channel-level delivery failure, real and retryable by nature
    (a channel adapter raises this; the loop decides retry policy)."""


@dataclass(frozen=True)
class DeliveryResult:
    notification_id: str
    outcome: str  # "Delivered" | "RetryScheduled" | "FailedTerminal"
    attempt_count: int


def _backoff_seconds(attempt_number: int) -> int:
    """Real doubling backoff: 30s, 60s, 120s, 240s, ... capped at 3600s.
    ``attempt_number`` is the attempt about to be retried from (1-based:
    the first retry after attempt 1 uses the base delay)."""
    delay = BASE_RETRY_DELAY_SECONDS * (2 ** max(attempt_number - 1, 0))
    return min(delay, MAX_RETRY_DELAY_SECONDS)


def deliver_local_durable(notification: dict) -> None:
    """The one real channel adapter this packet wires: `LocalDurable`.
    The row is already durably stored by `record_notification` itself,
    so this adapter has no real external call and — by construction —
    no real failure mode to simulate; it exists so the delivery loop
    has one real, unconditionally-succeeding channel to prove itself
    against before Slack (blocked) exists."""
    if notification["channel"] != "LocalDurable":
        raise DeliveryError(f"no real deliverer registered for channel {notification['channel']!r}")


_DELIVERERS = {"LocalDurable": deliver_local_durable}


def deliver_one(
    store: OperationalStateStore, notification: dict, actor, now: str,
) -> DeliveryResult:
    """Attempts real delivery of one `Pending` notification row and
    records the real outcome. ``notification`` must be a real, current
    snapshot (``store.snapshot("Notification", ...)``) — callers loop
    over real `Pending` rows themselves; this function does not query."""
    notification_id = notification["notification_id"]
    deliverer = _DELIVERERS.get(notification["channel"])
    error_reason = None
    if deliverer is None:
        error_reason = {
            "kind": "reason", "reason_code": "NO_DELIVERER_REGISTERED", "detail_reference": None,
        }
    else:
        try:
            deliverer(notification)
        except DeliveryError as error:
            error_reason = {
                "kind": "reason", "reason_code": "DELIVERY_FAILED", "detail_reference": str(error)[:512],
            }

    if error_reason is None:
        outcome = {"result": "Delivered"}
    else:
        next_attempt_number = notification["attempt_count"] + 1
        if next_attempt_number >= MAX_RETRYABLE_ATTEMPTS:
            outcome = {"result": "Failed", "retryable": False, "error_reason": error_reason}
        else:
            outcome = {
                "result": "Failed", "retryable": True, "error_reason": error_reason,
                "next_attempt_at": _add_seconds(now, _backoff_seconds(next_attempt_number)),
            }

    try:
        result = store.record_notification_outcome(
            notification_id, notification["version"], outcome,
            f"deliver-{notification_id}-{notification['attempt_count']}", actor, now,
        )
    except (StaleState, InvalidTransition):
        # A concurrent delivery attempt already recorded an outcome for
        # this exact real row -- an honest race loss, not this loop's
        # error to raise.
        return DeliveryResult(notification_id, "RaceLost", notification["attempt_count"])

    return DeliveryResult(
        notification_id, result["notification"]["state"], result["attempt_count"],
    )


def find_pending_notifications(config: RuntimeConfig, run_id: str, now: str) -> list[dict]:
    """Real, read-only, matching `staleness_detector.py`'s own
    established pattern: every real `Pending` notification for
    ``run_id`` whose `next_attempt_at` has already passed (or was never
    set)."""
    connection = sqlite3.connect(
        f"file:{config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0,
    )
    try:
        rows = connection.execute(
            "SELECT notification_id, channel, state, attempt_count, version "
            "FROM notifications "
            "WHERE run_id=? AND state='Pending' "
            "AND (next_attempt_at IS NULL OR next_attempt_at<=?) "
            "ORDER BY notification_id",
            (run_id, now),
        ).fetchall()
    finally:
        connection.close()
    return [
        {
            "notification_id": str(row[0]), "channel": str(row[1]), "state": str(row[2]),
            "attempt_count": int(row[3]), "version": int(row[4]),
        }
        for row in rows
    ]


def deliver_pending(
    store: OperationalStateStore, config: RuntimeConfig, run_id: str, actor, now: str,
) -> list[DeliveryResult]:
    """Real loop: finds every real `Pending` notification for
    ``run_id`` due for a real attempt, and delivers each. Sequential and
    never aborts on one row's failure or race loss, matching
    `auto_timeout.timeout_all_stale_attempts`'s own established shape."""
    results = []
    for notification in find_pending_notifications(config, run_id, now):
        results.append(deliver_one(store, notification, actor, now))
    return results
