"""The real "start Maestro" path: `register-project` then
`materialize-packet`, both as real subprocess CLI calls against a real
git repository -- the two steps that had no command at all before this."""

from __future__ import annotations

import json
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


class ProjectOnboardingCliTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository(manifest=FOUNDRY_MANIFEST)
        for relative, content in _FOUNDRY_AUTHORITY_FILES.items():
            target = self.repository.path / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.commit = self.repository.commit_all("real Foundry authority files")

        self.runtime = RuntimeDirectory()
        self.config = RuntimeConfig(self.runtime.path)

    def tearDown(self):
        self.repository.close()
        self.runtime.close()

    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "maestro.cli", *args],
            cwd=str(MAESTRO_SRC), env={"PYTHONPATH": str(MAESTRO_SRC), "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True, timeout=60,
        )

    def test_register_then_materialize_reaches_a_real_dispatchable_packet(self):
        registration_request = {
            "repository_path": str(self.repository.path), "commit": self.commit,
            "github_reference": "jmiedreich-ux/Foundry", "project_id": "foundry",
            "binding": {
                "binding_id": "binding-1", "binding_revision": "revision-1",
                "adapter_version": "maestro-github-adapter-v1", "process_version": "maestro-onboarding-cli-v1",
                "merge_policy": "no-automatic-merge", "acceptance_authority": "ProjectArchitect",
                "merge_execution_authority": "OwnerPerformed", "merge_delegation_reference": None,
                "binding_json": {"binding": "candidate"}, "state": "Candidate",
            },
            "graph": {"graph_projection_id": "graph-1", "graph_revision": "rev-1", "state": "Active"},
            "work_items": [
                {
                    "work_item_id": "work-1", "architecture_node_id": "ONBOARD-TEST",
                    "task_reference": "jmiedreich-ux/Foundry#1", "workstream_ref": "onboarding",
                    "milestone_ref": "M4", "title": "Onboarding CLI test fixture", "priority": "P1",
                    "planned_rank": 1, "specialist_role": "MaestroDeveloper",
                    "execution_classes_json": ["local-qwen"], "dependencies_json": [],
                    "change_domains_json": ["tests/fake"], "input_contract_json": {"prerequisite": None},
                    "output_contract_json": {"deliverable": "fake"}, "planning_state": "Active",
                }
            ],
            "run": {
                "run_id": "run-1", "milestone_ref": "M4", "branch_name": None,
                "pull_request_reference": None, "acceptance_boundary": "Owner",
            },
        }
        registration_path = self.runtime.path / "register.json"
        registration_path.parent.mkdir(parents=True, exist_ok=True)
        registration_path.write_text(json.dumps(registration_request), encoding="utf-8")

        register_result = self._run(
            "register-project", "--request", str(registration_path),
            "--runtime-dir", str(self.config.runtime_dir),
        )
        self.assertEqual(register_result.returncode, 0, register_result.stderr)
        registered = json.loads(register_result.stdout)
        self.assertEqual(registered["run"]["state"], "Planned")

        context_policy = {
            "minimum_context_tokens": 32768, "output_reserve_tokens": 8192,
            "warning_remaining_tokens": 16384, "checkpoint_remaining_tokens": 12288,
            "stop_remaining_tokens": 8192,
        }
        packet_request = {
            "packet_id": "packet-1", "run_id": "run-1", "work_item_id": "work-1",
            "packet_revision": "packet-r1", "authority_reference": registered["binding"]["authority_reference"],
            "base_commit": self.commit, "current_head": None, "expected_branch": "codex/onboarding-test",
            "role_contract_reference": "AGENTS.md", "sop_reference": "AGENTS.md", "executor_class": "local-qwen",
            "integration_route": "validate-only", "reviewer_route": "independent",
            "owned_paths_json": ["tests/fake/"], "forbidden_paths_json": ["package.json"],
            "checks_json": ["true"], "resource_claims_json": ["shared:tests/fake"],
            "context_policy_json": context_policy, "state": "Planned", "correction_count": 0,
        }
        packet_path = self.runtime.path / "packet.json"
        packet_path.write_text(json.dumps(packet_request), encoding="utf-8")

        materialize_result = self._run(
            "materialize-packet", "--request", str(packet_path),
            "--runtime-dir", str(self.config.runtime_dir),
        )
        self.assertEqual(materialize_result.returncode, 0, materialize_result.stderr)
        materialized = json.loads(materialize_result.stdout)
        self.assertEqual(materialized["state"], "Dispatchable")

        store = OperationalStateStore(self.config)
        stored = store.snapshot("Packet", "packet-1")
        self.assertEqual(stored["state"], "Dispatchable")


if __name__ == "__main__":
    unittest.main()
