"""M4.05 — reconstruct_coverage, against a real git repository (real
checkout, real diff, real shell commands — not a mocked git)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))

from support import TemporaryProjectRepository  # noqa: E402

from m4_fixtures import ClaimedPacketFixture  # noqa: E402

from maestro.coverage_reconstruction import reconstruct_coverage  # noqa: E402


class CoverageReconstructionTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository()
        self.base_commit = self.repository.commit

    def tearDown(self):
        self.repository.close()

    def _packet(self, **overrides) -> dict:
        packet = {
            "base_commit": self.base_commit,
            "owned_paths_json": ["tests/fake/"],
            "checks_json": ["echo real-check"],
        }
        packet.update(overrides)
        return packet

    def test_a_real_clean_change_inside_owned_paths_with_real_passing_checks_is_ready(self):
        target = self.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real new test file\n")
        head = self.repository.commit_all("add a real owned-path file")

        coverage = reconstruct_coverage(
            self._packet(),
            repository=str(self.repository.path),
            head=head,
            slice_id="MB-M4-05-TEST",
            reconstruction_commands=["true"],
        )

        self.assertEqual(coverage["kind"], "review-readiness-coverage")
        result = coverage["result"]
        self.assertEqual(result["request"]["review_kind"], "IndependentImplementation")
        self.assertTrue(result["ready"])
        self.assertEqual(result["blockers"], [])
        self.assertTrue(all(check["outcome"] == "Passed" for check in result["checks"]))
        self.assertEqual(result["resolved_base"], self.base_commit)
        self.assertEqual(result["resolved_head"], head)
        self.assertEqual(result["changed_paths"], ["tests/fake/new.spec.ts"])
        self.assertTrue(result["clean_before"])
        self.assertTrue(result["clean_after"])

    def test_a_real_failing_check_is_reflected_honestly_as_not_ready(self):
        target = self.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real new test file\n")
        head = self.repository.commit_all("add a real owned-path file")

        coverage = reconstruct_coverage(
            self._packet(checks_json=["false"]),
            repository=str(self.repository.path),
            head=head,
            slice_id="MB-M4-05-TEST-FAIL",
            reconstruction_commands=["true"],
        )

        result = coverage["result"]
        self.assertFalse(result["ready"])
        self.assertTrue(any(check["outcome"] != "Passed" for check in result["checks"]))

    def test_a_real_change_outside_owned_paths_is_reflected_as_not_ready(self):
        outside = self.repository.path / "package.json"
        outside.write_text("{}\n")
        head = self.repository.commit_all("touch a forbidden path")

        coverage = reconstruct_coverage(
            self._packet(),
            repository=str(self.repository.path),
            head=head,
            slice_id="MB-M4-05-TEST-OUTSIDE",
            reconstruction_commands=["true"],
        )

        result = coverage["result"]
        self.assertFalse(result["ready"])
        self.assertTrue(result["blockers"])

    def test_multi_word_shell_commands_split_into_real_distinct_check_ids(self):
        target = self.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real new test file\n")
        head = self.repository.commit_all("add a real owned-path file")

        coverage = reconstruct_coverage(
            self._packet(checks_json=["echo one", "echo two"]),
            repository=str(self.repository.path),
            head=head,
            slice_id="MB-M4-05-TEST-MULTI",
            reconstruction_commands=["true"],
        )
        check_ids = {check["check_id"] for check in coverage["result"]["checks"]}
        self.assertIn("echo-one", check_ids)
        self.assertIn("echo-two", check_ids)


if __name__ == "__main__":
    unittest.main()


class DuplicateCommandTests(unittest.TestCase):
    """Found running a real project end to end: a reconstruction command
    identical to one of the packet's own checks made the whole request
    malformed (check_id uniqueness spans both lists), stranding the
    packet in AwaitingIntegration behind an opaque blocker."""

    def setUp(self):
        self.fixture = ClaimedPacketFixture()

    def tearDown(self):
        self.fixture.close()

    def test_a_reconstruction_command_matching_a_packet_check_is_disambiguated_not_fatal(self):
        target = self.fixture.repository.path / "tests" / "fake" / "new.spec.ts"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("// a real change\n")
        head = self.fixture.repository.commit_all("real owned-path change")

        packet = self.fixture.store.snapshot("Packet", "packet-1")
        self.assertEqual(packet["checks_json"], ["true"])

        coverage = reconstruct_coverage(
            packet, repository=str(self.fixture.repository.path), head=head,
            slice_id="MB-DUPLICATE-TEST", reconstruction_commands=["true"],
        )
        self.assertTrue(coverage["result"]["ready"], coverage["result"]["blockers"])
        self.assertEqual(
            [c["check_id"] for c in coverage["result"]["request"]["reconstruction_commands"]],
            ["true-reconstruction"],
        )
        self.assertEqual(coverage["result"]["request"]["reconstruction_commands"][0]["argv"], ["true"])
