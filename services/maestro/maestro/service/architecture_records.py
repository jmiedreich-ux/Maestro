"""Architecture foundation records: outcome mapping, output validation and versioned set building.

Everything here is deterministic. The architect supplies judgments (findings, code-direction
decisions, structure, specialist guidance); the service assigns identities, versions, hashes and
paths and renders the records defined by ``docs/schemas/architecture-loop.schema.json``.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable, Mapping, Sequence

from maestro.foundation import canonical_json

ROOT = ".maestro/architecture"
DISPOSITIONS = ("reuse", "update", "replace", "retire", "missing")
INVESTIGATION_SCHEMA = "architecture_investigation_v1"
STRUCTURE_SCHEMA = "architecture_structure_v1"
_KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_SAFE_AREA = re.compile(r"(?!/)(?!.*(?:^|/)\.\.?(?:/|$))[A-Za-z0-9._/-]+\Z")
ROLE_HEADINGS = ("Responsibility", "Authority", "Source area", "Inputs and outputs")
CONTEXT_HEADINGS = ("Verified facts", "Source references", "Knowledge gaps")
MEMORY_HEADINGS = ("Entries",)
OUTPUT_RULES = {
    "exact": ["investigation.json", "project-structure.json"],
    "patterns": [
        r"specialists/[A-Za-z0-9._/-]+/\.maestro/role-[a-z0-9]+(?:-[a-z0-9]+)*\.md",
        r"specialists/[A-Za-z0-9._/-]+/\.maestro/context\.md",
        r"specialists/[A-Za-z0-9._/-]+/\.maestro/memory\.md",
    ],
}


class FoundationError(ValueError):
    """The architect's foundation outputs do not satisfy the contract; the message says exactly what to fix."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def kebab(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


# ----------------------------------------------------------------------------- outcome mapping

def map_outcomes(package_ref: Mapping[str, Any], read: Callable[[str], bytes | None]) -> tuple[list[dict[str, Any]], dict[str, bytes]]:
    """Convert the confirmed package's milestone and requirement records into architecture outcome references.

    ``read`` returns the bytes of a repository path at the package's exact publishing commit. Returns the
    references and the verified record bytes keyed by their package-relative path.
    """
    manifest_path = package_ref["manifest_path"]
    manifest_bytes = read(manifest_path)
    if manifest_bytes is None or sha256(manifest_bytes) != package_ref["manifest_sha256"]:
        raise FoundationError("the confirmed registration manifest does not match its recorded hash")
    manifest = json.loads(manifest_bytes)
    base = manifest_path.rsplit("/", 1)[0]
    references: list[dict[str, Any]] = []
    records: dict[str, bytes] = {}
    for entry in manifest["files"]:
        if entry["record_type"] not in {"milestone", "requirement"}:
            continue
        path = f"{base}/{entry['path']}"
        data = read(path)
        if data is None or sha256(data) != entry["sha256"]:
            raise FoundationError(f"{entry['path']} does not match the manifest inventory")
        record = json.loads(data)
        if (record["record_type"], record["record_id"], record["record_version"], record["subject"]) != (
            entry["record_type"], entry["record_id"], entry["record_version"], entry["subject"]
        ):
            raise FoundationError(f"{entry['path']} does not carry the identity the manifest lists")
        references.append({"id": entry["record_id"], "subject": entry["subject"], "version": int(entry["record_version"]),
                           "path": path, "sha256": entry["sha256"], "commit": package_ref["commit"]})
        records[entry["path"]] = data
    if not any(r["path"].split("/")[-2] == "milestones" for r in references):
        raise FoundationError("the confirmed registration has no milestone records")
    return sorted(references, key=lambda r: (r["path"], r["id"], r["version"])), records


