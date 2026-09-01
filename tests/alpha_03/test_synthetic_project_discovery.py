"""Tests for synthetic_discovery module (Alpha-03)."""
import copy
import hashlib
import json
import os
import pathlib
import tempfile
import unittest

import maestro.synthetic_discovery
from maestro.synthetic_discovery import (
    AREAS,
    AUTHORITY_LEAVES,
    DELIVERY_LEAVES,
    EXCEPTIONS_LEAVES,
    IDENTITY_LEAVES,
    OPERATIONS_LEAVES,
    ROLES_LEAVES,
    VERIFICATION_LEAVES,
    DiscoveryValidationError,
    discover,
    propose_binding,
    proposed_binding_json,
    as_json,
    load_discovery_fixture,
    sha256_digest,
)

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURES = REPOSITORY_ROOT / "fixtures" / "alpha" / "project-discovery"


def _load(name: str) -> dict:
    with open(FIXTURES / name) as f:
        return json.load(f)


class TestCompleteDiscovery(unittest.TestCase):

    def setUp(self):
        self.raw = _load("complete-snapshot.json")
        self.result = discover(self.raw)

    def test_seven_areas(self):
        self.assertEqual(sorted(self.result["areas"].keys()),
                         sorted(area for area, _ in AREAS))

    def test_29_confirmed_leaves(self):
        s = self.result["summary"]
        self.assertEqual(s["confirmed"], 29)
        self.assertEqual(s["missing"], 0)
        self.assertEqual(s["conflicting"], 0)

    def test_reviewable_true(self):
        self.assertTrue(self.result["reviewable"])

    def test_propose_binding_values(self):
        binding = propose_binding(self.result)
        area_leaves = {
            "identity": IDENTITY_LEAVES, "authority": AUTHORITY_LEAVES,
            "delivery": DELIVERY_LEAVES, "verification": VERIFICATION_LEAVES,
            "roles": ROLES_LEAVES, "operations": OPERATIONS_LEAVES,
            "exceptions": EXCEPTIONS_LEAVES,
        }
        for area_name, leaves in AREAS:
            for leaf, _ in leaves:
                raw_val = self.raw[area_name].get(leaf)
                if isinstance(raw_val, list):
                    raw_val = [v.strip() for v in raw_val]
                elif isinstance(raw_val, str):
                    raw_val = raw_val.strip()
                self.assertEqual(binding[area_name][leaf], raw_val)

    def test_canonical_json_format(self):
        binding = propose_binding(self.result)
        canonical = proposed_binding_json(self.result)
        expected = json.dumps(binding, sort_keys=True, separators=(",", ":"))
        self.assertEqual(canonical, expected)

    def test_sha256_digest(self):
        raw_bytes = proposed_binding_json(self.result).encode("utf-8")
        digest = sha256_digest(raw_bytes)
        expected = hashlib.sha256(raw_bytes).hexdigest()
        self.assertEqual(digest, expected)


class TestRemoveEachLeaf(unittest.TestCase):
    """Deep-copy complete snapshot, remove one leaf, verify summary."""

    def run_one_removal(self, area: str, leaf: str):
        raw = copy.deepcopy(_load("complete-snapshot.json"))
        if area in raw and leaf in raw[area]:
            del raw[area][leaf]
        result = discover(raw)
        s = result["summary"]
        self.assertEqual(s["confirmed"], 28)
        self.assertEqual(s["missing"], 1)
        self.assertEqual(s["conflicting"], 0)
        self.assertFalse(result["reviewable"])
        with self.assertRaises(DiscoveryValidationError):
            propose_binding(result)

    def test_identity(self):
        for l, _ in IDENTITY_LEAVES:
            self.run_one_removal("identity", l)

    def test_authority(self):
        for l, _ in AUTHORITY_LEAVES:
            self.run_one_removal("authority", l)

    def test_delivery(self):
        for l, _ in DELIVERY_LEAVES:
            self.run_one_removal("delivery", l)

    def test_verification(self):
        for l, _ in VERIFICATION_LEAVES:
            self.run_one_removal("verification", l)

    def test_roles(self):
        for l, _ in ROLES_LEAVES:
            self.run_one_removal("roles", l)

    def test_operations(self):
        for l, _ in OPERATIONS_LEAVES:
            self.run_one_removal("operations", l)

    def test_exceptions(self):
        for l, _ in EXCEPTIONS_LEAVES:
            self.run_one_removal("exceptions", l)


