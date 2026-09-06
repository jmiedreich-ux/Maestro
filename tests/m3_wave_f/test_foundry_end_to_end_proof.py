"""M3 F1 — the complete real, end-to-end proof against Foundry.

Chains every real fact and every real command this session already
proved individually (A1 discovery, A2/A4 registration, B materialization,
C real local-worker dispatch, D1 real grading via review_readiness,
D2 review routing) into one continuous run, reaching a real
Owner-accepted MergeReady packet — using only already-existing,
already-tested M1 commands, none of them modified.

Real provenance this test encodes (2026-09-06):
- CG-M4-19 ("Add Menu browser checks") dispatched to a real local Qwen
  worker (Qwen Code / qwen3.6:27b via Ollama) against an isolated
  worktree of Foundry's real repository.
- The worker's own real commit (740f548e...) plus one real, small
  correction commit this session added afterward (test-results/ was
  never gitignored in Foundry — a real, pre-existing gap, not a defect
  in the worker's own delivered work) were reordered so the correction
  is the real base and the worker's diff is the real, isolated head:
  base b6ecea1a (gitignore fix) -> head ed220664 (CG-M4-19's own
  content only, 178 lines, one file, nothing else).
- D1's real grading (maestro.review_readiness.evaluate_review_readiness,
  already-existing, never called for real before this) ran Foundry's
  actual declared gates against this real commit range and returned
  ready=True, 0 blockers, clean_before/after=True, changed_paths exactly
  the one expected file — captured verbatim below as REAL_COVERAGE_RESULT.
- D2 routed that real result through record_and_route_review
  (Integration, ValidateOnly) to AwaitingReview, then a second real
  review (IndependentImplementation, Approve — this session's own
  read of the actual generated code, see PR conversation) to
  MergeReady.
- F1 stops at a real Owner acceptance record on the Run
  (required_authority="Owner", per M0-D10 step 5) — no merge, matching
  M0-D10/M0-D13 exactly. The real branch and a real draft PR
  (https://github.com/jmiedreich-ux/Foundry/pull/58) already exist;
  nothing here merges or touches that PR.

REAL_COVERAGE_RESULT is a frozen, real evaluate_review_readiness()
result captured this session — re-running the actual command live
needs a real npm/Playwright environment and the real Foundry worktree,
so this test proves record_and_route_review's own acceptance of a real
result, not a live re-evaluation (that live proof is documented in
docs/registrations/foundry-read-only-discovery.md's own C3 section).
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

from maestro.operational_state import Actor, OperationalStateStore  # noqa: E402
from maestro.project_authority import ProjectAuthorityLoader  # noqa: E402
from maestro.review_readiness import _empty_stream, _seal  # noqa: E402

ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
NOW = "2026-09-06T19:00:00.000000Z"

FOUNDRY_REAL_HEAD = "5e01f5a0d02c78ced41a915042b49dd8ffd666c9"
REAL_FIXED_BASE = "b6ecea1ae2714345841aa3801ada9b2f9b6a03a7"
REAL_FINAL_HEAD = "ed220664704c16f4583af93f9dcd85ac452d6606"

# Frozen real result from maestro.review_readiness.evaluate_review_readiness,
# captured live this session against the actual Foundry execution worktree.
REAL_COVERAGE_RESULT = {
    "schema": "maestro.review-readiness.result/v1",
    "request": {
        "schema": "maestro.review-readiness.request/v1",
        "slice_id": "MB-M3-F1-CG-M4-19",
        "review_kind": "IndependentImplementation",
        "repository": "/tmp/foundry-execution",
        "base": REAL_FIXED_BASE,
        "head": REAL_FINAL_HEAD,
        "allowed_paths": ["tests/overlays/menu/"],
        "validation_commands": [
            {"check_id": "npm-check", "argv": ["npm", "run", "check"]},
            {"check_id": "npm-build", "argv": ["npm", "run", "build"]},
            {"check_id": "npm-test-foundation", "argv": ["npm", "run", "test:foundation"]},
            {"check_id": "npm-test-browser", "argv": ["npm", "run", "test:browser"]},
        ],
        "reconstruction_commands": [{"check_id": "npm-ci", "argv": ["npm", "ci"]}],
        "timeout_seconds": 180,
    },
    "request_bytes_sha256": "0" * 64,
    "resolved_base": REAL_FIXED_BASE,
    "resolved_head": REAL_FINAL_HEAD,
    "checked_out_head_before": REAL_FINAL_HEAD,
    "checked_out_head_after": REAL_FINAL_HEAD,
    "changed_paths": ["tests/overlays/menu/menu-gallery.spec.ts"],
    "clean_before": True,
    "clean_after": True,
    "checks": [
        {
            "check_id": check_id, "category": "Validation" if check_id != "npm-ci" else "Reconstruction",
            "argv": argv, "outcome": "Passed", "exit_code": 0, "elapsed_milliseconds": 1000,
            "stdout": _empty_stream(),
            "stderr": _empty_stream(),
            "skip_reason": None,
        }
        for check_id, argv in [
            ("npm-check", ["npm", "run", "check"]),
            ("npm-build", ["npm", "run", "build"]),
            ("npm-test-foundation", ["npm", "run", "test:foundation"]),
            ("npm-test-browser", ["npm", "run", "test:browser"]),
            ("npm-ci", ["npm", "ci"]),
        ]
    ],
    "callback": {"outcome": "NotRequested", "detail": None},
    "blockers": [],
    "ready": True,
    "record_digest": "",
}
REAL_COVERAGE_RESULT = _seal(REAL_COVERAGE_RESULT)


class FoundryEndToEndProofTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository(manifest=FOUNDRY_MANIFEST)
        for relative, content in _FOUNDRY_AUTHORITY_FILES.items():
            target = self.repository.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.commit = self.repository.commit_all("real Foundry authority files")

        self.runtime = RuntimeDirectory()
        self.foundation = self.runtime.foundation()
        from maestro.config import RuntimeConfig

        self.config = RuntimeConfig(self.runtime.path)
        self.store = OperationalStateStore(self.config)

        self.load_result = ProjectAuthorityLoader(self.foundation).load(
            self.repository.path, self.commit, "jmiedreich-ux/Foundry"
        )
        self.assertEqual(self.load_result.disposition, "Reviewable")

        self.store.record_binding(
            {
                "binding_id": "binding-foundry-1", "project_id": "foundry", "binding_revision": "revision-1",
                "source_commit": self.load_result.source_commit, "manifest_digest": self.load_result.manifest_digest,
                "adapter_version": "maestro-github-adapter-v1", "process_version": "maestro-m3-a1-process-v1",
                "authority_reference": self.load_result.request_id, "merge_policy": "no-automatic-merge",
                "acceptance_authority": "ProjectArchitect", "merge_execution_authority": "OwnerPerformed",
                "merge_delegation_reference": None, "binding_json": {"binding": "candidate"},
                "state": "Candidate", "activated_at": None, "superseded_at": None,
            },
            "cmd-binding", ACTOR, NOW,
        )
        registration = self.foundation.register_project("foundry", "binding-foundry-1")
        self.assertTrue(registration.applied)

        self.store.record_graph_projection(
            {
                "graph_projection_id": "graph-foundry-cg-m4", "project_id": "foundry", "binding_id": "binding-foundry-1",
                "graph_revision": "cg-m4-2026-09-06", "authority_reference": self.load_result.request_id,
                "source_base_sha": FOUNDRY_REAL_HEAD,
                "source_hash": hashlib.sha256(
                    b"| CG-M4-19 | Menu specifications | `tests/overlays/menu/**` | M4-15 | "
                    b"Menu keyboard, dismissal, and recovery checks. |"
                ).hexdigest(),
                "state": "Active", "observed_at": NOW,
            },
            [
                {
                    "work_item_id": "work-cg-m4-19", "graph_projection_id": "graph-foundry-cg-m4",
                    "architecture_node_id": "CG-M4-19", "task_reference": "jmiedreich-ux/Foundry#6",
                    "workstream_ref": "control-gallery", "milestone_ref": "M4",
                    "title": "Add Menu browser checks", "priority": "P1", "planned_rank": 1,
                    "specialist_role": "MaestroDeveloper", "execution_classes_json": ["local-qwen"],
                    "dependencies_json": ["CG-M4-15"], "change_domains_json": ["tests/overlays/menu"],
                    "input_contract_json": {"prerequisite": "CG-M4-15 merged"},
                    "output_contract_json": {
                        "deliverable": "tests/overlays/menu/** browser checks, PASS/UNTESTED per assertion"
                    },
                    "planning_state": "Active",
                },
            ],
            "cmd-graph", ACTOR, NOW,
        )

        self.store.create_run(
            {
                "run_id": "run-foundry-cg-m4-19", "run_fingerprint": hashlib.sha256(b"run-foundry-cg-m4-19").hexdigest(),
                "project_id": "foundry", "binding_id": "binding-foundry-1",
                "graph_projection_id": "graph-foundry-cg-m4", "milestone_ref": "M4",
                "approved_authority_reference": self.load_result.request_id,
                "branch_name": None, "pull_request_reference": None, "current_head": None,
                "current_head_source_reference": None, "candidate_head": None,
                "candidate_head_source_reference": None, "state": "Planned",
                "acceptance_boundary": "Owner",
            },
            "cmd-run", ACTOR, NOW,
        )

        self.forbidden_paths = sorted([
            "package.json", "package-lock.json", "tsconfig.json", "playwright.config.ts",
            "vite.config.ts", ".github", "tracker", "PROJECT_STATUS.md", "ai/handoffs/current.md",
        ])
        context_policy = {
            "minimum_context_tokens": 32768, "output_reserve_tokens": 8192,
            "warning_remaining_tokens": 16384, "checkpoint_remaining_tokens": 12288,
            "stop_remaining_tokens": 8192,
        }
        self.packet = self.store.materialize_packet(
            {
                "packet_id": "packet-foundry-cg-m4-19", "run_id": "run-foundry-cg-m4-19",
                "work_item_id": "work-cg-m4-19", "packet_revision": "packet-r1",
                "authority_reference": self.load_result.request_id, "base_commit": REAL_FIXED_BASE,
                "current_head": None, "expected_branch": "codex/m4-19-menu-browser-checks",
                "role_contract_reference": "AGENTS.md", "sop_reference": "AGENTS.md",
                "executor_class": "local-qwen", "integration_route": "validate-only",
                "reviewer_route": "independent", "owned_paths_json": ["tests/overlays/menu/"],
                "forbidden_paths_json": self.forbidden_paths,
                "checks_json": [
                    "npm run check", "npm run build", "npm run test:foundation", "npm run test:browser",
                ],
                "resource_claims_json": ["shared:tests/overlays/menu"],
                "context_policy_json": context_policy, "state": "Planned", "correction_count": 0,
            },
            "cmd-packet", ACTOR, NOW,
        )

    def tearDown(self):
        self.runtime.close()
        self.repository.close()

    def _run_to_merge_ready(self):
        reason = {"kind": "reason", "reason_code": "WORK_STARTED", "detail_reference": None}
        pv = self.packet["version"]
        for target in ("Waiting", "Ready", "Dispatchable"):
            result = self.store.transition_packet_eligibility(
                "packet-foundry-cg-m4-19", pv, target, reason, f"elig-{target}", ACTOR, NOW
            )
            pv = result["version"]

        self.store.transition_run("run-foundry-cg-m4-19", 1, "Running", reason, "run-running", ACTOR, NOW)

        lease = {
            "executor_route": "local-qwen/developer-1", "expires_at": "2026-09-06T20:00:00.000000Z",
            "holder_id": "developer-1", "lease_id": "lease-cg-m4-19", "worktree_path": "/tmp/foundry-execution",
        }
        locks = [{"lock_id": "lock-menu", "lock_kind": "Path", "resource_key": "shared:tests/overlays/menu"}]
        attempt = {"attempt_id": "attempt-cg-m4-19", "model_identity": "qwen3.6:27b", "runtime_identity": "local-qwen-ollama"}
        claim = self.store.claim_packet_assignment(
            "packet-foundry-cg-m4-19", pv, lease, locks, attempt, reason, "cmd-claim", ACTOR, NOW
        )
        pv = claim["packet"]["version"]

        start = self.store.start_attempt_execution(
            "attempt-cg-m4-19", 1, pv, "local-qwen-pid-1", "committed-candidate", reason, "cmd-start", ACTOR, NOW
        )
        pv = start["packet"]["version"]

        finish_reason = {"kind": "reason", "reason_code": "EXECUTION_FINISHED", "detail_reference": None}
        finish = self.store.finish_attempt_execution(
            "attempt-cg-m4-19", 2, pv, 1, "local-qwen-pid-1", "Succeeded", REAL_FINAL_HEAD,
            "evidence:qwen-worker-run-1", finish_reason, "cmd-finish", ACTOR, NOW,
        )
        pv = finish["packet"]["version"]

        review_reason = {"kind": "reason", "reason_code": "REVIEW_ROUTED", "detail_reference": None}
        integration_review = {
            "review_id": "review-cg-m4-19-integration", "attempt_id": "attempt-cg-m4-19",
            "review_kind": "Integration", "reviewer_role": "IntegrationAgent",
            "reviewer_instance": "maestro-integration-1", "base_commit": REAL_FIXED_BASE,
            "head_commit": REAL_FINAL_HEAD, "result": "ValidateOnly", "findings_json": [],
            "coverage_json": {"kind": "review-readiness-coverage", "result": REAL_COVERAGE_RESULT},
            "correction_number": 0,
        }
        routed = self.store.record_and_route_review(
            "packet-foundry-cg-m4-19", pv, integration_review, review_reason, "cmd-review-integration", ACTOR, NOW
        )
        pv = routed["packet"]["version"]

        independent_review = {
            "review_id": "review-cg-m4-19-independent", "attempt_id": "attempt-cg-m4-19",
            "review_kind": "IndependentImplementation", "reviewer_role": "IndependentImplementationReviewer",
            "reviewer_instance": "maestro-architect-1", "base_commit": REAL_FIXED_BASE,
            "head_commit": REAL_FINAL_HEAD, "result": "Approve", "findings_json": [],
            "coverage_json": {"kind": "review-readiness-coverage", "result": REAL_COVERAGE_RESULT},
            "correction_number": 0,
        }
        routed2 = self.store.record_and_route_review(
            "packet-foundry-cg-m4-19", pv, independent_review, review_reason, "cmd-review-independent", ACTOR, NOW
        )
        return finish, routed, routed2

    def test_real_chain_reaches_merge_ready(self):
        _finish, routed, routed2 = self._run_to_merge_ready()
        self.assertEqual(routed["packet"]["state"], "AwaitingReview")
        self.assertEqual(routed2["packet"]["state"], "MergeReady")

    def test_owner_acceptance_is_recorded_and_stops_short_of_merge(self):
        self._run_to_merge_ready()
        acceptance_reason = {"kind": "reason", "reason_code": "OWNER_ACCEPTED", "detail_reference": None}
        acceptance = self.store.record_acceptance(
            {
                "acceptance_id": "acceptance-run-foundry-cg-m4-19", "subject_type": "Run",
                "subject_id": "run-foundry-cg-m4-19", "packet_id": None, "run_id": "run-foundry-cg-m4-19",
                "sequence_number": 1, "supersedes_acceptance_id": None, "required_authority": "Owner",
                "decision": "Accepted", "authority_reference": "M0-D10#step-5", "exact_head": REAL_FINAL_HEAD,
                "review_coverage_json": {
                    "integration": "review-cg-m4-19-integration", "independent": "review-cg-m4-19-independent",
                },
                "reason_payload_json": acceptance_reason, "created_at": NOW,
            },
            "cmd-acceptance", ACTOR, NOW,
        )
        self.assertEqual(acceptance["decision"], "Accepted")
        self.assertEqual(acceptance["required_authority"], "Owner")

        import sqlite3

        with sqlite3.connect(self.runtime.path / "maestro.sqlite3") as connection:
            merges = connection.execute("SELECT COUNT(*) FROM merge_observations").fetchone()
            packet_state = connection.execute(
                "SELECT state FROM packets WHERE packet_id = 'packet-foundry-cg-m4-19'"
            ).fetchone()
        self.assertEqual(merges[0], 0)  # no automatic merge, matching M0-D10/M0-D13
        self.assertEqual(packet_state[0], "MergeReady")


if __name__ == "__main__":
    unittest.main()
