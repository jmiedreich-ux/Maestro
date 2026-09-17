"""Fixed registration boundary for service request operations."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping, Protocol

from maestro.foundation import Transaction, canonical_identifier


APPROVED_OPERATIONS = frozenset(
    {
        "registration.start",
        "question.publish",
        "question.answer",
        "registration.confirm",
        "registration.cancel",
        "registration.retry",
        "owner.decision",
        "architecture.start",
        "architecture.confirm",
        "architecture.cancel",
        "architecture.retry",
        "execution.start",
        "execution.status",
        "execution.pause",
        "execution.resume",
        "execution.stop",
        "execution.retry",
    }
)


class RegistryError(ValueError):
    """Raised when application-owned operation registration is invalid."""


class RequestLike(Protocol):
    request_id: str
    operation: str
    project_id: str | None
    activity_id: str | None
    question_id: str | None
    expected_version: int | None
    payload: Mapping[str, object]


@dataclass(frozen=True)
class OperationResult:
    """The durable public result returned by one atomic operation callback."""

    data: Mapping[str, object]
    status: str = "completed"
    project_id: str | None = None
    activity_id: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"accepted", "completed", "rejected"}:
            raise RegistryError("operation result status is invalid")
        if not isinstance(self.data, Mapping):
            raise RegistryError("operation result data must be an object")
        for name, value in (
            ("project_id", self.project_id),
            ("activity_id", self.activity_id),
        ):
            if value is not None:
                try:
                    canonical_identifier(value, name)
                except ValueError as error:
                    raise RegistryError(str(error)) from error


OperationEffect = Callable[[Transaction, int], OperationResult]


@dataclass(frozen=True)
class PreparedOperation:
    """Validated command details supplied before the shared transaction starts."""

    entity_id: str
    event_type: str
    event_data: Mapping[str, object]
    apply: OperationEffect

    def __post_init__(self) -> None:
        try:
            canonical_identifier(self.entity_id, "entity_id")
            canonical_identifier(self.event_type, "event type")
        except ValueError as error:
            raise RegistryError(str(error)) from error
        if not isinstance(self.event_data, Mapping):
            raise RegistryError("event data must be an object")
        if not callable(self.apply):
            raise RegistryError("operation callback must be callable")


OperationValidator = Callable[[RequestLike], PreparedOperation]


@dataclass(frozen=True)
class OperationHandler:
    """One application-owned operation name and its semantic validator."""

    operation: str
    validate: OperationValidator

    def __post_init__(self) -> None:
        if self.operation not in APPROVED_OPERATIONS:
            raise RegistryError(f"operation is not approved: {self.operation}")
        if not callable(self.validate):
            raise RegistryError("operation validator must be callable")


class OperationRegistry:
    """An immutable map of explicitly installed application handlers."""

    def __init__(self, handlers: tuple[OperationHandler, ...] = ()) -> None:
        installed: dict[str, OperationHandler] = {}
        for handler in handlers:
            if not isinstance(handler, OperationHandler):
                raise RegistryError("registry entries must be OperationHandler values")
            if handler.operation in installed:
                raise RegistryError(
                    f"operation is registered more than once: {handler.operation}"
                )
            installed[handler.operation] = handler
        self._handlers = MappingProxyType(installed)

    @property
    def operations(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def prepare(self, request: RequestLike) -> PreparedOperation:
        handler = self._handlers.get(request.operation)
        if handler is None:
            raise RegistryError(f"operation is unavailable: {request.operation}")
        try:
            prepared = handler.validate(request)
        except RegistryError:
            raise
        except (TypeError, ValueError) as error:
            raise RegistryError(str(error)) from error
        if not isinstance(prepared, PreparedOperation):
            raise RegistryError("operation validator returned an invalid command")
        return prepared
