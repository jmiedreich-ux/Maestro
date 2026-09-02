from __future__ import annotations

import copy
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path

from maestro.project_authority import ProjectAuthorityLoader, _idempotency_key
from maestro.storage import SCHEMA_VERSION, SQLiteFoundation
from support import RuntimeDirectory, TemporaryProjectRepository


class ProjectAuthorityStorageTests(unittest.TestCase):
    def test_existing_schema_two_upgrades_without_losing_representative_alpha_rows(self) -> None:
        runtime = RuntimeDirectory()
        try:
            runtime.path.mkdir(parents=True)
            database = runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.executescript(
                    """
                    CREATE TABLE schema_versions(
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO schema_versions(version) VALUES (2);
                    CREATE TABLE packet_runs(
                        packet_id TEXT PRIMARY KEY, status TEXT NOT NULL, authority_json TEXT NOT NULL,
                        worktree_path TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO packet_runs(packet_id, status, authority_json) VALUES ('alpha-row', 'Claimed', '{}');
                    CREATE TABLE packet_attempts(
                        packet_id TEXT PRIMARY KEY REFERENCES packet_runs(packet_id), attempt_number INTEGER NOT NULL,
                        status TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO packet_attempts(packet_id, attempt_number, status) VALUES ('alpha-row', 1, 'Claimed');
                    CREATE TABLE packet_evidence(
                        packet_id TEXT NOT NULL REFERENCES packet_runs(packet_id), evidence_kind TEXT NOT NULL,
                        payload_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(packet_id, evidence_kind)
                    );
                    CREATE TABLE packet_handoffs(
                        packet_id TEXT NOT NULL REFERENCES packet_runs(packet_id), handoff_kind TEXT NOT NULL,
                        reason TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(packet_id, handoff_kind)
                    );
                    CREATE TABLE discovery_evidence(
                        packet_id TEXT PRIMARY KEY REFERENCES packet_runs(packet_id), inventory_json TEXT NOT NULL,
                        proposed_binding_json TEXT, fixture_digest TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    INSERT INTO discovery_evidence(packet_id, inventory_json, fixture_digest)
                    VALUES ('alpha-row', '{"area":"preserved"}', 'digest');
                    """
                )

            health = runtime.foundation().health()

            self.assertEqual(health.schema_version, SCHEMA_VERSION)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(
                    connection.execute("SELECT version FROM schema_versions ORDER BY version").fetchall(),
                    [(2,), (3,)],
                )
                self.assertEqual(
                    connection.execute("SELECT packet_id, status FROM packet_runs").fetchall(),
                    [("alpha-row", "Claimed")],
                )
                self.assertEqual(
                    connection.execute("SELECT inventory_json FROM discovery_evidence").fetchone()[0],
                    '{"area":"preserved"}',
                )
        finally:
            runtime.close()

    def test_failed_migration_rolls_back_schema_version_and_created_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "migration.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute(
                    "CREATE TABLE schema_versions("
                    "version INTEGER PRIMARY KEY, "
                    "applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
                )
                connection.execute("INSERT INTO schema_versions(version) VALUES (2)")
                connection.execute("CREATE TABLE alpha_marker(value TEXT NOT NULL)")
                connection.execute("INSERT INTO alpha_marker(value) VALUES ('preserved')")
                connection.commit()

                def fail(stage: str) -> None:
                    if stage == "after_m1_schema":
                        raise RuntimeError("injected migration failure")

                with self.assertRaisesRegex(RuntimeError, "injected migration failure"):
                    SQLiteFoundation._apply_migrations(connection, fail)

                self.assertEqual(
                    connection.execute("SELECT version FROM schema_versions").fetchall(), [(2,)]
                )
                self.assertEqual(
                    connection.execute("SELECT value FROM alpha_marker").fetchall(), [("preserved",)]
                )
                self.assertIsNone(
                    connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
                    ).fetchone()
                )

    def test_injected_candidate_run_and_event_failures_roll_back_complete_transaction(self) -> None:
        repository = TemporaryProjectRepository()
        source_runtime = RuntimeDirectory()
        try:
            result = ProjectAuthorityLoader(source_runtime.foundation()).load(
                repository.path, repository.commit, "owner/example-project"
            ).to_dict()
            key = _idempotency_key(
                result["expected_repository"], result["source_commit"],
                result["manifest_path"], result["manifest_digest"],
            )
            for failure_stage in ("after_candidate", "after_run", "after_event"):
                runtime = RuntimeDirectory()
                try:
                    foundation = runtime.foundation()
                    foundation.health()

                    def fail(stage: str) -> None:
                        if stage == failure_stage:
                            raise RuntimeError(f"injected {stage}")

                    with self.subTest(stage=failure_stage), self.assertRaises(RuntimeError):
                        foundation.record_project_authority_load(result, key, failure_injector=fail)
                    with closing(sqlite3.connect(runtime.path / "maestro.sqlite3")) as connection:
                        counts = [
                            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                            for table in ("projects", "project_registration_runs", "events")
                        ]
                    self.assertEqual(counts, [0, 0, 0])
                finally:
                    runtime.close()
        finally:
            source_runtime.close()
            repository.close()

    def test_reopen_and_identical_replay_return_exact_original_result_once(self) -> None:
        repository = TemporaryProjectRepository()
        runtime = RuntimeDirectory()
        try:
            first = ProjectAuthorityLoader(runtime.foundation()).load(
                repository.path, repository.commit, "owner/example-project"
            )
            reopened = runtime.foundation()
            self.assertEqual(reopened.project_authority_snapshot(first.request_id), first.to_dict())
            second = ProjectAuthorityLoader(reopened).load(
                repository.path, repository.commit, "owner/example-project"
            )
            self.assertEqual(second, first)
            with closing(sqlite3.connect(runtime.path / "maestro.sqlite3")) as connection:
                counts = [
                    connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("projects", "project_registration_runs", "events")
                ]
            self.assertEqual(counts, [1, 1, 1])
        finally:
            runtime.close()
            repository.close()

    def test_request_and_idempotency_reuse_with_different_facts_is_rejected(self) -> None:
        repository = TemporaryProjectRepository()
        runtime = RuntimeDirectory()
        try:
            foundation = runtime.foundation()
            original = ProjectAuthorityLoader(foundation).load(
                repository.path, repository.commit, "owner/example-project"
            ).to_dict()
            key = _idempotency_key(
                original["expected_repository"], original["source_commit"],
                original["manifest_path"], original["manifest_digest"],
            )

            changed_same_key = copy.deepcopy(original)
            changed_same_key["repository_path"] += "-different"
            with self.assertRaisesRegex(ValueError, "idempotency_key"):
                foundation.record_project_authority_load(changed_same_key, key)

            changed_request = copy.deepcopy(original)
            changed_request["request_id"] = "authority-load-different-request"
            with self.assertRaisesRegex(ValueError, "idempotency_key"):
                foundation.record_project_authority_load(changed_request, key)

            with self.assertRaisesRegex(ValueError, "request_id"):
                foundation.record_project_authority_load(original, "f" * 64)
        finally:
            runtime.close()
            repository.close()

    def test_two_concurrent_identical_loads_observe_one_durable_result(self) -> None:
        repository = TemporaryProjectRepository()
        runtime = RuntimeDirectory()
        barrier = threading.Barrier(2)
        results = []
        errors = []

        def load() -> None:
            try:
                barrier.wait()
                result = ProjectAuthorityLoader(runtime.foundation()).load(
                    repository.path, repository.commit, "owner/example-project"
                )
                results.append(result)
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        try:
            threads = [threading.Thread(target=load) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=15)
            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0], results[1])
            with closing(sqlite3.connect(runtime.path / "maestro.sqlite3")) as connection:
                counts = [
                    connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in ("projects", "project_registration_runs", "events")
                ]
            self.assertEqual(counts, [1, 1, 1])
        finally:
            runtime.close()
            repository.close()


if __name__ == "__main__":
    unittest.main()
