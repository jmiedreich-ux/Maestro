"""Synthetic discovery: fixture-only project discovery normalization and inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .config import REPOSITORY_ROOT

_DISCOVERY_FIXTURE_ROOT = REPOSITORY_ROOT / "fixtures" / "alpha" / "project-discovery"

_REQUIRED_AREAS: dict[str, dict[str, str]] = {
    "identity": {
        "project_name": "string",
        "repository_identifier": "string",
        "default_branch": "string",
        "adapter_version": "string",
        "process_version": "string",
    },
    "authority": {
        "architecture_paths": "array",
        "plan_paths": "array",
        "handoff_path": "string",
        "rules_sop_path": "string",
        "task_issue_conventions": "string",
    },
    "delivery": {
        "branch_pr_merge_policy": "string",
        "owner_acceptance_policy": "string",
        "deployment_rollback_policy": "string",
    },
    "verification": {
        "build_commands": "array",
        "test_commands": "array",
        "integration_commands": "array",
        "ui_qa_commands": "array",
        "evidence_rules": "string",
        "untested_handling": "string",
    },
    "roles": {
        "specialist_overlays": "array",
        "reviewer_route": "string",
        "qa_murphy_policy": "string",
        "local_cloud_eligibility": "string",
    },
    "operations": {
        "environment_reference_names": "array",
        "secret_reference_names": "array",
        "resource_locks": "array",
        "notification_policy": "string",
    },
    "exceptions": {
        "disposition": "string",
        "items": "array",
    },
}


def validate_discovery_fixture_name(fixture_name: Any) -> str:
    """Validate a discovery_fixture value is a safe basename string."""
    if not isinstance(fixture_name, str) or not fixture_name.strip():
        raise ValueError("discovery_fixture must be a non-empty string")
    name = fixture_name.strip()
    if not name or "/" in name or "\\" in name or name.startswith(".."):
        raise ValueError("discovery_fixture must be a single filename without path separators or traversal")
    return name


def load_and_validate_discovery_fixture(fixture_name: str) -> dict[str, Any]:
    """Open, parse, and validate one discovery fixture file.

    Rejects missing files, malformed JSON, unknown keys, and schema violations.
    """
    fixture_path = _DISCOVERY_FIXTURE_ROOT / fixture_name
    if fixture_path.is_symlink():
        raise ValueError(f"Discovery fixture must not be a symlink: {fixture_name}")
    if not fixture_path.is_file():
        raise ValueError(f"Discovery fixture file not found: {fixture_name}")
    if _resolves_outside_root(fixture_path):
        raise ValueError(f"Discovery fixture resolves outside fixture root: {fixture_name}")
    raw = fixture_path.read_bytes()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in discovery fixture: {exc}") from exc
    _validate_discovery_schema(data)
    return data


def compute_fixture_digest(fixture_name: str) -> str:
    """SHA-256 hex digest of the raw fixture file contents."""
    fixture_path = _DISCOVERY_FIXTURE_ROOT / fixture_name
    return hashlib.sha256(fixture_path.read_bytes()).hexdigest()


def build_inventory(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize snapshot into inventory with per-leaf status and summary."""
    conflicts = data.get("conflicts")
    area_inventory: dict[str, dict[str, dict[str, Any]]] = {}
    confirmed = 0
    missing = 0
    conflicting = 0

    for area, leaves in _REQUIRED_AREAS.items():
        area_data = data.get(area, {})
        leaf_map: dict[str, dict[str, Any]] = {}
        for leaf, leaf_type in leaves.items():
            dotted = f"{area}.{leaf}"
            if conflicts and dotted in conflicts:
                raw_obs = conflicts[dotted]
                normalized_obs = _normalize_conflict_observed(raw_obs, area, leaf)
                leaf_map[leaf] = {"status": "conflicting", "observed_values": normalized_obs}
                conflicting += 1
            elif leaf in area_data:
                normalized = _normalize_leaf(area_data[leaf], leaf_type)
                leaf_map[leaf] = {"status": "confirmed", "value": normalized}
                confirmed += 1
            else:
                leaf_map[leaf] = {"status": "missing"}
                missing += 1
        area_inventory[area] = leaf_map

    return {
        "areas": area_inventory,
        "summary": {"confirmed": confirmed, "missing": missing, "conflicting": conflicting},
        "reviewable": missing == 0 and conflicting == 0,
    }


