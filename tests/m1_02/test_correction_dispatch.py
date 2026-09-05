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
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    ResourceConflict,
    StaleState,
)
from test_assignment_claim import ACTOR, COMMIT, RESOURCES, state_payload
from test_review_control_routing import (
    HEAD_COMMIT,
    ReviewRoutingDatabase,
    build_finding,
    build_review,
)


DISPATCH_AT = "2026-09-04T16:00:00.000000Z"
DISPATCH_LEASE_EXPIRY = "2026-09-04T17:00:00.000000Z"
DISPATCH_REASON = {
    "kind": "reason",
    "reason_code": "CORRECTION_DISPATCHED",
    "detail_reference": None,
}
CORRECTION_LEASE = {
    "executor_route": "codex-cloud/developer-2",
    "expires_at": DISPATCH_LEASE_EXPIRY,
    "holder_id": "developer-2",
    "lease_id": "lease-2",
    "worktree_path": "/runtime/worktree-2",
}
CORRECTION_LOCKS = [
    {"lock_id": "lock-correction-z", "lock_kind": "FiniteResource", "resource_key": RESOURCES[0]},
    {"lock_id": "lock-correction-a", "lock_kind": "Path", "resource_key": RESOURCES[1]},
    {"lock_id": "lock-correction-m", "lock_kind": "SharedBoundary", "resource_key": RESOURCES[2]},
]
CORRECTION_ATTEMPT = {
    "attempt_id": "attempt-2",
    "model_identity": "gpt-5.7",
    "runtime_identity": "codex-runtime-2",
}


def expected_dispatch_result(
    packet_id="packet-1", lease_id="lease-2", attempt_id="attempt-2",
    locks=CORRECTION_LOCKS, packet_version=10,
):
    lock_ids = sorted(item["lock_id"] for item in locks)
    return {
        "attempt": state_payload("Attempt", attempt_id, "Planned", 1),
        "claim": {
            "kind": "claim",
            "lease_id": lease_id,
            "lock_ids": lock_ids,
            "packet_id": packet_id,
        },
        "lease": state_payload("Lease", lease_id, "Active", 1),
        "locks": [state_payload("ResourceLock", lock_id, "Active", 1) for lock_id in lock_ids],
        "packet": state_payload("Packet", packet_id, "Leased", packet_version),
    }


class CorrectionDispatchDatabase(ReviewRoutingDatabase):
    def __init__(self, findings=None):
        super().__init__()
        self.integration_review = self.route(
            review=build_review(result="ValidateOnly"),
            expected_version=7,
            key="prep-integration-validate-only",
        )
        self.review_id = "review-request-changes"
        if findings is None:
            findings = (build_finding(),)
        self.routed = self.route(
            review=build_review(
                review_id=self.review_id,
                review_kind="IndependentImplementation",
                reviewer_role="IndependentImplementationReviewer",
                reviewer_instance="independent-reviewer-1",
                result="RequestChanges",
                findings_json=findings,
            ),
            expected_version=8,
            key="prep-request-changes",
        )

    def dispatch(
        self, *,
        packet_id="packet-1",
        version=9,
        review_id=None,
        lease=CORRECTION_LEASE,
        locks=CORRECTION_LOCKS,
        attempt=CORRECTION_ATTEMPT,
        reason=DISPATCH_REASON,
        key="dispatch-1",
        actor=ACTOR,
        now=DISPATCH_AT,
    ):
        review_id = self.review_id if review_id is None else review_id
        return self.store.record_and_dispatch_correction(
            packet_id, version, review_id, lease, locks, attempt, reason, key, actor, now,
        )

    def dispatch_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "PacketClaimed"
        ]

    def dispatch_state(self):
        return {
            "packet": self.store.snapshot("Packet", "packet-1"),
            "leases": self.rows("leases"),
            "locks": self.rows("resource_locks"),
            "attempts": self.rows("attempts"),
            "events": self.dispatch_events(),
        }

    def insert_correction_attempt(self, attempt_id, packet_id, lease_id, review_id):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO attempts(attempt_id,packet_id,lease_id,attempt_number,attempt_kind,"
                "executor_class,model_identity,runtime_identity,state,result_commit,"
                "correction_for_review_id,started_at,finished_at,created_at,updated_at,version) "
                "VALUES (?,?,?,2,'TargetedCorrection','codex-cloud','model','runtime','Planned',"
                "NULL,?,NULL,NULL,?,?,1)",
                (attempt_id, packet_id, lease_id, review_id, DISPATCH_AT, DISPATCH_AT),
            )
            connection.commit()


