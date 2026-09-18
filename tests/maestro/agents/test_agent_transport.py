from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from maestro.agents.preflight import (
    AdapterObservation,
    AgentRoutePreflight,
    InstalledAdapter,
)
from maestro.agents.routes import AgentRouteRegistry, RouteRequirements, ToolModelSelection
from maestro.agents.claude_transport import ClaudeTransport
from maestro.agents.codex_transport import CodexTransport
from maestro.agents.transport import (
    AgentAssignment,
    ArtifactReference,
    RegistrationResponseValidator,
    TransportError,
)
from maestro.agents.workspaces import ServiceProfileBinding, WorkspaceError, WorkspaceManager
from maestro.service.questions import LinkedQuestion


CODEX_MODEL = "openai/gpt-5.6-codex-2026-09-01"
CLAUDE_MODEL = "anthropic/claude-opus-4-1-20260805"
CAPABILITIES = ("approved_network", "code_edit", "local_command", "repository_search")


class Inspector:
    def __init__(self, provider, model, credential, settings):
        self.provider = provider
        self.model = model
        self.credential = credential
        self.settings = settings

    def inspect(self, route, configuration_hash):
        return AdapterObservation(
            True,
            "1.2.3",
            self.provider,
            (self.model,),
            (),
            CAPABILITIES,
            "cloud",
            {self.model: 131072},
            True,
            self.credential,
            self.settings,
            True,
            True,
            True,
            configuration_hash,
        )


class AgentTransportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.repository, self.commit = self._repository()
        # This executable makes the deterministic tests inspect a launch plan only.
        # A separate host check exercises real bubblewrap and is reported as UNTESTED
        # when the test host denies user namespaces.
        self.isolation_plan_only = self._script("isolation-plan-only", "#!/bin/sh\nexit 99\n")
        codex_install = self.root / "codex-install"
        codex_install.mkdir()
        self.installed_codex = self._script("codex-install/codex", "#!/bin/sh\nexit 0\n")
        self.codex_companion = self._script(
            "codex-install/codex-code-mode-host", "#!/bin/sh\nexit 0\n"
        )
        launcher_directory = self.root / "bin"
        launcher_directory.mkdir()
        self.codex_executable = launcher_directory / "codex"
        self.codex_executable.symlink_to(self.installed_codex)
        self.claude_executable = self._script("claude", "#!/bin/sh\nexit 0\n")
        self.service_home = self.root / "service-home"
        (self.service_home / ".codex").mkdir(parents=True)
        (self.service_home / ".claude").mkdir()
        for relative in (
            ".codex/auth.json",
            ".claude.json",
            ".claude/.credentials.json",
        ):
            path = self.service_home / relative
            path.touch(mode=0o600)
        registry = AgentRouteRegistry.from_mapping(
            {
                "codex": {
                    "executable": str(self.codex_executable),
                    "credential_profile": "credential-codex",
                    "settings_profile": "settings-codex",
                    "allowed_model_ids": [CODEX_MODEL],
                    "permitted_destinations": [
                        {"hostname": "chatgpt.com", "port": 443}
                    ],
                },
                "claude_code": {
                    "executable": str(self.claude_executable),
                    "credential_profile": "credential-claude",
                    "settings_profile": "settings-claude",
                    "allowed_model_ids": [CLAUDE_MODEL],
                    "permitted_destinations": [
                        {"hostname": "api.anthropic.com", "port": 443}
                    ],
                },
            }
        )
        preflight = AgentRoutePreflight(
            registry,
            {
                "codex": (
                    InstalledAdapter("codex", "openai", "cloud", CAPABILITIES),
                    Inspector("openai", CODEX_MODEL, "credential-codex", "settings-codex"),
                ),
                "claude_code": (
                    InstalledAdapter("claude_code", "anthropic", "cloud", CAPABILITIES),
                    Inspector(
                        "anthropic", CLAUDE_MODEL, "credential-claude", "settings-claude"
                    ),
                ),
            },
            credential_fingerprint=lambda reference: "1" * 64,
            settings_fingerprint=lambda reference: "2" * 64,
        )
        requirements = RouteRequirements(CAPABILITIES, ("cloud",), 32768)
        self.codex_route = preflight.resolve(
            "architect", ToolModelSelection("codex", CODEX_MODEL), requirements
        )
        self.claude_architect_route = preflight.resolve(
            "architect", ToolModelSelection("claude_code", CLAUDE_MODEL), requirements
        )
        self.claude_reviewer_route = preflight.resolve(
            "fidelity_reviewer",
            ToolModelSelection("claude_code", CLAUDE_MODEL),
            requirements,
        )
        (self.root / "workspaces").mkdir()
        self.manager = WorkspaceManager(
            self.root / "workspaces", isolation_executable=self.isolation_plan_only
        )
        self.validator = RegistrationResponseValidator()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _repository(self):
        repository = self.root / "repository"
        repository.mkdir()
        self._run(("git", "init", "--quiet", str(repository)))
        self._run(("git", "-C", str(repository), "config", "user.name", "Fixture"))
        self._run(("git", "-C", str(repository), "config", "user.email", "fixture@example.invalid"))
        (repository / "source.txt").write_text("exact source\n", encoding="utf-8")
        self._run(("git", "-C", str(repository), "add", "source.txt"))
        self._run(("git", "-C", str(repository), "commit", "--quiet", "-m", "source"))
        commit = self._run(("git", "-C", str(repository), "rev-parse", "HEAD")).stdout.strip()
        return repository, commit

    def _script(self, name, content):
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o700)
        return path

    @staticmethod
    def _run(arguments, **kwargs):
        return subprocess.run(arguments, check=True, text=True, capture_output=True, **kwargs)

    def _assignment(self, role, run_id, *, assigned_artifacts=None):
        return AgentAssignment(
            project_id="project-one",
            activity_id="activity-one",
            assignment_id=f"assignment-{run_id}",
            run_id=run_id,
            parent_assignment_id=None,
            role=role,
            role_responsibilities=("Assess exact assigned inputs.",),
            task="Return the assigned structured result.",
            source_commit=self.commit,
            decision_version="decision-one",
            instructions={
                "document_paths": ["source.txt"],
                "selected_scope": ["registered project"],
                "recorded_decisions": [],
                "relevant_answers": [],
                "outstanding_questions": [],
                "prior_findings": [],
                "candidate_refs": [],
            },
            permitted_actions=("read_source", "write_assigned_output", "ask_clarification"),
            writable_locations=("output", "scratch"),
            limits={"run_timeout_seconds": 30},
            clarification_conditions=("Required information is absent.",),
            response_schema={"type": "object", "additionalProperties": False},
            assigned_artifacts={} if assigned_artifacts is None else assigned_artifacts,
        )

    def _workspace(self, assignment, inputs=None):
        workspace_root = self.root / "workspaces"
        workspace_root.mkdir(exist_ok=True)
        return self.manager.prepare(
            project_id=assignment.project_id,
            activity_id=assignment.activity_id,
            run_id=assignment.run_id,
            source_repository=self.repository,
            source_commit=self.commit,
            assignment_bytes=assignment.to_bytes(),
            inputs={} if inputs is None else inputs,
        )

    def _profile(self, route):
        return ServiceProfileBinding(
            route.tool,
            route.credential_profile,
            route.settings_profile,
            self.service_home,
        )

    def _base_response(self, assignment, result="completed"):
        return {
            "contract_version": 1,
            "assignment_id": assignment.assignment_id,
            "run_id": assignment.run_id,
            "project_id": assignment.project_id,
            "activity_id": assignment.activity_id,
            "role": assignment.role,
            "source_commit": assignment.source_commit,
            "decision_version": assignment.decision_version,
            "result": result,
            "summary": "Completed the exact assignment.",
            "findings": [],
            "questions": [],
            "candidate": None,
            "assessment": None,
            "reviewed_assessment": None,
            "review_outcome": None,
            "failure": None,
        }

    @staticmethod
    def _reference(path, content, version="one"):
        return {
            "path": path,
            "sha256": hashlib.sha256(content).hexdigest(),
            "version": version,
        }

    def test_codex_app_server_actual_exchange_and_structured_artifacts(self) -> None:
        assignment = self._assignment("project_architect", "run-codex")
        workspace = self._workspace(assignment)
        candidate = b'{"candidate":1}\n'
        assessment = b'{"assessment":1}\n'
        response = self._base_response(assignment)
        response["candidate"] = self._reference("output/candidate.json", candidate)
        response["assessment"] = self._reference("output/assessment.json", assessment)
        self._write_codex_server(response, candidate, assessment, self.codex_route)

        conversation = CodexTransport().open(
            self.codex_route, assignment, workspace, self._profile(self.codex_route)
        )
        self.assertEqual((str(self.codex_executable), "app-server"), conversation.launch.tool_arguments)
        process = subprocess.Popen(
            conversation.launch.tool_arguments,
            cwd=conversation.launch.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None and process.stdout is not None
        for outgoing in conversation.launch.initial_stdin:
            process.stdin.write(outgoing)
        process.stdin.flush()
        while conversation.state != "completed":
            incoming = process.stdout.readline()
            if not incoming:
                self.fail(process.stderr.read().decode() if process.stderr else "Codex closed stdout")
            for outgoing in conversation.receive(incoming):
                process.stdin.write(outgoing)
            process.stdin.flush()
        process.stdin.close()
        self.assertEqual(0, process.wait(timeout=5))
        process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        validated = self.validator.validate(
            conversation.result(),
            route=self.codex_route,
            assignment=assignment,
            workspace=workspace,
            current_assignment_id=assignment.assignment_id,
            current_run_id=assignment.run_id,
        )
        self.assertEqual("completed", validated.result)
        self.assertEqual(response["candidate"]["sha256"], validated.candidate.sha256)
        self.assertIn("--tmpfs", conversation.launch.isolated_arguments)
        self.assertIn(str(self.root / "workspaces"), conversation.launch.isolated_arguments)
        self.assertNotIn(
            ("--ro-bind", "/", "/"),
            tuple(zip(
                conversation.launch.isolated_arguments,
                conversation.launch.isolated_arguments[1:],
                conversation.launch.isolated_arguments[2:],
            )),
        )
        self.assertIn(str(self.service_home / ".codex/auth.json"), conversation.launch.isolated_arguments)
        self.assertIn(str(self.codex_companion), conversation.launch.isolated_arguments)
        separator = conversation.launch.isolated_arguments.index("--")
        self.assertEqual(
            str(self.installed_codex), conversation.launch.isolated_arguments[separator + 1]
        )
        self.assertNotIn(str(self.codex_executable), conversation.launch.isolated_arguments)
        self.assertNotIn(str(self.service_home / ".claude.json"), conversation.launch.isolated_arguments)
        self.assertIn("--clearenv", conversation.launch.isolated_arguments)

    def test_claude_actual_print_mode_returns_linked_clarification(self) -> None:
        assignment = self._assignment("project_architect", "run-claude")
        workspace = self._workspace(assignment)
        response = self._base_response(assignment, "clarification_required")
        response["summary"] = "Need the publication preference."
        response["questions"] = [
            {
                "local_key": "publication",
                "subject": "Publication branch",
                "question": "Which prepared branch should be used?",
                "reason": "The supplied decision does not identify one.",
                "recipient": "owner",
                "finding_keys": [],
                "options": [
                    {
                        "local_key": "main",
                        "label": "Use main",
                        "tradeoff": "Uses the existing default branch.",
                        "recommendation_reason": "It is already protected.",
                    }
                ],
            }
        ]
        self._write_claude(response, self.claude_architect_route)
        transport = ClaudeTransport()
        launch = transport.launch(
            self.claude_architect_route,
            assignment,
            workspace,
            self._profile(self.claude_architect_route),
        )
        completed = subprocess.run(
            launch.tool_arguments,
            cwd=launch.cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        decoded = transport.decode(completed.stdout, self.claude_architect_route)
        validated = self.validator.validate(
            decoded,
            route=self.claude_architect_route,
            assignment=assignment,
            workspace=workspace,
            current_assignment_id=assignment.assignment_id,
            current_run_id=assignment.run_id,
        )
        question = validated.questions[0].to_linked_question(
            question_id="question-one", assignment=assignment, requester="registration-agent"
        )
        self.assertIsInstance(question, LinkedQuestion)
        self.assertEqual("owner", question.recipient)
        self.assertEqual("main", question.choices[0].choice_id)
        self.assertIn("--json-schema", launch.tool_arguments)
        self.assertIn("dontAsk", launch.tool_arguments)
        self.assertIn(str(self.service_home / ".claude.json"), launch.isolated_arguments)
        self.assertIn(
            str(self.service_home / ".claude/.credentials.json"), launch.isolated_arguments
        )
        self.assertNotIn(str(self.service_home / ".codex/auth.json"), launch.isolated_arguments)

    def test_profile_binding_rejects_mismatch_missing_and_unsafe_files(self) -> None:
        assignment = self._assignment("project_architect", "run-profile-rejections")
        workspace = self._workspace(assignment)
        mismatch = ServiceProfileBinding(
            "codex",
            self.codex_route.credential_profile,
            self.codex_route.settings_profile,
            self.service_home,
        )
        with self.assertRaises(TransportError) as caught:
            ClaudeTransport().launch(
                self.claude_architect_route, assignment, workspace, mismatch
            )
        self.assertEqual("profile_mismatch", caught.exception.code)

        missing_home = self.root / "missing-profile"
        missing_home.mkdir()
        missing = ServiceProfileBinding(
            "codex",
            self.codex_route.credential_profile,
            self.codex_route.settings_profile,
            missing_home,
        )
        with self.assertRaises(TransportError) as caught:
            CodexTransport().open(self.codex_route, assignment, workspace, missing)
        self.assertEqual("profile_unavailable", caught.exception.code)

        unsafe_home = self.root / "unsafe-profile"
        (unsafe_home / ".codex").mkdir(parents=True)
        unsafe_auth = unsafe_home / ".codex/auth.json"
        unsafe_auth.touch(mode=0o644)
        unsafe = ServiceProfileBinding(
            "codex",
            self.codex_route.credential_profile,
            self.codex_route.settings_profile,
            unsafe_home,
        )
        with self.assertRaises(TransportError) as caught:
            CodexTransport().open(self.codex_route, assignment, workspace, unsafe)
        self.assertEqual("unsafe_profile", caught.exception.code)

    def test_reviewer_has_separate_read_only_source_and_exact_assigned_artifacts(self) -> None:
        candidate = b'{"candidate":1}\n'
        assessment = b'{"assessment":1}\n'
        candidate_ref = ArtifactReference.from_mapping(
            self._reference("input/candidate.json", candidate), "candidate"
        )
        assessment_ref = ArtifactReference.from_mapping(
            self._reference("input/assessment.json", assessment), "reviewed_assessment"
        )
        assignment = self._assignment(
            "fidelity_reviewer",
            "run-reviewer",
            assigned_artifacts={"candidate": candidate_ref, "reviewed_assessment": assessment_ref},
        )
        workspace = self._workspace(
            assignment, {"candidate.json": candidate, "assessment.json": assessment}
        )
        response = self._base_response(assignment)
        response["candidate"] = candidate_ref.as_dict()
        response["reviewed_assessment"] = assessment_ref.as_dict()
        response["review_outcome"] = "APPROVE"
        self._write_claude(response, self.claude_reviewer_route)
        transport = ClaudeTransport()
        launch = transport.launch(
            self.claude_reviewer_route,
            assignment,
            workspace,
            self._profile(self.claude_reviewer_route),
        )
        raw = subprocess.run(
            launch.tool_arguments, cwd=launch.cwd, check=True, stdout=subprocess.PIPE
        ).stdout
        validated = self.validator.validate(
            transport.decode(raw, self.claude_reviewer_route),
            route=self.claude_reviewer_route,
            assignment=assignment,
            workspace=workspace,
            current_assignment_id=assignment.assignment_id,
            current_run_id=assignment.run_id,
        )
        self.assertEqual("APPROVE", validated.review_outcome)
        self.assertNotEqual(workspace.paths.root, self.root / "workspaces/project-one/activity-one/runs/run-codex")
        self.assertEqual(0o440, workspace.paths.input.joinpath("candidate.json").stat().st_mode & 0o777)
        input_bind = launch.isolated_arguments.index(str(workspace.paths.input))
        self.assertEqual("--ro-bind", launch.isolated_arguments[input_bind - 1])

    def test_reviewer_artifacts_reject_wrong_bytes_or_non_input_path_before_launch(self) -> None:
        candidate = b'{"candidate":1}\n'
        assessment = b'{"assessment":1}\n'
        references = {
            "candidate": ArtifactReference.from_mapping(
                self._reference("input/candidate.json", candidate), "candidate"
            ),
            "reviewed_assessment": ArtifactReference.from_mapping(
                self._reference("input/assessment.json", assessment), "reviewed_assessment"
            ),
        }

        missing_assignment = self._assignment("fidelity_reviewer", "run-reviewer-missing")
        missing_workspace = self._workspace(missing_assignment)
        with self.assertRaises(TransportError) as caught:
            ClaudeTransport().launch(
                self.claude_reviewer_route,
                missing_assignment,
                missing_workspace,
                self._profile(self.claude_reviewer_route),
            )
        self.assertEqual("invalid_assignment", caught.exception.code)

        wrong_hash_assignment = self._assignment(
            "fidelity_reviewer", "run-reviewer-wrong", assigned_artifacts=references
        )
        wrong_hash_workspace = self._workspace(
            wrong_hash_assignment,
            {"candidate.json": b"wrong bytes\n", "assessment.json": assessment},
        )
        with self.assertRaises(TransportError) as caught:
            ClaudeTransport().launch(
                self.claude_reviewer_route,
                wrong_hash_assignment,
                wrong_hash_workspace,
                self._profile(self.claude_reviewer_route),
            )
        self.assertEqual("artifact_mismatch", caught.exception.code)

        outside = dict(references)
        outside["candidate"] = ArtifactReference.from_mapping(
            self._reference("output/candidate.json", candidate), "candidate"
        )
        outside_assignment = self._assignment(
            "fidelity_reviewer", "run-reviewer-outside", assigned_artifacts=outside
        )
        outside_workspace = self._workspace(
            outside_assignment,
            {"candidate.json": candidate, "assessment.json": assessment},
        )
        with self.assertRaises(TransportError) as caught:
            ClaudeTransport().launch(
                self.claude_reviewer_route,
                outside_assignment,
                outside_workspace,
                self._profile(self.claude_reviewer_route),
            )
        self.assertEqual("artifact_out_of_scope", caught.exception.code)

    def test_malformed_stale_owner_action_and_out_of_scope_artifact_are_rejected(self) -> None:
        assignment = self._assignment("project_architect", "run-invalid")
        workspace = self._workspace(assignment)
        identity = self._identity(self.claude_architect_route)
        valid = self._base_response(assignment, "technical_failure")
        valid["failure"] = {"code": "tool", "message": "The tool failed."}
        from maestro.agents.transport import DecodedToolResult

        cases = []
        malformed = dict(valid)
        malformed["owner_action"] = "confirm_registration"
        cases.append((malformed, assignment.assignment_id, assignment.run_id, "malformed_response"))
        stale = dict(valid)
        stale["run_id"] = "older-run"
        cases.append((stale, assignment.assignment_id, assignment.run_id, "stale_response"))
        cases.append((valid, "new-assignment", assignment.run_id, "stale_assignment"))
        for payload, current_assignment, current_run, code in cases:
            with self.subTest(code=code), self.assertRaises(TransportError) as caught:
                self.validator.validate(
                    DecodedToolResult(payload, identity),
                    route=self.claude_architect_route,
                    assignment=assignment,
                    workspace=workspace,
                    current_assignment_id=current_assignment,
                    current_run_id=current_run,
                )
            self.assertEqual(code, caught.exception.code)

        source_ref = self._reference("source/source.txt", b"exact source\n")
        out_of_scope = self._base_response(assignment)
        out_of_scope["candidate"] = source_ref
        out_of_scope["assessment"] = source_ref
        with self.assertRaises(TransportError) as caught:
            self.validator.validate(
                DecodedToolResult(out_of_scope, identity),
                route=self.claude_architect_route,
                assignment=assignment,
                workspace=workspace,
                current_assignment_id=assignment.assignment_id,
                current_run_id=assignment.run_id,
            )
        self.assertEqual("artifact_out_of_scope", caught.exception.code)

    def test_forbidden_immutable_write_rejects_otherwise_valid_result(self) -> None:
        assignment = self._assignment("project_architect", "run-forbidden")
        workspace = self._workspace(assignment)
        source = workspace.paths.source / "source.txt"
        source.chmod(0o600)
        source.write_text("agent changed source\n", encoding="utf-8")
        response = self._base_response(assignment, "technical_failure")
        response["failure"] = {"code": "blocked", "message": "Could not complete."}
        from maestro.agents.transport import DecodedToolResult

        with self.assertRaises(WorkspaceError) as caught:
            workspace.verify_restrictions()
        self.assertEqual("forbidden_write", caught.exception.code)
        with self.assertRaises(TransportError) as caught:
            self.validator.validate(
                DecodedToolResult(response, self._identity(self.claude_architect_route)),
                route=self.claude_architect_route,
                assignment=assignment,
                workspace=workspace,
                current_assignment_id=assignment.assignment_id,
                current_run_id=assignment.run_id,
            )
        self.assertEqual("forbidden_write", caught.exception.code)

    @staticmethod
    def _identity(route):
        from maestro.agents.preflight import RunningToolIdentity

        return RunningToolIdentity(
            "tool_metadata",
            route.provider,
            route.requested_model_id,
            route.tool_version,
            route.configuration_hash,
        )

    def _write_claude(self, response, route):
        events = [
            {
                "type": "system",
                "subtype": "init",
                "session_id": "session-one",
                "model": route.requested_model_id,
                "claude_code_version": route.tool_version,
                "permissionMode": "dontAsk",
            },
            {"type": "result", "is_error": False, "structured_output": response},
        ]
        script = f'''#!/usr/bin/env python3
import json
events = {events!r}
for event in events:
    print(json.dumps(event, separators=(",", ":")))
'''
        self.claude_executable.write_text(script, encoding="utf-8")
        self.claude_executable.chmod(0o700)

    def _write_codex_server(self, response, candidate, assessment, route):
        source = f'''#!/usr/bin/env python3
import json
from pathlib import Path
Path("output/candidate.json").write_bytes({candidate!r})
Path("output/assessment.json").write_bytes({assessment!r})
response = {response!r}
progress = dict(response)
progress["summary"] = "Schema-constrained progress update."
for line in __import__("sys").stdin:
    message = json.loads(line)
    if message.get("method") == "initialized":
        continue
    request_id = message["id"]
    if request_id == 1:
        output = [{{"jsonrpc":"2.0","id":1,"result":{{"userAgent":"codex/{route.tool_version} (Linux)"}}}}]
    elif request_id == 2:
        output = [
            {{"method":"remoteControl/status/changed","params":{{"status":"unavailable"}}}},
            {{"id":2,"result":{{"data":[{{"id":{route.requested_model_id!r},"model":{route.requested_model_id!r}}}]}}}},
        ]
    elif request_id == 3:
        output = [{{"jsonrpc":"2.0","id":3,"result":{{"thread":{{"id":"thread-one"}},"model":{route.requested_model_id!r},"modelProvider":{route.provider!r}}}}}]
    elif request_id == 4:
        output = [
            {{"jsonrpc":"2.0","id":4,"result":{{"turn":{{"id":"turn-one"}}}}}},
            {{"jsonrpc":"2.0","method":"item/completed","params":{{"completedAtMs":1,"threadId":"thread-one","turnId":"turn-one","item":{{"id":"progress-one","type":"agentMessage","text":json.dumps(progress,separators=(",",":"))}}}}}},
            {{"jsonrpc":"2.0","method":"item/completed","params":{{"completedAtMs":1,"threadId":"thread-one","turnId":"turn-one","item":{{"id":"item-one","type":"agentMessage","text":json.dumps(response,separators=(",",":"))}}}}}},
            {{"jsonrpc":"2.0","method":"turn/completed","params":{{"threadId":"thread-one","turn":{{"id":"turn-one","status":"completed"}}}}}},
        ]
    for value in output:
        print(json.dumps(value, separators=(",", ":")), flush=True)
    if request_id == 4:
        break
'''
        self.codex_executable.write_text(source, encoding="utf-8")
        self.codex_executable.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
