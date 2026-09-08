"""M4.12/M4.13 — real notification delivery loop and retry/backoff."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.dispatch_orchestrator import now_iso  # noqa: E402
from maestro.notification_delivery import (  # noqa: E402
    MAX_RETRYABLE_ATTEMPTS,
    deliver_one,
    deliver_pending,
    find_pending_notifications,
)


def _seed(fixture, notification_id, *, channel="LocalDurable"):
    event_id = fixture.store.events_after(0, 1)[0]["event_id"]
    payload = {
        "kind": "notification", "event_id": event_id, "audience": "ProjectArchitect",
        "severity": "ActionNeeded", "subject_reference": "packet-1",
        "evidence_references": [], "next_action_reference": "review",
    }
    return fixture.store.record_notification(
        {
            "notification_id": notification_id, "event_id": event_id, "run_id": "run-1",
            "packet_id": "packet-1", "channel": channel, "destination_reference": "local-db",
            "audience": "ProjectArchitect", "severity": "ActionNeeded", "message_type": "ReviewReady",
            "grouping_key": "run-1", "escalation_at": None, "payload_json": payload,
            "state": "Pending", "attempt_count": 0, "last_error_payload_json": None,
            "next_attempt_at": None,
        },
        f"seed-{notification_id}", ACTOR, now_iso(),
    )


class NotificationDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture()

    def tearDown(self):
        self.fixture.close()

    def test_a_real_local_durable_notification_delivers_on_the_first_attempt(self):
        seeded = _seed(self.fixture, "notification-1")
        result = deliver_one(self.fixture.store, seeded, ACTOR, now_iso())
        self.assertEqual(result.outcome, "Delivered")
        self.assertEqual(result.attempt_count, 1)

    def test_an_unregistered_channel_schedules_a_real_retry_with_backoff(self):
        seeded = _seed(self.fixture, "notification-1", channel="Slack")
        now = "2026-09-08T06:00:00.000000Z"
        result = deliver_one(self.fixture.store, seeded, ACTOR, now)
        self.assertEqual(result.outcome, "Pending")
        stored = self.fixture.store.snapshot("Notification", "notification-1")
        self.assertEqual(stored["next_attempt_at"], "2026-09-08T06:00:30.000000Z")

    def test_exhausting_retries_reaches_a_real_terminal_failure(self):
        seeded = _seed(self.fixture, "notification-1", channel="Slack")
        now = "2026-09-08T06:00:00.000000Z"
        current = self.fixture.store.snapshot("Notification", "notification-1")
        self.assertEqual(current["notification_id"], seeded["notification_id"])
        row = seeded
        for _ in range(MAX_RETRYABLE_ATTEMPTS - 1):
            result = deliver_one(self.fixture.store, row, ACTOR, now)
            self.assertEqual(result.outcome, "Pending")
            row = self.fixture.store.snapshot("Notification", "notification-1")
        final = deliver_one(self.fixture.store, row, ACTOR, now)
        self.assertEqual(final.outcome, "Failed")
        self.assertEqual(final.attempt_count, MAX_RETRYABLE_ATTEMPTS)
        stored = self.fixture.store.snapshot("Notification", "notification-1")
        self.assertIsNone(stored["next_attempt_at"])

    def test_find_pending_notifications_respects_next_attempt_at(self):
        _seed(self.fixture, "notification-1", channel="Slack")
        far_future = "2026-09-09T00:00:00.000000Z"
        deliver_one(self.fixture.store, self.fixture.store.snapshot("Notification", "notification-1"), ACTOR, "2026-09-08T06:00:00.000000Z")

        due_now = find_pending_notifications(self.fixture.config, "run-1", "2026-09-08T06:00:00.000000Z")
        self.assertEqual(due_now, [])

        due_later = find_pending_notifications(self.fixture.config, "run-1", far_future)
        self.assertEqual([row["notification_id"] for row in due_later], ["notification-1"])

    def test_deliver_pending_delivers_every_real_due_row(self):
        _seed(self.fixture, "notification-1")
        _seed(self.fixture, "notification-2")
        results = deliver_pending(self.fixture.store, self.fixture.config, "run-1", ACTOR, now_iso())
        self.assertEqual({item.notification_id for item in results}, {"notification-1", "notification-2"})
        self.assertTrue(all(item.outcome == "Delivered" for item in results))


if __name__ == "__main__":
    unittest.main()
