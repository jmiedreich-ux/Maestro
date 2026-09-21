"""Installed registration assignment preparation and supervised tool delivery."""

from __future__ import annotations

import hashlib
import os
import stat
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path

from maestro.agents.claude_transport import ClaudeTransport
from maestro.agents.codex_transport import CodexTransport
from maestro.agents.preflight import ResolvedAgentRoute, RunningToolIdentity
from maestro.agents.supervisor import ManagedUnit, OperationIdentity
from maestro.agents.transport import (
    AgentAssignment,
    ArtifactReference as AssignedArtifactReference,
    RegistrationResponseValidator,
    decode_json_object,
)
from maestro.agents.workspaces import PreparedWorkspace, ServiceProfileBinding, WorkspaceManager
from maestro.foundation.credentials import RepositoryAuthorizer, ServiceGitTransport
from maestro.foundation.git_read import run_git
from maestro.foundation.github_destination import GitHubDestinationProvider
from maestro.planning.registration import RegistrationAssessment
from maestro.planning.registration_plugin import RegistrationServiceBinding
from maestro.planning.registration_records import ArtifactReference, RegistrationAgentResponse


_RESPONSE_SCHEMA: Mapping[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "contract_version", "assignment_id", "run_id", "project_id",
        "activity_id", "role", "source_commit", "decision_version", "result",
        "summary", "findings", "questions", "candidate", "assessment",
        "reviewed_assessment", "review_outcome", "failure",
    ],
    "properties": {
        "contract_version": {"type": "integer", "const": 1},
        "assignment_id": {"type": "string"},
        "run_id": {"type": "string"},
        "project_id": {"type": "string"},
        "activity_id": {"type": "string"},
        "role": {"type": "string", "enum": ["project_architect", "fidelity_reviewer"]},
        "source_commit": {"type": "string"},
        "decision_version": {"type": "string"},
        "result": {"type": "string", "enum": ["completed", "clarification_required", "technical_failure"]},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "object"}},
        "questions": {"type": "array", "items": {"type": "object"}},
        "candidate": {"type": ["object", "null"]},
        "assessment": {"type": ["object", "null"]},
        "reviewed_assessment": {"type": ["object", "null"]},
        "review_outcome": {"type": ["string", "null"]},
        "failure": {"type": ["object", "null"]},
    },
}


