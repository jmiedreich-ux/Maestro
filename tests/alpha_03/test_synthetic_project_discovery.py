from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig
from maestro.lifecycle import AWAITING_REVIEW, REJECTED
from maestro.packet_contract import (
    ApprovedPacket,
    PacketValidationError,
    _ALPHA03_SCENARIOS,
)
from maestro.packet_wrapper import (
    PacketWrapper,
    SyntheticLocalExecutor,
    _discovery_result,
)
from maestro.storage import SQLiteFoundation
from maestro.synthetic_discovery import (
    _DISCOVERY_FIXTURE_ROOT,
    _REQUIRED_AREAS,
    build_inventory,
    build_proposed_binding,
    build_escalation_reason,
    compute_fixture_digest,
    load_and_validate_discovery_fixture,
    validate_discovery_fixture_name,
)


FIXTURES = REPOSITORY_ROOT / "fixtures" / "alpha"
DISCOVERY_FIXTURES = _DISCOVERY_FIXTURE_ROOT


class CountingExecutor(SyntheticLocalExecutor):
    def __init__(self) -> None:
        self.executions = 0

    def execute(self, packet, worktree_path):  # type: ignore[no-untyped-def]
        self.executions += 1
        return super().execute(packet, worktree_path)


class DiscoveryFixtureNameValidationTests(unittest.TestCase):
    """Q1 — fixture name validation rejects unsafe references."""

    def test_valid_basename_passes(self) -> None:
        name = validate_discovery_fixture_name("complete-snapshot.json")
        self.assertEqual(name, "complete-snapshot.json")

    def test_empty_string_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("")

    def test_whitespace_only_rejected(self) -> none:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("   ")

    def test_none_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name(None)  # type: ignore[arg-type]

    def test_integer_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name(42)  # type: ignore[arg-type]

    def test_forwardSlash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("../sneaky.json")

    def test_backslash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("..\\sneaky.json")

    def test_absolute_path_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("/etc/passwd")

    def test_traversal_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("..filename.json")

    def test_nested_slash_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_discovery_fixture_name("sub/dir/file.json")


