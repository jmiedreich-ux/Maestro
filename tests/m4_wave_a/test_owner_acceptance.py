"""M4.09 — accept_packet, driven through a real MergeReady packet."""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.coverage_reconstruction import reconstruct_coverage  # noqa: E402
from maestro.operational_state import InvalidRecord  # noqa: E402
from maestro.owner_acceptance import accept_packet  # noqa: E402
from maestro.review_dispatch import (  # noqa: E402
    route_correction_review,
    route_independent_implementation,
    route_integration_validate_only,
)

from test_correction_review import _finding  # noqa: E402


def _reach_merge_ready(fixture: ClaimedPacketFixture) -> tuple[dict, str]:
    """Real happy path to MergeReady, returning (approve_result, head)."""
    target = fixture.repository.path / "tests" / "fake" / "new.spec.ts"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("// a real change\n")
    head = fixture.repository.commit_all("real owned-path change")

    packet = fixture.store.snapshot("Packet", "packet-1")
    coverage = reconstruct_coverage(
        packet, repository=str(fixture.repository.path), head=head,
        slice_id="MB-M4-09-TEST", reconstruction_commands=["echo reconstruct"],
    )
    finished = fixture.finish_succeeded(head)
    integration = route_integration_validate_only(
        fixture.store, "packet-1", finished["packet"]["version"],
        coverage, "attempt-1", "integration-agent-1", "review-integration-1", ACTOR,
    )
    approved = route_independent_implementation(
        fixture.store, "packet-1", integration["packet"]["version"],
        coverage, "attempt-1", "independent-reviewer-1", "review-independent-1", ACTOR,
    )
    return approved, head


class OwnerAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

    def tearDown(self):
        self.fixture.close()

    def test_a_real_merge_ready_packet_is_accepted_and_moves_to_awaiting_owner(self):
        approved, head = _reach_merge_ready(self.fixture)
        self.assertEqual(approved["packet"]["state"], "MergeReady")

        result = accept_packet(
            self.fixture.store, "packet-1", approved["packet"]["version"],
            "acceptance-1", "Owner", "architect-load-1", head, "review-independent-1", ACTOR,
        )
        self.assertEqual(result["packet"]["state"], "AwaitingOwner")

    def test_the_exact_head_must_really_match_the_initial_attempts_result_commit(self):
        approved, head = _reach_merge_ready(self.fixture)
        with self.assertRaises(InvalidRecord):
            accept_packet(
                self.fixture.store, "packet-1", approved["packet"]["version"],
                "acceptance-1", "Owner", "architect-load-1", "f" * 40,
                "review-independent-1", ACTOR,
            )

    def test_a_review_id_naming_a_non_approve_review_is_rejected(self):
        approved, head = _reach_merge_ready(self.fixture)
        with self.assertRaises(InvalidRecord):
            accept_packet(
                self.fixture.store, "packet-1", approved["packet"]["version"],
                "acceptance-1", "Owner", "architect-load-1", head,
                "review-integration-1", ACTOR,
            )


class CorrectedPacketAcceptanceLimitationTests(unittest.TestCase):
    """Documents a real, pre-existing M1 limitation: a corrected
    packet's own real Approve review always has correction_number=1,
    and record_and_accept_packet unconditionally requires 0. Not a bug
    in M4.09's own wiring -- this is the real store's own existing
    behavior, disclosed here rather than silently worked around."""

    def setUp(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

        target = self.fixture.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// initial attempt\n")
        self.head1 = self.fixture.repository.commit_all("initial attempt commit")

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        coverage1 = reconstruct_coverage(
            packet, repository=str(self.fixture.repository.path), head=self.head1,
            slice_id="MB-M4-09-INITIAL", reconstruction_commands=["echo reconstruct"],
        )
        finished = self.fixture.finish_succeeded(self.head1)
        integration = route_integration_validate_only(
            self.fixture.store, "packet-1", finished["packet"]["version"],
            coverage1, "attempt-1", "integration-agent-1", "review-integration-1", ACTOR,
        )
        request_changes = route_independent_implementation(
            self.fixture.store, "packet-1", integration["packet"]["version"],
            coverage1, "attempt-1", "independent-reviewer-1", "review-independent-1", ACTOR,
            result="RequestChanges", findings=[_finding()],
        )

        dispatched = self.fixture.dispatch_correction(
            "review-independent-1",
            expected_packet_version=request_changes["packet"]["version"],
        )
        self.fixture.start_execution(attempt_id="attempt-2")
        target2 = self.fixture.repository.path / "tests" / "fake" / "fixed.spec.ts"
        target2.write_text("// the real correction\n")
        head2 = self.fixture.repository.commit_all("real correction commit")
        packet2 = self.fixture.store.snapshot("Packet", "packet-1")
        coverage2 = reconstruct_coverage(
            packet2, repository=str(self.fixture.repository.path), head=head2,
            slice_id="MB-M4-09-CORRECTION", reconstruction_commands=["echo reconstruct"],
            base=self.head1,
        )
        finished2 = self.fixture.finish_succeeded(head2, attempt_id="attempt-2")
        integration2 = route_correction_review(
            self.fixture.store, "packet-1", finished2["packet"]["version"],
            coverage2, "attempt-2", "integration-agent-1", "review-integration-2",
            "Integration", "ValidateOnly", ACTOR,
        )
        self.approved = route_correction_review(
            self.fixture.store, "packet-1", integration2["packet"]["version"],
            coverage2, "attempt-2", "independent-reviewer-1", "review-independent-2",
            "IndependentImplementation", "Approve", ACTOR,
        )
        self.assertEqual(self.approved["packet"]["state"], "MergeReady")

    def tearDown(self):
        self.fixture.close()

    def test_a_corrected_packets_own_real_approve_review_cannot_be_accepted_today(self):
        with self.assertRaises(InvalidRecord):
            accept_packet(
                self.fixture.store, "packet-1", self.approved["packet"]["version"],
                "acceptance-1", "Owner", "architect-load-1", self.head1,
                "review-independent-2", ACTOR,
            )


if __name__ == "__main__":
    unittest.main()
