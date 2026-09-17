"""Shared records for the foundation database boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping


_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_DOMAIN = re.compile(r"[a-z][a-z0-9_-]{0,63}\Z")


class ContractError(ValueError):
    """Raised when a caller crosses the database boundary with invalid data."""


def canonical_identifier(value: str, field: str = "identifier") -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ContractError(f"{field} is not a canonical identifier")
    return value


def positive_version(value: int, field: str = "version") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ContractError(f"{field} must be a positive integer")
    return value


def expected_version(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ContractError("expected_version must be a nonnegative integer")
    return value


def canonical_json(value: Mapping[str, Any]) -> str:
    if not isinstance(value, Mapping):
        raise ContractError("event data must be an object")
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError) as error:
        raise ContractError("event data is not canonical JSON") from error


@dataclass(frozen=True)
class DomainMigration:
    """One immutable, ordered schema change owned by an installed domain."""

    domain: str
    version: int
    identity: str
    statements: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.domain, str) or _DOMAIN.fullmatch(self.domain) is None:
            raise ContractError("migration domain is invalid")
        positive_version(self.version, "migration version")
        canonical_identifier(self.identity, "migration identity")
        if not isinstance(self.statements, tuple) or not self.statements:
            raise ContractError("migration statements must be a nonempty tuple")
        if any(
            not isinstance(statement, str) or not statement.strip()
            for statement in self.statements
        ):
            raise ContractError("migration statements must be nonempty text")

    @property
    def checksum(self) -> str:
        encoded = canonical_json(
            {
                "domain": self.domain,
                "identity": self.identity,
                "statements": list(self.statements),
                "version": self.version,
            }
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Command:
    """Canonical metadata for one atomic service command."""

    request_id: str
    operation: str
    actor_id: str
    entity_id: str
    expected_version: int
    content_digest: str

    def __post_init__(self) -> None:
        canonical_identifier(self.request_id, "request_id")
        canonical_identifier(self.operation, "operation")
        canonical_identifier(self.actor_id, "actor_id")
        canonical_identifier(self.entity_id, "entity_id")
        expected_version(self.expected_version)
        if not isinstance(self.content_digest, str) or re.fullmatch(
            r"[0-9a-f]{64}", self.content_digest
        ) is None:
            raise ContractError("content_digest must be a lowercase SHA-256 digest")


@dataclass(frozen=True)
class Event:
    """An event written to the outbox as part of a command transaction."""

    event_id: str
    occurred_at: str
    type: str
    data: Mapping[str, Any]
    project_id: str | None = None
    activity_id: str | None = None

    def __post_init__(self) -> None:
        canonical_identifier(self.event_id, "event_id")
        canonical_identifier(self.type, "event type")
        if self.project_id is not None:
            canonical_identifier(self.project_id, "project_id")
        if self.activity_id is not None:
            canonical_identifier(self.activity_id, "activity_id")
        try:
            parsed = datetime.strptime(self.occurred_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        except (TypeError, ValueError) as error:
            raise ContractError("occurred_at must be UTC with microseconds") from error
        if parsed.replace(tzinfo=timezone.utc).utcoffset() != timezone.utc.utcoffset(None):
            raise ContractError("occurred_at must be UTC")
        canonical_json(self.data)


@dataclass(frozen=True)
class CommandResult:
    request_id: str
    entity_id: str
    version: int
    event_id: str
