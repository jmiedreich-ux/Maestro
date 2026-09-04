"""SQLite foundation, additive migrations, and service-owned durable writes."""

from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from .config import RuntimeConfig


SCHEMA_VERSION = 3


@dataclass(frozen=True)
class DatabaseHealth:
    """Readiness facts emitted without performing any worker activity."""

    database_path: str
    schema_version: int
    journal_mode: str
    foreign_keys_enabled: bool


@dataclass(frozen=True)
class PacketClaim:
    """Durable local ownership of one synthetic packet attempt."""

    packet_id: str
    status: str
    claimed: bool
    worktree_path: str | None


class SQLiteFoundation:
    """The service-owned writer for Alpha runtime and packet lifecycle state."""

    def __init__(self, config: RuntimeConfig) -> None:
        # Reconstruct through RuntimeConfig so direct service construction also
        # validates before health() can create a directory or open SQLite.
        self.config = RuntimeConfig(config.runtime_dir)

    def health(self) -> DatabaseHealth:
        # Hold an O_NOFOLLOW directory descriptor through SQLite's mutation
        # window. This enforces the trusted-local, pre-acquisition symlink
        # boundary; post-acquisition same-UID/root directory moves are outside
        # Alpha-01's declared assurance model.
        self.config = RuntimeConfig(self.config.runtime_dir)
        with self.config.open_runtime_dir_fd() as runtime_fd:
            connection = self._connect(runtime_fd)
            try:
                journal_mode, foreign_keys_enabled = self._prepare_connection(connection)
                self._apply_migrations(connection)
                version = int(connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0])
                connection.commit()
            finally:
                connection.close()

        return DatabaseHealth(
            database_path=str(self.config.database_path),
            schema_version=version,
            journal_mode=journal_mode,
            foreign_keys_enabled=foreign_keys_enabled,
        )

    def claim_packet(self, packet_id: str, authority: dict[str, Any]) -> PacketClaim:
        """Atomically claim one packet key; replays observe but never replace it."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT status, worktree_path FROM packet_runs WHERE packet_id = ?", (packet_id,)
            ).fetchone()
            if existing is not None:
                connection.commit()
                return PacketClaim(packet_id, str(existing[0]), False, existing[1])
            connection.execute(
                """
                INSERT INTO packet_runs(packet_id, status, authority_json)
                VALUES (?, 'Claimed', ?)
                """,
                (packet_id, _json(authority)),
            )
            connection.execute(
                "INSERT INTO packet_attempts(packet_id, attempt_number, status) VALUES (?, 1, 'Claimed')",
                (packet_id,),
            )
            connection.commit()
        return PacketClaim(packet_id, "Claimed", True, None)

    def start_packet(self, packet_id: str, worktree_path: str, start_evidence: dict[str, Any]) -> PacketClaim:
        """Record one fixture worktree and start facts exactly once after a claim."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, worktree_path FROM packet_runs WHERE packet_id = ?", (packet_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Packet {packet_id} has no durable claim")
            if row[0] != "Claimed":
                connection.commit()
                return PacketClaim(packet_id, str(row[0]), False, row[1])
            connection.execute(
                "UPDATE packet_runs SET status = 'Running', worktree_path = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE packet_id = ?",
                (worktree_path, packet_id),
            )
            connection.execute("UPDATE packet_attempts SET status = 'Running' WHERE packet_id = ?", (packet_id,))
            self._record_evidence(connection, packet_id, "start", start_evidence)
            connection.commit()
        return PacketClaim(packet_id, "Running", True, worktree_path)

    def finish_packet(
        self,
        packet_id: str,
        status: str,
        handoff_kind: str,
        reason: str,
        evidence: dict[str, Any],
    ) -> PacketClaim:
        """Persist one terminal outcome and immutable evidence/handoff facts."""
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT status, worktree_path FROM packet_runs WHERE packet_id = ?", (packet_id,)
            ).fetchone()
            if row is None:
                raise ValueError(f"Packet {packet_id} has no durable claim")
            if row[0] != "Running":
                connection.commit()
                return PacketClaim(packet_id, str(row[0]), False, row[1])
            self._record_evidence(connection, packet_id, "worker_result", evidence)
            connection.execute(
                "INSERT OR IGNORE INTO packet_handoffs(packet_id, handoff_kind, reason) VALUES (?, ?, ?)",
                (packet_id, handoff_kind, reason),
            )
            connection.execute(
                "UPDATE packet_runs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE packet_id = ?",
                (status, packet_id),
            )
            connection.execute("UPDATE packet_attempts SET status = ? WHERE packet_id = ?", (status, packet_id))
            connection.commit()
        return PacketClaim(packet_id, status, True, row[1])

    def packet_snapshot(self, packet_id: str) -> dict[str, Any] | None:
        """Read local lifecycle facts for tests and CLI output; no separate read service."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT packet_id, status, worktree_path FROM packet_runs WHERE packet_id = ?", (packet_id,)
            ).fetchone()
            if row is None:
                return None
            evidence = connection.execute(
                "SELECT evidence_kind, payload_json FROM packet_evidence WHERE packet_id = ? ORDER BY evidence_kind",
                (packet_id,),
            ).fetchall()
            handoffs = connection.execute(
                "SELECT handoff_kind, reason FROM packet_handoffs WHERE packet_id = ? ORDER BY handoff_kind",
                (packet_id,),
            ).fetchall()
        return {
            "packet_id": str(row[0]),
            "status": str(row[1]),
            "worktree_path": row[2],
            "evidence": {str(kind): json.loads(payload) for kind, payload in evidence},
            "handoffs": [{"kind": str(kind), "reason": str(reason)} for kind, reason in handoffs],
        }

    def record_project_authority_load(
        self,
        result: dict[str, Any],
        idempotency_key: str,
        *,
        failure_injector: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        """Atomically retain one Candidate or Blocked authority-load result.

        ``failure_injector`` is an internal deterministic test seam. Production
        callers omit it; each callback occurs inside the one transaction.
        """
        _validate_authority_result(result, idempotency_key)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                by_request = connection.execute(
                    "SELECT idempotency_key FROM project_registration_runs WHERE request_id = ?",
                    (result["request_id"],),
                ).fetchone()
                if by_request is not None and str(by_request[0]) != idempotency_key:
                    raise ValueError("request_id was already used for different authority facts")

                existing = connection.execute(
                    "SELECT request_id FROM project_registration_runs WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing is not None:
                    durable = self._authority_result(connection, str(existing[0]))
                    if durable != result:
                        raise ValueError("idempotency_key was already used for different authority facts")
                    connection.commit()
                    return durable

                manifest = result["normalized_manifest"]
                identity = manifest.get("identity", {})
                project_id: str | None = None
                if result["disposition"] == "Reviewable":
                    project_id = identity["project_id"]
                    connection.execute(
                        """
                        INSERT INTO projects(
                            project_id, repository_identity, default_branch,
                            adapter_version, process_version, registration_state
                        ) VALUES (?, ?, ?, ?, ?, 'Candidate')
                        """,
                        (
                            project_id,
                            result["expected_repository"],
                            identity["default_branch"],
                            identity["adapter_version"],
                            identity["process_version"],
                        ),
                    )
                    _inject(failure_injector, "after_candidate")

                inventory = {
                    "normalized_manifest": manifest,
                    "facts": result["facts"],
                    "summary": result["summary"],
                    "source_revision": result["source_revision"],
                }
                connection.execute(
                    """
                    INSERT INTO project_registration_runs(
                        request_id, idempotency_key, mode, project_id,
                        repository_identity, repository_path, source_commit,
                        manifest_path, manifest_digest, inventory_json,
                        candidate_binding_json, authority_files_json, result
                    ) VALUES (?, ?, 'AuthorityLoad', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result["request_id"],
                        idempotency_key,
                        project_id,
                        result["expected_repository"],
                        result["repository_path"],
                        result["source_commit"],
                        result["manifest_path"],
                        result["manifest_digest"],
                        _json(inventory),
                        _json(manifest) if project_id is not None else None,
                        _json(result["authority_files"]),
                        result["disposition"],
                    ),
                )
                _inject(failure_injector, "after_run")

                connection.execute(
                    """
                    INSERT INTO events(
                        idempotency_key, entity_type, entity_id, event_type,
                        before_json, after_json, reason
                    ) VALUES (?, 'ProjectRegistrationRun', ?, 'AuthorityLoaded', '{}', ?, ?)
                    """,
                    (
                        idempotency_key,
                        result["request_id"],
                        _json(result),
                        "candidate authority is reviewable"
                        if project_id is not None
                        else "authority load is blocked by missing or conflicting facts",
                    ),
                )
                _inject(failure_injector, "after_event")
                connection.commit()
                return result
            except Exception:
                connection.rollback()
                raise

    def project_authority_snapshot(self, request_id: str) -> dict[str, Any] | None:
        """Return the exact durable authority result, including after reopen."""
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM project_registration_runs WHERE request_id = ?", (request_id,)
            ).fetchone()
            if exists is None:
                return None
            return self._authority_result(connection, request_id)

    @staticmethod
    def _authority_result(connection: sqlite3.Connection, request_id: str) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT repository_identity, repository_path, source_commit,
                   manifest_path, manifest_digest, inventory_json,
                   authority_files_json, result
            FROM project_registration_runs WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"unknown project registration request: {request_id}")
        inventory = json.loads(row[5])
        return {
            "request_id": request_id,
            "repository_path": str(row[1]),
            "expected_repository": str(row[0]),
            "source_revision": inventory["source_revision"],
            "source_commit": str(row[2]),
            "manifest_path": str(row[3]),
            "manifest_digest": str(row[4]),
            "normalized_manifest": inventory["normalized_manifest"],
            "authority_files": json.loads(row[6]),
            "facts": inventory["facts"],
            "summary": inventory["summary"],
            "disposition": str(row[7]),
        }

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Keep all lifecycle reads/writes behind the same physical runtime boundary."""
        self.config = RuntimeConfig(self.config.runtime_dir)
        with self.config.open_runtime_dir_fd() as runtime_fd:
            connection = self._connect(runtime_fd)
            try:
                self._prepare_connection(connection)
                self._apply_migrations(connection)
                yield connection
            finally:
                connection.close()

    @staticmethod
    def _connect(runtime_fd: int) -> sqlite3.Connection:
        return sqlite3.connect(f"/proc/self/fd/{runtime_fd}/maestro.sqlite3", timeout=10.0)

    @staticmethod
    def _apply_migrations(
        connection: sqlite3.Connection,
        failure_injector: Callable[[str], None] | None = None,
    ) -> None:
        """Apply the additive version-3 schema in one rollback-safe transaction."""
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            versions = [
                int(row[0])
                for row in connection.execute(
                    "SELECT version FROM schema_versions ORDER BY version"
                ).fetchall()
            ]
            if versions and versions not in ([2], [2, 3], [3]):
                raise RuntimeError(f"unsupported or ambiguous schema history: {versions}")
            if versions == [3]:
                connection.commit()
                return

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS packet_runs (
                    packet_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    authority_json TEXT NOT NULL,
                    worktree_path TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS packet_attempts (
                    packet_id TEXT PRIMARY KEY REFERENCES packet_runs(packet_id),
                    attempt_number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS packet_evidence (
                    packet_id TEXT NOT NULL REFERENCES packet_runs(packet_id),
                    evidence_kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(packet_id, evidence_kind)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS packet_handoffs (
                    packet_id TEXT NOT NULL REFERENCES packet_runs(packet_id),
                    handoff_kind TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(packet_id, handoff_kind)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS discovery_evidence (
                    packet_id TEXT PRIMARY KEY REFERENCES packet_runs(packet_id),
                    inventory_json TEXT NOT NULL,
                    proposed_binding_json TEXT,
                    fixture_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            _inject(failure_injector, "before_m1_schema")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    repository_identity TEXT UNIQUE NOT NULL,
                    default_branch TEXT NOT NULL,
                    adapter_version TEXT NOT NULL,
                    process_version TEXT NOT NULL,
                    registration_state TEXT NOT NULL
                        CHECK(registration_state IN ('Candidate', 'Registered', 'Blocked')),
                    active_binding_revision TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS project_registration_runs (
                    request_id TEXT PRIMARY KEY,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    mode TEXT NOT NULL CHECK(mode = 'AuthorityLoad'),
                    project_id TEXT REFERENCES projects(project_id),
                    repository_identity TEXT NOT NULL,
                    repository_path TEXT NOT NULL,
                    source_commit TEXT NOT NULL,
                    manifest_path TEXT NOT NULL,
                    manifest_digest TEXT NOT NULL,
                    inventory_json TEXT NOT NULL,
                    candidate_binding_json TEXT,
                    authority_files_json TEXT NOT NULL,
                    result TEXT NOT NULL CHECK(result IN ('Reviewable', 'Blocked')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY,
                    idempotency_key TEXT UNIQUE NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    before_json TEXT NOT NULL,
                    after_json TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            _inject(failure_injector, "after_m1_schema")
            if not versions:
                connection.execute("INSERT INTO schema_versions(version) VALUES (?)", (SCHEMA_VERSION,))
            else:
                connection.execute("INSERT OR IGNORE INTO schema_versions(version) VALUES (?)", (SCHEMA_VERSION,))
            _inject(failure_injector, "after_schema_version")
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    @staticmethod
    def _prepare_connection(connection: sqlite3.Connection) -> tuple[str, bool]:
        connection.execute("PRAGMA busy_timeout=10000")
        journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if journal_mode != "wal":
            journal_mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
        connection.execute("PRAGMA foreign_keys=ON")
        foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys").fetchone()[0])
        if journal_mode != "wal":
            raise RuntimeError(f"SQLite WAL mode is unavailable: {journal_mode}")
        return journal_mode, foreign_keys_enabled

    @staticmethod
    def _record_evidence(
        connection: sqlite3.Connection, packet_id: str, evidence_kind: str, payload: dict[str, Any]
    ) -> None:
        connection.execute(
            "INSERT OR IGNORE INTO packet_evidence(packet_id, evidence_kind, payload_json) VALUES (?, ?, ?)",
            (packet_id, evidence_kind, _json(payload)),
        )

    def record_discovery_evidence(
        self,
        packet_id: str,
        inventory: dict[str, Any],
        proposed_binding: dict[str, Any] | None,
        fixture_digest: str,
    ) -> None:
        """Record immutable discovery inventory, binding, and fixture digest."""
        with self._connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO discovery_evidence("
                "packet_id, inventory_json, proposed_binding_json, fixture_digest) "
                "VALUES (?, ?, ?, ?)",
                (
                    packet_id,
                    _json(inventory),
                    _json(proposed_binding) if proposed_binding else None,
                    fixture_digest,
                ),
            )


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _inject(callback: Callable[[str], None] | None, stage: str) -> None:
    if callback is not None:
        callback(stage)


def _validate_authority_result(result: dict[str, Any], idempotency_key: str) -> None:
    required = {
        "request_id", "repository_path", "expected_repository", "source_revision",
        "source_commit", "manifest_path", "manifest_digest", "normalized_manifest",
        "authority_files", "facts", "summary", "disposition",
    }
    if set(result) != required:
        raise ValueError("authority result has an invalid closed shape")
    if not isinstance(idempotency_key, str) or re.fullmatch(r"[0-9a-f]{64}", idempotency_key) is None:
        raise ValueError("idempotency_key must be a SHA-256 hex digest")
    if result["disposition"] not in {"Reviewable", "Blocked"}:
        raise ValueError("authority result disposition is invalid")
    if result["source_revision"] != result["source_commit"]:
        raise ValueError("authority result must retain the exact source commit")
