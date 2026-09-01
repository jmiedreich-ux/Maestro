"""Pure discovery parser / normaliser for a single snapshot JSON object.

Phase 1 — storage-independent, stdlib-only.  No shell, network, git, or
filesystem side-effects.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class DiscoveryError(Exception):
    """Base for all synthetic-discovery errors."""


class DiscoveryValidationError(DiscoveryError):
    """Raised when the snapshot contains invalid or unsupported data."""


# ---------------------------------------------------------------------------
# Schema constants — deterministic order guaranteed by tuple ordering
# ---------------------------------------------------------------------------

# Leaf descriptions: (leaf_name, leaf_type)
#   leaf_type is "string", "array", or a special compound name.

_STRING = "string"
_ARRAY = "array"

IDENTITY_LEAVES: tuple[tuple[str, str], ...] = (
    ("project_name", _STRING),
    ("repository_identifier", _STRING),
    ("default_branch", _STRING),
    ("adapter_version", _STRING),
    ("process_version", _STRING),
)

AUTHORITY_LEAVES: tuple[tuple[str, str], ...] = (
    ("architecture_paths", _ARRAY),
    ("plan_paths", _ARRAY),
    ("handoff_path", _STRING),
    ("rules_sop_path", _STRING),
    ("task_issue_conventions", _STRING),
)

DELIVERY_LEAVES: tuple[tuple[str, str], ...] = (
    ("branch_pr_merge_policy", _STRING),
    ("owner_acceptance_policy", _STRING),
    ("deployment_rollback_policy", _STRING),
)

VERIFICATION_LEAVES: tuple[tuple[str, str], ...] = (
    ("build_commands", _ARRAY),
    ("test_commands", _ARRAY),
    ("integration_commands", _ARRAY),
    ("ui_qa_commands", _ARRAY),
    ("evidence_rules", _STRING),
    ("untested_handling", _STRING),
)

ROLES_LEAVES: tuple[tuple[str, str], ...] = (
    ("specialist_overlays", _ARRAY),
    ("reviewer_route", _STRING),
    ("qa_murphy_policy", _STRING),
    ("local_cloud_eligibility", _STRING),
)

OPERATIONS_LEAVES: tuple[tuple[str, str], ...] = (
    ("environment_reference_names", _ARRAY),
    ("secret_reference_names", _ARRAY),
    ("resource_locks", _ARRAY),
    ("notification_policy", _STRING),
)

EXCEPTIONS_LEAVES: tuple[tuple[str, str], ...] = (
    ("disposition", _STRING),
    ("items", _ARRAY),
)

# Area name → leaf tuple — deterministic iteration order
AREAS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    ("identity", IDENTITY_LEAVES),
    ("authority", AUTHORITY_LEAVES),
    ("delivery", DELIVERY_LEAVES),
    ("verification", VERIFICATION_LEAVES),
    ("roles", ROLES_LEAVES),
    ("operations", OPERATIONS_LEAVES),
    ("exceptions", EXCEPTIONS_LEAVES),
)

KNOWN_AREA_NAMES: frozenset[str] = frozenset(area for area, _ in AREAS)

# Build a flat mapping: "area.leaf" → (area, leaf_name, leaf_type)
_DOT_PATHS: dict[str, tuple[str, str, str]] = {}
for _area, _leaves in AREAS:
    for _lname, _ltype in _leaves:
        _DOT_PATHS[f"{_area}.{_lname}"] = (_area, _lname, _ltype)

# Arrays that MUST be non-empty (reject empty list)
_NON_EMPTY_ARRAYS: frozenset[str] = frozenset(("architecture_paths", "plan_paths"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trimmed(value: Any) -> str:
    """Return a trimmed string, raising on wrong type."""
    if not isinstance(value, str):
        raise DiscoveryValidationError(
            f"Expected string, got {type(value).__name__}: {value!r}"
        )
    return value.strip()


def _non_empty_string(value: Any) -> str:
    s = _trimmed(value)
    if not s:
        raise DiscoveryValidationError(f"Empty string not allowed: {value!r}")
    return s


def _string_array(values: Any, allow_empty: bool = True) -> list[str]:
    """Validate, trim, and deduplicate an array of strings.

    Rejects empty/whitespace elements after trimming and duplicates.
    Allows an empty input array when allow_empty=True.
    """
    if not isinstance(values, list):
        raise DiscoveryValidationError(
            f"Expected array, got {type(values).__name__}: {values!r}"
        )
    result: list[str] = []
    for item in values:
        if not isinstance(item, str):
            raise DiscoveryValidationError(
                f"Array element expected string, got {type(item).__name__}: {item!r}"
            )
        trimmed = item.strip()
        if not trimmed:
            raise DiscoveryValidationError(
                f"Empty string in array after trimming: {item!r}"
            )
        if trimmed in result:
            raise DiscoveryValidationError(
                f"Duplicate array element after trimming: {trimmed!r}"
            )
        result.append(trimmed)
    if not allow_empty and not result:
        raise DiscoveryValidationError(
            f"Non-empty array required, got empty: {values!r}"
        )
    return result


def _array_of_non_empty(values: Any) -> list[str]:
    """Array where each element must be a non-empty trimmed string."""
    items = _string_array(values)
    for item in items:
        if not item:
            raise DiscoveryValidationError(
                f"Empty string in array after trimming: {values!r}"
            )
    if not items:
        return []
    return items


# ---------------------------------------------------------------------------
# Per-area normalisers
# ---------------------------------------------------------------------------

def _normalize_identity(raw: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for leaf, _type in IDENTITY_LEAVES:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            val = raw[leaf]
            try:
                result[leaf] = {"status": "confirmed", "value": _non_empty_string(val)}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"identity.{leaf}: invalid value"
                )
    return result


def _normalize_authority(raw: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for leaf, leaf_type in AUTHORITY_LEAVES:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                if leaf_type == _ARRAY:
                    value = _string_array(raw[leaf], allow_empty=False)
                else:
                    value = _non_empty_string(raw[leaf])
                result[leaf] = {"status": "confirmed", "value": value}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"authority.{leaf}: invalid value"
                )
    return result


def _normalize_delivery(raw: Any) -> dict[str, Any]:
    leaves = ("branch_pr_merge_policy", "owner_acceptance_policy", "deployment_rollback_policy")
    result: dict[str, Any] = {}
    for leaf in leaves:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                result[leaf] = {"status": "confirmed", "value": _non_empty_string(raw[leaf])}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"delivery.{leaf}: invalid value"
                )
    return result


def _normalize_verification(raw: Any) -> dict[str, Any]:
    array_leaves = ("build_commands", "test_commands", "integration_commands", "ui_qa_commands")
    string_leaves = ("evidence_rules", "untested_handling")
    result: dict[str, Any] = {}
    for leaf in array_leaves:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                vals = _array_of_non_empty(raw[leaf])
                result[leaf] = {"status": "confirmed", "value": vals}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"verification.{leaf}: invalid value"
                )
    for leaf in string_leaves:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                result[leaf] = {"status": "confirmed", "value": _non_empty_string(raw[leaf])}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"verification.{leaf}: invalid value"
                )
    return result


def _normalize_roles(raw: Any) -> dict[str, Any]:
    string_leaves = ("reviewer_route", "qa_murphy_policy", "local_cloud_eligibility")
    result: dict[str, Any] = {}
    if raw is None or "specialist_overlays" not in raw:
        result["specialist_overlays"] = {"status": "missing"}
    else:
        try:
            vals = _array_of_non_empty(raw["specialist_overlays"])
            result["specialist_overlays"] = {"status": "confirmed", "value": vals}
        except DiscoveryValidationError:
            raise DiscoveryValidationError("roles.specialist_overlays: invalid value")
    for leaf in string_leaves:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                result[leaf] = {"status": "confirmed", "value": _non_empty_string(raw[leaf])}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"roles.{leaf}: invalid value"
                )
    return result


def _normalize_operations(raw: Any) -> dict[str, Any]:
    array_leaves = ("environment_reference_names", "secret_reference_names", "resource_locks")
    string_leaves = ("notification_policy",)
    result: dict[str, Any] = {}
    for leaf in array_leaves:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                vals = _array_of_non_empty(raw[leaf])
                result[leaf] = {"status": "confirmed", "value": vals}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"operations.{leaf}: invalid value"
                )
    for leaf in string_leaves:
        if raw is None or leaf not in raw:
            result[leaf] = {"status": "missing"}
        else:
            try:
                result[leaf] = {"status": "confirmed", "value": _non_empty_string(raw[leaf])}
            except DiscoveryValidationError:
                raise DiscoveryValidationError(
                    f"operations.{leaf}: invalid value"
                )
    return result


def _normalize_exceptions(raw: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if raw is None or "disposition" not in raw:
        result["disposition"] = {"status": "missing"}
    else:
        try:
            disp = _trimmed(raw["disposition"])
            if disp not in ("none", "declared"):
                raise DiscoveryValidationError(
                    f"exceptions.disposition: must be 'none' or 'declared', got {disp!r}"
                )
            result["disposition"] = {"status": "confirmed", "value": disp}
        except DiscoveryValidationError:
            raise DiscoveryValidationError(
                "exceptions.disposition: invalid value"
            )
    if raw is None or "items" not in raw:
        result["items"] = {"status": "missing"}
    else:
        try:
            vals = _array_of_non_empty(raw["items"])
            result["items"] = {"status": "confirmed", "value": vals}
        except DiscoveryValidationError:
            raise DiscoveryValidationError(
                "exceptions.items: invalid value"
            )
    # Cross-leaf validation: if both present, disposition must match items
    if (result["disposition"]["status"] == "confirmed"
            and result["items"]["status"] == "confirmed"):
        disp = result["disposition"]["value"]
        items = result["items"]["value"]
        if disp == "none" and items:
            raise DiscoveryValidationError(
                "exceptions: disposition 'none' requires empty items"
            )
        if disp == "declared" and not items:
            raise DiscoveryValidationError(
                "exceptions: disposition 'declared' requires >=1 items"
            )
    return result


# ---------------------------------------------------------------------------
# Area dispatch
# ---------------------------------------------------------------------------

_AREA_NORMALIZERS: dict[str, Any] = {
    "identity": _normalize_identity,
    "authority": _normalize_authority,
    "delivery": _normalize_delivery,
    "verification": _normalize_verification,
    "roles": _normalize_roles,
    "operations": _normalize_operations,
    "exceptions": _normalize_exceptions,
}


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------

def _parse_conflicts(raw_conflicts: Any) -> dict[str, list[Any]]:
    """Return {dotted_path: [distinct_values]} after validation."""
    if not isinstance(raw_conflicts, dict):
        raise DiscoveryValidationError(
            f"conflicts must be a dict, got {type(raw_conflicts).__name__}"
        )
    result: dict[str, list[Any]] = {}
    for path, candidates in raw_conflicts.items():
        if path not in _DOT_PATHS:
            raise DiscoveryValidationError(f"Unknown conflict path: {path!r}")
        _, _, ltype = _DOT_PATHS[path]
        if not isinstance(candidates, list) or len(candidates) < 2:
            raise DiscoveryValidationError(
                f"conflicts.{path}: requires >=2 values, got {len(candidates) if isinstance(candidates, list) else 'not a list'}"
            )
        if ltype == _ARRAY:
            normalized: list[Any] = []
            for c in candidates:
                if not isinstance(c, list):
                    raise DiscoveryValidationError(
                        f"conflicts.{path}: candidate must be array for array leaf"
                    )
                allow_empty = path not in {
                    "authority.architecture_paths",
                    "authority.plan_paths",
                }
                nv = _string_array(c, allow_empty=allow_empty)
                normalized.append(nv)
            seen: list[list[Any]] = []
            for nv in normalized:
                if nv in seen:
                    raise DiscoveryValidationError(
                        f"conflicts.{path}: duplicate candidate value"
                    )
                seen.append(nv)
            result[path] = normalized
        else:  # string leaf
            normalized: list[str] = []
            for c in candidates:
                nv = _non_empty_string(c)
                if path == "exceptions.disposition" and nv not in {
                    "none",
                    "declared",
                }:
                    raise DiscoveryValidationError(
                        f"conflicts.{path}: value must be 'none' or 'declared', got {nv!r}"
                    )
                normalized.append(nv)
            seen: list[str] = []
            for nv in normalized:
                if nv in seen:
                    raise DiscoveryValidationError(
                        f"conflicts.{path}: duplicate candidate value"
                    )
                seen.append(nv)
            result[path] = normalized
    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Parse and normalise a snapshot into the canonical areas + summary.

    Parameters
    ----------
    snapshot:
        The top-level JSON object (parsed from a JSON fixture).

    Returns
    -------
    dict
        ``{"areas": {...}, "summary": {"confirmed": int, ...}, "reviewable": bool}``

    Raises
    ------
    DiscoveryValidationError
        On unknown keys, wrong types, malformed values, or schema violations.
    """
    if not isinstance(snapshot, dict):
        raise DiscoveryValidationError(
            f"Snapshot must be a dict, got {type(snapshot).__name__}"
        )

    # --- Reject unknown top-level keys ---
    allowed_top: frozenset[str] = KNOWN_AREA_NAMES | frozenset({"conflicts"})
    for key in snapshot:
        if key not in allowed_top:
            # Allow area objects to have unknown *leaf* keys rejected later
            # but reject unknown *top-level* keys now
            if key not in KNOWN_AREA_NAMES:
                raise DiscoveryValidationError(f"Unknown top-level key: {key!r}")

    # --- Reject unknown leaf keys inside supplied area objects ---
    for area_name, leaves in AREAS:
        if area_name not in snapshot:
            continue
        raw = snapshot[area_name]
        if not isinstance(raw, dict):
            raise DiscoveryValidationError(
                f"{area_name} must be a dict when present"
            )
        allowed_leaves = frozenset(name for name, _ in leaves)
        for leaf in raw:
            if leaf not in allowed_leaves:
                raise DiscoveryValidationError(
                    f"Unknown leaf key in {area_name}: {leaf!r}"
                )

    # --- Normalize each area ---
    areas: dict[str, Any] = {}
    for area_name, _leaves in AREAS:
        if area_name not in snapshot:
            raw = None
        else:
            raw = snapshot[area_name]
            if not isinstance(raw, dict):
                raise DiscoveryValidationError(
                    f"{area_name} must be a dict or absent, got {type(raw).__name__}"
                )
        normalizer = _AREA_NORMALIZERS[area_name]
        areas[area_name] = normalizer(raw)

    # --- Parse conflicts ---
    conflicts: dict[str, list[Any]] = {}
    if "conflicts" in snapshot:
        conflicts = _parse_conflicts(snapshot["conflicts"])

    # --- Merge conflicts into area leaves ---
    conflicted_paths: set[str] = set()
    for path, cands in conflicts.items():
        area_name, leaf_name, _ = _DOT_PATHS[path]
        areas[area_name][leaf_name] = {
            "status": "conflicting",
            "observed_values": cands,
        }
        conflicted_paths.add(path)

    # --- Build summary ---
    confirmed: int = 0
    missing: int = 0
    conflicting: int = 0
    for area_name, _leaves in AREAS:
        for leaf_data in areas[area_name].values():
            st = leaf_data["status"]
            if st == "confirmed":
                confirmed += 1
            elif st == "missing":
                missing += 1
            else:
                conflicting += 1

    reviewable = missing == 0 and conflicting == 0

    return {
        "areas": areas,
        "summary": {
            "confirmed": confirmed,
            "missing": missing,
            "conflicting": conflicting,
        },
        "reviewable": reviewable,
    }


