"""M4.11 — observe_merge, driven through a full real chain:
claim -> execute -> Integration review -> IndependentImplementation
review -> Owner acceptance (M4.09) -> real merge + observation (M4.11),
ending in a real `Merged` packet.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from m4_fixtures import ACTOR, ClaimedPacketFixture  # noqa: E402

from maestro.coverage_reconstruction import reconstruct_coverage  # noqa: E402
from maestro.merge_observation import observe_merge  # noqa: E402
from maestro.operational_state import InvalidRecord  # noqa: E402
from maestro.owner_acceptance import accept_packet  # noqa: E402
from maestro.review_dispatch import (  # noqa: E402
    route_independent_implementation,
    route_integration_validate_only,
)


def _reach_awaiting_owner(fixture: ClaimedPacketFixture) -> tuple[dict, str]:
    target = fixture.repository.path / "tests" / "fake" / "new.spec.ts"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("// a real change\n")
    head = fixture.repository.commit_all("real owned-path change")

    packet = fixture.store.snapshot("Packet", "packet-1")
    coverage = reconstruct_coverage(
        packet, repository=str(fixture.repository.path), head=head,
        slice_id="MB-M4-11-TEST", reconstruction_commands=["echo reconstruct"],
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
    accepted = accept_packet(
        fixture.store, "packet-1", approved["packet"]["version"],
        "acceptance-1", "Owner", "architect-load-1", head, "review-independent-1", ACTOR,
    )
    return accepted, head


class MergeObservationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ClaimedPacketFixture()
        self.fixture.start_execution()

    def tearDown(self):
        self.fixture.close()

    def test_a_real_accepted_packet_is_merged_and_observed(self):
        accepted, head = _reach_awaiting_owner(self.fixture)
        self.assertEqual(accepted["packet"]["state"], "AwaitingOwner")

        result = observe_merge(
            self.fixture.store, "packet-1", accepted["packet"]["version"],
            merge_observation_id="merge-observation-1",
            acceptance_id="acceptance-1",
            repository_path=str(self.fixture.repository.path),
            repository_reference="jmiedreich-ux/Foundry",
            default_branch="main",
            accepted_head=head,
            source_reference="refs/heads/codex/m4-test",
            delegation_reference="architect-load-1",
            actor=ACTOR,
        )

        self.assertEqual(result["packet"]["state"], "Merged")
        self.assertEqual(result["merge_observation"]["accepted_head"], head)
        self.assertEqual(result["merge_observation"]["performed_by_authority"], "DelegatedIdentity")
        self.assertEqual(result["merge_observation"]["delegation_reference"], "architect-load-1")

        stored = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(stored["state"], "Merged")

    def test_a_wrong_accepted_head_is_rejected_by_the_real_store(self):
        accepted, _head = _reach_awaiting_owner(self.fixture)
        with self.assertRaises(InvalidRecord):
            observe_merge(
                self.fixture.store, "packet-1", accepted["packet"]["version"],
                merge_observation_id="merge-observation-1",
                acceptance_id="acceptance-1",
                repository_path=str(self.fixture.repository.path),
                repository_reference="jmiedreich-ux/Foundry",
                default_branch="main",
                accepted_head="f" * 40,
                source_reference="refs/heads/codex/m4-test",
                delegation_reference="architect-load-1",
                actor=ACTOR,
            )


if __name__ == "__main__":
    unittest.main()
