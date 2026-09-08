"""The real M4 driver loop — end-to-end: one already-dispatched, real
succeeded attempt reaches Merged through nothing but repeated
`run_cycle` calls, no manual routing in between."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.development_manager import run_cycle  # noqa: E402
from maestro.dispatch_orchestrator import now_iso  # noqa: E402


class DevelopmentManagerLoopTests(unittest.TestCase):
    def tearDown(self):
        self.fixture.close()

    def test_a_real_succeeded_attempt_reaches_merged_through_repeated_cycles_only(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

        target = self.fixture.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real change\n")
        head = self.fixture.repository.commit_all("real owned-path change")
        self.fixture.finish_succeeded(head)

        for _ in range(4):
            run_cycle(
                self.fixture.store, self.fixture.config,
                repository_path=str(self.fixture.repository.path), run_id="run-1",
                default_branch="main", actor=ACTOR, now=now_iso(),
                reconstruction_commands=["echo reconstruct"],
            )
            packet = self.fixture.store.snapshot("Packet", "packet-1")
            if packet["state"] == "Merged":
                break

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(packet["state"], "Merged")

        pending = [
            row for row in self.fixture.store.events_after(0, 1000)
            if row["entity_type"] == "Notification"
        ]
        self.assertTrue(pending)

    def test_a_real_stale_attempt_is_recovered_and_redispatched_by_the_loop_alone(self):
        self.fixture = ClaimedPacketFixture(lease_expires_in_seconds=1)
        self.fixture.start_execution()
        time.sleep(1.2)

        report = run_cycle(
            self.fixture.store, self.fixture.config,
            repository_path=str(self.fixture.repository.path), run_id="run-1",
            default_branch="main", actor=ACTOR, now=now_iso(),
            reconstruction_commands=["echo reconstruct"],
        )
        self.assertEqual(report.timed_out, ["packet-1"])
        self.assertEqual(len(report.redispatched), 1)

        new_packet_id = report.redispatched[0]
        replacement = self.fixture.store.snapshot("Packet", new_packet_id)
        self.assertIsNotNone(replacement)
        self.assertEqual(replacement["state"], "Planned")

    def test_a_real_owned_path_violation_cannot_be_mechanically_reviewed_and_only_notifies(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

        outside = self.fixture.repository.path / "package.json"
        outside.write_text("{}\n")
        head = self.fixture.repository.commit_all("touches a forbidden path")
        self.fixture.finish_succeeded(head)

        report = run_cycle(
            self.fixture.store, self.fixture.config,
            repository_path=str(self.fixture.repository.path), run_id="run-1",
            default_branch="main", actor=ACTOR, now=now_iso(),
            reconstruction_commands=["echo reconstruct"],
        )
        self.assertEqual(report.reviewed, ["packet-1"])
        packet = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(packet["state"], "AwaitingIntegration")
        notifications = [
            row for row in self.fixture.store.events_after(0, 1000)
            if row["entity_type"] == "Notification"
        ]
        self.assertTrue(notifications)


if __name__ == "__main__":
    unittest.main()
