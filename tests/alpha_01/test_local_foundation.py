from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig, RuntimePathError
from maestro.storage import SCHEMA_VERSION, SQLiteFoundation


class LocalFoundationTests(unittest.TestCase):
    def test_health_creates_and_reuses_database_inside_runtime_directory(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR) as temporary_directory:
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

    def test_default_runtime_directory_is_the_worktree_var_path(self) -> None:
        expected_runtime_dir = Path(__file__).resolve().parents[2] / "var"
        self.assertEqual(RuntimeConfig.from_runtime_dir().runtime_dir, expected_runtime_dir.resolve())

    def test_source_tree_runtime_path_is_rejected_without_mutation(self) -> None:
        rejected_path = REPOSITORY_ROOT / "services" / "maestro" / "maestro" / "runtime-check"

        self.assertFalse(rejected_path.exists())
        with self.assertRaises(RuntimePathError):
            RuntimeConfig(rejected_path)
        self.assertFalse(rejected_path.exists())
        self.assertFalse((rejected_path / "maestro.sqlite3").exists())

    def test_health_cli_rejects_source_tree_path_without_mutation(self) -> None:
        rejected_path = REPOSITORY_ROOT / "services" / "maestro" / "maestro" / "runtime-cli-check"

        result = subprocess.run(
            [sys.executable, "-m", "maestro.cli", "health", "--runtime-dir", str(rejected_path)],
            cwd=REPOSITORY_ROOT / "services" / "maestro",
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Runtime directory must be inside", result.stderr)
        self.assertFalse(rejected_path.exists())
        self.assertFalse((rejected_path / "maestro.sqlite3").exists())

    def test_outside_repository_runtime_path_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            rejected_path = Path(temporary_directory) / "outside-runtime"

            self.assertFalse(rejected_path.exists())
            with self.assertRaises(RuntimePathError):
                RuntimeConfig(rejected_path)
            self.assertFalse(rejected_path.exists())
            self.assertFalse((rejected_path / "maestro.sqlite3").exists())

    def test_direct_foundation_construction_rejects_unvalidated_source_path(self) -> None:
        rejected_path = REPOSITORY_ROOT / "services" / "maestro" / "maestro" / "runtime-foundation-check"
        unsafe_config = object.__new__(RuntimeConfig)
        object.__setattr__(unsafe_config, "runtime_dir", rejected_path)

        self.assertFalse(rejected_path.exists())
        with self.assertRaises(RuntimePathError):
            SQLiteFoundation(unsafe_config)
        self.assertFalse(rejected_path.exists())
        self.assertFalse((rejected_path / "maestro.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
