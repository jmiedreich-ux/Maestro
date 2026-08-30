from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig, RuntimePathError
from maestro import config as runtime_config_module
from maestro.storage import SCHEMA_VERSION, SQLiteFoundation


class LocalFoundationTests(unittest.TestCase):
    def assert_no_runtime_artifacts(self, directory: Path) -> None:
        artifact_names = {
            "maestro.sqlite3",
            "maestro.sqlite3-journal",
            "maestro.sqlite3-wal",
            "maestro.sqlite3-shm",
            "maestro.log",
            "maestro.sock",
        }
        self.assertFalse(any((directory / name).exists() for name in artifact_names))
        if directory.is_dir():
            self.assertEqual(list(directory.iterdir()), [])

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
        self.assert_no_runtime_artifacts(rejected_path)

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
        self.assert_no_runtime_artifacts(rejected_path)

    def test_outside_repository_runtime_path_is_rejected_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            rejected_path = Path(temporary_directory) / "outside-runtime"

            self.assertFalse(rejected_path.exists())
            with self.assertRaises(RuntimePathError):
                RuntimeConfig(rejected_path)
            self.assertFalse(rejected_path.exists())
            self.assert_no_runtime_artifacts(rejected_path)

    def test_direct_foundation_construction_rejects_unvalidated_source_path(self) -> None:
        rejected_path = REPOSITORY_ROOT / "services" / "maestro" / "maestro" / "runtime-foundation-check"
        unsafe_config = object.__new__(RuntimeConfig)
        object.__setattr__(unsafe_config, "runtime_dir", rejected_path)

        self.assertFalse(rejected_path.exists())
        with self.assertRaises(RuntimePathError):
            SQLiteFoundation(unsafe_config)
        self.assertFalse(rejected_path.exists())
        self.assert_no_runtime_artifacts(rejected_path)

    def test_symlinked_runtime_component_is_rejected_without_outside_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            outside_directory = Path(temporary_directory)
            container = DEFAULT_RUNTIME_DIR / "alpha-01-r1-symlink-component"
            container.mkdir(parents=True, exist_ok=False)
            linked_component = container / "outside-link"
            linked_component.symlink_to(outside_directory, target_is_directory=True)
            rejected_path = linked_component / "runtime"
            try:
                with self.assertRaises(RuntimePathError):
                    RuntimeConfig(rejected_path)
                self.assert_no_runtime_artifacts(outside_directory)
                self.assertFalse((outside_directory / "runtime").exists())
            finally:
                linked_component.unlink()
                container.rmdir()

    def test_symlink_swap_before_health_cannot_escape_runtime_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            outside_directory = Path(temporary_directory)
            runtime_directory = DEFAULT_RUNTIME_DIR / "alpha-01-r1-race-check"
            runtime_directory.mkdir(parents=True, exist_ok=False)
            foundation = SQLiteFoundation(RuntimeConfig(runtime_directory))

            runtime_directory.rmdir()
            runtime_directory.symlink_to(outside_directory, target_is_directory=True)
            try:
                with self.assertRaises(RuntimePathError):
                    foundation.health()
                self.assert_no_runtime_artifacts(outside_directory)
                self.assertFalse((outside_directory / "alpha-01-r1-race-check").exists())
            finally:
                runtime_directory.unlink()

    def test_component_swap_after_revalidation_cannot_escape_runtime_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            outside_directory = Path(temporary_directory)
            runtime_directory = DEFAULT_RUNTIME_DIR / "alpha-01-r1-openat-race-check"
            runtime_directory.mkdir(parents=True, exist_ok=False)
            foundation = SQLiteFoundation(RuntimeConfig(runtime_directory))
            original_open_or_create = runtime_config_module._open_or_create_directory

            def swap_then_open(parent_fd: int, component: str) -> int:
                if component == runtime_directory.name:
                    runtime_directory.rmdir()
                    runtime_directory.symlink_to(outside_directory, target_is_directory=True)
                return original_open_or_create(parent_fd, component)

            try:
                with patch("maestro.config._open_or_create_directory", side_effect=swap_then_open):
                    with self.assertRaises(RuntimePathError):
                        foundation.health()
                self.assert_no_runtime_artifacts(outside_directory)
                self.assertFalse((outside_directory / "alpha-01-r1-openat-race-check").exists())
            finally:
                runtime_directory.unlink()


if __name__ == "__main__":
    unittest.main()
