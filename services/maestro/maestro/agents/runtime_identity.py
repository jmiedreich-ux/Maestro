"""Protected delivery of service-confirmed agent runtime identities.

The installed supervisor and planning binding are trusted components in the
same Maestro process. Composition gives each component a separate narrow
capability: the supervisor can publish, while planning can consume. Agent
processes receive neither endpoint and cannot supply one through a service
request.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Mapping, Protocol


class RuntimeIdentityProtocolError(RuntimeError):
    """A protected runtime-identity operation was rejected."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class ConfirmedRuntimeIdentity:
    """The record produced only after supervisor verification."""

    operation_key: str
    provider: str
    model_id: str
    tool_version: str
    configuration_hash: str
    pid: int
    boot_id: str
    start_identity: str
    invocation_id: str

    def __post_init__(self) -> None:
        for name in (
            "operation_key", "provider", "model_id", "tool_version",
            "configuration_hash", "boot_id", "start_identity", "invocation_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise RuntimeIdentityProtocolError("invalid_identity", f"{name} must be nonempty")
        if not isinstance(self.pid, int) or isinstance(self.pid, bool) or self.pid <= 0:
            raise RuntimeIdentityProtocolError("invalid_identity", "pid must be positive")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "ConfirmedRuntimeIdentity":
        if not isinstance(value, Mapping):
            raise RuntimeIdentityProtocolError("invalid_identity", "identity must be an object")
        fields = {
            "operation_key", "provider", "model_id", "tool_version", "configuration_hash",
            "pid", "boot_id", "start_identity", "invocation_id",
        }
        if set(value) != fields:
            raise RuntimeIdentityProtocolError("invalid_identity", "identity fields are invalid")
        return cls(**{field: value[field] for field in fields})  # type: ignore[arg-type]


class SupervisorIdentityReporter(Protocol):
    """Write-only capability held by the installed supervisor."""

    def publish(self, identity: ConfirmedRuntimeIdentity) -> None: ...


class PlanningIdentityConsumer(Protocol):
    """Read-once capability held by the installed planning binding."""

    def consume(self, operation_key: str) -> ConfirmedRuntimeIdentity: ...


def compose_runtime_identity_endpoints() -> tuple[SupervisorIdentityReporter, PlanningIdentityConsumer]:
    """Create one isolated authority and return its non-interchangeable ends."""
    identities: dict[str, ConfirmedRuntimeIdentity] = {}
    published_operations: set[str] = set()
    lock = threading.Lock()

    def publish(identity: ConfirmedRuntimeIdentity) -> None:
        if not isinstance(identity, ConfirmedRuntimeIdentity):
            raise RuntimeIdentityProtocolError("invalid_identity", "identity is invalid")
        with lock:
            if identity.operation_key in published_operations:
                raise RuntimeIdentityProtocolError(
                    "identity_already_published", "runtime identity already exists",
                )
            identities[identity.operation_key] = identity
            published_operations.add(identity.operation_key)

    def consume(operation_key: str) -> ConfirmedRuntimeIdentity:
        if not isinstance(operation_key, str) or not operation_key:
            raise RuntimeIdentityProtocolError("invalid_operation", "operation key is invalid")
        with lock:
            try:
                return identities.pop(operation_key)
            except KeyError as error:
                raise RuntimeIdentityProtocolError(
                    "identity_unavailable", "confirmed runtime identity is unavailable",
                ) from error

    class SupervisorEndpoint:
        __slots__ = ()

        def publish(self, identity: ConfirmedRuntimeIdentity) -> None:
            publish(identity)

    class PlanningEndpoint:
        __slots__ = ()

        def consume(self, operation_key: str) -> ConfirmedRuntimeIdentity:
            return consume(operation_key)

    return SupervisorEndpoint(), PlanningEndpoint()
