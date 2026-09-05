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
from test_assignment_claim import ACTOR, state_payload
from test_review_control_routing import (
    BASE_COMMIT,
    HEAD_COMMIT,
    ROUTE_AT,
    ReviewRoutingDatabase,
    build_review,
)


ACCEPT_AT = "2026-09-04T16:00:00.000000Z"
ACCEPT_REASON = {
    "kind": "reason",
    "reason_code": "PACKET_ACCEPTED",
    "detail_reference": None,
}
ACCEPTANCE_REASON_PAYLOAD = {
    "kind": "reason",
    "reason_code": "ACCEPTANCE_RECORDED",
    "detail_reference": None,
}
GOOD_REVIEW_ID = "review-approve-1"


def build_acceptance(
    *,
    acceptance_id="acceptance-1",
    subject_type="Packet",
    subject_id="packet-1",
    packet_id="packet-1",
    run_id=None,
    sequence_number=1,
    supersedes_acceptance_id=None,
    required_authority="ProjectArchitect",
    decision="Accepted",
    authority_reference="architect-1",
    exact_head=HEAD_COMMIT,
    review_id=GOOD_REVIEW_ID,
    review_coverage_json=None,
    reason_payload_json=None,
):
    coverage = (
        {"kind": "acceptance-review-coverage", "review_id": review_id}
        if review_coverage_json is None
        else review_coverage_json
    )
    reason = (
        dict(ACCEPTANCE_REASON_PAYLOAD)
        if reason_payload_json is None
        else reason_payload_json
    )
    return {
        "acceptance_id": acceptance_id,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "packet_id": packet_id,
        "run_id": run_id,
        "sequence_number": sequence_number,
        "supersedes_acceptance_id": supersedes_acceptance_id,
        "required_authority": required_authority,
        "decision": decision,
        "authority_reference": authority_reference,
        "exact_head": exact_head,
        "review_coverage_json": coverage,
        "reason_payload_json": reason,
    }


def build_extra_review(
    *,
    review_id,
    packet_id="packet-1",
    review_kind="IndependentImplementation",
    reviewer_role="IndependentImplementationReviewer",
    reviewer_instance="independent-reviewer-extra",
    head_commit=HEAD_COMMIT,
    result="Approve",
    findings_json=None,
    correction_number=0,
    created_at=ROUTE_AT,
):
    if findings_json is None:
        findings_json = [] if result in ("Approve", "ValidateOnly") else [
            {
                "kind": "review-finding",
                "finding_id": "finding-extra",
                "criterion_reference": "M0-D05#acceptance",
                "evidence": {
                    "kind": "evidence-reference",
                    "evidence_id": "evidence-extra",
                    "digest": "0" * 64,
                    "source_reference": None,
                },
                "disposition": {
                    "kind": "reason", "reason_code": "CorrectNow",
                    "detail_reference": None,
                },
            }
        ]
    return {
        "review_id": review_id,
        "packet_id": packet_id,
        "attempt_id": None,
        "review_kind": review_kind,
        "reviewer_role": reviewer_role,
        "reviewer_instance": reviewer_instance,
        "base_commit": BASE_COMMIT,
        "head_commit": head_commit,
        "result": result,
        "findings_json": findings_json,
        "coverage_json": {},
        "correction_number": correction_number,
        "created_at": created_at,
    }


class AcceptanceRoutingDatabase(ReviewRoutingDatabase):
    def __init__(self):
        super().__init__()
        self.route(
            review=build_review(result="ValidateOnly"),
            expected_version=7,
            key="prep-integration-validate-only",
        )
        self.route(
            review=build_review(
                review_id=GOOD_REVIEW_ID,
                review_kind="IndependentImplementation",
                reviewer_role="IndependentImplementationReviewer",
                reviewer_instance="independent-reviewer-1",
                result="Approve",
            ),
            expected_version=8,
            key="prep-independent-approve",
        )

    def accept(
        self,
        *,
        packet_id="packet-1",
        expected_version=9,
        acceptance,
        reason=None,
        key="accept-1",
        actor=ACTOR,
        now=ACCEPT_AT,
    ):
        return self.store.record_and_accept_packet(
            packet_id, expected_version, acceptance,
            dict(ACCEPT_REASON) if reason is None else reason,
            key, actor, now,
        )

    def accept_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "AcceptanceRecorded"
        ]

    def accept_state(self):
        return {
            "packets": self.rows("packets"),
            "acceptance_records": self.rows("acceptance_records"),
            "events": self.store.events_after(0, 1000),
        }


