"""Minimal SQLite foundation: connection safety and migration metadata only."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .config import RuntimeConfig


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class DatabaseHealth:
    """Readiness facts emitted without performing any worker activity."""

    database_path: str
    schema_version: int
    journal_mode: str
    foreign_keys_enabled: bool


class SQLiteFoundation:
    """Owns only Alpha-01 migration metadata, not operational packet state."""

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config

    def health(self) -> DatabaseHealth:
        self.config.ensure_runtime_dir()
        with self._connect() as connection:
            journal_mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
            foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys=ON").fetchone())
            foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys").fetchone()[0])
            if journal_mode != "wal":
                raise RuntimeError(f"SQLite WAL mode is unavailable: {journal_mode}")
            self._apply_migrations(connection)
            version = int(connection.execute("SELECT MAX(version) FROM schema_versions").fetchone()[0])

        return DatabaseHealth(
            database_path=str(self.config.database_path),
            schema_version=version,
            journal_mode=journal_mode,
            foreign_keys_enabled=foreign_keys_enabled,
        )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.config.database_path)

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
