"""M4.08 — route_correction_review, driven through a real full
correction cycle: Initial attempt -> RequestChanges -> real
record_and_dispatch_correction -> a real second (TargetedCorrection)
attempt -> a real MergeReady packet.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.coverage_reconstruction import reconstruct_coverage  # noqa: E402
from maestro.review_dispatch import (  # noqa: E402
    route_correction_review,
    route_independent_implementation,
    route_integration_validate_only,
)


def _finding() -> dict:
    return {
        "kind": "review-finding",
        "finding_id": "DF-01",
        "criterion_reference": "M4.08-TEST#owned-path",
        "evidence": {
            "kind": "evidence-reference",
            "evidence_id": "evidence-1",
            "digest": hashlib.sha256(b"real finding evidence").hexdigest(),
            "source_reference": None,
        },
        "disposition": {"kind": "reason", "reason_code": "CorrectNow", "detail_reference": None},
    }


class CorrectionReviewTests(unittest.TestCase):
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
            slice_id="MB-M4-08-INITIAL", reconstruction_commands=["echo reconstruct"],
        )
        self.assertTrue(coverage1["result"]["ready"], coverage1["result"]["blockers"])

        finished = self.fixture.finish_succeeded(self.head1)
        self.assertEqual(finished["packet"]["state"], "AwaitingIntegration")

        integration = route_integration_validate_only(
            self.fixture.store, "packet-1", finished["packet"]["version"],
            coverage1, "attempt-1", "integration-agent-1", "review-integration-1", ACTOR,
        )
        self.assertEqual(integration["packet"]["state"], "AwaitingReview")

        request_changes = route_independent_implementation(
            self.fixture.store, "packet-1", integration["packet"]["version"],
            coverage1, "attempt-1", "independent-reviewer-1", "review-independent-1", ACTOR,
            result="RequestChanges", findings=[_finding()],
        )
        self.assertEqual(request_changes["packet"]["state"], "AwaitingArchitect")
        self.review_id = "review-independent-1"
        self.after_request_changes_version = request_changes["packet"]["version"]

    def tearDown(self):
        self.fixture.close()

    def test_a_real_correction_cycle_reaches_merge_ready(self):
        dispatched = self.fixture.dispatch_correction(
            self.review_id, expected_packet_version=self.after_request_changes_version,
        )
        self.assertEqual(dispatched["packet"]["state"], "Leased")

        self.fixture.start_execution(attempt_id="attempt-2")
        target = self.fixture.repository.path / "tests" / "fake" / "fixed.spec.ts"
        target.write_text("// the real correction\n")
        head2 = self.fixture.repository.commit_all("real correction commit")

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        coverage2 = reconstruct_coverage(
            packet, repository=str(self.fixture.repository.path), head=head2,
            slice_id="MB-M4-08-CORRECTION", reconstruction_commands=["echo reconstruct"],
            base=self.head1,
        )
        self.assertTrue(coverage2["result"]["ready"], coverage2["result"]["blockers"])

        finished2 = self.fixture.finish_succeeded(head2, attempt_id="attempt-2")
        self.assertEqual(finished2["packet"]["state"], "AwaitingIntegration")

        integration2 = route_correction_review(
            self.fixture.store, "packet-1", finished2["packet"]["version"],
            coverage2, "attempt-2", "integration-agent-1", "review-integration-2",
            "Integration", "ValidateOnly", ACTOR,
        )
        self.assertEqual(integration2["packet"]["state"], "AwaitingReview")

        approved = route_correction_review(
            self.fixture.store, "packet-1", integration2["packet"]["version"],
            coverage2, "attempt-2", "independent-reviewer-1", "review-independent-2",
            "IndependentImplementation", "Approve", ACTOR,
        )
        self.assertEqual(approved["packet"]["state"], "MergeReady")


if __name__ == "__main__":
    unittest.main()