class TestMissingAndConflictFixtures(unittest.TestCase):

    def test_missing_verification_summary(self):
        raw = _load("missing-verification-exceptions-none.json")
        result = discover(raw)
        s = result["summary"]
        self.assertEqual(s["confirmed"], 23)
        self.assertEqual(s["missing"], 6)
        self.assertEqual(s["conflicting"], 0)
        self.assertFalse(result["reviewable"])

    def test_missing_verification_paths(self):
        raw = _load("missing-verification-exceptions-none.json")
        result = discover(raw)
        for leaf, _ in VERIFICATION_LEAVES:
            self.assertEqual(result["areas"]["verification"][leaf]["status"], "missing")

    def test_conflict_fixtures_summary(self):
        raw = _load("conflict-branches-examples.json")
        result = discover(raw)
        s = result["summary"]
        # 2 conflicted leaves: identity.default_branch + exceptions.items
        self.assertEqual(s["conflicting"], 2)
        self.assertEqual(s["confirmed"], 27)
        self.assertEqual(s["missing"], 0)

    def test_conflict_observed_values_preserved(self):
        raw = _load("conflict-branches-examples.json")
        result = discover(raw)
        entry = result["areas"]["identity"]["default_branch"]
        self.assertEqual(entry["status"], "conflicting")
        self.assertIn("observed_values", entry)
        self.assertEqual(entry["observed_values"], ["main", "trunk"])

    def test_conflict_proposals_raise(self):
        raw = _load("conflict-branches-examples.json")
        result = discover(raw)
        with self.assertRaises(DiscoveryValidationError):
            propose_binding(result)


class TestExceptionsValidation(unittest.TestCase):

    def _base(self, disposition: str, items: list[str]) -> dict:
        return {
            "identity": {"project_name": "x", "repository_identifier": "y",
                         "default_branch": "main", "adapter_version": "1",
                         "process_version": "v"},
            "authority": {"architecture_paths": ["a"], "plan_paths": ["b"],
                          "handoff_path": "c", "rules_sop_path": "d",
                          "task_issue_conventions": "e"},
            "delivery": {"branch_pr_merge_policy": "f",
                         "owner_acceptance_policy": "g",
                         "deployment_rollback_policy": "h"},
            "verification": {"build_commands": ["i"], "test_commands": ["j"],
                             "integration_commands": ["k"], "ui_qa_commands": [],
                             "evidence_rules": "l", "untested_handling": "m"},
            "roles": {"specialist_overlays": [], "reviewer_route": "n",
                      "qa_murphy_policy": "o", "local_cloud_eligibility": "p"},
            "operations": {"environment_reference_names": ["dev"],
                           "secret_reference_names": [],
                           "resource_locks": [], "notification_policy": "q"},
            "exceptions": {"disposition": disposition, "items": items},
        }

    def test_none_empty_confirms(self):
        result = discover(self._base("none", []))
        self.assertTrue(result["reviewable"])
        self.assertEqual(result["summary"]["confirmed"], 29)

    def test_declared_nonempty_confirms(self):
        result = discover(self._base("declared", ["risky thing"]))
        self.assertTrue(result["reviewable"])
        self.assertEqual(result["summary"]["confirmed"], 29)

    def test_none_with_items_raises(self):
        with self.assertRaises(DiscoveryValidationError):
            discover(self._base("none", ["something"]))

    def test_declared_empty_raises(self):
        with self.assertRaises(DiscoveryValidationError):
            discover(self._base("declared", []))


# ---------------------------------------------------------------------------
# Malformed schema tests
# ---------------------------------------------------------------------------

