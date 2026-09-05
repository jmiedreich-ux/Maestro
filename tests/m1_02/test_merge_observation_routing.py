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
from test_acceptance_routing import (
    ACCEPT_AT,
    AcceptanceRoutingDatabase,
    build_acceptance,
)
from test_assignment_claim import ACTOR, state_payload
from test_review_control_routing import HEAD_COMMIT


OBSERVE_AT = "2026-09-04T17:00:00.000000Z"
OBSERVE_REASON = {
    "kind": "reason",
    "reason_code": "MERGE_OBSERVED",
    "detail_reference": None,
}


def build_merge_observation(
    *,
    merge_observation_id="merge-observation-1",
    run_id="run-1",
    packet_id="packet-1",
    acceptance_id="acceptance-1",
    repository_reference="owner/repo",
    default_branch="main",
    accepted_head=HEAD_COMMIT,
    merge_commit=None,
    source_kind="Git",
    source_reference="refs/heads/implementation/packet-1",
    performed_by_authority="Owner",
    performed_by_reference="owner-1",
    delegation_reference=None,
    review_coverage_json=None,
):
    return {
        "merge_observation_id": merge_observation_id,
        "run_id": run_id,
        "packet_id": packet_id,
        "acceptance_id": acceptance_id,
        "repository_reference": repository_reference,
        "default_branch": default_branch,
        "accepted_head": accepted_head,
        "merge_commit": accepted_head if merge_commit is None else merge_commit,
        "source_kind": source_kind,
        "source_reference": source_reference,
        "performed_by_authority": performed_by_authority,
        "performed_by_reference": performed_by_reference,
        "delegation_reference": delegation_reference,
        "review_coverage_json": review_coverage_json,
    }


class MergeObservationDatabase(AcceptanceRoutingDatabase):
    def __init__(self, *, accept=True):
        super().__init__()
        if accept:
            self.accepted = self.accept(acceptance=build_acceptance(), key="accept-1")

    def observe(
        self,
        *,
        packet_id="packet-1",
        expected_version=10,
        merge_observation,
        reason=None,
        key="observe-1",
        actor=ACTOR,
        now=OBSERVE_AT,
    ):
        return self.store.record_and_observe_merge(
            packet_id, expected_version, merge_observation,
            dict(OBSERVE_REASON) if reason is None else reason,
            key, actor, now,
        )

    def observe_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "MergeObserved"
        ]

    def observe_state(self):
        return {
            "packets": self.rows("packets"),
            "merge_observations": self.rows("merge_observations"),
            "events": self.store.events_after(0, 1000),
        }


