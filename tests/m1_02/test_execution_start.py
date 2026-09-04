from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest import mock

from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    ResourceConflict,
    StaleState,
)
from maestro.storage import SCHEMA_VERSION, SQLiteFoundation, _apply_schema_four
from test_assignment_claim import (
    ACTOR,
    ATTEMPT,
    LEASE,
    REASON,
    AssignmentDatabase,
    state_payload,
)
from test_schema_and_records import _schema_three


STARTED = "2026-09-04T12:30:00.000000Z"
AFTER_EXPIRY = "2026-09-04T14:00:00.000000Z"
HANDLE = "provider-job-1"
EXPECTED = "committed-candidate"
START_REASON = {
    "kind": "reason",
    "reason_code": "EXECUTION_OBSERVED",
    "detail_reference": None,
}


def expected_start_result(
    attempt_id="attempt-1", packet_id="packet-1", lease_id="lease-1"
):
    return {
        "attempt": state_payload("Attempt", attempt_id, "Running", 2),
        "execution": {
            "attempt_id": attempt_id,
            "execution_handle": HANDLE,
            "expected_result": EXPECTED,
            "heartbeat_at": STARTED,
            "started_at": STARTED,
        },
        "lease": state_payload("Lease", lease_id, "Active", 1),
        "packet": state_payload("Packet", packet_id, "Running", 6),
    }


def build_schema_four(database: Path, *, with_attempt=True):
    database.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(database)) as connection:
        _schema_three(connection)
        _apply_schema_four(connection, None)
        connection.execute("INSERT INTO schema_versions(version) VALUES (4)")
        if with_attempt:
            connection.execute(
                "INSERT INTO attempts(attempt_id,packet_id,lease_id,attempt_number,attempt_kind,"
                "executor_class,model_identity,runtime_identity,state,result_commit,"
                "correction_for_review_id,started_at,finished_at,created_at,updated_at,version) "
                "VALUES ('preserved-attempt','missing-packet','missing-lease',1,'Initial',"
                "'codex-cloud','gpt-5','codex','Planned',NULL,NULL,NULL,NULL,?,?,1)",
                (STARTED, STARTED),
            )
        connection.commit()


def database_inventory(database: Path):
    with closing(sqlite3.connect(database)) as connection:
        schema = connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        versions = connection.execute(
            "SELECT version,applied_at FROM schema_versions ORDER BY version"
        ).fetchall()
        attempts = connection.execute("SELECT * FROM attempts ORDER BY attempt_id").fetchall()
        return schema, versions, attempts


class ExecutionDatabase(AssignmentDatabase):
    def __init__(self):
        super().__init__()
        self.claimed = self.claim()

    def start(
        self,
        *,
        attempt_id="attempt-1",
        attempt_version=1,
        packet_version=5,
        handle=HANDLE,
        expected_result=EXPECTED,
        reason=START_REASON,
        key="execution-start-1",
        actor=ACTOR,
        now=STARTED,
    ):
        return self.store.start_attempt_execution(
            attempt_id,
            attempt_version,
            packet_version,
            handle,
            expected_result,
            reason,
            key,
            actor,
            now,
        )

    def start_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "AttemptStateChanged"
        ]

    def start_state(self):
        return {
            "attempts": self.rows("attempts"),
            "packets": self.rows("packets"),
            "leases": self.rows("leases"),
            "locks": self.rows("resource_locks"),
            "events": self.start_events(),
        }

    def add_claimed_packet(self):
        self.add_packet("packet-2", "work-2", [])
        self.claim(
            packet_id="packet-2",
            lease={
                **LEASE,
                "lease_id": "lease-2",
                "worktree_path": "/runtime/worktree-2",
            },
            locks=[],
            attempt={**ATTEMPT, "attempt_id": "attempt-2"},
            key="claim-2",
        )


class ExecutionStartTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ExecutionDatabase()

    def tearDown(self):
        if self.runtime is not None:
            self.runtime.close()

    def replace_runtime(self):
        self.runtime.close()
        self.runtime = ExecutionDatabase()

    def test_01_schema_four_upgrades_additively_to_exact_schema_five(self):
        self.runtime.close()
        self.runtime = None
        with tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR) as directory:
            runtime_path = Path(directory) / "runtime"
            database = runtime_path / "maestro.sqlite3"
            build_schema_four(database)
            with closing(sqlite3.connect(database)) as connection:
                before_columns = connection.execute("PRAGMA table_info(attempts)").fetchall()
                before_row = connection.execute(
                    "SELECT * FROM attempts WHERE attempt_id='preserved-attempt'"
                ).fetchone()

            health = SQLiteFoundation(RuntimeConfig(runtime_path)).health()
            self.assertEqual((SCHEMA_VERSION, health.schema_version), (5, 5))
            with closing(sqlite3.connect(database)) as connection:
                columns = connection.execute("PRAGMA table_info(attempts)").fetchall()
                names = [row[1] for row in columns]
                self.assertEqual(
                    names[-4:],
                    [
                        "execution_handle",
                        "expected_result",
                        "heartbeat_at",
                        "completion_evidence_reference",
                    ],
                )
                self.assertEqual(columns[: len(before_columns)], before_columns)
                after_row = connection.execute(
                    "SELECT * FROM attempts WHERE attempt_id='preserved-attempt'"
                ).fetchone()
                self.assertEqual(after_row[: len(before_row)], before_row)
                self.assertEqual(after_row[-4:], (None, None, None, None))
                self.assertEqual(
                    connection.execute(
                        "SELECT version FROM schema_versions ORDER BY version"
                    ).fetchall(),
                    [(3,), (4,), (5,)],
                )
                objects = {
                    row[0]: row[1]
                    for row in connection.execute(
                        "SELECT name,type FROM sqlite_master WHERE name IN "
                        "('one_attempt_per_execution_handle','attempts_execution_shape_insert',"
                        "'attempts_execution_shape_update')"
                    )
                }
                self.assertEqual(
                    objects,
                    {
                        "one_attempt_per_execution_handle": "index",
                        "attempts_execution_shape_insert": "trigger",
                        "attempts_execution_shape_update": "trigger",
                    },
                )
                connection.execute("PRAGMA foreign_keys=OFF")
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "UPDATE attempts SET execution_handle='partial' "
                        "WHERE attempt_id='preserved-attempt'"
                    )
                connection.execute(
                    "UPDATE attempts SET state='Running',execution_handle='handle-preserved',"
                    "expected_result='candidate',started_at=?,heartbeat_at=?,updated_at=?,version=2 "
                    "WHERE attempt_id='preserved-attempt'",
                    (STARTED, STARTED, STARTED),
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "UPDATE attempts SET state='Succeeded',finished_at=?,"
                        "completion_evidence_reference='evidence',result_commit=NULL "
                        "WHERE attempt_id='preserved-attempt'",
                        (AFTER_EXPIRY,),
                    )
                connection.execute(
                    "UPDATE attempts SET state='Succeeded',finished_at=?,"
                    "completion_evidence_reference='evidence',result_commit=? "
                    "WHERE attempt_id='preserved-attempt'",
                    (AFTER_EXPIRY, "a" * 40),
                )

    def test_02_injected_schema_five_failure_rolls_back_schema_version_and_data(self):
        self.runtime.close()
        self.runtime = None
        with tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR) as directory:
            runtime_path = Path(directory) / "runtime"
            database = runtime_path / "maestro.sqlite3"
            build_schema_four(database)
            before = database_inventory(database)

            def fail(stage):
                if stage == "after_m1_execution_schema":
                    raise RuntimeError("injected schema-five failure")

            with closing(sqlite3.connect(database)) as connection:
                with self.assertRaisesRegex(RuntimeError, "schema-five"):
                    SQLiteFoundation._apply_migrations(connection, fail)
            self.assertEqual(database_inventory(database), before)
            with closing(sqlite3.connect(database)) as connection:
                self.assertNotIn(
                    "execution_handle",
                    [row[1] for row in connection.execute("PRAGMA table_info(attempts)")],
                )

    def test_03_reopen_and_two_concurrent_migrators_create_one_version_five_row(self):
        self.runtime.close()
        self.runtime = None
        with tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR) as directory:
            runtime_path = Path(directory) / "runtime"
            database = runtime_path / "maestro.sqlite3"
            build_schema_four(database, with_attempt=False)
            barrier = threading.Barrier(2)
            errors = []

            def migrate():
                try:
                    barrier.wait()
                    with closing(sqlite3.connect(database, timeout=10)) as connection:
                        SQLiteFoundation._prepare_connection(connection)
                        SQLiteFoundation._apply_migrations(connection)
                except Exception as error:  # pragma: no cover - asserted below
                    errors.append(error)

            threads = [threading.Thread(target=migrate) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(15)
            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
            with closing(sqlite3.connect(database)) as connection:
                schema = connection.execute(
                    "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
                ).fetchall()
            self.assertEqual(SQLiteFoundation(RuntimeConfig(runtime_path)).health().schema_version, 5)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT version,COUNT(*) FROM schema_versions GROUP BY version"
                    ).fetchall(),
                    [(3, 1), (4, 1), (5, 1)],
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
                    ).fetchall(),
                    schema,
                )

    def test_04_valid_start_returns_exact_result_and_changes_attempt_and_packet_once(self):
        lease_before = self.runtime.rows("leases")
        locks_before = self.runtime.rows("resource_locks")
        result = self.runtime.start()
        self.assertEqual(result, expected_start_result())
        attempt = self.runtime.store.snapshot("Attempt", "attempt-1")
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual(
            (
                attempt["state"], attempt["version"], attempt["execution_handle"],
                attempt["expected_result"], attempt["started_at"], attempt["heartbeat_at"],
                attempt["finished_at"], attempt["result_commit"],
                attempt["completion_evidence_reference"],
            ),
            ("Running", 2, HANDLE, EXPECTED, STARTED, STARTED, None, None, None),
        )
        self.assertEqual((packet["state"], packet["version"], packet["updated_at"]), ("Running", 6, STARTED))
        self.assertEqual(self.runtime.rows("leases"), lease_before)
        self.assertEqual(self.runtime.rows("resource_locks"), locks_before)
        self.assertEqual(len(self.runtime.start_events()), 1)

    def test_05_malformed_empty_reused_and_concurrently_duplicated_handles_are_blocked(self):
        before = self.runtime.start_state()
        malformed = (
            lambda: self.runtime.start(attempt_id=""),
            lambda: self.runtime.start(attempt_version=False),
            lambda: self.runtime.start(packet_version=0),
            lambda: self.runtime.start(handle=""),
            lambda: self.runtime.start(expected_result=""),
            lambda: self.runtime.start(reason=state_payload("Attempt", "attempt-1", "Planned", 1)),
            lambda: self.runtime.start(key=""),
            lambda: self.runtime.start(actor={"actor_type": "x"}),
            lambda: self.runtime.start(now="later"),
        )
        for command in malformed:
            with self.assertRaises(InvalidRecord):
                command()
            self.assertEqual(self.runtime.start_state(), before)

        self.runtime.start()
        self.runtime.add_claimed_packet()
        with self.assertRaises(ResourceConflict):
            self.runtime.start(
                attempt_id="attempt-2", handle=HANDLE, key="reused-handle"
            )

        self.replace_runtime()
        self.runtime.add_claimed_packet()
        barrier = threading.Barrier(2)

        def start(number):
            barrier.wait()
            try:
                return self.runtime.start(
                    attempt_id=f"attempt-{number}",
                    handle="shared-provider-handle",
                    key=f"shared-handle-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(start, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, ResourceConflict) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.start_events()), 1)

    def test_06_missing_mismatched_wrong_state_parent_and_expired_lease_are_blocked(self):
        cases = (
            "missing-attempt", "missing-packet", "mismatched-lease", "attempt-running",
            "packet-ready", "lease-released", "run-blocked", "run-complete",
            "run-cancelled", "expired-lease",
        )
        for case in cases:
            with self.subTest(case=case):
                self.replace_runtime()
                attempt_id = "attempt-1"
                attempt_version = 1
                packet_version = 5
                if case == "missing-attempt":
                    attempt_id = "missing"
                elif case == "missing-packet":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM packets WHERE packet_id='packet-1'")
                        connection.commit()
                elif case == "mismatched-lease":
                    self.runtime.add_packet("packet-2", "work-2", [])
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE leases SET packet_id='packet-2' WHERE lease_id='lease-1'")
                        connection.commit()
                elif case == "attempt-running":
                    self.runtime.start()
                    attempt_version = 2
                    packet_version = 6
                elif case == "packet-ready":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE packets SET state='Ready' WHERE packet_id='packet-1'")
                        connection.commit()
                elif case == "lease-released":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE leases SET state='Released' WHERE lease_id='lease-1'")
                        connection.commit()
                elif case.startswith("run-"):
                    state = case.removeprefix("run-").capitalize()
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE runs SET state=? WHERE run_id='run-1'", (state,))
                        connection.commit()
                else:
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute(
                            "UPDATE leases SET expires_at='2026-09-04T12:15:00.000000Z' "
                            "WHERE lease_id='lease-1'"
                        )
                        connection.commit()
                before = self.runtime.start_state()
                error = InvalidRecord if case in {"missing-attempt", "missing-packet", "mismatched-lease"} else InvalidTransition
                with self.assertRaises(error):
                    self.runtime.start(
                        attempt_id=attempt_id,
                        attempt_version=attempt_version,
                        packet_version=packet_version,
                        key=f"blocked-{case}",
                    )
                self.assertEqual(self.runtime.start_state(), before)

    def test_07_stale_attempt_or_packet_version_leaves_all_state_unchanged(self):
        before = self.runtime.start_state()
        with self.assertRaisesRegex(StaleState, "attempt"):
            self.runtime.start(attempt_version=2)
        self.assertEqual(self.runtime.start_state(), before)
        with self.assertRaisesRegex(StaleState, "packet"):
            self.runtime.start(packet_version=6, key="stale-packet")
        self.assertEqual(self.runtime.start_state(), before)

    def test_08_same_key_replay_is_exact_and_changed_immutable_facts_conflict(self):
        first = self.runtime.start(key="immutable-start")
        replay = self.runtime.start(key="immutable-start", now=AFTER_EXPIRY)
        self.assertEqual(replay, first)
        changed = (
            lambda: self.runtime.start(key="immutable-start", attempt_id="other"),
            lambda: self.runtime.start(key="immutable-start", attempt_version=2),
            lambda: self.runtime.start(key="immutable-start", packet_version=6),
            lambda: self.runtime.start(key="immutable-start", handle="other"),
            lambda: self.runtime.start(key="immutable-start", expected_result="other"),
            lambda: self.runtime.start(key="immutable-start", reason={**START_REASON, "reason_code": "OTHER"}),
            lambda: self.runtime.start(key="immutable-start", actor=Actor("Other", "developer-1", "correlation-1")),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.start_events()), 1)
        self.assertEqual(self.runtime.start_events()[0]["observed_at"], STARTED)

    def test_09_event_failure_rolls_back_both_updates_and_concurrency_has_one_winner(self):
        before = self.runtime.start_state()
        with mock.patch.object(
            self.runtime.store,
            "_insert_attempt_state_event",
            side_effect=RuntimeError("event failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "event failure"):
                self.runtime.start()
        self.assertEqual(self.runtime.start_state(), before)

        barrier = threading.Barrier(2)

        def start(number):
            barrier.wait()
            try:
                return self.runtime.start(
                    handle=f"provider-job-{number}", key=f"concurrent-start-{number}"
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(start, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.start_events()), 1)

    def test_10_restart_preserves_running_identity_and_exact_replay_without_duplication(self):
        first = self.runtime.start()
        reopened = OperationalStateStore(self.runtime.config)
        self.assertEqual(reopened.health().schema_version, 5)
        replay = reopened.start_attempt_execution(
            "attempt-1", 1, 5, HANDLE, EXPECTED, START_REASON,
            "execution-start-1", ACTOR, AFTER_EXPIRY,
        )
        self.assertEqual(replay, first)
        attempt = reopened.snapshot("Attempt", "attempt-1")
        packet = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((attempt["state"], attempt["execution_handle"], attempt["version"]), ("Running", HANDLE, 2))
        self.assertEqual((packet["state"], packet["version"]), ("Running", 6))
        self.assertEqual(len(self.runtime.start_events()), 1)

    def test_11_independent_fingerprint_and_event_envelope_match_every_field(self):
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        result = self.runtime.start(actor=actor)
        documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 1,
                "correlation_id": "correlation-1",
            },
            "operation": "start_attempt_execution",
            "payload": {
                "attempt_id": "attempt-1",
                "execution_handle": HANDLE,
                "expected_attempt_version": 1,
                "expected_packet_version": 5,
                "expected_result": EXPECTED,
                "reason": START_REASON,
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event = self.runtime.start_events()[0]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            (event["entity_type"], event["entity_id"], event["event_type"]),
            ("Attempt", "attempt-1", "AttemptStateChanged"),
        )
        self.assertEqual(
            event["before_json"],
            {
                "attempt": state_payload("Attempt", "attempt-1", "Planned", 1),
                "packet": state_payload("Packet", "packet-1", "Leased", 5),
            },
        )
        self.assertEqual(event["after_json"], result)
        self.assertEqual(json.loads(event["reason"]), START_REASON)
        self.assertEqual(
            (
                event["actor_type"], event["actor_id"], event["correlation_id"],
                event["causation_event_id"], event["observed_at"],
            ),
            ("MaestroDeveloper", "developer-1", "correlation-1", 1, STARTED),
        )


if __name__ == "__main__":
    unittest.main()
