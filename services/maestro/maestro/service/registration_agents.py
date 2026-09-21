"""Installed registration assignment preparation and supervised tool delivery."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import threading
import time
from collections.abc import Callable, Mapping
from importlib import resources
from pathlib import Path, PurePosixPath

from maestro.agents.claude_transport import ClaudeTransport
from maestro.agents.codex_transport import CodexTransport
from maestro.agents.preflight import ResolvedAgentRoute, RunningToolIdentity
from maestro.agents.supervisor import ManagedUnit, OperationIdentity, SupervisionError
from maestro.agents.transport import (
    AgentAssignment,
    ArtifactReference as AssignedArtifactReference,
    DecodedToolResult,
    RegistrationResponseValidator,
    TransportError,
)
from maestro.agents.workspaces import PreparedWorkspace, ServiceProfileBinding, WorkspaceManager
from maestro.foundation.credentials import RepositoryAuthorizer, ServiceGitTransport
from maestro.foundation.git_read import run_git
from maestro.foundation.github_destination import (
    GitHubDestination,
    GitHubDestinationProvider,
    GitHubDestinationRouter,
    destination_provider_for,
)
from maestro.planning.registration import RegistrationAssessment
from maestro.planning.registration_plugin import RegistrationServiceBinding
from maestro.planning.registration_records import ArtifactReference, RegistrationAgentResponse
from maestro.foundation import canonical_json


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
        destination_provider: GitHubDestination,
    ) -> None:
        self.workspaces = WorkspaceManager(workspace_root)
        self.source_cache_root = _service_directory(source_cache_root)
        self.runner_root = _service_directory(source_cache_root.parent / "registration-runs")
        self.service_home = Path(service_home)
        self.authorizer = authorizer
        self.transport = transport
        if not isinstance(
            destination_provider, (GitHubDestinationProvider, GitHubDestinationRouter)
        ):
            raise TypeError("registration launcher requires a GitHub destination provider")
        self.destination_provider = destination_provider
        self.validator = RegistrationResponseValidator()
        self._failure_listener: (
            Callable[[str, str, str, str, str, bool], None] | None
        ) = None

    def connect_failure_listener(
        self, listener: Callable[[str, str, str, str, str, bool], None]
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
        runner_directory = self.runner_root / run.run_id
        runner_directory.mkdir(mode=0o700)
        plan_path = runner_directory / "plan.json"
        event_path = runner_directory / "events.jsonl"
        result_path = runner_directory / "result.json"
        plan = {
            "route": _route_mapping(route),
            "assignment": assignment.as_dict(),
            "workspace": _workspace_mapping(workspace),
            "command": list(launch.isolated_arguments),
            "cwd": launch.cwd,
            "initial_stdin": [value.decode("utf-8") for value in launch.initial_stdin],
            "event_path": str(event_path),
            "result_path": str(result_path),
        }
        _write_service_file(plan_path, canonical_json(plan).encode("utf-8"))
        identity, managed = binding.launch_agent(
            assessment.context.activity_id,
            role,
            (
                str(Path(sys.executable).resolve()), "-m",
                "maestro.service.registration_runner", str(plan_path),
            ),
            launch.cwd,
            timeout,
        )
        worker = threading.Thread(
            target=self._drive_runner,
            args=(
                binding, assessment, role, route, assignment, workspace,
                identity, managed, event_path, result_path, originals,
            ),
            name=f"registration-{run.run_id}",
            daemon=True,
        )
        worker.start()

    def resume(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        role: str,
    ) -> None:
        """Resume a saved runner by replaying only its service-owned files."""
        run, route = _run_and_route(assessment, role)
        assignment, _inputs, originals = self._assignment(binding, assessment, role)
        workspace = self.workspaces.open_existing(
            project_id=assessment.context.project_id,
            activity_id=assessment.context.activity_id,
            run_id=run.run_id,
            source_commit=assessment.context.source_inventory.source_commit,
            assignment_bytes=assignment.to_bytes(),
        )
        identity = binding.current_operation(assessment, role)
        runner_directory = self.runner_root / run.run_id
        worker = threading.Thread(
            target=self._drive_runner,
            args=(
                binding, assessment, role, route, assignment, workspace, identity,
                None, runner_directory / "events.jsonl",
                runner_directory / "result.json", originals,
            ),
            name=f"registration-resume-{run.run_id}", daemon=True,
        )
        worker.start()

    def _drive_runner(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        role: str,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        identity: OperationIdentity,
        _managed: ManagedUnit | None,
        event_path: Path,
        result_path: Path,
        originals: Mapping[str, ArtifactReference],
    ) -> None:
        try:
            reported = binding.has_saved_agent_identity(assessment, role)
            recorded_runner_sequences = _recorded_runner_sequences(
                binding.poll_agent(identity)
            )
            while True:
                if event_path.exists():
                    for line in event_path.read_text(encoding="utf-8").splitlines():
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        sequence = int(event["sequence"])
                        if sequence in recorded_runner_sequences:
                            continue
                        recorded_runner_sequences.add(sequence)
                        try:
                            binding.record_agent_protocol_event(
                                identity, "stdout",
                                (canonical_json(event) + "\n").encode("utf-8"),
                            )
                        except SupervisionError as error:
                            if error.code != "protocol_event_rejected":
                                raise
                        if event["kind"] == "runtime_identity" and not reported:
                            binding.restore_agent_identity_reservation(identity, route)
                            tool_identity = RunningToolIdentity(**event["identity"])
                            try:
                                binding.report_agent_identity(identity, tool_identity)
                            except SupervisionError as error:
                                if error.code != "runtime_identity_unconfirmed":
                                    raise
                                reconciled = binding.poll_agent(identity)
                                if reconciled.state != "completed":
                                    raise
                                binding.report_agent_identity(identity, tool_identity)
                            reported = True
                terminal = binding.poll_agent(identity)
                if terminal.state != "running":
                    break
                time.sleep(0.05)
            if terminal.state != "completed" or terminal.terminal_reason != "exit_0":
                raise RuntimeError("registration runner did not exit successfully")
            if not result_path.is_file() or result_path.is_symlink():
                raise RuntimeError("registration runner result is unavailable")
            value = json.loads(result_path.read_text(encoding="utf-8"))
            decoded = DecodedToolResult(
                value["response"], RunningToolIdentity(**value["identity"])
            )
            if not reported:
                binding.restore_agent_identity_reservation(identity, route)
                try:
                    binding.report_agent_identity(identity, decoded.identity)
                except SupervisionError as error:
                    if error.code != "runtime_identity_unconfirmed":
                        raise
                    reconciled = binding.poll_agent(identity)
                    if reconciled.state != "completed":
                        raise
                    binding.report_agent_identity(identity, decoded.identity)
            self._accept_decoded(
                binding, assessment, role, route, assignment, workspace,
                decoded, originals,
            )
        except Exception as error:
            try:
                binding.stop_agent(identity, "adapter_failure")
            except Exception:
                pass
            if self._failure_listener is not None:
                self._failure_listener(
                    assessment.context.activity_id, role, assignment.assignment_id,
                    assignment.run_id, f"{type(error).__name__}: {error}",
                    isinstance(error, (OSError, TransportError, RuntimeError)),
                )

    def _accept_decoded(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        role: str,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        decoded: object,
        originals: Mapping[str, ArtifactReference],
    ) -> None:
        validated = self.validator.validate(
            decoded, route=route, assignment=assignment, workspace=workspace,
            current_assignment_id=assignment.assignment_id,
            current_run_id=assignment.run_id,
        )
        response = dict(decoded.response)
        if role == "fidelity_reviewer":
            response["candidate"] = originals["candidate"].as_dict()
            response["reviewed_assessment"] = originals["reviewed_assessment"].as_dict()
        if validated.result != response["result"]:
            raise RuntimeError("validated registration result differs")
        record = RegistrationAgentResponse.from_mapping(response)
        if role == "project_architect":
            binding.submit_architect(record)
        else:
            binding.submit_reviewer(record)
        if record.result == "technical_failure" and self._failure_listener is not None:
            assert record.failure is not None
            self._failure_listener(
                assessment.context.activity_id, role, assignment.assignment_id,
                assignment.run_id,
                f"{record.failure['code']}: {record.failure['message']}",
                _retryable_failure_code(str(record.failure["code"])),
            )

    def _source_repository(self, assessment: RegistrationAssessment) -> Path:
        context = assessment.context
        repository = context.package_context.source_repository
        branch = context.package_context.publication_branch
        configured_provider = destination_provider_for(
            self.destination_provider, repository
        )
        configured_snapshot_reference = hashlib.sha256(
            canonical_json(
                configured_provider.profile.snapshot(repository, branch)
            ).encode("utf-8")
        ).hexdigest()
        if (
            configured_snapshot_reference
            != context.package_context.destination_snapshot_reference
        ):
            raise ValueError(
                "repository profile changed since registration intake; "
                "assignment source access is paused"
            )
        authorization = self.authorizer.authorize(repository, branch)
        observed = self.destination_provider.authorize(repository, branch)
        self.destination_provider.require_fresh_match(observed, authorization)
        observed_snapshot_reference = hashlib.sha256(
            canonical_json(dict(observed.snapshot)).encode("utf-8")
        ).hexdigest()
        if (
            observed_snapshot_reference
            != context.package_context.destination_snapshot_reference
        ):
            raise ValueError("live repository profile differs from its saved intake snapshot")
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
                initialized = command("init", "--quiet", str(target))
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
        lineage = binding.assignment_lineage(assessment, role)
        inputs: dict[str, bytes] = {}
        contract_relative = "contract/registration-package-v1.json"
        inputs[contract_relative] = _registration_package_contract()
        assigned: dict[str, AssignedArtifactReference] = {}
        originals: dict[str, ArtifactReference] = {}
        if role == "fidelity_reviewer":
            if status.candidate is None or status.assessment is None:
                raise ValueError("review assignment has no exact architect artifacts")
            original = status.candidate
            manifest_relative = self._stage_candidate(
                binding, assessment, original, "candidate", inputs
            )
            assigned["candidate"] = AssignedArtifactReference(
                f"input/{manifest_relative}", original.sha256, original.version
            )
            originals["candidate"] = original
            original = status.assessment
            relative = f"reviewed_assessment/{Path(original.path).name}"
            inputs[relative] = self._artifact_bytes(binding, assessment, original)
            assigned["reviewed_assessment"] = AssignedArtifactReference(
                f"input/{relative}", original.sha256, original.version
            )
            originals["reviewed_assessment"] = original
        elif (
            lineage["parent_assignment_id"] is not None
            and status.candidate is not None
            and status.assessment is not None
        ):
            original = status.candidate
            manifest_relative = self._stage_candidate(
                binding, assessment, original, "prior_candidate", inputs
            )
            assigned["prior_candidate"] = AssignedArtifactReference(
                f"input/{manifest_relative}", original.sha256, original.version
            )
            originals["prior_candidate"] = original
            original = status.assessment
            relative = f"prior_assessment/{Path(original.path).name}"
            inputs[relative] = self._artifact_bytes(binding, assessment, original)
            assigned["prior_assessment"] = AssignedArtifactReference(
                f"input/{relative}", original.sha256, original.version
            )
            originals["prior_assessment"] = original
        relevant_answers = _answers(binding, context.activity_id)
        state = assessment.to_record()
        manifest_values = binding.candidate_manifest_values(assessment)
        instructions = {
            "document_paths": [blob.path for blob in context.source_inventory.blobs],
            "selected_scope": context.selected_scope,
            "confirmed_scope_boundary": context.package_context.scope_boundary.as_dict(),
            "package_contract_path": f"input/{contract_relative}",
            "candidate_manifest_values": manifest_values,
            "recorded_decisions": [item.to_record() for item in context.source_inventory.outcomes],
            "relevant_answers": relevant_answers,
            "outstanding_questions": _outstanding_questions(
                binding, context.activity_id, role
            ),
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
            parent_assignment_id=lineage["parent_assignment_id"],
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

    def _stage_candidate(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        reference: ArtifactReference,
        prefix: str,
        inputs: dict[str, bytes],
    ) -> str:
        manifest_path = self._artifact_path(binding, assessment, reference)
        manifest_bytes = manifest_path.read_bytes()
        try:
            manifest = json.loads(manifest_bytes)
            files = manifest["files"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as error:
            raise ValueError("assigned registration candidate manifest is invalid") from error
        if not isinstance(files, list):
            raise ValueError("assigned registration candidate inventory is invalid")
        manifest_relative = f"{prefix}/manifest.json"
        inputs[manifest_relative] = manifest_bytes
        seen: set[str] = set()
        for entry in files:
            if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
                raise ValueError("assigned registration candidate inventory is invalid")
            relative = entry["path"]
            parsed = PurePosixPath(relative)
            if (
                parsed.is_absolute() or ".." in parsed.parts or relative.startswith("./")
                or relative in seen or not isinstance(entry.get("sha256"), str)
            ):
                raise ValueError("assigned registration candidate inventory path is invalid")
            seen.add(relative)
            path = _regular_descendant(
                manifest_path.parent, parsed.parts,
                "assigned registration candidate record is unavailable",
            )
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != entry["sha256"]:
                raise ValueError("assigned registration candidate record differs from its manifest")
            inputs[f"{prefix}/{relative}"] = content
        return manifest_relative

    def _artifact_bytes(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        reference: ArtifactReference,
    ) -> bytes:
        return self._artifact_path(binding, assessment, reference).read_bytes()

    def _artifact_path(
        self,
        binding: RegistrationServiceBinding,
        assessment: RegistrationAssessment,
        reference: ArtifactReference,
    ) -> Path:
        for run_id in binding.assignment_runs(assessment, "project_architect"):
            root = (
                self.workspaces.root / assessment.context.project_id
                / assessment.context.activity_id / "runs" / run_id
            )
            try:
                path = _regular_descendant(
                    root, PurePosixPath(reference.path).parts,
                    "assigned registration artifact is unavailable or differs",
                )
            except ValueError:
                continue
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() == reference.sha256:
                return path
        raise ValueError("assigned registration artifact is unavailable or differs")


def _registration_package_contract() -> bytes:
    return (
        resources.files("maestro.service")
        .joinpath("registration_package_contract.json")
        .read_bytes()
    )


def _regular_descendant(root: Path, parts: tuple[str, ...], message: str) -> Path:
    path = root
    try:
        for index, part in enumerate(parts):
            path = path / part
            details = path.lstat()
            if stat.S_ISLNK(details.st_mode):
                raise ValueError(message)
            if index < len(parts) - 1 and not stat.S_ISDIR(details.st_mode):
                raise ValueError(message)
        if not parts or not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError(message)
    except OSError as error:
        raise ValueError(message) from error
    return path


def _recorded_runner_sequences(record: object) -> set[int]:
    """Recover runner event numbers already copied into the durable supervisor."""
    sequences: set[int] = set()
    for saved in getattr(record, "events", ()):
        if not isinstance(saved, Mapping) or saved.get("kind") != "stdout":
            continue
        data = saved.get("data")
        if not isinstance(data, str):
            continue
        try:
            event = json.loads(data)
            sequence = event["sequence"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if isinstance(sequence, int) and not isinstance(sequence, bool) and sequence > 0:
            sequences.add(sequence)
    return sequences


def _run_and_route(assessment: RegistrationAssessment, role: str):
    if role == "project_architect":
        return assessment.current_run(role), assessment.context.routes.architect
    if role == "fidelity_reviewer":
        return assessment.current_run(role), assessment.context.routes.fidelity_reviewer
    raise ValueError("registration role is invalid")


def _retryable_failure_code(code: str) -> bool:
    normalized = code.strip().lower().replace("-", "_")
    return normalized.startswith(("temporary_", "transient_", "response_")) or normalized in {
        "invalid_output",
        "malformed_response",
        "output_validation",
    }


def _run_timeout(assessment: RegistrationAssessment, role: str) -> int:
    section = "architect" if role == "project_architect" else "fidelity_reviewer"
    value = assessment.process_snapshot.definition[section]["run_timeout_seconds"]
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("registration run timeout is invalid")
    return value


def _route_mapping(route: ResolvedAgentRoute) -> dict[str, object]:
    return {
        "role": route.role, "tool": route.tool,
        "requested_model_id": route.requested_model_id, "provider": route.provider,
        "tool_version": route.tool_version, "executable": route.executable,
        "credential_profile": route.credential_profile,
        "settings_profile": route.settings_profile, "location": route.location,
        "capabilities": list(route.capabilities),
        "context_limit_tokens": route.context_limit_tokens,
        "permitted_destinations": [
            item.as_dict() for item in route.permitted_destinations
        ],
        "configuration_hash": route.configuration_hash,
    }


def _workspace_mapping(workspace: PreparedWorkspace) -> dict[str, object]:
    return {
        "project_id": workspace.project_id, "activity_id": workspace.activity_id,
        "run_id": workspace.run_id, "source_commit": workspace.source_commit,
        "root": str(workspace.paths.root),
        "assignment_sha256": workspace.assignment_sha256,
        "isolation_executable": str(workspace.isolation_executable),
        "workspace_root": str(workspace.workspace_root),
    }


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


def _outstanding_questions(
    binding: RegistrationServiceBinding, activity_id: str, role: str
) -> list[dict[str, object]]:
    with binding.database.read_connection() as connection:
        rows = connection.execute(
            """SELECT questions.question_id, questions.subject, questions.prompt,
                      details.original_question_id, details.previous_answer_id
               FROM service_questions AS questions
               JOIN service_question_details AS details USING(question_id)
               WHERE questions.activity_id = ? AND questions.requester = ?
                 AND questions.status IN ('awaiting_answer', 'clarification_required')
               ORDER BY questions.rowid""",
            (activity_id, role),
        ).fetchall()
    return [
        {
            "question_id": str(row[0]),
            "subject": str(row[1]),
            "prompt": str(row[2]),
            "original_question_id": None if row[3] is None else str(row[3]),
            "previous_answer_id": None if row[4] is None else str(row[4]),
        }
        for row in rows
    ]


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


def _write_service_file(path: Path, content: bytes) -> None:
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
    )
    try:
        os.write(descriptor, content)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
