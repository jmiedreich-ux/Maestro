from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from unittest import mock

from maestro import review_readiness as rr
from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    StaleState,
)
from test_assignment_claim import ACTOR, ATTEMPT, COMMIT, LEASE, state_payload
from test_execution_heartbeat_and_finish import ExecutionLifecycleDatabase


NOW = "2026-09-04T12:00:00.000000Z"
ROUTE_AT = "2026-09-04T15:00:00.000000Z"
BASE_COMMIT = COMMIT
HEAD_COMMIT = "c" * 40
ROUTE_REASON = {"kind": "reason", "reason_code": "REVIEW_ROUTED", "detail_reference": None}


def build_finding(
    finding_id="finding-1", reason_code="CorrectNow", detail_reference=None,
):
    return {
        "kind": "review-finding",
        "finding_id": finding_id,
        "criterion_reference": "M0-D05#worker-routing",
        "evidence": {
            "kind": "evidence-reference",
            "evidence_id": "evidence-1",
            "digest": "0" * 64,
            "source_reference": None,
        },
        "disposition": {
            "kind": "reason",
            "reason_code": reason_code,
            "detail_reference": detail_reference,
        },
    }


def _findings_for(result):
    if result in ("RequestChanges", "NeedsReplan"):
        return (build_finding(),)
    return ()


def build_coverage(
    *,
    base_commit=BASE_COMMIT,
    head_commit=HEAD_COMMIT,
    allowed_paths=("services/maestro",),
    changed_paths=("services/maestro/example.py",),
    ready=True,
    blockers=(),
    check_outcome="Passed",
    clean_before=True,
    clean_after=True,
    resolved_base=None,
    resolved_head=None,
    checked_out_head_before=None,
    checked_out_head_after=None,
    request_review_kind="IndependentImplementation",
):
    resolved_base = base_commit if resolved_base is None else resolved_base
    resolved_head = head_commit if resolved_head is None else resolved_head
    checked_out_head_before = (
        head_commit if checked_out_head_before is None else checked_out_head_before
    )
    checked_out_head_after = (
        head_commit if checked_out_head_after is None else checked_out_head_after
    )
    request = {
        "schema": rr.REQUEST_SCHEMA,
        "slice_id": "MB-SLICE-M1-REVIEW-ROUTING-05",
        "review_kind": request_review_kind,
        "repository": "/runtime/repository",
        "base": base_commit,
        "head": head_commit,
        "allowed_paths": sorted(allowed_paths, key=lambda item: item.encode("utf-8")),
        "validation_commands": [{"check_id": "unit-tests", "argv": ["true"]}],
        "reconstruction_commands": [{"check_id": "rebuild", "argv": ["true"]}],
        "timeout_seconds": 60,
    }

    def make_check(check_id, category, outcome):
        exit_code = 0 if outcome == "Passed" else 1
        return {
            "check_id": check_id,
            "category": category,
            "argv": ["true"],
            "outcome": outcome,
            "exit_code": exit_code,
            "elapsed_milliseconds": 5,
            "stdout": rr._empty_stream(),
            "stderr": rr._empty_stream(),
            "skip_reason": None,
        }

    checks = [
        make_check("unit-tests", "Validation", check_outcome),
        make_check("rebuild", "Reconstruction", "Passed"),
    ]
    result = {
        "schema": rr.RESULT_SCHEMA,
        "request": request,
        "request_bytes_sha256": "0" * 64,
        "resolved_base": resolved_base,
        "resolved_head": resolved_head,
        "checked_out_head_before": checked_out_head_before,
        "checked_out_head_after": checked_out_head_after,
        "changed_paths": sorted(changed_paths, key=lambda item: item.encode("utf-8"))
        if changed_paths
        else [],
        "clean_before": clean_before,
        "clean_after": clean_after,
        "checks": checks,
        "callback": {"outcome": "NotRequested", "detail": None},
        "blockers": list(blockers),
        "ready": ready,
        "record_digest": "",
    }
    sealed = rr._seal(result)
    return {"kind": "review-readiness-coverage", "result": sealed}