def _validate_reviewable(result: dict[str, Any]) -> None:
    """Validate that *result* is a well-formed reviewable inventory.

    Raises :class:`DiscoveryValidationError` on the first violation found.
    """
    if not isinstance(result, dict):
        raise DiscoveryValidationError(
            f"Expected dict, got {type(result).__name__}"
        )
    if set(result.keys()) != {"areas", "summary", "reviewable"}:
        raise DiscoveryValidationError(
            f"Result must have exactly keys areas, summary, reviewable; "
            f"got {sorted(result.keys())}"
        )
    if result.get("reviewable") is not True:
        raise DiscoveryValidationError(
            "Cannot propose binding: reviewable is not True"
        )
    areas = result.get("areas")
    if not isinstance(areas, dict):
        raise DiscoveryValidationError(
            f"Expected areas to be dict, got {type(areas).__name__}"
        )
    expected_area_names = {name for name, _ in AREAS}
    if set(areas.keys()) != expected_area_names:
        raise DiscoveryValidationError(
            f"areas must contain exactly {sorted(expected_area_names)}; "
            f"got {sorted(areas.keys())}"
        )
    for area_name, leaves_tuple in AREAS:
        area_data = areas.get(area_name)
        if not isinstance(area_data, dict):
            raise DiscoveryValidationError(
                f"Area {area_name!r} must be a dict, got {type(area_data).__name__}"
            )
        expected_leaves = {name for name, _ in leaves_tuple}
        if set(area_data.keys()) != expected_leaves:
            raise DiscoveryValidationError(
                f"Area {area_name!r} must have exactly {sorted(expected_leaves)}; "
                f"got {sorted(area_data.keys())}"
            )
        for leaf_name in expected_leaves:
            entry = area_data[leaf_name]
            if not isinstance(entry, dict):
                raise DiscoveryValidationError(
                    f"Leaf {area_name}.{leaf_name} must be a dict, "
                    f"got {type(entry).__name__}"
                )
            if set(entry.keys()) != {"status", "value"}:
                raise DiscoveryValidationError(
                    f"Leaf {area_name}.{leaf_name} must have exactly keys "
                    f"status, value; got {sorted(entry.keys())}"
                )
            if entry.get("status") != "confirmed":
                raise DiscoveryValidationError(
                    f"Leaf {area_name}.{leaf_name} status must be 'confirmed', "
                    f"got {entry.get('status')!r}"
                )