def build_proposed_binding(data: dict[str, Any]) -> dict[str, Any] | None:
    """Build proposed binding from confirmed leaves only, or None if not reviewable."""
    inventory = build_inventory(data)
    if not inventory["reviewable"]:
        return None
    binding: dict[str, dict[str, Any]] = {}
    for area, leaves in _REQUIRED_AREAS.items():
        confirmed_leaves: dict[str, Any] = {}
        for leaf in leaves:
            leaf_entry = inventory["areas"][area][leaf]
            if leaf_entry["status"] == "confirmed":
                confirmed_leaves[leaf] = leaf_entry["value"]
        binding[area] = confirmed_leaves
    return binding


def build_escalation_reason(data: dict[str, Any]) -> str | None:
    """Return named reason listing all dotted missing/conflicting paths, or None."""
    inventory = build_inventory(data)
    paths: list[str] = []
    for area, leaves in _REQUIRED_AREAS.items():
        for leaf in leaves:
            dotted = f"{area}.{leaf}"
            entry = inventory["areas"][area][leaf]
            if entry["status"] in ("missing", "conflicting"):
                paths.append(dotted)
    return ", ".join(paths) if paths else None


def _resolves_outside_root(fixture_path: Path) -> bool:
    resolved = fixture_path.resolve()
    root = _DISCOVERY_FIXTURE_ROOT.resolve()
    try:
        resolved.relative_to(root)
        return False
    except ValueError:
        return True


def _validate_discovery_schema(data: dict[str, Any]) -> None:
    """Strictly validate the discovery fixture JSON against the required schema."""
    if not isinstance(data, dict):
        raise ValueError("Discovery snapshot must be a JSON object")
    allowed_top = set(_REQUIRED_AREAS.keys()) | {"conflicts"}
    for key in data:
        if key not in allowed_top:
            raise ValueError(f"Unknown top-level key in discovery fixture: {key}")
    for area, leaves in _REQUIRED_AREAS.items():
        _validate_area(data.get(area), area, leaves)
    if "conflicts" in data:
        _validate_conflicts(data["conflicts"])


def _validate_area(area_data: Any, area_name: str, leaves: dict[str, str]) -> None:
    if area_data is None:
        return
    if not isinstance(area_data, dict):
        raise ValueError(f"Area '{area_name}' must be a JSON object or absent")
    if area_name == "exceptions":
        _validate_exceptions(area_data)
        return
    allowed = set(leaves.keys())
    for key in area_data:
        if key not in allowed:
            raise ValueError(f"Unknown key '{key}' in area '{area_name}'")
    for leaf, leaf_type in leaves.items():
        if leaf in area_data:
            _validate_leaf(area_data[leaf], leaf_type, area_name, leaf)


def _validate_leaf(value: Any, leaf_type: str, area: str, leaf: str) -> None:
    if leaf_type == "string":
        if not isinstance(value, str):
            raise ValueError(f"Leaf {area}.{leaf} must be a string")
        if not value.strip():
            raise ValueError(f"Leaf {area}.{leaf} must be non-empty after trimming")
    elif leaf_type == "array":
        if not isinstance(value, list):
            raise ValueError(f"Leaf {area}.{leaf} must be an array")
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"Leaf {area}.{leaf} array entries must be non-empty strings")
        trimmed = [item.strip() for item in value]
        if len(set(trimmed)) != len(value):
            raise ValueError(f"Leaf {area}.{leaf} array must not contain duplicates")


def _validate_exceptions(data: Any) -> None:
    """Validate exceptions area disposition/items contract."""
    if data is None:
        return
    if not isinstance(data, dict):
        raise ValueError("Area 'exceptions' must be a JSON object or absent")
    allowed = {"disposition", "items"}
    for key in data:
        if key not in allowed:
            raise ValueError(f"Unknown key '{key}' in area 'exceptions'")
    disposition = data.get("disposition")
    items = data.get("items")
    if disposition is None:
        pass
    elif disposition not in ("none", "declared"):
        raise ValueError(f"exceptions.disposition must be 'none' or 'declared', got '{disposition}'")
    else:
        if disposition == "none" and items is not None:
            if not isinstance(items, list) or items != []:
                raise ValueError("exceptions.items must be [] when disposition is 'none'")
        elif disposition == "declared":
            if not isinstance(items, list) or len(items) < 1:
                raise ValueError(
                    "exceptions.items must contain one or more items when disposition is 'declared'"
                )
    _validate_array_items(items)


