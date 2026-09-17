from __future__ import annotations

import hashlib
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from maestro.foundation import (
    Command,
    Database,
    DomainMigration,
    Event,
    MigrationConflictError,
    StorageConfigurationError,
    StorageSettings,
    UnsupportedStoreError,
    VersionConflictError,
)


WIDGET_MIGRATION = DomainMigration(
    domain="widgets",
    version=1,
    identity="widgets-schema-v1",
    statements=(
        """
        CREATE TABLE widgets(
            widget_id TEXT PRIMARY KEY,
            version INTEGER NOT NULL,
            value TEXT NOT NULL
        )
        """,
    ),
)


def command(request_id: str, entity_id: str, expected_version: int = 0) -> Command:
    return Command(
        request_id=request_id,
        operation="widget.update",
        actor_id="owner-local",
        entity_id=entity_id,
        expected_version=expected_version,
        content_digest=hashlib.sha256(request_id.encode()).hexdigest(),
    )


def event(event_id: str, value: str) -> Event:
    return Event(
        event_id=event_id,
        occurred_at="2026-09-17T12:34:56.000000Z",
        project_id="project-one",
        activity_id="activity-one",
        type="widget.changed",
        data={"value": value},
    )


class StoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "maestro.sqlite3"
        self.settings = StorageSettings(path=self.path)

    def database(self) -> Database:
        return Database(self.settings, [WIDGET_MIGRATION])

    @staticmethod
    def save_widget(transaction, next_version: int, *, value: str = "saved") -> str:
        transaction.execute(
            "INSERT INTO widgets(widget_id, version, value) VALUES (?, ?, ?)",
            ("widget-one", next_version, value),
        )
        return value

    def test_command_commits_receipt_effect_and_event_and_reopens(self) -> None:
        database = self.database()
        result, effect_result = database.commit_command(
            command("request-one", "widget-one"),
            event("event-one", "saved"),
            self.save_widget,
        )

        self.assertEqual(1, result.version)
        self.assertEqual("saved", effect_result)

        reopened = self.database()
        with reopened.read_connection() as connection:
            receipt = connection.execute(
                "SELECT entity_id, resulting_version FROM request_receipts"
            ).fetchone()
            widget = connection.execute(
                "SELECT widget_id, version, value FROM widgets"
            ).fetchone()
            saved_event = connection.execute(
                "SELECT event_id, type, data_json FROM outbox_events"
            ).fetchone()

        self.assertEqual(("widget-one", 1), receipt)
        self.assertEqual(("widget-one", 1, "saved"), widget)
        self.assertEqual(
            ("event-one", "widget.changed", '{"value":"saved"}'), saved_event
        )

    def test_failed_effect_rolls_back_receipt_effect_and_event(self) -> None:
        database = self.database()

        def interrupted(transaction, next_version: int) -> None:
            transaction.execute(
                "INSERT INTO widgets(widget_id, version, value) VALUES (?, ?, ?)",
                ("widget-one", next_version, "not-committed"),
            )
            raise RuntimeError("injected interruption")

        with self.assertRaisesRegex(RuntimeError, "injected interruption"):
            database.commit_command(
                command("request-interrupted", "widget-one"),
                event("event-interrupted", "not-committed"),
                interrupted,
            )

        with database.read_connection() as connection:
            counts = tuple(
                connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in ("request_receipts", "widgets", "outbox_events", "entity_versions")
            )
        self.assertEqual((0, 0, 0, 0), counts)

    def test_two_competing_expected_versions_apply_exactly_once(self) -> None:
        database = self.database()
        database.initialize()
        barrier = threading.Barrier(3)
        successes: list[str] = []
        conflicts: list[VersionConflictError] = []
        unexpected: list[BaseException] = []

        def writer(index: int) -> None:
            try:
                barrier.wait()
                request_id = f"request-{index}"
                event_id = f"event-{index}"

                def apply(transaction, next_version: int) -> None:
                    transaction.execute(
                        "INSERT INTO widgets(widget_id, version, value) VALUES (?, ?, ?)",
                        ("contended-widget", next_version, request_id),
                    )

                database.commit_command(
                    command(request_id, "contended-widget"),
                    event(event_id, request_id),
                    apply,
                )
                successes.append(request_id)
            except VersionConflictError as error:
                conflicts.append(error)
            except BaseException as error:  # retained for a useful assertion below
                unexpected.append(error)

        threads = [threading.Thread(target=writer, args=(index,)) for index in (1, 2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()

        self.assertEqual([], unexpected)
        self.assertEqual(1, len(successes))
        self.assertEqual(1, len(conflicts))
        self.assertEqual((0, 1), (conflicts[0].expected, conflicts[0].observed))
        with database.read_connection() as connection:
            self.assertEqual(1, connection.execute("SELECT COUNT(*) FROM widgets").fetchone()[0])
            self.assertEqual(
                1, connection.execute("SELECT COUNT(*) FROM request_receipts").fetchone()[0]
            )
            self.assertEqual(
                1, connection.execute("SELECT COUNT(*) FROM outbox_events").fetchone()[0]
            )

    def test_every_connection_enforces_required_sqlite_pragmas(self) -> None:
        database = self.database()
        with database.read_connection() as connection:
            first = (
                connection.execute("PRAGMA journal_mode").fetchone()[0],
                connection.execute("PRAGMA synchronous").fetchone()[0],
                connection.execute("PRAGMA foreign_keys").fetchone()[0],
            )
        with database.transaction() as transaction:
            second = (
                transaction.execute("PRAGMA journal_mode").fetchone()[0],
                transaction.execute("PRAGMA synchronous").fetchone()[0],
                transaction.execute("PRAGMA foreign_keys").fetchone()[0],
            )

        self.assertEqual(("wal", 2, 1), first)
        self.assertEqual(("wal", 2, 1), second)

    def test_invalid_or_unsupported_storage_is_rejected_without_replacement(self) -> None:
        with self.assertRaises(StorageConfigurationError):
            StorageSettings(path=Path("relative.sqlite3"))
        with self.assertRaises(StorageConfigurationError):
            StorageSettings(engine="postgres", path=self.path)
        with self.assertRaises(StorageConfigurationError):
            StorageSettings(path=Path(":memory:"))

        missing_path = Path(self.temporary.name) / "missing" / "maestro.sqlite3"
        with self.assertRaises(StorageConfigurationError):
            Database(StorageSettings(path=missing_path)).initialize()
        self.assertFalse(missing_path.parent.exists())

        legacy_path = Path(self.temporary.name) / "legacy.sqlite3"
        legacy = sqlite3.connect(legacy_path)
        legacy.execute("CREATE TABLE legacy(value TEXT)")
        legacy.execute("INSERT INTO legacy(value) VALUES ('preserved')")
        legacy.commit()
        legacy.close()

        with self.assertRaises(UnsupportedStoreError):
            Database(StorageSettings(path=legacy_path)).initialize()
        observed = sqlite3.connect(legacy_path).execute("SELECT value FROM legacy").fetchone()
        self.assertEqual(("preserved",), observed)

    def test_migrations_are_ordered_and_conflicting_identities_are_rejected(self) -> None:
        alpha = DomainMigration(
            domain="alpha",
            version=1,
            identity="alpha-v1",
            statements=("CREATE TABLE alpha_record(value TEXT)",),
        )
        beta = DomainMigration(
            domain="beta",
            version=1,
            identity="beta-v1",
            statements=("CREATE TABLE beta_record(value TEXT)",),
        )
        database = Database(self.settings, [beta, alpha])
        database.initialize()
        with database.read_connection() as connection:
            applied = connection.execute(
                "SELECT domain, version FROM domain_migrations ORDER BY rowid"
            ).fetchall()
        self.assertEqual([("alpha", 1), ("beta", 1)], applied)

        changed_alpha = DomainMigration(
            domain="alpha",
            version=1,
            identity="alpha-v1",
            statements=("CREATE TABLE altered(value TEXT)",),
        )
        with self.assertRaises(MigrationConflictError):
            Database(self.settings, [changed_alpha]).initialize()


if __name__ == "__main__":
    unittest.main()
