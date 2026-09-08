"""Shared real-fixture builder for M4 tests — one real registered
project, binding, graph, run, and claimed packet, built through the
exact same real commands this session's own manual Foundry dispatches
used. Every M4 packet's own tests start from the same real base state
(a claimed, `Leased` packet with a real `Planned` attempt) rather than
each re-deriving its own copy.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m3_wave_a"))

from support import RuntimeDirectory, TemporaryProjectRepository  # noqa: E402
from test_foundry_real_registration import FOUNDRY_MANIFEST, _FOUNDRY_AUTHORITY_FILES  # noqa: E402

from maestro.config import RuntimeConfig  # noqa: E402
from maestro.dispatch_orchestrator import iso_plus  # noqa: E402
from maestro.operational_state import Actor, OperationalStateStore  # noqa: E402
from maestro.project_authority import ProjectAuthorityLoader  # noqa: E402

ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
NOW = "2026-09-08T05:00:00.000000Z"
REASON = {"kind": "reason", "reason_code": "TEST_SETUP", "detail_reference": None}


class ClaimedPacketFixture:
    """Owns the real runtime/repository resources; call ``close()`` in
    ``tearDown`` (or use as a context manager)."""

    def __init__(self, *, lease_expires_in_seconds: float = 3600) -> None:
        self.repository = TemporaryProjectRepository(manifest=FOUNDRY_MANIFEST)
        for relative, content in _FOUNDRY_AUTHORITY_FILES.items():
            target = self.repository.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        commit = self.repository.commit_all("real Foundry authority files")
        self.base_commit = commit

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
                "source_base_sha": commit,
                "source_hash": hashlib.sha256(b"M4 test work item").hexdigest(),
                "state": "Active", "observed_at": NOW,
            },
            [{
                "work_item_id": "work-1", "graph_projection_id": "graph-1",
                "architecture_node_id": "M4-TEST", "task_reference": "jmiedreich-ux/Foundry#99",
                "workstream_ref": "control-gallery", "milestone_ref": "M4",
                "title": "M4 packet test fixture", "priority": "P1", "planned_rank": 1,
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
                "base_commit": commit, "current_head": None,
                "expected_branch": "codex/m4-test", "role_contract_reference": "AGENTS.md",
                "sop_reference": "AGENTS.md", "executor_class": "local-qwen",
                "integration_route": "validate-only", "reviewer_route": "independent",
                "owned_paths_json": ["tests/fake/"], "forbidden_paths_json": ["package.json"],
                "checks_json": ["true"], "resource_claims_json": ["shared:tests/fake"],
                "context_policy_json": context_policy, "state": "Planned", "correction_count": 0,
            },
            "cmd-packet", ACTOR, NOW,
        )
        version = packet["version"]
        for target in ("Waiting", "Ready", "Dispatchable"):
            result = self.store.transition_packet_eligibility(
                "packet-1", version, target, REASON, f"elig-{target}", ACTOR, NOW,
            )
            version = result["version"]
        self.store.transition_run("run-1", 1, "Running", REASON, "run-running", ACTOR, NOW)

        self.lease_expires_at = iso_plus(lease_expires_in_seconds)
        lease = {
            "executor_route": "local-qwen/developer-1", "expires_at": self.lease_expires_at,
            "holder_id": "developer-1", "lease_id": "lease-1",
            "worktree_path": str(self.repository.path),
        }
        locks = [{"lock_id": "lock-1", "lock_kind": "Path", "resource_key": "shared:tests/fake"}]
        attempt = {"attempt_id": "attempt-1", "model_identity": "qwen3.6:27b", "runtime_identity": "local-qwen-ollama"}
        claim = self.store.claim_packet_assignment(
            "packet-1", version, lease, locks, attempt, REASON, "claim-1", ACTOR, NOW,
        )
        self.attempt_version = claim["attempt"]["version"]
        self.packet_version = claim["packet"]["version"]
        self.lease_version = claim["lease"]["version"]

    def start_execution(
        self, *, attempt_id: str = "attempt-1", handle: str | None = None,
        expected_result: str = "AwaitingIntegration",
    ):
        # execution_handle is globally unique (attempts.execution_handle)
        # -- a real second attempt (a real correction) needs its own
        # real, distinct handle, not the Initial attempt's.
        if handle is None:
            handle = f"fake-handle-{attempt_id}"
        started = self.store.start_attempt_execution(
            attempt_id, self.attempt_version, self.packet_version,
            handle, expected_result, REASON, f"start-{attempt_id}", ACTOR, NOW,
        )
        self.attempt_version = started["attempt"]["version"]
        self.packet_version = started["packet"]["version"]
        self.execution_handle = handle
        return started

    def finish_succeeded(self, result_commit: str, *, attempt_id: str = "attempt-1"):
        """Real finish, Succeeded — requires `start_execution` first.
        ``result_commit`` should be a real commit the fixture's own
        repository actually has."""
        finished = self.store.finish_attempt_execution(
            attempt_id, self.attempt_version, self.packet_version, self.lease_version,
            self.execution_handle, "Succeeded", result_commit, "evidence-ref",
            REASON, f"finish-{attempt_id}", ACTOR, NOW,
        )
        self.attempt_version = finished["attempt"]["version"]
        self.packet_version = finished["packet"]["version"]
        return finished

    def dispatch_correction(
        self, review_id: str, *, expected_packet_version: int | None = None,
        attempt_id: str = "attempt-2", lease_id: str = "lease-2", lock_id: str = "lock-2",
    ):
        """Real correction dispatch — requires the packet already be
        real `AwaitingArchitect` (a real `RequestChanges` review).
        ``expected_packet_version`` defaults to the fixture's own last
        tracked version, but a caller that routed a review directly
        through `review_dispatch.py` (bypassing the fixture) must pass
        the real version that call actually returned — the fixture has
        no way to observe that on its own. Resets the fixture's own
        tracked attempt/packet/lease version state to this new real
        correction attempt's own.

        Real gap this session already found once for CG-M4-19: lock
        rows persist even after release (an existence check, not a
        state check) — reusing the Initial attempt's own `lock_id` here
        would fail with "correction lock_id already exists".
        """
        version = self.packet_version if expected_packet_version is None else expected_packet_version
        self.lease_expires_at = iso_plus(3600)
        lease = {
            "executor_route": "local-qwen/developer-1", "expires_at": self.lease_expires_at,
            "holder_id": "developer-1", "lease_id": lease_id,
            "worktree_path": str(self.repository.path),
        }
        locks = [{"lock_id": lock_id, "lock_kind": "Path", "resource_key": "shared:tests/fake"}]
        attempt = {"attempt_id": attempt_id, "model_identity": "qwen3.6:27b", "runtime_identity": "local-qwen-ollama"}
        dispatched = self.store.record_and_dispatch_correction(
            "packet-1", version, review_id, lease, locks, attempt,
            REASON, f"dispatch-correction-{attempt_id}", ACTOR, NOW,
        )
        self.attempt_version = dispatched["attempt"]["version"]
        self.packet_version = dispatched["packet"]["version"]
        self.lease_version = dispatched["lease"]["version"]
        return dispatched

    def close(self) -> None:
        self.runtime.close()

    def __enter__(self) -> "ClaimedPacketFixture":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
