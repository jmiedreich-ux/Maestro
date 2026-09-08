"""record_notification_outcome — the new store command M4.12/M4.13 need,
since no command existed to update a notification after insert."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.dispatch_orchestrator import now_iso  # noqa: E402
from maestro.operational_state import InvalidRecord, InvalidTransition, StaleState  # noqa: E402

REASON = {"kind": "reason", "reason_code": "TEST_SETUP", "detail_reference": None}


def _notification(fixture, notification_id="notification-1"):
    event_id = fixture.store.events_after(0, 1)[0]["event_id"]
    payload = {
        "kind": "notification", "event_id": event_id, "audience": "ProjectArchitect",
        "severity": "ActionNeeded", "subject_reference": "packet-1",
        "evidence_references": [], "next_action_reference": "review",
    }
    return fixture.store.record_notification(
        {
            "notification_id": notification_id, "event_id": event_id, "run_id": "run-1",
            "packet_id": "packet-1", "channel": "LocalDurable", "destination_reference": "local-db",
            "audience": "ProjectArchitect", "severity": "ActionNeeded", "message_type": "ReviewReady",
            "grouping_key": "run-1", "escalation_at": None, "payload_json": payload,
            "state": "Pending", "attempt_count": 0, "last_error_payload_json": None,
            "next_attempt_at": None,
        },
        f"seed-{notification_id}", ACTOR, now_iso(),
    )


class NotificationOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture()

    def tearDown(self):
        self.fixture.close()

    def test_delivered_moves_pending_to_delivered_and_bumps_attempt_count(self):
        seeded = _notification(self.fixture)
        result = self.fixture.store.record_notification_outcome(
            "notification-1", seeded["version"], {"result": "Delivered"},
            "outcome-1", ACTOR, now_iso(),
        )
        self.assertEqual(result["notification"]["state"], "Delivered")
        self.assertEqual(result["attempt_count"], 1)
        self.assertIsNone(result["next_attempt_at"])
        stored = self.fixture.store.snapshot("Notification", "notification-1")
        self.assertEqual((stored["state"], stored["attempt_count"], stored["version"]), ("Delivered", 1, 2))

    def test_retryable_failure_stays_pending_with_a_real_next_attempt_at(self):
        seeded = _notification(self.fixture)
        outcome = {
            "result": "Failed", "retryable": True, "next_attempt_at": "2026-09-08T06:00:00.000000Z",
            "error_reason": {"kind": "reason", "reason_code": "DELIVERY_TIMEOUT", "detail_reference": None},
        }
        result = self.fixture.store.record_notification_outcome(
            "notification-1", seeded["version"], outcome, "outcome-1", ACTOR, now_iso(),
        )
        self.assertEqual(result["notification"]["state"], "Pending")
        self.assertEqual(result["attempt_count"], 1)
        self.assertEqual(result["next_attempt_at"], "2026-09-08T06:00:00.000000Z")

        again = self.fixture.store.record_notification_outcome(
            "notification-1", result["notification"]["version"], {"result": "Delivered"},
            "outcome-2", ACTOR, now_iso(),
        )
        self.assertEqual(again["notification"]["state"], "Delivered")
        self.assertEqual(again["attempt_count"], 2)

    def test_terminal_failure_moves_to_failed(self):
        seeded = _notification(self.fixture)
        outcome = {
            "result": "Failed", "retryable": False,
            "error_reason": {"kind": "reason", "reason_code": "DESTINATION_REJECTED", "detail_reference": None},
        }
        result = self.fixture.store.record_notification_outcome(
            "notification-1", seeded["version"], outcome, "outcome-1", ACTOR, now_iso(),
        )
        self.assertEqual(result["notification"]["state"], "Failed")
        self.assertIsNone(result["next_attempt_at"])

    def test_a_non_pending_row_is_rejected(self):
        seeded = _notification(self.fixture)
        delivered = self.fixture.store.record_notification_outcome(
            "notification-1", seeded["version"], {"result": "Delivered"},
            "outcome-1", ACTOR, now_iso(),
        )
        with self.assertRaises(InvalidTransition):
            self.fixture.store.record_notification_outcome(
                "notification-1", delivered["notification"]["version"], {"result": "Delivered"},
                "outcome-2", ACTOR, now_iso(),
            )

    def test_a_stale_version_is_rejected(self):
        seeded = _notification(self.fixture)
        with self.assertRaises(StaleState):
            self.fixture.store.record_notification_outcome(
                "notification-1", seeded["version"] + 1, {"result": "Delivered"},
                "outcome-1", ACTOR, now_iso(),
            )

    def test_an_invalid_result_is_rejected(self):
        seeded = _notification(self.fixture)
        with self.assertRaises(InvalidRecord):
            self.fixture.store.record_notification_outcome(
                "notification-1", seeded["version"], {"result": "Bogus"},
                "outcome-1", ACTOR, now_iso(),
            )

    def test_replay_is_exact(self):
        seeded = _notification(self.fixture)
        outcome = {"result": "Delivered"}
        first = self.fixture.store.record_notification_outcome(
            "notification-1", seeded["version"], outcome, "outcome-1", ACTOR, "2026-09-08T06:00:00.000000Z",
        )
        replay = self.fixture.store.record_notification_outcome(
            "notification-1", seeded["version"], outcome, "outcome-1", ACTOR, "2026-09-08T06:00:00.000000Z",
        )
        self.assertEqual(first, replay)


if __name__ == "__main__":
    unittest.main()
