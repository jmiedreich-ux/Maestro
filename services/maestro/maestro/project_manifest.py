"""Strict parsing and validation for ``maestro.project.yaml`` version 1."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

import yaml


class ProjectManifestError(ValueError):
    """The project manifest is malformed and must not be persisted."""


_PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{2,63}\Z")
_REPOSITORY = re.compile(r"[^/\s]+/[^/\s]+\Z")
_SECRET_REFERENCE = re.compile(r"[A-Z][A-Z0-9_]{2,127}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_ACCEPTANCE_AUTHORITIES = frozenset({"project-architect", "owner"})

_SHAPE: dict[str, tuple[str, ...]] = {
    "identity": (
        "project_id", "name", "repository", "default_branch", "adapter_version", "process_version"
    ),
    "authority": (
        "architecture_paths", "plan_paths", "work_graph_path", "handoff_path",
        "rules_sop_path", "task_issue_convention",
    ),
    "delivery": (
        "branch_policy", "pull_request_policy", "merge_policy", "acceptance_authority",
        "deployment_policy", "rollback_policy",
    ),
    "verification": (
        "build_commands", "test_commands", "integration_commands", "ui_qa_commands",
        "evidence_rules", "untested_handling",
    ),
    "routing": (
        "specialist_overlays", "worker_routes", "integration_route",
        "independent_reviewer_route", "qa_murphy_policy",
    ),
    "operations": (
        "environment_references", "secret_references", "resource_locks", "notification_policy",
    ),
    "exceptions": ("disposition", "items"),
}

_LIST_FIELDS = {
    "authority.architecture_paths", "authority.plan_paths",
    "verification.build_commands", "verification.test_commands",
    "verification.integration_commands", "verification.ui_qa_commands",
    "routing.specialist_overlays", "routing.worker_routes",
    "operations.environment_references", "operations.secret_references",
    "operations.resource_locks", "exceptions.items",
}
_REQUIRED_NONEMPTY_LISTS = {"authority.architecture_paths", "authority.plan_paths"}
_PATH_FIELDS = {
    "authority.work_graph_path", "authority.handoff_path", "authority.rules_sop_path"
}
_PATH_LIST_FIELDS = {"authority.architecture_paths", "authority.plan_paths"}


class _StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _StrictSafeLoader, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ProjectManifestError("manifest mapping keys must be strings")
        if key == "<<":
            raise ProjectManifestError("YAML merge keys are prohibited")
        if key in result:
            raise ProjectManifestError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def parse_project_manifest(raw: bytes) -> dict[str, Any]:
    """Parse the closed YAML subset and validate every present value.

    Missing required leaves remain absent so the authority inventory can report
    each one honestly. Structural/type violations raise before persistence.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProjectManifestError("manifest must be UTF-8") from exc
    try:
        for token in yaml.scan(text, Loader=_StrictSafeLoader):
            if isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken, yaml.tokens.TagToken)):
                raise ProjectManifestError("YAML anchors, aliases, and custom tags are prohibited")
        value = yaml.load(text, Loader=_StrictSafeLoader)
    except ProjectManifestError:
        raise
    except yaml.YAMLError as exc:
        raise ProjectManifestError(f"invalid YAML: {exc}") from exc
    if not isinstance(value, dict):
        raise ProjectManifestError("manifest must contain exactly one mapping document")
    _validate_closed_shape(value)
    return value


def manifest_leaf_paths() -> tuple[str, ...]:
    return ("schema_version",) + tuple(f"{area}.{leaf}" for area, leaves in _SHAPE.items() for leaf in leaves)


def authority_paths(manifest: dict[str, Any]) -> tuple[str, ...]:
    authority = manifest.get("authority")
    if not isinstance(authority, dict):
        return ()
    paths: list[str] = []
    for field in ("architecture_paths", "plan_paths"):
        values = authority.get(field)
        if isinstance(values, list):
            paths.extend(values)
    for field in ("work_graph_path", "handoff_path", "rules_sop_path"):
        value = authority.get(field)
        if isinstance(value, str):
            paths.append(value)
    return tuple(dict.fromkeys(paths))


