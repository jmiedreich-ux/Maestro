from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig
from maestro.lifecycle import AWAITING_REVIEW, CORRECTION_ELIGIBLE, REJECTED
from maestro.packet_contract import PacketValidationError
from maestro.packet_wrapper import PacketWrapper, SyntheticLocalExecutor
from maestro.storage import SQLiteFoundation


FIXTURES = REPOSITORY_ROOT / "fixtures" / "alpha"


class CountingExecutor(SyntheticLocalExecutor):
    def __init__(self) -> None:
        self.executions = 0

    def execute(self, packet, worktree_path):  # type: ignore[no-untyped-def]
        self.executions += 1
        return super().execute(packet, worktree_path)


class RunPacketWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary_runtime = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary_runtime.name) / "runtime"

    def tearDown(self) -> None:
        self._temporary_runtime.cleanup()

    def wrapper(self, executor: SyntheticLocalExecutor | None = None) -> PacketWrapper:
        return PacketWrapper(RuntimeConfig(self.runtime_dir), executor)

    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def snapshot(self, packet_id: str) -> dict[str, object]:
        snapshot = SQLiteFoundation(RuntimeConfig(self.runtime_dir)).packet_snapshot(packet_id)
        self.assertIsNotNone(snapshot)
        return snapshot  # type: ignore[return-value]

    def test_valid_packet_records_review_handoff_and_stops(self) -> None:
        executor = CountingExecutor()
        result = self.wrapper(executor).run(self.fixture("approved-success-packet.json"))

        self.assertEqual(result.status, AWAITING_REVIEW)
        self.assertEqual(result.handoff_kind, "IndependentReview")
        self.assertTrue(result.launched)
        self.assertEqual(executor.executions, 1)
        self.assertTrue(Path(result.worktree_path or "").is_dir())
        self.assertTrue(str(result.worktree_path).startswith(str(self.runtime_dir)))

        snapshot = self.snapshot("alpha-02-success")
        self.assertEqual(snapshot["status"], AWAITING_REVIEW)
        self.assertEqual(snapshot["handoffs"], [{"kind": "IndependentReview", "reason": "valid result awaits independent review"}])
        evidence = snapshot["evidence"]  # type: ignore[assignment]
        self.assertEqual(evidence["worker_result"]["commit"], "synthetic-commit-alpha-02")  # type: ignore[index]
        self.assertEqual(evidence["worker_result"]["scoped_diff"], ["synthetic-output/result.txt"])  # type: ignore[index]
        self.assertEqual(evidence["worker_result"]["gate_results"], {"synthetic-check": True})  # type: ignore[index]

    def test_duplicate_and_restart_do_not_launch_a_second_worker_or_overwrite_evidence(self) -> None:
        executor = CountingExecutor()
        first = self.wrapper(executor).run(self.fixture("approved-success-packet.json"))
        before = self.snapshot("alpha-02-success")
        replay = self.wrapper(executor).run(self.fixture("approved-success-packet.json"))
        after = self.snapshot("alpha-02-success")

        self.assertEqual(first.status, AWAITING_REVIEW)
        self.assertEqual(replay.status, AWAITING_REVIEW)
        self.assertFalse(replay.launched)
        self.assertEqual(executor.executions, 1)
        self.assertEqual(before, after)

    def test_competing_claim_does_not_launch_a_worker_or_create_a_worktree(self) -> None:
        packet_id = "alpha-02-success"
        storage = SQLiteFoundation(RuntimeConfig(self.runtime_dir))
        initial = storage.claim_packet(packet_id, {"fixture": True})
        executor = CountingExecutor()
        result = self.wrapper(executor).run(self.fixture("approved-success-packet.json"))

        self.assertTrue(initial.claimed)
        self.assertEqual(result.status, "Claimed")
        self.assertFalse(result.launched)
        self.assertEqual(executor.executions, 0)
        self.assertFalse((self.runtime_dir / "packet-worktrees").exists())

    def test_m0_d05_non_delivery_and_scope_violations_escalate_without_correction(self) -> None:
        fixtures = {
            "missing-commit-packet.json": "alpha-02-missing-commit",
            "missing-diff-packet.json": "alpha-02-missing-diff",
            "out-of-scope-packet.json": "alpha-02-out-of-scope",
            "dependency-violation-packet.json": "alpha-02-dependency-violation",
            "configuration-violation-packet.json": "alpha-02-configuration-violation",
            "placeholder-violation-packet.json": "alpha-02-placeholder-violation",
        }
        for fixture_name, packet_id in fixtures.items():
            with self.subTest(fixture=fixture_name):
                result = self.wrapper().run(self.fixture(fixture_name))
                snapshot = self.snapshot(packet_id)
                self.assertEqual(result.status, REJECTED)
                self.assertEqual(result.handoff_kind, "CoordinatorEscalation")
                self.assertEqual(snapshot["status"], REJECTED)
                self.assertEqual(len(snapshot["handoffs"]), 1)  # type: ignore[arg-type]
                self.assertEqual(snapshot["handoffs"][0]["kind"], "CoordinatorEscalation")  # type: ignore[index]

    def test_only_one_named_gate_failure_is_eligible_for_targeted_correction(self) -> None:
        executor = CountingExecutor()
        result = self.wrapper(executor).run(self.fixture("gate-failure-packet.json"))
        replay = self.wrapper(executor).run(self.fixture("gate-failure-packet.json"))
        snapshot = self.snapshot("alpha-02-gate-failure")

        self.assertEqual(result.status, CORRECTION_ELIGIBLE)
        self.assertEqual(result.handoff_kind, "TargetedCorrection")
        self.assertFalse(replay.launched)
        self.assertEqual(executor.executions, 1)
        self.assertEqual(snapshot["handoffs"][0]["kind"], "TargetedCorrection")  # type: ignore[index]
        self.assertIn("named gate failed: synthetic-check", snapshot["handoffs"][0]["reason"])  # type: ignore[index]

    def test_packet_validation_rejects_every_required_authority_field_before_mutation(self) -> None:
        valid_payload = json.loads(self.fixture("approved-success-packet.json").read_text(encoding="utf-8"))
        invalid_payloads = []
        for field in ("packet_id", "title", "owned_paths", "gates", "independent_review_route", "owner_stop_boundary"):
            payload = json.loads(json.dumps(valid_payload))
            payload.pop(field)
            invalid_payloads.append(payload)
        for authority_field in ("approval_reference", "fidelity_reference"):
            payload = json.loads(json.dumps(valid_payload))
            payload["authority"].pop(authority_field)
            invalid_payloads.append(payload)
        for executor_field, value in (
            ("kind", None),
            ("kind", "real-agent"),
            ("scenario", None),
            ("scenario", "unknown-synthetic-case"),
        ):
            payload = json.loads(json.dumps(valid_payload))
            if value is None:
                payload["executor"].pop(executor_field)
            else:
                payload["executor"][executor_field] = value
            invalid_payloads.append(payload)

        with tempfile.TemporaryDirectory() as packet_directory:
            packet_path = Path(packet_directory) / "invalid.json"
            for payload in invalid_payloads:
                with self.subTest(payload=payload):
                    packet_path.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaises(PacketValidationError):
                        self.wrapper().run(packet_path)
                    self.assertFalse(self.runtime_dir.exists())

    def test_cli_run_packet_reports_awaiting_review(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "maestro.cli",
                "run-packet",
                "--packet",
                str(self.fixture("approved-success-packet.json")),
                "--runtime-dir",
                str(self.runtime_dir),
            ],
            cwd=REPOSITORY_ROOT / "services" / "maestro",
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["status"], AWAITING_REVIEW)
        self.assertEqual(output["handoff_kind"], "IndependentReview")


if __name__ == "__main__":
    unittest.main()
