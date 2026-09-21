from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from maestro.agents.transport import AgentAssignment
from maestro.foundation import canonical_json
from maestro.service.registration_runner import run


class DurableRegistrationRunnerTest(unittest.TestCase):
    def test_runner_persists_numbered_protocol_events_identity_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            workspace.mkdir()
            response = {
                "contract_version": 1,
                "assignment_id": "assignment-one",
                "run_id": "run-one",
                "project_id": "project-one",
                "activity_id": "activity-one",
                "role": "project_architect",
                "source_commit": "a" * 40,
                "decision_version": "decision-one",
                "result": "technical_failure",
                "summary": "The isolated fixture reported a bounded failure.",
                "findings": [],
                "questions": [],
                "candidate": None,
                "assessment": None,
                "reviewed_assessment": None,
                "review_outcome": None,
                "failure": {"code": "temporary_fixture", "message": "fixture"},
            }
            events = [
                {
                    "type": "system", "subtype": "init", "session_id": "session-one",
                    "model": "anthropic/model-one", "claude_code_version": "1.2.3",
                },
                {"type": "result", "is_error": False, "structured_output": response},
            ]
            script = (
                "import json; events=" + repr(events)
                + "; [print(json.dumps(item), flush=True) for item in events]"
            )
            assignment = AgentAssignment(
                "project-one", "activity-one", "assignment-one", "run-one", None,
                "project_architect", ("Assess source.",), "Assess source.",
                "a" * 40, "decision-one", {}, ("read_source",),
                ("output", "scratch"), {"run_timeout_seconds": 10},
                ("Ask when blocked.",), {"type": "object"},
            )
            event_path = root / "events.jsonl"
            result_path = root / "result.json"
            plan = {
                "route": {
                    "role": "architect", "tool": "claude_code",
                    "requested_model_id": "anthropic/model-one",
                    "provider": "anthropic", "tool_version": "1.2.3",
                    "executable": "/usr/bin/python3",
                    "credential_profile": "credential", "settings_profile": "settings",
                    "location": "cloud", "capabilities": ["code_edit"],
                    "context_limit_tokens": 65536, "permitted_destinations": [],
                    "configuration_hash": "b" * 64,
                },
                "assignment": assignment.as_dict(),
                "workspace": {
                    "project_id": "project-one", "activity_id": "activity-one",
                    "run_id": "run-one", "source_commit": "a" * 40,
                    "root": str(workspace), "assignment_sha256": "c" * 64,
                    "isolation_executable": "/usr/bin/true",
                    "workspace_root": str(root),
                },
                "command": ["/usr/bin/python3", "-c", script],
                "cwd": str(workspace), "initial_stdin": [],
                "event_path": str(event_path), "result_path": str(result_path),
            }
            plan_path = root / "plan.json"
            plan_path.write_text(canonical_json(plan), encoding="utf-8")

            self.assertEqual(0, run(plan_path))
            saved_events = [
                json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                list(range(1, len(saved_events) + 1)),
                [item["sequence"] for item in saved_events],
            )
            self.assertIn("runtime_identity", [item["kind"] for item in saved_events])
            saved_result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(response, saved_result["response"])
            self.assertEqual("anthropic/model-one", saved_result["identity"]["model_id"])


if __name__ == "__main__":
    unittest.main()
