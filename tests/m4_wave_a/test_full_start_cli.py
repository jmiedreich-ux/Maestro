"""The full real "start Maestro" path, all five steps, every one a real
subprocess CLI call: register-project -> materialize-packet ->
claim-packet -> run-attempt -> development-manager-loop, ending in a
real Merged packet. The worker binary is a real subprocess stand-in
(a shell script that makes a real commit) so the path is proven
without needing Ollama installed."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m3_wave_a"))

from support import RuntimeDirectory, TemporaryProjectRepository  # noqa: E402
from test_foundry_real_registration import FOUNDRY_MANIFEST, _FOUNDRY_AUTHORITY_FILES  # noqa: E402

from maestro.config import RuntimeConfig  # noqa: E402
from maestro.operational_state import OperationalStateStore  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MAESTRO_SRC = REPO_ROOT / "services" / "maestro"

FAKE_WORKER = """#!/bin/sh
set -e
mkdir -p tests/fake
echo "// written by the real worker subprocess" > tests/fake/new.spec.ts
git add tests/fake/new.spec.ts
git commit -q -m "worker: real owned-path change"
"""


class FullStartCliTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository(manifest=FOUNDRY_MANIFEST)
        for relative, content in _FOUNDRY_AUTHORITY_FILES.items():
            target = self.repository.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.commit = self.repository.commit_all("real Foundry authority files")
        self.runtime = RuntimeDirectory()
        self.config = RuntimeConfig(self.runtime.path)
        self.runtime.path.mkdir(parents=True, exist_ok=True)
        self.worker = self.runtime.path / "fake-qwen"
        self.worker.write_text(FAKE_WORKER)
        self.worker.chmod(0o755)

    def tearDown(self):
        self.repository.close()
        self.runtime.close()

    def _cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "maestro.cli", *args, "--runtime-dir", str(self.config.runtime_dir)],
            cwd=str(MAESTRO_SRC), env={"PYTHONPATH": str(MAESTRO_SRC), "PATH": os.environ.get("PATH", "/usr/bin:/bin")},
            capture_output=True, text=True, timeout=120,
        )

    def _write(self, name: str, payload: dict) -> str:
        path = self.runtime.path / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_all_five_steps_over_the_cli_reach_a_real_merged_packet(self):
        register = self._cli("register-project", "--request", self._write("register.json", {
            "repository_path": str(self.repository.path), "commit": self.commit,
            "github_reference": "jmiedreich-ux/Foundry", "project_id": "foundry",
            "binding": {
                "binding_id": "binding-1", "binding_revision": "revision-1",
                "adapter_version": "maestro-github-adapter-v1", "process_version": "maestro-full-start-v1",
                "merge_policy": "no-automatic-merge", "acceptance_authority": "ProjectArchitect",
                "merge_execution_authority": "OwnerPerformed", "merge_delegation_reference": None,
                "binding_json": {"binding": "candidate"}, "state": "Candidate",
            },
            "graph": {"graph_projection_id": "graph-1", "graph_revision": "rev-1", "state": "Active"},
            "work_items": [{
                "work_item_id": "work-1", "architecture_node_id": "FULL-START",
                "task_reference": "jmiedreich-ux/Foundry#1", "workstream_ref": "onboarding",
                "milestone_ref": "M4", "title": "Full start test", "priority": "P1", "planned_rank": 1,
                "specialist_role": "MaestroDeveloper", "execution_classes_json": ["local-qwen"],
                "dependencies_json": [], "change_domains_json": ["tests/fake"],
                "input_contract_json": {"prerequisite": None}, "output_contract_json": {"deliverable": "fake"},
                "planning_state": "Active",
            }],
            "run": {"run_id": "run-1", "milestone_ref": "M4", "branch_name": None,
                    "pull_request_reference": None, "acceptance_boundary": "Owner"},
        }))
        self.assertEqual(register.returncode, 0, register.stderr)
        authority = json.loads(register.stdout)["binding"]["authority_reference"]

        materialize = self._cli("materialize-packet", "--request", self._write("packet.json", {
            "packet_id": "packet-1", "run_id": "run-1", "work_item_id": "work-1",
            "packet_revision": "packet-r1", "authority_reference": authority,
            "base_commit": self.commit, "current_head": None, "expected_branch": "main",
            "role_contract_reference": "AGENTS.md", "sop_reference": "AGENTS.md", "executor_class": "local-qwen",
            "integration_route": "validate-only", "reviewer_route": "independent",
            "owned_paths_json": ["tests/fake/"], "forbidden_paths_json": ["package.json"],
            "checks_json": ["true"], "resource_claims_json": ["shared:tests/fake"],
            "context_policy_json": {
                "minimum_context_tokens": 32768, "output_reserve_tokens": 8192,
                "warning_remaining_tokens": 16384, "checkpoint_remaining_tokens": 12288,
                "stop_remaining_tokens": 8192,
            },
            "state": "Planned", "correction_count": 0,
        }))
        self.assertEqual(materialize.returncode, 0, materialize.stderr)

        claim = self._cli("claim-packet", "--request", self._write("claim.json", {
            "packet_id": "packet-1",
            "lease": {"lease_id": "lease-1", "holder_id": "developer-1",
                      "executor_route": "local-qwen/developer-1",
                      "worktree_path": str(self.repository.path), "expires_in_seconds": 3600},
            "locks": [{"lock_id": "lock-1", "lock_kind": "Path", "resource_key": "shared:tests/fake"}],
            "attempt": {"attempt_id": "attempt-1", "model_identity": "qwen3.6:27b",
                        "runtime_identity": "local-qwen-ollama"},
        }))
        self.assertEqual(claim.returncode, 0, claim.stderr)
        self.assertEqual(json.loads(claim.stdout)["packet"]["state"], "Leased")

        run = self._cli("run-attempt", "--qwen-binary", str(self.worker), "--request", self._write("run.json", {
            "attempt_id": "attempt-1", "instructions": "write the test",
            "heartbeat_interval_seconds": 0.05, "poll_interval_seconds": 0.05,
        }))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["outcome"], "Succeeded")

        store = OperationalStateStore(self.config)
        for _ in range(5):
            loop = self._cli(
                "development-manager-loop", "--run-id", "run-1", "--repository", str(self.repository.path),
                "--default-branch", "main", "--reconstruction-command", "echo reconstruct",
            )
            self.assertEqual(loop.returncode, 0, loop.stderr)
            if store.snapshot("Packet", "packet-1")["state"] == "Merged":
                break

        self.assertEqual(store.snapshot("Packet", "packet-1")["state"], "Merged")


if __name__ == "__main__":
    unittest.main()
