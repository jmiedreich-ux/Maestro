"""Shared assignment and structured-response contracts for agent transports."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Mapping, Protocol

from maestro.foundation import ContractError, canonical_identifier, canonical_json
from maestro.service.questions import AnswerChoice, LinkedQuestion

from .preflight import ResolvedAgentRoute, RunningToolIdentity, verify_running_identity
from .workspaces import PreparedWorkspace, ServiceProfileBinding, WorkspaceError


_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_TOP_LEVEL = {
    "contract_version",
    "assignment_id",
    "run_id",
    "project_id",
    "activity_id",
    "role",
    "source_commit",
    "decision_version",
    "result",
    "summary",
    "findings",
    "questions",
    "candidate",
    "assessment",
    "reviewed_assessment",
    "review_outcome",
    "failure",
}


class TransportError(ValueError):
    """A typed launch-protocol or structured-result rejection."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


@dataclass(frozen=True)
class ArtifactReference:
    path: str
    sha256: str
    version: str

    @classmethod
    def from_mapping(cls, value: object, field: str) -> "ArtifactReference":
        if not isinstance(value, Mapping) or set(value) != {"path", "sha256", "version"}:
            raise TransportError("malformed_response", f"{field} artifact reference is invalid")
        path, digest, version = value["path"], value["sha256"], value["version"]
        if not isinstance(path, str) or not path:
            raise TransportError("malformed_response", f"{field}.path is invalid")
        if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
            raise TransportError("malformed_response", f"{field}.sha256 is invalid")
        if not isinstance(version, str) or not version.strip():
            raise TransportError("malformed_response", f"{field}.version is invalid")
        return cls(path, digest, version)

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256, "version": self.version}


# Execution roles run on the same run service; the run service's own role class (architect or fidelity_reviewer) selects the route requirements.
ASSIGNMENT_ROLES = frozenset({"project_architect", "fidelity_reviewer", "development_manager", "packet_coder", "packet_reviewer", "integration_manager", "integration_reviewer"})


@dataclass(frozen=True)
class AgentAssignment:
    project_id: str
    activity_id: str
    assignment_id: str
    run_id: str
    parent_assignment_id: str | None
    role: str
    role_responsibilities: tuple[str, ...]
    task: str
    source_commit: str
    decision_version: str
    instructions: Mapping[str, Any]
    permitted_actions: tuple[str, ...]
    writable_locations: tuple[str, ...]
    limits: Mapping[str, Any]
    clarification_conditions: tuple[str, ...]
    response_schema: Mapping[str, Any]
    response_path: str = "output/response.json"
    assigned_artifacts: Mapping[str, ArtifactReference] = field(default_factory=dict)
    contract: str = "registration"

    def __post_init__(self) -> None:
        for value, field in (
            (self.project_id, "project_id"),
            (self.activity_id, "activity_id"),
            (self.assignment_id, "assignment_id"),
            (self.run_id, "run_id"),
        ):
            _canonical(value, field, "invalid_assignment")
        if self.parent_assignment_id is not None:
            _canonical(self.parent_assignment_id, "parent_assignment_id", "invalid_assignment")
        if self.role not in ASSIGNMENT_ROLES:
            raise TransportError("invalid_assignment", "assigned role is unsupported")
        if not isinstance(self.source_commit, str) or _COMMIT.fullmatch(self.source_commit) is None:
            raise TransportError("invalid_assignment", "source_commit must be a lowercase full commit")
        _nonempty(self.task, "task")
        _nonempty(self.decision_version, "decision_version")
        _text_tuple(self.role_responsibilities, "role_responsibilities")
        _text_tuple(self.permitted_actions, "permitted_actions")
        _text_tuple(self.clarification_conditions, "clarification_conditions")
        if set(self.writable_locations) != {"output", "scratch"}:
            raise TransportError(
                "invalid_assignment", "writable locations must be exactly output and scratch"
            )
        for value, field in (
            (self.instructions, "instructions"),
            (self.limits, "limits"),
            (self.response_schema, "response_schema"),
        ):
            if not isinstance(value, Mapping):
                raise TransportError("invalid_assignment", f"{field} must be an object")
            _plain_object(value, field)
        if self.response_path != "output/response.json":
            raise TransportError("invalid_assignment", "response_path must be output/response.json")
        artifacts = self.assigned_artifacts
        if not isinstance(artifacts, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, ArtifactReference)
            for key, value in artifacts.items()
        ):
            raise TransportError("invalid_assignment", "assigned_artifacts are invalid")
        object.__setattr__(self, "assigned_artifacts", dict(artifacts))

    def as_dict(self) -> dict[str, Any]:
        value = self._registration_dict()
        if self.contract != "registration":
            value["contract"] = self.contract
        return value

    def _registration_dict(self) -> dict[str, Any]:
        return {
            "contract_version": 1,
            "project_id": self.project_id,
            "activity_id": self.activity_id,
            "assignment_id": self.assignment_id,
            "run_id": self.run_id,
            "parent_assignment_id": self.parent_assignment_id,
            "role": self.role,
            "role_responsibilities": list(self.role_responsibilities),
            "task": self.task,
            "source_commit": self.source_commit,
            "decision_version": self.decision_version,
            "instructions": dict(self.instructions),
            "assigned_artifacts": {
                key: value.as_dict() for key, value in sorted(self.assigned_artifacts.items())
            },
            "permitted_actions": list(self.permitted_actions),
            "writable_locations": list(self.writable_locations),
            "limits": dict(self.limits),
            "clarification_conditions": list(self.clarification_conditions),
            "required_response": {
                "path": self.response_path,
                "schema": dict(self.response_schema),
            },
        }

    def to_bytes(self) -> bytes:
        return (canonical_json(self.as_dict()) + "\n").encode("utf-8")


