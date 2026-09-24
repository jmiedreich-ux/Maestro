"""Registration package records, candidate validation, receipts and the discovery index.

Everything here is deterministic: source facts come from the validated Markdown
sources, judgments come from the architect's validated candidate and assessment,
and identities, versions and hashes are assigned by the service.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from .registration_source import SourceModel

ROOT = ".maestro/registrations"
SCHEMA_VERSION = 1
_DEPENDENCY_STATES = {"existing", "included", "missing"}
_ASSESSMENT_OUTCOMES = {"ready", "clarification_required", "blocked"}
_EVIDENCE_LEVELS = {"reported", "source_inspection", "verified_in_operation", "not_applicable"}
_HASHED_TYPES = {"summary", "declaration", "naming_conventions", "milestone", "requirement", "assessment", "decision"}


class CandidateError(ValueError):
    """The architect's candidate or assessment does not satisfy the registration contract."""


def encode(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def key_of(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CandidateError(f"{name} must be nonempty text")
    return value.strip()


def validate_candidate(document: object, scope: Mapping[str, Any]) -> dict[str, Any]:
    """Check candidate.json; the milestone list must match the confirmed scope exactly."""
    if not isinstance(document, Mapping) or set(document) != {"schema", "summary", "milestones"}:
        raise CandidateError("candidate.json must contain exactly schema, summary and milestones")
    if document["schema"] != "registration_candidate_v1":
        raise CandidateError("candidate.json schema must be registration_candidate_v1")
    summary = document["summary"]
    if not isinstance(summary, Mapping) or set(summary) != {"purpose", "priorities", "assessment_outcome"}:
        raise CandidateError("candidate summary must contain purpose, priorities and assessment_outcome")
    _text(summary["purpose"], "summary.purpose")
    priorities = summary["priorities"]
    if not isinstance(priorities, list) or not priorities or not all(isinstance(p, str) and p.strip() for p in priorities):
        raise CandidateError("summary.priorities must be a nonempty list of text")
    if summary["assessment_outcome"] not in _ASSESSMENT_OUTCOMES:
        raise CandidateError("summary.assessment_outcome must be ready, clarification_required or blocked")
    included = [item["reference"] for item in scope["included"]]
    milestones = document["milestones"]
    if not isinstance(milestones, list):
        raise CandidateError("candidate milestones must be a list")
    seen: list[str] = []
    for entry in milestones:
        if not isinstance(entry, Mapping) or set(entry) != {"reference", "dependencies", "usage_walkthrough"}:
            raise CandidateError("each candidate milestone needs reference, dependencies and usage_walkthrough")
        seen.append(_text(entry["reference"], "milestone.reference"))
        _text(entry["usage_walkthrough"], f"{entry['reference']}.usage_walkthrough")
        dependencies = entry["dependencies"]
        if not isinstance(dependencies, list):
            raise CandidateError(f"{entry['reference']} dependencies must be a list")
        for dependency in dependencies:
            if not isinstance(dependency, Mapping) or set(dependency) != {"subject", "required_outcome", "state", "evidence_level", "evidence"}:
                raise CandidateError(f"{entry['reference']} dependency fields are invalid")
            _text(dependency["subject"], "dependency.subject")
            _text(dependency["required_outcome"], "dependency.required_outcome")
            _text(dependency["evidence"], "dependency.evidence")
            if dependency["state"] not in _DEPENDENCY_STATES:
                raise CandidateError("dependency state must be existing, included or missing")
            if dependency["evidence_level"] not in _EVIDENCE_LEVELS:
                raise CandidateError("dependency evidence_level is invalid")
    if sorted(seen) != sorted(included) or len(set(seen)) != len(seen):
        raise CandidateError(f"candidate milestones must be exactly the confirmed scope: {', '.join(sorted(included))}")
    return dict(document)


def validate_assessment(document: object) -> dict[str, Any]:
    if not isinstance(document, Mapping) or set(document) != {"schema", "summary", "evidence"}:
        raise CandidateError("assessment.json must contain exactly schema, summary and evidence")
    if document["schema"] != "registration_assessment_v1":
        raise CandidateError("assessment.json schema must be registration_assessment_v1")
    _text(document["summary"], "assessment.summary")
    evidence = document["evidence"]
    if not isinstance(evidence, list) or not evidence:
        raise CandidateError("assessment.evidence must be a nonempty list")
    for item in evidence:
        if not isinstance(item, Mapping) or set(item) != {"claim", "level", "source"}:
            raise CandidateError("each evidence entry needs claim, level and source")
        _text(item["claim"], "evidence.claim")
        _text(item["source"], "evidence.source")
        if item["level"] not in _EVIDENCE_LEVELS:
            raise CandidateError("evidence level is invalid")
    return dict(document)


def _record(record_type: str, record_id: str, subject: str, version: int, data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": record_type,
        "record_id": record_id,
        "subject": subject,
        "record_version": version,
        "data": dict(data),
    }


def candidate_directory(version: int, candidate_id: str) -> str:
    return f"{ROOT}/versions/{version}/candidates/{candidate_id}"


def build_package(
    *,
    project_id: str,
    registration_version: int,
    candidate_id: str,
    repository: str,
    source_ref: str | None,
    source_commit: str,
    publication_branch: str,
    decision_version: int,
    model: SourceModel,
    scope: Mapping[str, Any],
    candidate: Mapping[str, Any],
    assessment: Mapping[str, Any],
    findings: list[Mapping[str, Any]],
    decisions: list[Mapping[str, Any]],
    selection: Mapping[str, Any],
    reviews: list[Mapping[str, Any]],
    assessment_run: Mapping[str, str],
    previous_ref: Mapping[str, Any] | None = None,
) -> tuple[dict[str, bytes], dict[str, Any], str]:
    """Return (files relative to the repository root, manifest, manifest path)."""
    base = candidate_directory(registration_version, candidate_id)
    files: dict[str, dict[str, Any]] = {}

    def add(relative: str, record: dict[str, Any]) -> dict[str, str]:
        files[f"{base}/{relative}"] = record
        return {"record_id": record["record_id"], "subject": record["subject"], "record_version": record["record_version"], "path": relative}

    included = {item["reference"] for item in scope["included"]}
    declaration_refs: dict[str, dict[str, str]] = {}
    milestone_refs: dict[str, dict[str, str]] = {}
    requirement_refs: dict[str, list[dict[str, str]]] = {}
    by_reference = {entry["reference"]: entry for entry in candidate["milestones"]}
    for declaration in model.declarations:
        for milestone in declaration.milestones:
            if milestone.reference not in included:
                continue
            requirement_refs[milestone.reference] = []
            for number, (expected, boundary, verification, exception) in enumerate(milestone.criteria, 1):
                record_id = f"{key_of(milestone.reference)}-req-{number}"
                requirement_refs[milestone.reference].append(
                    add(
                        f"requirements/{record_id}.json",
                        _record("requirement", record_id, f"{milestone.reference} — {milestone.subject}: criterion {number}", milestone.version, {
                            "applies_to": {"record_id": key_of(milestone.reference), "subject": f"{milestone.reference} — {milestone.subject}", "record_version": milestone.version},
                            "expected_result": expected,
                            "conditions": expected,
                            "pass_boundary": boundary,
                            "verification": verification,
                            "accepted_exception": exception,
                            "source_refs": [_source(declaration.path, source_commit, milestone.section)],
                            "journey": [{"interaction": name, "expected_result": milestone.outcome, "essential_failure_behavior": reference} for name, reference in milestone.journeys],
                        }),
                    )
                )
    project_requirement = add(
        "requirements/project-completion.json",
        _record("requirement", "project-completion", f"{model.project_name} completion", 1, {
            "applies_to": {"record_id": "summary", "subject": model.project_name, "record_version": 1},
            "expected_result": "Every included project milestone meets its own acceptance criteria and definition of done.",
            "conditions": scope["description"],
            "pass_boundary": "All included milestone requirements are met with the evidence each one names.",
            "verification": "; ".join(f"{m['reference']} — {m['subject']}" for m in scope["included"]),
            "accepted_exception": "None",
            "source_refs": [_source(model.overview_path, source_commit, "Overall scope")],
            "journey": [],
        }),
    )
    for declaration in model.declarations:
        milestones_here = [m for m in declaration.milestones if m.reference in included]
        if not milestones_here:
            continue
        for milestone in milestones_here:
            entry = by_reference[milestone.reference]
            milestone_refs[milestone.reference] = add(
                f"milestones/{key_of(milestone.reference)}.json",
                _record("milestone", key_of(milestone.reference), f"{milestone.reference} — {milestone.subject}", milestone.version, {
                    "declaration_id": key_of(declaration.designation),
                    "milestone_id": milestone.reference,
                    "purpose": milestone.outcome,
                    "included": milestone.included,
                    "excluded": milestone.excluded,
                    "dependencies": [
                        {"subject": d["subject"], "required_outcome": d["required_outcome"], "state": d["state"], "evidence_level": d["evidence_level"], "evidence": d["evidence"]}
                        for d in entry["dependencies"]
                    ],
                    "declared_dependencies": [{"subject": name, "reference": reference, "state": state} for name, reference, state in milestone.dependencies],
                    "usage_walkthrough": entry["usage_walkthrough"],
                    "requirement_refs": requirement_refs[milestone.reference],
                    "source_refs": [_source(declaration.path, source_commit, milestone.section)],
                }),
            )
        declaration_refs[declaration.designation] = add(
            f"declarations/{key_of(declaration.designation)}.json",
            _record("declaration", key_of(declaration.designation), f"{declaration.designation} — {declaration.subject}", declaration.version, {
                "designation": declaration.designation,
                "milestone_refs": [milestone_refs[m.reference] for m in milestones_here],
                "source_refs": [_source(declaration.path, source_commit, "Milestones and order")],
            }),
        )
    summary_ref = add(
        "summary.json",
        _record("summary", "summary", f"{model.project_name} registration summary", 1, {
            "project_id": project_id,
            "purpose": candidate["summary"]["purpose"],
            "scope": {"included": scope["included"], "excluded": scope["excluded"], "description": scope["description"]},
            "priorities": candidate["summary"]["priorities"],
            "assessment_outcome": candidate["summary"]["assessment_outcome"],
            "requirement_refs": [project_requirement],
        }),
    )
    add(
        "conventions.json",
        _record("naming_conventions", "conventions", "Naming conventions", 1, {
            "declaration_designations": [{"code": d.designation, "subject": d.subject} for d in model.declarations],
            "record_types": [{"code": "PM", "subject": "Project milestone"}],
            "prefixes": [{"code": d.designation, "subject": f"{d.subject} milestones"} for d in model.declarations],
            "decision_refs": [{"record_id": "selection", "subject": "Source and publication selection", "record_version": 1, "path": "decisions/selection.json"}],
        }),
    )
    add(
        "assessments/assessment-1.json",
        _record("assessment", "assessment-1", "Architect assessment", 1, {
            "assignment_id": assessment_run["assignment_id"],
            "run_id": assessment_run["run_id"],
            "source_commit": source_commit,
            "decision_version": str(decision_version),
            "summary": assessment["summary"],
            "evidence": assessment["evidence"],
            "findings": findings,
        }),
    )
    selection_ref = add("decisions/selection.json", _record("decision", "selection", "Source and publication selection", 1, dict(selection)))
    for number, decision in enumerate(decisions, 1):
        add(f"decisions/decision-{number}.json", _record("decision", f"decision-{number}", decision["subject"], 1, {
            "question": decision.get("question"),
            "answers": decision["answers"],
            "resolution": decision["resolution"],
            "authority": decision["authority"],
            "affected_refs": decision.get("affected_refs", []),
            "supersedes_ref": None,
        }))
    hashed_bytes = {path: encode(record) for path, record in files.items()}
    content_lines = "".join(
        f"{path}\t{sha256(hashed_bytes[path])}\n"
        for path in sorted(hashed_bytes)
        if files[path]["record_type"] in _HASHED_TYPES
    )
    content_hash = sha256(content_lines.encode("utf-8"))
    review_files: dict[str, bytes] = {}
    for review in reviews:
        record = _record("review", f"review-{review['round']}", f"Independent fidelity review, round {review['round']}", 1, {
            "assignment_id": review["assignment_id"],
            "run_id": review["run_id"],
            "reviewer_identity": review["reviewer_identity"],
            "review_round": review["round"],
            "review_limit": review["limit"],
            "reviewed_content_hash": content_hash if review["covers_final"] else review["content_hash"],
            "reviewed_assessment_ref": {"record_id": "assessment-1", "subject": "Architect assessment", "record_version": 1, "path": "assessments/assessment-1.json"},
            "outcome": review["outcome"],
            "findings": review["findings"],
        })
        review_files[f"{base}/reviews/review-{review['round']}.json"] = encode(record)
        files[f"{base}/reviews/review-{review['round']}.json"] = record
    all_bytes = {**hashed_bytes, **review_files}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "registration_version": registration_version,
        "candidate_id": candidate_id,
        "previous_registration_ref": None if previous_ref is None else dict(previous_ref),
        "source_repository": repository,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "publication_branch": publication_branch,
        "selection_decision_ref": {**selection_ref},
        "overview_path": model.overview_path,
        "decision_version": decision_version,
        "content_hash": content_hash,
        "files": [
            {
                "path": path[len(base) + 1:],
                "record_id": files[path]["record_id"],
                "record_type": files[path]["record_type"],
                "record_version": files[path]["record_version"],
                "subject": files[path]["subject"],
                "sha256": sha256(all_bytes[path]),
            }
            for path in sorted(all_bytes)
        ],
    }
    manifest_path = f"{base}/manifest.json"
    all_bytes[manifest_path] = encode(manifest)
    return all_bytes, manifest, manifest_path


def _source(path: str, commit: str, heading: str) -> dict[str, str]:
    return {"path": path, "commit": commit, "heading": heading}


def package_reference(repository: str, commit: str, manifest: Mapping[str, Any], manifest_path: str, manifest_bytes: bytes) -> dict[str, Any]:
    return {
        "repository": repository,
        "commit": commit,
        "registration_version": manifest["registration_version"],
        "candidate_id": manifest["candidate_id"],
        "manifest_path": manifest_path,
        "manifest_sha256": sha256(manifest_bytes),
    }


def validate_package(files: Mapping[str, bytes], manifest_path: str, source_commit: str, scope: Mapping[str, Any]) -> None:
    """Independent check of the frozen candidate before publication: fields, hashes, references."""
    manifest = json.loads(files[manifest_path])
    base = manifest_path.rsplit("/", 1)[0]
    listed = {entry["path"]: entry for entry in manifest["files"]}
    actual = {path[len(base) + 1:]: data for path, data in files.items() if path != manifest_path}
    if set(listed) != set(actual):
        raise CandidateError("the manifest inventory does not match the candidate files")
    records: dict[str, dict[str, Any]] = {}
    for relative, data in actual.items():
        if sha256(data) != listed[relative]["sha256"]:
            raise CandidateError(f"{relative} does not match its manifest hash")
        record = json.loads(data)
        if set(record) != {"schema_version", "record_type", "record_id", "subject", "record_version", "data"} or record["schema_version"] != 1:
            raise CandidateError(f"{relative} does not follow the record contract")
        if not all(isinstance(record[name], str) and record[name].strip() for name in ("record_type", "record_id", "subject")):
            raise CandidateError(f"{relative} has empty required text")
        if isinstance(record["record_version"], bool) or not isinstance(record["record_version"], int) or record["record_version"] < 1:
            raise CandidateError(f"{relative} has an invalid record_version")
        if relative.startswith("/") or ".." in relative.split("/"):
            raise CandidateError(f"{relative} is not a safe relative path")
        records[relative] = record
    identities = [(r["record_type"], r["record_id"]) for r in records.values()]
    if len(set(identities)) != len(identities):
        raise CandidateError("record identities are not unique")
    for relative, record in records.items():
        for reference in _references(record["data"]):
            target = records.get(reference["path"])
            if target is None or target["record_id"] != reference["record_id"] or target["record_version"] != reference["record_version"]:
                raise CandidateError(f"{relative} references {reference['path']}, which is not in the candidate at that version")
    if manifest["source_commit"] != source_commit:
        raise CandidateError("the manifest source commit differs from the assessed commit")
    selection = records["decisions/selection.json"]["data"]
    if selection["source_commit"] != manifest["source_commit"] or selection["publication_branch"] != manifest["publication_branch"] or selection["source_ref"] != manifest["source_ref"]:
        raise CandidateError("the manifest selection differs from the selection decision")
    milestones = sorted(r["data"]["milestone_id"] for r in records.values() if r["record_type"] == "milestone")
    if milestones != sorted(item["reference"] for item in scope["included"]):
        raise CandidateError("the candidate milestones differ from the confirmed scope")
    if not any(r["record_type"] == "review" for r in records.values()):
        raise CandidateError("the candidate has no review record")
    reviews = [r["data"] for r in records.values() if r["record_type"] == "review"]
    if any(data["outcome"] not in {"APPROVE", "REQUEST_CHANGES"} for data in reviews):
        raise CandidateError("a review outcome is invalid")
    if not any(data["outcome"] == "APPROVE" and data["reviewed_content_hash"] == manifest["content_hash"] for data in reviews):
        raise CandidateError("no approving review covers this exact candidate")


def _references(value: object) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        if {"record_id", "subject", "record_version", "path"} <= set(value):
            found.append(value)
        for item in value.values():
            found.extend(_references(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_references(item))
    return found


def receipt_and_index(
    *,
    project_id: str,
    confirmation_id: str,
    request_id: str,
    package_ref: Mapping[str, Any],
    owner_id: str,
    confirmed_at: str,
    previous_confirmation_ref: Mapping[str, Any] | None,
    previous_index: Mapping[str, Any] | None,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "confirmation_id": confirmation_id,
        "request_id": request_id,
        "project_id": project_id,
        "package_ref": dict(package_ref),
        "owner_id": owner_id,
        "confirmed_at": confirmed_at,
        "previous_confirmation_ref": None if previous_confirmation_ref is None else dict(previous_confirmation_ref),
    }
    receipt_path = f"{ROOT}/confirmations/{confirmation_id}.json"
    receipt_bytes = encode(receipt)
    reference = {"path": receipt_path, "sha256": sha256(receipt_bytes)}
    refs = list(previous_index["confirmation_refs"]) if previous_index else []
    refs.append(reference)
    index = {"schema_version": SCHEMA_VERSION, "project_id": project_id, "current_confirmation_ref": reference, "confirmation_refs": refs}
    return {receipt_path: receipt_bytes, f"{ROOT}/index.json": encode(index)}, reference
