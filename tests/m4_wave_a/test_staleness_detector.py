"""M4.02 — find_stale_attempts, tested against a real Running attempt
with a real, short-lived lease.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m3_wave_a"))

from support import RuntimeDirectory, TemporaryProjectRepository  # noqa: E402
from test_foundry_real_registration import FOUNDRY_MANIFEST, _FOUNDRY_AUTHORITY_FILES  # noqa: E402

from maestro.config import RuntimeConfig  # noqa: E402
from maestro.dispatch_orchestrator import iso_plus, now_iso  # noqa: E402
from maestro.operational_state import Actor, OperationalStateStore  # noqa: E402
from maestro.project_authority import ProjectAuthorityLoader  # noqa: E402
from maestro.staleness_detector import find_stale_attempts  # noqa: E402

ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
NOW = "2026-09-08T05:00:00.000000Z"
REAL_HEAD = "5e01f5a0d02c78ced41a915042b49dd8ffd666c9"


class StalenessDetectorTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository(manifest=FOUNDRY_MANIFEST)
        for relative, content in _FOUNDRY_AUTHORITY_FILES.items():
            target = self.repository.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        commit = self.repository.commit_all("real Foundry authority files")

        self.runtime = RuntimeDirectory()
        self.foundation = self.runtime.foundation()
        self.config = RuntimeConfig(self.runtime.path)
        self.store = OperationalStateStore(self.config)

        load_result = ProjectAuthorityLoader(self.foundation).load(
            self.repository.path, commit, "jmiedreich-ux/Foundry"
        )
        self.store.record_binding(
            {
                "binding_id": "binding-1", "project_id": "foundry", "binding_revision": "revision-1",
                "source_commit": load_result.source_commit, "manifest_digest": load_result.manifest_digest,
                "adapter_version": "maestro-github-adapter-v1", "process_version": "maestro-m4-process-v1",
                "authority_reference": load_result.request_id, "merge_policy": "no-automatic-merge",
                "acceptance_authority": "ProjectArchitect", "merge_execution_authority": "OwnerPerformed",
                "merge_delegation_reference": None, "binding_json": {"binding": "candidate"},
                "state": "Candidate", "activated_at": None, "superseded_at": None,
            },
            "cmd-binding", ACTOR, NOW,
        )
        self.foundation.register_project("foundry", "binding-1")
        self.store.record_graph_projection(
            {
                "graph_projection_id": "graph-1", "project_id": "foundry", "binding_id": "binding-1",
                "graph_revision": "rev-1", "authority_reference": load_result.request_id,
                "source_base_sha": REAL_HEAD,
                "source_hash": hashlib.sha256(b"M4.02 test work item").hexdigest(),
                "state": "Active", "observed_at": NOW,
            },
            [{
                "work_item_id": "work-1", "graph_projection_id": "graph-1",
                "architecture_node_id": "M4-02", "task_reference": "jmiedreich-ux/Foundry#99",
                "workstream_ref": "control-gallery", "milestone_ref": "M4",
                "title": "M4.02 staleness detector test", "priority": "P1", "planned_rank": 1,
                "specialist_role": "MaestroDeveloper", "execution_classes_json": ["local-qwen"],
                "dependencies_json": [], "change_domains_json": ["tests/fake"],
                "input_contract_json": {"prerequisite": None},
                "output_contract_json": {"deliverable": "fake"},
                "planning_state": "Active",
            }],
            "cmd-graph", ACTOR, NOW,
        )
        self.store.create_run(
            {
                "run_id": "run-1", "run_fingerprint": hashlib.sha256(b"run-1").hexdigest(),
                "project_id": "foundry", "binding_id": "binding-1", "graph_projection_id": "graph-1",
                "milestone_ref": "M4", "approved_authority_reference": load_result.request_id,
                "branch_name": None, "pull_request_reference": None, "current_head": None,
                "current_head_source_reference": None, "candidate_head": None,
                "candidate_head_source_reference": None, "state": "Planned",
                "acceptance_boundary": "Owner",
            },
            "cmd-run", ACTOR, NOW,
        )
        context_policy = {
            "minimum_context_tokens": 32768, "output_reserve_tokens": 8192,
            "warning_remaining_tokens": 16384, "checkpoint_remaining_tokens": 12288,
            "stop_remaining_tokens": 8192,
        }
        packet = self.store.materialize_packet(
            {
                "packet_id": "packet-1", "run_id": "run-1", "work_item_id": "work-1",
                "packet_revision": "packet-r1", "authority_reference": load_result.request_id,
                "base_commit": REAL_HEAD, "current_head": None,
                "expected_branch": "codex/m4-02-test", "role_contract_reference": "AGENTS.md",
                "sop_reference": "AGENTS.md", "executor_class": "local-qwen",
                "integration_route": "validate-only", "reviewer_route": "independent",
                "owned_paths_json": ["tests/fake/"], "forbidden_paths_json": ["package.json"],
                "checks_json": ["npm run check"], "resource_claims_json": ["shared:tests/fake"],
                "context_policy_json": context_policy, "state": "Planned", "correction_count": 0,
            },
            "cmd-packet", ACTOR, NOW,
        )
        reason = {"kind": "reason", "reason_code": "TEST_SETUP", "detail_reference": None}
        version = packet["version"]
        for target in ("Waiting", "Ready", "Dispatchable"):
            result = self.store.transition_packet_eligibility(
                "packet-1", version, target, reason, f"elig-{target}", ACTOR, NOW,
            )
            version = result["version"]
        self.store.transition_run("run-1", 1, "Running", reason, "run-running", ACTOR, NOW)

        self.short_lease_expiry = iso_plus(1)
        lease = {
            "executor_route": "local-qwen/developer-1", "expires_at": self.short_lease_expiry,
            "holder_id": "developer-1", "lease_id": "lease-1",
            "worktree_path": str(self.repository.path),
        }
        locks = [{"lock_id": "lock-1", "lock_kind": "Path", "resource_key": "shared:tests/fake"}]
        attempt = {"attempt_id": "attempt-1", "model_identity": "qwen3.6:27b", "runtime_identity": "local-qwen-ollama"}
        claim = self.store.claim_packet_assignment(
            "packet-1", version, lease, locks, attempt, reason, "claim-1", ACTOR, NOW,
        )
        started = self.store.start_attempt_execution(
            "attempt-1", claim["attempt"]["version"], claim["packet"]["version"],
            "fake-handle-1", "AwaitingIntegration", reason, "start-1", ACTOR, NOW,
        )
        self.attempt_version = started["attempt"]["version"]
        self.packet_version = started["packet"]["version"]
        self.lease_version = claim["lease"]["version"]

    def tearDown(self):
        self.runtime.close()

    def test_a_running_attempt_with_an_unexpired_lease_is_not_stale(self):
        found = find_stale_attempts(self.config, now_iso())
        self.assertEqual(found, [])

    def test_a_running_attempt_whose_lease_has_really_expired_is_found(self):
        past_the_real_expiry = iso_plus(5)  # short_lease_expiry was iso_plus(1)
        found = find_stale_attempts(self.config, past_the_real_expiry)

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].attempt_id, "attempt-1")
        self.assertEqual(found[0].packet_id, "packet-1")
        self.assertEqual(found[0].lease_id, "lease-1")
        self.assertEqual(found[0].expires_at, self.short_lease_expiry)

    def test_a_finished_attempt_is_never_reported_stale_even_long_after_its_old_lease_expiry(self):
        # Real recovery must never flag an attempt that already finished
        # for real (e.g. via M4.01's own normal-completion path) just
        # because its now-irrelevant old lease timestamp is in the past.
        reason = {"kind": "reason", "reason_code": "TEST_SETUP", "detail_reference": None}
        self.store.finish_attempt_execution(
            "attempt-1", self.attempt_version, self.packet_version, self.lease_version,
            "fake-handle-1", "Succeeded", "a" * 40, "evidence-ref", reason, "finish-1", ACTOR, NOW,
        )
        far_future = "2027-01-01T00:00:00.000000Z"
        found = find_stale_attempts(self.config, far_future)
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