def milestone_ids(references: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted(r["id"] for r in references if r["path"].split("/")[-2] == "milestones")


# ----------------------------------------------------------------------------- output validation

def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FoundationError(f"{name} must be nonempty text")
    return value.strip()


def _evidence(items: object, commit: str, exists: Callable[[str], bool], where: str) -> list[dict[str, str]]:
    if not isinstance(items, list):
        raise FoundationError(f"{where}.evidence must be a list")
    checked = []
    for item in items:
        if not isinstance(item, Mapping) or set(item) != {"path", "commit", "locator"}:
            raise FoundationError(f"{where}.evidence entries need path, commit and locator")
        path = _text(item["path"], f"{where}.evidence.path")
        if item["commit"] != commit:
            raise FoundationError(f"{where}.evidence commit must be the assigned source commit {commit}")
        if not exists(path):
            raise FoundationError(f"{where}.evidence cites {path}, which does not exist in the source at the assigned commit")
        checked.append({"path": path, "commit": commit, "locator": _text(item["locator"], f"{where}.evidence.locator")})
    return checked


def validate_findings(findings: Sequence[Mapping[str, Any]], commit: str, exists: Callable[[str], bool]) -> None:
    """Every cited source path must exist at the assigned commit; a finding with no source states the missing information."""
    for finding in findings:
        for ref in finding["source_refs"]:
            if ref["commit"] != commit:
                raise FoundationError(f"finding {finding['local_key']} cites commit {ref['commit']}, not the assigned {commit}")
            if not exists(ref["path"]):
                raise FoundationError(f"finding {finding['local_key']} cites {ref['path']}, which does not exist in the source at the assigned commit")


def validate_investigation(document: object, finding_keys: set[str], outcome_ids: set[str], required_outcomes: set[str], commit: str, exists: Callable[[str], bool]) -> dict[str, Any]:
    if not isinstance(document, Mapping) or set(document) != {"schema", "summary", "decisions"} or document["schema"] != INVESTIGATION_SCHEMA:
        raise FoundationError(f"investigation.json must contain exactly schema ({INVESTIGATION_SCHEMA}), summary and decisions")
    _text(document["summary"], "investigation.summary")
    decisions = document["decisions"]
    if not isinstance(decisions, list) or not decisions:
        raise FoundationError("investigation.decisions must be a nonempty list")
    keys: set[str] = set()
    cited: set[str] = set()
    for decision in decisions:
        fields = {"local_key", "subject", "disposition", "rationale", "code_paths", "evidence", "outcome_ids", "finding_keys"}
        if not isinstance(decision, Mapping) or set(decision) != fields:
            raise FoundationError(f"each investigation decision needs exactly: {', '.join(sorted(fields))}")
        key = _text(decision["local_key"], "decision.local_key")
        if key in keys:
            raise FoundationError(f"decision local_key {key} is used twice")
        keys.add(key)
        _text(decision["subject"], f"decision {key} subject")
        _text(decision["rationale"], f"decision {key} rationale")
        if decision["disposition"] not in DISPOSITIONS:
            raise FoundationError(f"decision {key} disposition must be one of {', '.join(DISPOSITIONS)}")
        paths = decision["code_paths"]
        if not isinstance(paths, list) or not all(isinstance(p, str) and p for p in paths):
            raise FoundationError(f"decision {key} code_paths must be a list of paths")
        if decision["disposition"] != "missing" and not paths:
            raise FoundationError(f"decision {key} needs code_paths unless its disposition is missing")
        for path in paths:
            if not exists(path):
                raise FoundationError(f"decision {key} names {path}, which does not exist in the source at the assigned commit")
        _evidence(decision["evidence"], commit, exists, f"decision {key}")
        ids = decision["outcome_ids"]
        if not isinstance(ids, list) or not ids or not all(i in outcome_ids for i in ids):
            raise FoundationError(f"decision {key} outcome_ids must be a nonempty list of confirmed outcome record ids (one of: {', '.join(sorted(outcome_ids))})")
        cited.update(ids)
        fk = decision["finding_keys"]
        if not isinstance(fk, list) or not set(fk) <= finding_keys:
            raise FoundationError(f"decision {key} finding_keys must name findings reported in the response")
    uncovered = sorted(required_outcomes - cited)
    if uncovered:
        raise FoundationError(f"no decision covers these confirmed milestone outcomes: {', '.join(uncovered)}")
    return dict(document)


def validate_structure(document: object, commit: str, exists_dir: Callable[[str], bool]) -> dict[str, Any]:
    if not isinstance(document, Mapping) or set(document) != {"schema", "summary", "locations", "specialists"} or document["schema"] != STRUCTURE_SCHEMA:
        raise FoundationError(f"project-structure.json must contain exactly schema ({STRUCTURE_SCHEMA}), summary, locations and specialists")
    _text(document["summary"], "structure.summary")
    locations, specialists = document["locations"], document["specialists"]
    if not isinstance(locations, list) or not locations:
        raise FoundationError("structure.locations must be a nonempty list")
    if not isinstance(specialists, list) or not specialists:
        raise FoundationError("structure.specialists must be a nonempty list")
    owners = set()
    seen_areas: set[str] = set()
    keys: set[str] = set()
    for specialist in specialists:
        if not isinstance(specialist, Mapping) or set(specialist) != {"local_key", "subject", "source_area", "role_title", "owner"}:
            raise FoundationError("each specialist needs local_key, subject, source_area, role_title and owner")
        key = _text(specialist["local_key"], "specialist.local_key")
        if key in keys:
            raise FoundationError(f"specialist local_key {key} is used twice")
        keys.add(key)
        _text(specialist["subject"], f"specialist {key} subject")
        title = _text(specialist["role_title"], f"specialist {key} role_title")
        if not _KEBAB.fullmatch(kebab(title)):
            raise FoundationError(f"specialist {key} role_title must contain letters or digits")
        area = _text(specialist["source_area"], f"specialist {key} source_area").strip("/")
        if not _SAFE_AREA.fullmatch(area):
            raise FoundationError(f"specialist {key} source_area must be a relative path inside the source")
        if not exists_dir(area):
            raise FoundationError(f"specialist {key} source_area {area} is not a directory in the source at the assigned commit")
        if area in seen_areas:
            raise FoundationError(f"source area {area} has two specialists; each context and memory file has one owner")
        seen_areas.add(area)
        owners.add(_text(specialist["owner"], f"specialist {key} owner"))
    for location in locations:
        if not isinstance(location, Mapping) or set(location) != {"current_path", "intended_path", "responsibility", "owner", "shared_boundaries", "planned_move"}:
            raise FoundationError("each location needs current_path, intended_path, responsibility, owner, shared_boundaries and planned_move")
        _text(location["intended_path"], "location.intended_path")
        _text(location["responsibility"], "location.responsibility")
        _text(location["owner"], "location.owner")
        if location["current_path"] is not None:
            _text(location["current_path"], "location.current_path")
        if not isinstance(location["planned_move"], bool) or not isinstance(location["shared_boundaries"], list) or not all(isinstance(b, str) and b for b in location["shared_boundaries"]):
            raise FoundationError("location planned_move must be true or false and shared_boundaries a list of text")
        if location["planned_move"] is False and location["current_path"] != location["intended_path"]:
            raise FoundationError(f"location {location['intended_path']} is not a planned move, so its current_path must equal its intended_path")
    return dict(document)


def _headings(text: str) -> list[str]:
    return [line.lstrip("#").strip() for line in text.splitlines() if line.startswith("#")]


def validate_specialist_files(structure: Mapping[str, Any], files: Mapping[str, bytes]) -> list[dict[str, Any]]:
    """Match the specialist Markdown files under output/ to the structure; return one entry per specialist."""
    by_area: dict[str, dict[str, str]] = {}
    for relative in files:
        if not relative.startswith("specialists/"):
            continue
        area, _, name = relative[len("specialists/"):].rpartition("/.maestro/")
        kind = "context" if name == "context.md" else "memory" if name == "memory.md" else "role"
        by_area.setdefault(area, {})[kind if kind != "role" else f"role:{name}"] = relative
    result = []
    for specialist in structure["specialists"]:
        area = specialist["source_area"].strip("/")
        found = by_area.pop(area, {})
        role_name = f"role-{kebab(specialist['role_title'])}.md"
        role = found.get(f"role:{role_name}")
        if role is None or len([k for k in found if k.startswith("role:")]) != 1:
            raise FoundationError(f"specialist {specialist['local_key']} needs exactly one role file named {role_name} under specialists/{area}/.maestro/")
        context = found.get("context")
        if context is None:
            raise FoundationError(f"specialist {specialist['local_key']} needs specialists/{area}/.maestro/context.md")
        title = specialist["role_title"].strip()
        role_text = files[role].decode("utf-8")
        if not role_text.lstrip().startswith("#") or title.lower() not in role_text.lstrip().splitlines()[0].lower():
            raise FoundationError(f"{role} must begin with the role title '{title}' as its first heading")
        for path, headings in ((role, ROLE_HEADINGS), (context, CONTEXT_HEADINGS), (found.get("memory"), MEMORY_HEADINGS)):
            if path is None:
                continue
            present = [h.lower() for h in _headings(files[path].decode("utf-8"))]
            missing = [h for h in headings if h.lower() not in present]
            if missing:
                raise FoundationError(f"{path} lacks the required heading(s): {', '.join(missing)}")
        result.append({"specialist": dict(specialist), "area": area, "role": role, "context": context, "memory": found.get("memory")})
    if by_area:
        raise FoundationError(f"specialist files exist for areas the structure does not list: {', '.join(sorted(by_area))}")
    return result


# ----------------------------------------------------------------------------- record building

def repo_path(relative: str) -> str:
    """specialists/<area>/.maestro/<file> in the output root becomes <area>/.maestro/<file> in the repository."""
    return relative[len("specialists/"):]


def saved_findings(findings: Sequence[Mapping[str, Any]], identities: Mapping[str, tuple[str, int]]) -> list[dict[str, Any]]:
    saved = []
    for finding in findings:
        identifier, version = identities[finding["local_key"]]
        saved.append({
            "id": identifier, "version": version, "subject": finding["subject"], "severity": finding["severity"],
            "explanation": finding["explanation"], "impact": finding["impact"], "requested_correction": finding["requested_correction"],
            "source_refs": [dict(r) for r in finding["source_refs"]], "missing_information": finding["missing_information"],
            "affected_items": [dict(a) for a in finding["affected_items"]],
        })
    return saved


def build_foundation_set(
    *,
    project_id: str,
    activity_id: str,
    version: int,
    registration_ref: Mapping[str, Any],
    source_commit: str,
    decision_version: int,
    outcomes: Sequence[Mapping[str, Any]],
    findings: Sequence[Mapping[str, Any]],
    finding_identities: Mapping[str, tuple[str, int]],
    investigation: Mapping[str, Any],
    structure: Mapping[str, Any],
    specialists: Sequence[Mapping[str, Any]],
    specialist_files: Mapping[str, bytes],
    specialist_commit: str,
    owner_decisions: Sequence[Mapping[str, Any]],
    owner_id: str,
) -> tuple[dict[str, bytes], dict[str, Any], str]:
    """Return (repository files, manifest, manifest path) for the foundations stage of one architecture version."""
    base = f"{ROOT}/versions/{version}"
    common = {"schema_version": 1, "project_id": project_id, "activity_id": activity_id, "version": 1,
              "registration_ref": dict(registration_ref), "source_commit": source_commit}
    by_id = {o["id"]: o for o in outcomes}
    investigation_record = {
        **common, "id": "investigation", "subject": "Code investigation",
        "findings": saved_findings(findings, finding_identities),
        "decisions": [
            {"id": f"code-direction-{n}", "subject": d["subject"], "disposition": d["disposition"], "rationale": d["rationale"],
             "code_paths": list(d["code_paths"]), "evidence": [dict(e) for e in d["evidence"]],
             "outcome_refs": [dict(by_id[i]) for i in d["outcome_ids"]]}
            for n, d in enumerate(investigation["decisions"], 1)
        ],
    }
    investigation_path = f"{base}/investigation.json"
    inv_ref = {"id": "investigation", "subject": "Code investigation", "version": 1, "path": "investigation.json"}
    decisions = []
    for n, d in enumerate(investigation_record["decisions"], 1):
        decisions.append({
            "id": f"decision-{len(decisions) + 1}", "subject": d["subject"], "version": 1, "source_question_id": None, "source_finding_ref": None,
            "answer": f"{d['disposition']}: {d['rationale']}", "authority": {"kind": "architect", "identity": "project_architect"},
            "affected_items": [inv_ref], "rationale": d["rationale"],
        })
    for owner in owner_decisions:
        decisions.append({
            "id": f"decision-{len(decisions) + 1}", "subject": owner["subject"], "version": 1, "source_question_id": owner["question_id"], "source_finding_ref": None,
            "answer": owner["answer"], "authority": {"kind": "owner", "identity": owner_id},
            "affected_items": [inv_ref], "rationale": owner["rationale"],
        })
    decisions_record = {**common, "id": "decisions", "subject": "Architecture decisions", "decision_version": f"d{decision_version}", "decisions": decisions}
    specialist_records = []
    inventory_specialists = []
    for number, entry in enumerate(specialists, 1):
        specialist = entry["specialist"]
        refs = {}
        for kind in ("role", "context", "memory"):
            relative = entry[kind]
            if relative is None:
                refs[kind] = None
                continue
            path = repo_path(relative)
            data = specialist_files[relative]
            record_type = {"role": "specialist_role", "context": "specialist_context", "memory": "specialist_memory"}[kind]
            identifier = f"specialist-{number}-{kind}"
            subject = f"{specialist['subject']} — {kind}"
            refs[kind] = {"id": identifier, "subject": subject, "version": 1, "path": path, "sha256": sha256(data), "commit": specialist_commit}
            inventory_specialists.append({"record_type": record_type, "id": identifier, "subject": subject, "version": 1, "path": path,
                                          "sha256": sha256(data), "commit": specialist_commit, "dependencies": []})
        specialist_records.append({
            "id": f"specialist-{number}", "subject": specialist["subject"], "source_area": entry["area"],
            "role_ref": refs["role"], "context_ref": refs["context"], "memory_ref": refs["memory"], "context_owner": specialist["owner"],
        })
    structure_record = {
        **common, "id": "project-structure", "subject": "Project structure",
        "locations": [dict(loc) for loc in structure["locations"]], "specialists": specialist_records,
    }
    files = {
        investigation_path: encode(investigation_record),
        f"{base}/decisions.json": encode(decisions_record),
        f"{base}/project-structure.json": encode(structure_record),
    }
    dec_ref = {"id": "decisions", "subject": "Architecture decisions", "version": 1, "path": "decisions.json"}
    inventory = [
        {"record_type": "investigation", "id": "investigation", "subject": "Code investigation", "version": 1, "path": "investigation.json",
         "sha256": sha256(files[investigation_path]), "commit": None, "dependencies": []},
        {"record_type": "decisions", "id": "decisions", "subject": "Architecture decisions", "version": 1, "path": "decisions.json",
         "sha256": sha256(files[f"{base}/decisions.json"]), "commit": None, "dependencies": [inv_ref]},
        {"record_type": "project_structure", "id": "project-structure", "subject": "Project structure", "version": 1, "path": "project-structure.json",
         "sha256": sha256(files[f"{base}/project-structure.json"]), "commit": None, "dependencies": [inv_ref]},
        *inventory_specialists,
    ]
    inventory.sort(key=lambda e: (e["path"], e["id"]))
    input_refs = sorted((dict(o) for o in outcomes), key=lambda r: (r["path"], r["id"], r["version"]))
    content = {
        "registration_ref": dict(registration_ref), "source_commit": source_commit, "decision_version": f"d{decision_version}",
        "decision_ref": dec_ref, "input_refs": input_refs, "carried_forward": [], "inventory": inventory,
    }
    reviewed_content_hash = sha256(canonical_json(content).encode("utf-8"))
    manifest = {
        **{**common, "version": version}, "id": "manifest", "subject": "Architecture foundations manifest", "stage": "foundations",
        "decision_version": f"d{decision_version}", "input_refs": input_refs, "reviewed_content_hash": reviewed_content_hash,
        "inventory": inventory, "carried_forward": [], "decision_ref": dec_ref,
    }
    manifest_path = f"{base}/manifest.json"
    files[manifest_path] = encode(manifest)
    return files, manifest, manifest_path


def discovery_index(project_id: str, previous: Mapping[str, Any] | None, version: int, commit: str, manifest_path: str, manifest_sha256: str, reviewed_hash: str) -> dict[str, Any]:
    ref = {"version": version, "commit": commit, "manifest_path": manifest_path, "manifest_sha256": manifest_sha256, "reviewed_content_hash": reviewed_hash}
    versions = [dict(v) for v in (previous or {}).get("versions", []) if v["version"] != version]
    versions.append(ref)
    return {"schema_version": 1, "project_id": project_id, "versions": versions, "working_ref": ref, "confirmed_ref": (previous or {}).get("confirmed_ref")}


def set_ref(commit: str, manifest: Mapping[str, Any], manifest_path: str, manifest_bytes: bytes) -> dict[str, Any]:
    return {"version": manifest["version"], "commit": commit, "manifest_path": manifest_path,
            "manifest_sha256": sha256(manifest_bytes), "reviewed_content_hash": manifest["reviewed_content_hash"]}
