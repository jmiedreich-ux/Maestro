"""Architecture-loop agent response: provider schema and transport validation.

The version-1 response fields follow ``docs/schemas/architecture-loop.schema.json``
(`agentResponse`). Transport validation checks identity, session, result shape and
that every named output exists at an assigned path with the stated hash; the
service checks the outputs' own contents afterwards.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import PurePosixPath
from typing import Any, Mapping

from maestro.foundation import canonical_json

from .preflight import ResolvedAgentRoute, verify_running_identity
from .transport import (
    AgentAssignment,
    ArtifactReference,
    DecodedToolResult,
    TransportError,
    ValidatedAgentResponse,
    _failure,
    _findings,
    _nonempty,
    _questions,
)
from .workspaces import PreparedWorkspace, WorkspaceError

_STR = {"type": "string"}
_NULLABLE_STR = {"type": ["string", "null"]}
_FINDING = {
    "type": "object",
    "properties": {
        "local_key": _STR, "subject": _STR, "severity": {"type": "string", "enum": ["blocking", "non_blocking"]},
        "explanation": _STR, "impact": _STR, "requested_correction": _STR,
        "source_refs": {"type": "array", "items": {"type": "object", "properties": {"path": _STR, "commit": _STR, "locator": _STR}, "required": ["path", "commit", "locator"], "additionalProperties": False}},
        "missing_information": _NULLABLE_STR,
        "affected_items": {"type": "array", "items": {"type": "object", "properties": {"id": _STR, "subject": _STR, "version": {"type": "integer"}, "path": _STR}, "required": ["id", "subject", "version", "path"], "additionalProperties": False}},
    },
    "required": ["local_key", "subject", "severity", "explanation", "impact", "requested_correction", "source_refs", "missing_information", "affected_items"],
    "additionalProperties": False,
}
_QUESTION = {
    "type": "object",
    "properties": {
        "local_key": _STR, "subject": _STR, "question": _STR, "reason": _STR,
        "recipient": {"type": "string", "enum": ["owner", "project_architect"]},
        "linked_finding_keys": {"type": "array", "items": _STR},
        "options": {"type": "array", "items": {"type": "object", "properties": {"local_key": _STR, "label": _STR, "tradeoff": _STR, "recommendation_reason": _NULLABLE_STR}, "required": ["local_key", "label", "tradeoff", "recommendation_reason"], "additionalProperties": False}},
    },
    "required": ["local_key", "subject", "question", "reason", "recipient", "linked_finding_keys", "options"],
    "additionalProperties": False,
}
RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "contract_version": {"type": "integer"}, "assignment_id": _STR, "run_id": _STR, "session_id": _STR, "project_id": _STR, "activity_id": _STR,
        "role": _STR, "source_commit": _STR, "decision_version": _STR,
        "input_manifest": {"type": "null"},
        "result": {"type": "string", "enum": ["completed", "clarification_required", "technical_failure"]},
        "summary": _STR,
        "findings": {"type": "array", "items": _FINDING},
        "questions": {"type": "array", "items": _QUESTION},
        "outputs": {"type": "array", "items": {"type": "object", "properties": {"path": _STR, "sha256": _STR, "version": {"type": "integer"}}, "required": ["path", "sha256", "version"], "additionalProperties": False}},
        "reviewed_set": {"type": "null"}, "review_outcome": {"type": "null"},
        "failure": {"type": ["object", "null"], "properties": {"code": _STR, "message": _STR, "affected_fields": {"type": "array", "items": _STR}}, "required": ["code", "message", "affected_fields"], "additionalProperties": False},
        "allocations": {"type": "array", "items": {"type": "object", "properties": {}, "additionalProperties": False}},
    },
    "required": ["contract_version", "assignment_id", "run_id", "session_id", "project_id", "activity_id", "role", "source_commit", "decision_version", "input_manifest", "result", "summary", "findings", "questions", "outputs", "reviewed_set", "review_outcome", "failure", "allocations"],
    "additionalProperties": False,
}
_TOP_LEVEL = set(RESPONSE_SCHEMA["properties"])
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class ArchitectureResponseValidator:
    """Validate transport output for an architecture assignment without deciding anything for the Owner."""

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
        verify_running_identity(route, decoded.identity)
        if assignment.assignment_id != current_assignment_id or assignment.run_id != current_run_id:
            raise TransportError("stale_assignment", "assignment or run is no longer current")
        try:
            workspace.verify_restrictions()
        except WorkspaceError as error:
            raise TransportError(error.code, str(error), **error.fields) from error
        value = decoded.response
        if not isinstance(value, Mapping) or set(value) != _TOP_LEVEL:
            raise TransportError("malformed_response", "response fields do not match contract version 1")
        expected = {
            "contract_version": 1, "assignment_id": assignment.assignment_id, "run_id": assignment.run_id,
            "session_id": assignment.instructions["session_id"], "project_id": assignment.project_id,
            "activity_id": assignment.activity_id, "role": assignment.role, "source_commit": assignment.source_commit,
            "decision_version": assignment.decision_version,
        }
        for name, wanted in expected.items():
            if type(value[name]) is not type(wanted) or value[name] != wanted:
                raise TransportError("stale_response", f"response {name} does not match assignment")
        if value["input_manifest"] is not None or value["reviewed_set"] is not None or value["review_outcome"] is not None or value["allocations"] != []:
            raise TransportError("conflicting_response", "an investigation response carries only its own fields")
        result = value["result"]
        if result not in {"completed", "clarification_required", "technical_failure"}:
            raise TransportError("malformed_response", "response result is invalid")
        summary = _nonempty(value["summary"], "summary")
        findings = _findings(_finding_view(value["findings"]))
        questions = _questions(_question_view(value["questions"]))
        finding_keys = {str(f["local_key"]) for f in findings}
        if any(not set(q.finding_keys).issubset(finding_keys) for q in questions):
            raise TransportError("malformed_response", "question links an unknown finding key")
        failure = value["failure"]
        if failure is not None:
            failure = _failure({"code": failure.get("code"), "message": failure.get("message")}) if isinstance(failure, Mapping) else _failure(failure)
        outputs = self._outputs(assignment, workspace, value["outputs"], result)
        if result == "completed" and failure is not None:
            raise TransportError("conflicting_response", "completed response has a failure")
        if result == "clarification_required" and (not questions or failure is not None):
            raise TransportError("conflicting_response", "clarification response is invalid")
        if result == "technical_failure" and failure is None:
            raise TransportError("conflicting_response", "technical failure response is invalid")
        return ValidatedAgentResponse(
            assignment.assignment_id, assignment.run_id, result, summary, findings, questions, None, None, None, None, failure,
            hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest(), outputs,
        )

    @staticmethod
    def _outputs(assignment: AgentAssignment, workspace: PreparedWorkspace, listed: object, result: str) -> tuple[ArtifactReference, ...]:
        rules = assignment.instructions["output_rules"]
        exact, patterns = set(rules["exact"]), [re.compile(p) for p in rules["patterns"]]
        if not isinstance(listed, list):
            raise TransportError("malformed_response", "outputs must be a list")
        references: list[ArtifactReference] = []
        seen: set[str] = set()
        for entry in listed:
            if not isinstance(entry, Mapping) or set(entry) != {"path", "sha256", "version"}:
                raise TransportError("malformed_response", "output reference is invalid")
            path, digest, version = entry["path"], entry["sha256"], entry["version"]
            if not isinstance(path, str) or not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None or isinstance(version, bool) or not isinstance(version, int) or version < 1:
                raise TransportError("malformed_response", "output reference fields are invalid")
            posix = PurePosixPath(path)
            if posix.is_absolute() or ".." in posix.parts or "\\" in path or not posix.parts or posix.parts[0] != "output":
                raise TransportError("artifact_out_of_scope", f"output path is outside the assigned output root: {path}")
            relative = str(PurePosixPath(*posix.parts[1:]))
            if relative not in exact and not any(p.fullmatch(relative) for p in patterns):
                raise TransportError("artifact_out_of_scope", f"output path is not an assigned name: {relative}")
            if path in seen:
                raise TransportError("malformed_response", f"output listed twice: {path}")
            seen.add(path)
            try:
                actual = workspace.resolve_artifact(path)
            except WorkspaceError as error:
                raise TransportError(error.code, str(error), **error.fields) from error
            if hashlib.sha256(actual.read_bytes()).hexdigest() != digest:
                raise TransportError("artifact_mismatch", f"output hash differs: {path}")
            references.append(ArtifactReference(path, digest, str(version)))
        if result == "completed":
            missing = sorted(f"output/{name}" for name in exact if f"output/{name}" not in seen)
            if missing:
                raise TransportError("missing_output", f"required outputs are missing: {', '.join(missing)}")
            # No unlisted file may sit beside the assigned outputs.
            root = workspace.paths.output
            present = {f"output/{p.relative_to(root).as_posix()}" for p in root.rglob("*") if p.is_file() and p.name != "response.json"}
            extra = sorted(present - seen)
            if extra:
                raise TransportError("artifact_out_of_scope", f"files were written that the response does not list: {', '.join(extra[:5])}")
        return tuple(references)


def _finding_view(findings: object) -> object:
    """The shared finding checker takes plain affected items and omits an empty missing_information."""
    if not isinstance(findings, list):
        return findings
    shaped = []
    for finding in findings:
        if not isinstance(finding, Mapping):
            shaped.append(finding)
            continue
        item = {k: v for k, v in finding.items() if k != "missing_information"}
        if finding.get("missing_information") is not None:
            item["missing_information"] = finding["missing_information"]
        item["affected_items"] = [
            {k: v for k, v in a.items() if k != "path"} if isinstance(a, Mapping) else a for a in finding.get("affected_items", [])
        ] if isinstance(finding.get("affected_items"), list) else finding.get("affected_items")
        shaped.append(item)
    return shaped


def _question_view(questions: object) -> object:
    if not isinstance(questions, list):
        return questions
    return [
        {"local_key": q["local_key"], "subject": q["subject"], "question": q["question"], "reason": q["reason"], "recipient": q["recipient"],
         "finding_keys": q["linked_finding_keys"], "options": q["options"]}
        if isinstance(q, Mapping) and set(q) == {"local_key", "subject", "question", "reason", "recipient", "linked_finding_keys", "options"} else q
        for q in questions
    ]