def build_review(
    *,
    review_id="review-1",
    attempt_id="attempt-1",
    review_kind="Integration",
    reviewer_role="IntegrationAgent",
    reviewer_instance="integration-reviewer-1",
    base_commit=BASE_COMMIT,
    head_commit=HEAD_COMMIT,
    result="ValidateOnly",
    findings_json=None,
    coverage=None,
    correction_number=0,
):
    if findings_json is None:
        findings_json = _findings_for(result)
    if coverage is None:
        coverage = build_coverage(base_commit=base_commit, head_commit=head_commit)
    return {
        "review_id": review_id,
        "attempt_id": attempt_id,
        "review_kind": review_kind,
        "reviewer_role": reviewer_role,
        "reviewer_instance": reviewer_instance,
        "base_commit": base_commit,
        "head_commit": head_commit,
        "result": result,
        "findings_json": list(findings_json),
        "coverage_json": coverage,
        "correction_number": correction_number,
    }


class ReviewRoutingDatabase(ExecutionLifecycleDatabase):
    def __init__(self):
        super().__init__()
        self.finished = self.finish(result_commit=HEAD_COMMIT, key="execution-finish-1")

    def route(
        self,
        *,
        packet_id="packet-1",
        expected_version=7,
        review,
        reason=None,
        key="route-1",
        actor=ACTOR,
        now=ROUTE_AT,
    ):
        return self.store.record_and_route_review(
            packet_id, expected_version, review,
            dict(ROUTE_REASON) if reason is None else reason,
            key, actor, now,
        )

    def route_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "ReviewRecorded"
        ]

    def route_state(self):
        return {
            "packets": self.rows("packets"),
            "reviews": self.rows("reviews"),
            "events": self.store.events_after(0, 1000),
        }