class MergeObservationRoutingTests(unittest.TestCase):
    def setUp(self):
        self.runtime = MergeObservationDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self, **kwargs):
        self.runtime.close()
        self.runtime = MergeObservationDatabase(**kwargs)

    def test_01_awaitingowner_valid_observation_transitions_to_merged(self):
        observation = build_merge_observation()
        result = self.runtime.observe(merge_observation=observation, key="observe-good")
        self.assertEqual(
            result["packet"], state_payload("Packet", "packet-1", "Merged", 11)
        )
        self.assertEqual(
            result["merge_observation"]["merge_observation_id"], "merge-observation-1"
        )
        self.assertEqual(result["merge_observation"]["observed_at"], OBSERVE_AT)
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((packet["state"], packet["version"]), ("Merged", 11))
        stored = self.runtime.store.snapshot("MergeObservation", "merge-observation-1")
        self.assertEqual(stored, result["merge_observation"])
        events = self.runtime.observe_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["after_json"], result)
        self.assertEqual(
            events[0]["before_json"],
            {"packet": state_payload("Packet", "packet-1", "AwaitingOwner", 10)},
        )

    def test_02_every_other_source_state_raises_invalid_transition(self):
        states = (
            "Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Leased", "Running",
            "AwaitingIntegration", "AwaitingReview", "MergeReady", "AwaitingArchitect",
            "Merged", "Complete", "NeedsReplan", "Cancelled",
        )
        for state in states:
            with self.subTest(state=state):
                with closing(sqlite3.connect(self.runtime.database)) as connection:
                    connection.execute(
                        "UPDATE packets SET state=? WHERE packet_id='packet-1'", (state,)
                    )
                    connection.commit()
                with self.assertRaises(InvalidTransition):
                    self.runtime.observe(
                        merge_observation=build_merge_observation(), key=f"outside-{state}",
                    )
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='AwaitingOwner' WHERE packet_id='packet-1'"
            )
            connection.commit()

    def test_03_version_and_relation_guards_reject(self):
        with self.assertRaises(StaleState):
            self.runtime.observe(
                merge_observation=build_merge_observation(), expected_version=9,
                key="version-mismatch",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(packet_id="packet-2"),
                key="wrong-packet-id",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(run_id="run-2"),
                key="wrong-run-id",
            )

    def test_04_acceptance_lookup_guards_reject(self):
        self.runtime.add_packet("packet-2", "work-2", [])
        self.runtime.store.record_acceptance(
            {
                **build_acceptance(
                    acceptance_id="acceptance-other-packet",
                    subject_id="packet-2", packet_id="packet-2",
                ),
                "created_at": ACCEPT_AT,
            },
            "seed-other-packet-acceptance", ACTOR, ACCEPT_AT,
        )
        self.runtime.store.record_acceptance(
            {
                **build_acceptance(
                    acceptance_id="acceptance-sequence-two", sequence_number=2,
                ),
                "created_at": ACCEPT_AT,
            },
            "seed-sequence-two-acceptance", ACTOR, ACCEPT_AT,
        )

        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(acceptance_id="does-not-exist"),
                key="missing-acceptance",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(
                    acceptance_id="acceptance-other-packet"
                ),
                key="wrong-packet-acceptance",
            )
        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(
                    acceptance_id="acceptance-sequence-two"
                ),
                key="sequence-two-acceptance",
            )

        self.replace_runtime(accept=False)
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='AwaitingOwner',version=10 WHERE packet_id='packet-1'"
            )
            connection.commit()
        self.runtime.store.record_acceptance(
            {**build_acceptance(decision="Returned"), "created_at": ACCEPT_AT},
            "seed-wrong-decision-acceptance", ACTOR, ACCEPT_AT,
        )
        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(), key="wrong-decision-acceptance",
            )

        self.replace_runtime()
        result = self.runtime.observe(
            merge_observation=build_merge_observation(), key="matching-acceptance",
        )
        self.assertEqual(result["packet"]["state"], "Merged")

    def test_05_accepted_head_mismatch_rejects_fast_forward_is_legal(self):
        with self.assertRaises(InvalidRecord):
            self.runtime.observe(
                merge_observation=build_merge_observation(accepted_head="d" * 40),
                key="accepted-head-mismatch",
            )
        result = self.runtime.observe(
            merge_observation=build_merge_observation(merge_commit=HEAD_COMMIT),
            key="fast-forward-merge",
        )
        self.assertEqual(result["packet"]["state"], "Merged")
        self.assertEqual(
            result["merge_observation"]["merge_commit"],
            result["merge_observation"]["accepted_head"],
        )

    def test_06_fingerprint_replay_is_exact_and_changed_facts_conflict(self):
        observation = build_merge_observation()
        first = self.runtime.observe(
            merge_observation=observation, key="observe-replay", now=OBSERVE_AT,
        )
        replay = self.runtime.observe(
            merge_observation=observation, key="observe-replay", now=OBSERVE_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.observe_events()), 1)
        self.assertEqual(self.runtime.observe_events()[0]["observed_at"], OBSERVE_AT)

        changed = (
            lambda: self.runtime.observe(
                merge_observation=observation, key="observe-replay",
                reason={**OBSERVE_REASON, "reason_code": "OTHER"},
            ),
            lambda: self.runtime.observe(
                merge_observation={**observation, "performed_by_reference": "owner-2"},
                key="observe-replay",
            ),
            lambda: self.runtime.observe(
                merge_observation=observation, key="observe-replay",
                actor=Actor("Other", "developer-1", "correlation-1"),
            ),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.observe_events()), 1)
        self.assertEqual(len(self.runtime.rows("merge_observations")), 1)

    def test_07_event_rollback_concurrency_and_restart_reconstruct_exactly(self):
        observation = build_merge_observation()
        before = self.runtime.observe_state()

        with mock.patch.object(
            self.runtime.store, "_insert",
            side_effect=RuntimeError("merge observation insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "merge observation insert failure"):
                self.runtime.observe(merge_observation=observation, key="fail-merge-insert")
        self.assertEqual(self.runtime.observe_state(), before)

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
                self.runtime.observe(merge_observation=observation, key="fail-packet-update")
        self.assertEqual(self.runtime.observe_state(), before)

        with mock.patch.object(
            self.runtime.store, "_insert_merge_observation_event",
            side_effect=RuntimeError("event insert failure"),
        ):
            with self.assertRaisesRegex(RuntimeError, "event insert failure"):
                self.runtime.observe(merge_observation=observation, key="fail-event-insert")
        self.assertEqual(self.runtime.observe_state(), before)

        self.replace_runtime()
        barrier = threading.Barrier(2)

        def attempt(number):
            barrier.wait()
            try:
                return self.runtime.observe(
                    merge_observation=build_merge_observation(
                        merge_observation_id=f"merge-observation-concurrent-{number}"
                    ),
                    key=f"observe-concurrent-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(attempt, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.observe_events()), 1)
        self.assertEqual(len(self.runtime.rows("merge_observations")), 1)
        winner = next(item for item in outcomes if isinstance(item, dict))
        self.assertEqual(self.runtime.observe_events()[0]["after_json"], winner)

        self.replace_runtime()
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        restart_observation = build_merge_observation()
        first = self.runtime.observe(
            merge_observation=restart_observation, key="restart-observe",
            actor=actor, now=OBSERVE_AT,
        )

        reopened = OperationalStateStore(self.runtime.config)
        self.assertEqual(reopened.health().schema_version, 5)
        replay = reopened.record_and_observe_merge(
            "packet-1", 10, restart_observation, dict(OBSERVE_REASON),
            "restart-observe", actor, OBSERVE_AT,
        )
        self.assertEqual(replay, first)
        self.assertEqual(reopened.snapshot("Packet", "packet-1")["state"], "Merged")
        self.assertEqual(
            reopened.snapshot(
                "MergeObservation", restart_observation["merge_observation_id"]
            )["merge_commit"],
            restart_observation["merge_commit"],
        )
        self.assertEqual(len(self.runtime.observe_events()), 1)

        documented = {
            "actor": {
                "actor_id": "developer-1", "actor_type": "MaestroDeveloper",
                "causation_event_id": 1, "correlation_id": "correlation-1",
            },
            "operation": "record_and_observe_merge",
            "payload": {
                "expected_packet_version": 10,
                "packet_id": "packet-1",
                "reason": OBSERVE_REASON,
                "merge_observation": first["merge_observation"],
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event = self.runtime.observe_events()[0]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(
            (event["entity_type"], event["entity_id"], event["event_type"]),
            ("Packet", "packet-1", "MergeObserved"),
        )
        self.assertEqual(
            event["before_json"],
            {"packet": state_payload("Packet", "packet-1", "AwaitingOwner", 10)},
        )
        self.assertEqual(event["after_json"], first)
        self.assertEqual(json.loads(event["reason"]), OBSERVE_REASON)
        self.assertEqual(
            (
                event["actor_type"], event["actor_id"], event["correlation_id"],
                event["causation_event_id"], event["observed_at"],
            ),
            ("MaestroDeveloper", "developer-1", "correlation-1", 1, OBSERVE_AT),
        )


if __name__ == "__main__":
    unittest.main()