def _validate_closed_shape(manifest: dict[str, Any]) -> None:
    allowed_top = {"schema_version", *_SHAPE}
    _reject_unknown(manifest, allowed_top, "manifest")
    if "schema_version" in manifest:
        version = manifest["schema_version"]
        if isinstance(version, bool) or not isinstance(version, int) or version != 1:
            raise ProjectManifestError("schema_version must be integer 1")

    for area, fields in _SHAPE.items():
        if area not in manifest:
            continue
        area_value = manifest[area]
        if not isinstance(area_value, dict):
            raise ProjectManifestError(f"{area} must be a mapping")
        _reject_unknown(area_value, set(fields), area)
        for field, value in area_value.items():
            dotted = f"{area}.{field}"
            if dotted in _LIST_FIELDS:
                _validate_list(dotted, value)
            else:
                _validate_scalar(dotted, value)

    identity = manifest.get("identity", {})
    if isinstance(identity, dict):
        project_id = identity.get("project_id")
        if project_id is not None and not _PROJECT_ID.fullmatch(project_id):
            raise ProjectManifestError("identity.project_id has invalid format")
        repository = identity.get("repository")
        if repository is not None and not _REPOSITORY.fullmatch(repository):
            raise ProjectManifestError("identity.repository must have owner/name form")

    delivery = manifest.get("delivery", {})
    if isinstance(delivery, dict) and "acceptance_authority" in delivery:
        acceptance_authority = delivery["acceptance_authority"]
        if acceptance_authority not in _ACCEPTANCE_AUTHORITIES:
            raise ProjectManifestError(
                "delivery.acceptance_authority must be project-architect or owner"
            )

    authority = manifest.get("authority", {})
    if isinstance(authority, dict):
        for dotted in _PATH_FIELDS:
            field = dotted.split(".", 1)[1]
            if field in authority:
                _validate_repository_path(authority[field], dotted)
        for dotted in _PATH_LIST_FIELDS:
            field = dotted.split(".", 1)[1]
            for path in authority.get(field, []):
                _validate_repository_path(path, dotted)
        graph = authority.get("work_graph_path")
        plans = authority.get("plan_paths")
        if graph is not None and plans is not None and graph not in plans:
            raise ProjectManifestError("authority.work_graph_path must occur in authority.plan_paths")

    operations = manifest.get("operations", {})
    if isinstance(operations, dict) and "secret_references" in operations:
        for value in operations["secret_references"]:
            if not _SECRET_REFERENCE.fullmatch(value):
                raise ProjectManifestError("operations.secret_references contains an invalid identifier")

    exceptions = manifest.get("exceptions", {})
    if isinstance(exceptions, dict):
        disposition = exceptions.get("disposition")
        items = exceptions.get("items")
        if disposition is not None and disposition not in {"none", "declared"}:
            raise ProjectManifestError("exceptions.disposition must be none or declared")
        if disposition == "none" and items is not None and items != []:
            raise ProjectManifestError("exceptions.items must be empty when disposition is none")
        if disposition == "declared" and (not isinstance(items, list) or not items):
            raise ProjectManifestError("exceptions.items must be non-empty when disposition is declared")


def _reject_unknown(value: dict[str, Any], allowed: set[str], location: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise ProjectManifestError(f"unknown field at {location}: {unknown[0]}")


def _validate_scalar(dotted: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ProjectManifestError(f"{dotted} must be a string")
    if not value or value != value.strip():
        raise ProjectManifestError(f"{dotted} must be non-empty without surrounding whitespace")
    if len(value.encode("utf-8")) > 512:
        raise ProjectManifestError(f"{dotted} exceeds 512 UTF-8 bytes")
    if _CONTROL.search(value):
        raise ProjectManifestError(f"{dotted} contains a control character")


def _validate_list(dotted: str, value: Any) -> None:
    if not isinstance(value, list):
        raise ProjectManifestError(f"{dotted} must be a list")
    if dotted in _REQUIRED_NONEMPTY_LISTS and not value:
        raise ProjectManifestError(f"{dotted} must contain at least one path")
    seen: set[str] = set()
    for item in value:
        _validate_scalar(dotted, item)
        if item in seen:
            raise ProjectManifestError(f"{dotted} must not contain duplicates")
        seen.add(item)


def _validate_repository_path(value: str, dotted: str) -> None:
    if _CONTROL.search(value) or "\\" in value:
        raise ProjectManifestError(f"{dotted} contains a prohibited path character")
    path = PurePosixPath(value)
    if path.is_absolute() or value in {"", "."}:
        raise ProjectManifestError(f"{dotted} must be a repository-relative POSIX path")
    components = value.split("/")
    if any(component in {"", ".", "..", ".git"} for component in components):
        raise ProjectManifestError(f"{dotted} contains a prohibited path component")
