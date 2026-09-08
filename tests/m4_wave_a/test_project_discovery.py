"""The real M0-D02 discovery pass: read a real repository, report what
is genuinely there, and name exactly what the Architect still owes."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "m1_01"))

from support import TemporaryProjectRepository, run_git  # noqa: E402

from maestro.project_discovery import discover_project, observe_repository  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
MAESTRO_SRC = REPO_ROOT / "services" / "maestro"

ARCHITECT_OVERLAY = {
    "identity": {"adapter_version": "maestro-github-adapter-v1", "process_version": "maestro-m4-v1"},
    "delivery": {
        "branch_pr_merge_policy": "no-automatic-merge",
        "owner_acceptance_policy": "architect-accepts-when-checks-pass",
        "deployment_rollback_policy": "manual",
    },
    "verification": {
        "integration_commands": [], "ui_qa_commands": [],
        "evidence_rules": "commit sha plus check output",
        "untested_handling": "report UNTESTED honestly",
    },
    "roles": {
        "specialist_overlays": ["MaestroDeveloper"], "reviewer_route": "independent",
        "qa_murphy_policy": "none", "local_cloud_eligibility": "local-qwen",
    },
    "operations": {
        "environment_reference_names": [], "secret_reference_names": [],
        "resource_locks": [], "notification_policy": "local-durable",
    },
    "exceptions": {"disposition": "none", "items": []},
}


class ProjectDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.repository = TemporaryProjectRepository()

    def tearDown(self):
        self.repository.close()

    def test_it_observes_only_real_facts_and_names_every_missing_leaf(self):
        result = discover_project(self.repository.path, "janedoe/bookshelf")

        identity = result["inventory"]["areas"]["identity"]
        self.assertEqual(identity["repository_identifier"]["value"], "janedoe/bookshelf")
        self.assertEqual(identity["project_name"]["value"], "bookshelf")
        self.assertEqual(identity["default_branch"]["value"], "main")
        # Maestro-side facts are not observable in the repo -- honestly missing.
        self.assertEqual(identity["adapter_version"]["status"], "missing")

        # The fixture repo really does carry these authority files.
        authority = result["inventory"]["areas"]["authority"]
        self.assertEqual(authority["rules_sop_path"]["value"], "AGENTS.md")
        self.assertEqual(authority["handoff_path"]["value"], "ai/handoffs/current.md")

        self.assertIsNone(result["proposed_binding"])
        self.assertIn("identity.adapter_version", result["architect_worklist"])
        self.assertIn("delivery.owner_acceptance_policy", result["architect_worklist"])

    def test_real_declared_npm_scripts_are_read_as_facts_not_guesses(self):
        (self.repository.path / "package.json").write_text(
            json.dumps({"scripts": {"build": "vite build", "test": "vitest run"}}), encoding="utf-8"
        )
        self.repository.commit_all("add package.json")

        snapshot = observe_repository(self.repository.path, "janedoe/bookshelf")
        self.assertEqual(snapshot["verification"]["test_commands"], ["npm test"])
        self.assertEqual(snapshot["verification"]["build_commands"], ["npm run build"])
        # Nothing declares an e2e script, so nothing is invented.
        self.assertNotIn("ui_qa_commands", snapshot["verification"])

    def test_the_architect_overlay_completes_it_into_a_real_proposed_binding(self):
        (self.repository.path / "package.json").write_text(
            json.dumps({"scripts": {"build": "vite build", "test": "vitest run"}}), encoding="utf-8"
        )
        self.repository.commit_all("add package.json")

        overlay = {**ARCHITECT_OVERLAY}
        overlay["authority"] = {"task_issue_conventions": "GitHub issues, one packet per issue"}
        result = discover_project(self.repository.path, "janedoe/bookshelf", overlay)

        self.assertEqual(result["architect_worklist"], [])
        self.assertIsNone(result["escalation_reason"])
        binding = result["proposed_binding"]
        self.assertIsNotNone(binding)
        self.assertEqual(binding["identity"]["repository_identifier"], "janedoe/bookshelf")
        self.assertEqual(binding["verification"]["test_commands"], ["npm test"])
        self.assertEqual(binding["authority"]["rules_sop_path"], "AGENTS.md")

    def test_it_runs_as_a_real_cli_command(self):
        result = subprocess.run(
            [
                sys.executable, "-m", "maestro.cli", "discover-project",
                "--repository", str(self.repository.path),
                "--github-reference", "janedoe/bookshelf",
            ],
            cwd=str(MAESTRO_SRC), env={"PYTHONPATH": str(MAESTRO_SRC), "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIsNone(payload["proposed_binding"])
        self.assertTrue(payload["architect_worklist"])

    def test_a_directory_that_is_not_a_git_worktree_is_rejected_honestly(self):
        from maestro.project_discovery import DiscoveryError

        with self.assertRaises(DiscoveryError):
            observe_repository(Path("/tmp"), "janedoe/bookshelf")


if __name__ == "__main__":
    unittest.main()
