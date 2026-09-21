"""Immutable validation records for registration assessment and review.

The registration handler owns semantic validation rather than trusting an
agent's readiness text.  These records intentionally stay transport-neutral:
the service verifies their artifact references before it saves or publishes
them.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping

from .sources import SourceInventory


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ROLES = frozenset(("project_architect", "fidelity_reviewer"))
_RESULTS = frozenset(("completed", "clarification_required", "technical_failure"))
_RECORD_TYPES = frozenset((
    "summary", "declaration", "naming_conventions", "milestone", "requirement",
    "assessment", "review", "decision", "confirmation",
))
_PACKAGE_RECORD_TYPES = frozenset(_RECORD_TYPES - {"confirmation"})
_REQUIRED_SINGLETONS = {
    "summary": "summary.json",
    "naming_conventions": "conventions.json",
}
_REQUIRED_COLLECTIONS = frozenset((
    "declaration", "milestone", "requirement", "assessment", "review", "decision",
))


class RegistrationRecordError(ValueError):
    """A registration response or package cannot be accepted."""


@dataclass(frozen=True)
class RegistrationScopeBoundary:
    """The Owner-confirmed outcome boundary interpreted against exact intake."""

    confirmation: str
    included_outcomes: tuple[str, ...]
    excluded_outcomes: tuple[str, ...]
    completion_outcomes: tuple[str, ...]
    outside_dependencies: tuple[tuple[str, tuple[str, ...]], ...]

    @classmethod
    def from_selection(
        cls, selection: str, inventory: SourceInventory
    ) -> "RegistrationScopeBoundary":
        confirmation = _text(selection, "selected scope")
        outcome_ids = tuple(item.milestone for item in inventory.outcomes)
        if not outcome_ids:
            raise RegistrationRecordError("selected scope needs supplied project outcomes")
        by_selector: dict[str, str] = {}
        for item in inventory.outcomes:
            for selector in (
                item.milestone, item.subject,
                f"{item.milestone} — {item.subject}",
                f"{item.milestone} - {item.subject}",
            ):
                normalized = selector.strip().casefold()
                if normalized in by_selector and by_selector[normalized] != item.milestone:
                    raise RegistrationRecordError("selected scope outcome labels are ambiguous")
                by_selector[normalized] = item.milestone
        dependencies: Mapping[str, object]
        structured_boundary = False
        try:
            structured = json.loads(confirmation)
        except json.JSONDecodeError:
            structured = None
        if isinstance(structured, Mapping):
            structured_boundary = True
            fields = {
                "confirmed", "included_outcomes", "excluded_outcomes",
                "completion_outcomes", "outside_dependencies",
            }
            if set(structured) != fields or structured.get("confirmed") is not True:
                raise RegistrationRecordError("structured scope boundary is not explicitly confirmed")
            included = tuple(_text_array(structured["included_outcomes"], "included scope outcome"))
            excluded = tuple(_text_array(structured["excluded_outcomes"], "excluded scope outcome"))
            completion = tuple(_text_array(structured["completion_outcomes"], "completion scope outcome"))
            dependencies_value = structured["outside_dependencies"]
            if not isinstance(dependencies_value, Mapping):
                raise RegistrationRecordError("outside scope dependencies must be keyed by included outcome")
            dependencies = dependencies_value
        else:
            normalized = confirmation.strip().casefold()
            if normalized in {
                "all supplied milestones", "all supplied outcomes", "whole supplied plan",
            }:
                included = outcome_ids
            else:
                selected: list[str] = []
                for token in confirmation.split(","):
                    identity = by_selector.get(token.strip().casefold())
                    if identity is None:
                        raise RegistrationRecordError(
                            "selected scope must name exact supplied outcomes or an explicitly confirmed structured boundary"
                        )
                    if identity not in selected:
                        selected.append(identity)
                included = tuple(item for item in outcome_ids if item in selected)
                if set(included) != set(outcome_ids):
                    raise RegistrationRecordError(
                        "a partial scope requires an explicitly confirmed structured boundary"
                    )
            excluded = tuple(item for item in outcome_ids if item not in included)
            completion = included
            dependencies = {item: [] for item in included}
        if (
            not included
            or len(set(included)) != len(included)
            or len(set(excluded)) != len(excluded)
            or set(included).intersection(excluded)
            or set(included).union(excluded) != set(outcome_ids)
            or tuple(item for item in outcome_ids if item in included) != included
            or tuple(item for item in outcome_ids if item in excluded) != excluded
            or completion != included
            or set(dependencies) != set(included)
        ):
            raise RegistrationRecordError(
                "confirmed scope must partition supplied outcomes and map completion for every included outcome"
            )
        frozen_dependencies: list[tuple[str, tuple[str, ...]]] = []
        outcomes_by_id = {item.milestone: item for item in inventory.outcomes}
        for milestone in included:
            values = dependencies[milestone]
            if not isinstance(values, list):
                raise RegistrationRecordError("outside scope dependencies must be arrays")
            supplied: dict[str, Mapping[str, object]] = {}
            for value in values:
                validated = _validate_dependency(value, "scope dependency")
                record_id = str(validated["record_id"])
                if record_id in supplied:
                    raise RegistrationRecordError("scope dependency identities must be unique")
                supplied[record_id] = validated
            encoded: list[str] = []
            declared = outcomes_by_id[milestone].dependencies
            declared_ids = {item.record_id for item in declared}
            if set(supplied) - declared_ids:
                raise RegistrationRecordError("scope dependency is not declared by the pinned source")
            for item in declared:
                internal = bool(item.referenced_outcomes) and set(
                    item.referenced_outcomes
                ).issubset(included)
                selected = supplied.get(item.record_id)
                if selected is not None:
                    if (
                        selected["subject"] != item.subject
                        or selected["required_outcome"] != item.required_outcome
                    ):
                        raise RegistrationRecordError(
                            "scope dependency identity differs from the pinned source"
                        )
                    dependency = selected
                elif internal:
                    dependency = {
                        "record_id": item.record_id,
                        "subject": item.subject,
                        "required_outcome": item.required_outcome,
                        "state": "included",
                        "evidence": [item.evidence],
                    }
                elif structured_boundary:
                    raise RegistrationRecordError(
                        "confirmed scope omits a declared outside dependency"
                    )
                else:
                    dependency = {
                        "record_id": item.record_id,
                        "subject": item.subject,
                        "required_outcome": item.required_outcome,
                        "state": "existing",
                        "evidence": [item.evidence],
                    }
                encoded.append(canonical_record_bytes(dependency).decode("utf-8"))
            frozen_dependencies.append((milestone, tuple(encoded)))
        return cls(
            confirmation, included, excluded, completion,
            tuple(frozen_dependencies),
        )

    @classmethod
    def whole(cls, inventory: SourceInventory) -> "RegistrationScopeBoundary":
        return cls.from_selection("All supplied milestones", inventory)

    def dependencies_for(self, milestone: str) -> list[Mapping[str, object]]:
        values = dict(self.outside_dependencies).get(milestone, ())
        return [json.loads(value) for value in values]

    def as_dict(self) -> dict[str, object]:
        return {
            "confirmed": True,
            "confirmation": self.confirmation,
            "included_outcomes": list(self.included_outcomes),
            "excluded_outcomes": list(self.excluded_outcomes),
            "completion_outcomes": list(self.completion_outcomes),
            "outside_dependencies": {
                milestone: self.dependencies_for(milestone)
                for milestone in self.included_outcomes
            },
        }


@dataclass(frozen=True)
class RegistrationPackageContext:
    """Saved intake facts that an agent-written candidate cannot replace."""

    project_id: str
    source_repository: str
    source_inventory: SourceInventory
    decision_version: str
    publication_branch: str
    destination_snapshot_reference: str
    selection_decision_ref: str
    scope_boundary: RegistrationScopeBoundary | None = None

    def __post_init__(self) -> None:
        for field in (
            "project_id", "source_repository", "decision_version", "publication_branch",
            "destination_snapshot_reference", "selection_decision_ref",
        ):
            _text(getattr(self, field), field)
        if not isinstance(self.source_inventory, SourceInventory):
            raise RegistrationRecordError("package context requires exact source intake inventory")
        if self.scope_boundary is None:
            object.__setattr__(self, "scope_boundary", RegistrationScopeBoundary.whole(self.source_inventory))
        elif not isinstance(self.scope_boundary, RegistrationScopeBoundary):
            raise RegistrationRecordError("package context requires a confirmed scope boundary")

    @classmethod
    def from_intake(
        cls,
        *,
        project_id: str,
        source_repository: str,
        intake: object,
        decision_version: str,
        selection_decision_ref: str,
    ) -> "RegistrationPackageContext":
        """Derive package bindings solely from a saved, authorized intake result."""
        # Local import avoids making source-intake import record validation.
        from .intake import RegistrationIntakeResult

        if not isinstance(intake, RegistrationIntakeResult) or intake.inventory is None:
            raise RegistrationRecordError("package context requires completed exact source intake")
        if intake.missing_questions or intake.failure is not None:
            raise RegistrationRecordError("package context requires an unblocked saved intake")
        if (
            intake.source_ref != intake.inventory.source_ref
            or not intake.publication_branch
            or not intake.destination_snapshot_reference
            or intake.destination_evidence is None
            or intake.destination_evidence.get("decision") != "allowed"
        ):
            raise RegistrationRecordError("saved intake selection is incomplete or no longer authorized")
        return cls(
            project_id, source_repository, intake.inventory, decision_version,
            intake.publication_branch, intake.destination_snapshot_reference,
            selection_decision_ref,
            RegistrationScopeBoundary.from_selection(
                intake.selected_scope or "", intake.inventory
            ),
        )


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RegistrationRecordError(f"{field} must be nonempty text")
    return value


def _positive(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RegistrationRecordError(f"{field} must be a positive integer")
    return value


def _safe_path(value: object, field: str) -> str:
    path = _text(value, field)
    parsed = PurePosixPath(path)
    if parsed.is_absolute() or ".." in parsed.parts or path.startswith("./"):
        raise RegistrationRecordError(f"{field} must be a safe relative path")
    return path


@dataclass(frozen=True)
class ArtifactReference:
    """A verified artifact location supplied by an assigned agent."""

    path: str
    sha256: str
    version: str

    @classmethod
    def from_mapping(cls, value: object, field: str = "artifact") -> "ArtifactReference":
        if not isinstance(value, Mapping) or set(value) != {"path", "sha256", "version"}:
            raise RegistrationRecordError(f"{field} must contain path, sha256, and version")
        path = _safe_path(value["path"], f"{field}.path")
        digest = _text(value["sha256"], f"{field}.sha256")
        if _SHA256.fullmatch(digest) is None:
            raise RegistrationRecordError(f"{field}.sha256 must be a lowercase SHA-256")
        return cls(path, digest, _text(value["version"], f"{field}.version"))

    def as_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256, "version": self.version}


@dataclass(frozen=True)
class Finding:
    local_key: str
    subject: str
    severity: str
    explanation: str
    impact: str
    requested_correction: str
    source_refs: tuple[Mapping[str, str], ...]
    affected_items: tuple[Mapping[str, object], ...]
    missing_information: str | None = None

    @classmethod
    def from_mapping(cls, value: object) -> "Finding":
        required = {
            "local_key", "subject", "severity", "explanation", "impact",
            "requested_correction", "source_refs", "affected_items",
        }
        if not isinstance(value, Mapping) or not required.issubset(value) or set(value) - (required | {"missing_information"}):
            raise RegistrationRecordError("finding fields are invalid")
        severity = value["severity"]
        if severity not in {"blocking", "non_blocking"}:
            raise RegistrationRecordError("finding severity is invalid")
        source_refs = value["source_refs"]
        affected_items = value["affected_items"]
        if not isinstance(source_refs, list) or not isinstance(affected_items, list):
            raise RegistrationRecordError("finding references must be arrays")
        normalized_sources: list[Mapping[str, str]] = []
        for source in source_refs:
            if not isinstance(source, Mapping) or set(source) != {"path", "commit", "locator"}:
                raise RegistrationRecordError("finding source reference is invalid")
            normalized_sources.append({
                "path": _safe_path(source["path"], "source path"),
                "commit": _text(source["commit"], "source commit"),
                "locator": _text(source["locator"], "source locator"),
            })
        normalized_items: list[Mapping[str, object]] = []
        for item in affected_items:
            if not isinstance(item, Mapping) or set(item) != {"record_id", "subject", "record_version"}:
                raise RegistrationRecordError("affected item is invalid")
            normalized_items.append({
                "record_id": _text(item["record_id"], "affected record_id"),
                "subject": _text(item["subject"], "affected subject"),
                "record_version": _positive(item["record_version"], "affected record_version"),
            })
        missing = value.get("missing_information")
        if missing is not None:
            missing = _text(missing, "missing_information")
        if not normalized_sources and missing is None:
            raise RegistrationRecordError("a finding without source references needs missing_information")
        return cls(
            _text(value["local_key"], "finding local_key"), _text(value["subject"], "finding subject"), severity,
            _text(value["explanation"], "finding explanation"), _text(value["impact"], "finding impact"),
            _text(value["requested_correction"], "finding requested_correction"), tuple(normalized_sources),
            tuple(normalized_items), missing,
        )


@dataclass(frozen=True)
class Clarification:
    local_key: str
    subject: str
    question: str
    reason: str
    recipient: str
    finding_keys: tuple[str, ...]
    options: tuple[Mapping[str, str | None], ...]

    @classmethod
    def from_mapping(cls, value: object) -> "Clarification":
        required = {"local_key", "subject", "question", "reason", "recipient", "finding_keys", "options"}
        if not isinstance(value, Mapping) or set(value) != required:
            raise RegistrationRecordError("clarification fields are invalid")
        if value["recipient"] not in {"project_architect", "owner"}:
            raise RegistrationRecordError("clarification recipient is invalid")
        if not isinstance(value["finding_keys"], list) or not isinstance(value["options"], list):
            raise RegistrationRecordError("clarification links and options must be arrays")
        keys = tuple(_text(item, "clarification finding key") for item in value["finding_keys"])
        if len(keys) != len(set(keys)):
            raise RegistrationRecordError("clarification finding keys must be unique")
        options: list[Mapping[str, str | None]] = []
        for option in value["options"]:
            if not isinstance(option, Mapping) or set(option) != {"local_key", "label", "tradeoff", "recommendation_reason"}:
                raise RegistrationRecordError("clarification option is invalid")
            reason = option["recommendation_reason"]
            if reason is not None:
                reason = _text(reason, "option recommendation_reason")
            options.append({
                "local_key": _text(option["local_key"], "option local_key"),
                "label": _text(option["label"], "option label"),
                "tradeoff": _text(option["tradeoff"], "option tradeoff"),
                "recommendation_reason": reason,
            })
        return cls(
            _text(value["local_key"], "clarification local_key"), _text(value["subject"], "clarification subject"),
            _text(value["question"], "clarification question"), _text(value["reason"], "clarification reason"),
            value["recipient"], keys, tuple(options),
        )


@dataclass(frozen=True)
class RegistrationAgentResponse:
    """The version-one structured response contract for both registration roles."""

    assignment_id: str
    run_id: str
    project_id: str
    activity_id: str
    role: str
    source_commit: str
    decision_version: str
    result: str
    summary: str
    findings: tuple[Finding, ...]
    questions: tuple[Clarification, ...]
    candidate: ArtifactReference | None
    assessment: ArtifactReference | None
    reviewed_assessment: ArtifactReference | None
    review_outcome: str | None
    failure: Mapping[str, str] | None

    @classmethod
    def from_mapping(cls, value: object) -> "RegistrationAgentResponse":
        fields = {
            "contract_version", "assignment_id", "run_id", "project_id", "activity_id", "role", "source_commit",
            "decision_version", "result", "summary", "findings", "questions", "candidate", "assessment",
            "reviewed_assessment", "review_outcome", "failure",
        }
        if not isinstance(value, Mapping) or set(value) != fields or value.get("contract_version") != 1:
            raise RegistrationRecordError("registration response must be contract version 1 with no unknown fields")
        role, result = value["role"], value["result"]
        if role not in _ROLES or result not in _RESULTS:
            raise RegistrationRecordError("registration response role or result is invalid")
        if not isinstance(value["findings"], list) or not isinstance(value["questions"], list):
            raise RegistrationRecordError("registration response findings and questions must be arrays")
        findings = tuple(Finding.from_mapping(item) for item in value["findings"])
        questions = tuple(Clarification.from_mapping(item) for item in value["questions"])
        if len({item.local_key for item in findings}) != len(findings) or len({item.local_key for item in questions}) != len(questions):
            raise RegistrationRecordError("response local keys must be unique within their collection")
        candidate = None if value["candidate"] is None else ArtifactReference.from_mapping(value["candidate"], "candidate")
        assessment = None if value["assessment"] is None else ArtifactReference.from_mapping(value["assessment"], "assessment")
        reviewed = None if value["reviewed_assessment"] is None else ArtifactReference.from_mapping(value["reviewed_assessment"], "reviewed_assessment")
        outcome = value["review_outcome"]
        if outcome not in {None, "APPROVE", "REQUEST_CHANGES"}:
            raise RegistrationRecordError("review_outcome is invalid")
        failure = value["failure"]
        if failure is not None:
            if not isinstance(failure, Mapping) or set(failure) != {"code", "message"}:
                raise RegistrationRecordError("failure is invalid")
            failure = {"code": _text(failure["code"], "failure code"), "message": _text(failure["message"], "failure message")}
        response = cls(
            *(_text(value[name], name) for name in ("assignment_id", "run_id", "project_id", "activity_id")),
            role, _text(value["source_commit"], "source_commit"), _text(value["decision_version"], "decision_version"), result,
            _text(value["summary"], "summary"), findings, questions, candidate, assessment, reviewed, outcome, failure,
        )
        response._validate_result_shape()
        return response

    def _validate_result_shape(self) -> None:
        blocking = any(item.severity == "blocking" for item in self.findings)
        if self.result == "completed" and self.role == "project_architect" and (self.assessment is None or self.candidate is None or self.review_outcome is not None or self.reviewed_assessment is not None):
            raise RegistrationRecordError("completed architect response requires assessment and candidate only")
        if self.result == "completed" and self.role == "fidelity_reviewer":
            if self.candidate is None or self.reviewed_assessment is None or self.assessment is not None or self.review_outcome not in {"APPROVE", "REQUEST_CHANGES"}:
                raise RegistrationRecordError("completed reviewer response requires exact reviewed artifacts and outcome")
            if self.review_outcome == "APPROVE" and (blocking or self.questions):
                raise RegistrationRecordError("approved review cannot contain blockers or unanswered questions")
            if self.review_outcome == "REQUEST_CHANGES" and not blocking:
                raise RegistrationRecordError("requested changes requires a blocking finding")
        if self.result == "clarification_required" and (not self.questions or self.review_outcome is not None):
            raise RegistrationRecordError("clarification response requires questions and no review approval")
        if self.result == "technical_failure" and (self.failure is None or self.review_outcome is not None):
            raise RegistrationRecordError("technical failure requires failure details and no review approval")
        if self.result != "technical_failure" and self.failure is not None:
            raise RegistrationRecordError("only technical failure can carry failure details")


def canonical_record_bytes(record: Mapping[str, Any]) -> bytes:
    """Canonical bytes used for a frozen package inventory hash."""
    try:
        return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RegistrationRecordError("record is not JSON serializable") from error


def validate_package_record(record: object) -> Mapping[str, Any]:
    """Validate the complete typed registration record contract."""
    if not isinstance(record, Mapping):
        raise RegistrationRecordError("package record must be an object")
    required = {"schema_version", "record_type", "record_id", "subject", "record_version", "data"}
    if set(record) != required or record["schema_version"] != 1 or not isinstance(record["data"], Mapping):
        raise RegistrationRecordError("package record envelope is invalid")
    record_type = _text(record["record_type"], "record_type")
    if record_type not in _PACKAGE_RECORD_TYPES:
        raise RegistrationRecordError("package record_type is unsupported")
    _text(record["record_id"], "record_id")
    _text(record["subject"], "subject")
    _positive(record["record_version"], "record_version")
    _validate_record_data(record_type, record["data"])
    return record


def _array(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise RegistrationRecordError(f"{field} must be an array")
    return value


def _text_array(value: object, field: str) -> list[str]:
    values = _array(value, field)
    return [_text(item, field) for item in values]


def _reference(value: object, field: str) -> Mapping[str, object]:
    local = {"record_id", "subject", "record_version", "path"}
    external = local | {"repository", "commit", "locator"}
    if not isinstance(value, Mapping) or frozenset(value) not in {frozenset(local), frozenset(external)}:
        raise RegistrationRecordError(f"{field} is invalid")
    _text(value["record_id"], f"{field}.record_id")
    _text(value["subject"], f"{field}.subject")
    _positive(value["record_version"], f"{field}.record_version")
    _safe_path(value["path"], f"{field}.path")
    if set(value) == external:
        _text(value["repository"], f"{field}.repository")
        commit = _text(value["commit"], f"{field}.commit")
        if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            raise RegistrationRecordError(f"{field}.commit must be a full Git object ID")
        _text(value["locator"], f"{field}.locator")
    return value


def _references(value: object, field: str) -> list[Mapping[str, object]]:
    return [_reference(item, field) for item in _array(value, field)]


def _required_data(data: Mapping[str, object], fields: set[str], record_type: str) -> None:
    if set(data) != fields:
        raise RegistrationRecordError(f"{record_type} record data fields are invalid")


def _validate_dependency(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or set(value) != {
        "record_id", "subject", "required_outcome", "state", "evidence"
    }:
        raise RegistrationRecordError(f"{field} is invalid")
    for name in ("record_id", "subject", "required_outcome"):
        _text(value[name], f"{field} {name}")
    if value["state"] not in {"existing", "included", "missing"}:
        raise RegistrationRecordError(f"{field} state is invalid")
    _text_array(value["evidence"], f"{field} evidence")
    return value


def _validate_record_data(record_type: str, data: Mapping[str, object]) -> None:
    if record_type == "summary":
        fields = {"project_id", "purpose", "scope", "priorities", "assessment_outcome", "project_requirement_refs"}
        _required_data(data, fields, record_type)
        _text(data["project_id"], "summary project_id")
        _text(data["purpose"], "summary purpose")
        scope = data["scope"]
        if not isinstance(scope, Mapping) or set(scope) != {"included", "excluded"}:
            raise RegistrationRecordError("summary scope is invalid")
        _text_array(scope["included"], "summary included outcomes")
        _text_array(scope["excluded"], "summary excluded outcomes")
        _text_array(data["priorities"], "summary priorities")
        if data["assessment_outcome"] not in {"ready", "clarification_required", "blocked"}:
            raise RegistrationRecordError("summary assessment_outcome is invalid")
        _references(data["project_requirement_refs"], "summary project requirement reference")
        return
    if record_type == "declaration":
        _required_data(data, {"designation", "milestone_refs", "source_refs"}, record_type)
        _text(data["designation"], "declaration designation")
        if not _references(data["milestone_refs"], "declaration milestone reference"):
            raise RegistrationRecordError("declaration needs at least one milestone reference")
        if not _references(data["source_refs"], "declaration source reference"):
            raise RegistrationRecordError("declaration needs source references")
        return
    if record_type == "naming_conventions":
        fields = {"declaration_designations", "record_types", "prefixes", "decision_refs"}
        _required_data(data, fields, record_type)
        for name in ("declaration_designations", "record_types", "prefixes"):
            entries = _array(data[name], f"naming conventions {name}")
            if not entries:
                raise RegistrationRecordError(f"naming conventions {name} cannot be empty")
            for entry in entries:
                if not isinstance(entry, Mapping) or set(entry) != {"code", "subject"}:
                    raise RegistrationRecordError(f"naming conventions {name} entry is invalid")
                _text(entry["code"], f"naming conventions {name} code")
                _text(entry["subject"], f"naming conventions {name} subject")
        if not _references(data["decision_refs"], "naming convention decision reference"):
            raise RegistrationRecordError("naming conventions need a decision reference")
        return
    if record_type == "milestone":
        fields = {"declaration_id", "milestone_id", "purpose", "included", "excluded", "dependencies", "requirement_refs", "source_refs"}
        _required_data(data, fields, record_type)
        for name in ("declaration_id", "milestone_id", "purpose"):
            _text(data[name], f"milestone {name}")
        _text_array(data["included"], "milestone included outcomes")
        _text_array(data["excluded"], "milestone excluded outcomes")
        for dependency in _array(data["dependencies"], "milestone dependencies"):
            _validate_dependency(dependency, "milestone dependency")
        if not _references(data["requirement_refs"], "milestone requirement reference"):
            raise RegistrationRecordError("milestone needs a completion requirement")
        if not _references(data["source_refs"], "milestone source reference"):
            raise RegistrationRecordError("milestone needs source references")
        return
    if record_type == "requirement":
        fields = {"applies_to", "expected_result", "conditions", "pass_boundary", "verification", "accepted_exception", "source_refs", "journey"}
        _required_data(data, fields, record_type)
        _reference(data["applies_to"], "requirement applies_to")
        for name in ("expected_result", "pass_boundary"):
            _text(data[name], f"requirement {name}")
        _text_array(data["conditions"], "requirement conditions")
        _text_array(data["verification"], "requirement verification")
        if data["accepted_exception"] is not None:
            _text(data["accepted_exception"], "requirement accepted_exception")
        if not _references(data["source_refs"], "requirement source reference"):
            raise RegistrationRecordError("requirement needs source references")
        for entry in _array(data["journey"], "requirement journey"):
            if not isinstance(entry, Mapping) or set(entry) != {"interaction", "expected_result", "essential_failure"}:
                raise RegistrationRecordError("requirement journey entry is invalid")
            for name in ("interaction", "expected_result", "essential_failure"):
                _text(entry[name], f"requirement journey {name}")
        return
    if record_type == "assessment":
        fields = {"assignment_id", "run_id", "source_commit", "decision_version", "summary", "findings"}
        _required_data(data, fields, record_type)
        for name in ("assignment_id", "run_id", "decision_version", "summary"):
            _text(data[name], f"assessment {name}")
        if re.fullmatch(r"[0-9a-f]{40}", _text(data["source_commit"], "assessment source_commit")) is None:
            raise RegistrationRecordError("assessment source_commit must be a full Git object ID")
        for finding in _array(data["findings"], "assessment findings"):
            Finding.from_mapping(finding)
        return
    if record_type == "review":
        fields = {"assignment_id", "run_id", "reviewer_identity", "review_round", "review_limit", "reviewed_content_hash", "reviewed_assessment_ref", "outcome", "findings"}
        _required_data(data, fields, record_type)
        for name in ("assignment_id", "run_id", "reviewer_identity"):
            _text(data[name], f"review {name}")
        _positive(data["review_round"], "review round")
        _positive(data["review_limit"], "review limit")
        if _SHA256.fullmatch(_text(data["reviewed_content_hash"], "reviewed_content_hash")) is None:
            raise RegistrationRecordError("reviewed_content_hash must be a lowercase SHA-256")
        _reference(data["reviewed_assessment_ref"], "reviewed assessment reference")
        if data["outcome"] not in {"APPROVE", "REQUEST_CHANGES"}:
            raise RegistrationRecordError("review outcome is invalid")
        findings = [Finding.from_mapping(item) for item in _array(data["findings"], "review findings")]
        if data["outcome"] == "APPROVE" and any(item.severity == "blocking" for item in findings):
            raise RegistrationRecordError("approved review cannot retain blocking findings")
        return
    if record_type == "decision":
        fields = {"question", "answers", "resolution", "authority", "affected_refs", "supersedes_ref"}
        _required_data(data, fields, record_type)
        if data["question"] is not None:
            _reference(data["question"], "decision question")
        for answer in _array(data["answers"], "decision answers"):
            if not isinstance(answer, Mapping) or set(answer) != {"answer_id", "author", "text", "answered_at"}:
                raise RegistrationRecordError("decision answer is invalid")
            for name in ("answer_id", "author", "text", "answered_at"):
                _text(answer[name], f"decision answer {name}")
        _text(data["resolution"], "decision resolution")
        authority = data["authority"]
        if isinstance(authority, Mapping):
            if set(authority) != {"kind", "identity"}:
                raise RegistrationRecordError("decision authority is invalid")
            _text(authority["kind"], "decision authority kind")
            _text(authority["identity"], "decision authority identity")
        else:
            _text(authority, "decision authority")
        _references(data["affected_refs"], "decision affected reference")
        if data["supersedes_ref"] is not None:
            _reference(data["supersedes_ref"], "decision supersedes reference")
        return
    raise RegistrationRecordError("package record_type is unsupported")


def package_content_hash(records: Mapping[str, Mapping[str, Any]]) -> str:
    """Hash non-review package records by path, exactly as the architecture specifies."""
    if not isinstance(records, Mapping) or not records:
        raise RegistrationRecordError("candidate needs package records")
    entries: list[str] = []
    for path, record in sorted(records.items()):
        safe = _safe_path(path, "record path")
        validated = validate_package_record(record)
        if validated["record_type"] == "review":
            continue
        entries.append(f"{safe}\t{hashlib.sha256(canonical_record_bytes(validated)).hexdigest()}\n")
    if not entries:
        raise RegistrationRecordError("candidate needs non-review package records")
    return hashlib.sha256("".join(entries).encode("utf-8")).hexdigest()


def validate_registration_package(
    manifest: object,
    records: Mapping[str, Mapping[str, Any]],
    context: RegistrationPackageContext,
    *,
    review_context: Mapping[str, object] | None = None,
    require_review: bool = True,
    manifest_values: Mapping[str, object] | None = None,
) -> Mapping[str, Any]:
    """Validate a frozen candidate manifest against its exact record inventory.

    The service calls this before publication.  It deliberately validates bytes,
    paths, identities, and source/decision binding; an agent cannot replace any
    of those checks with a textual readiness claim.
    """
    required = {
        "project_id", "registration_version", "candidate_id", "previous_registration_ref",
        "source_repository", "source_commit", "overview_path", "decision_version",
        "source_ref", "publication_branch", "destination_snapshot_reference", "selection_decision_ref",
        "scope_boundary", "content_hash", "files",
    }
    if not isinstance(context, RegistrationPackageContext):
        raise TypeError("package validation requires saved registration intake context")
    if not isinstance(manifest, Mapping) or set(manifest) != required:
        raise RegistrationRecordError("candidate manifest fields are invalid")
    for field in ("project_id", "candidate_id", "source_repository", "source_commit", "decision_version", "source_ref", "publication_branch", "destination_snapshot_reference", "selection_decision_ref"):
        _text(manifest[field], f"manifest {field}")
    _positive(manifest["registration_version"], "manifest registration_version")
    _safe_path(manifest["overview_path"], "manifest overview_path")
    previous = manifest["previous_registration_ref"]
    if previous is not None:
        previous_fields = {
            "repository", "commit", "registration_version", "candidate_id",
            "manifest_path", "manifest_sha256",
        }
        if not isinstance(previous, Mapping) or set(previous) != previous_fields:
            raise RegistrationRecordError(
                "manifest previous_registration_ref fields are invalid"
            )
        _text(previous["repository"], "previous registration repository")
        if re.fullmatch(r"[0-9a-f]{40}", _text(previous["commit"], "previous registration commit")) is None:
            raise RegistrationRecordError("previous registration commit must be a full Git object ID")
        _positive(previous["registration_version"], "previous registration version")
        _text(previous["candidate_id"], "previous registration candidate_id")
        _safe_path(previous["manifest_path"], "previous registration manifest_path")
        if _SHA256.fullmatch(_text(previous["manifest_sha256"], "previous registration manifest_sha256")) is None:
            raise RegistrationRecordError("previous registration manifest_sha256 is invalid")
    expected = {
        "project_id": context.project_id,
        "source_repository": context.source_repository,
        "source_commit": context.source_inventory.source_commit,
        "overview_path": context.source_inventory.overview_path,
        "decision_version": context.decision_version,
        "source_ref": context.source_inventory.source_ref,
        "publication_branch": context.publication_branch,
        "destination_snapshot_reference": context.destination_snapshot_reference,
        "selection_decision_ref": context.selection_decision_ref,
        "scope_boundary": context.scope_boundary.as_dict(),
    }
    for field, value in expected.items():
        if manifest[field] != value:
            raise RegistrationRecordError(f"manifest {field} differs from saved intake context")
    if manifest_values is not None:
        service_fields = required - {"content_hash", "files"}
        if set(manifest_values) != service_fields:
            raise RegistrationRecordError("service-owned manifest values are incomplete")
        for field, value in manifest_values.items():
            if manifest[field] != value:
                raise RegistrationRecordError(
                    f"manifest {field} differs from service-owned assignment values"
                )
    expected_content = package_content_hash(records)
    if manifest["content_hash"] != expected_content:
        raise RegistrationRecordError("manifest content_hash does not match frozen package records")
    files = manifest["files"]
    if not isinstance(files, list) or len(files) != len(records):
        raise RegistrationRecordError("manifest files do not match candidate records")
    seen: set[str] = set()
    record_ids: set[str] = set()
    typed: dict[str, list[tuple[str, Mapping[str, Any]]]] = {}
    for entry in files:
        fields = {"path", "record_id", "record_type", "record_version", "subject", "sha256"}
        if not isinstance(entry, Mapping) or set(entry) != fields:
            raise RegistrationRecordError("manifest file entry is invalid")
        path = _safe_path(entry["path"], "manifest file path")
        if path in seen or path not in records:
            raise RegistrationRecordError("manifest file paths must uniquely inventory records")
        seen.add(path)
        record = validate_package_record(records[path])
        if record["record_id"] in record_ids:
            raise RegistrationRecordError("package record_id must be unique across paths")
        record_ids.add(record["record_id"])
        if any(entry[name] != record[name] for name in ("record_id", "record_type", "record_version", "subject")):
            raise RegistrationRecordError("manifest file identity differs from record")
        if entry["sha256"] != hashlib.sha256(canonical_record_bytes(record)).hexdigest():
            raise RegistrationRecordError("manifest file hash differs from record bytes")
        typed.setdefault(str(record["record_type"]), []).append((path, record))
    _validate_package_topology(
        manifest,
        typed,
        context,
        review_context=review_context,
        require_review=require_review,
    )
    return manifest


def _validate_package_topology(
    manifest: Mapping[str, Any],
    typed: Mapping[str, list[tuple[str, Mapping[str, Any]]]],
    context: RegistrationPackageContext,
    *,
    review_context: Mapping[str, object] | None,
    require_review: bool,
) -> None:
    required = set(_REQUIRED_COLLECTIONS)
    if not require_review:
        required.remove("review")
    missing = sorted(record_type for record_type in required if not typed.get(record_type))
    if missing:
        raise RegistrationRecordError(
            "candidate package is missing required record type(s): " + ", ".join(missing)
        )
    for record_type, path in _REQUIRED_SINGLETONS.items():
        values = typed.get(record_type, [])
        if len(values) != 1 or values[0][0] != path:
            raise RegistrationRecordError(f"candidate requires exactly one {record_type} record at {path}")
    for record_type, values in typed.items():
        if record_type in {"summary", "naming_conventions"}:
            continue
        root = {
            "declaration": "declarations/",
            "milestone": "milestones/",
            "requirement": "requirements/",
            "assessment": "assessments/",
            "review": "reviews/",
            "decision": "decisions/",
        }[record_type]
        if any(not path.startswith(root) or not path.endswith(".json") for path, _ in values):
            raise RegistrationRecordError(f"{record_type} records must use the required package directory")

    by_path = {
        path: record for values in typed.values() for path, record in values
    }
    by_id = {
        str(record["record_id"]): (path, record)
        for path, record in by_path.items()
    }
    if len(by_id) != len(by_path):
        raise RegistrationRecordError("package record identities must be unique")
    for record in by_path.values():
        _validate_local_references(record["data"], by_path, by_id)
        _validate_external_source_references(record["data"], context)

    summary = typed["summary"][0][1]
    if summary["data"]["project_id"] != context.project_id:
        raise RegistrationRecordError("summary project_id differs from saved intake")
    if summary["data"]["assessment_outcome"] != "ready":
        raise RegistrationRecordError("published candidate summary must be ready")

    declarations = typed.get("declaration", [])
    milestones = typed.get("milestone", [])
    boundary = context.scope_boundary
    assert boundary is not None
    all_outcomes = context.source_inventory.outcomes
    outcomes = tuple(
        item for item in all_outcomes
        if item.milestone in boundary.included_outcomes
    )
    outcome_by_id = {item.milestone: item for item in all_outcomes}
    expected_scope = {
        "included": [outcome_by_id[item].subject for item in boundary.included_outcomes],
        "excluded": [outcome_by_id[item].subject for item in boundary.excluded_outcomes],
    }
    if summary["data"]["scope"] != expected_scope:
        raise RegistrationRecordError(
            "candidate summary scope differs from the confirmed intake boundary"
        )
    declared_designations = {
        str(record["data"]["designation"]) for _, record in declarations
    }
    expected_designations = {item.declaration for item in outcomes}
    if declared_designations != expected_designations:
        raise RegistrationRecordError("candidate declarations do not cover the exact source outcomes")
    milestone_records = {
        (str(record["data"]["declaration_id"]), str(record["data"]["milestone_id"])):
        (path, record)
        for path, record in milestones
    }
    expected_milestones = {
        (item.declaration, item.milestone): item for item in outcomes
    }
    if set(milestone_records) != set(expected_milestones):
        raise RegistrationRecordError("candidate milestones do not cover the exact source outcomes")
    for identity, outcome in expected_milestones.items():
        _path, record = milestone_records[identity]
        if (
            record["subject"] != outcome.subject
            or record["record_version"] != outcome.version
        ):
            raise RegistrationRecordError(
                "candidate milestone identity, subject, or version differs from the exact source outcome"
            )
        if record["data"]["dependencies"] != boundary.dependencies_for(outcome.milestone):
            raise RegistrationRecordError(
                "candidate milestone dependencies differ from the confirmed intake boundary"
            )
    declaration_records = {
        str(record["data"]["designation"]): record
        for _, record in declarations
    }
    for designation, declaration in declaration_records.items():
        expected_order = [
            item for item in outcomes if item.declaration == designation
        ]
        expected_versions = {item.declaration_version for item in expected_order}
        expected_subjects = {item.declaration_subject for item in expected_order}
        if (
            len(expected_versions) != 1
            or declaration["record_version"] not in expected_versions
            or len(expected_subjects) != 1
            or declaration["subject"] not in expected_subjects
        ):
            raise RegistrationRecordError(
                "candidate declaration version or subject differs from the exact source declaration"
            )
        actual_order = [
            str(reference["record_id"])
            for reference in declaration["data"]["milestone_refs"]
        ]
        if actual_order != [item.milestone for item in expected_order]:
            raise RegistrationRecordError(
                "candidate declaration order differs from the exact source declaration"
            )

    completion_mappings = [
        str(record["data"]["applies_to"]["record_id"])
        for _, record in typed.get("requirement", [])
    ]
    mapped_outcomes = set(completion_mappings)
    if (
        not set(boundary.completion_outcomes).issubset(mapped_outcomes)
        or set(boundary.excluded_outcomes).intersection(mapped_outcomes)
    ):
        raise RegistrationRecordError(
            "candidate completion mappings differ from the confirmed intake boundary"
        )
    requirement_paths = {
        path for path, _ in typed.get("requirement", [])
    }
    if {
        str(reference["path"])
        for reference in summary["data"]["project_requirement_refs"]
    } != requirement_paths:
        raise RegistrationRecordError(
            "candidate summary completion references differ from the confirmed intake boundary"
        )

    selection = [
        record for _, record in typed.get("decision", [])
        if record["record_id"] == context.selection_decision_ref
    ]
    if len(selection) != 1:
        raise RegistrationRecordError("candidate lacks the exact service selection decision")
    selection_authority = selection[0]["data"]["authority"]
    if selection_authority != {
        "kind": "service", "identity": "registration-intake"
    }:
        raise RegistrationRecordError(
            "candidate selection decision lacks service-owned intake authority"
        )
    if context.selection_decision_ref != manifest["selection_decision_ref"]:
        raise RegistrationRecordError("candidate selection decision differs from its manifest")

    assessments = typed.get("assessment", [])
    if len(assessments) != 1:
        raise RegistrationRecordError("candidate requires exactly one current assessment record")
    assessment_path, assessment = assessments[0]
    assessment_data = assessment["data"]
    if (
        assessment_data["source_commit"] != manifest["source_commit"]
        or assessment_data["decision_version"] != manifest["decision_version"]
    ):
        raise RegistrationRecordError("candidate assessment differs from source or decision context")
    if review_context is not None and (
        assessment_data["assignment_id"]
        != review_context.get("architect_assignment_id")
        or assessment_data["run_id"] != review_context.get("architect_run_id")
    ):
        raise RegistrationRecordError(
            "candidate assessment assignment is not the service-created architect run"
        )

    reviews = typed.get("review", [])
    if require_review:
        if len(reviews) != 1:
            raise RegistrationRecordError("candidate requires exactly one complete current review record")
        _, review = reviews[0]
        data = review["data"]
        if data["outcome"] != "APPROVE":
            raise RegistrationRecordError("candidate review must approve the exact candidate")
        if data["reviewed_content_hash"] != manifest["content_hash"]:
            raise RegistrationRecordError("candidate review does not cover the exact content hash")
        reference = data["reviewed_assessment_ref"]
        if (
            reference["path"] != assessment_path
            or reference["record_id"] != assessment["record_id"]
            or reference["record_version"] != assessment["record_version"]
            or reference["subject"] != assessment["subject"]
        ):
            raise RegistrationRecordError("candidate review does not cover the current assessment")
        if review_context is not None:
            expected = {
                "assignment_id": review_context.get("assignment_id"),
                "run_id": review_context.get("run_id"),
                "reviewer_identity": review_context.get("reviewer_identity"),
                "review_round": review_context.get("review_round"),
                "review_limit": review_context.get("review_limit"),
            }
            if any(data[name] != value for name, value in expected.items()):
                raise RegistrationRecordError("candidate review identity or accounting is not service-owned")


def _validate_local_references(
    value: object,
    by_path: Mapping[str, Mapping[str, Any]],
    by_id: Mapping[str, tuple[str, Mapping[str, Any]]],
) -> None:
    if isinstance(value, Mapping):
        fields = set(value)
        local = {"record_id", "subject", "record_version", "path"}
        external = local | {"repository", "commit", "locator"}
        frozen_fields = frozenset(fields)
        if frozen_fields in {frozenset(local), frozenset(external)}:
            if frozen_fields == frozenset(external):
                return
            path = str(value["path"])
            target = by_path.get(path)
            if target is None:
                raise RegistrationRecordError("package reference names a nonexistent record path")
            if by_id.get(str(value["record_id"])) != (path, target) or any(
                value[name] != target[name]
                for name in ("record_id", "subject", "record_version")
            ):
                raise RegistrationRecordError("package reference differs from its target record")
            return
        for item in value.values():
            _validate_local_references(item, by_path, by_id)
    elif isinstance(value, list):
        for item in value:
            _validate_local_references(item, by_path, by_id)


def _validate_external_source_references(
    value: object, context: RegistrationPackageContext
) -> None:
    if isinstance(value, Mapping):
        external = {
            "record_id", "subject", "record_version", "path",
            "repository", "commit", "locator",
        }
        if set(value) == external:
            paths = {item.path for item in context.source_inventory.blobs}
            if (
                value["repository"] != context.source_repository
                or value["commit"] != context.source_inventory.source_commit
                or value["path"] not in paths
            ):
                raise RegistrationRecordError(
                    "package source reference differs from the exact source inventory"
                )
            return
        for item in value.values():
            _validate_external_source_references(item, context)
    elif isinstance(value, list):
        for item in value:
            _validate_external_source_references(item, context)