@dataclass(frozen=True)
class ClarificationOption:
    local_key: str
    label: str
    tradeoff: str
    recommendation_reason: str | None


@dataclass(frozen=True)
class ClarificationRequest:
    local_key: str
    subject: str
    question: str
    reason: str
    recipient: str
    finding_keys: tuple[str, ...]
    options: tuple[ClarificationOption, ...]

    def to_linked_question(
        self,
        *,
        question_id: str,
        assignment: AgentAssignment,
        requester: str,
        original_question_id: str | None = None,
        previous_answer_id: str | None = None,
    ) -> LinkedQuestion:
        """Use the linked-question provider without granting the agent persistence authority."""
        return LinkedQuestion(
            question_id=question_id,
            project_id=assignment.project_id,
            activity_id=assignment.activity_id,
            subject=self.subject,
            prompt=f"{self.question}\n\nWhy this is needed: {self.reason}",
            requester=requester,
            recipient=self.recipient,
            choices=tuple(
                AnswerChoice(option.local_key, option.label, option.tradeoff, option.recommendation_reason)
                for option in self.options
            ),
            allow_free_text=True,
            original_question_id=original_question_id,
            previous_answer_id=previous_answer_id,
        )


@dataclass(frozen=True)
class ValidatedAgentResponse:
    assignment_id: str
    run_id: str
    result: str
    summary: str
    findings: tuple[Mapping[str, Any], ...]
    questions: tuple[ClarificationRequest, ...]
    candidate: ArtifactReference | None
    assessment: ArtifactReference | None
    reviewed_assessment: ArtifactReference | None
    review_outcome: str | None
    failure: Mapping[str, str] | None
    response_sha256: str
    outputs: tuple[ArtifactReference, ...] = ()


@dataclass(frozen=True)
class DecodedToolResult:
    response: Mapping[str, Any]
    identity: RunningToolIdentity
    session_id: str | None = None
    thread_id: str | None = None
    turn_id: str | None = None


class ResponseDecoder(Protocol):
    def decode(self, *args: object, **kwargs: object) -> DecodedToolResult: ...


