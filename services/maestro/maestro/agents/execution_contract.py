"""Execution agent responses: provider schemas and transport validation.

Three assignment roles share one response envelope (identity, result, summary, questions, failure) and
add their own fields: the Development Manager's planning result, a coder's submitted result, and an
independent reviewer's verdict. Transport validation checks identity and shape only; the service
checks the result against saved state (packets, capacity, the pushed revision) afterwards.
"""

from __future__ import annotations

import hashlib
import re
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
    _nonempty,
    _questions,
)
from .workspaces import PreparedWorkspace, WorkspaceError
from .architecture_contract import _QUESTION, _question_view

_STR = {"type": "string"}
_STRS = {"type": "array", "items": _STR}
_NULLABLE_STR = {"type": ["string", "null"]}
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")

_COMMON = {
    "contract_version": {"type": "integer"}, "assignment_id": _STR, "run_id": _STR, "session_id": _STR, "project_id": _STR, "activity_id": _STR,
    "role": _STR, "source_commit": _STR, "decision_version": _STR,
    "result": {"type": "string", "enum": ["completed", "clarification_required", "technical_failure"]},
    "summary": _STR,
    "questions": {"type": "array", "items": _QUESTION},
    "failure": {"type": ["object", "null"], "properties": {"code": _STR, "message": _STR, "affected_fields": _STRS}, "required": ["code", "message", "affected_fields"], "additionalProperties": False},
}
_LAUNCH = {
    "type": "object",
    "properties": {"packet_key": _STR, "route_id": _STR, "model": _STR, "reason": _STR},
    "required": ["packet_key", "route_id", "model", "reason"], "additionalProperties": False,
}
_BLOCKER = {"type": "object", "properties": {"packet_key": _STR, "reason": _STR}, "required": ["packet_key", "reason"], "additionalProperties": False}
_CHECK = {
    "type": "object",
    "properties": {"command": _STR, "outcome": {"type": "string", "enum": ["passed", "failed", "untested"]}, "detail": _STR},
    "required": ["command", "outcome", "detail"], "additionalProperties": False,
}
_LOCATION = {"type": "object", "properties": {"path": _STR, "locator": _STR}, "required": ["path", "locator"], "additionalProperties": False}
_FINDING = {
    "type": "object",
    "properties": {
        "local_key": _STR, "subject": _STR, "severity": {"type": "string", "enum": ["blocking", "non_blocking"]},
        "explanation": _STR, "impact": _STR, "requested_correction": _STR, "locations": {"type": "array", "items": _LOCATION},
    },
    "required": ["local_key", "subject", "severity", "explanation", "impact", "requested_correction", "locations"], "additionalProperties": False,
}
_RANGE = {"type": "object", "properties": {"base": _STR, "head": _STR}, "required": ["base", "head"], "additionalProperties": False}


def _schema(extra: Mapping[str, Any]) -> dict[str, Any]:
    properties = {**_COMMON, **extra}
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