class AcceptanceRoutingTests(unittest.TestCase):
    def setUp(self):
        self.runtime = AcceptanceRoutingDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self):
        self.runtime.close()
        self.runtime = AcceptanceRoutingDatabase()

    def test_01_mergeready_accepted_transitions_to_awaiting_owner(self):
        acceptance = build_acceptance()
        result = self.runtime.accept(acceptance=acceptance, key="accept-good")
        self.assertEqual(
            result["packet"], state_payload("Packet", "packet-1", "AwaitingOwner", 10)
        )
        self.assertEqual(result["acceptance"]["decision"], "Accepted")
        self.assertEqual(result["acceptance"]["acceptance_id"], "acceptance-1")
        self.assertEqual(result["acceptance"]["created_at"], ACCEPT_AT)
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((packet["state"], packet["version"]), ("AwaitingOwner", 10))
        stored = self.runtime.store.snapshot("Acceptance", "acceptance-1")
        self.assertEqual(stored, result["acceptance"])
        events = self.runtime.accept_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["after_json"], result)
        self.assertEqual(
            events[0]["before_json"],
            {"packet": state_payload("Packet", "packet-1", "MergeReady", 9)},
        )

    def test_02_every_other_source_state_raises_invalid_transition(self):
        states = (
            "Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Leased", "Running",
            "AwaitingIntegration", "AwaitingReview", "AwaitingArchitect",
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
                    self.runtime.accept(
                        acceptance=build_acceptance(), key=f"outside-{state}",
                    )
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='MergeReady' WHERE packet_id='packet-1'"
            )
            connection.commit()

    def test_03_attempt_and_head_guards_reject(self):
        with self.assertRaises(StaleState):
            self.runtime.accept(
                acceptance=build_acceptance(), expected_version=8, key="version-mismatch",
            )

        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(exact_head="d" * 40),
                key="wrong-exact-head",
            )

        self.replace_runtime()
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE attempts SET state='Failed',result_commit=NULL WHERE attempt_id='attempt-1'"
            )
            connection.commit()
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(), key="no-succeeded-attempt",
            )

    def test_04_relation_sequence_and_decision_guards_reject(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(
                    subject_type="Run", subject_id="run-1", packet_id=None, run_id="run-1",
                ),
                key="wrong-subject-type",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(packet_id="packet-2", subject_id="packet-2"),
                key="wrong-packet-id",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(subject_id="not-packet-1"),
                key="subject-id-mismatch",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(run_id="run-1"),
                key="nonnull-run-id",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(sequence_number=2),
                key="sequence-two",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(supersedes_acceptance_id="acceptance-0"),
                key="supersedes-nonnull",
            )
        for decision in ("Returned", "ReservedChoice"):
            with self.assertRaises(InvalidRecord):
                self.runtime.accept(
                    acceptance=build_acceptance(decision=decision),
                    key=f"decision-{decision}",
                )

    def test_05_required_authority_must_equal_run_acceptance_boundary(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.accept(
                acceptance=build_acceptance(required_authority="Owner"),
                key="authority-mismatch",
            )
        result = self.runtime.accept(
            acceptance=build_acceptance(required_authority="ProjectArchitect"),
            key="authority-match-architect",
        )
        self.assertEqual(result["packet"]["state"], "AwaitingOwner")

        self.replace_runtime()
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE runs SET acceptance_boundary='Owner' WHERE run_id='run-1'"
            )
            connection.commit()
        result = self.runtime.accept(
            acceptance=build_acceptance(required_authority="Owner"),
            key="authority-match-owner",
        )
        self.assertEqual(result["packet"]["state"], "AwaitingOwner")

    def test_06_closed_review_coverage_accepts_only_the_matching_approve_review(self):
        self.runtime.add_packet("packet-2", "work-2", [])
        self.runtime.store.record_review(
            build_extra_review(review_id="review-wrong-packet", packet_id="packet-2"),
            "seed-wrong-packet", ACTOR, ROUTE_AT,
        )
        self.runtime.store.record_review(
            build_extra_review(review_id="review-wrong-kind", review_kind="Integration"),
            "seed-wrong-kind", ACTOR, ROUTE_AT,
        )
        self.runtime.store.record_review(
            build_extra_review(review_id="review-wrong-result", result="RequestChanges"),
            "seed-wrong-result", ACTOR, ROUTE_AT,
        )
        self.runtime.store.record_review(
            build_extra_review(review_id="review-wrong-head", head_commit="d" * 40),
            "seed-wrong-head", ACTOR, ROUTE_AT,
        )
        self.runtime.store.record_review(
            build_extra_review(review_id="review-wrong-correction", correction_number=1),
            "seed-wrong-correction", ACTOR, ROUTE_AT,
        )

        for name in (
            "review-wrong-packet", "review-wrong-kind", "review-wrong-result",
            "review-wrong-head", "review-wrong-correction",
        ):
            with self.subTest(review_id=name):
                with self.assertRaises(InvalidRecord):
                    self.runtime.accept(
                        acceptance=build_acceptance(review_id=name), key=f"coverage-{name}",
                    )

        result = self.runtime.accept(
            acceptance=build_acceptance(review_id=GOOD_REVIEW_ID), key="coverage-good",
        )
        self.assertEqual(result["packet"]["state"], "AwaitingOwner")

    def test_07_fingerprint_replay_is_exact_and_changed_facts_conflict(self):
        acceptance = build_acceptance()
        first = self.runtime.accept(
            acceptance=acceptance, key="accept-replay", now=ACCEPT_AT,
        )
        replay = self.runtime.accept(
            acceptance=acceptance, key="accept-replay", now=ACCEPT_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.accept_events()), 1)
        self.assertEqual(self.runtime.accept_events()[0]["observed_at"], ACCEPT_AT)

        changed = (
            lambda: self.runtime.accept(
                acceptance=acceptance, key="accept-replay",
                reason={**ACCEPT_REASON, "reason_code": "OTHER"},
            ),
            lambda: self.runtime.accept(
                acceptance={**acceptance, "authority_reference": "architect-2"},
                key="accept-replay",
            ),
            lambda: self.runtime.accept(
                acceptance=acceptance, key="accept-replay",
                actor=Actor("Other", "developer-1", "correlation-1"),
            ),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.accept_events()), 1)
        self.assertEqual(len(self.runtime.rows("acceptance_records")), 1)

    def test_08_event_rollback_concurrency_and_restart_reconstruct_exactly(self):
        acceptance = build_acceptance()
        before = self.runtime.accept_state()

        with mock.patch.object(
            self.runtime.store, "_insert", side_effect=RuntimeError("acceptance insert failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "acceptance insert failure"):
                self.runtime.accept(acceptance=acceptance, key="fail-acceptance-insert")
        self.assertEqual(self.runtime.accept_state(), before)

        class _FailingConnection(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if (
                    isinstance(sql, str)
                    and "UPDATE packets SET state=?,updated_at=?,version=?" in sql
                ):
                    raise RuntimeError("packet update failure")
                return super().execute(sql, *args, **kwargs)

        original_connect = sqlite3.connect

        def connect_with_failing_factory(*args, **kwargs):
            kwargs.setdefault("factory", _FailingConnection)
            return original_connect(*args, **kwargs)

        with mock.patch.object(sqlite3, "connect", connect_with_failing_factory):
            with self.assertRaisesRegex(RuntimeError, "packet update failure"):
                self.runtime.accept(acceptance=acceptance, key="fail-packet-update")
        self.assertEqual(self.runtime.accept_state(), before)

        with mock.patch.object(
            self.runtime.store, "_insert_acceptance_event",
            side_effect=RuntimeError("event insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "event insert failure"):
                self.runtime.accept(acceptance=acceptance, key="fail-event-insert")
        self.assertEqual(self.runtime.accept_state(), before)

        self.replace_runtime()
        barrier = threading.Barrier(2)

        def attempt(number):
            barrier.wait()
            try:
                return self.runtime.accept(
                    acceptance=build_acceptance(acceptance_id=f"acceptance-concurrent-{number}"),
                    key=f"accept-concurrent-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.accept_events()), 1)
        self.assertEqual(len(self.runtime.rows("acceptance_records")), 1)
        winner = next(item for item in outcomes if isinstance(item, dict))
        self.assertEqual(self.runtime.accept_events()[0]["after_json"], winner)

        self.replace_runtime()
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        restart_acceptance = build_acceptance()
        first = self.runtime.accept(
            acceptance=restart_acceptance, key="restart-accept", actor=actor, now=ACCEPT_AT,
        )

        reopened = OperationalStateStore(self.runtime.config)
        self.assertEqual(reopened.health().schema_version, 5)
        replay = reopened.record_and_accept_packet(
            "packet-1", 9, restart_acceptance, dict(ACCEPT_REASON),
            "restart-accept", actor, ACCEPT_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(reopened.snapshot("Packet", "packet-1")["state"], "AwaitingOwner")
        self.assertEqual(
            reopened.snapshot("Acceptance", restart_acceptance["acceptance_id"])["decision"],
            "Accepted",
        )
        self.assertEqual(len(self.runtime.accept_events()), 1)

        documented = {
            "actor": {
                "actor_id": "developer-1", "actor_type": "MaestroDeveloper",
                "causation_event_id": 1, "correlation_id": "correlation-1",
            },
            "operation": "record_and_accept_packet",
            "payload": {
                "expected_packet_version": 9,
                "packet_id": "packet-1",
                "reason": ACCEPT_REASON,
                "acceptance": first["acceptance"],
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event = self.runtime.accept_events()[0]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            (event["entity_type"], event["entity_id"], event["event_type"]),
            ("Packet", "packet-1", "AcceptanceRecorded"),
        )
        self.assertEqual(
            event["before_json"],
            {"packet": state_payload("Packet", "packet-1", "MergeReady", 9)},
        )
        self.assertEqual(event["after_json"], first)
        self.assertEqual(json.loads(event["reason"]), ACCEPT_REASON)
        self.assertEqual(
            (
                event["actor_type"], event["actor_id"], event["correlation_id"],
                event["causation_event_id"], event["observed_at"],
            ),
            ("MaestroDeveloper", "developer-1", "correlation-1", 1, ACCEPT_AT),
        )


if __name__ == "__main__":
    unittest.main()
