"""Architecture review and confirmation records.

A review record binds the independent reviewer's outcome and findings to the exact published set it
read. The confirmation record binds the Owner's decision to that set. Both are added to a published
version after its content, so they update the manifest and publication reference without changing the
reviewed content hash (which excludes them).
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from maestro.foundation import canonical_json

from .architecture_records import ROOT, FoundationError, encode, saved_findings, sha256

REVIEW_ROOT_SUFFIX = "reviews"
CONTENT_TYPES = {"investigation", "project_structure", "development_milestone", "work_packet", "qa_plan", "decisions", "specialist_role", "specialist_context", "specialist_memory"}


def check_reviewed_set(response_set: Mapping[str, Any], working: Mapping[str, Any]) -> None:
    """The reviewer must name the exact set it was given; anything else means it read something else."""
    if response_set.get("manifest_sha256") != working["manifest_sha256"] or response_set.get("reviewed_content_hash") != working["reviewed_content_hash"]:
        raise FoundationError("the review names a different set than the one assigned; it cannot cover the working version")


def reviewed_refs(manifest: Mapping[str, Any], manifest_path: str, commit: str) -> list[dict[str, Any]]:
    """Every content record the reviewer was given, as exact published references: this set's own files and the records it carries forward."""
    base = manifest_path.rsplit("/", 1)[0]
    refs = [
        {"id": e["id"], "subject": e["subject"], "version": e["version"], "path": f"{base}/{e['path']}", "sha256": e["sha256"], "commit": commit}
        for e in manifest["inventory"] if e["record_type"] in CONTENT_TYPES
    ]
    refs += [dict(c["record_ref"]) for c in manifest["carried_forward"]]
    if not refs:
        raise FoundationError("the working set lists no reviewable content")
    return sorted(refs, key=lambda r: (r["path"], r["id"], r["version"]))


def listing(manifest: Mapping[str, Any], manifest_path: str, commit: str) -> list[dict[str, Any]]:
    """Every saved record of a working version for the Owner: this set's own files (with review and confirmation) and the records it carries forward."""
    base = manifest_path.rsplit("/", 1)[0]
    rows = [{"kind": e["record_type"], "id": e["id"], "subject": e["subject"], "version": e["version"], "path": f"{base}/{e['path']}", "sha256": e["sha256"], "commit": e["commit"] or commit}
            for e in manifest["inventory"]]
    rows += [{"kind": "carried_forward", **{k: c["record_ref"][k] for k in ("id", "subject", "version", "path", "sha256", "commit")}} for c in manifest["carried_forward"]]
    return sorted(rows, key=lambda r: (r["path"], r["id"]))


def review_id(number: int) -> str:
    return f"review-{number}"


def build_review(
    *, project_id: str, activity_id: str, number: int, registration_ref: Mapping[str, Any], source_commit: str, assignment_id: str, run_id: str,
    working: Mapping[str, Any], manifest: Mapping[str, Any], outcome: str, findings: Sequence[Mapping[str, Any]], identities: Mapping[str, tuple[str, int]],
) -> dict[str, Any]:
    return {
        "schema_version": 1, "project_id": project_id, "activity_id": activity_id, "id": review_id(number), "subject": f"Independent review {number}", "version": 1,
        "registration_ref": dict(registration_ref), "source_commit": source_commit, "reviewer_assignment_id": assignment_id, "reviewer_run_id": run_id,
        "reviewed_set": {k: working[k] for k in ("version", "commit", "manifest_path", "manifest_sha256", "reviewed_content_hash")},
        "reviewed_refs": reviewed_refs(manifest, working["manifest_path"], working["commit"]), "outcome": outcome,
        "findings": saved_findings(findings, identities), "retained_coverage": [],
    }


def with_record(manifest: Mapping[str, Any], *, record_type: str, record: Mapping[str, Any], relative: str, stage: str) -> tuple[dict[str, Any], bytes]:
    """The manifest after one more review or confirmation record is added to the same version."""
    data = encode(record)
    entry = {"record_type": record_type, "id": record["id"], "subject": record["subject"], "version": record["version"], "path": relative, "sha256": sha256(data),
             "commit": None, "dependencies": []}
    inventory = [e for e in manifest["inventory"] if e["id"] != entry["id"]] + [entry]
    inventory.sort(key=lambda e: (e["path"], e["id"]))
    updated = {**manifest, "inventory": inventory, "stage": stage}
    return updated, data


def build_confirmation(
    *, project_id: str, activity_id: str, registration_ref: Mapping[str, Any], source_commit: str, operation_id: str, request_id: str, owner_id: str, confirmed_at: str,
    expected: Mapping[str, Any], accepted: Sequence[Mapping[str, Any]], review_refs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1, "project_id": project_id, "activity_id": activity_id, "id": "confirmation", "subject": "Owner confirmation", "version": 1,
        "registration_ref": dict(registration_ref), "source_commit": source_commit, "operation_id": operation_id, "request_id": request_id, "owner_id": owner_id,
        "confirmed_at": confirmed_at, "expected_working_ref": dict(expected), "accepted_limitations": [dict(a) for a in accepted], "review_refs": [dict(r) for r in review_refs],
    }


def coverage_valid(last_review: Mapping[str, Any] | None, working: Mapping[str, Any] | None) -> bool:
    return bool(last_review and working and last_review["outcome"] == "APPROVE" and last_review["reviewed_content_hash"] == working["reviewed_content_hash"])


def canonical_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8"))


__all__ = ["ROOT", "build_confirmation", "build_review", "canonical_hash", "check_reviewed_set", "coverage_valid", "listing", "review_id", "reviewed_refs", "with_record"]
