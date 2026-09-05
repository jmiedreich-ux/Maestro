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
from test_correction_dispatch import (
    CORRECTION_ATTEMPT,
    CORRECTION_LEASE,
    CorrectionDispatchDatabase,
)
from test_review_control_routing import (
    HEAD_COMMIT,
    build_coverage,
    build_finding,
    build_review,
)


CORRECTION_HEAD_COMMIT = "d" * 40
CORRECTION_START_AT = "2026-09-04T16:15:00.000000Z"
CORRECTION_FINISHED_AT = "2026-09-04T16:30:00.000000Z"
CORRECTION_ROUTE_AT = "2026-09-04T17:00:00.000000Z"
CORRECTION_HANDLE = "provider-job-2"
CORRECTION_EXPECTED_RESULT = "committed-correction-candidate"
CORRECTION_COMPLETION_REFERENCE = "evidence:worker-result-2"
CORRECTION_START_REASON = {
    "kind": "reason", "reason_code": "CORRECTION_EXECUTION_OBSERVED", "detail_reference": None,
}
CORRECTION_FINISH_REASON = {
    "kind": "reason", "reason_code": "CORRECTION_EXECUTION_FINISHED", "detail_reference": None,
}
CORRECTION_ROUTE_REASON = {
    "kind": "reason", "reason_code": "CORRECTION_REVIEW_ROUTED", "detail_reference": None,
}


def build_correction_review(
    *,
    review_id="correction-review-1",
    attempt_id="attempt-2",
    review_kind="Integration",
    reviewer_role="IntegrationAgent",
    reviewer_instance="integration-corrector-1",
    base_commit=HEAD_COMMIT,
    head_commit=CORRECTION_HEAD_COMMIT,
    result="ValidateOnly",
    findings_json=None,
    coverage=None,
):
    return build_review(
        review_id=review_id,
        attempt_id=attempt_id,
        review_kind=review_kind,
        reviewer_role=reviewer_role,
        reviewer_instance=reviewer_instance,
        base_commit=base_commit,
        head_commit=head_commit,
        result=result,
        findings_json=findings_json,
        coverage=coverage,
        correction_number=1,
    )


class CorrectionReviewRoutingDatabase(CorrectionDispatchDatabase):
    def __init__(self, correction_result_commit=CORRECTION_HEAD_COMMIT):
        super().__init__()
        self.dispatched = self.dispatch()
        self.started = self.store.start_attempt_execution(
            "attempt-2", 1, 10, CORRECTION_HANDLE, CORRECTION_EXPECTED_RESULT,
            CORRECTION_START_REASON, "correction-execution-start-1", ACTOR,
            CORRECTION_START_AT,
        )
        self.finished = self.store.finish_attempt_execution(
            "attempt-2", 2, 11, 1, CORRECTION_HANDLE, "Succeeded", correction_result_commit,
            CORRECTION_COMPLETION_REFERENCE, CORRECTION_FINISH_REASON,
            "correction-execution-finish-1", ACTOR, CORRECTION_FINISHED_AT,
        )

    def route_correction(
        self,
        *,
        packet_id="packet-1",
        expected_version=12,
        review,
        reason=None,
        key="correction-route-1",
        actor=ACTOR,
        now=CORRECTION_ROUTE_AT,
    ):
        return self.store.record_and_route_correction_review(
            packet_id, expected_version, review,
            dict(CORRECTION_ROUTE_REASON) if reason is None else reason,
            key, actor, now,
        )

    def correction_route_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "ReviewRecorded"
        ]

    def correction_route_state(self):
        return {
            "packets": self.rows("packets"),
            "reviews": self.rows("reviews"),
            "events": self.store.events_after(0, 1000),
        }