def propose_binding(result: dict[str, Any]) -> dict[str, Any]:
    """Return a bare 7-area tree with confirmed values only.

    Raises :class:`DiscoveryValidationError` if ``result`` is not a well-
    formed reviewable inventory.
    """
    _validate_reviewable(result)
    binding: dict[str, Any] = {}
    for area_name, leaves_tuple in AREAS:
        area_data = result["areas"][area_name]
        binding[area_name] = {}
        for leaf_name, _leaf_type in leaves_tuple:
            binding[area_name][leaf_name] = area_data[leaf_name]["value"]
    return binding


def proposed_binding_json(result: dict[str, Any]) -> str:
    """Return canonical JSON string for the binding of a reviewable result."""
    return as_json(propose_binding(result))


# ---------------------------------------------------------------------------
# Canonical JSON & digest helpers
# ---------------------------------------------------------------------------

def as_json(obj: Any) -> str:
    """Canonical compact JSON (sorted keys, no spaces, ASCII-safe)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_digest(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes.  Raises on non-bytes input."""
    if not isinstance(data, bytes):
        raise DiscoveryValidationError(
            f"sha256_digest requires bytes, got {type(data).__name__}"
        )
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Fixed-root fixture loader
# ---------------------------------------------------------------------------

_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]

DISCOVERY_FIXTURE_ROOT: pathlib.Path = (
    _PROJECT_ROOT / "fixtures" / "alpha" / "project-discovery"
)
"""Resolved absolute path to the directory that holds discovery fixtures.

Derived from this file's location; mutable only by replacing the module-
level name (for tests).  The loader itself never mutates this value.
"""