_SUPPORT_REQUEST = {"type": "object", "properties": {"packet_key": _STR, "reason": _STR}, "required": ["packet_key", "reason"], "additionalProperties": False}
_ARCH_QUESTION = {"type": "object", "properties": {"packet_key": _STR, "question": _STR}, "required": ["packet_key", "question"], "additionalProperties": False}
MANAGER_SCHEMA = _schema({
    "understanding": _STR,
    "launches": {"type": "array", "items": _LAUNCH},
    "priorities": _STRS,
    "blockers": {"type": "array", "items": _BLOCKER},
    "support_requests": {"type": "array", "items": _SUPPORT_REQUEST},
    "architectural_questions": {"type": "array", "items": _ARCH_QUESTION},
    "checkpoint": _STR,
})
CODER_SCHEMA = _schema({
    "base_revision": _STR,
    "changed_paths": _STRS,
    "checks": {"type": "array", "items": _CHECK},
    "evidence": _STRS,
    "limitations": _STRS,
    "blockers": _STRS,
    "unfinished": _STRS,
})
REVIEWER_SCHEMA = _schema({
    "review_outcome": {"type": ["string", "null"], "enum": ["APPROVE", "REQUEST_CHANGES", None]},
    "reviewed_range": {"anyOf": [_RANGE, {"type": "null"}]},
    "independence": _STR,
    "findings": {"type": "array", "items": _FINDING},
})
SUPPORT_DISPOSITIONS = ("use_existing", "create_role", "replanning_required")
SUPPORT_ARCHITECT_SCHEMA = _schema({
    "disposition": {"type": "string", "enum": list(SUPPORT_DISPOSITIONS)},
    "rationale": _STR,
    "existing_role_path": _NULLABLE_STR,
    "source_area": _NULLABLE_STR,
    "role_title": _NULLABLE_STR,
    "role_markdown": _NULLABLE_STR,
    "context_markdown": _NULLABLE_STR,
    "packet_keys": _STRS,
})
RECOMMENDATIONS = ("grant_one", "remain_paused")
DISPOSITION_CHOICES = ("continue_unaffected", "finish_safe_work", "stop_affected_or_all", "finish_current_for_replanning")
SUPPORT_LIMIT_SCHEMA = _schema({
    "support_id": _STR,
    "support_version": {"type": "integer"},
    "completed_reviews": {"type": "integer"},
    "recommendation": {"type": "string", "enum": list(RECOMMENDATIONS)},
    "rationale": _STR,
})
_SUPPLEMENT_PACKET = {
    "type": "object",
    "properties": {
        "key": _STR, "subject": _STR, "purpose": _STR, "implementation_ownership": _STR, "permitted_paths": _STRS, "dependencies": _STRS,
        "completion_criteria": _STRS, "essential_failure_checks": _STRS,
    },
    "required": ["key", "subject", "purpose", "implementation_ownership", "permitted_paths", "dependencies", "completion_criteria", "essential_failure_checks"], "additionalProperties": False,
}
_SUPPLEMENT = {
    "type": ["object", "null"],
    "properties": {"scope_explanation": _STR, "packets": {"type": "array", "items": _SUPPLEMENT_PACKET}},
    "required": ["scope_explanation", "packets"], "additionalProperties": False,
}
DETERMINATIONS = ("within_confirmed_design", "implementation_defect", "reregistration_required", "in_scope_supplement")
DETERMINATION_SCHEMA = _schema({
    "determination": {"type": "string", "enum": list(DETERMINATIONS)},
    "rationale": _STR,
    "interpretation": _NULLABLE_STR,
    "minimum_correction": _NULLABLE_STR,
    "affected_work": _STRS,
    "owner_recommendation": {"type": ["string", "null"], "enum": [*RECOMMENDATIONS, None]},
    "disposition_recommendation": {"type": ["string", "null"], "enum": [*DISPOSITION_CHOICES, None]},
    "supplement": _SUPPLEMENT,
})
SCHEMAS = {"development_manager": MANAGER_SCHEMA, "packet_coder": CODER_SCHEMA, "packet_reviewer": REVIEWER_SCHEMA,
           "integration_manager": CODER_SCHEMA, "integration_reviewer": REVIEWER_SCHEMA,
           "support_architect": SUPPORT_ARCHITECT_SCHEMA, "support_reviewer": REVIEWER_SCHEMA, "support_limit_architect": SUPPORT_LIMIT_SCHEMA,
           "determination_architect": DETERMINATION_SCHEMA, "milestone_gap_architect": DETERMINATION_SCHEMA}
PLAN_KEYS = ("intended_changes", "existing_code", "connections", "verification", "blockers")