@dataclass(frozen=True)
class TransportLaunch:
    tool_arguments: tuple[str, ...]
    isolated_arguments: tuple[str, ...]
    cwd: str
    initial_stdin: tuple[bytes, ...] = ()
    sandbox_arguments: tuple[str, ...] = ()


def validate_transport_context(
    tool: str,
    route: ResolvedAgentRoute,
    assignment: AgentAssignment,
    workspace: PreparedWorkspace,
    profile: ServiceProfileBinding,
) -> None:
    expected_roles = {
        "architect": {"project_architect", "development_manager", "packet_coder", "integration_manager"},
        "fidelity_reviewer": {"fidelity_reviewer", "packet_reviewer", "integration_reviewer"},
    }.get(route.role, set())
    if route.tool != tool or assignment.role not in expected_roles:
        raise TransportError("route_mismatch", "route does not match the assignment")
    if (
        workspace.project_id != assignment.project_id
        or workspace.activity_id != assignment.activity_id
        or workspace.run_id != assignment.run_id
        or workspace.source_commit != assignment.source_commit
    ):
        raise TransportError("workspace_mismatch", "workspace does not match the assignment")
    if workspace.assignment_sha256 != hashlib.sha256(assignment.to_bytes()).hexdigest():
        raise TransportError("workspace_mismatch", "workspace assignment bytes differ")
    try:
        if (
            profile.service_home.stat().st_uid != workspace.workspace_root.stat().st_uid
            or profile.service_home == workspace.workspace_root
            or profile.service_home.is_relative_to(workspace.workspace_root)
        ):
            raise WorkspaceError("unsafe_profile", "profile is not owned outside the workspace")
        profile.validate_selection(
            route.tool, route.credential_profile, route.settings_profile
        )
        profile.mounts()
    except WorkspaceError as error:
        raise TransportError(error.code, str(error), **error.fields) from error
    if assignment.role == "fidelity_reviewer" and assignment.contract == "registration":
        _verify_reviewer_inputs(assignment, workspace)


def _verify_reviewer_inputs(
    assignment: AgentAssignment,
    workspace: PreparedWorkspace,
) -> None:
    required = {"candidate", "reviewed_assessment"}
    if set(assignment.assigned_artifacts) != required:
        raise TransportError(
            "invalid_assignment",
            "reviewer assignment must declare exact candidate and assessment artifacts",
        )
    try:
        workspace.verify_restrictions()
        for field in sorted(required):
            reference = assignment.assigned_artifacts[field]
            path = PurePosixPath(reference.path)
            if not path.parts or path.parts[0] != "input":
                raise TransportError(
                    "artifact_out_of_scope",
                    f"reviewer {field} must be under immutable input",
                )
            artifact = workspace.resolve_artifact(reference.path, allow_input=True)
            if hashlib.sha256(artifact.read_bytes()).hexdigest() != reference.sha256:
                raise TransportError(
                    "artifact_mismatch",
                    f"reviewer {field} does not match its declared hash",
                )
    except WorkspaceError as error:
        raise TransportError(error.code, str(error), **error.fields) from error


