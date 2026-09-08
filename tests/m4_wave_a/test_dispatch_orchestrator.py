"""M4.01 — DispatchOrchestrator, tested against a real claimed packet.

Builds one real packet/attempt/lease through the exact same real
commands this session's own manual Foundry dispatches used
(materialize_packet -> eligibility transitions -> claim_packet_
assignment), then drives DispatchOrchestrator against it with a fake
ExecutorAdapter (no real subprocess/git needed to prove the real
attempt/lease state machine wiring is correct).
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
from maestro.dispatch_orchestrator import DispatchOrchestrator, DispatchRequest, iso_plus  # noqa: E402
from maestro.executor import ExecutorHandoff, ExecutorObservation, ExecutorPreflight  # noqa: E402
from maestro.operational_state import Actor, OperationalStateStore, StaleState  # noqa: E402
from maestro.project_authority import ProjectAuthorityLoader  # noqa: E402

ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
NOW = "2026-09-08T05:00:00.000000Z"
REAL_HEAD = "5e01f5a0d02c78ced41a915042b49dd8ffd666c9"


class FakeExecutorAdapter:
    """A real, honest fake: `observe()` reports running for exactly
    `running_ticks` calls, then finished; `retrieve_evidence` returns
    the exact `ExecutorHandoff` the test configured, never invented.
    """

    def __init__(self, *, running_ticks: int, handoff: ExecutorHandoff) -> None:
        self.running_ticks = running_ticks
        self.handoff = handoff
        self.submitted: list[tuple[ExecutorPreflight, str]] = []
        self.cancelled: list[str] = []
        self._ticks = 0

    def submit(self, preflight: ExecutorPreflight, instructions: str) -> str:
        self.submitted.append((preflight, instructions))
        return "fake-handle-1"

    def observe(self, handle: str) -> ExecutorObservation:
        self._ticks += 1
        running = self._ticks <= self.running_ticks
        return ExecutorObservation(handle=handle, running=running, exit_code=None if running else 0)

    def cancel(self, handle: str) -> None:
        self.cancelled.append(handle)

    def retrieve_evidence(self, handle: str, *, branch_name: str) -> ExecutorHandoff:
        return self.handoff


class DispatchOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository(manifest=FOUNDRY_MANIFEST)
        for relative, content in _FOUNDRY_AUTHORITY_FILES.items():
            target = self.repository.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.commit = self.repository.commit_all("real Foundry authority files")

        self.runtime = RuntimeDirectory()
        self.foundation = self.runtime.foundation()
        self.config = RuntimeConfig(self.runtime.path)
        self.store = OperationalStateStore(self.config)

        load_result = ProjectAuthorityLoader(self.foundation).load(
            self.repository.path, self.commit, "jmiedreich-ux/Foundry"
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
                "source_hash": hashlib.sha256(b"M4.01 test work item").hexdigest(),
                "state": "Active", "observed_at": NOW,
            },
            [{
                "work_item_id": "work-1", "graph_projection_id": "graph-1",
                "architecture_node_id": "M4-01", "task_reference": "jmiedreich-ux/Foundry#99",
                "workstream_ref": "control-gallery", "milestone_ref": "M4",
                "title": "M4.01 dispatch orchestrator test", "priority": "P1", "planned_rank": 1,
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
                "expected_branch": "codex/m4-01-test", "role_contract_reference": "AGENTS.md",
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

        self.lease_expires_at = iso_plus(3600)
        lease = {
            "executor_route": "local-qwen/developer-1", "expires_at": self.lease_expires_at,
            "holder_id": "developer-1", "lease_id": "lease-1",
            "worktree_path": str(self.repository.path),
        }
        locks = [{"lock_id": "lock-1", "lock_kind": "Path", "resource_key": "shared:tests/fake"}]
        attempt = {"attempt_id": "attempt-1", "model_identity": "qwen3.6:27b", "runtime_identity": "local-qwen-ollama"}
        claim = self.store.claim_packet_assignment(
            "packet-1", version, lease, locks, attempt, reason, "claim-1", ACTOR, NOW,
        )
        self.attempt_version = claim["attempt"]["version"]
        self.packet_version = claim["packet"]["version"]
        self.lease_version = claim["lease"]["version"]

        self.preflight = ExecutorPreflight(
            base_commit=REAL_HEAD,
            worktree_path=self.repository.path,
            allowed_paths=("tests/fake/",),
            forbidden_paths=("package.json",),
            model_identity="qwen3.6:27b",
        )

    def tearDown(self):
        self.runtime.close()

    def _orchestrator(self, executor) -> DispatchOrchestrator:
        return DispatchOrchestrator(
            self.store, executor, ACTOR,
            heartbeat_interval_seconds=0.001, poll_interval_seconds=0.001,
        )

    def _request(self) -> DispatchRequest:
        return DispatchRequest(
            attempt_id="attempt-1", lease_id="lease-1",
            expected_attempt_version=self.attempt_version,
            expected_packet_version=self.packet_version,
            expected_lease_version=self.lease_version,
            expected_lease_expires_at=self.lease_expires_at,
            preflight=self.preflight, instructions="do the real work",
            expected_result="AwaitingIntegration", expected_branch="codex/m4-01-test",
        )

    def test_real_success_path_calls_start_heartbeat_and_finish_succeeded(self):
        handoff = ExecutorHandoff(
            branch_name="codex/m4-01-test", commit_sha="a" * 40,
            changed_files=("tests/fake/x.spec.ts",), raw_output="ok", completed=True,
        )
        executor = FakeExecutorAdapter(running_ticks=3, handoff=handoff)
        result = self._orchestrator(executor).run(self._request())

        self.assertEqual(result.outcome, "Succeeded")
        self.assertEqual(result.result_commit, "a" * 40)
        self.assertEqual(executor.submitted[0][1], "do the real work")

        snapshot = self.store.snapshot("Packet", "packet-1")
        self.assertEqual(snapshot["state"], "AwaitingIntegration")

    def test_real_failure_path_calls_finish_failed_when_no_commit_was_produced(self):
        handoff = ExecutorHandoff(
            branch_name="codex/m4-01-test", commit_sha=None,
            changed_files=(), raw_output="crashed before committing", completed=False,
        )
        executor = FakeExecutorAdapter(running_ticks=1, handoff=handoff)
        result = self._orchestrator(executor).run(self._request())

        self.assertEqual(result.outcome, "Failed")
        self.assertIsNone(result.result_commit)

        snapshot = self.store.snapshot("Packet", "packet-1")
        self.assertEqual(snapshot["state"], "NeedsReplan")

    def test_heartbeats_advance_the_real_attempt_and_lease_version_before_finish(self):
        handoff = ExecutorHandoff(
            branch_name="codex/m4-01-test", commit_sha="b" * 40,
            changed_files=("tests/fake/x.spec.ts",), raw_output="ok", completed=True,
        )
        executor = FakeExecutorAdapter(running_ticks=2, handoff=handoff)
        orchestrator = DispatchOrchestrator(
            self.store, executor, ACTOR,
            heartbeat_interval_seconds=0.001,
            poll_interval_seconds=0.001,
        )
        # heartbeat_interval_seconds=0 means every poll tick heartbeats,
        # so with running_ticks=2 the real attempt/lease versions must
        # have advanced by the time finish is called.
        result = orchestrator.run(self._request())
        self.assertGreater(result.attempt_version, self.attempt_version + 1)
        self.assertGreater(result.lease_version, self.lease_version)

    def test_a_second_stale_finish_call_is_rejected_not_silently_overwritten(self):
        # Proves the real optimistic-version protection recovery
        # (M4.02/M4.03) depends on: once one real finish call has
        # already advanced the attempt/packet/lease versions, a second
        # caller using the old, now-stale versions (e.g. a real recovery
        # path racing a real late completion) is rejected, never
        # silently applied on top.
        handoff = ExecutorHandoff(
            branch_name="codex/m4-01-test", commit_sha="c" * 40,
            changed_files=("tests/fake/x.spec.ts",), raw_output="ok", completed=True,
        )
        executor = FakeExecutorAdapter(running_ticks=0, handoff=handoff)
        self._orchestrator(executor).run(self._request())

        reason = {"kind": "reason", "reason_code": "TIMEOUT", "detail_reference": None}
        with self.assertRaises(StaleState):
            self.store.finish_attempt_execution(
                "attempt-1", self.attempt_version, self.packet_version, self.lease_version,
                "some-other-handle", "TimedOut", None, "recovery-detected-silence",
                reason, "recovery-finish-1", ACTOR, NOW,
            )


if __name__ == "__main__":
    unittest.main()