class ReviewControlRoutingTests(unittest.TestCase):
    def setUp(self):
        self.runtime = ReviewRoutingDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self):
        self.runtime.close()
        self.runtime = ReviewRoutingDatabase()

    def test_01_each_of_the_four_routes_records_the_exact_result_and_state(self):
        cases = (
            ("AwaitingIntegration", "Integration", "ValidateOnly", "AwaitingReview"),
            ("AwaitingIntegration", "Integration", "NeedsReplan", "NeedsReplan"),
            ("AwaitingReview", "IndependentImplementation", "Approve", "MergeReady"),
            ("AwaitingReview", "IndependentImplementation", "RequestChanges", "AwaitingArchitect"),
        )
        for source_state, review_kind, result, target_state in cases:
            with self.subTest(source_state=source_state, review_kind=review_kind, result=result):
                self.replace_runtime()
                expected_version = 7
                if source_state == "AwaitingReview":
                    self.runtime.route(
                        review=build_review(
                            review_id="review-integration-setup",
                            review_kind="Integration",
                            reviewer_role="IntegrationAgent",
                            reviewer_instance="integration-reviewer-1",
                            result="ValidateOnly",
                        ),
                        expected_version=expected_version,
                        key="route-integration-setup",
                    )
                    expected_version = 8
                reviewer_role = (
                    "IntegrationAgent" if review_kind == "Integration"
                    else "IndependentImplementationReviewer"
                )
                reviewer_instance = (
                    "integration-reviewer-2" if review_kind == "Integration"
                    else "independent-reviewer-1"
                )
                review = build_review(
                    review_id=f"review-target-{result}",
                    review_kind=review_kind,
                    reviewer_role=reviewer_role,
                    reviewer_instance=reviewer_instance,
                    result=result,
                )
                outcome = self.runtime.route(
                    review=review, expected_version=expected_version, key=f"route-target-{result}",
                )
                self.assertEqual(
                    outcome["packet"],
                    state_payload("Packet", "packet-1", target_state, expected_version + 1),
                )
                self.assertEqual(outcome["review"]["result"], result)
                self.assertEqual(outcome["review"]["review_kind"], review_kind)
                self.assertEqual(outcome["review"]["packet_id"], "packet-1")
                packet = self.runtime.store.snapshot("Packet", "packet-1")
                self.assertEqual((packet["state"], packet["version"]), (target_state, expected_version + 1))
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
                    review = build_review(
                        review_kind=kind, reviewer_role=reviewer_role,
                        reviewer_instance="reviewer-outside-table", result=result,
                        coverage={},
                    )
                    with self.assertRaises(InvalidTransition):
                        self.runtime.route(
                            review=review, expected_version=7,
                            key=f"outside-{state}-{kind}-{result}",
                        )
        self.assertEqual(exercised, len(states) * len(kinds_results) - len(valid_routes))

    def test_03_approve_and_validate_only_require_empty_findings(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(result="ValidateOnly", findings_json=(build_finding(),)),
                expected_version=7, key="validate-only-with-finding",
            )
        validated = self.runtime.route(
            review=build_review(result="ValidateOnly"),
            expected_version=7, key="validate-only-empty",
        )
        self.assertEqual(validated["packet"]["state"], "AwaitingReview")

        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(
                    review_id="review-approve-bad", review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-reviewer-1",
                    result="Approve", findings_json=(build_finding(),),
                ),
                expected_version=8, key="approve-with-finding",
            )
        approved = self.runtime.route(
            review=build_review(
                review_id="review-approve-good", review_kind="IndependentImplementation",
                reviewer_role="IndependentImplementationReviewer",
                reviewer_instance="independent-reviewer-1",
                result="Approve",
            ),
            expected_version=8, key="approve-empty",
        )
        self.assertEqual(approved["packet"]["state"], "MergeReady")

    def test_04_request_changes_and_needs_replan_require_at_least_one_finding(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(result="NeedsReplan", findings_json=()),
                expected_version=7, key="needs-replan-empty",
            )
        replanned = self.runtime.route(
            review=build_review(
                review_id="review-needs-replan", result="NeedsReplan",
                findings_json=(build_finding(),),
            ),
            expected_version=7, key="needs-replan-with-finding",
        )
        self.assertEqual(replanned["packet"]["state"], "NeedsReplan")

        self.replace_runtime()
        self.runtime.route(
            review=build_review(result="ValidateOnly"), expected_version=7, key="prep-validate-only",
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(
                    review_id="review-request-changes-empty", review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-reviewer-1",
                    result="RequestChanges", findings_json=(),
                ),
                expected_version=8, key="request-changes-empty",
            )
        requested = self.runtime.route(
            review=build_review(
                review_id="review-request-changes-ok", review_kind="IndependentImplementation",
                reviewer_role="IndependentImplementationReviewer",
                reviewer_instance="independent-reviewer-1",
                result="RequestChanges", findings_json=(build_finding(),),
            ),
            expected_version=8, key="request-changes-ok",
        )
        self.assertEqual(requested["packet"]["state"], "AwaitingArchitect")

    def test_05_malformed_or_unrelated_finding_variants_are_rejected(self):
        base_finding = build_finding()
        variants = (
            {key: value for key, value in base_finding.items() if key != "finding_id"},
            {**base_finding, "kind": "unknown-kind"},
            {
                **base_finding,
                "evidence": {"kind": "reason", "reason_code": "X", "detail_reference": None},
            },
            {
                **base_finding,
                "disposition": {
                    "kind": "evidence-reference", "evidence_id": "x",
                    "digest": "0" * 64, "source_reference": None,
                },
            },
            {
                **base_finding,
                "disposition": {
                    "kind": "reason", "reason_code": "AcceptKnownLimitation",
                    "detail_reference": None,
                },
            },
            {
                "kind": "state", "entity_type": "Packet", "entity_id": "packet-1",
                "state": "Planned", "version": 1,
            },
        )
        for index, finding in enumerate(variants):
            with self.subTest(index=index):
                with self.assertRaises(InvalidRecord):
                    self.runtime.route(
                        review=build_review(result="NeedsReplan", findings_json=(finding,)),
                        expected_version=7, key=f"malformed-finding-{index}",
                    )

    def test_06_packet_attempt_commit_base_head_and_correction_guards_reject(self):
        with self.assertRaises(StaleState):
            self.runtime.route(
                review=build_review(result="ValidateOnly"),
                expected_version=6, key="version-mismatch",
            )

        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE attempts SET state='Failed',result_commit=NULL WHERE attempt_id='attempt-1'"
            )
            connection.commit()
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(result="ValidateOnly"),
                expected_version=7, key="no-succeeded-attempt",
            )
        self.replace_runtime()

        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(result="ValidateOnly", base_commit="d" * 40),
                expected_version=7, key="wrong-base-commit",
            )

        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(result="ValidateOnly", head_commit="e" * 40),
                expected_version=7, key="wrong-head-commit",
            )

        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(result="ValidateOnly", correction_number=1),
                expected_version=7, key="nonzero-correction",
            )

        equal_head_runtime = ExecutionLifecycleDatabase()
        try:
            equal_head_runtime.finish(key="execution-finish-equal")
            with self.assertRaises(InvalidRecord):
                equal_head_runtime.store.record_and_route_review(
                    "packet-1", 7,
                    build_review(result="ValidateOnly", base_commit=COMMIT, head_commit=COMMIT),
                    dict(ROUTE_REASON), "equal-base-head", ACTOR, ROUTE_AT,
                )
        finally:
            equal_head_runtime.close()

    def test_07_closed_coverage_accepts_only_a_complete_matching_ready_result(self):
        good = self.runtime.route(
            review=build_review(result="ValidateOnly", coverage=build_coverage()),
            expected_version=7, key="coverage-good",
        )
        self.assertEqual(good["packet"]["state"], "AwaitingReview")

        self.replace_runtime()
        variants = {
            "malformed": {"kind": "review-readiness-coverage"},
            "not-ready": build_coverage(
                ready=False,
                blockers=({"code": "DIRTY_BEFORE", "check_id": None, "detail": "dirty"},),
            ),
            "nonempty-blockers": build_coverage(
                ready=True,
                blockers=({"code": "DIRTY_BEFORE", "check_id": None, "detail": "dirty"},),
            ),
            "mismatched-head": build_coverage(resolved_head="d" * 40),
            "dirty": build_coverage(clean_before=False),
        }
        digest_altered = build_coverage()
        digest_altered["result"]["changed_paths"] = digest_altered["result"]["changed_paths"] + [
            "services/maestro/extra.py"
        ]
        variants["digest-altered"] = digest_altered

        for name, coverage in variants.items():
            with self.subTest(variant=name):
                with self.assertRaises(InvalidRecord):
                    self.runtime.route(
                        review=build_review(result="ValidateOnly", coverage=coverage),
                        expected_version=7, key=f"coverage-{name}",
                    )

    def test_08_reviewer_role_and_independence_relationships_reject_mismatches(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(
                    review_kind="Integration", reviewer_role="IndependentImplementationReviewer",
                ),
                expected_version=7, key="wrong-role",
            )

        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(reviewer_instance=ATTEMPT["model_identity"]),
                expected_version=7, key="collide-model",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(reviewer_instance=ATTEMPT["runtime_identity"]),
                expected_version=7, key="collide-runtime",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(reviewer_instance=LEASE["holder_id"]),
                expected_version=7, key="collide-holder",
            )

        self.runtime.route(
            review=build_review(result="ValidateOnly", reviewer_instance="integration-reviewer-1"),
            expected_version=7, key="prep-integration",
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(
                    review_id="review-collide-prior", review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="integration-reviewer-1", result="Approve",
                ),
                expected_version=8, key="collide-prior-reviewer",
            )

    def test_09_independent_implementation_requires_one_prior_validate_only(self):
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='AwaitingReview' WHERE packet_id='packet-1'"
            )
            connection.commit()
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(
                    review_id="review-zero-prior", review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-reviewer-1", result="Approve",
                ),
                expected_version=7, key="zero-prior",
            )
        self.replace_runtime()

        self.runtime.route(
            review=build_review(result="ValidateOnly", reviewer_instance="integration-reviewer-1"),
            expected_version=7, key="one-prior-setup",
        )
        good = self.runtime.route(
            review=build_review(
                review_id="review-one-prior", review_kind="IndependentImplementation",
                reviewer_role="IndependentImplementationReviewer",
                reviewer_instance="independent-reviewer-1", result="Approve",
            ),
            expected_version=8, key="one-prior",
        )
        self.assertEqual(good["packet"]["state"], "MergeReady")

        self.replace_runtime()
        self.runtime.route(
            review=build_review(result="ValidateOnly", reviewer_instance="integration-reviewer-1"),
            expected_version=7, key="dup-prior-route",
        )
        extra_review = {
            "review_id": "review-extra-integration", "packet_id": "packet-1",
            "attempt_id": "attempt-1", "review_kind": "Integration",
            "reviewer_role": "IntegrationAgent", "reviewer_instance": "integration-reviewer-2",
            "base_commit": BASE_COMMIT, "head_commit": HEAD_COMMIT, "result": "ValidateOnly",
            "findings_json": [], "coverage_json": {}, "correction_number": 0, "created_at": NOW,
        }
        self.runtime.store.record_review(extra_review, "extra-integration-review", ACTOR, NOW)
        with self.assertRaises(InvalidRecord):
            self.runtime.route(
                review=build_review(
                    review_id="review-two-prior", review_kind="IndependentImplementation",
                    reviewer_role="IndependentImplementationReviewer",
                    reviewer_instance="independent-reviewer-1", result="Approve",
                ),
                expected_version=8, key="two-prior",
            )

    def test_10_fingerprint_replay_is_exact_and_changed_facts_conflict(self):
        review = build_review(result="ValidateOnly")
        first = self.runtime.route(
            review=review, expected_version=7, key="route-immutable", now=ROUTE_AT,
        )
        replay = self.runtime.route(
            review=review, expected_version=7, key="route-immutable", now=ROUTE_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.route_events()), 1)
        self.assertEqual(self.runtime.route_events()[0]["observed_at"], ROUTE_AT)

        changed = (
            lambda: self.runtime.route(
                review=review, expected_version=7, key="route-immutable",
                reason={**ROUTE_REASON, "reason_code": "OTHER"},
            ),
            lambda: self.runtime.route(
                review={**review, "reviewer_instance": "integration-reviewer-2"},
                expected_version=7, key="route-immutable",
            ),
            lambda: self.runtime.route(
                review=review, expected_version=7, key="route-immutable",
                actor=Actor("Other", "developer-1", "correlation-1"),
            ),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.route_events()), 1)
        self.assertEqual(len(self.runtime.rows("reviews")), 1)

    def test_11_review_event_or_packet_update_failure_rolls_back_atomically(self):
        review = build_review(result="ValidateOnly")
        before = self.runtime.route_state()

        with mock.patch.object(
            self.runtime.store, "_insert", side_effect=RuntimeError("review insert failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "review insert failure"):
                self.runtime.route(review=review, expected_version=7, key="fail-review-insert")
        self.assertEqual(self.runtime.route_state(), before)

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
                self.runtime.route(review=review, expected_version=7, key="fail-packet-update")
        self.assertEqual(self.runtime.route_state(), before)

        with mock.patch.object(
            self.runtime.store, "_insert_review_route_event",
            side_effect=RuntimeError("event insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "event insert failure"):
                self.runtime.route(review=review, expected_version=7, key="fail-event-insert")
        self.assertEqual(self.runtime.route_state(), before)

    def test_12_concurrent_routing_calls_have_one_winner_and_no_residue(self):
        barrier = threading.Barrier(2)

        def attempt(number):
            barrier.wait()
            try:
                review = build_review(
                    review_id=f"review-concurrent-{number}",
                    reviewer_instance=f"integration-reviewer-concurrent-{number}",
                    result="ValidateOnly",
                )
                return self.runtime.route(
                    review=review, expected_version=7, key=f"concurrent-route-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.route_events()), 1)
        self.assertEqual(len(self.runtime.rows("reviews")), 1)
        winner = next(item for item in outcomes if isinstance(item, dict))
        self.assertEqual(self.runtime.route_events()[0]["after_json"], winner)

    def test_13_restart_preserves_exact_replay_and_reconstruction(self):
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        review = build_review(result="ValidateOnly")
        first = self.runtime.route(
            review=review, expected_version=7, key="restart-route", actor=actor, now=ROUTE_AT,
        )

        reopened = OperationalStateStore(self.runtime.config)
        self.assertEqual(reopened.health().schema_version, 5)
        replay = reopened.record_and_route_review(
            "packet-1", 7, review, dict(ROUTE_REASON), "restart-route", actor, ROUTE_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(reopened.snapshot("Packet", "packet-1")["state"], "AwaitingReview")
        self.assertEqual(
            reopened.snapshot("Review", review["review_id"])["result"], "ValidateOnly"
        )
        self.assertEqual(len(self.runtime.route_events()), 1)

        documented = {
            "actor": {
                "actor_id": "developer-1", "actor_type": "MaestroDeveloper",
                "causation_event_id": 1, "correlation_id": "correlation-1",
            },
            "operation": "record_and_route_review",
            "payload": {
                "expected_packet_version": 7,
                "packet_id": "packet-1",
                "reason": ROUTE_REASON,
                "review": first["review"],
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event = self.runtime.route_events()[0]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            (event["entity_type"], event["entity_id"], event["event_type"]),
            ("Packet", "packet-1", "ReviewRecorded"),
        )
        self.assertEqual(
            event["before_json"],
            {"packet": state_payload("Packet", "packet-1", "AwaitingIntegration", 7)},
        )
        self.assertEqual(event["after_json"], first)
        self.assertEqual(json.loads(event["reason"]), ROUTE_REASON)
        self.assertEqual(
            (
                event["actor_type"], event["actor_id"], event["correlation_id"],
                event["causation_event_id"], event["observed_at"],
            ),
            ("MaestroDeveloper", "developer-1", "correlation-1", 1, ROUTE_AT),
        )


if __name__ == "__main__":
    unittest.main()
