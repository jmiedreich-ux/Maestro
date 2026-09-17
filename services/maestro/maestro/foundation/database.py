"""Service-owned SQLite connections, migrations, and atomic writes."""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, Sequence, TypeVar

from .contracts import Command, CommandResult, DomainMigration, Event, canonical_json
from .settings import StorageConfigurationError, StorageSettings


STORE_FORMAT_VERSION = 1
BUSY_TIMEOUT_MS = 5000
_INITIALIZATION_LOCK = threading.RLock()
_EffectResult = TypeVar("_EffectResult")


class DatabaseError(RuntimeError):
    """Base error for the service-owned database boundary."""


class UnsupportedStoreError(DatabaseError):
    """Raised without replacing an existing incompatible database."""


class MigrationConflictError(DatabaseError):
    """Raised when installed migration identities or bytes disagree."""


class VersionConflictError(DatabaseError):
    """Raised when a command's optimistic version is stale."""

    def __init__(self, entity_id: str, expected: int, observed: int) -> None:
        super().__init__(
            f"version conflict for {entity_id}: expected {expected}, observed {observed}"
        )
        self.entity_id = entity_id
        self.expected = expected
        self.observed = observed


class MigrationRegistry:
    """Collect application-owned migrations with deterministic ordering."""

    def __init__(self, migrations: Sequence[DomainMigration] = ()) -> None:
        self._by_key: dict[tuple[str, int], DomainMigration] = {}
        self._by_identity: dict[str, DomainMigration] = {}
        for migration in migrations:
            self.register(migration)

    def register(self, migration: DomainMigration) -> None:
        key = (migration.domain, migration.version)
        by_key = self._by_key.get(key)
        by_identity = self._by_identity.get(migration.identity)
        if by_key is not None and by_key != migration:
            raise MigrationConflictError(
                f"migration {migration.domain}@{migration.version} is registered differently"
            )
        if by_identity is not None and by_identity != migration:
            raise MigrationConflictError(
                f"migration identity {migration.identity} is registered differently"
            )
        self._by_key[key] = migration
        self._by_identity[migration.identity] = migration

    def ordered(self) -> tuple[DomainMigration, ...]:
        return tuple(self._by_key[key] for key in sorted(self._by_key))