class CorrectionReviewRoutingTests(unittest.TestCase):
    def setUp(self):
        self.runtime = CorrectionReviewRoutingDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self):
        self.runtime.close()
        self.runtime = CorrectionReviewRoutingDatabase()

    def test_01_each_of_the_four_routes_records_the_exact_result_and_state(self):
        cases = (
            ("AwaitingIntegration", "Integration", "ValidateOnly", "AwaitingReview"),
            ("AwaitingIntegration", "Integration", "NeedsReplan", "NeedsReplan"),
            ("AwaitingReview", "IndependentImplementation", "Approve", "MergeReady"),
            ("AwaitingReview", "IndependentImplementation", "RequestChanges", "NeedsReplan"),
        )
        for source_state, review_kind, result, target_state in cases:
            with self.subTest(source_state=source_state, review_kind=review_kind, result=result):
                self.replace_runtime()
                expected_version = 12
                if source_state == "AwaitingReview":
                    self.runtime.route_correction(
                        review=build_correction_review(
                            review_id="correction-review-integration-setup",
                            review_kind="Integration",
                            reviewer_role="IntegrationAgent",
                            reviewer_instance="integration-corrector-1",
                            result="ValidateOnly",
                        ),
                        expected_version=expected_version,
                        key="correction-route-integration-setup",
                    )
                    expected_version = 13
                reviewer_role = (
                    "IntegrationAgent" if review_kind == "Integration"
                    else "IndependentImplementationReviewer"
                )
                reviewer_instance = (
                    "integration-corrector-2" if review_kind == "Integration"
                    else "independent-corrector-1"
                )
                review = build_correction_review(
                    review_id=f"correction-review-target-{result}",
                    review_kind=review_kind,
                    reviewer_role=reviewer_role,
                    reviewer_instance=reviewer_instance,
                    result=result,
                )
                outcome = self.runtime.route_correction(
                    review=review, expected_version=expected_version,
                    key=f"correction-route-target-{result}",
                )
                self.assertEqual(
                    outcome["packet"],
                    state_payload("Packet", "packet-1", target_state, expected_version + 1),
                )
                self.assertEqual(outcome["review"]["result"], result)
                self.assertEqual(outcome["review"]["review_kind"], review_kind)
                self.assertEqual(outcome["review"]["correction_number"], 1)
                self.assertEqual(outcome["review"]["packet_id"], "packet-1")
                packet = self.runtime.store.snapshot("Packet", "packet-1")
                self.assertEqual(
                    (packet["state"], packet["version"]), (target_state, expected_version + 1)
                )
                stored_review = self.runtime.store.snapshot("Review", review["review_id"])
                self.assertEqual(stored_review, outcome["review"])

    def test_02_every_route_outside_the_closed_table_raises_invalid_transition(self):
        states = (
            "Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Leased", "Running",
            "AwaitingIntegration", "AwaitingReview", "MergeReady", "AwaitingArchitect",
            "AwaitingOwner", "Merged", "Complete", "NeedsReplan", "Cancelled",
        )
        kinds_results = (
            ("Integration", "ValidateOnly"), ("Integration", "NeedsReplan"),
            ("Integration", "Approve"), ("Integration", "RequestChanges"),
            ("Integration", "Assemble"), ("Integration", "Comment"),
            ("IndependentImplementation", "ValidateOnly"), ("IndependentImplementation", "NeedsReplan"),
            ("IndependentImplementation", "Approve"), ("IndependentImplementation", "RequestChanges"),
            ("IndependentImplementation", "Assemble"), ("IndependentImplementation", "Comment"),
        )
        valid_routes = {
            ("AwaitingIntegration", "Integration", "ValidateOnly"),
            ("AwaitingIntegration", "Integration", "NeedsReplan"),
            ("AwaitingReview", "IndependentImplementation", "Approve"),
            ("AwaitingReview", "IndependentImplementation", "RequestChanges"),
        }
        exercised = 0
        for state in states:
            for kind, result in kinds_results:
                if (state, kind, result) in valid_routes:
                    continue
                exercised += 1
                with self.subTest(state=state, kind=kind, result=result):
                    with closing(sqlite3.connect(self.runtime.database)) as connection:
                        connection.execute(
                            "UPDATE packets SET state=? WHERE packet_id='packet-1'", (state,)
                        )
                        connection.commit()
                    reviewer_role = (
                        "IntegrationAgent" if kind == "Integration"
                        else "IndependentImplementationReviewer"
                    )
                    review = build_correction_review(
                        review_kind=kind, reviewer_role=reviewer_role,
                        reviewer_instance="reviewer-outside-table", result=result,
                        coverage={},
                    )
                    with self.assertRaises(InvalidTransition):
                        self.runtime.route_correction(
                            review=review, expected_version=12,
                            key=f"correction-outside-{state}-{kind}-{result}",
                        )
        self.assertEqual(exercised, len(states) * len(kinds_results) - len(valid_routes))

    def test_03_correction_number_zero_is_rejected(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_review(result="ValidateOnly"),
                expected_version=12, key="correction-number-zero",
            )

    def test_04_attempt_and_commit_range_guards_reject(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE attempts SET state='Failed',result_commit=NULL WHERE attempt_id='attempt-2'"
            )
            connection.commit()
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(result="ValidateOnly"),
                expected_version=12, key="correction-no-succeeded-attempt",
            )
        self.replace_runtime()

        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(result="ValidateOnly", base_commit="e" * 40),
                expected_version=12, key="correction-wrong-base-commit",
            )

        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(result="ValidateOnly", head_commit="f" * 40),
                expected_version=12, key="correction-wrong-head-commit",
            )

        equal_runtime = CorrectionReviewRoutingDatabase(correction_result_commit=HEAD_COMMIT)
        try:
            with self.assertRaises(InvalidRecord):
                equal_runtime.store.record_and_route_correction_review(
                    "packet-1", 12,
                    build_correction_review(
                        result="ValidateOnly", base_commit=HEAD_COMMIT, head_commit=HEAD_COMMIT,
                    ),
                    dict(CORRECTION_ROUTE_REASON), "correction-equal-base-head", ACTOR,
                    CORRECTION_ROUTE_AT,
                )
        finally:
            equal_runtime.close()

    def test_05_correction_count_guard_rejects(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute("UPDATE packets SET correction_count=0 WHERE packet_id='packet-1'")
            connection.commit()
        before = self.runtime.correction_route_state()
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(result="ValidateOnly"),
                expected_version=12, key="correction-count-zero",
            )
        self.assertEqual(self.runtime.correction_route_state(), before)

    def test_06_closed_coverage_accepts_only_a_complete_matching_ready_result(self):
        good = self.runtime.route_correction(
            review=build_correction_review(
                result="ValidateOnly",
                coverage=build_coverage(base_commit=HEAD_COMMIT, head_commit=CORRECTION_HEAD_COMMIT),
            ),
            expected_version=12, key="correction-coverage-good",
        )
        self.assertEqual(good["packet"]["state"], "AwaitingReview")

        self.replace_runtime()
        variants = {
            "malformed": {"kind": "review-readiness-coverage"},
            "not-ready": build_coverage(
                base_commit=HEAD_COMMIT, head_commit=CORRECTION_HEAD_COMMIT,
                ready=False,
                blockers=({"code": "DIRTY_BEFORE", "check_id": None, "detail": "dirty"},),
            ),
            "nonempty-blockers": build_coverage(
                base_commit=HEAD_COMMIT, head_commit=CORRECTION_HEAD_COMMIT,
                ready=True,
                blockers=({"code": "DIRTY_BEFORE", "check_id": None, "detail": "dirty"},),
            ),
            "mismatched-head": build_coverage(
                base_commit=HEAD_COMMIT, head_commit=CORRECTION_HEAD_COMMIT,
                resolved_head="e" * 40,
            ),
            "dirty": build_coverage(
                base_commit=HEAD_COMMIT, head_commit=CORRECTION_HEAD_COMMIT, clean_before=False,
            ),
        }
        digest_altered = build_coverage(base_commit=HEAD_COMMIT, head_commit=CORRECTION_HEAD_COMMIT)
        digest_altered["result"]["changed_paths"] = digest_altered["result"]["changed_paths"] + [
            "services/maestro/extra.py"
        ]
        variants["digest-altered"] = digest_altered

        for name, coverage in variants.items():
            with self.subTest(variant=name):
                with self.assertRaises(InvalidRecord):
                    self.runtime.route_correction(
                        review=build_correction_review(result="ValidateOnly", coverage=coverage),
                        expected_version=12, key=f"correction-coverage-{name}",
                    )

    def test_07_reviewer_role_and_independence_relationships_reject_mismatches(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    review_kind="Integration", reviewer_role="IndependentImplementationReviewer",
                ),
                expected_version=12, key="correction-wrong-role",
            )

        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    reviewer_instance=CORRECTION_ATTEMPT["model_identity"]
                ),
                expected_version=12, key="correction-collide-model",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    reviewer_instance=CORRECTION_ATTEMPT["runtime_identity"]
                ),
                expected_version=12, key="correction-collide-runtime",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    reviewer_instance=CORRECTION_LEASE["holder_id"]
                ),
                expected_version=12, key="correction-collide-holder",
            )

        self.runtime.route_correction(
            review=build_correction_review(
                result="ValidateOnly", reviewer_instance="integration-corrector-1"
            ),
            expected_version=12, key="correction-prep-integration",
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    review_id="correction-review-collide-prior",
                    review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="integration-corrector-1", result="Approve",
                ),
                expected_version=13, key="correction-collide-prior-reviewer",
            )

    def test_08_independent_implementation_requires_one_prior_correction_pass_validate_only(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='AwaitingReview' WHERE packet_id='packet-1'"
            )
            connection.commit()
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    review_id="correction-review-zero-prior",
                    review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-corrector-1", result="Approve",
                ),
                expected_version=12, key="correction-zero-prior",
            )
        self.replace_runtime()

        self.runtime.store.record_review(
            {
                "review_id": "correction-review-wrong-correction-number",
                "packet_id": "packet-1",
                "attempt_id": "attempt-2",
                "review_kind": "Integration",
                "reviewer_role": "IntegrationAgent",
                "reviewer_instance": "integration-corrector-mismatch",
                "base_commit": HEAD_COMMIT,
                "head_commit": CORRECTION_HEAD_COMMIT,
                "result": "ValidateOnly",
                "findings_json": [],
                "coverage_json": {},
                "correction_number": 0,
                "created_at": CORRECTION_ROUTE_AT,
            },
            "seed-correction-wrong-correction-number", ACTOR, CORRECTION_ROUTE_AT,
        )
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='AwaitingReview' WHERE packet_id='packet-1'"
            )
            connection.commit()
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    review_id="correction-review-wrong-correction-number-approve",
                    review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-corrector-1", result="Approve",
                ),
                expected_version=12, key="correction-wrong-correction-number",
            )
        self.replace_runtime()

        self.runtime.route_correction(
            review=build_correction_review(
                result="ValidateOnly", reviewer_instance="integration-corrector-1"
            ),
            expected_version=12, key="correction-one-prior-setup",
        )
        good = self.runtime.route_correction(
            review=build_correction_review(
                review_id="correction-review-one-prior",
                review_kind="IndependentImplementation",
                reviewer_role="IndependentImplementationReviewer",
                reviewer_instance="independent-corrector-1", result="Approve",
            ),
            expected_version=13, key="correction-one-prior",
        )
        self.assertEqual(good["packet"]["state"], "MergeReady")

    def test_09_findings_complement_and_closed_kind_are_enforced_unchanged(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    review_id="correction-review-approve-bad",
                    review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-corrector-1", result="Approve",
                    findings_json=(build_finding(),),
                ),
                expected_version=12, key="correction-approve-with-finding",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.route_correction(
                review=build_correction_review(
                    review_id="correction-review-request-changes-empty",
                    review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-corrector-1", result="RequestChanges",
                    findings_json=(),
                ),
                expected_version=12, key="correction-request-changes-empty",
            )

    def test_10_fingerprint_replay_rollback_concurrency_and_restart_reconstruct_exactly(self):
        review = build_correction_review(result="ValidateOnly")
        first = self.runtime.route_correction(
            review=review, expected_version=12, key="correction-route-immutable",
            now=CORRECTION_ROUTE_AT,
        )
        replay = self.runtime.route_correction(
            review=review, expected_version=12, key="correction-route-immutable",
            now=CORRECTION_ROUTE_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.rows("reviews")), 3)
        events = self.runtime.correction_route_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[-1]["observed_at"], CORRECTION_ROUTE_AT)

        changed = (
            lambda: self.runtime.route_correction(
                review=review, expected_version=12, key="correction-route-immutable",
                reason={**CORRECTION_ROUTE_REASON, "reason_code": "OTHER"},
            ),
            lambda: self.runtime.route_correction(
                review={**review, "reviewer_instance": "integration-corrector-2"},
                expected_version=12, key="correction-route-immutable",
            ),
            lambda: self.runtime.route_correction(
                review=review, expected_version=12, key="correction-route-immutable",
                actor=Actor("Other", "developer-1", "correlation-1"),
            ),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.correction_route_events()), 3)
        self.assertEqual(len(self.runtime.rows("reviews")), 3)

        self.replace_runtime()
        before = self.runtime.correction_route_state()
        with mock.patch.object(
            self.runtime.store, "_insert",
            side_effect=RuntimeError("correction review insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "correction review insert failure"):
                self.runtime.route_correction(
                    review=build_correction_review(result="ValidateOnly"),
                    expected_version=12, key="correction-fail-review-insert",
                )
        self.assertEqual(self.runtime.correction_route_state(), before)

        class _FailingConnection(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if (
                    isinstance(sql, str)
                    and "UPDATE packets SET state=?,updated_at=?,version=?" in sql
                ):
                    raise RuntimeError("correction packet update failure")
                return super().execute(sql, *args, **kwargs)

        original_connect = sqlite3.connect

        def connect_with_failing_factory(*args, **kwargs):
            kwargs.setdefault("factory", _FailingConnection)
            return original_connect(*args, **kwargs)

        with mock.patch.object(sqlite3, "connect", connect_with_failing_factory):
            with self.assertRaisesRegex(RuntimeError, "correction packet update failure"):
                self.runtime.route_correction(
                    review=build_correction_review(result="ValidateOnly"),
                    expected_version=12, key="correction-fail-packet-update",
                )
        self.assertEqual(self.runtime.correction_route_state(), before)

        with mock.patch.object(
            self.runtime.store, "_insert_review_route_event",
            side_effect=RuntimeError("correction event insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "correction event insert failure"):
                self.runtime.route_correction(
                    review=build_correction_review(result="ValidateOnly"),
                    expected_version=12, key="correction-fail-event-insert",
                )
        self.assertEqual(self.runtime.correction_route_state(), before)

        self.replace_runtime()
        barrier = threading.Barrier(2)

        def attempt(number):
            barrier.wait()
            try:
                review = build_correction_review(
                    review_id=f"correction-review-concurrent-{number}",
                    reviewer_instance=f"integration-corrector-concurrent-{number}",
                    result="ValidateOnly",
                )
                return self.runtime.route_correction(
                    review=review, expected_version=12,
                    key=f"correction-concurrent-route-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.correction_route_events()), 3)
        self.assertEqual(len(self.runtime.rows("reviews")), 3)
        winner = next(item for item in outcomes if isinstance(item, dict))
        self.assertEqual(self.runtime.correction_route_events()[-1]["after_json"], winner)

        self.replace_runtime()
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        review = build_correction_review(result="ValidateOnly")
        first = self.runtime.route_correction(
            review=review, expected_version=12, key="correction-restart-route",
            actor=actor, now=CORRECTION_ROUTE_AT,
        )

        reopened = OperationalStateStore(self.runtime.config)
        self.assertEqual(reopened.health().schema_version, 5)
        replay = reopened.record_and_route_correction_review(
            "packet-1", 12, review, dict(CORRECTION_ROUTE_REASON),
            "correction-restart-route", actor, CORRECTION_ROUTE_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(reopened.snapshot("Packet", "packet-1")["state"], "AwaitingReview")
        self.assertEqual(
            reopened.snapshot("Review", review["review_id"])["result"], "ValidateOnly"
        )
        self.assertEqual(len(self.runtime.correction_route_events()), 3)

        documented = {
            "actor": {
                "actor_id": "developer-1", "actor_type": "MaestroDeveloper",
                "causation_event_id": 1, "correlation_id": "correlation-1",
            },
            "operation": "record_and_route_correction_review",
            "payload": {
                "expected_packet_version": 12,
                "packet_id": "packet-1",
                "reason": CORRECTION_ROUTE_REASON,
                "review": first["review"],
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event = self.runtime.correction_route_events()[-1]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            (event["entity_type"], event["entity_id"], event["event_type"]),
            ("Packet", "packet-1", "ReviewRecorded"),
        )
        self.assertEqual(
            event["before_json"],
            {"packet": state_payload("Packet", "packet-1", "AwaitingIntegration", 12)},
        )
        self.assertEqual(event["after_json"], first)
        self.assertEqual(json.loads(event["reason"]), CORRECTION_ROUTE_REASON)
        self.assertEqual(
            (
                event["actor_type"], event["actor_id"], event["correlation_id"],
                event["causation_event_id"], event["observed_at"],
            ),
            ("MaestroDeveloper", "developer-1", "correlation-1", 1, CORRECTION_ROUTE_AT),
        )


if __name__ == "__main__":
    unittest.main()