def _validate_array_items(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        raise ValueError("'items' must be an array")
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("'items' array entries must be non-empty strings")
    if len(value):
        trimmed = [item.strip() for item in value]
        if len(set(trimmed)) != len(value):
            raise ValueError("'items' array must not contain duplicates")


def _validate_conflicts(conflicts: Any) -> None:
    if not isinstance(conflicts, dict):
        raise ValueError("'conflicts' must be a JSON object")
    required_dotted = set()
    for area, leaves in _REQUIRED_AREAS.items():
        for leaf in leaves:
            required_dotted.add(f"{area}.{leaf}")
    for path, values in conflicts.items():
        if path not in required_dotted:
            raise ValueError(f"Unknown conflict path: {path}")
        if not isinstance(values, list) or len(values) < 2:
            raise ValueError(f"Conflict for '{path}' requires at least two distinct values")
        dotted_area, dotted_leaf = path.rsplit(".", 1)
        leaf_type = _REQUIRED_AREAS[dotted_area][dotted_leaf]
        for v in values:
            if dotted_area == "exceptions" and dotted_leaf == "disposition":
                _validate_conflict_disposition_value(v)
            elif dotted_area == "exceptions" and dotted_leaf == "items":
                _validate_conflict_exception_item_value(v)
            elif leaf_type == "array":
                _validate_conflict_array_value(v, path)
            elif leaf_type == "string":
                if not isinstance(v, str):
                    raise ValueError(f"Conflict value for string leaf '{path}' must be a string")
                if not v.strip():
                    raise ValueError(f"Conflict value for string leaf '{path}' must be non-empty after trimming")
        normalized = _normalize_conflict_values(values, dotted_area, dotted_leaf)
        if len(set(normalized)) != len(values):
            raise ValueError(f"Conflict for '{path}' must have distinct values after normalization")


def _validate_conflict_disposition_value(v: Any) -> None:
    """Validate that a conflicting exceptions.disposition value is 'none' or 'declared'."""
    if not isinstance(v, str):
        raise ValueError(
            "Conflict value for exceptions.disposition must be 'none' or 'declared', "
            f"got {type(v).__name__}"
        )
    if v not in ("none", "declared"):
        raise ValueError(
            f"Conflict value for exceptions.disposition must be 'none' or 'declared', got '{v}'"
        )


def _validate_conflict_exception_item_value(v: Any) -> None:
    if not isinstance(v, list):
        raise ValueError(f"Conflict value for exceptions.items must be an array of strings")
    for item in v:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Conflict value for exceptions.items array entries must be non-empty strings")
    trimmed = [item.strip() for item in v]
    if len(set(trimmed)) != len(v):
        raise ValueError(f"Conflict value for exceptions.items must not contain duplicates")


def _validate_conflict_array_value(v: Any, path: str) -> None:
    """Validate that a conflicting array leaf value has non-empty, unique string entries."""
    if not isinstance(v, list):
        raise ValueError(f"Conflict value for array leaf '{path}' must be an array")
    for item in v:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Conflict value for array leaf '{path}' entries must be non-empty strings")
    trimmed = [item.strip() for item in v]
    if len(set(trimmed)) != len(v):
        raise ValueError(f"Conflict value for array leaf '{path}' must not contain duplicates")


def _normalize_conflict_observed(values: list, dotted_area: str, dotted_leaf: str) -> list:
    """Normalize conflict observed_values for inventory storage."""
    if dotted_area == "exceptions" and dotted_leaf == "items":
        return [
            [item.strip() for item in v] for v in values
        ]
    if leaf_type_for_leaf(dotted_area, dotted_leaf) == "string":
        return [v.strip() for v in values]
    return [
        [item.strip() for item in v] for v in values
    ]


def leaf_type_for_leaf(dotted_area: str, dotted_leaf: str) -> str:
    return _REQUIRED_AREAS[dotted_area][dotted_leaf]


def _normalize_conflict_values(values: list, dotted_area: str, dotted_leaf: str) -> tuple:
    """Normalize conflict values per their leaf type for distinctness comparison."""
    if dotted_area == "exceptions" and dotted_leaf == "items":
        return tuple(
            tuple(item.strip() for item in v) for v in values
        )
    if dotted_area == "exceptions" and dotted_leaf == "disposition":
        return tuple(v.strip() if isinstance(v, str) else v for v in values)
    leaf_type = _REQUIRED_AREAS[dotted_area][dotted_leaf]
    if leaf_type == "string":
        return tuple(v.strip() for v in values)
    return tuple(tuple(item.strip() for item in v) for v in values)


def _normalize_leaf(value: Any, leaf_type: str) -> Any:
    if leaf_type == "string":
        return value.strip()
    return [item.strip() for item in value]
