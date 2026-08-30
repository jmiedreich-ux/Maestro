"""Minimal SQLite foundation: connection safety and migration metadata only."""

from __future__ import annotations

import os
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from .config import RuntimeConfig


SCHEMA_VERSION = 1


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

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Keep all lifecycle reads/writes behind the same physical runtime boundary."""
        self.config = RuntimeConfig(self.config.runtime_dir)
        with self.config.open_runtime_dir_fd() as runtime_fd:
            connection = self._connect(runtime_fd)
            try:
                self._prepare_connection(connection)
                self._apply_migrations(connection)
                # DDL/migration metadata may begin SQLite's implicit transaction.
                # Finish that setup before callers take the explicit claim lock.
                connection.commit()
                yield connection
            finally:
                connection.close()

    @staticmethod
    def _connect(runtime_fd: int) -> sqlite3.Connection:
        return sqlite3.connect(f"/proc/self/fd/{runtime_fd}/maestro.sqlite3")

    @staticmethod
    def _apply_migrations(connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_versions (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute("INSERT OR IGNORE INTO schema_versions(version) VALUES (?)", (SCHEMA_VERSION,))
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

    @staticmethod
    def _prepare_connection(connection: sqlite3.Connection) -> tuple[str, bool]:
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


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
