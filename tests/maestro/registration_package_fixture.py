from __future__ import annotations

import hashlib
from collections.abc import Mapping

from maestro.planning.registration_records import (
    RegistrationPackageContext,
    canonical_record_bytes,
    package_content_hash,
)


def complete_package(
    context: RegistrationPackageContext,
    *,
    registration_version: int,
    candidate_id: str,
    previous_registration_ref: Mapping[str, object] | None = None,
    review_context: Mapping[str, object] | None = None,
    include_review: bool = True,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Build a complete contract-valid package for source-level tests."""
    outcomes = context.source_inventory.outcomes
    review_context = dict(review_context or {
        "architect_assignment_id": "project_architect-assignment",
        "architect_run_id": "project_architect-run",
        "assignment_id": "reviewer-assignment",
        "run_id": "reviewer-run",
        "reviewer_identity": "fidelity_reviewer",
        "review_round": 1,
        "review_limit": 2,
    })

    def record_ref(path: str, record: Mapping[str, object]) -> dict[str, object]:
        return {
            "record_id": record["record_id"],
            "subject": record["subject"],
            "record_version": record["record_version"],
            "path": path,
        }

    def source_ref(path: str, subject: str) -> dict[str, object]:
        return {
            "record_id": "source-" + hashlib.sha256(path.encode()).hexdigest()[:16],
            "subject": subject,
            "record_version": 1,
            "path": path,
            "repository": context.source_repository,
            "commit": context.source_inventory.source_commit,
            "locator": path,
        }

    records: dict[str, dict[str, object]] = {}
    decision_path = f"decisions/{context.selection_decision_ref}.json"
    decision = {
        "schema_version": 1,
        "record_type": "decision",
        "record_id": context.selection_decision_ref,
        "subject": "Registration source and publication selection",
        "record_version": 1,
        "data": {
            "question": None,
            "answers": [],
            "resolution": "Use the exact saved source, scope, roles, and publication destination.",
            "authority": {"kind": "service", "identity": "registration-intake"},
            "affected_refs": [],
            "supersedes_ref": None,
        },
    }
    records[decision_path] = decision
    change_decision_path = f"decisions/decision-{registration_version}.json"
    if change_decision_path != decision_path:
        records[change_decision_path] = {
            "schema_version": 1,
            "record_type": "decision",
            "record_id": f"decision-{registration_version}",
            "subject": "Registration version decision",
            "record_version": registration_version,
            "data": {
                "question": None,
                "answers": [],
                "resolution": "Preserve the reviewed content for this registration version.",
                "authority": {"kind": "owner", "identity": "owner-local"},
                "affected_refs": [],
                "supersedes_ref": None,
            },
        }

    requirement_refs: dict[str, dict[str, object]] = {}
    milestone_refs: dict[str, dict[str, object]] = {}
    for outcome in outcomes:
        requirement_path = f"requirements/{outcome.milestone}-completion.json"
        milestone_path = f"milestones/{outcome.milestone}.json"
        requirement = {
            "schema_version": 1,
            "record_type": "requirement",
            "record_id": f"{outcome.milestone}-completion",
            "subject": f"{outcome.subject} completion",
            "record_version": outcome.version,
            "data": {
                "applies_to": {
                    "record_id": outcome.milestone,
                    "subject": outcome.subject,
                    "record_version": outcome.version,
                    "path": milestone_path,
                },
                "expected_result": f"{outcome.subject} is demonstrably complete.",
                "conditions": ["The supplied milestone outcome is preserved."],
                "pass_boundary": "All stated completion evidence passes.",
                "verification": ["Inspect the supplied outcome and its evidence."],
                "accepted_exception": None,
                "source_refs": [
                    source_ref(
                        context.source_inventory.overview_path,
                        "Project overview",
                    )
                ],
                "journey": [],
            },
        }
        milestone = {
            "schema_version": 1,
            "record_type": "milestone",
            "record_id": outcome.milestone,
            "subject": outcome.subject,
            "record_version": outcome.version,
            "data": {
                "declaration_id": outcome.declaration,
                "milestone_id": outcome.milestone,
                "purpose": f"Deliver {outcome.subject}.",
                "included": [outcome.subject],
                "excluded": [],
                "dependencies": [],
                "requirement_refs": [record_ref(requirement_path, requirement)],
                "source_refs": [
                    source_ref(
                        context.source_inventory.overview_path,
                        "Project overview",
                    )
                ],
            },
        }
        records[requirement_path] = requirement
        records[milestone_path] = milestone
        requirement_refs[outcome.milestone] = record_ref(requirement_path, requirement)
        milestone_refs[outcome.milestone] = record_ref(milestone_path, milestone)

    for designation in dict.fromkeys(item.declaration for item in outcomes):
        declaration_path = f"declarations/{designation}.json"
        declaration = {
            "schema_version": 1,
            "record_type": "declaration",
            "record_id": designation,
            "subject": next(
                item.declaration_subject
                for item in outcomes
                if item.declaration == designation
            ),
            "record_version": max(
                item.declaration_version for item in outcomes if item.declaration == designation
            ),
            "data": {
                "designation": designation,
                "milestone_refs": [
                    milestone_refs[item.milestone]
                    for item in outcomes
                    if item.declaration == designation
                ],
                "source_refs": [
                    source_ref(
                        next(
                            reference.path
                            for reference in context.source_inventory.source_references
                            if reference.source_type == "Milestone declaration"
                        )
                        if any(
                            reference.source_type == "Milestone declaration"
                            for reference in context.source_inventory.source_references
                        )
                        else context.source_inventory.overview_path,
                        f"{designation} declaration source",
                    )
                ],
            },
        }
        records[declaration_path] = declaration

    summary = {
        "schema_version": 1,
        "record_type": "summary",
        "record_id": f"summary-{context.project_id}",
        "subject": "Project registration summary",
        "record_version": registration_version,
        "data": {
            "project_id": context.project_id,
            "purpose": "Preserve the supplied project outcomes for registration.",
            "scope": {
                "included": [item.subject for item in outcomes],
                "excluded": [],
            },
            "priorities": ["Preserve the supplied outcomes and completion boundaries."],
            "assessment_outcome": "ready",
            "project_requirement_refs": list(requirement_refs.values()),
        },
    }
    records["summary.json"] = summary
    records["conventions.json"] = {
        "schema_version": 1,
        "record_type": "naming_conventions",
        "record_id": f"conventions-{context.project_id}",
        "subject": "Registration naming conventions",
        "record_version": 1,
        "data": {
            "declaration_designations": [
                {"code": value, "subject": f"{value} declaration designation"}
                for value in dict.fromkeys(item.declaration for item in outcomes)
            ],
            "record_types": [
                {"code": value, "subject": value.replace("_", " ").title()}
                for value in (
                    "summary", "declaration", "naming_conventions", "milestone",
                    "requirement", "assessment", "review", "decision",
                )
            ],
            "prefixes": [{"code": "registration", "subject": "Registration records"}],
            "decision_refs": [record_ref(decision_path, decision)],
        },
    }
    assessment_path = f"assessments/assessment-{candidate_id}.json"
    assessment = {
        "schema_version": 1,
        "record_type": "assessment",
        "record_id": f"assessment-{candidate_id}",
        "subject": "Registration assessment",
        "record_version": registration_version,
        "data": {
            "assignment_id": review_context.get(
                "architect_assignment_id", "project_architect-assignment"
            ),
            "run_id": review_context.get(
                "architect_run_id", "project_architect-run"
            ),
            "source_commit": context.source_inventory.source_commit,
            "decision_version": context.decision_version,
            "summary": "The complete supplied package is ready for independent review.",
            "findings": [{
                "local_key": f"finding-{registration_version}",
                "subject": "Registration version evidence",
                "severity": "non_blocking",
                "explanation": "This record identifies the exact assessed registration version.",
                "impact": "Comparison can explain a changed package record.",
                "requested_correction": "No correction is required.",
                "source_refs": [{
                    "path": context.source_inventory.overview_path,
                    "commit": context.source_inventory.source_commit,
                    "locator": context.source_inventory.overview_path,
                }],
                "affected_items": [{
                    "record_id": summary["record_id"],
                    "subject": summary["subject"],
                    "record_version": summary["record_version"],
                }],
            }],
        },
    }
    records[assessment_path] = assessment

    content_hash = package_content_hash(records)
    review_id = f"review-{candidate_id}"
    review_path = f"reviews/{review_id}.json"
    review = {
        "schema_version": 1,
        "record_type": "review",
        "record_id": review_id,
        "subject": "Independent registration review",
        "record_version": int(review_context["review_round"]),
        "data": {
            **{
                key: value for key, value in review_context.items()
                if key not in {"architect_assignment_id", "architect_run_id"}
            },
            "reviewed_content_hash": content_hash,
            "reviewed_assessment_ref": record_ref(assessment_path, assessment),
            "outcome": "APPROVE",
            "findings": [],
        },
    }
    if include_review:
        records[review_path] = review
    manifest: dict[str, object] = {
        "project_id": context.project_id,
        "registration_version": registration_version,
        "candidate_id": candidate_id,
        "previous_registration_ref": (
            None if previous_registration_ref is None else dict(previous_registration_ref)
        ),
        "source_repository": context.source_repository,
        "source_commit": context.source_inventory.source_commit,
        "overview_path": context.source_inventory.overview_path,
        "decision_version": context.decision_version,
        "source_ref": context.source_inventory.source_ref,
        "publication_branch": context.publication_branch,
        "destination_snapshot_reference": context.destination_snapshot_reference,
        "selection_decision_ref": context.selection_decision_ref,
        "content_hash": content_hash,
        "files": [
            {
                "path": path,
                "record_id": record["record_id"],
                "record_type": record["record_type"],
                "record_version": record["record_version"],
                "subject": record["subject"],
                "sha256": hashlib.sha256(canonical_record_bytes(record)).hexdigest(),
            }
            for path, record in sorted(records.items())
        ],
    }
    return manifest, records