def _safe_basename(name: str) -> str:
    """Validate a fixture basename and return the cleaned name.

    Rules
    -----
    - Must be a str (non-string raises DiscoveryValidationError).
    - Non-empty after stripping.
    - Contains no path separators (``/`` or ``\\``).
    - Not absolute after stripping.
    - Does not resolve to ``.`` or ``..``.
    - Must end with ``.json``; stem must not be empty.
    - Harmless ``..`` substrings (e.g. ``v..2``) are allowed; only exact
      component ``..`` is rejected.
    - A leading dot on the stem is allowed (e.g. ``.hidden.json``).
    """
    if not isinstance(name, str):
        raise DiscoveryValidationError(
            f"Fixture name must be a string, got {type(name).__name__}"
        )
    trimmed = name.strip()
    if not trimmed:
        raise DiscoveryValidationError("Fixture name must not be empty")
    if "/" in trimmed or "\\" in trimmed:
        raise DiscoveryValidationError(
            f"Fixture name must not contain path separators: {trimmed!r}"
        )
    if pathlib.PurePath(trimmed).is_absolute():
        raise DiscoveryValidationError(
            f"Fixture name must not be absolute: {trimmed!r}"
        )
    if trimmed == "." or trimmed == "..":
        raise DiscoveryValidationError(
            f"Fixture name must not be '.' or '..': {trimmed!r}"
        )
    if not trimmed.endswith(".json"):
        raise DiscoveryValidationError(
            f"Fixture name must end with '.json': {trimmed!r}"
        )
    stem = trimmed[:-5]  # strip .json
    if not stem:
        raise DiscoveryValidationError(
            "Fixture name must contain a stem before '.json'"
        )
    return trimmed