class TestMalformedSchema(unittest.TestCase):
    """Feed deliberately broken snapshots into discover() and expect
    DiscoveryValidationError on every case."""

    def _full(self) -> dict:
        return _load("complete-snapshot.json")

    # --- unknown top-level keys ---

    def test_unknown_top_level_key(self):
        snap = self._full()
        snap["bogus_section"] = {}
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- unknown leaf keys ---

    def test_unknown_leaf_key(self):
        snap = self._full()
        snap["identity"]["fake_leaf"] = "x"
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- explicit null area ---

    def test_null_area(self):
        snap = self._full()
        snap["identity"] = None
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- wrong-typed area (non-dict, non-None) ---

    def test_wrong_typed_area(self):
        snap = self._full()
        snap["delivery"] = "not a dict"
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- wrong string value (integer instead) ---

    def test_wrong_string_leaf_value_integer(self):
        snap = self._full()
        snap["identity"]["project_name"] = 42
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- wrong array value (string instead) ---

    def test_wrong_array_leaf_value_string(self):
        snap = self._full()
        snap["authority"]["architecture_paths"] = "not a list"
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- authority empty required arrays ---

    def test_authority_architecture_paths_empty(self):
        snap = self._full()
        snap["authority"]["architecture_paths"] = []
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    def test_authority_plan_paths_empty(self):
        snap = self._full()
        snap["authority"]["plan_paths"] = []
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- blank array items ---

    def test_blank_array_item(self):
        snap = self._full()
        snap["authority"]["architecture_paths"] = ["  "]
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- duplicate array items ---

    def test_duplicate_array_item(self):
        snap = self._full()
        snap["authority"]["architecture_paths"] = ["a", "a"]
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- invalid exception disposition ---

    def test_invalid_exception_disposition(self):
        snap = self._full()
        snap["exceptions"]["disposition"] = "wrong_value"
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- invalid disposition/items combination (already covered by
    # TestExceptionsValidation but add disposition=none + items here
    # for coverage completeness within MalformedSchema) ---

    def test_exception_disposition_none_with_items(self):
        snap = self._full()
        snap["exceptions"]["disposition"] = "none"
        snap["exceptions"]["items"] = ["something"]
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- conflicts: unknown path ---

    def test_conflicts_unknown_path(self):
        snap = self._full()
        snap["conflicts"] = {"identity.nonexistent": ["a", "b"]}
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- conflicts: fewer than two candidates ---

    def test_conflicts_single_candidate(self):
        snap = self._full()
        snap["conflicts"] = {"identity.default_branch": ["main"]}
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- conflicts: duplicate candidates ---

    def test_conflicts_duplicate_candidates(self):
        snap = self._full()
        snap["conflicts"] = {"identity.default_branch": ["main", "main"]}
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- conflicts: wrong scalar candidate type (string leaf gets integer) ---

    def test_conflicts_wrong_scalar_candidate_type(self):
        snap = self._full()
        snap["conflicts"] = {"identity.default_branch": ["main", 42]}
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)

    # --- conflicts: wrong array candidate type (array leaf gets scalar) ---

    def test_conflicts_wrong_array_candidate_type(self):
        snap = self._full()
        snap["conflicts"] = {
            "verification.build_commands": [
                ["pip install"],
                "not an array",
            ]
        }
        with self.assertRaises(DiscoveryValidationError):
            discover(snap)


# ---------------------------------------------------------------------------
# Loader confinement tests
# ---------------------------------------------------------------------------