class InstalledRegistrationAgentLauncher:
    """Prepare the exact assignment and connect its tool result to registration."""

    def __init__(
        self,
        *,
        workspace_root: Path,
        source_cache_root: Path,
        service_home: Path,
        authorizer: RepositoryAuthorizer,
        transport: ServiceGitTransport,
        destination_provider: GitHubDestinationProvider,
    ) -> None:
        self.workspaces = WorkspaceManager(workspace_root)
        self.source_cache_root = _service_directory(source_cache_root)
        self.service_home = Path(service_home)
        self.authorizer = authorizer
        self.transport = transport
        self.destination_provider = destination_provider
        self.validator = RegistrationResponseValidator()
        self._failure_listener: Callable[[str, str], None] | None = None

    def connect_failure_listener(
        self, listener: Callable[[str, str], None]
    ) -> None:
        if not callable(listener):
            raise TypeError("registration assignment failure listener must be callable")
        self._failure_listener = listener

    def __call__(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        role: str,
    ) -> None:
        run, route = _run_and_route(assessment, role)
        assignment, inputs, originals = self._assignment(binding, assessment, role)
        source = self._source_repository(assessment)
        workspace = self.workspaces.prepare(
            project_id=assessment.context.project_id,
            activity_id=assessment.context.activity_id,
            run_id=run.run_id,
            source_repository=source,
            source_commit=assessment.context.source_inventory.source_commit,
            assignment_bytes=assignment.to_bytes(),
            inputs=inputs,
        )
        profile = ServiceProfileBinding(
            route.tool,
            route.credential_profile,
            route.settings_profile,
            self.service_home,
        )
        if route.tool == "codex":
            adapter: object = CodexTransport().open(route, assignment, workspace, profile)
            launch = adapter.launch
        elif route.tool == "claude_code":
            adapter = ClaudeTransport()
            launch = adapter.launch(route, assignment, workspace, profile)
        else:  # pragma: no cover - resolved routes already enforce this
            raise ValueError(f"registration tool is unsupported: {route.tool}")
        timeout = _run_timeout(assessment, role)
        identity, managed = binding.launch_agent(
            assessment.context.activity_id,
            role,
            launch.isolated_arguments,
            launch.cwd,
            timeout,
        )
        worker = threading.Thread(
            target=self._drive,
            args=(
                binding, assessment, role, route, assignment, workspace,
                identity, managed, adapter, launch.initial_stdin, originals,
            ),
            name=f"registration-{run.run_id}",
            daemon=True,
        )
        worker.start()

    def _source_repository(self, assessment: RegistrationAssessment) -> Path:
        context = assessment.context
        repository = context.package_context.source_repository
        branch = context.package_context.publication_branch
        authorization = self.authorizer.authorize(repository, branch)
        observed = self.destination_provider.authorize(repository, branch)
        self.destination_provider.require_fresh_match(observed, authorization)
        remote = self.transport.remote_for(authorization)
        target = self.source_cache_root / context.project_id / f"{context.activity_id}.git"
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if target.is_symlink():
            raise ValueError("registration source cache is unsafe")
        with self.destination_provider.bind_transport(
            observed, self.transport, authorization
        ) as bound:
            command = lambda *arguments: run_git(
                *arguments, environment=bound.environment()
            )
            if not target.exists():
                initialized = command("init", "--bare", "--quiet", str(target))
                if initialized.returncode:
                    raise ValueError("registration source cache could not be initialized")
            fetched = command(
                "-C", str(target), "fetch", "--no-tags", "--quiet", remote,
                context.source_inventory.source_commit,
            )
            checked = command(
                "-C", str(target), "cat-file", "-e",
                f"{context.source_inventory.source_commit}^{{commit}}",
            )
        if fetched.returncode or checked.returncode:
            raise ValueError("exact registration source commit is unavailable for assignment")
        return target

    def _assignment(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        role: str,
    ) -> tuple[AgentAssignment, dict[str, bytes], dict[str, ArtifactReference]]:
        context = assessment.context
        run, _route = _run_and_route(assessment, role)
        status = assessment.status
        inputs: dict[str, bytes] = {}
        assigned: dict[str, AssignedArtifactReference] = {}
        originals: dict[str, ArtifactReference] = {}
        if role == "fidelity_reviewer":
            if status.candidate is None or status.assessment is None:
                raise ValueError("review assignment has no exact architect artifacts")
            for field, original in (
                ("candidate", status.candidate),
                ("reviewed_assessment", status.assessment),
            ):
                relative = f"{field}/{Path(original.path).name}"
                content = self._artifact_bytes(assessment, original)
                inputs[relative] = content
                assigned[field] = AssignedArtifactReference(
                    f"input/{relative}", original.sha256, original.version
                )
                originals[field] = original
        relevant_answers = _answers(binding, context.activity_id)
        state = assessment.to_record()
        instructions = {
            "document_paths": [blob.path for blob in context.source_inventory.blobs],
            "selected_scope": context.selected_scope,
            "recorded_decisions": [item.to_record() for item in context.source_inventory.outcomes],
            "relevant_answers": relevant_answers,
            "outstanding_questions": [],
            "prior_findings": [
                *state.get("architect_findings", []),
                *state.get("review_findings", []),
            ],
            "candidate_refs": [
                value.as_dict()
                for value in (status.candidate, status.assessment)
                if value is not None
            ],
            "publication": {
                "repository": context.package_context.source_repository,
                "branch": context.package_context.publication_branch,
                "package_root": assessment.process_snapshot.definition["saved_outputs"]["root"],
            },
        }
        assignment = AgentAssignment(
            project_id=context.project_id,
            activity_id=context.activity_id,
            assignment_id=run.assignment_id,
            run_id=run.run_id,
            parent_assignment_id=None,
            role=role,
            role_responsibilities=(
                (
                    "Assess the exact registered source and prepare or amend the registration package.",
                    "Return only service-valid package and assessment artifacts.",
                )
                if role == "project_architect"
                else (
                    "Independently review the exact assigned candidate and assessment.",
                    "Return an approval or bounded blocking findings without amending assigned artifacts.",
                )
            ),
            task=(
                "Prepare the exact registration candidate and assessment."
                if role == "project_architect"
                else "Review the exact candidate for source and decision fidelity."
            ),
            source_commit=context.source_inventory.source_commit,
            decision_version=context.decision_version,
            instructions=instructions,
            permitted_actions=("read_source", "write_assigned_output", "ask_clarification"),
            writable_locations=("output", "scratch"),
            limits={
                "run_timeout_seconds": _run_timeout(assessment, role),
                "maximum_fidelity_reviews": context.review_limit,
            },
            clarification_conditions=(
                "Required source meaning or Owner-reserved input is absent or ambiguous.",
            ),
            response_schema=_RESPONSE_SCHEMA,
            assigned_artifacts=assigned,
        )
        return assignment, inputs, originals

    def _artifact_bytes(
        self, assessment: RegistrationAssessment, reference: ArtifactReference
    ) -> bytes:
        architect = assessment.current_run("project_architect")
        root = (
            self.workspaces.root / assessment.context.project_id
            / assessment.context.activity_id / "runs" / architect.run_id
        )
        path = root.joinpath(*Path(reference.path).parts)
        if path.is_symlink() or not path.is_file():
            raise ValueError("assigned registration artifact is unavailable")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != reference.sha256:
            raise ValueError("assigned registration artifact hash differs")
        return content

    def _drive(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        role: str,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        identity: OperationIdentity,
        managed: ManagedUnit,
        adapter: object,
        initial_stdin: tuple[bytes, ...],
        originals: Mapping[str, ArtifactReference],
    ) -> None:
        try:
            if managed.stdout is None:
                raise RuntimeError("registration tool stdout is unavailable")
            _drain_stderr(managed)
            identity_reported = False
            if route.tool == "codex":
                if managed.process is None or managed.process.stdin is None:
                    raise RuntimeError("Codex protocol input is unavailable")
                conversation = adapter
                for outgoing in initial_stdin:
                    managed.process.stdin.write(outgoing)
                managed.process.stdin.flush()
                while conversation.state != "completed":
                    incoming = managed.stdout.readline()
                    if not incoming:
                        raise RuntimeError("Codex closed before returning a complete result")
                    for outgoing in conversation.receive(incoming):
                        managed.process.stdin.write(outgoing)
                    managed.process.stdin.flush()
                decoded = conversation.result()
                binding.report_agent_identity(identity, decoded.identity)
                identity_reported = True
                managed.process.stdin.close()
            else:
                chunks: list[bytes] = []
                for line in iter(managed.stdout.readline, b""):
                    chunks.append(line)
                    if identity_reported:
                        continue
                    event = decode_json_object(line)
                    if event.get("type") == "system" and event.get("subtype") == "init":
                        model = event.get("model")
                        version = event.get("claude_code_version")
                        if not isinstance(model, str) or not isinstance(version, str):
                            raise RuntimeError("Claude startup identity is invalid")
                        binding.report_agent_identity(
                            identity,
                            RunningToolIdentity(
                                "tool_metadata", route.provider, model, version,
                                route.configuration_hash,
                            ),
                        )
                        identity_reported = True
                raw = b"".join(chunks)
                decoded = adapter.decode(raw, route)
            if not identity_reported:
                raise RuntimeError("registration tool identity was not reported while running")
            terminal = _wait_for_terminal(binding, identity)
            if terminal.state != "completed" or terminal.terminal_reason != "exit_0":
                raise RuntimeError("registration agent did not exit successfully")
            validated = self.validator.validate(
                decoded,
                route=route,
                assignment=assignment,
                workspace=workspace,
                current_assignment_id=assignment.assignment_id,
                current_run_id=assignment.run_id,
            )
            response = dict(decoded.response)
            if role == "fidelity_reviewer":
                response["candidate"] = originals["candidate"].as_dict()
                response["reviewed_assessment"] = originals[
                    "reviewed_assessment"
                ].as_dict()
            if validated.result != response["result"]:  # pragma: no cover - defensive
                raise RuntimeError("validated registration result differs")
            record = RegistrationAgentResponse.from_mapping(response)
            if role == "project_architect":
                binding.submit_architect(record)
            else:
                binding.submit_reviewer(record)
        except Exception as error:
            # The supervisor journal and preserved workspace retain exact failure
            # evidence. Recovery remains an explicit service action.
            try:
                binding.stop_agent(identity, "adapter_failure")
            except Exception:
                pass
            if self._failure_listener is not None:
                self._failure_listener(
                    assessment.context.activity_id,
                    f"{type(error).__name__}: {error}",
                )
            return


