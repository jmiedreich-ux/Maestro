"""Authenticated, idempotent durable request submission and reconciliation."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from maestro.foundation import (
    Command,
    ContractError,
    Database,
    DatabaseError,
    Event,
    StorageConfigurationError,
    VersionConflictError,
    canonical_identifier,
    canonical_json,
)

from .authentication import HTTPRejection, OwnerAuthenticator
from .receipts import (
    REQUEST_MIGRATION,
    ReceiptDataError,
    ReceiptRepository,
    RequestReceipt,
)
from .registry import OperationRegistry, OperationResult, RegistryError


_ENVELOPE_FIELDS = frozenset(
    {
        "request_id",
        "operation",
        "project_id",
        "activity_id",
        "question_id",
        "expected_version",
        "payload",
    }
)


class RequestRejection(HTTPRejection):
    """A typed request error with architecture-required affected fields."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        fields: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(status_code, code, message)
        self.fields = {} if fields is None else dict(fields)

    def as_body(self) -> dict[str, object]:
        error: dict[str, object] = {"code": self.code, "message": self.message}
        if self.fields:
            error["fields"] = dict(self.fields)
        return {"error": error}


@dataclass(frozen=True)
class RequestEnvelope:
    request_id: str
    operation: str
    project_id: str | None
    activity_id: str | None
    question_id: str | None
    expected_version: int | None
    payload: Mapping[str, object]

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "RequestEnvelope":
        if not isinstance(value, Mapping):
            raise _invalid("request body must be a JSON object", "body")
        missing = _ENVELOPE_FIELDS - set(value)
        unknown = set(value) - _ENVELOPE_FIELDS
        if missing or unknown:
            affected = sorted(missing | unknown)
            raise _invalid("request envelope fields do not match the contract", *affected)
        try:
            request_id = canonical_identifier(
                value["request_id"], "request_id"  # type: ignore[arg-type]
            )
            operation = canonical_identifier(
                value["operation"], "operation"  # type: ignore[arg-type]
            )
            project_id = _optional_identifier(value["project_id"], "project_id")
            activity_id = _optional_identifier(value["activity_id"], "activity_id")
            question_id = _optional_identifier(value["question_id"], "question_id")
        except (ContractError, TypeError) as error:
            raise _invalid(str(error)) from error
        expected = value["expected_version"]
        if expected is not None and (
            isinstance(expected, bool) or not isinstance(expected, int) or expected < 0
        ):
            raise _invalid(
                "expected_version must be a nonnegative integer or null",
                "expected_version",
            )
        payload = value["payload"]
        if not isinstance(payload, Mapping):
            raise _invalid("payload must be a JSON object", "payload")
        try:
            canonical_json(payload)
        except ContractError as error:
            raise _invalid(str(error), "payload") from error
        return cls(
            request_id=request_id,
            operation=operation,
            project_id=project_id,
            activity_id=activity_id,
            question_id=question_id,
            expected_version=expected,
            payload=dict(payload),
        )

    @property
    def content_digest(self) -> str:
        content = canonical_json(
            {
                "activity_id": self.activity_id,
                "expected_version": self.expected_version,
                "operation": self.operation,
                "payload": dict(self.payload),
                "project_id": self.project_id,
                "question_id": self.question_id,
            }
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


class _DeferredEvent:
    """Bind callback-created context before the foundation saves the event."""

    def __init__(
        self,
        *,
        event_id: str,
        occurred_at: str,
        project_id: str | None,
        activity_id: str | None,
        event_type: str,
        data: Mapping[str, object],
    ) -> None:
        self._submitted_project_id = project_id
        self._submitted_activity_id = activity_id
        self._event_values = {
            "schema_version": 1,
            "event_id": event_id,
            "occurred_at": occurred_at,
            "type": event_type,
            "data": data,
        }
        self._event = Event(
            project_id=project_id,
            activity_id=activity_id,
            **self._event_values,
        )

    def bind(self, result: OperationResult) -> None:
        project_id = _resolved_context(
            "project_id", self._submitted_project_id, result.project_id
        )
        activity_id = _resolved_context(
            "activity_id", self._submitted_activity_id, result.activity_id
        )
        self._event = Event(
            project_id=project_id,
            activity_id=activity_id,
            **self._event_values,
        )

    @property
    def schema_version(self) -> int:
        return self._event.schema_version

    @property
    def event_id(self) -> str:
        return self._event.event_id

    @property
    def occurred_at(self) -> str:
        return self._event.occurred_at

    @property
    def project_id(self) -> str | None:
        return self._event.project_id

    @property
    def activity_id(self) -> str | None:
        return self._event.activity_id

    @property
    def type(self) -> str:
        return self._event.type

    @property
    def data(self) -> Mapping[str, object]:
        return self._event.data


class RequestService:
    """The authenticated application boundary for POST and GET request routes."""

    def __init__(
        self,
        database: Database,
        authenticator: OwnerAuthenticator,
        registry: OperationRegistry,
    ) -> None:
        self._database = database
        self._authenticator = authenticator
        self._registry = registry
        self._database.registry.register(REQUEST_MIGRATION)
        self._database.initialize()
        self._receipts = ReceiptRepository(database)

    def submit(
        self,
        authorization: str | None,
        body: Mapping[str, object],
    ) -> RequestReceipt:
        actor = self._authenticator.authenticate_write(authorization)
        request = RequestEnvelope.from_mapping(body)
        digest = request.content_digest
        existing = self._find_receipt(request.request_id)
        if existing is not None:
            return self._reconcile(existing, digest)
        self._reject_stale_external_operation(request)
        try:
            prepared = self._registry.prepare(request)
        except RegistryError as error:
            raise _invalid(str(error), "operation") from error

        effective_expected_version = (
            0 if request.expected_version is None else request.expected_version
        )
        event_key = hashlib.sha256(
            f"{request.request_id}\0{digest}".encode("utf-8")
        ).hexdigest()
        event_id = f"request-{event_key}"
        command = Command(
            request_id=request.request_id,
            operation=request.operation,
            actor_id=actor.actor_id,
            entity_id=prepared.entity_id,
            expected_version=effective_expected_version,
            content_digest=digest,
        )
        event = _DeferredEvent(
            event_id=event_id,
            occurred_at=_utc_now(),
            project_id=request.project_id,
            activity_id=request.activity_id,
            event_type=prepared.event_type,
            data=prepared.event_data,
        )

        def apply(transaction, next_version: int):
            result = prepared.apply(transaction, next_version)
            if not isinstance(result, OperationResult):
                raise RegistryError("operation callback returned an invalid result")
            event.bind(result)
            ReceiptRepository.save_result(
                transaction, request.request_id, event_id, result
            )
            return result

        try:
            committed, result = self._database.commit_command(  # type: ignore[arg-type]
                command, event, apply
            )
        except (VersionConflictError, sqlite3.IntegrityError) as error:
            raced = self._find_receipt(request.request_id)
            if raced is not None:
                return self._reconcile(raced, digest)
            if isinstance(error, VersionConflictError):
                raise RequestRejection(
                    409,
                    "version_conflict",
                    "the expected version is stale",
                    fields={
                        "entity_id": error.entity_id,
                        "expected_version": error.expected,
                        "current_version": error.observed,
                    },
                ) from error
            raise
        except sqlite3.DatabaseError as error:
            if not _is_storage_unavailable(error):
                raise
            raise _unavailable() from error
        except (DatabaseError, StorageConfigurationError) as error:
            raise _unavailable() from error
        if prepared.after_commit is not None:
            prepared.after_commit(result)
        return RequestReceipt(
            request_id=committed.request_id,
            status=result.status,
            entity_id=committed.entity_id,
            resulting_version=committed.version,
            event_id=committed.event_id,
            result=dict(result.data),
            project_id=result.project_id,
            activity_id=result.activity_id,
        )

    def _reject_stale_external_operation(self, request: RequestEnvelope) -> None:
        """Reject stale registration writes before their external preparation.

        Confirmation and publication recovery prepare against Git and GitHub.
        Their activity identity is already authoritative in the envelope, so
        the exact version can and must be checked before invoking the handler.
        The transactional command check remains the final concurrency guard.
        """
        if request.operation not in {
            "registration.confirm",
            "registration.cancel",
            "registration.retry",
        }:
            return
        if request.activity_id is None or request.expected_version is None:
            return
        try:
            with self._database.read_connection() as connection:
                row = connection.execute(
                    "SELECT version FROM entity_versions WHERE entity_id = ?",
                    (request.activity_id,),
                ).fetchone()
        except sqlite3.DatabaseError as error:
            if not _is_storage_unavailable(error):
                raise
            raise _unavailable() from error
        observed = 0 if row is None else int(row[0])
        if observed != request.expected_version:
            raise RequestRejection(
                409,
                "version_conflict",
                "the expected version is stale",
                fields={
                    "entity_id": request.activity_id,
                    "expected_version": request.expected_version,
                    "current_version": observed,
                },
            )

    def lookup(self, authorization: str | None, request_id: str) -> RequestReceipt:
        self._authenticator.authenticate_read(authorization)
        try:
            canonical_identifier(request_id, "request_id")
        except ContractError as error:
            raise _invalid(str(error), "request_id") from error
        saved = self._find_receipt(request_id)
        if saved is None:
            raise RequestRejection(
                404, "request_not_found", "the requested receipt was not found"
            )
        return saved[0]

    def authenticate_write(self, authorization: str | None) -> None:
        """Authenticate before the transport parses a submitted representation."""
        self._authenticator.authenticate_write(authorization)

    def authenticate_read(self, authorization: str | None) -> None:
        """Authenticate before the transport validates a receipt identifier."""
        self._authenticator.authenticate_read(authorization)

    def _find_receipt(self, request_id: str) -> tuple[RequestReceipt, str] | None:
        try:
            return self._receipts.find(request_id)
        except ReceiptDataError as error:
            raise RequestRejection(
                503,
                "receipt_unavailable",
                "the saved request receipt is unavailable",
                fields={"request_id": request_id},
            ) from error
        except sqlite3.DatabaseError as error:
            if not _is_storage_unavailable(error):
                raise
            raise _unavailable() from error
        except (DatabaseError, StorageConfigurationError) as error:
            raise _unavailable() from error

    @staticmethod
    def _reconcile(saved: tuple[RequestReceipt, str], digest: str) -> RequestReceipt:
        receipt, saved_digest = saved
        if saved_digest != digest:
            raise RequestRejection(
                409,
                "request_content_conflict",
                "request_id is already bound to different request content",
                fields={"request_id": receipt.request_id},
            )
        return receipt


def _optional_identifier(value: object, field: str) -> str | None:
    if value is None:
        return None
    return canonical_identifier(value, field)  # type: ignore[arg-type]


def _resolved_context(
    field: str, submitted: str | None, created: str | None
) -> str | None:
    if submitted is not None and created is not None and submitted != created:
        raise RegistryError(f"operation result {field} conflicts with request context")
    return submitted if submitted is not None else created


def _is_storage_unavailable(error: sqlite3.DatabaseError) -> bool:
    code = getattr(error, "sqlite_errorcode", None)
    if isinstance(code, int):
        base_code = code & 0xFF
        return base_code in {
            sqlite3.SQLITE_BUSY,
            sqlite3.SQLITE_LOCKED,
            sqlite3.SQLITE_READONLY,
            sqlite3.SQLITE_IOERR,
            sqlite3.SQLITE_CORRUPT,
            sqlite3.SQLITE_FULL,
            sqlite3.SQLITE_CANTOPEN,
            sqlite3.SQLITE_NOTADB,
        }
    message = str(error).casefold()
    return message in {
        "database is locked",
        "database table is locked",
        "attempt to write a readonly database",
        "disk i/o error",
        "database or disk is full",
        "unable to open database file",
        "database disk image is malformed",
        "file is not a database",
    }


def _unavailable() -> RequestRejection:
    return RequestRejection(
        503,
        "service_unavailable",
        "request storage is temporarily unavailable",
    )


def _invalid(message: str, *fields: str) -> RequestRejection:
    affected: dict[str, object] = {}
    if fields:
        affected["affected"] = list(fields)
    return RequestRejection(400, "invalid_request", message, fields=affected)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
