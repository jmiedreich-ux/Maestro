"""Minimal SQLite foundation: connection safety and migration metadata only."""

from __future__ import annotations

import os
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
        # Reconstruct through RuntimeConfig so direct service construction also
        # validates before health() can create a directory or open SQLite.
        self.config = RuntimeConfig(config.runtime_dir)

    def health(self) -> DatabaseHealth:
        # Hold an O_NOFOLLOW directory descriptor through SQLite's entire
        # mutation window. /proc/self/fd retains that physical directory even
        # if its pathname is swapped for a symlink after validation.
        self.config = RuntimeConfig(self.config.runtime_dir)
        with self.config.open_runtime_dir_fd() as runtime_fd:
            connection = self._connect(runtime_fd)
            try:
                journal_mode = str(connection.execute("PRAGMA journal_mode=WAL").fetchone()[0]).lower()
                foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys=ON").fetchone())
                foreign_keys_enabled = bool(connection.execute("PRAGMA foreign_keys").fetchone()[0])
                if journal_mode != "wal":
                    raise RuntimeError(f"SQLite WAL mode is unavailable: {journal_mode}")
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
