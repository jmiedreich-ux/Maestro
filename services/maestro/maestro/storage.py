"""SQLite foundation, additive migrations, and service-owned durable writes."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Iterator

from .config import RuntimeConfig


SCHEMA_VERSION = 4
SQLITE_BUSY_TIMEOUT_MS = 5000


# SQLite serializes the database itself, but changing journal mode while a
# second local thread is also bootstrapping the same new database can fail
# before SQLite's busy handler is effective.  Maestro is one service process,
# so serialize only connection preparation and migration.  Logical commands
# remain single-attempt transactions and are never retried here.
_INITIALIZATION_LOCK = threading.RLock()


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
                with _INITIALIZATION_LOCK:
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
                with _INITIALIZATION_LOCK:
                    self._prepare_connection(connection)
                    self._apply_migrations(connection)
                yield connection
            finally:
                connection.close()

    @staticmethod
    def _connect(runtime_fd: int) -> sqlite3.Connection:
        return sqlite3.connect(
            f"/proc/self/fd/{runtime_fd}/maestro.sqlite3",
            timeout=SQLITE_BUSY_TIMEOUT_MS / 1000,
        )

    @staticmethod
    def _apply_migrations(
        connection: sqlite3.Connection,
        failure_injector: Callable[[str], None] | None = None,
    ) -> None:
        with _INITIALIZATION_LOCK:
            SQLiteFoundation._apply_migrations_locked(connection, failure_injector)

    @staticmethod
    def _apply_migrations_locked(
        connection: sqlite3.Connection,
        failure_injector: Callable[[str], None] | None = None,
    ) -> None:
        """Apply the additive schema through version 4 in one transaction.

        Version 4 deliberately uses only ``CREATE``, ``ALTER ... ADD COLUMN``
        and index/trigger creation.  In particular, the accepted Alpha and
        M1-01 tables are never rebuilt: SQLite can therefore roll an injected
        DDL failure back without copying or rewriting any accepted row.
        """
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
            supported_histories = ([2], [2, 3], [3], [2, 3, 4], [3, 4], [4])
            if versions and versions not in supported_histories:
                raise RuntimeError(f"unsupported or ambiguous schema history: {versions}")
            if versions and versions[-1] == SCHEMA_VERSION:
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
            if versions == [2]:
                connection.execute("INSERT INTO schema_versions(version) VALUES (3)")
                versions = [2, 3]

            _inject(failure_injector, "before_m1_02_schema")
            _apply_schema_four(connection, failure_injector)
            connection.execute("INSERT INTO schema_versions(version) VALUES (4)")
            _inject(failure_injector, "after_schema_version")
            connection.commit()
        except Exception:
            connection.rollback()
            raise

    @staticmethod
    def _prepare_connection(connection: sqlite3.Connection) -> tuple[str, bool]:
        with _INITIALIZATION_LOCK:
            connection.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
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


def _apply_schema_four(
    connection: sqlite3.Connection,
    failure_injector: Callable[[str], None] | None,
) -> None:
    """Install the schema-4 extension without rebuilding accepted tables."""
    event_columns = {str(row[1]) for row in connection.execute("PRAGMA table_info(events)")}
    for name, declaration in (
        ("correlation_id", "TEXT"),
        ("causation_event_id", "INTEGER REFERENCES events(event_id)"),
        ("actor_type", "TEXT"),
        ("actor_id", "TEXT"),
        ("command_fingerprint", "TEXT"),
        ("observed_at", "TEXT"),
    ):
        if name not in event_columns:
            connection.execute(f"ALTER TABLE events ADD COLUMN {name} {declaration}")
    _inject(failure_injector, "after_events_extension")

    for statement in _SCHEMA_FOUR_TABLES:
        connection.execute(statement)
    for statement in _SCHEMA_FOUR_INDEXES:
        connection.execute(statement)
    for statement in _SCHEMA_FOUR_TRIGGERS:
        connection.execute(statement)
    _inject(failure_injector, "after_m1_02_schema")


_SCHEMA_FOUR_TABLES = (
    """
    CREATE TABLE project_bindings (
        binding_id TEXT PRIMARY KEY CHECK(length(CAST(binding_id AS BLOB)) BETWEEN 1 AND 512),
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        binding_revision TEXT NOT NULL CHECK(length(CAST(binding_revision AS BLOB)) BETWEEN 1 AND 512),
        source_commit TEXT NOT NULL CHECK(length(source_commit)=40 AND source_commit NOT GLOB '*[^0-9a-f]*'),
        manifest_digest TEXT NOT NULL CHECK(length(manifest_digest)=64 AND manifest_digest NOT GLOB '*[^0-9a-f]*'),
        adapter_version TEXT NOT NULL CHECK(length(CAST(adapter_version AS BLOB)) BETWEEN 1 AND 512),
        process_version TEXT NOT NULL CHECK(length(CAST(process_version AS BLOB)) BETWEEN 1 AND 512),
        authority_reference TEXT NOT NULL CHECK(length(CAST(authority_reference AS BLOB)) BETWEEN 1 AND 512),
        merge_policy TEXT NOT NULL CHECK(length(CAST(merge_policy AS BLOB)) BETWEEN 1 AND 512),
        acceptance_authority TEXT NOT NULL CHECK(acceptance_authority IN ('ProjectArchitect','Owner')),
        merge_execution_authority TEXT NOT NULL CHECK(merge_execution_authority IN ('OwnerPerformed','PolicyDelegated')),
        merge_delegation_reference TEXT,
        binding_json TEXT NOT NULL CHECK(json_valid(binding_json) AND json_type(binding_json)='object' AND length(CAST(binding_json AS BLOB))<=1048576),
        state TEXT NOT NULL CHECK(state IN ('Candidate','Active','Superseded','Blocked')),
        created_at TEXT NOT NULL,
        activated_at TEXT,
        superseded_at TEXT,
        UNIQUE(project_id,binding_revision),
        CHECK((merge_execution_authority='OwnerPerformed' AND merge_delegation_reference IS NULL)
           OR (merge_execution_authority='PolicyDelegated' AND merge_delegation_reference IS NOT NULL))
    )
    """,
    """
    CREATE TABLE secret_reference_observations (
        secret_reference_observation_id TEXT PRIMARY KEY CHECK(length(CAST(secret_reference_observation_id AS BLOB)) BETWEEN 1 AND 512),
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        binding_id TEXT NOT NULL REFERENCES project_bindings(binding_id),
        provider TEXT NOT NULL,
        reference_name TEXT NOT NULL,
        owner_reference TEXT NOT NULL CHECK(length(CAST(owner_reference AS BLOB)) BETWEEN 1 AND 512),
        rotation_at TEXT,
        expires_at TEXT,
        status TEXT NOT NULL CHECK(status IN ('Active','Stale','Revoked','Unavailable')),
        observed_at TEXT NOT NULL,
        UNIQUE(binding_id,provider,reference_name,observed_at)
    )
    """,
    """
    CREATE TABLE graph_projections (
        graph_projection_id TEXT PRIMARY KEY CHECK(length(CAST(graph_projection_id AS BLOB)) BETWEEN 1 AND 512),
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        binding_id TEXT NOT NULL REFERENCES project_bindings(binding_id),
        graph_revision TEXT NOT NULL CHECK(length(CAST(graph_revision AS BLOB)) BETWEEN 1 AND 512),
        authority_reference TEXT NOT NULL CHECK(length(CAST(authority_reference AS BLOB)) BETWEEN 1 AND 512),
        source_base_sha TEXT NOT NULL CHECK(length(source_base_sha)=40 AND source_base_sha NOT GLOB '*[^0-9a-f]*'),
        source_hash TEXT NOT NULL CHECK(length(source_hash)=64 AND source_hash NOT GLOB '*[^0-9a-f]*'),
        state TEXT NOT NULL CHECK(state IN ('Active','Stale','NeedsReplan','Superseded')),
        observed_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),
        UNIQUE(project_id,graph_revision,source_hash)
    )
    """,
    """
    CREATE TABLE work_items (
        work_item_id TEXT PRIMARY KEY CHECK(length(CAST(work_item_id AS BLOB)) BETWEEN 1 AND 512),
        graph_projection_id TEXT NOT NULL REFERENCES graph_projections(graph_projection_id),
        architecture_node_id TEXT NOT NULL CHECK(length(CAST(architecture_node_id AS BLOB)) BETWEEN 1 AND 512),
        task_reference TEXT NOT NULL CHECK(length(CAST(task_reference AS BLOB)) BETWEEN 1 AND 512),
        workstream_ref TEXT NOT NULL CHECK(length(CAST(workstream_ref AS BLOB)) BETWEEN 1 AND 512),
        milestone_ref TEXT NOT NULL CHECK(length(CAST(milestone_ref AS BLOB)) BETWEEN 1 AND 512),
        title TEXT NOT NULL CHECK(length(CAST(title AS BLOB)) BETWEEN 1 AND 512),
        priority TEXT NOT NULL CHECK(length(CAST(priority AS BLOB)) BETWEEN 1 AND 512),
        planned_rank INTEGER NOT NULL CHECK(planned_rank>=0),
        specialist_role TEXT NOT NULL CHECK(length(CAST(specialist_role AS BLOB)) BETWEEN 1 AND 512),
        execution_classes_json TEXT NOT NULL CHECK(json_valid(execution_classes_json) AND json_type(execution_classes_json)='array' AND length(CAST(execution_classes_json AS BLOB))<=1048576),
        dependencies_json TEXT NOT NULL CHECK(json_valid(dependencies_json) AND json_type(dependencies_json)='array' AND length(CAST(dependencies_json AS BLOB))<=1048576),
        change_domains_json TEXT NOT NULL CHECK(json_valid(change_domains_json) AND json_type(change_domains_json)='array' AND length(CAST(change_domains_json AS BLOB))<=1048576),
        input_contract_json TEXT NOT NULL CHECK(json_valid(input_contract_json) AND json_type(input_contract_json)='object' AND length(CAST(input_contract_json AS BLOB))<=1048576),
        output_contract_json TEXT NOT NULL CHECK(json_valid(output_contract_json) AND json_type(output_contract_json)='object' AND length(CAST(output_contract_json AS BLOB))<=1048576),
        planning_state TEXT NOT NULL CHECK(planning_state IN ('Active','NeedsReplan','Superseded')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),
        UNIQUE(graph_projection_id,architecture_node_id)
    )
    """,
    """
    CREATE TABLE runs (
        run_id TEXT PRIMARY KEY CHECK(length(CAST(run_id AS BLOB)) BETWEEN 1 AND 512),
        run_fingerprint TEXT NOT NULL UNIQUE CHECK(length(run_fingerprint)=64 AND run_fingerprint NOT GLOB '*[^0-9a-f]*'),
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        binding_id TEXT NOT NULL REFERENCES project_bindings(binding_id),
        graph_projection_id TEXT NOT NULL REFERENCES graph_projections(graph_projection_id),
        milestone_ref TEXT NOT NULL CHECK(length(CAST(milestone_ref AS BLOB)) BETWEEN 1 AND 512),
        approved_authority_reference TEXT NOT NULL CHECK(length(CAST(approved_authority_reference AS BLOB)) BETWEEN 1 AND 512),
        branch_name TEXT,
        pull_request_reference TEXT,
        current_head TEXT CHECK(current_head IS NULL OR (length(current_head)=40 AND current_head NOT GLOB '*[^0-9a-f]*')),
        current_head_source_reference TEXT,
        candidate_head TEXT CHECK(candidate_head IS NULL OR (length(candidate_head)=40 AND candidate_head NOT GLOB '*[^0-9a-f]*')),
        candidate_head_source_reference TEXT,
        state TEXT NOT NULL CHECK(state IN ('Planned','Running','Blocked','AwaitingArchitect','AwaitingOwner','Complete','Cancelled')),
        acceptance_boundary TEXT NOT NULL CHECK(acceptance_boundary IN ('ProjectArchitect','Owner')),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1)
    )
    """,
    """
    CREATE TABLE packets (
        packet_id TEXT PRIMARY KEY CHECK(length(CAST(packet_id AS BLOB)) BETWEEN 1 AND 512),
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
        packet_revision TEXT NOT NULL CHECK(length(CAST(packet_revision AS BLOB)) BETWEEN 1 AND 512),
        authority_reference TEXT NOT NULL CHECK(length(CAST(authority_reference AS BLOB)) BETWEEN 1 AND 512),
        base_commit TEXT NOT NULL CHECK(length(base_commit)=40 AND base_commit NOT GLOB '*[^0-9a-f]*'),
        current_head TEXT CHECK(current_head IS NULL OR (length(current_head)=40 AND current_head NOT GLOB '*[^0-9a-f]*')),
        expected_branch TEXT NOT NULL CHECK(length(CAST(expected_branch AS BLOB)) BETWEEN 1 AND 512),
        role_contract_reference TEXT NOT NULL CHECK(length(CAST(role_contract_reference AS BLOB)) BETWEEN 1 AND 512),
        sop_reference TEXT NOT NULL CHECK(length(CAST(sop_reference AS BLOB)) BETWEEN 1 AND 512),
        executor_class TEXT NOT NULL CHECK(length(CAST(executor_class AS BLOB)) BETWEEN 1 AND 512),
        integration_route TEXT NOT NULL CHECK(length(CAST(integration_route AS BLOB)) BETWEEN 1 AND 512),
        reviewer_route TEXT NOT NULL CHECK(length(CAST(reviewer_route AS BLOB)) BETWEEN 1 AND 512),
        owned_paths_json TEXT NOT NULL CHECK(json_valid(owned_paths_json) AND json_type(owned_paths_json)='array' AND length(CAST(owned_paths_json AS BLOB))<=1048576),
        forbidden_paths_json TEXT NOT NULL CHECK(json_valid(forbidden_paths_json) AND json_type(forbidden_paths_json)='array' AND length(CAST(forbidden_paths_json AS BLOB))<=1048576),
        checks_json TEXT NOT NULL CHECK(json_valid(checks_json) AND json_type(checks_json)='array' AND length(CAST(checks_json AS BLOB))<=1048576),
        resource_claims_json TEXT NOT NULL CHECK(json_valid(resource_claims_json) AND json_type(resource_claims_json)='array' AND length(CAST(resource_claims_json AS BLOB))<=1048576),
        context_policy_json TEXT NOT NULL CHECK(json_valid(context_policy_json) AND json_type(context_policy_json)='object' AND length(CAST(context_policy_json AS BLOB))<=1048576),
        state TEXT NOT NULL CHECK(state IN ('Planned','Waiting','Blocked','Ready','Dispatchable','Leased','Running','AwaitingIntegration','AwaitingReview','MergeReady','AwaitingArchitect','AwaitingOwner','Merged','Complete','NeedsReplan','Cancelled')),
        correction_count INTEGER NOT NULL DEFAULT 0 CHECK(correction_count IN (0,1)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),
        UNIQUE(run_id,work_item_id,packet_revision)
    )
    """,
    """
    CREATE TABLE leases (
        lease_id TEXT PRIMARY KEY CHECK(length(CAST(lease_id AS BLOB)) BETWEEN 1 AND 512),
        packet_id TEXT NOT NULL REFERENCES packets(packet_id),
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        claim_key TEXT NOT NULL UNIQUE CHECK(length(CAST(claim_key AS BLOB)) BETWEEN 1 AND 512),
        run_fingerprint TEXT NOT NULL CHECK(length(run_fingerprint)=64 AND run_fingerprint NOT GLOB '*[^0-9a-f]*'),
        base_commit TEXT NOT NULL CHECK(length(base_commit)=40 AND base_commit NOT GLOB '*[^0-9a-f]*'),
        worktree_path TEXT NOT NULL CHECK(length(CAST(worktree_path AS BLOB)) BETWEEN 1 AND 512),
        executor_route TEXT NOT NULL CHECK(length(CAST(executor_route AS BLOB)) BETWEEN 1 AND 512),
        holder_id TEXT NOT NULL CHECK(length(CAST(holder_id AS BLOB)) BETWEEN 1 AND 512),
        state TEXT NOT NULL CHECK(state IN ('Active','Released','Expired','Cancelled')),
        acquired_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        heartbeat_at TEXT NOT NULL,
        released_at TEXT,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),
        CHECK(expires_at>acquired_at)
    )
    """,
    """
    CREATE TABLE attempts (
        attempt_id TEXT PRIMARY KEY CHECK(length(CAST(attempt_id AS BLOB)) BETWEEN 1 AND 512),
        packet_id TEXT NOT NULL REFERENCES packets(packet_id),
        lease_id TEXT NOT NULL REFERENCES leases(lease_id),
        attempt_number INTEGER NOT NULL CHECK(attempt_number IN (1,2)),
        attempt_kind TEXT NOT NULL CHECK(attempt_kind IN ('Initial','TargetedCorrection')),
        executor_class TEXT NOT NULL CHECK(length(CAST(executor_class AS BLOB)) BETWEEN 1 AND 512),
        model_identity TEXT NOT NULL CHECK(length(CAST(model_identity AS BLOB)) BETWEEN 1 AND 512),
        runtime_identity TEXT NOT NULL CHECK(length(CAST(runtime_identity AS BLOB)) BETWEEN 1 AND 512),
        state TEXT NOT NULL CHECK(state IN ('Planned','Running','Succeeded','Failed','Cancelled','TimedOut','Stale')),
        result_commit TEXT CHECK(result_commit IS NULL OR (length(result_commit)=40 AND result_commit NOT GLOB '*[^0-9a-f]*')),
        correction_for_review_id TEXT REFERENCES reviews(review_id) DEFERRABLE INITIALLY DEFERRED,
        started_at TEXT,
        finished_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1),
        UNIQUE(packet_id,attempt_number),
        CHECK((attempt_number=1 AND attempt_kind='Initial' AND correction_for_review_id IS NULL)
           OR (attempt_number=2 AND attempt_kind='TargetedCorrection' AND correction_for_review_id IS NOT NULL))
    )
    """,
    """
    CREATE TABLE resource_locks (
        lock_id TEXT PRIMARY KEY CHECK(length(CAST(lock_id AS BLOB)) BETWEEN 1 AND 512),
        resource_key TEXT NOT NULL CHECK(length(CAST(resource_key AS BLOB)) BETWEEN 1 AND 512),
        lock_kind TEXT NOT NULL CHECK(lock_kind IN ('Path','SharedBoundary','FiniteResource')),
        packet_id TEXT NOT NULL REFERENCES packets(packet_id),
        lease_id TEXT NOT NULL REFERENCES leases(lease_id),
        state TEXT NOT NULL CHECK(state IN ('Active','Released','Expired')),
        acquired_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        released_at TEXT,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1)
    )
    """,
    """
    CREATE TABLE evidence (
        evidence_id TEXT PRIMARY KEY CHECK(length(CAST(evidence_id AS BLOB)) BETWEEN 1 AND 512),
        idempotency_key TEXT NOT NULL UNIQUE CHECK(length(CAST(idempotency_key AS BLOB)) BETWEEN 1 AND 512),
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        packet_id TEXT NOT NULL REFERENCES packets(packet_id),
        attempt_id TEXT REFERENCES attempts(attempt_id),
        evidence_kind TEXT NOT NULL CHECK(length(CAST(evidence_kind AS BLOB)) BETWEEN 1 AND 512),
        payload_json TEXT NOT NULL CHECK(json_valid(payload_json) AND json_type(payload_json)='object' AND length(CAST(payload_json AS BLOB))<=1048576),
        content_digest TEXT NOT NULL CHECK(length(content_digest)=64 AND content_digest NOT GLOB '*[^0-9a-f]*'),
        source_reference TEXT,
        redaction_state TEXT NOT NULL CHECK(redaction_state IN ('Redacted','NotRequired')),
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE waits (
        wait_id TEXT PRIMARY KEY CHECK(length(CAST(wait_id AS BLOB)) BETWEEN 1 AND 512),
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        packet_id TEXT REFERENCES packets(packet_id),
        gate_type TEXT NOT NULL CHECK(length(CAST(gate_type AS BLOB)) BETWEEN 1 AND 512),
        awaited_role TEXT NOT NULL CHECK(length(CAST(awaited_role AS BLOB)) BETWEEN 1 AND 512),
        awaited_reference TEXT NOT NULL CHECK(length(CAST(awaited_reference AS BLOB)) BETWEEN 1 AND 512),
        expected_result TEXT NOT NULL CHECK(length(CAST(expected_result AS BLOB)) BETWEEN 1 AND 512),
        timeout_at TEXT,
        next_permitted_action TEXT NOT NULL CHECK(length(CAST(next_permitted_action AS BLOB)) BETWEEN 1 AND 512),
        state TEXT NOT NULL CHECK(state IN ('Open','Resolved','Expired','Cancelled')),
        resolution_reason_payload_json TEXT CHECK(resolution_reason_payload_json IS NULL OR (json_valid(resolution_reason_payload_json) AND json_type(resolution_reason_payload_json)='object' AND length(CAST(resolution_reason_payload_json AS BLOB))<=1048576)),
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1)
    )
    """,
    """
    CREATE TABLE reviews (
        review_id TEXT PRIMARY KEY CHECK(length(CAST(review_id AS BLOB)) BETWEEN 1 AND 512),
        packet_id TEXT NOT NULL REFERENCES packets(packet_id),
        attempt_id TEXT REFERENCES attempts(attempt_id),
        review_kind TEXT NOT NULL CHECK(review_kind IN ('Integration','IndependentImplementation')),
        reviewer_role TEXT NOT NULL CHECK(length(CAST(reviewer_role AS BLOB)) BETWEEN 1 AND 512),
        reviewer_instance TEXT NOT NULL CHECK(length(CAST(reviewer_instance AS BLOB)) BETWEEN 1 AND 512),
        base_commit TEXT NOT NULL CHECK(length(base_commit)=40 AND base_commit NOT GLOB '*[^0-9a-f]*'),
        head_commit TEXT NOT NULL CHECK(length(head_commit)=40 AND head_commit NOT GLOB '*[^0-9a-f]*'),
        result TEXT NOT NULL CHECK(result IN ('ValidateOnly','Assemble','NeedsReplan','Approve','RequestChanges','Comment')),
        findings_json TEXT NOT NULL CHECK(json_valid(findings_json) AND json_type(findings_json)='array' AND length(CAST(findings_json AS BLOB))<=1048576),
        coverage_json TEXT NOT NULL CHECK(json_valid(coverage_json) AND json_type(coverage_json)='object' AND length(CAST(coverage_json AS BLOB))<=1048576),
        correction_number INTEGER NOT NULL CHECK(correction_number IN (0,1)),
        created_at TEXT NOT NULL,
        UNIQUE(packet_id,review_kind,reviewer_instance,head_commit,correction_number)
    )
    """,
    """
    CREATE TABLE notifications (
        notification_id TEXT PRIMARY KEY CHECK(length(CAST(notification_id AS BLOB)) BETWEEN 1 AND 512),
        event_id INTEGER NOT NULL REFERENCES events(event_id),
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        packet_id TEXT REFERENCES packets(packet_id),
        channel TEXT NOT NULL CHECK(channel IN ('LocalDurable','Slack')),
        destination_reference TEXT NOT NULL CHECK(length(CAST(destination_reference AS BLOB)) BETWEEN 1 AND 512),
        audience TEXT NOT NULL CHECK(length(CAST(audience AS BLOB)) BETWEEN 1 AND 512),
        severity TEXT NOT NULL CHECK(severity IN ('Informational','ActionNeeded','CompletionReady','CompletionSummary')),
        message_type TEXT NOT NULL CHECK(length(CAST(message_type AS BLOB)) BETWEEN 1 AND 512),
        grouping_key TEXT NOT NULL CHECK(length(CAST(grouping_key AS BLOB)) BETWEEN 1 AND 512),
        escalation_at TEXT,
        payload_json TEXT NOT NULL CHECK(json_valid(payload_json) AND json_type(payload_json)='object' AND length(CAST(payload_json AS BLOB))<=1048576),
        state TEXT NOT NULL CHECK(state IN ('Pending','Delivered','Failed','Acknowledged')),
        attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count>=0),
        last_error_payload_json TEXT CHECK(last_error_payload_json IS NULL OR (json_valid(last_error_payload_json) AND json_type(last_error_payload_json)='object' AND length(CAST(last_error_payload_json AS BLOB))<=1048576)),
        next_attempt_at TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1)
    )
    """,
    """
    CREATE TABLE acceptance_records (
        acceptance_id TEXT PRIMARY KEY CHECK(length(CAST(acceptance_id AS BLOB)) BETWEEN 1 AND 512),
        subject_type TEXT NOT NULL CHECK(subject_type IN ('Packet','Run')),
        subject_id TEXT NOT NULL CHECK(length(CAST(subject_id AS BLOB)) BETWEEN 1 AND 512),
        packet_id TEXT REFERENCES packets(packet_id),
        run_id TEXT REFERENCES runs(run_id),
        sequence_number INTEGER NOT NULL CHECK(sequence_number IN (1,2)),
        supersedes_acceptance_id TEXT REFERENCES acceptance_records(acceptance_id),
        required_authority TEXT NOT NULL CHECK(required_authority IN ('ProjectArchitect','Owner')),
        decision TEXT NOT NULL CHECK(decision IN ('Accepted','Returned','ReservedChoice')),
        authority_reference TEXT NOT NULL CHECK(length(CAST(authority_reference AS BLOB)) BETWEEN 1 AND 512),
        exact_head TEXT NOT NULL CHECK(length(exact_head)=40 AND exact_head NOT GLOB '*[^0-9a-f]*'),
        review_coverage_json TEXT NOT NULL CHECK(json_valid(review_coverage_json) AND json_type(review_coverage_json)='object' AND length(CAST(review_coverage_json AS BLOB))<=1048576),
        reason_payload_json TEXT NOT NULL CHECK(json_valid(reason_payload_json) AND json_type(reason_payload_json)='object' AND length(CAST(reason_payload_json AS BLOB))<=1048576),
        created_at TEXT NOT NULL,
        CHECK((subject_type='Packet' AND packet_id IS NOT NULL AND run_id IS NULL AND subject_id=packet_id)
           OR (subject_type='Run' AND run_id IS NOT NULL AND packet_id IS NULL AND subject_id=run_id)),
        UNIQUE(subject_type,subject_id,sequence_number)
    )
    """,
    """
    CREATE TABLE merge_observations (
        merge_observation_id TEXT PRIMARY KEY CHECK(length(CAST(merge_observation_id AS BLOB)) BETWEEN 1 AND 512),
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        packet_id TEXT NOT NULL REFERENCES packets(packet_id),
        acceptance_id TEXT REFERENCES acceptance_records(acceptance_id),
        repository_reference TEXT NOT NULL CHECK(length(CAST(repository_reference AS BLOB)) BETWEEN 1 AND 512),
        default_branch TEXT NOT NULL CHECK(length(CAST(default_branch AS BLOB)) BETWEEN 1 AND 512),
        accepted_head TEXT NOT NULL CHECK(length(accepted_head)=40 AND accepted_head NOT GLOB '*[^0-9a-f]*'),
        merge_commit TEXT NOT NULL CHECK(length(merge_commit)=40 AND merge_commit NOT GLOB '*[^0-9a-f]*'),
        source_kind TEXT NOT NULL CHECK(source_kind IN ('Git','GitHub')),
        source_reference TEXT NOT NULL CHECK(length(CAST(source_reference AS BLOB)) BETWEEN 1 AND 512),
        performed_by_authority TEXT NOT NULL CHECK(performed_by_authority IN ('Owner','DelegatedIdentity')),
        performed_by_reference TEXT NOT NULL CHECK(length(CAST(performed_by_reference AS BLOB)) BETWEEN 1 AND 512),
        delegation_reference TEXT,
        review_coverage_json TEXT CHECK(review_coverage_json IS NULL OR (json_valid(review_coverage_json) AND json_type(review_coverage_json)='object' AND length(CAST(review_coverage_json AS BLOB))<=1048576)),
        observed_at TEXT NOT NULL,
        CHECK((performed_by_authority='Owner' AND delegation_reference IS NULL)
           OR (performed_by_authority='DelegatedIdentity' AND delegation_reference IS NOT NULL))
    )
    """,
    """
    CREATE TABLE worker_progress_observations (
        progress_id TEXT PRIMARY KEY CHECK(length(CAST(progress_id AS BLOB)) BETWEEN 1 AND 512),
        attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
        plan_payload_json TEXT NOT NULL CHECK(json_valid(plan_payload_json) AND json_type(plan_payload_json)='object' AND length(CAST(plan_payload_json AS BLOB))<=1048576),
        current_step_payload_json TEXT NOT NULL CHECK(json_valid(current_step_payload_json) AND json_type(current_step_payload_json)='object' AND length(CAST(current_step_payload_json AS BLOB))<=1048576),
        blocker_payload_json TEXT NOT NULL CHECK(json_valid(blocker_payload_json) AND json_type(blocker_payload_json)='object' AND length(CAST(blocker_payload_json AS BLOB))<=1048576),
        eta_text TEXT NOT NULL,
        confidence TEXT NOT NULL CHECK(confidence IN ('Reported','Unknown')),
        status_request_state TEXT NOT NULL CHECK(status_request_state IN ('NotRequested','Requested','Answered','Unavailable')),
        next_permitted_action TEXT NOT NULL CHECK(length(CAST(next_permitted_action AS BLOB)) BETWEEN 1 AND 512),
        observed_at TEXT NOT NULL,
        received_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE attempt_context_usage (
        context_usage_id TEXT PRIMARY KEY CHECK(length(CAST(context_usage_id AS BLOB)) BETWEEN 1 AND 512),
        attempt_id TEXT NOT NULL UNIQUE REFERENCES attempts(attempt_id),
        model_identity TEXT NOT NULL CHECK(length(CAST(model_identity AS BLOB)) BETWEEN 1 AND 512),
        runtime_identity TEXT NOT NULL CHECK(length(CAST(runtime_identity AS BLOB)) BETWEEN 1 AND 512),
        quantization TEXT,
        configured_context_limit INTEGER CHECK(configured_context_limit IS NULL OR configured_context_limit>0),
        context_policy_digest TEXT NOT NULL CHECK(length(context_policy_digest)=64 AND context_policy_digest NOT GLOB '*[^0-9a-f]*'),
        counting_method TEXT NOT NULL CHECK(counting_method IN ('Runtime','Tokenizer','Estimate','Unavailable')),
        starting_input_measurement_json TEXT NOT NULL CHECK(json_valid(starting_input_measurement_json) AND json_type(starting_input_measurement_json)='object' AND length(CAST(starting_input_measurement_json AS BLOB))<=1048576),
        future_growth_estimate_json TEXT NOT NULL CHECK(json_valid(future_growth_estimate_json) AND json_type(future_growth_estimate_json)='object' AND length(CAST(future_growth_estimate_json AS BLOB))<=1048576),
        token_measurements_json TEXT NOT NULL CHECK(json_valid(token_measurements_json) AND json_type(token_measurements_json)='object' AND length(CAST(token_measurements_json AS BLOB))<=1048576),
        cost_measurement_json TEXT NOT NULL CHECK(json_valid(cost_measurement_json) AND json_type(cost_measurement_json)='object' AND length(CAST(cost_measurement_json AS BLOB))<=1048576),
        availability_state TEXT NOT NULL CHECK(availability_state IN ('Available','Partial','Unavailable')),
        observed_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1 CHECK(version>=1)
    )
    """,
    """
    CREATE TABLE provider_allowance_windows (
        allowance_observation_id TEXT PRIMARY KEY CHECK(length(CAST(allowance_observation_id AS BLOB)) BETWEEN 1 AND 512),
        provider TEXT NOT NULL,
        account_reference TEXT NOT NULL CHECK(length(CAST(account_reference AS BLOB)) BETWEEN 1 AND 512),
        native_window_type TEXT NOT NULL CHECK(length(CAST(native_window_type AS BLOB)) BETWEEN 1 AND 512),
        used_value TEXT,
        remaining_value TEXT,
        native_unit TEXT,
        reset_at TEXT,
        precision TEXT NOT NULL CHECK(precision IN ('Exact','Coarse','Unavailable')),
        measurement_quality TEXT NOT NULL CHECK(measurement_quality IN ('RuntimeReported','ProviderReported','Estimated','Unavailable')),
        freshness TEXT NOT NULL CHECK(freshness IN ('Fresh','Stale','Unavailable')),
        observed_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE usage_reconciliations (
        usage_reconciliation_id TEXT PRIMARY KEY CHECK(length(CAST(usage_reconciliation_id AS BLOB)) BETWEEN 1 AND 512),
        allowance_observation_id TEXT NOT NULL REFERENCES provider_allowance_windows(allowance_observation_id),
        window_change_value TEXT NOT NULL,
        tracked_controlled_value TEXT NOT NULL,
        registered_coarse_value TEXT NOT NULL,
        unattributed_value TEXT NOT NULL,
        native_unit TEXT NOT NULL CHECK(length(CAST(native_unit AS BLOB)) BETWEEN 1 AND 512),
        measurement_quality TEXT NOT NULL CHECK(measurement_quality IN ('Exact','Coarse','Estimated')),
        observed_at TEXT NOT NULL
    )
    """,
)


_SCHEMA_FOUR_INDEXES = (
    "CREATE UNIQUE INDEX one_active_binding_per_project ON project_bindings(project_id) WHERE state='Active'",
    "CREATE UNIQUE INDEX one_active_graph_per_project ON graph_projections(project_id) WHERE state='Active'",
    "CREATE UNIQUE INDEX one_active_lease_per_packet ON leases(packet_id) WHERE state='Active'",
    "CREATE UNIQUE INDEX one_active_lease_per_worktree ON leases(worktree_path) WHERE state='Active'",
    "CREATE UNIQUE INDEX one_active_resource_key ON resource_locks(resource_key) WHERE state='Active'",
    "CREATE UNIQUE INDEX one_open_wait_per_packet_gate ON waits(packet_id,gate_type) WHERE state='Open' AND packet_id IS NOT NULL",
)


_PRODUCTION_EVENTS_SQL = ",".join(
    repr(value)
    for value in (
        "ProjectBindingRecorded", "SecretReferenceObserved", "GraphProjectionRecorded",
        "GraphProjectionStateChanged", "WorkItemProjected", "RunCreated", "RunStateChanged",
        "PacketMaterialized", "PacketStateChanged", "PacketClaimed", "LeaseHeartbeatRecorded",
        "LeaseReleased", "LeaseExpired", "AttemptRecorded", "AttemptStateChanged",
        "StaleObservationIgnored", "EvidenceAppended", "WaitOpened", "WaitStateChanged",
        "NotificationRecorded", "NotificationStateChanged", "ReviewRecorded",
        "WorkerProgressRecorded", "AttemptContextUsageRecorded", "AllowanceWindowObserved",
        "UsageReconciliationRecorded", "AcceptanceRecorded", "MergeObserved",
        "StartupReconciliationRecorded",
    )
)


_SCHEMA_FOUR_TRIGGERS = (
    """
    CREATE TRIGGER events_require_v4_metadata
    BEFORE INSERT ON events
    WHEN NOT (NEW.entity_type='ProjectRegistrationRun' AND NEW.event_type='AuthorityLoaded')
      AND (NEW.correlation_id IS NULL OR NEW.actor_type IS NULL OR NEW.actor_id IS NULL
           OR NEW.command_fingerprint IS NULL OR NEW.observed_at IS NULL)
    BEGIN SELECT RAISE(ABORT, 'schema-4 event metadata is required'); END
    """,
    """
    CREATE TRIGGER events_validate_v4_shape
    BEFORE INSERT ON events
    WHEN NOT (NEW.entity_type='ProjectRegistrationRun' AND NEW.event_type='AuthorityLoaded')
      AND (
        length(CAST(NEW.idempotency_key AS BLOB)) NOT BETWEEN 1 AND 512
        OR length(CAST(NEW.entity_type AS BLOB)) NOT BETWEEN 1 AND 512
        OR length(CAST(NEW.entity_id AS BLOB)) NOT BETWEEN 1 AND 512
        OR length(CAST(NEW.correlation_id AS BLOB)) NOT BETWEEN 1 AND 512
        OR length(CAST(NEW.actor_type AS BLOB)) NOT BETWEEN 1 AND 512
        OR length(CAST(NEW.actor_id AS BLOB)) NOT BETWEEN 1 AND 512
        OR length(NEW.command_fingerprint)<>64
        OR NEW.command_fingerprint GLOB '*[^0-9a-f]*'
        OR length(NEW.observed_at)<>27
        OR NEW.observed_at NOT GLOB '????-??-??T??:??:??.??????Z'
        OR (NEW.causation_event_id IS NOT NULL AND NEW.causation_event_id<=0)
        OR NOT json_valid(NEW.before_json) OR json_type(NEW.before_json)<>'object'
        OR NOT json_valid(NEW.after_json) OR json_type(NEW.after_json)<>'object'
        OR NOT json_valid(NEW.reason) OR json_type(NEW.reason)<>'object'
        OR length(CAST(NEW.before_json AS BLOB))>1048576
        OR length(CAST(NEW.after_json AS BLOB))>1048576
        OR length(CAST(NEW.reason AS BLOB))>1048576
      )
    BEGIN SELECT RAISE(ABORT, 'schema-4 event shape is invalid'); END
    """,
    f"""
    CREATE TRIGGER events_closed_event_type
    BEFORE INSERT ON events
    WHEN NOT (NEW.entity_type='ProjectRegistrationRun' AND NEW.event_type='AuthorityLoaded')
      AND NEW.event_type NOT IN ({_PRODUCTION_EVENTS_SQL})
    BEGIN SELECT RAISE(ABORT, 'unknown production event type'); END
    """,
    """
    CREATE TRIGGER events_no_update BEFORE UPDATE ON events
    BEGIN SELECT RAISE(ABORT, 'events are append-only'); END
    """,
    """
    CREATE TRIGGER events_no_delete BEFORE DELETE ON events
    BEGIN SELECT RAISE(ABORT, 'events are append-only'); END
    """,
) + tuple(
    statement
    for table in (
        "evidence", "reviews", "secret_reference_observations",
        "worker_progress_observations", "provider_allowance_windows",
        "usage_reconciliations", "acceptance_records", "merge_observations",
    )
    for statement in (
        f"CREATE TRIGGER {table}_no_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END",
        f"CREATE TRIGGER {table}_no_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT, '{table} is append-only'); END",
    )
)


def _json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)


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
