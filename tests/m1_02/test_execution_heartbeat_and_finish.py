from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest import mock

from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    StaleState,
)
from test_assignment_claim import ACTOR, COMMIT, state_payload
from test_execution_start import (
    EXPECTED,
    HANDLE,
    STARTED,
    ExecutionDatabase,
)


HEARTBEAT_AT = "2026-09-04T12:45:00.000000Z"
FINISHED_AT = "2026-09-04T12:50:00.000000Z"
RENEWED_EXPIRY = "2026-09-04T14:00:00.000000Z"
FINISH_AFTER_RENEWAL = "2026-09-04T13:30:00.000000Z"
EXPIRED_AT = "2026-09-04T13:30:00.000000Z"
HEARTBEAT_REASON = {
    "kind": "reason",
    "reason_code": "EXECUTION_HEARTBEAT_OBSERVED",
    "detail_reference": None,
}
FINISH_REASON = {
    "kind": "reason",
    "reason_code": "EXECUTION_FINISHED",
    "detail_reference": None,
}
COMPLETION_REFERENCE = "evidence:worker-result-1"
OUTCOME_STATES = {
    "Succeeded": ("AwaitingIntegration", "Released", "Released"),
    "Failed": ("NeedsReplan", "Released", "Released"),
    "Cancelled": ("Cancelled", "Cancelled", "Released"),
    "TimedOut": ("NeedsReplan", "Expired", "Expired"),
    "Stale": ("NeedsReplan", "Released", "Released"),
}


def expected_heartbeat_result():
    return {
        "attempt": state_payload("Attempt", "attempt-1", "Running", 3),
        "execution": {
            "attempt_id": "attempt-1",
            "execution_handle": HANDLE,
            "heartbeat_at": HEARTBEAT_AT,
        },
        "lease": state_payload("Lease", "lease-1", "Active", 2),
        "renewal": {
            "expires_at": RENEWED_EXPIRY,
            "heartbeat_at": HEARTBEAT_AT,
            "lease_id": "lease-1",
        },
    }


def expected_finish_result(outcome, *, attempt_version=2, lease_version=1,
                           packet_version=6, finished_at=FINISHED_AT,
                           lock_ids=("lock-a", "lock-m", "lock-z")):
    packet_state, lease_state, lock_state = OUTCOME_STATES[outcome]
    result_commit = COMMIT if outcome == "Succeeded" else None
    return {
        "attempt": state_payload(
            "Attempt", "attempt-1", outcome, attempt_version + 1
        ),
        "completion": {
            "attempt_id": "attempt-1",
            "completion_evidence_reference": COMPLETION_REFERENCE,
            "execution_handle": HANDLE,
            "finished_at": finished_at,
            "result_commit": result_commit,
        },
        "lease": state_payload(
            "Lease", "lease-1", lease_state, lease_version + 1
        ),
        "locks": [
            state_payload("ResourceLock", lock_id, lock_state, 2)
            for lock_id in lock_ids
        ],
        "packet": state_payload(
            "Packet", "packet-1", packet_state, packet_version + 1
        ),
    }


class ExecutionLifecycleDatabase(ExecutionDatabase):
    def __init__(self):
        super().__init__()
        self.started = self.start()

    def heartbeat(
        self, *, attempt_id="attempt-1", attempt_version=2, lease_version=1,
        handle=HANDLE, new_expires_at=RENEWED_EXPIRY, reason=HEARTBEAT_REASON,
        key="execution-heartbeat-1", actor=ACTOR, now=HEARTBEAT_AT,
    ):
        return self.store.heartbeat_attempt_execution(
            attempt_id, attempt_version, lease_version, handle, new_expires_at,
            reason, key, actor, now,
        )

    def finish(
        self, *, attempt_id="attempt-1", attempt_version=2, packet_version=6,
        lease_version=1, handle=HANDLE, outcome="Succeeded",
        result_commit=COMMIT, completion_reference=COMPLETION_REFERENCE,
        reason=FINISH_REASON, key="execution-finish-1", actor=ACTOR,
        now=FINISHED_AT,
    ):
        return self.store.finish_attempt_execution(
            attempt_id, attempt_version, packet_version, lease_version, handle,
            outcome, result_commit, completion_reference, reason, key, actor, now,
        )

    def heartbeat_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "LeaseHeartbeatRecorded"
        ]

    def finish_events(self):
        terminal = set(OUTCOME_STATES)
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "AttemptStateChanged"
            and event["after_json"].get("attempt", {}).get("state") in terminal
        ]

    def lifecycle_state(self):
        return {
            "attempts": self.rows("attempts"),
            "packets": self.rows("packets"),
            "leases": self.rows("leases"),
            "locks": self.rows("resource_locks"),
            "events": self.store.events_after(0, 1000),
        }


class ExecutionHeartbeatAndFinishTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ExecutionLifecycleDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self):
        self.runtime.close()
        self.runtime = ExecutionLifecycleDatabase()

    def test_01_valid_heartbeat_returns_exact_result_and_renews_only_attempt_and_lease(self):
        packet_before = self.runtime.rows("packets")
        run_before = self.runtime.rows("runs")
        locks_before = self.runtime.rows("resource_locks")
        result = self.runtime.heartbeat()
        self.assertEqual(result, expected_heartbeat_result())
        attempt = self.runtime.store.snapshot("Attempt", "attempt-1")
        lease = self.runtime.store.snapshot("Lease", "lease-1")
        self.assertEqual(
            (attempt["state"], attempt["heartbeat_at"], attempt["updated_at"], attempt["version"]),
            ("Running", HEARTBEAT_AT, HEARTBEAT_AT, 3),
        )
        self.assertEqual(
            (lease["state"], lease["expires_at"], lease["heartbeat_at"], lease["version"]),
            ("Active", RENEWED_EXPIRY, HEARTBEAT_AT, 2),
        )
        self.assertEqual(self.runtime.rows("packets"), packet_before)
        self.assertEqual(self.runtime.rows("runs"), run_before)
        self.assertEqual(self.runtime.rows("resource_locks"), locks_before)
        self.assertEqual(len(self.runtime.heartbeat_events()), 1)

    def test_02_heartbeat_wrong_handle_missing_relationships_wrong_states_or_stopped_run_blocks(self):
        cases = (
            "wrong-handle", "missing-attempt", "missing-packet", "missing-lease",
            "mismatched-lease", "missing-run", "attempt-terminal", "packet-ready",
            "lease-released", "run-blocked", "run-complete", "run-cancelled",
        )
        for case in cases:
            with self.subTest(case=case):
                self.replace_runtime()
                attempt_id, attempt_version, lease_version, handle = "attempt-1", 2, 1, HANDLE
                if case == "wrong-handle":
                    handle = "other-handle"
                elif case == "missing-attempt":
                    attempt_id = "missing"
                elif case == "missing-packet":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM packets WHERE packet_id='packet-1'")
                        connection.commit()
                elif case == "missing-lease":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM leases WHERE lease_id='lease-1'")
                        connection.commit()
                elif case == "mismatched-lease":
                    self.runtime.add_packet("packet-2", "work-2", [])
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE leases SET packet_id='packet-2' WHERE lease_id='lease-1'")
                        connection.commit()
                elif case == "missing-run":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM runs WHERE run_id='run-1'")
                        connection.commit()
                elif case == "attempt-terminal":
                    self.runtime.finish(outcome="Failed", result_commit=None)
                    attempt_version, lease_version = 3, 2
                elif case == "packet-ready":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE packets SET state='Ready' WHERE packet_id='packet-1'")
                        connection.commit()
                elif case == "lease-released":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute(
                            "UPDATE leases SET state='Released',released_at=? WHERE lease_id='lease-1'",
                            (FINISHED_AT,),
                        )
                        connection.commit()
                else:
                    run_state = case.removeprefix("run-").capitalize()
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute(
                            "UPDATE runs SET state=? WHERE run_id='run-1'", (run_state,)
                        )
                        connection.commit()
                before = self.runtime.lifecycle_state()
                error = StaleState if case == "wrong-handle" else (
                    InvalidRecord if case in {
                        "missing-attempt", "missing-packet", "missing-lease",
                        "mismatched-lease", "missing-run",
                    }
                    else InvalidTransition
                )
                with self.assertRaises(error):
                    self.runtime.heartbeat(
                        attempt_id=attempt_id, attempt_version=attempt_version,
                        lease_version=lease_version, handle=handle,
                        key=f"heartbeat-blocked-{case}",
                    )
                self.assertEqual(self.runtime.lifecycle_state(), before)

    def test_03_heartbeat_stale_versions_and_nonmonotonic_or_invalid_expiry_block(self):
        commands = (
            (InvalidRecord, lambda: self.runtime.heartbeat(attempt_id="")),
            (InvalidRecord, lambda: self.runtime.heartbeat(attempt_version=False)),
            (InvalidRecord, lambda: self.runtime.heartbeat(lease_version=0)),
            (InvalidRecord, lambda: self.runtime.heartbeat(handle="")),
            (InvalidRecord, lambda: self.runtime.heartbeat(
                reason=state_payload("Attempt", "attempt-1", "Running", 2)
            )),
            (InvalidRecord, lambda: self.runtime.heartbeat(key="")),
            (InvalidRecord, lambda: self.runtime.heartbeat(actor={"actor_type": "x"})),
            (InvalidRecord, lambda: self.runtime.heartbeat(now="later")),
            (StaleState, lambda: self.runtime.heartbeat(attempt_version=3)),
            (StaleState, lambda: self.runtime.heartbeat(lease_version=2, key="stale-lease")),
            (InvalidRecord, lambda: self.runtime.heartbeat(new_expires_at="later", key="bad-expiry")),
            (InvalidTransition, lambda: self.runtime.heartbeat(now=STARTED, key="same-heartbeat")),
            (InvalidTransition, lambda: self.runtime.heartbeat(
                new_expires_at="2026-09-04T12:55:00.000000Z", key="old-expiry"
            )),
            (InvalidTransition, lambda: self.runtime.heartbeat(
                new_expires_at=HEARTBEAT_AT, key="expiry-not-after-now"
            )),
        )
        for error, command in commands:
            before = self.runtime.lifecycle_state()
            with self.assertRaises(error):
                command()
            self.assertEqual(self.runtime.lifecycle_state(), before)

    def test_04_heartbeat_replay_and_changed_fact_conflict_are_exact(self):
        first = self.runtime.heartbeat(key="heartbeat-immutable")
        replay = self.runtime.heartbeat(
            key="heartbeat-immutable", now="2026-09-04T15:00:00.000000Z"
        )
        self.assertEqual(replay, first)
        changed = (
            lambda: self.runtime.heartbeat(key="heartbeat-immutable", attempt_id="other"),
            lambda: self.runtime.heartbeat(key="heartbeat-immutable", attempt_version=3),
            lambda: self.runtime.heartbeat(key="heartbeat-immutable", lease_version=2),
            lambda: self.runtime.heartbeat(key="heartbeat-immutable", handle="other"),
            lambda: self.runtime.heartbeat(
                key="heartbeat-immutable", new_expires_at="2026-09-04T15:00:00.000000Z"
            ),
            lambda: self.runtime.heartbeat(
                key="heartbeat-immutable", reason={**HEARTBEAT_REASON, "reason_code": "OTHER"}
            ),
            lambda: self.runtime.heartbeat(
                key="heartbeat-immutable", actor=Actor("Other", "developer-1", "correlation-1")
            ),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.heartbeat_events()), 1)
        self.assertEqual(self.runtime.heartbeat_events()[0]["observed_at"], HEARTBEAT_AT)

    def test_05_heartbeat_event_failure_and_concurrency_cannot_partially_renew(self):
        before = self.runtime.lifecycle_state()
        with mock.patch.object(
            self.runtime.store,
            "_insert_lease_heartbeat_event",
            side_effect=RuntimeError("heartbeat event failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "heartbeat event failure"):
                self.runtime.heartbeat()
        self.assertEqual(self.runtime.lifecycle_state(), before)

        barrier = threading.Barrier(2)

        def heartbeat(number):
            barrier.wait()
            try:
                return self.runtime.heartbeat(
                    new_expires_at=f"2026-09-04T14:0{number}:00.000000Z",
                    key=f"concurrent-heartbeat-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(heartbeat, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.heartbeat_events()), 1)

    def test_06_each_finish_outcome_follows_the_closed_mapping_exactly(self):
        for outcome in OUTCOME_STATES:
            with self.subTest(outcome=outcome):
                self.replace_runtime()
                now = EXPIRED_AT if outcome == "TimedOut" else FINISHED_AT
                commit = COMMIT if outcome == "Succeeded" else None
                result = self.runtime.finish(
                    outcome=outcome, result_commit=commit, now=now,
                    key=f"finish-{outcome}",
                )
                self.assertEqual(
                    result, expected_finish_result(outcome, finished_at=now)
                )
                attempt = self.runtime.store.snapshot("Attempt", "attempt-1")
                packet = self.runtime.store.snapshot("Packet", "packet-1")
                lease = self.runtime.store.snapshot("Lease", "lease-1")
                packet_state, lease_state, lock_state = OUTCOME_STATES[outcome]
                self.assertEqual(
                    (
                        attempt["state"], attempt["result_commit"], attempt["finished_at"],
                        attempt["completion_evidence_reference"], attempt["version"],
                    ),
                    (outcome, commit, now, COMPLETION_REFERENCE, 3),
                )
                self.assertEqual((packet["state"], packet["version"]), (packet_state, 7))
                self.assertEqual(
                    (lease["state"], lease["released_at"], lease["version"]),
                    (lease_state, now, 2),
                )
                self.assertEqual(
                    [(row["state"], row["released_at"], row["version"]) for row in self.runtime.rows("resource_locks")],
                    [(lock_state, now, 2)] * 3,
                )
                self.assertEqual(len(self.runtime.finish_events()), 1)

    def test_07_success_requires_full_commit_and_other_outcomes_prohibit_one(self):
        commands = (
            lambda: self.runtime.finish(attempt_id=""),
            lambda: self.runtime.finish(attempt_version=False),
            lambda: self.runtime.finish(packet_version=0),
            lambda: self.runtime.finish(lease_version=False),
            lambda: self.runtime.finish(handle=""),
            lambda: self.runtime.finish(result_commit=None),
            lambda: self.runtime.finish(result_commit="abc"),
            lambda: self.runtime.finish(outcome="Failed", result_commit=COMMIT),
            lambda: self.runtime.finish(outcome="Unknown", result_commit=None),
            lambda: self.runtime.finish(completion_reference=""),
            lambda: self.runtime.finish(
                reason=state_payload("Attempt", "attempt-1", "Running", 2)
            ),
            lambda: self.runtime.finish(key=""),
            lambda: self.runtime.finish(actor={"actor_type": "x"}),
            lambda: self.runtime.finish(now="later"),
        )
        for command in commands:
            before = self.runtime.lifecycle_state()
            with self.assertRaises(InvalidRecord):
                command()
            self.assertEqual(self.runtime.lifecycle_state(), before)

    def test_08_finish_wrong_handle_missing_relationship_wrong_states_or_stopped_run_blocks(self):
        cases = (
            "wrong-handle", "missing-attempt", "missing-packet", "missing-lease",
            "mismatched-lease", "missing-run", "attempt-terminal", "packet-ready",
            "lease-released", "run-blocked", "run-complete", "run-cancelled",
        )
        for case in cases:
            with self.subTest(case=case):
                self.replace_runtime()
                attempt_id, attempt_version, packet_version, lease_version = "attempt-1", 2, 6, 1
                handle = HANDLE
                if case == "wrong-handle":
                    handle = "other-handle"
                elif case == "missing-attempt":
                    attempt_id = "missing"
                elif case == "missing-packet":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM packets WHERE packet_id='packet-1'")
                        connection.commit()
                elif case == "missing-lease":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM leases WHERE lease_id='lease-1'")
                        connection.commit()
                elif case == "mismatched-lease":
                    self.runtime.add_packet("packet-2", "work-2", [])
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE leases SET packet_id='packet-2' WHERE lease_id='lease-1'")
                        connection.commit()
                elif case == "missing-run":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("DELETE FROM runs WHERE run_id='run-1'")
                        connection.commit()
                elif case == "attempt-terminal":
                    self.runtime.finish(outcome="Failed", result_commit=None)
                    attempt_version, packet_version, lease_version = 3, 7, 2
                elif case == "packet-ready":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute("UPDATE packets SET state='Ready' WHERE packet_id='packet-1'")
                        connection.commit()
                elif case == "lease-released":
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute(
                            "UPDATE leases SET state='Released',released_at=? WHERE lease_id='lease-1'",
                            (FINISHED_AT,),
                        )
                        connection.commit()
                else:
                    run_state = case.removeprefix("run-").capitalize()
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute(
                            "UPDATE runs SET state=? WHERE run_id='run-1'", (run_state,)
                        )
                        connection.commit()
                before = self.runtime.lifecycle_state()
                error = StaleState if case == "wrong-handle" else (
                    InvalidRecord if case in {
                        "missing-attempt", "missing-packet", "missing-lease",
                        "mismatched-lease", "missing-run",
                    }
                    else InvalidTransition
                )
                with self.assertRaises(error):
                    self.runtime.finish(
                        attempt_id=attempt_id, attempt_version=attempt_version,
                        packet_version=packet_version, lease_version=lease_version,
                        handle=handle, key=f"finish-blocked-{case}",
                    )
                self.assertEqual(self.runtime.lifecycle_state(), before)

    def test_09_finish_stale_versions_and_outcome_time_rules_block(self):
        commands = (
            (StaleState, lambda: self.runtime.finish(attempt_version=3)),
            (StaleState, lambda: self.runtime.finish(packet_version=7, key="stale-packet")),
            (StaleState, lambda: self.runtime.finish(lease_version=2, key="stale-lease")),
            (InvalidTransition, lambda: self.runtime.finish(now=EXPIRED_AT, key="late-success")),
            (InvalidTransition, lambda: self.runtime.finish(
                outcome="TimedOut", result_commit=None,
                now="2026-09-04T13:00:00.000000Z", key="early-timeout",
            )),
        )
        for error, command in commands:
            before = self.runtime.lifecycle_state()
            with self.assertRaises(error):
                command()
            self.assertEqual(self.runtime.lifecycle_state(), before)
        self.replace_runtime()
        result = self.runtime.finish(now="2026-09-04T13:00:00.000000Z")
        self.assertEqual(result["attempt"]["state"], "Succeeded")

    def test_10_finish_closes_exact_active_lease_locks_in_sorted_order(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE resource_locks SET state='Released',released_at=?,version=2 "
                "WHERE lock_id='lock-m'",
                (HEARTBEAT_AT,),
            )
            connection.commit()
        result = self.runtime.finish()
        self.assertEqual(
            result["locks"],
            [
                state_payload("ResourceLock", "lock-a", "Released", 2),
                state_payload("ResourceLock", "lock-z", "Released", 2),
            ],
        )
        locks = {row["lock_id"]: row for row in self.runtime.rows("resource_locks")}
        self.assertEqual(
            (locks["lock-m"]["state"], locks["lock-m"]["released_at"], locks["lock-m"]["version"]),
            ("Released", HEARTBEAT_AT, 2),
        )
        self.assertEqual(
            [(locks[key]["state"], locks[key]["released_at"], locks[key]["version"]) for key in ("lock-a", "lock-z")],
            [("Released", FINISHED_AT, 2), ("Released", FINISHED_AT, 2)],
        )

    def test_11_finish_replay_and_changed_fact_conflict_are_exact(self):
        first = self.runtime.finish(key="finish-immutable")
        replay = self.runtime.finish(key="finish-immutable", now=EXPIRED_AT)
        self.assertEqual(replay, first)
        changed = (
            lambda: self.runtime.finish(key="finish-immutable", attempt_id="other"),
            lambda: self.runtime.finish(key="finish-immutable", attempt_version=3),
            lambda: self.runtime.finish(key="finish-immutable", packet_version=7),
            lambda: self.runtime.finish(key="finish-immutable", lease_version=2),
            lambda: self.runtime.finish(key="finish-immutable", handle="other"),
            lambda: self.runtime.finish(
                key="finish-immutable", outcome="Failed", result_commit=None
            ),
            lambda: self.runtime.finish(key="finish-immutable", result_commit="b" * 40),
            lambda: self.runtime.finish(key="finish-immutable", completion_reference="other"),
            lambda: self.runtime.finish(
                key="finish-immutable", reason={**FINISH_REASON, "reason_code": "OTHER"}
            ),
            lambda: self.runtime.finish(
                key="finish-immutable", actor=Actor("Other", "developer-1", "correlation-1")
            ),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.finish_events()), 1)
        self.assertEqual(self.runtime.finish_events()[0]["observed_at"], FINISHED_AT)

    def test_12_finish_event_failure_rolls_back_every_row_update(self):
        before = self.runtime.lifecycle_state()
        with mock.patch.object(
            self.runtime.store,
            "_insert_attempt_state_event",
            side_effect=RuntimeError("finish event failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "finish event failure"):
                self.runtime.finish()
        self.assertEqual(self.runtime.lifecycle_state(), before)

    def test_13_concurrent_finishes_have_one_winner_and_no_loser_residue(self):
        barrier = threading.Barrier(2)

        def finish(number):
            barrier.wait()
            try:
                if number == 1:
                    return self.runtime.finish(key="concurrent-success")
                return self.runtime.finish(
                    outcome="Failed", result_commit=None, key="concurrent-failure"
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(finish, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        winner = next(item for item in outcomes if isinstance(item, dict))
        self.assertEqual(len(self.runtime.finish_events()), 1)
        self.assertEqual(self.runtime.finish_events()[0]["after_json"], winner)
        self.assertEqual(
            self.runtime.store.snapshot("Attempt", "attempt-1")["state"],
            winner["attempt"]["state"],
        )

    def test_14_restart_preserves_terminal_state_and_replay_without_active_ownership(self):
        first = self.runtime.finish()
        reopened = OperationalStateStore(self.runtime.config)
        replay = reopened.finish_attempt_execution(
            "attempt-1", 2, 6, 1, HANDLE, "Succeeded", COMMIT,
            COMPLETION_REFERENCE, FINISH_REASON, "execution-finish-1", ACTOR,
            EXPIRED_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(reopened.snapshot("Attempt", "attempt-1")["state"], "Succeeded")
        self.assertEqual(reopened.snapshot("Packet", "packet-1")["state"], "AwaitingIntegration")
        self.assertEqual(reopened.snapshot("Lease", "lease-1")["state"], "Released")
        self.assertEqual(
            {row["state"] for row in self.runtime.rows("resource_locks")}, {"Released"}
        )
        self.assertEqual(len(self.runtime.finish_events()), 1)

    def test_15_independent_heartbeat_and_finish_fingerprints_and_events_are_exact(self):
        heartbeat_actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        heartbeat_result = self.runtime.heartbeat(actor=heartbeat_actor)
        heartbeat_documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 1,
                "correlation_id": "correlation-1",
            },
            "operation": "heartbeat_attempt_execution",
            "payload": {
                "attempt_id": "attempt-1",
                "execution_handle": HANDLE,
                "expected_attempt_version": 2,
                "expected_lease_version": 1,
                "new_expires_at": RENEWED_EXPIRY,
                "reason": HEARTBEAT_REASON,
            },
        }
        heartbeat_encoded = json.dumps(
            heartbeat_documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        heartbeat_event = self.runtime.heartbeat_events()[0]
        self.assertEqual(
            heartbeat_event["command_fingerprint"],
            hashlib.sha256(heartbeat_encoded).hexdigest(),
        )
        self.assertEqual(
            (
                heartbeat_event["entity_type"], heartbeat_event["entity_id"],
                heartbeat_event["event_type"], heartbeat_event["actor_type"],
                heartbeat_event["actor_id"], heartbeat_event["correlation_id"],
                heartbeat_event["causation_event_id"], heartbeat_event["observed_at"],
            ),
            (
                "Lease", "lease-1", "LeaseHeartbeatRecorded", "MaestroDeveloper",
                "developer-1", "correlation-1", 1, HEARTBEAT_AT,
            ),
        )
        self.assertEqual(
            heartbeat_event["before_json"],
            {
                "attempt": state_payload("Attempt", "attempt-1", "Running", 2),
                "execution": {
                    "attempt_id": "attempt-1",
                    "execution_handle": HANDLE,
                    "heartbeat_at": STARTED,
                },
                "lease": state_payload("Lease", "lease-1", "Active", 1),
                "renewal": {
                    "expires_at": "2026-09-04T13:00:00.000000Z",
                    "heartbeat_at": "2026-09-04T12:00:00.000000Z",
                    "lease_id": "lease-1",
                },
            },
        )
        self.assertEqual(heartbeat_event["after_json"], heartbeat_result)
        self.assertEqual(json.loads(heartbeat_event["reason"]), HEARTBEAT_REASON)

        finish_actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 2)
        finish_result = self.runtime.finish(
            attempt_version=3, lease_version=2, actor=finish_actor,
            now=FINISH_AFTER_RENEWAL, key="execution-finish-after-heartbeat",
        )
        finish_documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 2,
                "correlation_id": "correlation-1",
            },
            "operation": "finish_attempt_execution",
            "payload": {
                "attempt_id": "attempt-1",
                "completion_evidence_reference": COMPLETION_REFERENCE,
                "execution_handle": HANDLE,
                "expected_attempt_version": 3,
                "expected_lease_version": 2,
                "expected_packet_version": 6,
                "outcome": "Succeeded",
                "reason": FINISH_REASON,
                "result_commit": COMMIT,
            },
        }
        finish_encoded = json.dumps(
            finish_documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        finish_event = self.runtime.finish_events()[0]
        self.assertEqual(
            finish_event["command_fingerprint"], hashlib.sha256(finish_encoded).hexdigest()
        )
        self.assertEqual(
            (
                finish_event["entity_type"], finish_event["entity_id"],
                finish_event["event_type"], finish_event["actor_type"],
                finish_event["actor_id"], finish_event["correlation_id"],
                finish_event["causation_event_id"], finish_event["observed_at"],
            ),
            (
                "Attempt", "attempt-1", "AttemptStateChanged", "MaestroDeveloper",
                "developer-1", "correlation-1", 2, FINISH_AFTER_RENEWAL,
            ),
        )
        self.assertEqual(
            finish_event["before_json"],
            {
                "attempt": state_payload("Attempt", "attempt-1", "Running", 3),
                "execution": {
                    "attempt_id": "attempt-1",
                    "execution_handle": HANDLE,
                    "expected_result": EXPECTED,
                    "heartbeat_at": HEARTBEAT_AT,
                },
                "lease": state_payload("Lease", "lease-1", "Active", 2),
                "locks": [
                    state_payload("ResourceLock", lock_id, "Active", 1)
                    for lock_id in ("lock-a", "lock-m", "lock-z")
                ],
                "packet": state_payload("Packet", "packet-1", "Running", 6),
            },
        )
        self.assertEqual(finish_event["after_json"], finish_result)
        self.assertEqual(json.loads(finish_event["reason"]), FINISH_REASON)


if __name__ == "__main__":
    unittest.main()
