"""M4.03 — timeout_stale_attempt / timeout_all_stale_attempts.

Uses a real, short lease (1 second) and a real `time.sleep` past it,
rather than querying `find_stale_attempts` against a simulated future
"now" — a real bug this caught while writing it: `finish_attempt_
execution(outcome="TimedOut")` validates the lease is expired against
the *actual* real now it's called with, so simulating a future "now"
only for detection while the finish call used genuine wall-clock time
raised a real `InvalidTransition`, honestly, since real time hadn't
actually passed yet.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, NOW, REASON, ClaimedPacketFixture  # noqa: E402

from maestro.auto_timeout import timeout_all_stale_attempts, timeout_stale_attempt  # noqa: E402
from maestro.dispatch_orchestrator import now_iso  # noqa: E402
from maestro.staleness_detector import find_stale_attempts  # noqa: E402


class AutoTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture(lease_expires_in_seconds=1)
        self.fixture.start_execution()

    def tearDown(self):
        self.fixture.close()

    def test_a_real_stale_attempt_is_timed_out_and_routes_to_needs_replan(self):
        time.sleep(1.2)
        found = find_stale_attempts(self.fixture.config, now_iso())
        self.assertEqual(len(found), 1)

        result = timeout_stale_attempt(self.fixture.store, found[0], ACTOR)
        self.assertTrue(result.applied)
        self.assertEqual(result.attempt_id, "attempt-1")

        snapshot = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(snapshot["state"], "NeedsReplan")
        lease_snapshot = self.fixture.store.snapshot("Lease", "lease-1")
        self.assertEqual(lease_snapshot["state"], "Expired")

    def test_a_real_race_already_resolved_by_a_normal_finish_is_honestly_reported_not_applied(self):
        time.sleep(1.2)
        found = find_stale_attempts(self.fixture.config, now_iso())
        self.assertEqual(len(found), 1)
        stale = found[0]

        # A real completion wins the race first (e.g. M4.01's own
        # orchestrator finishing normally just before recovery acts).
        self.fixture.store.finish_attempt_execution(
            "attempt-1", stale.attempt_version, stale.packet_version, stale.lease_version,
            stale.execution_handle, "Succeeded", "a" * 40, "evidence-ref", REASON, "finish-1", ACTOR, NOW,
        )

        result = timeout_stale_attempt(self.fixture.store, stale, ACTOR)
        self.assertFalse(result.applied)

        snapshot = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(snapshot["state"], "AwaitingIntegration")

    def test_a_real_idempotent_replay_of_the_same_timeout_applies_once(self):
        time.sleep(1.2)
        found = find_stale_attempts(self.fixture.config, now_iso())
        first = timeout_stale_attempt(self.fixture.store, found[0], ACTOR)
        self.assertTrue(first.applied)

        # The exact same real stale-attempt facts, called again (e.g. a
        # second recovery sweep before the read model catches up) --
        # must replay the original real result, not raise or double-close.
        second = timeout_stale_attempt(self.fixture.store, found[0], ACTOR)
        self.assertTrue(second.applied)

    def test_timeout_all_stale_attempts_continues_past_one_real_race_loss(self):
        time.sleep(1.2)
        found = find_stale_attempts(self.fixture.config, now_iso())
        self.assertEqual(len(found), 1)
        stale = found[0]

        self.fixture.store.finish_attempt_execution(
            "attempt-1", stale.attempt_version, stale.packet_version, stale.lease_version,
            stale.execution_handle, "Succeeded", "a" * 40, "evidence-ref", REASON, "finish-1", ACTOR, NOW,
        )

        results = timeout_all_stale_attempts(self.fixture.store, [stale], ACTOR)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].applied)


if __name__ == "__main__":
    unittest.main()
