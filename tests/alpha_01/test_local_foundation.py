from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from maestro.config import RuntimeConfig
from maestro.storage import SCHEMA_VERSION, SQLiteFoundation


class LocalFoundationTests(unittest.TestCase):
    def test_health_creates_and_reuses_database_inside_runtime_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            runtime_dir = Path(temporary_directory) / "runtime"
            foundation = SQLiteFoundation(RuntimeConfig.from_runtime_dir(runtime_dir))

            first = foundation.health()
            second = foundation.health()

            database_path = runtime_dir / "maestro.sqlite3"
            self.assertEqual(first.database_path, str(database_path))
            self.assertTrue(database_path.is_file())
            self.assertEqual(first.schema_version, SCHEMA_VERSION)
            self.assertEqual(second.schema_version, SCHEMA_VERSION)
            self.assertEqual(first.journal_mode, "wal")
            self.assertTrue(first.foreign_keys_enabled)

            with sqlite3.connect(database_path) as connection:
                versions = connection.execute("SELECT version FROM schema_versions ORDER BY version").fetchall()
            self.assertEqual(versions, [(SCHEMA_VERSION,)])

    def test_default_runtime_directory_is_under_repository_var(self) -> None:
        self.assertEqual(RuntimeConfig.from_runtime_dir().runtime_dir, RuntimeConfig.from_runtime_dir().runtime_dir)
        self.assertEqual(RuntimeConfig.from_runtime_dir().runtime_dir.name, "var")


if __name__ == "__main__":
    unittest.main()