class RegistrationResponseValidator:
    """Validate transport output without making a registration or Owner decision."""

    def validate(
        self,
        decoded: DecodedToolResult,
        *,
        route: ResolvedAgentRoute,
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        current_assignment_id: str,
        current_run_id: str,
    ) -> ValidatedAgentResponse:
        if not isinstance(decoded, DecodedToolResult):
            raise TransportError("malformed_output", "decoded tool result is invalid")
        verify_running_identity(route, decoded.identity)
        if assignment.assignment_id != current_assignment_id or assignment.run_id != current_run_id:
            raise TransportError("stale_assignment", "assignment or run is no longer current")
        try:
            workspace.verify_restrictions()
        except WorkspaceError as error:
            raise TransportError(error.code, str(error), **error.fields) from error
        value = decoded.response
        if not isinstance(value, Mapping) or set(value) != _TOP_LEVEL:
            raise TransportError(
                "malformed_response", "response fields do not match contract version 1"
            )
        expected = {
            "contract_version": 1,
            "assignment_id": assignment.assignment_id,
            "run_id": assignment.run_id,
            "project_id": assignment.project_id,
            "activity_id": assignment.activity_id,
            "role": assignment.role,
            "source_commit": assignment.source_commit,
            "decision_version": assignment.decision_version,
        }
        for field, expected_value in expected.items():
            if type(value[field]) is not type(expected_value) or value[field] != expected_value:
                raise TransportError("stale_response", f"response {field} does not match assignment")
        result = value["result"]
        if result not in {"completed", "clarification_required", "technical_failure"}:
            raise TransportError("malformed_response", "response result is invalid")
        summary = _nonempty(value["summary"], "summary")
        findings = _findings(value["findings"])
        questions = _questions(value["questions"])
        finding_keys = {str(finding["local_key"]) for finding in findings}
        question_keys = {question.local_key for question in questions}
        if finding_keys & question_keys:
            raise TransportError("malformed_response", "response local keys are duplicated")
        if any(not set(question.finding_keys).issubset(finding_keys) for question in questions):
            raise TransportError("malformed_response", "question links an unknown finding key")
        candidate = _artifact(value["candidate"], "candidate")
        assessment = _artifact(value["assessment"], "assessment")
        reviewed = _artifact(value["reviewed_assessment"], "reviewed_assessment")
        outcome = value["review_outcome"]
        failure = _failure(value["failure"])
        if outcome not in {None, "APPROVE", "REQUEST_CHANGES"}:
            raise TransportError("malformed_response", "review_outcome is invalid")
        self._validate_result_shape(
            assignment, result, findings, questions, candidate, assessment, reviewed, outcome, failure
        )
        for field, reference in (
            ("candidate", candidate),
            ("assessment", assessment),
            ("reviewed_assessment", reviewed),
        ):
            if reference is not None:
                self._verify_artifact(assignment, workspace, field, reference)
        encoded = canonical_json(value)
        return ValidatedAgentResponse(
            assignment.assignment_id,
            assignment.run_id,
            result,
            summary,
            findings,
            questions,
            candidate,
            assessment,
            reviewed,
            outcome,
            failure,
            hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        )

    @staticmethod
    def _verify_artifact(
        assignment: AgentAssignment,
        workspace: PreparedWorkspace,
        field: str,
        reference: ArtifactReference,
    ) -> None:
        assigned = assignment.assigned_artifacts.get(field)
        if assignment.role == "fidelity_reviewer" and field in {"candidate", "reviewed_assessment"}:
            if assigned != reference:
                raise TransportError(
                    "stale_response", f"reviewer {field} does not match the assigned artifact"
                )
            allow_input = True
        else:
            allow_input = False
        try:
            path = workspace.resolve_artifact(reference.path, allow_input=allow_input)
        except WorkspaceError as error:
            raise TransportError(error.code, str(error), **error.fields) from error
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != reference.sha256:
            raise TransportError("artifact_mismatch", f"{field} artifact hash differs")

    @staticmethod
    def _validate_result_shape(
        assignment: AgentAssignment,
        result: str,
        findings: tuple[Mapping[str, Any], ...],
        questions: tuple[ClarificationRequest, ...],
        candidate: ArtifactReference | None,
        assessment: ArtifactReference | None,
        reviewed: ArtifactReference | None,
        outcome: object,
        failure: Mapping[str, str] | None,
    ) -> None:
        blocking = any(finding["severity"] == "blocking" for finding in findings)
        if assignment.role == "project_architect" and (reviewed is not None or outcome is not None):
            raise TransportError("conflicting_response", "architect response contains review fields")
        if assignment.role == "fidelity_reviewer" and assessment is not None:
            raise TransportError("conflicting_response", "reviewer response contains architect assessment")
        if result == "completed":
            if failure is not None:
                raise TransportError("conflicting_response", "completed response has a failure")
            if assignment.role == "project_architect":
                if candidate is None or assessment is None or reviewed is not None or outcome is not None:
                    raise TransportError("conflicting_response", "completed architect response is invalid")
            else:
                if candidate is None or reviewed is None or assessment is not None or outcome is None:
                    raise TransportError("conflicting_response", "completed reviewer response is invalid")
                if outcome == "APPROVE" and (blocking or questions):
                    raise TransportError("conflicting_response", "review approval has unresolved blockers")
                if outcome == "REQUEST_CHANGES" and not blocking:
                    raise TransportError("conflicting_response", "requested changes require a blocker")
        elif result == "clarification_required":
            if not questions or outcome is not None or failure is not None:
                raise TransportError("conflicting_response", "clarification response is invalid")
        else:
            if failure is None or outcome is not None:
                raise TransportError("conflicting_response", "technical failure response is invalid")


