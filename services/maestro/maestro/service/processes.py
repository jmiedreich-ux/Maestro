"""Validated process policy, immutable activity snapshots, and bookkeeping."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from maestro.foundation import (
    Database,
    DomainMigration,
    Transaction,
    canonical_identifier,
    canonical_json,
)

from .resources import BundleSnapshot, InstalledSchemaResources, ProcessResourceError


PROCESS_POLICY_MIGRATION = DomainMigration(
    domain="service_process_policy",
    version=1,
    identity="service-process-policy-v1",
    statements=(
        """
        CREATE TABLE service_process_snapshots(
            activity_id TEXT PRIMARY KEY,
            process_name TEXT NOT NULL,
            definition_json TEXT NOT NULL,
            definition_sha256 TEXT NOT NULL,
            bundle_snapshot_json TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE service_process_counters(
            activity_id TEXT NOT NULL
                REFERENCES service_process_snapshots(activity_id) ON DELETE CASCADE,
            counter_name TEXT NOT NULL,
            scope_id TEXT NOT NULL,
            consumed INTEGER NOT NULL CHECK(consumed >= 0),
            PRIMARY KEY(activity_id, counter_name, scope_id)
        )
        """,
    ),
)


class ProcessPolicyError(ValueError):
    """A typed configuration or process-policy rejection."""

    def __init__(self, code: str, message: str, **fields: object) -> None:
        super().__init__(message)
        self.code = code
        self.fields = dict(fields)


PolicyHandler = Callable[..., object]
DefinitionValidator = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class ProcessProvider:
    """Process-owned behavior supplied to the shared registry."""

    name: str
    bundle_reference: str
    validator: DefinitionValidator
    handlers: Mapping[str, Mapping[str, PolicyHandler]]
    migrations: tuple[DomainMigration, ...] = ()
    routes: tuple[str, ...] = ()
    required_outputs: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProcessSnapshot:
    process_name: str
    definition_json: str
    definition_sha256: str
    bundle: BundleSnapshot

    @property
    def definition(self) -> Mapping[str, Any]:
        value = json.loads(self.definition_json)
        if not isinstance(value, Mapping):  # pragma: no cover - guarded on creation/load
            raise ProcessPolicyError("invalid_snapshot", "saved process definition is invalid")
        return value


@dataclass(frozen=True)
class ProcessStatus:
    snapshot: ProcessSnapshot
    counters: Mapping[tuple[str, str], int]


_DECLARED: Mapping[str, tuple[str, Mapping[str, str]]] = {
    "registration": (
        "registration-process@1",
        {
            "initiation": "registration_intake_or_idle_update",
            "agent_session": "fixed_assignment_followups",
            "saved_outputs": "versioned_registration_package",
            "review": "bounded_independent_fidelity",
            "confirmation": "explicit_exact_candidate_activation",
            "recovery": "reconcile_preserved_registration",
        },
    ),
    "architecture_loop": (
        "architecture-loop@1",
        {
            "initiation": "confirmed_registration_idle_project",
            "agent_session": "persistent_exact_session",
            "saved_outputs": "versioned_architecture_set",
            "review": "bounded_independent_fidelity",
            "confirmation": "exact_reviewed_working_version",
            "recovery": "reconcile_preserved_work",
        },
    ),
}

_DEFAULTS: Mapping[str, Mapping[str, int]] = {
    "registration": {
        "maximum_fidelity_reviews": 2,
        "architect.run_timeout_seconds": 1800,
        "fidelity_reviewer.run_timeout_seconds": 1800,
        "recovery.automatic_recovery_attempts": 2,
    },
    "architecture_loop": {
        "maximum_fidelity_reviews": 2,
        "architect.run_timeout_seconds": 1800,
        "fidelity_reviewer.run_timeout_seconds": 1800,
        "recovery.automatic_recovery_attempts": 2,
        "recovery.maximum_output_corrections": 2,
    },
}


class ProcessHandlerRegistry:
    """Register process-owned semantics without inferring them."""

    def __init__(self) -> None:
        self._providers: dict[str, ProcessProvider] = {}

    def register(self, provider: ProcessProvider) -> None:
        if not isinstance(provider, ProcessProvider):
            raise TypeError("process registry requires a ProcessProvider")
        declared = _DECLARED.get(provider.name)
        if declared is None:
            raise ProcessPolicyError("unsupported_process", f"process is not supported: {provider.name}")
        expected_bundle, expected_policies = declared
        if provider.bundle_reference != expected_bundle:
            raise ProcessPolicyError("unsupported_bundle", "process uses an unsupported schema bundle")
        if not callable(provider.validator):
            raise ProcessPolicyError("invalid_provider", "process definition validator is not callable")
        if set(provider.handlers) != set(expected_policies):
            raise ProcessPolicyError("unsupported_policy", "process handler sections are incomplete")
        for section, policy in expected_policies.items():
            handlers = provider.handlers[section]
            if not isinstance(handlers, Mapping) or set(handlers) != {policy}:
                raise ProcessPolicyError(
                    "unsupported_policy", f"unsupported {provider.name}.{section} policy handlers"
                )
            if not callable(handlers[policy]):
                raise ProcessPolicyError("unsupported_policy", "process policy handler is not callable")
        if provider.name in self._providers and self._providers[provider.name] != provider:
            raise ProcessPolicyError("duplicate_process", f"process is already registered: {provider.name}")
        self._providers[provider.name] = provider

    def provider(self, process_name: str) -> ProcessProvider:
        try:
            return self._providers[process_name]
        except KeyError as error:
            raise ProcessPolicyError(
                "unsupported_process", f"process is not registered: {process_name}"
            ) from error

    def dispatch(self, snapshot: ProcessSnapshot, section: str, *args: object, **kwargs: object) -> object:
        provider = self.provider(snapshot.process_name)
        definition = snapshot.definition
        selected = definition.get(section)
        if not isinstance(selected, Mapping) or not isinstance(selected.get("policy"), str):
            raise ProcessPolicyError("invalid_definition", f"missing policy for {section}")
        policy = selected["policy"]
        try:
            handler = provider.handlers[section][policy]
        except KeyError as error:
            raise ProcessPolicyError("unsupported_policy", f"unsupported policy: {policy}") from error
        return handler(snapshot, *args, **kwargs)

    @property
    def migrations(self) -> tuple[DomainMigration, ...]:
        return tuple(migration for provider in self._providers.values() for migration in provider.migrations)


class ProcessPolicyService:
    """Validate definitions and persist the exact authority used by an activity."""

    def __init__(
        self,
        database: Database,
        resources: InstalledSchemaResources,
        registry: ProcessHandlerRegistry,
    ) -> None:
        if not isinstance(database, Database):
            raise TypeError("process policy requires the service Database")
        self.database = database
        self.resources = resources
        self.registry = registry
        database.registry.register(PROCESS_POLICY_MIGRATION)
        for migration in registry.migrations:
            database.registry.register(migration)
        database.initialize()

    def prepare(self, process_name: str, definition: Mapping[str, Any]) -> ProcessSnapshot:
        provider = self.registry.provider(process_name)
        return prepare_process_snapshot(self.resources, provider, process_name, definition)

    def create_activity(
        self,
        transaction: Transaction,
        activity_id: str,
        snapshot: ProcessSnapshot,
        creator: Callable[[Transaction, ProcessSnapshot], object],
    ) -> object:
        """Save policy first, then invoke the process-owned creator atomically."""
        canonical_identifier(activity_id, "activity_id")
        provider = self.registry.provider(snapshot.process_name)
        try:
            current_bundle = self.resources.verify(snapshot.bundle)
        except ProcessResourceError as error:
            raise ProcessPolicyError(error.code, str(error), **error.fields) from error
        definition = snapshot.definition
        if (
            provider.bundle_reference != snapshot.bundle.reference
            or canonical_json(definition) != snapshot.definition_json
            or hashlib.sha256(snapshot.definition_json.encode("utf-8")).hexdigest()
            != snapshot.definition_sha256
        ):
            raise ProcessPolicyError("invalid_snapshot", "process snapshot integrity check failed")
        schema = current_bundle.schema["$defs"][current_bundle.snapshot.definition]
        _validate_schema(definition, schema, snapshot.process_name)
        try:
            provider.validator(definition)
        except ProcessPolicyError:
            raise
        except (TypeError, ValueError) as error:
            raise ProcessPolicyError("invalid_definition", str(error)) from error
        transaction.execute(
            """
            INSERT INTO service_process_snapshots(
                activity_id, process_name, definition_json, definition_sha256,
                bundle_snapshot_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                activity_id,
                snapshot.process_name,
                snapshot.definition_json,
                snapshot.definition_sha256,
                canonical_json(snapshot.bundle.as_dict()),
            ),
        )
        return creator(transaction, snapshot)

    def status(self, activity_id: str) -> ProcessStatus:
        canonical_identifier(activity_id, "activity_id")
        with self.database.read_connection() as connection:
            row = connection.execute(
                """SELECT process_name, definition_json, definition_sha256,
                          bundle_snapshot_json
                   FROM service_process_snapshots WHERE activity_id = ?""",
                (activity_id,),
            ).fetchone()
            if row is None:
                raise ProcessPolicyError("activity_not_found", "process activity was not found")
            counter_rows = connection.execute(
                """SELECT counter_name, scope_id, consumed FROM service_process_counters
                   WHERE activity_id = ?""",
                (activity_id,),
            ).fetchall()
        snapshot = _snapshot_from_row(row)
        return ProcessStatus(snapshot, {(str(a), str(b)): int(c) for a, b, c in counter_rows})

    def resume(self, activity_id: str) -> ProcessStatus:
        status = self.status(activity_id)
        try:
            self.resources.verify(status.snapshot.bundle)
        except ProcessResourceError as error:
            raise ProcessPolicyError(error.code, str(error), **error.fields) from error
        self.registry.provider(status.snapshot.process_name)
        return status

    def consume(self, activity_id: str, counter_name: str, scope_id: str = "activity") -> int:
        canonical_identifier(activity_id, "activity_id")
        canonical_identifier(scope_id, "scope_id")
        status = self.resume(activity_id)
        limit = _counter_limit(status.snapshot.definition, counter_name)
        with self.database.transaction() as transaction:
            row = transaction.execute(
                """SELECT consumed FROM service_process_counters
                   WHERE activity_id = ? AND counter_name = ? AND scope_id = ?""",
                (activity_id, counter_name, scope_id),
            ).fetchone()
            consumed = 0 if row is None else int(row[0])
            if consumed >= limit:
                raise ProcessPolicyError(
                    "allowance_exhausted", f"{counter_name} allowance is exhausted", limit=limit
                )
            consumed += 1
            transaction.execute(
                """INSERT INTO service_process_counters(activity_id, counter_name, scope_id, consumed)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(activity_id, counter_name, scope_id)
                   DO UPDATE SET consumed = excluded.consumed""",
                (activity_id, counter_name, scope_id, consumed),
            )
        return consumed


