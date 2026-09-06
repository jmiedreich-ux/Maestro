"""M3 Wave B (B1-B3) — real graph node ingestion and packet materialization,
proven end to end against Foundry's real next unclaimed work item.

CG-M4-19 ("Add Menu browser checks") was confirmed genuinely unclaimed live
this session via the real GitHub API:
- Issue #6 checklist: `- [ ] CG-M4-19 · Add Menu browser checks. — Qwen (local)`
  (unchecked; compare CG-M4-05, CG-M4-11, both `[x]`).
- tracker/assignments.json: no entry for CG-M4-19 at all.
- docs/features/control-gallery/milestones/m4.md's own table (real, fetched
  live): `CG-M4-19 | Menu specifications | tests/overlays/menu/** | M4-15 |
  Menu keyboard, dismissal, and recovery checks.`
- PROJECT_STATUS.md's own real text: "Resume at CG-M4-19 only" — the
  project's own stated next action, not a resumption of the active Popover
  packet the M0-D10 selection rule explicitly excludes.

This is M0-D10's real selection rule (one unclaimed, explicitly released
packet) applied for real, chaining every real fact this session already
gathered (A1 discovery, A2 registration, A3 dry run) into one real,
materialized packet — using only already-existing, already-tested M1
storage commands (record_graph_projection, create_run, materialize_packet),
none of them modified, all of them previously uncalled by anything real.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m3_wave_a"))

from support import RuntimeDirectory, TemporaryProjectRepository  # noqa: E402
from test_foundry_real_registration import (  # noqa: E402
    FOUNDRY_MANIFEST,
    _FOUNDRY_AUTHORITY_FILES,
)

from maestro.config import RuntimeConfig  # noqa: E402
from maestro.operational_state import Actor, OperationalStateStore  # noqa: E402
from maestro.project_authority import ProjectAuthorityLoader  # noqa: E402

ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
NOW = "2026-09-06T18:00:00.000000Z"

# Foundry's real current HEAD at the time of this session's investigation
# (confirmed via `git rev-parse HEAD` against a live clone, and via the
# GitHub API's own commits endpoint).
FOUNDRY_REAL_HEAD = "5e01f5a0d02c78ced41a915042b49dd8ffd666c9"

# Real milestones.md content (docs/features/control-gallery/milestones/m4.md
# table row), sha256'd here as a real, reproducible source_hash rather than
# a fabricated digest.
_MILESTONES_M4_TABLE_ROW = (
    "| CG-M4-19 | Menu specifications | `tests/overlays/menu/**` | M4-15 | "
    "Menu keyboard, dismissal, and recovery checks. |"
)

# AGENTS.md "Shared-file and agent safety": "The coordinator owns contracts,
# package configuration, shared fixtures, workflows, tracker, status, and
# handoff." — the same real, cited list already used as
# operations.resource_locks in FOUNDRY_MANIFEST; reused here as the real
# forbidden-paths boundary for this packet.
FOUNDRY_COORDINATOR_OWNED_PATHS = sorted([
    "package.json", "package-lock.json", "tsconfig.json", "playwright.config.ts",
    "vite.config.ts", ".github", "tracker", "PROJECT_STATUS.md", "ai/handoffs/current.md",
])

CONTEXT_POLICY = {
    "minimum_context_tokens": 32768,
    "output_reserve_tokens": 8192,
    "warning_remaining_tokens": 16384,
    "checkpoint_remaining_tokens": 12288,
    "stop_remaining_tokens": 8192,
}


class FoundryRealPacketMaterializationTests(unittest.TestCase):
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

        # A1/A2: real discovery + real registration, chained exactly as
        # Wave A already proved.
        loader = ProjectAuthorityLoader(self.foundation)
        self.load_result = loader.load(self.repository.path, self.commit, "jmiedreich-ux/Foundry")
        self.assertEqual(self.load_result.disposition, "Reviewable")

        self.store.record_binding(
            {
                "binding_id": "binding-foundry-1",
                "project_id": "foundry",
                "binding_revision": "revision-1",
                "source_commit": self.load_result.source_commit,
                "manifest_digest": self.load_result.manifest_digest,
                "adapter_version": "maestro-github-adapter-v1",
                "process_version": "maestro-m3-a1-process-v1",
                "authority_reference": self.load_result.request_id,
                "merge_policy": "no-automatic-merge",
                "acceptance_authority": "ProjectArchitect",
                "merge_execution_authority": "OwnerPerformed",
                "merge_delegation_reference": None,
                "binding_json": {"binding": "candidate"},
                "state": "Candidate",
                "activated_at": None,
                "superseded_at": None,
            },
            "command-binding-foundry-1",
            ACTOR,
            NOW,
        )
        # A4: real Candidate -> Registered promotion.
        registration = self.foundation.register_project("foundry", "binding-foundry-1")
        self.assertTrue(registration.applied)

    def tearDown(self):
        self.runtime.close()
        self.repository.close()

    def _materialize_cg_m4_19(self):
        graph_result = self.store.record_graph_projection(
            {
                "graph_projection_id": "graph-foundry-cg-m4",
                "project_id": "foundry",
                "binding_id": "binding-foundry-1",
                "graph_revision": "cg-m4-2026-09-06",
                "authority_reference": self.load_result.request_id,
                "source_base_sha": FOUNDRY_REAL_HEAD,
                "source_hash": hashlib.sha256(_MILESTONES_M4_TABLE_ROW.encode()).hexdigest(),
                "state": "Active",
                "observed_at": NOW,
            },
            [
                {
                    "work_item_id": "work-cg-m4-19",
                    "graph_projection_id": "graph-foundry-cg-m4",
                    # Real, cited stable ID: docs/features/control-gallery/
                    # milestones/m4.md's own table + issue #6's own checklist,
                    # both fetched live this session.
                    "architecture_node_id": "CG-M4-19",
                    "task_reference": "jmiedreich-ux/Foundry#6",
                    "workstream_ref": "control-gallery",
                    "milestone_ref": "M4",
                    "title": "Add Menu browser checks",
                    "priority": "P1",
                    "planned_rank": 1,
                    "specialist_role": "MaestroDeveloper",
                    "execution_classes_json": ["local-qwen"],
                    "dependencies_json": ["CG-M4-15"],
                    "change_domains_json": ["tests/overlays/menu"],
                    "input_contract_json": {"prerequisite": "CG-M4-15 merged"},
                    "output_contract_json": {
                        "deliverable": "tests/overlays/menu/** browser checks, PASS/UNTESTED per assertion"
                    },
                    "planning_state": "Active",
                },
            ],
            "command-graph-foundry-1",
            ACTOR,
            NOW,
        )

        run = self.store.create_run(
            {
                "run_id": "run-foundry-cg-m4-19",
                "run_fingerprint": hashlib.sha256(b"run-foundry-cg-m4-19").hexdigest(),
                "project_id": "foundry",
                "binding_id": "binding-foundry-1",
                "graph_projection_id": "graph-foundry-cg-m4",
                "milestone_ref": "M4",
                "approved_authority_reference": self.load_result.request_id,
                "branch_name": None,
                "pull_request_reference": None,
                "current_head": None,
                "current_head_source_reference": None,
                "candidate_head": None,
                "candidate_head_source_reference": None,
                "state": "Planned",
                "acceptance_boundary": "ProjectArchitect",
            },
            "command-run-foundry-cg-m4-19",
            ACTOR,
            NOW,
        )

        packet = self.store.materialize_packet(
            {
                "packet_id": "packet-foundry-cg-m4-19",
                "run_id": "run-foundry-cg-m4-19",
                "work_item_id": "work-cg-m4-19",
                "packet_revision": "packet-r1",
                "authority_reference": self.load_result.request_id,
                "base_commit": FOUNDRY_REAL_HEAD,
                "current_head": None,
                # Matches Foundry's own real precedent naming
                # (codex/m4-18-popover-browser-checks, merged PR #56).
                "expected_branch": "codex/m4-19-menu-browser-checks",
                "role_contract_reference": "AGENTS.md",
                "sop_reference": "AGENTS.md",
                "executor_class": "local-qwen",
                "integration_route": "validate-only",
                "reviewer_route": "independent",
                "owned_paths_json": ["tests/overlays/menu"],
                "forbidden_paths_json": FOUNDRY_COORDINATOR_OWNED_PATHS,
                # Foundry's real declared gates (A3: all confirmed passing
                # live against this exact commit this session).
                "checks_json": [
                    "npm run check", "npm run build", "npm run test:foundation", "npm run test:browser",
                ],
                "resource_claims_json": ["shared:tests/overlays/menu"],
                "context_policy_json": CONTEXT_POLICY,
                "state": "Planned",
                "correction_count": 0,
            },
            "command-packet-foundry-cg-m4-19",
            ACTOR,
            NOW,
        )
        return graph_result, run, packet

    def test_real_graph_projection_and_work_item_are_recorded(self):
        graph_result, _run, _packet = self._materialize_cg_m4_19()
        self.assertEqual(graph_result["graph"]["state"], "Active")
        self.assertEqual(len(graph_result["work_items"]), 1)
        self.assertEqual(graph_result["work_items"][0]["architecture_node_id"], "CG-M4-19")
        self.assertEqual(graph_result["work_items"][0]["title"], "Add Menu browser checks")

    def test_real_run_is_planned_against_the_real_registered_project(self):
        _graph_result, run, _packet = self._materialize_cg_m4_19()
        self.assertEqual(run["state"], "Planned")
        self.assertEqual(run["project_id"], "foundry")
        self.assertEqual(run["binding_id"], "binding-foundry-1")

    def test_real_packet_is_materialized_planned_with_foundrys_real_gates(self):
        _graph_result, _run, packet = self._materialize_cg_m4_19()
        self.assertEqual(packet["state"], "Planned")
        self.assertEqual(packet["correction_count"], 0)
        self.assertEqual(packet["base_commit"], FOUNDRY_REAL_HEAD)
        self.assertEqual(packet["owned_paths_json"], ["tests/overlays/menu"])
        self.assertEqual(
            packet["checks_json"],
            ["npm run check", "npm run build", "npm run test:foundation", "npm run test:browser"],
        )

    def test_full_chain_is_durable_across_a_fresh_read(self):
        self._materialize_cg_m4_19()

        import sqlite3

        with sqlite3.connect(self.runtime.path / "maestro.sqlite3") as connection:
            row = connection.execute(
                "SELECT packet_id, work_item_id, run_id, state FROM packets WHERE packet_id = ?",
                ("packet-foundry-cg-m4-19",),
            ).fetchone()
        self.assertEqual(row, ("packet-foundry-cg-m4-19", "work-cg-m4-19", "run-foundry-cg-m4-19", "Planned"))


if __name__ == "__main__":
    unittest.main()