class ExecutionResponseValidator:
    """Validate transport output for an Execution assignment; the service decides what the result means."""

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
        schema = SCHEMAS.get(assignment.role)
        value = decoded.response
        if schema is None or not isinstance(value, Mapping) or set(value) != set(schema["properties"]):
            raise TransportError("malformed_response", "response fields do not match the execution contract")
        expected = {
            "contract_version": 1, "assignment_id": assignment.assignment_id, "run_id": assignment.run_id,
            "session_id": assignment.instructions["session_id"], "project_id": assignment.project_id,
            "activity_id": assignment.activity_id, "role": assignment.role, "source_commit": assignment.source_commit,
            "decision_version": assignment.decision_version,
        }
        for name, wanted in expected.items():
            if type(value[name]) is not type(wanted) or value[name] != wanted:
                raise TransportError("stale_response", f"response {name} does not match assignment")
        result = value["result"]
        if result not in {"completed", "clarification_required", "technical_failure"}:
            raise TransportError("malformed_response", "response result is invalid")
        summary = _nonempty(value["summary"], "summary")
        questions = _questions(_question_view(value["questions"]))
        failure = value["failure"]
        if failure is not None:
            failure = _failure({"code": failure.get("code"), "message": failure.get("message")}) if isinstance(failure, Mapping) else _failure(failure)
        if result == "completed" and failure is not None:
            raise TransportError("conflicting_response", "completed response has a failure")
        if result == "clarification_required" and (not questions or failure is not None):
            raise TransportError("conflicting_response", "clarification response is invalid")
        if result == "technical_failure" and failure is None:
            raise TransportError("conflicting_response", "technical failure response is invalid")
        if assignment.role != "development_manager" and questions and result != "clarification_required":
            raise TransportError("conflicting_response", "questions need a clarification result")
        if result == "completed":
            self._check_role(assignment.role, value)
        outputs = self._outputs(assignment, workspace, result)
        return ValidatedAgentResponse(
            assignment.assignment_id, assignment.run_id, result, summary, (), questions, None, None, None,
            value.get("review_outcome") if assignment.role in {"packet_reviewer", "integration_reviewer", "support_reviewer"} and result == "completed" else None,
            failure, hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest(), outputs,
        )

    @staticmethod
    def _check_role(role: str, value: Mapping[str, Any]) -> None:
        if role == "development_manager":
            if not value["launches"] and not value["blockers"] and not value["priorities"]:
                raise TransportError("conflicting_response", "a planning result names launches, priorities or blockers")
            for launch in value["launches"]:
                if not all(isinstance(launch.get(k), str) and launch[k] for k in ("packet_key", "route_id", "model", "reason")):
                    raise TransportError("malformed_response", "a launch names its packet, route, model and reason")
            keys = [launch["packet_key"] for launch in value["launches"]]
            if len(set(keys)) != len(keys):
                raise TransportError("conflicting_response", "a packet is requested more than once")
        elif role == "support_architect":
            if value["disposition"] not in SUPPORT_DISPOSITIONS or not isinstance(value["rationale"], str) or not value["rationale"].strip():
                raise TransportError("malformed_response", "a support result states its disposition and rationale")
            if value["disposition"] == "use_existing" and not value["existing_role_path"]:
                raise TransportError("conflicting_response", "using an existing role names it")
            if value["disposition"] == "create_role" and not all(isinstance(value[k], str) and value[k].strip() for k in ("source_area", "role_title", "role_markdown", "context_markdown")):
                raise TransportError("conflicting_response", "a new role supplies its source area, title, role text and starting context")
            if not value["packet_keys"]:
                raise TransportError("conflicting_response", "a support result names the packets it covers")
        elif role == "support_limit_architect":
            if value["recommendation"] not in RECOMMENDATIONS or not isinstance(value["rationale"], str) or not value["rationale"].strip():
                raise TransportError("malformed_response", "a recommendation names grant_one or remain_paused with a rationale")
        elif role in {"determination_architect", "milestone_gap_architect"}:
            kind = value["determination"]
            if kind not in DETERMINATIONS or not isinstance(value["rationale"], str) or not value["rationale"].strip():
                raise TransportError("malformed_response", "a determination states its kind and rationale")
            if kind == "in_scope_supplement" and (role != "milestone_gap_architect" or not value["supplement"] or not value["supplement"]["packets"]):
                raise TransportError("conflicting_response", "only a milestone-gap result supplies a supplement, with at least one packet")
            if kind != "in_scope_supplement" and value["supplement"] is not None:
                raise TransportError("conflicting_response", "a supplement accompanies only an in-scope supplement determination")
            if kind == "implementation_defect" and not value["minimum_correction"]:
                raise TransportError("conflicting_response", "an implementation defect states the minimum correction")
            if kind == "within_confirmed_design" and not value["interpretation"]:
                raise TransportError("conflicting_response", "an interpretation states it")
            if kind == "reregistration_required" and not value["disposition_recommendation"]:
                raise TransportError("conflicting_response", "a re-registration result recommends a work disposition")
        elif role in {"packet_coder", "integration_manager"}:
            if not isinstance(value["changed_paths"], list) or not all(isinstance(p, str) and p for p in value["changed_paths"]):
                raise TransportError("malformed_response", "changed paths must be a list of paths")
            if not value["checks"]:
                raise TransportError("conflicting_response", "a coder result reports its checks")
        else:
            outcome, reviewed, findings = value["review_outcome"], value["reviewed_range"], value["findings"]
            if outcome not in {"APPROVE", "REQUEST_CHANGES"} or not isinstance(reviewed, Mapping):
                raise TransportError("conflicting_response", "a completed review states its outcome and the exact range it reviewed")
            blocking = any(f.get("severity") == "blocking" for f in findings)
            if outcome == "APPROVE" and blocking:
                raise TransportError("conflicting_response", "an approval cannot carry a blocking finding")
            if outcome == "REQUEST_CHANGES" and not blocking:
                raise TransportError("conflicting_response", "requested changes need at least one blocking finding")
            keys = [f["local_key"] for f in findings]
            if len(set(keys)) != len(keys):
                raise TransportError("malformed_response", "finding keys repeat")

    @staticmethod
    def _outputs(assignment: AgentAssignment, workspace: PreparedWorkspace, result: str) -> tuple[ArtifactReference, ...]:
        """A coder's plan is its only named output; the working tree is checked by the service, not listed."""
        if assignment.role != "packet_coder":
            return ()
        try:
            path = workspace.resolve_artifact("output/plan.json")
        except WorkspaceError as error:
            if result == "completed":
                raise TransportError("missing_output", "the coder did not write output/plan.json") from error
            return ()
        return (ArtifactReference("output/plan.json", hashlib.sha256(path.read_bytes()).hexdigest(), "1"),)
