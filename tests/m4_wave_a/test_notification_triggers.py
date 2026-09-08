"""M4.14 — real trigger wiring, driven through real R3/V3 chains."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.auto_timeout import timeout_stale_attempt  # noqa: E402
from maestro.coverage_reconstruction import reconstruct_coverage  # noqa: E402
from maestro.dispatch_orchestrator import now_iso  # noqa: E402
from maestro.notification_triggers import (  # noqa: E402
    notify_attempt_timed_out,
    notify_awaiting_architect,
    notify_merge_ready,
)
from maestro.operational_state import InvalidRecord  # noqa: E402
from maestro.review_dispatch import (  # noqa: E402
    route_independent_implementation,
    route_integration_validate_only,
)
from maestro.staleness_detector import find_stale_attempts  # noqa: E402


class NotificationTriggerTests(unittest.TestCase):
    def tearDown(self):
        self.fixture.close()

    def test_a_real_timeout_produces_a_deterministic_notification_id(self):
        self.fixture = ClaimedPacketFixture(lease_expires_in_seconds=1)
        self.fixture.start_execution()
        time.sleep(1.2)
        stale = find_stale_attempts(self.fixture.config, now_iso())
        self.assertEqual(len(stale), 1)
        timeout_stale_attempt(self.fixture.store, stale[0], ACTOR)

        result = notify_attempt_timed_out(
            self.fixture.store, run_id="run-1", packet_id="packet-1", actor=ACTOR, now=now_iso(),
        )
        self.assertEqual(result["state"], "Pending")

        replay = notify_attempt_timed_out(
            self.fixture.store, run_id="run-1", packet_id="packet-1", actor=ACTOR, now=now_iso(),
        )
        self.assertEqual(replay["notification_id"], result["notification_id"])

    def test_a_restarted_trigger_for_the_same_event_never_double_notifies(self):
        self.fixture = ClaimedPacketFixture(lease_expires_in_seconds=1)
        self.fixture.start_execution()
        time.sleep(1.2)
        stale = find_stale_attempts(self.fixture.config, now_iso())
        timeout_stale_attempt(self.fixture.store, stale[0], ACTOR)

        first = notify_attempt_timed_out(
            self.fixture.store, run_id="run-1", packet_id="packet-1", actor=ACTOR, now=now_iso(),
        )
        with self.assertRaises(InvalidRecord):
            self.fixture.store.record_notification(
                {
                    "notification_id": first["notification_id"], "event_id": first["event_id"],
                    "run_id": "run-1", "packet_id": "packet-1", "channel": "LocalDurable",
                    "destination_reference": "local-db", "audience": "ProjectArchitect",
                    "severity": "ActionNeeded", "message_type": "AttemptTimedOut",
                    "grouping_key": "run-1", "escalation_at": None,
                    "payload_json": first["payload_json"], "state": "Pending", "attempt_count": 0,
                    "last_error_payload_json": None, "next_attempt_at": None,
                },
                "a-totally-different-fresh-idempotency-key", ACTOR, now_iso(),
            )

    def test_a_real_request_changes_and_a_real_approve_each_notify_correctly(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()
        target = self.fixture.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real change\n")
        head = self.fixture.repository.commit_all("real owned-path change")

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        coverage = reconstruct_coverage(
            packet, repository=str(self.fixture.repository.path), head=head,
            slice_id="MB-M4-14-TEST", reconstruction_commands=["echo reconstruct"],
        )
        finished = self.fixture.finish_succeeded(head)
        integration = route_integration_validate_only(
            self.fixture.store, "packet-1", finished["packet"]["version"],
            coverage, "attempt-1", "integration-agent-1", "review-integration-1", ACTOR,
        )
        approved = route_independent_implementation(
            self.fixture.store, "packet-1", integration["packet"]["version"],
            coverage, "attempt-1", "independent-reviewer-1", "review-independent-1", ACTOR,
        )
        self.assertEqual(approved["packet"]["state"], "MergeReady")

        result = notify_merge_ready(
            self.fixture.store, run_id="run-1", packet_id="packet-1", actor=ACTOR, now=now_iso(),
        )
        self.assertEqual(result["message_type"], "PacketMergeReady")
        self.assertEqual(result["severity"], "CompletionReady")


if __name__ == "__main__":
    unittest.main()
