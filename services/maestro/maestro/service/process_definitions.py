"""Registration and architecture-loop definitions applied through shared handlers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .processes import (
    ProcessHandlerRegistry,
    ProcessPolicyError,
    ProcessPolicyService,
    ProcessProvider,
    ProcessSnapshot,
)
from .registry import APPROVED_OPERATIONS

PROCESS_TABLES = ("registration", "architecture_loop")
_ROLE_KEYS = {"architect": "architect_role", "fidelity_reviewer": "reviewer_role"}
_BUNDLES = {"registration": "registration-process@1", "architecture_loop": "architecture-loop@1"}
_POLICIES = {
    "registration": {
        "initiation": "registration_intake_or_idle_update",
        "agent_session": "fixed_assignment_followups",
        "saved_outputs": "versioned_registration_package",
        "review": "bounded_independent_fidelity",
        "confirmation": "explicit_exact_candidate_activation",
        "recovery": "reconcile_preserved_registration",
    },
    "architecture_loop": {
        "initiation": "confirmed_registration_idle_project",
        "agent_session": "persistent_exact_session",
        "saved_outputs": "versioned_architecture_set",
        "review": "bounded_independent_fidelity",
        "confirmation": "exact_reviewed_working_version",
        "recovery": "reconcile_preserved_work",
    },
}


@dataclass(frozen=True)
class AssignmentTerms:
    """Limits a process definition gives one agent assignment."""

    process: str
    role: str
    duration_seconds: int
    automatic_limit: int
    definition_sha256: str


def _initiation(snapshot: ProcessSnapshot) -> str:
    operation = snapshot.definition["initiation"]["start_operation"]
    if operation not in APPROVED_OPERATIONS:
        raise ProcessPolicyError("unsupported_policy", f"start operation is not approved: {operation}")
    return operation


def _agent_session(snapshot: ProcessSnapshot, role: str) -> AssignmentTerms:
    definition = snapshot.definition
    if role not in _ROLE_KEYS:
        raise ProcessPolicyError("unsupported_role", f"role is not defined by the process: {role}")
    return AssignmentTerms(
        snapshot.process_name,
        definition["agent_session"][_ROLE_KEYS[role]],
        int(definition[role]["run_timeout_seconds"]),
        int(definition["recovery"]["automatic_recovery_attempts"]),
        snapshot.definition_sha256,
    )


def _review(snapshot: ProcessSnapshot) -> int:
    return int(snapshot.definition["maximum_fidelity_reviews"])


def _declared(section: str):
    def handler(snapshot: ProcessSnapshot) -> Mapping[str, Any]:
        return dict(snapshot.definition[section])
    return handler


def _provider(name: str) -> ProcessProvider:
    policies = _POLICIES[name]
    handlers = {
        "initiation": _initiation,
        "agent_session": _agent_session,
        "review": _review,
        "saved_outputs": _declared("saved_outputs"),
        "confirmation": _declared("confirmation"),
        "recovery": _declared("recovery"),
    }
    return ProcessProvider(
        name=name,
        bundle_reference=_BUNDLES[name],
        validator=lambda definition: None,
        handlers={section: {policy: handlers[section]} for section, policy in policies.items()},
        routes=("registration.start",) if name == "registration" else ("architecture.start",),
        required_outputs=("registration_package",) if name == "registration" else ("architecture_set",),
    )


def process_registry() -> ProcessHandlerRegistry:
    registry = ProcessHandlerRegistry()
    for name in PROCESS_TABLES:
        registry.register(_provider(name))
    return registry


class ProcessDefinitions:
    """Definitions read from service configuration, each valid or held with its error."""

    def __init__(self, policy: ProcessPolicyService, source: Callable[[], Mapping[str, Any]]) -> None:
        self.policy = policy
        self._source = source

    def evaluate(self, process: str, tables: Mapping[str, Any] | None = None) -> ProcessSnapshot:
        """Validate the current configuration for a new activity; raises a plain error."""
        source = self._source() if tables is None else tables
        if process not in source:
            raise ProcessPolicyError("missing_process", f"process definition is not configured: {process}")
        return self.policy.prepare(process, source[process])

    def report(self) -> list[dict[str, object]]:
        try:
            tables = self._source()
        except ValueError as error:
            return [{"process": name, "state": "invalid", "error": {"code": "configuration_unreadable", "message": str(error)}} for name in PROCESS_TABLES]
        rows: list[dict[str, object]] = []
        for process in PROCESS_TABLES:
            try:
                snapshot = self.evaluate(process, tables)
            except ProcessPolicyError as error:
                rows.append({"process": process, "state": "invalid", "error": {"code": error.code, "message": str(error), **error.fields}})
            else:
                rows.append(
                    {
                        "process": process,
                        "state": "valid",
                        "definition_sha256": snapshot.definition_sha256,
                        "bundle": snapshot.bundle.as_dict(),
                        "definition": dict(snapshot.definition),
                    }
                )
        return rows