def _snapshot_from_row(row: Sequence[object]) -> ProcessSnapshot:
    process_name, definition_json, definition_sha256, bundle_json = map(str, row)
    try:
        definition = json.loads(definition_json)
        bundle_value = json.loads(bundle_json)
    except json.JSONDecodeError as error:
        raise ProcessPolicyError("invalid_snapshot", "saved process snapshot is invalid") from error
    if not isinstance(definition, Mapping) or canonical_json(definition) != definition_json:
        raise ProcessPolicyError("invalid_snapshot", "saved process definition is invalid")
    digest = hashlib.sha256(definition_json.encode("utf-8")).hexdigest()
    if digest != definition_sha256:
        raise ProcessPolicyError("invalid_snapshot", "saved process definition hash differs")
    try:
        bundle = BundleSnapshot.from_dict(bundle_value)
    except ProcessResourceError as error:
        raise ProcessPolicyError(error.code, str(error)) from error
    return ProcessSnapshot(process_name, definition_json, definition_sha256, bundle)


def prepare_process_snapshot(
    resources: InstalledSchemaResources,
    provider: ProcessProvider,
    process_name: str,
    definition: Mapping[str, Any],
) -> ProcessSnapshot:
    """Validate one installed process definition without touching service state."""
    if not isinstance(resources, InstalledSchemaResources):
        raise TypeError("process snapshot preparation requires installed resources")
    if not isinstance(provider, ProcessProvider) or provider.name != process_name:
        raise ProcessPolicyError(
            "unsupported_process", "process provider does not match the definition"
        )
    if process_name not in _DEFAULTS:
        raise ProcessPolicyError(
            "unsupported_process", f"process is not supported: {process_name}"
        )
    if not isinstance(definition, Mapping):
        raise ProcessPolicyError("invalid_definition", "process definition must be a table")
    effective = _copy_json_object(definition)
    for dotted, value in _DEFAULTS[process_name].items():
        _apply_default(effective, dotted.split("."), value)
    try:
        bundle = resources.resolve(provider.bundle_reference)
    except ProcessResourceError as error:
        raise ProcessPolicyError(error.code, str(error), **error.fields) from error
    schema = bundle.schema["$defs"][bundle.snapshot.definition]
    try:
        _validate_schema(effective, schema, process_name)
        provider.validator(effective)
    except ProcessPolicyError:
        raise
    except (TypeError, ValueError) as error:
        raise ProcessPolicyError("invalid_definition", str(error)) from error
    definition_json = canonical_json(effective)
    return ProcessSnapshot(
        process_name,
        definition_json,
        hashlib.sha256(definition_json.encode("utf-8")).hexdigest(),
        bundle.snapshot,
    )