def _run_and_route(assessment: RegistrationAssessment, role: str):
    if role == "project_architect":
        return assessment.current_run(role), assessment.context.routes.architect
    if role == "fidelity_reviewer":
        return assessment.current_run(role), assessment.context.routes.fidelity_reviewer
    raise ValueError("registration role is invalid")


def _run_timeout(assessment: RegistrationAssessment, role: str) -> int:
    section = "architect" if role == "project_architect" else "fidelity_reviewer"
    value = assessment.process_snapshot.definition[section]["run_timeout_seconds"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("registration run timeout is invalid")
    return value


def _answers(
    binding: RegistrationServiceBinding, activity_id: str
) -> list[dict[str, object]]:
    with binding.database.read_connection() as connection:
        rows = connection.execute(
            """SELECT answers.question_id, answers.answer_id, answers.text,
                      answers.choice_id
               FROM service_question_answers AS answers
               WHERE answers.activity_id = ? ORDER BY answers.answered_at, answers.answer_id""",
            (activity_id,),
        ).fetchall()
    return [
        {
            "question_id": str(row[0]),
            "answer_id": str(row[1]),
            "text": str(row[2]),
            "choice_id": None if row[3] is None else str(row[3]),
        }
        for row in rows
    ]


def _wait_for_terminal(
    binding: RegistrationServiceBinding, identity: OperationIdentity
):
    while True:
        record = binding.poll_agent(identity)
        if record.state != "running":
            return record
        time.sleep(0.05)


def _drain_stderr(managed: ManagedUnit) -> None:
    if managed.stderr is None:
        return

    def drain() -> None:
        for _line in iter(managed.stderr.readline, b""):
            pass

    threading.Thread(target=drain, daemon=True).start()


def _service_directory(path: Path) -> Path:
    path = Path(path)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    details = path.lstat()
    if (
        path.is_symlink()
        or not stat.S_ISDIR(details.st_mode)
        or details.st_uid != os.getuid()
        or stat.S_IMODE(details.st_mode) & 0o077
    ):
        raise ValueError("registration source cache directory is unsafe")
    return path