class Transaction:
    """The only SQL boundary supplied to service and domain repositories."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def execute(
        self, statement: str, parameters: tuple[object, ...] = ()
    ) -> sqlite3.Cursor:
        return self._connection.execute(statement, parameters)

    def executemany(
        self, statement: str, parameters: Sequence[tuple[object, ...]]
    ) -> sqlite3.Cursor:
        return self._connection.executemany(statement, parameters)

    def current_version(self, entity_id: str) -> int:
        row = self.execute(
            "SELECT version FROM entity_versions WHERE entity_id = ?", (entity_id,)
        ).fetchone()
        return 0 if row is None else int(row[0])


class Database:
    """Open one configured database and serialize each short service write."""

    def __init__(
        self,
        settings: StorageSettings,
        migrations: Sequence[DomainMigration] = (),
    ) -> None:
        if not isinstance(settings, StorageSettings):
            raise StorageConfigurationError("database requires validated StorageSettings")
        self.settings = settings
        self.registry = MigrationRegistry(migrations)
        self._initialized = False

    @property
    def path(self) -> Path:
        return self.settings.path

    def initialize(self) -> None:
        """Validate/open the configured store and atomically install migrations."""
        with _INITIALIZATION_LOCK:
            self.settings.validate_host_path()
            connection = self._connect()
            try:
                self._verify_or_bootstrap_store(connection)
                self._apply_migrations(connection)
            finally:
                connection.close()
            self._initialized = True

    @contextmanager
    def transaction(self) -> Iterator[Transaction]:
        """Yield one immediate write transaction, rolling back every failure."""
        self._ensure_initialized()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            transaction = Transaction(connection)
            try:
                yield transaction
            except BaseException:
                connection.rollback()
                raise
            else:
                connection.commit()
        finally:
            connection.close()

    @contextmanager
    def read_connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a configured, short-lived read connection."""
        self._ensure_initialized()
        connection = self._connect()
        try:
            connection.execute("PRAGMA query_only = ON")
            yield connection
        finally:
            connection.close()

    def commit_command(
        self,
        command: Command,
        event: Event,
        apply_effect: Callable[[Transaction, int], _EffectResult],
    ) -> tuple[CommandResult, _EffectResult]:
        """Save receipt, caller-owned effect, version, and event atomically."""
        with self.transaction() as transaction:
            observed = transaction.current_version(command.entity_id)
            if observed != command.expected_version:
                raise VersionConflictError(
                    command.entity_id, command.expected_version, observed
                )
            next_version = observed + 1
            transaction.execute(
                """
                INSERT INTO request_receipts(
                    request_id, operation, actor_id, entity_id, expected_version,
                    resulting_version, content_digest
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    command.request_id,
                    command.operation,
                    command.actor_id,
                    command.entity_id,
                    command.expected_version,
                    next_version,
                    command.content_digest,
                ),
            )
            effect_result = apply_effect(transaction, next_version)
            transaction.execute(
                """
                INSERT INTO entity_versions(entity_id, version) VALUES (?, ?)
                ON CONFLICT(entity_id) DO UPDATE SET version = excluded.version
                """,
                (command.entity_id, next_version),
            )
            transaction.execute(
                """
                INSERT INTO outbox_events(
                    schema_version, event_id, occurred_at, project_id, activity_id,
                    type, data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.schema_version,
                    event.event_id,
                    event.occurred_at,
                    event.project_id,
                    event.activity_id,
                    event.type,
                    canonical_json(event.data),
                ),
            )

        return (
            CommandResult(
                request_id=command.request_id,
                entity_id=command.entity_id,
                version=next_version,
                event_id=event.event_id,
            ),
            effect_result,
        )

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            self.initialize()

    def _connect(self) -> sqlite3.Connection:
        try:
            connection = sqlite3.connect(
                self.path,
                timeout=BUSY_TIMEOUT_MS / 1000,
                isolation_level=None,
            )
        except (sqlite3.Error, OSError) as error:
            raise StorageConfigurationError(
                f"cannot open configured SQLite storage: {self.path}"
            ) from error

        try:
            connection.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
            journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0])
            connection.execute("PRAGMA synchronous = FULL")
            connection.execute("PRAGMA foreign_keys = ON")
            if journal_mode.lower() != "wal":
                raise UnsupportedStoreError("configured database cannot use WAL journaling")
            if int(connection.execute("PRAGMA synchronous").fetchone()[0]) != 2:
                raise UnsupportedStoreError(
                    "configured database cannot use FULL synchronous writes"
                )
            if int(connection.execute("PRAGMA foreign_keys").fetchone()[0]) != 1:
                raise UnsupportedStoreError("configured database cannot enforce foreign keys")
            return connection
        except BaseException:
            connection.close()
            raise

    def _verify_or_bootstrap_store(self, connection: sqlite3.Connection) -> None:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        }
        if tables and "maestro_store_metadata" not in tables:
            raise UnsupportedStoreError(
                "existing database is not a supported Maestro service store"
            )

        connection.execute("BEGIN IMMEDIATE")
        try:
            for statement in _FOUNDATION_SCHEMA:
                connection.execute(statement)
            row = connection.execute(
                "SELECT format_version FROM maestro_store_metadata WHERE singleton = 1"
            ).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO maestro_store_metadata(singleton, format_version) VALUES (1, ?)",
                    (STORE_FORMAT_VERSION,),
                )
            elif int(row[0]) != STORE_FORMAT_VERSION:
                raise UnsupportedStoreError(
                    f"unsupported Maestro store format version: {row[0]}"
                )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise

    def _apply_migrations(self, connection: sqlite3.Connection) -> None:
        connection.execute("BEGIN IMMEDIATE")
        try:
            for migration in self.registry.ordered():
                by_slot = connection.execute(
                    """
                    SELECT identity, checksum FROM domain_migrations
                    WHERE domain = ? AND version = ?
                    """,
                    (migration.domain, migration.version),
                ).fetchone()
                by_identity = connection.execute(
                    """
                    SELECT domain, version, checksum FROM domain_migrations
                    WHERE identity = ?
                    """,
                    (migration.identity,),
                ).fetchone()
                if by_slot is not None:
                    if (str(by_slot[0]), str(by_slot[1])) != (
                        migration.identity,
                        migration.checksum,
                    ):
                        raise MigrationConflictError(
                            f"installed migration {migration.domain}@{migration.version} conflicts"
                        )
                    continue
                if by_identity is not None:
                    raise MigrationConflictError(
                        f"installed migration identity {migration.identity} conflicts"
                    )
                previous = connection.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM domain_migrations WHERE domain = ?",
                    (migration.domain,),
                ).fetchone()
                if int(previous[0]) + 1 != migration.version:
                    raise MigrationConflictError(
                        f"migration {migration.domain}@{migration.version} is out of order"
                    )
                for statement in migration.statements:
                    connection.execute(statement)
                connection.execute(
                    """
                    INSERT INTO domain_migrations(domain, version, identity, checksum)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        migration.domain,
                        migration.version,
                        migration.identity,
                        migration.checksum,
                    ),
                )
            connection.commit()
        except BaseException:
            connection.rollback()
            raise


_FOUNDATION_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS maestro_store_metadata(
        singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
        format_version INTEGER NOT NULL CHECK(format_version > 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS domain_migrations(
        domain TEXT NOT NULL,
        version INTEGER NOT NULL CHECK(version > 0),
        identity TEXT NOT NULL UNIQUE,
        checksum TEXT NOT NULL,
        applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(domain, version)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS entity_versions(
        entity_id TEXT PRIMARY KEY,
        version INTEGER NOT NULL CHECK(version > 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS request_receipts(
        request_id TEXT PRIMARY KEY,
        operation TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        expected_version INTEGER NOT NULL CHECK(expected_version >= 0),
        resulting_version INTEGER NOT NULL CHECK(resulting_version > 0),
        content_digest TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS outbox_events(
        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
        schema_version INTEGER NOT NULL CHECK(schema_version = 1),
        event_id TEXT NOT NULL UNIQUE,
        occurred_at TEXT NOT NULL,
        project_id TEXT,
        activity_id TEXT,
        type TEXT NOT NULL,
        data_json TEXT NOT NULL
    )
    """,
)