def _copy_json_object(value: Mapping[str, Any]) -> dict[str, Any]:
    try:
        encoded = json.dumps(value, allow_nan=False)
        copied = json.loads(encoded)
    except (TypeError, ValueError, UnicodeError) as error:
        raise ProcessPolicyError("invalid_definition", "process definition is not plain data") from error
    if not isinstance(copied, dict):
        raise ProcessPolicyError("invalid_definition", "process definition must be a table")
    return copied


def _apply_default(target: dict[str, Any], path: list[str], value: int) -> None:
    current = target
    for part in path[:-1]:
        child = current.get(part)
        if child is None:
            return  # Defaults never create an omitted required section.
        if not isinstance(child, dict):
            return  # Schema validation will report the bad type.
        current = child
    current.setdefault(path[-1], value)


def _validate_schema(value: Any, schema: Mapping[str, Any], path: str) -> None:
    expected_type = schema.get("type")
    if expected_type == "object":
        if not isinstance(value, Mapping):
            raise ProcessPolicyError("invalid_definition", f"{path} must be a table", field=path)
        properties = schema.get("properties", {})
        if not isinstance(properties, Mapping):
            raise ProcessPolicyError("invalid_bundle", "process schema properties are invalid")
        unknown = set(value) - set(properties)
        if schema.get("additionalProperties") is False and unknown:
            field = f"{path}.{sorted(unknown)[0]}"
            raise ProcessPolicyError("unknown_field", f"unknown process setting: {field}", field=field)
        required = schema.get("required", [])
        missing = [name for name in required if name not in value]
        if missing:
            field = f"{path}.{missing[0]}"
            raise ProcessPolicyError("missing_field", f"required process setting is missing: {field}", field=field)
        for name, child in value.items():
            child_schema = properties.get(name)
            if isinstance(child_schema, Mapping):
                _validate_schema(child, child_schema, f"{path}.{name}")
    elif expected_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ProcessPolicyError("invalid_type", f"{path} must be an integer", field=path)
        minimum = schema.get("minimum")
        if isinstance(minimum, int) and value < minimum:
            code = "invalid_duration" if path.endswith("run_timeout_seconds") else "invalid_value"
            raise ProcessPolicyError(code, f"{path} must be at least {minimum}", field=path)
    elif expected_type == "string" and not isinstance(value, str):
        raise ProcessPolicyError("invalid_type", f"{path} must be text", field=path)
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        code = "unsupported_policy" if path.endswith(".policy") else "invalid_value"
        raise ProcessPolicyError(code, f"unsupported process setting: {path}", field=path)


def _counter_limit(definition: Mapping[str, Any], counter_name: str) -> int:
    if counter_name == "fidelity_reviews":
        value = definition.get("maximum_fidelity_reviews")
    elif counter_name in {"automatic_recovery_attempts", "maximum_output_corrections"}:
        recovery = definition.get("recovery")
        value = recovery.get(counter_name) if isinstance(recovery, Mapping) else None
    else:
        raise ProcessPolicyError("unsupported_counter", f"unsupported process counter: {counter_name}")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ProcessPolicyError("unsupported_counter", f"counter is not available: {counter_name}")
    return value