@dataclass(frozen=True)
class LoadedDiscoveryFixture:
    """Frozen result of loading and discovering a single fixture file."""

    filename: str
    resolved_path: pathlib.Path
    raw: bytes
    inventory: dict[str, Any]
    fixture_digest: str


def load_discovery_fixture(filename: str) -> LoadedDiscoveryFixture:
    """Load, validate, parse, and discover a fixture by safe basename.

    Process
    -------
    1. Validate ``filename`` through ``_safe_basename``.
    2. Resolve ``DISCOVERY_FIXTURE_ROOT`` physically (no symlink escape).
    3. Resolve the candidate path physically; reject if it falls outside the
       resolved root (catches symlink escapes).
    4. Read raw bytes once, UTF-8 decode, ``json.loads``, then call
       ``discover`` so any schema violation surfaces as
       ``DiscoveryValidationError``.
    5. Return a frozen ``LoadedDiscoveryFixture``.

    Raises
    ------
    DiscoveryValidationError
        On any failure (unsafe name, missing file, bad encoding,
        malformed JSON, or schema violation). File paths and contents are
        NEVER leaked into the message beyond the original filename.
    """
    safe = _safe_basename(filename)

    # Resolve the physical root strictly (no symlinks).
    try:
        root_resolved = DISCOVERY_FIXTURE_ROOT.resolve(strict=True)
    except (OSError, ValueError):
        raise DiscoveryValidationError(
            "Fixture root is not accessible"
        ) from None

    # Build and resolve candidate strictly.
    candidate = root_resolved / safe
    try:
        candidate_resolved = candidate.resolve(strict=True)
    except (OSError, ValueError):
        raise DiscoveryValidationError(
            f"Fixture not found: {safe!r}"
        ) from None

    # Hard escape check: resolved candidate must stay inside resolved root.
    try:
        candidate_resolved.relative_to(root_resolved)
    except ValueError:
        raise DiscoveryValidationError(
            f"Fixture resolves outside fixture root: {safe!r}"
        ) from None

    # Read bytes once.
    try:
        raw = candidate_resolved.read_bytes()
    except (OSError, PermissionError):
        raise DiscoveryValidationError(
            f"Fixture unreadable: {safe!r}"
        ) from None

    # UTF-8 decode.
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DiscoveryValidationError(
            f"Fixture is not valid UTF-8: {safe!r}"
        ) from exc

    # Parse JSON.
    try:
        snapshot = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        raise DiscoveryValidationError(
            f"Fixture contains invalid JSON: {safe!r}"
        ) from None

    # Discover (schema validation).
    try:
        inventory = discover(snapshot)
    except DiscoveryValidationError:
        raise
    except Exception:
        raise DiscoveryValidationError(
            f"Discovery failed for {safe!r}"
        ) from None

    return LoadedDiscoveryFixture(
        filename=safe,
        resolved_path=candidate_resolved,
        raw=raw,
        inventory=inventory,
        fixture_digest=sha256_digest(raw),
    )