def decode_json_object(raw: bytes | str) -> Mapping[str, Any]:
    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        raise TransportError("malformed_output", "tool output is not one UTF-8 JSON value") from error
    if not isinstance(value, Mapping):
        raise TransportError("malformed_output", "tool output must be one JSON object")
    return value


def _artifact(value: object, field: str) -> ArtifactReference | None:
    return None if value is None else ArtifactReference.from_mapping(value, field)


def _failure(value: object) -> Mapping[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"code", "message"}:
        raise TransportError("malformed_response", "failure is invalid")
    code = _nonempty(value["code"], "failure.code")
    message = _nonempty(value["message"], "failure.message")
    return {"code": code, "message": message}


def _findings(value: object) -> tuple[Mapping[str, Any], ...]:
    fields = {
        "local_key",
        "subject",
        "severity",
        "explanation",
        "impact",
        "requested_correction",
        "source_refs",
        "affected_items",
    }
    if not isinstance(value, list):
        raise TransportError("malformed_response", "findings must be a list")
    result: list[Mapping[str, Any]] = []
    keys: set[str] = set()
    for finding in value:
        if not isinstance(finding, Mapping) or not (
            set(finding) == fields or set(finding) == fields | {"missing_information"}
        ):
            raise TransportError("malformed_response", "finding fields are invalid")
        _canonical(finding["local_key"], "finding.local_key", "malformed_response")
        for field in (
            "subject",
            "explanation",
            "impact",
            "requested_correction",
        ):
            _nonempty(finding[field], f"finding.{field}")
        if finding["severity"] not in {"blocking", "non_blocking"}:
            raise TransportError("malformed_response", "finding severity is invalid")
        source_refs = finding["source_refs"]
        affected_items = finding["affected_items"]
        if not isinstance(source_refs, list) or not isinstance(affected_items, list):
            raise TransportError("malformed_response", "finding references are invalid")
        for source in source_refs:
            if not isinstance(source, Mapping):
                raise TransportError("malformed_response", "finding source reference is invalid")
            locator_fields = set(source) - {"path", "commit"}
            if locator_fields not in ({"locator"}, {"heading"}, {"line"}):
                raise TransportError("malformed_response", "finding source locator is invalid")
            _relative_reference(source.get("path"), "finding.source_refs.path")
            _nonempty(source.get("commit"), "finding.source_refs.commit")
            if _COMMIT.fullmatch(str(source["commit"])) is None:
                raise TransportError("malformed_response", "finding source commit is invalid")
            locator = source[next(iter(locator_fields))]
            if isinstance(locator, bool) or not (
                isinstance(locator, str) and locator.strip()
                or isinstance(locator, int) and locator > 0
            ):
                raise TransportError("malformed_response", "finding source locator is invalid")
        for affected in affected_items:
            if not isinstance(affected, Mapping) or set(affected) != {"id", "subject", "version"}:
                raise TransportError("malformed_response", "finding affected item is invalid")
            _canonical(affected["id"], "finding.affected_items.id", "malformed_response")
            _nonempty(affected["subject"], "finding.affected_items.subject")
            version = affected["version"]
            if isinstance(version, bool) or not (
                isinstance(version, str) and version.strip()
                or isinstance(version, int) and version > 0
            ):
                raise TransportError("malformed_response", "finding affected item version is invalid")
        missing_information = finding.get("missing_information")
        if not source_refs and not (
            isinstance(missing_information, str) and missing_information.strip()
        ):
            raise TransportError("malformed_response", "finding has no source or missing information")
        if source_refs and missing_information is not None:
            raise TransportError(
                "malformed_response", "sourced finding cannot also claim missing information"
            )
        key = str(finding["local_key"])
        if key in keys:
            raise TransportError("malformed_response", "finding local keys are duplicated")
        keys.add(key)
        result.append(dict(finding))
    return tuple(result)