class DiscoveryFixtureLoadValidationTests(unittest.TestCase):
    """Q1+Q2 — fixture loading rejects malformed / unknown / wrong-typed input before claim."""

    def test_valid_complete_fixture_loads(self) -> None:
        data = load_and_validate_discovery_fixture("complete-snapshot.json")
        self.assertIsInstance(data, dict)
        for area in _REQUIRED_AREAS:
            self.assertIn(area, data)

    def test_missing_file_rejected(self) -> None:
        with self.assertRaises(ValueError):
            load_and_validate_discovery_fixture("does-not-exist.json")

    def test_malformed_json_rejected(self) -> None:
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False
        ) as tmp:
            tmp.write(b"{invalid json")
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_top_level_not_object_rejected(self) -> None:
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(["not", "an", "object"], tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_unknown_top_level_key_rejected(self) -> None:
        payload = {
            "identity": {"project_name": "x", "repository_identifier": "y", "default_branch": "z", "adapter_version": "1", "process_version": "1"},
            "unknown_area": {},
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_unknown_leaf_key_rejected(self) -> None:
        payload = {
            "identity": {
                "project_name": "x",
                "repository_identifier": "y",
                "default_branch": "z",
                "adapter_version": "1",
                "process_version": "1",
                "extra_key": "bad",
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_wrong_type_string_leaf_rejected(self) -> None:
        payload = {
            "identity": {
                "project_name": 123,
                "repository_identifier": "y",
                "default_branch": "z",
                "adapter_version": "1",
                "process_version": "1",
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_wrong_type_array_leaf_rejected(self) -> None:
        payload = {
            "authority": {
                "architecture_paths": "not-an-array",
                "plan_paths": ["a"],
                "handoff_path": "a",
                "rules_sop_path": "a",
                "task_issue_conventions": "a",
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_empty_array_entry_rejected(self) -> None:
        payload = {
            "authority": {
                "architecture_paths": [""],
                "plan_paths": ["a"],
                "handoff_path": "a",
                "rules_sop_path": "a",
                "task_issue_conventions": "a",
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_duplicate_array_entry_rejected(self) -> None:
        payload = {
            "authority": {
                "architecture_paths": ["a", "a"],
                "plan_paths": ["a"],
                "handoff_path": "a",
                "rules_sop_path": "a",
                "task_issue_conventions": "a",
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_invalid_exception_disposition_rejected(self) -> None:
        payload = {
            "exceptions": {
                "disposition": "invalid",
                "items": [],
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_disposition_none_with_items_rejected(self) -> None:
        payload = {
            "exceptions": {
                "disposition": "none",
                "items": ["something"],
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_disposition_declared_with_empty_items_rejected(self) -> None:
        payload = {
            "exceptions": {
                "disposition": "declared",
                "items": [],
            }
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_conflicts_unknown_path_rejected(self) -> None:
        payload = {
            "identity": {"project_name": "x", "repository_identifier": "y", "default_branch": "z", "adapter_version": "1", "process_version": "1"},
            "conflicts": {
                "nonexistent.leaf": ["a", "b"],
            },
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_conflicts_fewer_than_two_values_rejected(self) -> None:
        payload = {
            "identity": {"project_name": "x", "repository_identifier": "y", "default_branch": "z", "adapter_version": "1", "process_version": "1"},
            "conflicts": {
                "identity.project_name": ["only-one"],
            },
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)

    def test_conflicts_duplicate_values_rejected(self) -> None:
        payload = {
            "identity": {"project_name": "x", "repository_identifier": "y", "default_branch": "z", "adapter_version": "1", "process_version": "1"},
            "conflicts": {
                "identity.project_name": ["same", "same"],
            },
        }
        with tempfile.NamedTemporaryFile(
            dir=DISCOVERY_FIXTURES, suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump(payload, tmp)
        try:
            with self.assertRaises(ValueError):
                load_and_validate_discovery_fixture(Path(tmp.name).name)
        finally:
            os.unlink(tmp.name)


class InventoryNormalizationTests(unittest.TestCase):
    """Q2 — inventory normalization to exact required shape."""

    def test_complete_fixture_all_confirmed_reviewable_true(self) -> None:
        data = load_and_validate_discovery_fixture("complete-snapshot.json")
        inventory = build_inventory(data)
        self.assertTrue(inventory["reviewable"])
        self.assertEqual(inventory["summary"]["missing"], 0)
        self.assertEqual(inventory["summary"]["conflicting"], 0)
        total_confirmed = 0
        for area, leaves in _REQUIRED_AREAS.items():
            self.assertIn(area, inventory["areas"])
            for leaf in leaves:
                entry = inventory["areas"][area][leaf]
                self.assertEqual(entry["status"], "confirmed")
                self.assertIn("value", entry)
                self.assertNotIn("observed_values", entry)
                total_confirmed += 1
        self.assertEqual(inventory["summary"]["confirmed"], total_confirmed)

    def test_missing_area_all_leaves_missing(self) -> None:
        data = load_and_validate_discovery_fixture("missing-verification-exceptions-none.json")
        inventory = build_inventory(data)
        self.assertFalse(inventory["reviewable"])
        for leaf in _REQUIRED_AREAS["verification"]:
            entry = inventory["areas"]["verification"][leaf]
            self.assertEqual(entry["status"], "missing")
            self.assertNotIn("value", entry)

    def test_conflict_fixture_conflicting_leaves(self) -> None:
        data = load_and_validate_discovery_fixture("conflict-branches-examples.json")
        inventory = build_inventory(data)
        self.assertFalse(inventory["reviewable"])
        conflict_entry = inventory["areas"]["identity"]["default_branch"]
        self.assertEqual(conflict_entry["status"], "conflicting")
        self.assertEqual(conflict_entry["observed_values"], ["main", "develop"])
        exc_conflict = inventory["areas"]["exceptions"]["items"]
        self.assertEqual(exc_conflict["status"], "conflicting")
        self.assertEqual(
            exc_conflict["observed_values"],
            [["custom-approval-flow"], ["custom-approval-flow", "ci-skip-weekends"]],
        )

    def test_proposed_binding_only_when_reviewable(self) -> None:
        complete_data = load_and_validate_discovery_fixture("complete-snapshot.json")
        binding = build_proposed_binding(complete_data)
        self.assertIsNotNone(binding)
        self.assertEqual(set(binding.keys()), set(_REQUIRED_AREAS.keys()))
        self.assertNotIn("conflicts", binding)

        missing_data = load_and_validate_discovery_fixture("missing-verification-exceptions-none.json")
        binding = build_proposed_binding(missing_data)
        self.assertIsNone(binding)

        conflict_data = load_and_validate_discovery_fixture("conflict-branches-examples.json")
        binding = build_proposed_binding(conflict_data)
        self.assertIsNone(binding)

    def test_escalation_reason_none_when_reviewable(self) -> None:
        data = load_and_validate_discovery_fixture("complete-snapshot.json")
        reason = build_escalation_reason(data)
        self.assertIsNone(reason)

    def test_escalation_reason_names_missing_conflicting_paths(self) -> None:
        data = load_and_validate_discovery_fixture("missing-verification-exceptions-none.json")
        reason = build_escalation_reason(data)
        self.assertIsNotNone(reason)
        self.assertIn("verification.build_commands", reason)
        self.assertIn("verification.test_commands", reason)

    def test_fixture_digest_is_sha256(self) -> None:
        digest = compute_fixture_digest("complete-snapshot.json")
        self.assertEqual(len(digest), 64)
        int(digest, 16)


class PacketWrapperDiscoveryTests(unittest.TestCase):
    """Q2+Q3 — full wrapper lifecycle for discovery packets."""

    def setUp(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary_runtime = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary_runtime.name) / "runtime"

    def tearDown(self) -> None:
        self._temporary_runtime.cleanup()

    def wrapper(self, executor=None) -> PacketWrapper:
        return PacketWrapper(RuntimeConfig(self.runtime_dir), executor)

    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def snapshot(self, packet_id: str) -> dict:
        snap = SQLiteFoundation(RuntimeConfig(self.runtime_dir)).packet_snapshot(packet_id)
        self.assertIsNotNone(snap)
        return snap  # type: ignore[return-value]

    def test_complete_discovery_awaits_review_with_evidence(self) -> None:
        executor = CountingExecutor()
        result = self.wrapper(executor).run(self.fixture("alpha-03-complete-discovery-packet.json"))
        self.assertEqual(result.status, AWAITING_REVIEW)
        self.assertEqual(result.handoff_kind, "IndependentReview")
        self.assertTrue(result.launched)
        self.assertEqual(executor.executions, 1)

        snap = self.snapshot("alpha-03-complete-discovery")
        self.assertEqual(snap["status"], AWAITING_REVIEW)
        worker = snap["evidence"]["worker_result"]
        inv = worker["inventory"]
        self.assertTrue(inv["reviewable"])
        self.assertEqual(inv["summary"]["missing"], 0)
        self.assertEqual(inv["summary"]["conflicting"], 0)
        self.assertIn("proposed_binding", worker)
        self.assertIn("fixture_digest", worker)
        self.assertEqual(len(worker["fixture_digest"]), 64)

    def test_missing_facts_discovery_escalates(self) -> None:
        executor = CountingExecutor()
        result = self.wrapper(executor).run(self.fixture("alpha-03-missing-verification-packet.json"))
        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.handoff_kind, "CoordinatorEscalation")
        self.assertTrue(result.launched)

        snap = self.snapshot("alpha-03-missing-verification")
        self.assertEqual(snap["status"], REJECTED)
        handoff = snap["handoffs"][0]
        self.assertEqual(handoff["kind"], "CoordinatorEscalation")
        self.assertIn("verification.", handoff["reason"])

    def test_conflict_discovery_escalates(self) -> None:
        executor = CountingExecutor()
        result = self.wrapper(executor).run(self.fixture("alpha-03-conflict-branches-packet.json"))
        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.handoff_kind, "CoordinatorEscalation")
        self.assertTrue(result.launched)

        snap = self.snapshot("alpha-03-conflict-branches")
        self.assertEqual(snap["status"], REJECTED)

    def test_duplicate_discovery_no_second_executor(self) -> None:
        executor = CountingExecutor()
        first = self.wrapper(executor).run(self.fixture("alpha-03-complete-discovery-packet.json"))
        first_snap = self.snapshot("alpha-03-complete-discovery")
        replay = self.wrapper(executor).run(self.fixture("alpha-03-complete-discovery-packet.json"))
        replay_snap = self.snapshot("alpha-03-complete-discovery")

        self.assertEqual(first.status, AWAITING_REVIEW)
        self.assertEqual(replay.status, AWAITING_REVIEW)
        self.assertFalse(replay.launched)
        self.assertEqual(executor.executions, 1)
        self.assertEqual(first_snap, replay_snap)

    def test_discovery_fixture_error_before_claim(self) -> None:
        """Fixture name validation failure prevents any claim or mutation."""
        bad_packet = FIXTURES / "alpha-03-traversal-fixture-packet.json"
        if not bad_packet.exists():
            with tempfile.NamedTemporaryFile(
                dir=FIXTURES, suffix=".json", delete=False, mode="w"
            ) as tmp:
                payload = {
                    "packet_id": "alpha-03-traversal-test",
                    "title": "Traversal fixture test",
                    "authority": {"approval_reference": "test", "fidelity_reference": "test"},
                    "owned_paths": ["tests/alpha_03"],
                    "gates": [{"name": "t", "command": "echo"}],
                    "executor": {"kind": "synthetic-local", "scenario": "discovery-complete"},
                    "discovery_fixture": "../bad.json",
                    "independent_review_route": "test",
                    "owner_stop_boundary": "test",
                }
                json.dump(payload, tmp)
                bad_packet = Path(tmp.name)
        try:
            with self.assertRaises(ValueError):
                self.wrapper().run(bad_packet)
            self.assertFalse(self.runtime_dir.exists())
        finally:
            if str(bad_packet).startswith(str(FIXTURES)) and not str(bad_packet.name).startswith("alpha"):
                os.unlink(bad_packet)

    def test_discovery_fixture_missing_file_rejected(self) -> None:
        """Missing fixture file rejected before claim."""
        bad_packet = FIXTURES / "alpha-03-missing-file-packet.json"
        if not bad_packet.exists():
            with tempfile.NamedTemporaryFile(
                dir=FIXTURES, suffix=".json", delete=False, mode="w"
            ) as tmp:
                payload = {
                    "packet_id": "alpha-03-missing-fixture",
                    "title": "Missing fixture test",
                    "authority": {"approval_reference": "test", "fidelity_reference": "test"},
                    "owned_paths": ["tests/alpha_03"],
                    "gates": [{"name": "t", "command": "echo"}],
                    "executor": {"kind": "synthetic-local", "scenario": "discovery-complete"},
                    "discovery_fixture": "nonexistent.json",
                    "independent_review_route": "test",
                    "owner_stop_boundary": "test",
                }
                json.dump(payload, tmp)
                bad_packet = Path(tmp.name)
        try:
            with self.assertRaises(ValueError):
                self.wrapper().run(bad_packet)
            self.assertFalse(self.runtime_dir.exists())
        finally:
            if bad_packet.exists() and not bad_packet.name.startswith("alpha-03-"):
                os.unlink(bad_packet)

    def test_discovery_disposition_none_accepted(self) -> None:
        """Fixture with exceptions disposition=none and items=[] is valid."""
        data = load_and_validate_discovery_fixture("missing-verification-exceptions-none.json")
        inventory = build_inventory(data)
        exc = inventory["areas"]["exceptions"]
        self.assertEqual(exc["disposition"]["status"], "confirmed")
        self.assertEqual(exc["items"]["status"], "confirmed")


class DiscoveryScenarioResultTests(unittest.TestCase):
    """Unit-level tests for _discovery_result."""

    def _packet(self, fixture_name: str, scenario: str = "discovery-complete") -> ApprovedPacket:
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as tmp:
            json.dump({
                "packet_id": "test-discovery",
                "title": "Test",
                "authority": {"approval_reference": "a", "fidelity_reference": "b"},
                "owned_paths": ["tests/alpha_03"],
                "gates": [{"name": "g", "command": "echo"}],
                "executor": {"kind": "synthetic-local", "scenario": scenario},
                "discovery_fixture": fixture_name,
                "independent_review_route": "r",
                "owner_stop_boundary": "s",
            }, tmp)
        try:
            return ApprovedPacket.from_file(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_complete_result_reviewable(self) -> None:
        pkt = self._packet("complete-snapshot.json")
        result = _discovery_result(pkt)
        self.assertEqual(result.exit_code, 0)
        self.assertIsNotNone(result.inventory)
        self.assertIsNotNone(result.proposed_binding)
        self.assertIsNotNone(result.fixture_digest)
        self.assertTrue(result.inventory["reviewable"])

    def test_missing_result_not_reviewable(self) -> None:
        pkt = self._packet("missing-verification-exceptions-none.json")
        result = _discovery_result(pkt)
        self.assertEqual(result.exit_code, 1)
        self.assertIsNotNone(result.inventory)
        self.assertIsNone(result.proposed_binding)
        self.assertFalse(result.inventory["reviewable"])

    def test_conflict_result_not_reviewable(self) -> None:
        pkt = self._packet("conflict-branches-examples.json")
        result = _discovery_result(pkt)
        self.assertIsNone(result.proposed_binding)
        self.assertFalse(result.inventory["reviewable"])


class DiscoveryEvidenceSQLiteTests(unittest.TestCase):
    """Q3 — discovery evidence recording is durable and idempotent."""

    def setUp(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary_runtime = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary_runtime.name) / "runtime"
        self.storage = SQLiteFoundation(RuntimeConfig(self.runtime_dir))
        self.storage.health()

    def tearDown(self) -> None:
        self._temporary_runtime.cleanup()

    def test_discovery_evidence_recorded_and_readable(self) -> None:
        pkt = "alpha-03-unique-discovery"
        inv = {"areas": {}, "summary": {"confirmed": 0, "missing": 0, "conflicting": 0}, "reviewable": True}
        binding = {"identity": {}}
        digest = "abc123"
        self.storage.claim_packet(pkt, {"test": True})
        self.storage.start_packet(pkt, "/tmp/wt", {"start": True})
        self.storage.record_discovery_evidence(pkt, inv, binding, digest)
        self.storage.finish_packet(pkt, AWAITING_REVIEW, "IndependentReview", "complete", {})

        snap = self.storage.packet_snapshot(pkt)
        self.assertIsNotNone(snap)
        self.assertEqual(snap["status"], AWAITING_REVIEW)


if __name__ == "__main__":
    unittest.main()
