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


class RegistrationRecordError(ValueError):
    """A registration response or package cannot be accepted."""


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

    def __post_init__(self) -> None:
        for field in (
            "project_id", "source_repository", "decision_version", "publication_branch",
            "destination_snapshot_reference", "selection_decision_ref",
        ):
            _text(getattr(self, field), field)
        if not isinstance(self.source_inventory, SourceInventory):
            raise RegistrationRecordError("package context requires exact source intake inventory")

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
    """Validate the common immutable registration record envelope."""
    if not isinstance(record, Mapping):
        raise RegistrationRecordError("package record must be an object")
    required = {"schema_version", "record_type", "record_id", "subject", "record_version", "data"}
    if not required.issubset(record) or record["schema_version"] != 1 or not isinstance(record["data"], Mapping):
        raise RegistrationRecordError("package record envelope is invalid")
    record_type = _text(record["record_type"], "record_type")
    if record_type not in _RECORD_TYPES:
        raise RegistrationRecordError("package record_type is unsupported")
    _text(record["record_id"], "record_id")
    _text(record["subject"], "subject")
    _positive(record["record_version"], "record_version")
    return record


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
    manifest: object, records: Mapping[str, Mapping[str, Any]], context: RegistrationPackageContext,
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
        "content_hash", "files",
    }
    if not isinstance(context, RegistrationPackageContext):
        raise TypeError("package validation requires saved registration intake context")
    if not isinstance(manifest, Mapping) or not required.issubset(manifest):
        raise RegistrationRecordError("candidate manifest fields are invalid")
    for field in ("project_id", "candidate_id", "source_repository", "source_commit", "decision_version", "source_ref", "publication_branch", "destination_snapshot_reference", "selection_decision_ref"):
        _text(manifest[field], f"manifest {field}")
    _positive(manifest["registration_version"], "manifest registration_version")
    _safe_path(manifest["overview_path"], "manifest overview_path")
    if manifest["previous_registration_ref"] is not None and not isinstance(manifest["previous_registration_ref"], Mapping):
        raise RegistrationRecordError("manifest previous_registration_ref must be null or an object")
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
    }
    for field, value in expected.items():
        if manifest[field] != value:
            raise RegistrationRecordError(f"manifest {field} differs from saved intake context")
    expected_content = package_content_hash(records)
    if manifest["content_hash"] != expected_content:
        raise RegistrationRecordError("manifest content_hash does not match frozen package records")
    files = manifest["files"]
    if not isinstance(files, list) or len(files) != len(records):
        raise RegistrationRecordError("manifest files do not match candidate records")
    seen: set[str] = set()
    record_ids: set[str] = set()
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
    return manifest
