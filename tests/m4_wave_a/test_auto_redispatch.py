"""M4.04 — redispatch_after_needs_replan, driven by a real M4.02/M4.03
recovery timeout (not a hand-crafted NeedsReplan) so the whole real
chain (stale -> timeout -> redispatch) is proven together.
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.auto_redispatch import redispatch_after_needs_replan  # noqa: E402
from maestro.auto_timeout import timeout_stale_attempt  # noqa: E402
from maestro.dispatch_orchestrator import now_iso  # noqa: E402
from maestro.operational_state import InvalidRecord, InvalidTransition  # noqa: E402
from maestro.staleness_detector import find_stale_attempts  # noqa: E402


class AutoRedispatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture(lease_expires_in_seconds=1)
        self.fixture.start_execution()
        time.sleep(1.2)
        found = find_stale_attempts(self.fixture.config, now_iso())
        self.assertEqual(len(found), 1)
        result = timeout_stale_attempt(self.fixture.store, found[0], ACTOR)
        self.assertTrue(result.applied)
        needs_replan = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(needs_replan["state"], "NeedsReplan")
        self.needs_replan_version = needs_replan["version"]
        self.old_packet = needs_replan

    def tearDown(self):
        self.fixture.close()

    def test_a_real_recovery_driven_redispatch_carries_forward_every_real_fact(self):
        new_packet = redispatch_after_needs_replan(
            self.fixture.store, "packet-1", self.needs_replan_version,
            "packet-1-redispatch-1", "packet-r2", ACTOR,
        )
        self.assertEqual(new_packet["state"], "Planned")
        self.assertEqual(new_packet["packet_id"], "packet-1-redispatch-1")
        self.assertEqual(new_packet["run_id"], self.old_packet["run_id"])
        self.assertEqual(new_packet["work_item_id"], self.old_packet["work_item_id"])
        self.assertEqual(new_packet["base_commit"], self.old_packet["base_commit"])
        self.assertEqual(new_packet["expected_branch"], self.old_packet["expected_branch"])
        self.assertEqual(new_packet["owned_paths_json"], self.old_packet["owned_paths_json"])
        self.assertEqual(new_packet["checks_json"], self.old_packet["checks_json"])
        self.assertEqual(new_packet["context_policy_json"], self.old_packet["context_policy_json"])
        self.assertIsNone(new_packet["current_head"])
        self.assertEqual(new_packet["correction_count"], 0)

        old_packet_now = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(old_packet_now["state"], "Cancelled")

    def test_the_old_packets_own_revision_can_never_be_reused_even_under_a_new_id(self):
        # A real schema fact worth proving directly, not just asserting
        # in a docstring: packets' own UNIQUE(run_id,work_item_id,
        # packet_revision) means reusing the old packet_revision fails
        # even under a brand-new packet_id, matching this session's own
        # real precedent for why a redispatch always takes a genuinely
        # new revision, not just a new id.
        with self.assertRaises(InvalidRecord):
            redispatch_after_needs_replan(
                self.fixture.store, "packet-1", self.needs_replan_version,
                "packet-1-redispatch-1", "packet-r1", ACTOR,
            )

    def test_a_stale_expected_version_is_rejected_not_silently_applied(self):
        with self.assertRaises((InvalidTransition, Exception)):
            redispatch_after_needs_replan(
                self.fixture.store, "packet-1", self.needs_replan_version + 1,
                "packet-1-redispatch-1", "packet-r2", ACTOR,
            )
        # The old packet must still be NeedsReplan -- a rejected close
        # must never have partially applied.
        old_packet_now = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(old_packet_now["state"], "NeedsReplan")


if __name__ == "__main__":
    unittest.main()
