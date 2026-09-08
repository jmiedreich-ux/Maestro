"""M4.06/M4.07 — route_integration_validate_only /
route_independent_implementation, driven through a real Succeeded
attempt with a real commit, reaching a real MergeReady packet.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.coverage_reconstruction import reconstruct_coverage  # noqa: E402
from maestro.operational_state import InvalidRecord, InvalidTransition  # noqa: E402
from maestro.review_dispatch import (  # noqa: E402
    route_independent_implementation,
    route_integration_validate_only,
)


class ReviewDispatchTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

        # A real change inside the packet's own real owned path, in the
        # fixture's own real repository (its real worktree_path at claim
        # time) -- so base_commit really is an ancestor of head.
        target = self.fixture.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real change\n")
        self.head_commit = self.fixture.repository.commit_all("real owned-path change")

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        self.coverage = reconstruct_coverage(
            packet, repository=str(self.fixture.repository.path), head=self.head_commit,
            slice_id="MB-M4-06-TEST", reconstruction_commands=["echo reconstruct"],
        )
        self.assertTrue(self.coverage["result"]["ready"], self.coverage["result"]["blockers"])

        finished = self.fixture.finish_succeeded(self.head_commit)
        self.assertEqual(finished["packet"]["state"], "AwaitingIntegration")
        self.packet_version = finished["packet"]["version"]

    def tearDown(self):
        self.fixture.close()

    def test_the_full_real_chain_reaches_merge_ready(self):
        integration = route_integration_validate_only(
            self.fixture.store, "packet-1", self.packet_version,
            self.coverage, "attempt-1", "integration-agent-1", "review-integration-1", ACTOR,
        )
        self.assertEqual(integration["packet"]["state"], "AwaitingReview")

        independent = route_independent_implementation(
            self.fixture.store, "packet-1", integration["packet"]["version"],
            self.coverage, "attempt-1", "independent-reviewer-1", "review-independent-1", ACTOR,
        )
        self.assertEqual(independent["packet"]["state"], "MergeReady")

    def test_independent_review_before_integration_review_is_rejected(self):
        # _REVIEW_ROUTES requires the real Integration/ValidateOnly
        # review first -- exactly the structural gap the fidelity
        # review caught in the original packet breakdown draft.
        with self.assertRaises(InvalidTransition):
            route_independent_implementation(
                self.fixture.store, "packet-1", self.packet_version,
                self.coverage, "attempt-1", "independent-reviewer-1", "review-independent-1", ACTOR,
            )

    def test_a_not_ready_coverage_is_rejected_by_the_real_validator(self):
        packet = dict(self.fixture.store.snapshot("Packet", "packet-1"), checks_json=["false"])
        not_ready_coverage = reconstruct_coverage(
            packet, repository=str(self.fixture.repository.path), head=self.head_commit,
            slice_id="MB-M4-06-TEST-FAIL", reconstruction_commands=["echo reconstruct"],
        )
        with self.assertRaises(InvalidRecord):
            route_integration_validate_only(
                self.fixture.store, "packet-1", self.packet_version,
                not_ready_coverage, "attempt-1", "integration-agent-1", "review-integration-1", ACTOR,
            )


if __name__ == "__main__":
    unittest.main()