def _questions(value: object) -> tuple[ClarificationRequest, ...]:
    fields = {
        "local_key",
        "subject",
        "question",
        "reason",
        "recipient",
        "finding_keys",
        "options",
    }
    option_fields = {"local_key", "label", "tradeoff", "recommendation_reason"}
    if not isinstance(value, list):
        raise TransportError("malformed_response", "questions must be a list")
    result: list[ClarificationRequest] = []
    keys: set[str] = set()
    for question in value:
        if not isinstance(question, Mapping) or set(question) != fields:
            raise TransportError("malformed_response", "question fields are invalid")
        _canonical(question["local_key"], "question.local_key", "malformed_response")
        for field in ("subject", "question", "reason"):
            _nonempty(question[field], f"question.{field}")
        if question["recipient"] not in {"project_architect", "owner"}:
            raise TransportError("malformed_response", "question recipient is invalid")
        if not isinstance(question["finding_keys"], list) or any(
            not isinstance(key, str) or not key for key in question["finding_keys"]
        ):
            raise TransportError("malformed_response", "question finding keys are invalid")
        if not isinstance(question["options"], list):
            raise TransportError("malformed_response", "question options are invalid")
        options: list[ClarificationOption] = []
        option_keys: set[str] = set()
        for option in question["options"]:
            if not isinstance(option, Mapping) or set(option) != option_fields:
                raise TransportError("malformed_response", "question option fields are invalid")
            _canonical(option["local_key"], "question.option.local_key", "malformed_response")
            for field in ("label", "tradeoff"):
                _nonempty(option[field], f"question.option.{field}")
            reason = option["recommendation_reason"]
            if reason is not None:
                _nonempty(reason, "question.option.recommendation_reason")
            local_key = str(option["local_key"])
            if local_key in option_keys:
                raise TransportError("malformed_response", "question option keys are duplicated")
            option_keys.add(local_key)
            options.append(
                ClarificationOption(
                    local_key,
                    str(option["label"]),
                    str(option["tradeoff"]),
                    None if reason is None else str(reason),
                )
            )
        local_key = str(question["local_key"])
        if local_key in keys:
            raise TransportError("malformed_response", "question local keys are duplicated")
        keys.add(local_key)
        result.append(
            ClarificationRequest(
                local_key,
                str(question["subject"]),
                str(question["question"]),
                str(question["reason"]),
                str(question["recipient"]),
                tuple(question["finding_keys"]),
                tuple(options),
            )
        )
    return tuple(result)


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TransportError("malformed_response", f"{field} must be nonempty text")
    return value


def _text_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value:
        raise TransportError("invalid_assignment", f"{field} must be a nonempty tuple")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise TransportError("invalid_assignment", f"{field} contains invalid text")
    return value


def _plain_object(value: Mapping[str, Any], field: str) -> None:
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError, UnicodeError) as error:
        raise TransportError("invalid_assignment", f"{field} is not plain JSON data") from error


def _canonical(value: object, field: str, code: str) -> str:
    try:
        return canonical_identifier(value, field)  # type: ignore[arg-type]
    except ContractError as error:
        raise TransportError(code, str(error)) from error


def _relative_reference(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise TransportError("malformed_response", f"{field} is invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise TransportError("malformed_response", f"{field} is invalid")
    return value