class TestLoaderConfinement(unittest.TestCase):
    """Patch DISCOVERY_FIXTURE_ROOT to a TemporaryDirectory and exercise
    load_discovery_fixture() with both valid and hostile inputs."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self._original = maestro.synthetic_discovery.DISCOVERY_FIXTURE_ROOT
        maestro.synthetic_discovery.DISCOVERY_FIXTURE_ROOT = self.root

    def tearDown(self):
        maestro.synthetic_discovery.DISCOVERY_FIXTURE_ROOT = self._original
        self.tmp.cleanup()

    def _write(self, name: str, content) -> pathlib.Path:
        p = self.root / name
        if isinstance(content, str):
            content = content.encode("utf-8")
        p.write_bytes(content)
        return p

    # --- happy path ---

    def test_valid_load_and_digest(self):
        snap = {
            "identity": {"project_name": "x", "repository_identifier": "y",
                         "default_branch": "main", "adapter_version": "1",
                         "process_version": "v"},
            "authority": {"architecture_paths": ["a"], "plan_paths": ["b"],
                          "handoff_path": "c", "rules_sop_path": "d",
                          "task_issue_conventions": "e"},
            "delivery": {"branch_pr_merge_policy": "f",
                         "owner_acceptance_policy": "g",
                         "deployment_rollback_policy": "h"},
            "verification": {"build_commands": ["i"], "test_commands": ["j"],
                             "integration_commands": ["k"], "ui_qa_commands": [],
                             "evidence_rules": "l", "untested_handling": "m"},
            "roles": {"specialist_overlays": [], "reviewer_route": "n",
                      "qa_murphy_policy": "o", "local_cloud_eligibility": "p"},
            "operations": {"environment_reference_names": ["dev"],
                           "secret_reference_names": [],
                           "resource_locks": [], "notification_policy": "q"},
            "exceptions": {"disposition": "none", "items": []},
        }
        json_bytes = json.dumps(snap).encode("utf-8")
        self._write("ok.json", json_bytes)
        loaded = load_discovery_fixture("ok.json")
        self.assertEqual(loaded.filename, "ok.json")
        self.assertEqual(loaded.fixture_digest, hashlib.sha256(json_bytes).hexdigest())
        self.assertTrue(loaded.inventory["reviewable"])

    # --- malformed JSON ---

    def test_malformed_json(self):
        self._write("bad.json", b"{not-json}")
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("bad.json")

    # --- missing file ---

    def test_missing_file(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("no-such.json")

    # --- empty name ---

    def test_empty_name(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("   ")

    # --- absolute path ---

    def test_absolute_path(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("/etc/passwd.json")

    # --- traversal ---

    def test_traversal(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("../foo.json")

    # --- forward slash in name ---

    def test_forward_slash(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("sub/dir.json")

    # --- backslash in name ---

    def test_backslash(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("sub\\dir.json")

    # --- non-json filename ---

    def test_non_json_extension(self):
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("data.txt")

    # --- symlink inside root that resolves outside ---

    def test_symlink_escape(self):
        outside = pathlib.Path(self.tmp.name + "_outside")
        outside.mkdir()
        outside_file = outside / "secret.json"
        outside_file.write_text(json.dumps({"a": 1}))
        link = self.root / "escape.json"
        link.symlink_to(outside_file)
        with self.assertRaises(DiscoveryValidationError):
            load_discovery_fixture("escape.json")


class TestPacketWrapperDiscovery(unittest.TestCase):
    """End-to-end PacketWrapper tests for the three Alpha-03 discovery packets."""

    @classmethod
    def setUpClass(cls):
        from maestro.config import DEFAULT_RUNTIME_DIR
        import tempfile
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        cls._runtime_dir = DEFAULT_RUNTIME_DIR
        cls._tmp = tempfile.TemporaryDirectory(dir=str(DEFAULT_RUNTIME_DIR))
        cls._runtime = pathlib.Path(cls._tmp.name) / "runtime"

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def _wrapper(self):
        from maestro.config import RuntimeConfig
        from maestro.packet_wrapper import PacketWrapper
        return PacketWrapper(RuntimeConfig(self._runtime))

    # --- complete packet ---

    def test_complete_packet_status_and_evidence(self):
        from maestro.packet_wrapper import PacketWrapper
        from maestro.config import RuntimeConfig
        wrapper = PacketWrapper(RuntimeConfig(self._runtime))
        result = wrapper.run(FIXTURES.parent / "alpha-03-complete-discovery-packet.json")
        self.assertEqual(result.status, "AwaitingReview")
        self.assertEqual(result.handoff_kind, "IndependentReview")
        self.assertTrue(result.launched)
        self.assertIsNone(result.worktree_path)

        snapshot = wrapper.storage.packet_snapshot(result.packet_id)
        # Evidence keys
        self.assertEqual(
            sorted(snapshot["evidence"].keys()),
            ["fixture_digest", "inventory", "proposed_binding"],
        )
        # Summary counts
        inv = snapshot["evidence"]["inventory"]
        self.assertEqual(inv["summary"]["confirmed"], 29)
        self.assertEqual(inv["summary"]["missing"], 0)
        self.assertEqual(inv["summary"]["conflicting"], 0)
        # 7 binding areas
        binding = snapshot["evidence"]["proposed_binding"]
        self.assertEqual(sorted(binding.keys()), sorted(area for area, _ in AREAS))
        # Digest matches complete raw file bytes SHA-256
        raw_bytes = (FIXTURES / "complete-snapshot.json").read_bytes()
        expected_digest = hashlib.sha256(raw_bytes).hexdigest()
        self.assertEqual(
            snapshot["evidence"]["fixture_digest"]["sha256"],
            expected_digest,
        )
        # One handoff
        self.assertEqual(len(snapshot["handoffs"]), 1)
        self.assertEqual(snapshot["handoffs"][0]["kind"], "IndependentReview")

    # --- missing packet ---

    def test_missing_packet_rejected(self):
        from maestro.packet_wrapper import PacketWrapper
        from maestro.config import RuntimeConfig
        wrapper = PacketWrapper(RuntimeConfig(self._runtime))
        result = wrapper.run(FIXTURES.parent / "alpha-03-missing-verification-packet.json")
        self.assertEqual(result.status, "Rejected")
        self.assertEqual(result.handoff_kind, "CoordinatorEscalation")

        snapshot = wrapper.storage.packet_snapshot(result.packet_id)
        self.assertNotIn("proposed_binding", snapshot["evidence"])
        # Reason contains missing paths
        handoff = snapshot["handoffs"][0]
        reason = handoff["reason"]
        for leaf, _ in VERIFICATION_LEAVES:
            self.assertIn(f"verification.{leaf}", reason)

    # --- conflict packet ---

    def test_conflict_packet_rejected(self):
        from maestro.packet_wrapper import PacketWrapper
        from maestro.config import RuntimeConfig
        wrapper = PacketWrapper(RuntimeConfig(self._runtime))
        result = wrapper.run(FIXTURES.parent / "alpha-03-conflict-branches-packet.json")
        self.assertEqual(result.status, "Rejected")
        self.assertEqual(result.handoff_kind, "CoordinatorEscalation")

        snapshot = wrapper.storage.packet_snapshot(result.packet_id)
        self.assertNotIn("proposed_binding", snapshot["evidence"])
        # Reason contains conflicting paths
        handoff = snapshot["handoffs"][0]
        reason = handoff["reason"]
        self.assertIn("identity.default_branch", reason)
        self.assertIn("exceptions.items", reason)

    # --- replay: fresh wrapper reads unchanged snapshot ---

    def test_replay_fresh_wrapper_snapshot_unchanged(self):
        from maestro.packet_wrapper import PacketWrapper
        from maestro.config import RuntimeConfig
        # Run the complete packet
        w1 = self._wrapper()
        r1 = w1.run(FIXTURES.parent / "alpha-03-complete-discovery-packet.json")
        snapshot_1 = w1.storage.packet_snapshot(r1.packet_id)

        # Replay with a fresh wrapper
        w2 = self._wrapper()
        r2 = w2.run(FIXTURES.parent / "alpha-03-complete-discovery-packet.json")
        self.assertFalse(r2.launched)
        snapshot_2 = w2.storage.packet_snapshot(r2.packet_id)

        # Evidence keys and values identical
        self.assertEqual(
            sorted(snapshot_2["evidence"].keys()),
            ["fixture_digest", "inventory", "proposed_binding"],
        )
        self.assertEqual(snapshot_2["evidence"]["inventory"], snapshot_1["evidence"]["inventory"])


# ---------------------------------------------------------------------------
# Preclaim and fixture-contention tests
# ---------------------------------------------------------------------------

class TestDiscoveryPreclaimAndContention(unittest.TestCase):
    """Test that a prior SQLite claim blocks execution, and that hostile
    discovery_fixture values raise before any worktree or executor runs."""

    # -- Test 1: hostile discovery_fixture values via temp packet JSONs --

    def test_hostile_fixture_values(self):
        import copy
        import tempfile
        import unittest.mock
        from maestro.synthetic_discovery import (
            DISCOVERY_FIXTURE_ROOT,
            DiscoveryError,
        )
        from maestro.packet_wrapper import PacketWrapper, SyntheticLocalExecutor
        from maestro.config import RuntimeConfig, DEFAULT_RUNTIME_DIR
        from maestro.synthetic_discovery import load_discovery_fixture

        base_raw = _load("complete-snapshot.json")

        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        runtime_tmp = tempfile.TemporaryDirectory(dir=str(DEFAULT_RUNTIME_DIR))

        # Outside file that a symlink-escape would target
        outside_dir = tempfile.TemporaryDirectory()
        outside_file = pathlib.Path(outside_dir.name) / "outside.json"
        outside_file.write_text(json.dumps(base_raw))

        # Payloads: (discovery_fixture_value, packet_id_suffix)
        payloads = [
            ("", "empty"),
            ("/etc/passwd.json", "absolute"),
            ("../escape.json", "traversal"),
            ("sub/dir.json", "forward-slash"),
            ("sub\\dir.json", "backslash"),
            ("complete-snapshot.json", "missing-filename"),  # won't exist in temp root
            ("malformed.json", "malformed"),
            ("escape.json", "symlink-escape"),
        ]

        for fixture_value, suffix in payloads:
            with self.subTest(fixture_value=fixture_value):
                tmp = tempfile.TemporaryDirectory()
                root = pathlib.Path(tmp.name)
                (root / "project-discovery").mkdir()

                # For symlink-escape target, create link pointing outside
                if suffix == "symlink-escape":
                    (root / "project-discovery" / "escape.json").symlink_to(outside_file)
                if suffix == "malformed":
                    (root / "project-discovery" / "malformed.json").write_text("{bad}")

                # Build a per-test packet with distinct ID and fresh runtime dir
                packet_id = f"alpha-03-test-{suffix}"
                runtime_dir = pathlib.Path(runtime_tmp.name) / "runtime"

                packet_data = copy.deepcopy(
                    json.loads(
                        (FIXTURES.parent / "alpha-03-complete-discovery-packet.json").read_text()
                    )
                )
                packet_data["packet_id"] = packet_id
                packet_data["executor"]["scenario"] = "discovery-complete"
                packet_data["discovery_fixture"] = fixture_value

                packet_file = root / f"{packet_id}.json"
                packet_file.write_text(json.dumps(packet_data))

                counting = SyntheticLocalExecutor()
                counting._calls = 0
                original_execute = counting.execute

                def counting_execute(self_exec, packet, worktree_path):
                    self_exec._calls += 1
                    return original_execute(self_exec, packet, worktree_path)

                import types
                counting.execute = types.MethodType(counting_execute, counting)

                wrapper = PacketWrapper(RuntimeConfig(runtime_dir), executor=counting)

                with unittest.mock.patch.object(
                    maestro.synthetic_discovery,
                    "DISCOVERY_FIXTURE_ROOT",
                    root / "project-discovery",
                ):
                    with self.assertRaises((ValueError, DiscoveryError)):
                        wrapper.run(packet_file)

                # Executor never executes
                self.assertEqual(counting._calls, 0)
                # No packet-worktrees directory created
                self.assertFalse((runtime_dir / "packet-worktrees").exists())

                self.assertFalse(runtime_dir.exists())
                tmp.cleanup()

        outside_dir.cleanup()
        runtime_tmp.cleanup()

    # -- Test 2: preclaim blocks execution --

    def test_preclaim_blocks_execution(self):
        import json
        import tempfile
        from maestro.storage import SQLiteFoundation
        from maestro.packet_wrapper import PacketWrapper, SyntheticLocalExecutor
        from maestro.config import RuntimeConfig, DEFAULT_RUNTIME_DIR

        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

        tmp = tempfile.TemporaryDirectory(dir=str(DEFAULT_RUNTIME_DIR))
        runtime_dir = pathlib.Path(tmp.name) / "runtime"

        wrapper = PacketWrapper(RuntimeConfig(runtime_dir))
        foundation = wrapper.storage

        # Pre-claim the packet before wrapper.run
        claim = foundation.claim_packet(
            "alpha-03-complete-discovery",
            {"pre": "claim"},
        )

        self.assertEqual(claim.status, "Claimed")
        self.assertTrue(claim.claimed)

        # Second claim should see the existing claim
        claim2 = foundation.claim_packet(
            "alpha-03-complete-discovery",
            {"pre": "claim2"},
        )
        self.assertFalse(claim2.claimed)

        # Now run the wrapper — it should see the existing claim and short-circuit
        counting = SyntheticLocalExecutor()
        counting._calls = 0
        original_execute = counting.execute

        import types
        def counting_execute(self_exec, packet, worktree_path):
            self_exec._calls += 1
            return original_execute(self_exec, packet, worktree_path)
        counting.execute = types.MethodType(counting_execute, counting)

        wrapper2 = PacketWrapper(RuntimeConfig(runtime_dir), executor=counting)
        result = wrapper2.run(FIXTURES.parent / "alpha-03-complete-discovery-packet.json")

        self.assertFalse(result.launched)
        self.assertIsNone(result.worktree_path)
        self.assertEqual(counting._calls, 0)
        self.assertFalse((runtime_dir / "packet-worktrees").exists())

        snapshot = wrapper2.storage.packet_snapshot(result.packet_id)
        self.assertEqual(len(snapshot.get("evidence", {})), 0)
        self.assertEqual(len(snapshot.get("handoffs", [])), 0)

        tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