class CorrectionDispatchTests(unittest.TestCase):
    def setUp(self):
        self.runtime = CorrectionDispatchDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self, findings=None):
        self.runtime.close()
        self.runtime = CorrectionDispatchDatabase(findings)

    def assert_no_dispatch_mutation(self, before):
        self.assertEqual(self.runtime.dispatch_state(), before)

    def test_01_awaitingarchitect_with_correctnow_finding_transitions_to_leased(self):
        result = self.runtime.dispatch()
        self.assertEqual(result, expected_dispatch_result())
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual(
            (packet["state"], packet["version"], packet["correction_count"], packet["updated_at"]),
            ("Leased", 10, 1, DISPATCH_AT),
        )
        self.assertEqual(len(self.runtime.rows("leases")), 2)
        self.assertEqual(len(self.runtime.rows("resource_locks")), 6)
        self.assertEqual(len(self.runtime.rows("attempts")), 2)
        events = self.runtime.dispatch_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[-1]["after_json"], result)
        self.assertEqual(events[-1]["event_type"], "PacketClaimed")
        attempt = self.runtime.store.snapshot("Attempt", "attempt-2")
        self.assertEqual(
            (attempt["attempt_number"], attempt["attempt_kind"], attempt["correction_for_review_id"]),
            (2, "TargetedCorrection", self.runtime.review_id),
        )

    def test_02_every_other_source_state_raises_invalid_transition(self):
        states = (
            "Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Leased", "Running",
            "AwaitingIntegration", "AwaitingReview", "MergeReady",
            "AwaitingOwner", "Merged", "Complete", "NeedsReplan", "Cancelled",
        )
        for state in states:
            with self.subTest(state=state):
                with closing(sqlite3.connect(self.runtime.database)) as connection:
                    connection.execute(
                        "UPDATE packets SET state=? WHERE packet_id='packet-1'", (state,)
                    )
                    connection.commit()
                with self.assertRaises(InvalidTransition):
                    self.runtime.dispatch(key=f"other-state-{state}")
        self.assertEqual(len(self.runtime.dispatch_events()), 1)

    def test_03_correction_already_used_rejects(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET correction_count=1 WHERE packet_id='packet-1'"
            )
            connection.commit()
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(InvalidRecord, "already used"):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

    def test_04_review_lookup_guards_reject(self):
        self.runtime.add_packet("packet-2", "work-2", [])
        before = self.runtime.dispatch_state()

        with self.assertRaises(InvalidRecord):
            self.runtime.dispatch(review_id="review-missing", key="lookup-missing")
        self.assert_no_dispatch_mutation(before)

        self.runtime.store.record_review(
            {
                "review_id": "review-wrong-packet",
                "packet_id": "packet-2",
                "attempt_id": None,
                "review_kind": "IndependentImplementation",
                "reviewer_role": "IndependentImplementationReviewer",
                "reviewer_instance": "independent-reviewer-2",
                "base_commit": COMMIT,
                "head_commit": HEAD_COMMIT,
                "result": "RequestChanges",
                "findings_json": [build_finding()],
                "coverage_json": {},
                "correction_number": 0,
                "created_at": DISPATCH_AT,
            },
            "seed-review-wrong-packet", ACTOR, DISPATCH_AT,
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.dispatch(review_id="review-wrong-packet", key="lookup-wrong-packet")
        self.assert_no_dispatch_mutation(before)

        self.runtime.store.record_review(
            {
                "review_id": "review-wrong-kind",
                "packet_id": "packet-1",
                "attempt_id": None,
                "review_kind": "Integration",
                "reviewer_role": "IntegrationAgent",
                "reviewer_instance": "integration-reviewer-9",
                "base_commit": COMMIT,
                "head_commit": HEAD_COMMIT,
                "result": "RequestChanges",
                "findings_json": [build_finding()],
                "coverage_json": {},
                "correction_number": 0,
                "created_at": DISPATCH_AT,
            },
            "seed-review-wrong-kind", ACTOR, DISPATCH_AT,
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.dispatch(review_id="review-wrong-kind", key="lookup-wrong-kind")
        self.assert_no_dispatch_mutation(before)

        self.runtime.store.record_review(
            {
                "review_id": "review-wrong-result",
                "packet_id": "packet-1",
                "attempt_id": None,
                "review_kind": "IndependentImplementation",
                "reviewer_role": "IndependentImplementationReviewer",
                "reviewer_instance": "independent-reviewer-result-mismatch",
                "base_commit": COMMIT,
                "head_commit": HEAD_COMMIT,
                "result": "Approve",
                "findings_json": [],
                "coverage_json": {},
                "correction_number": 0,
                "created_at": DISPATCH_AT,
            },
            "seed-review-wrong-result", ACTOR, DISPATCH_AT,
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.dispatch(review_id="review-wrong-result", key="lookup-wrong-result")
        self.assert_no_dispatch_mutation(before)

        self.runtime.store.record_review(
            {
                "review_id": "review-wrong-correction-number",
                "packet_id": "packet-1",
                "attempt_id": None,
                "review_kind": "IndependentImplementation",
                "reviewer_role": "IndependentImplementationReviewer",
                "reviewer_instance": "independent-reviewer-correction-mismatch",
                "base_commit": COMMIT,
                "head_commit": HEAD_COMMIT,
                "result": "RequestChanges",
                "findings_json": [build_finding()],
                "coverage_json": {},
                "correction_number": 1,
                "created_at": DISPATCH_AT,
            },
            "seed-review-wrong-correction-number", ACTOR, DISPATCH_AT,
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.dispatch(
                review_id="review-wrong-correction-number", key="lookup-wrong-correction"
            )
        self.assert_no_dispatch_mutation(before)

        result = self.runtime.dispatch()
        self.assertEqual(result["packet"]["state"], "Leased")

    def test_05_disposition_guards_reject(self):
        self.replace_runtime(
            findings=(
                build_finding(reason_code="AcceptKnownLimitation", detail_reference="detail-1"),
            )
        )
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(InvalidRecord, "no CorrectNow"):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

        self.replace_runtime(
            findings=(
                build_finding(finding_id="finding-correct", reason_code="CorrectNow"),
                build_finding(finding_id="finding-return", reason_code="ReturnSlice"),
            )
        )
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(InvalidRecord, "ReturnSlice"):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

        self.replace_runtime(
            findings=(
                build_finding(finding_id="finding-correct", reason_code="CorrectNow"),
                build_finding(
                    finding_id="finding-accept", reason_code="AcceptKnownLimitation",
                    detail_reference="detail-1",
                ),
            )
        )
        result = self.runtime.dispatch()
        self.assertEqual(result["packet"]["state"], "Leased")

        self.replace_runtime(
            findings=(
                build_finding(finding_id="finding-correct", reason_code="CorrectNow"),
                build_finding(finding_id="finding-reject", reason_code="RejectFinding"),
            )
        )
        result = self.runtime.dispatch()
        self.assertEqual(result["packet"]["state"], "Leased")

    def test_06_run_not_running_raises_invalid_transition(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute("UPDATE runs SET state='Blocked' WHERE run_id='run-1'")
            connection.commit()
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(InvalidTransition, "Running run"):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

    def test_07_resource_claim_mismatch_rejects(self):
        before = self.runtime.dispatch_state()
        cases = (
            CORRECTION_LOCKS[:-1],
            CORRECTION_LOCKS + [
                {"lock_id": "lock-extra", "lock_kind": "Path", "resource_key": "zz:extra"}
            ],
            [{**CORRECTION_LOCKS[0], "resource_key": "finite:other"}, *CORRECTION_LOCKS[1:]],
        )
        for number, locks in enumerate(cases, 1):
            with self.subTest(case=number):
                with self.assertRaisesRegex(InvalidRecord, "exactly cover"):
                    self.runtime.dispatch(locks=locks, key=f"mismatch-{number}")
        self.assert_no_dispatch_mutation(before)

    def test_08_duplicate_ids_reject(self):
        cases = ("lease-id", "claim-key", "lock-id", "attempt-id", "correction-attempt")
        for case in cases:
            with self.subTest(case=case):
                self.replace_runtime()
                self.runtime.add_packet("packet-2", "work-2", [])
                if case in {"lease-id", "claim-key"}:
                    self.runtime.insert_lease(
                        "lease-2" if case == "lease-id" else "lease-existing",
                        "packet-2",
                        "/runtime/other",
                        state="Released",
                        claim_key=f"dup-{case}" if case == "claim-key" else None,
                    )
                elif case == "lock-id":
                    self.runtime.insert_lease(
                        "lease-existing", "packet-2", "/runtime/other", state="Released"
                    )
                    self.runtime.insert_lock(
                        "lock-correction-a", "old:resource", "lease-existing", "packet-2",
                        state="Released",
                    )
                elif case == "attempt-id":
                    self.runtime.insert_lease(
                        "lease-existing", "packet-2", "/runtime/other", state="Released"
                    )
                    self.runtime.insert_attempt("attempt-2", "packet-2", "lease-existing")
                else:
                    self.runtime.insert_lease(
                        "lease-existing-corr", "packet-1", "/runtime/existing-corr",
                        state="Released",
                    )
                    self.runtime.insert_correction_attempt(
                        "attempt-existing-2", "packet-1", "lease-existing-corr",
                        self.runtime.review_id,
                    )
                before = self.runtime.dispatch_state()
                with self.assertRaises(InvalidRecord):
                    self.runtime.dispatch(key=f"dup-{case}")
                self.assert_no_dispatch_mutation(before)

    def test_09_active_lease_or_worktree_conflict_raises_resource_conflict(self):
        self.runtime.insert_lease("lease-active-packet", "packet-1", "/runtime/other-active")
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(ResourceConflict, "packet"):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

        self.replace_runtime()
        self.runtime.add_packet("packet-2", "work-2", [])
        self.runtime.insert_lease(
            "lease-active-worktree", "packet-2", CORRECTION_LEASE["worktree_path"]
        )
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(ResourceConflict, "worktree"):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

    def test_10_active_resource_lock_conflict_raises_resource_conflict(self):
        self.runtime.add_packet("packet-2", "work-2", [])
        self.runtime.insert_lease("lease-other-active", "packet-2", "/runtime/other-active")
        self.runtime.insert_lock(
            "lock-other-active", RESOURCES[2], "lease-other-active", "packet-2",
        )
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(ResourceConflict, RESOURCES[2]):
            self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

    def test_11_fingerprint_replay_rollback_concurrency_and_restart_reconstruct_exactly(self):
        # Reviewer-suggested explicit StaleState (version-mismatch) sub-case.
        before = self.runtime.dispatch_state()
        with self.assertRaisesRegex(StaleState, "stale"):
            self.runtime.dispatch(version=999, key="stale-standalone")
        self.assert_no_dispatch_mutation(before)

        # Replay: identical facts under the same key return the identical result.
        first = self.runtime.dispatch()
        replay = self.runtime.dispatch(now="2026-09-04T16:30:00.000000Z")
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.dispatch_events()), 2)
        dispatch_event = self.runtime.dispatch_events()[-1]
        self.assertEqual(dispatch_event["observed_at"], DISPATCH_AT)

        # Exact fingerprint and event envelope match.
        documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": None,
                "correlation_id": "correlation-1",
            },
            "operation": "record_and_dispatch_correction",
            "payload": {
                "attempt": CORRECTION_ATTEMPT,
                "expected_packet_version": 9,
                "lease": CORRECTION_LEASE,
                "locks": CORRECTION_LOCKS,
                "packet_id": "packet-1",
                "reason": DISPATCH_REASON,
                "review_id": self.runtime.review_id,
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        self.assertEqual(
            dispatch_event["command_fingerprint"], hashlib.sha256(encoded).hexdigest()
        )
        self.assertEqual(dispatch_event["entity_type"], "Packet")
        self.assertEqual(dispatch_event["entity_id"], "packet-1")
        self.assertEqual(dispatch_event["event_type"], "PacketClaimed")
        self.assertEqual(
            dispatch_event["before_json"],
            state_payload("Packet", "packet-1", "AwaitingArchitect", 9),
        )
        self.assertEqual(dispatch_event["after_json"], first)
        self.assertEqual(json.loads(dispatch_event["reason"]), DISPATCH_REASON)

        # A changed fact under the same key conflicts rather than replaying.
        with self.assertRaises(IdempotencyConflict):
            self.runtime.dispatch(attempt={**CORRECTION_ATTEMPT, "attempt_id": "other"})
        self.assertEqual(len(self.runtime.dispatch_events()), 2)

        # A write-step failure at each stage rolls back the entire transaction.
        for table in ("leases", "resource_locks", "attempts"):
            with self.subTest(table=table):
                self.replace_runtime()
                before = self.runtime.dispatch_state()
                original = self.runtime.store._insert

                def failing_insert(connection, candidate_table, row, _table=table):
                    if candidate_table == _table:
                        raise RuntimeError(f"failure at {_table}")
                    return original(connection, candidate_table, row)

                with mock.patch.object(
                    self.runtime.store, "_insert", side_effect=failing_insert
                ):
                    with self.assertRaisesRegex(RuntimeError, f"failure at {table}"):
                        self.runtime.dispatch()
                self.assert_no_dispatch_mutation(before)

        self.replace_runtime()
        before = self.runtime.dispatch_state()
        with mock.patch.object(
            self.runtime.store, "_insert_packet_claim_event",
            side_effect=RuntimeError("event failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "event failure"):
                self.runtime.dispatch()
        self.assert_no_dispatch_mutation(before)

        # Concurrency: exactly one concurrent caller wins the shared packet update.
        self.replace_runtime()
        barrier = threading.Barrier(2)

        def race(number):
            barrier.wait()
            try:
                return self.runtime.dispatch(
                    lease={
                        **CORRECTION_LEASE,
                        "lease_id": f"lease-race-{number}",
                        "worktree_path": f"/runtime/race-{number}",
                    },
                    locks=[
                        {**item, "lock_id": f"{item['lock_id']}-race-{number}"}
                        for item in CORRECTION_LOCKS
                    ],
                    attempt={**CORRECTION_ATTEMPT, "attempt_id": f"attempt-race-{number}"},
                    key=f"race-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(race, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.dispatch_events()), 2)

        # Restart: re-invoking with the same idempotency_key reconstructs the same result.
        self.replace_runtime()
        first_after_restart_setup = self.runtime.dispatch()
        reopened = OperationalStateStore(self.runtime.config)
        reopened.health()
        replay_after_restart = reopened.record_and_dispatch_correction(
            "packet-1", 9, self.runtime.review_id, CORRECTION_LEASE, CORRECTION_LOCKS,
            CORRECTION_ATTEMPT, DISPATCH_REASON, "dispatch-1", ACTOR,
            "2026-09-04T18:00:00.000000Z",
        )
        self.assertEqual(replay_after_restart, first_after_restart_setup)
        self.assertEqual(len(self.runtime.dispatch_events()), 2)
        packet = reopened.snapshot("Packet", "packet-1")
        attempt = reopened.snapshot("Attempt", "attempt-2")
        self.assertEqual(packet["state"], "Leased")
        self.assertEqual((attempt["state"], attempt["started_at"]), ("Planned", None))


if __name__ == "__main__":
    unittest.main()
