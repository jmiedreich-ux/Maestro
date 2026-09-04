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

from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    StaleState,
)


NOW = "2026-09-04T12:00:00.000000Z"
LATER = "2026-09-04T13:00:00.000000Z"
COMMIT = "a" * 40
DIGEST = "b" * 64
ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
REASON = {"kind": "reason", "reason_code": "ELIGIBILITY_CHANGED", "detail_reference": None}
STATES = (
    "Planned",
    "Waiting",
    "Blocked",
    "Ready",
    "Dispatchable",
    "Leased",
    "Running",
    "AwaitingIntegration",
    "AwaitingReview",
    "MergeReady",
    "AwaitingArchitect",
    "AwaitingOwner",
    "Merged",
    "Complete",
    "NeedsReplan",
    "Cancelled",
)
ELIGIBILITY_STATES = STATES[:5]
COMPANION_STATES = STATES[5:15]
FORWARD_EDGES = {
    ("Planned", "Waiting"),
    ("Waiting", "Ready"),
    ("Ready", "Dispatchable"),
}
EDGES = {
    ("Planned", "Waiting"),
    ("Planned", "Blocked"),
    ("Planned", "Cancelled"),
    ("Waiting", "Ready"),
    ("Waiting", "Blocked"),
    ("Waiting", "Cancelled"),
    ("Blocked", "Waiting"),
    ("Blocked", "Ready"),
    ("Blocked", "Cancelled"),
    ("Ready", "Waiting"),
    ("Ready", "Blocked"),
    ("Ready", "Dispatchable"),
    ("Ready", "Cancelled"),
    ("Dispatchable", "Ready"),
    ("Dispatchable", "Waiting"),
    ("Dispatchable", "Blocked"),
    ("Dispatchable", "Cancelled"),
}


def state_payload(state: str, version: int) -> dict[str, object]:
    return {
        "entity_id": "packet-1",
        "entity_type": "Packet",
        "kind": "state",
        "state": state,
        "version": version,
    }


class PacketDatabase:
    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = Path(self._temporary.name) / "runtime"
        self.config = RuntimeConfig(self.path)
        self.store = OperationalStateStore(self.config)
        self.store.health()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO projects(project_id,repository_identity,default_branch,adapter_version,"
                "process_version,registration_state) VALUES (?,?,?,?,?,'Candidate')",
                ("project-1", "owner/repo", "main", "adapter-v1", "process-v1"),
            )
            connection.commit()
        self.store.record_binding(
            {
                "binding_id": "binding-1",
                "project_id": "project-1",
                "binding_revision": "revision-1",
                "source_commit": COMMIT,
                "manifest_digest": DIGEST,
                "adapter_version": "adapter-v1",
                "process_version": "process-v1",
                "authority_reference": "authority-1",
                "merge_policy": "no-automatic-merge",
                "acceptance_authority": "ProjectArchitect",
                "merge_execution_authority": "OwnerPerformed",
                "merge_delegation_reference": None,
                "binding_json": {"binding": "candidate"},
                "state": "Candidate",
                "activated_at": None,
                "superseded_at": None,
            },
            "seed-binding",
            ACTOR,
            NOW,
        )
        self.store.record_graph_projection(
            {
                "graph_projection_id": "graph-1",
                "project_id": "project-1",
                "binding_id": "binding-1",
                "graph_revision": "graph-r1",
                "authority_reference": "graph-authority",
                "source_base_sha": COMMIT,
                "source_hash": DIGEST,
                "state": "Active",
                "observed_at": NOW,
            },
            [
                {
                    "work_item_id": "work-1",
                    "graph_projection_id": "graph-1",
                    "architecture_node_id": "node-1",
                    "task_reference": "task-1",
                    "workstream_ref": "operational-core",
                    "milestone_ref": "M1",
                    "title": "Packet eligibility",
                    "priority": "P0",
                    "planned_rank": 1,
                    "specialist_role": "MaestroDeveloper",
                    "execution_classes_json": ["codex-cloud"],
                    "dependencies_json": [],
                    "change_domains_json": ["operational-state"],
                    "input_contract_json": {"version": 4},
                    "output_contract_json": {"version": 4},
                    "planning_state": "Active",
                }
            ],
            "seed-graph",
            ACTOR,
            NOW,
        )
        self.store.create_run(
            {
                "run_id": "run-1",
                "run_fingerprint": DIGEST,
                "project_id": "project-1",
                "binding_id": "binding-1",
                "graph_projection_id": "graph-1",
                "milestone_ref": "M1",
                "approved_authority_reference": "authority-1",
                "branch_name": None,
                "pull_request_reference": None,
                "current_head": None,
                "current_head_source_reference": None,
                "candidate_head": None,
                "candidate_head_source_reference": None,
                "state": "Planned",
                "acceptance_boundary": "ProjectArchitect",
            },
            "seed-run",
            ACTOR,
            NOW,
        )
        self.created = self.store.materialize_packet(
            {
                "packet_id": "packet-1",
                "run_id": "run-1",
                "work_item_id": "work-1",
                "packet_revision": "packet-r1",
                "authority_reference": "packet-authority",
                "base_commit": COMMIT,
                "current_head": None,
                "expected_branch": "implementation/packet-eligibility",
                "role_contract_reference": "role-1",
                "sop_reference": "sop-1",
                "executor_class": "codex-cloud",
                "integration_route": "validate-only",
                "reviewer_route": "independent",
                "owned_paths_json": ["services/maestro"],
                "forbidden_paths_json": ["live-project"],
                "checks_json": ["python", "unittest"],
                "resource_claims_json": ["shared:operational-state"],
                "context_policy_json": {
                    "minimum_context_tokens": 32768,
                    "output_reserve_tokens": 8192,
                    "warning_remaining_tokens": 16384,
                    "checkpoint_remaining_tokens": 12288,
                    "stop_remaining_tokens": 8192,
                },
                "state": "Planned",
                "correction_count": 0,
            },
            "seed-packet",
            ACTOR,
            NOW,
        )

    @property
    def database(self) -> Path:
        return self.path / "maestro.sqlite3"

    def force_source(self, state: str) -> None:
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "UPDATE packets SET state=?,version=1,updated_at=? WHERE packet_id='packet-1'",
                (state, NOW),
            )
            connection.commit()

    def state_events(self):
        return [
            event
            for event in self.store.events_after(0, 1000)
            if event["event_type"] == "PacketStateChanged"
        ]

    def companion_snapshot(self):
        with closing(sqlite3.connect(self.database)) as connection:
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' AND name NOT IN "
                    "('schema_versions','packets','events') ORDER BY name"
                )
            ]
            return {
                table: connection.execute(
                    f'SELECT * FROM "{table}" ORDER BY 1'
                ).fetchall()
                for table in tables
            }

    def close(self) -> None:
        self._temporary.cleanup()


class PacketEligibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = PacketDatabase()

    def tearDown(self) -> None:
        self.runtime.close()

    def transition(
        self,
        target: str,
        *,
        version: int = 1,
        key: str = "eligibility-1",
        reason=REASON,
        actor=ACTOR,
        now: str = NOW,
        packet_id: str = "packet-1",
    ):
        return self.runtime.store.transition_packet_eligibility(
            packet_id, version, target, reason, key, actor, now
        )

    def test_01_materialization_starts_planned_version_one(self) -> None:
        self.assertEqual(self.runtime.created["state"], "Planned")
        self.assertEqual(self.runtime.created["version"], 1)
        self.assertEqual(self.runtime.created["created_at"], NOW)
        self.assertEqual(self.runtime.created["updated_at"], NOW)
        self.assertEqual(
            self.runtime.store.snapshot("Packet", "packet-1"), self.runtime.created
        )
        self.assertEqual(self.runtime.state_events(), [])

    def test_02_each_forward_eligibility_edge_succeeds(self) -> None:
        path = ((1, "Waiting"), (2, "Ready"), (3, "Dispatchable"))
        observed = set()
        source = "Planned"
        for number, (version, target) in enumerate(path, 1):
            self.assertEqual(
                self.transition(target, version=version, key=f"forward-{number}"),
                state_payload(target, version + 1),
            )
            observed.add((source, target))
            source = target
        self.assertEqual(observed, FORWARD_EDGES)

    def test_03_each_fallback_block_and_cancel_edge_succeeds(self) -> None:
        remaining = EDGES - FORWARD_EDGES
        before_events = len(self.runtime.state_events())
        for number, (source, target) in enumerate(sorted(remaining), 1):
            self.runtime.force_source(source)
            self.assertEqual(
                self.transition(target, key=f"fallback-{number}"),
                state_payload(target, 2),
            )
            self.assertEqual(len(self.runtime.state_events()), before_events + number)
        self.assertEqual(len(remaining), 14)

    def test_04_all_256_source_target_pairs_match_exactly_seventeen_edges(self) -> None:
        observed = set()
        for number, (source, target) in enumerate(
            ((source, target) for source in STATES for target in STATES), 1
        ):
            self.runtime.force_source(source)
            before_events = len(self.runtime.state_events())
            if (source, target) in EDGES:
                self.assertEqual(
                    self.transition(target, key=f"pair-{number}"),
                    state_payload(target, 2),
                )
                self.assertEqual(len(self.runtime.state_events()), before_events + 1)
                observed.add((source, target))
            else:
                with self.subTest(source=source, target=target), self.assertRaises(InvalidTransition):
                    self.transition(target, key=f"pair-{number}")
                row = self.runtime.store.snapshot("Packet", "packet-1")
                self.assertEqual((row["state"], row["version"]), (source, 1))
                self.assertEqual(len(self.runtime.state_events()), before_events)
        self.assertEqual(observed, EDGES)
        self.assertEqual(len(observed), 17)

    def test_05_companion_evidence_states_are_unreachable(self) -> None:
        for source in COMPANION_STATES + ("Cancelled",):
            self.runtime.force_source(source)
            before_events = len(self.runtime.state_events())
            for target in STATES:
                with self.subTest(source=source, target=target), self.assertRaises(InvalidTransition):
                    self.transition(target, key=f"leave-{source}-{target}")
            row = self.runtime.store.snapshot("Packet", "packet-1")
            self.assertEqual((row["state"], row["version"]), (source, 1))
            self.assertEqual(len(self.runtime.state_events()), before_events)
        for source in ELIGIBILITY_STATES:
            self.runtime.force_source(source)
            for target in COMPANION_STATES:
                with self.subTest(source=source, target=target), self.assertRaises(InvalidTransition):
                    self.transition(target, key=f"enter-{source}-{target}")

    def test_06_stale_version_fails_without_mutation(self) -> None:
        before = self.runtime.store.snapshot("Packet", "packet-1")
        before_events = self.runtime.store.events_after(0, 1000)
        cases = (
            (StaleState, lambda: self.transition("Waiting", version=2)),
            (InvalidRecord, lambda: self.transition("Waiting", packet_id="")),
            (InvalidRecord, lambda: self.transition("Waiting", version=True)),
            (InvalidTransition, lambda: self.transition("Unknown")),
            (InvalidRecord, lambda: self.transition("Waiting", reason=state_payload("Planned", 1))),
            (InvalidRecord, lambda: self.transition("Waiting", key="")),
            (InvalidRecord, lambda: self.transition("Waiting", actor={"actor_type": "x"})),
            (InvalidRecord, lambda: self.transition("Waiting", now="later")),
        )
        for error_type, command in cases:
            with self.subTest(error=error_type.__name__), self.assertRaises(error_type):
                command()
            self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), before)
            self.assertEqual(self.runtime.store.events_after(0, 1000), before_events)

    def test_07_missing_packet_fails_without_event(self) -> None:
        before = self.runtime.store.events_after(0, 1000)
        with self.assertRaisesRegex(InvalidRecord, "^unknown packet$"):
            self.transition("Waiting", packet_id="missing-packet")
        self.assertEqual(self.runtime.store.events_after(0, 1000), before)

    def test_08_same_key_later_now_replay_is_exact_and_single_event(self) -> None:
        first = self.transition("Waiting", now=NOW)
        replay = self.transition("Waiting", now=LATER)
        self.assertEqual(replay, first)
        self.assertEqual(replay, state_payload("Waiting", 2))
        row = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"], row["updated_at"]), ("Waiting", 2, NOW))
        events = self.runtime.state_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["observed_at"], NOW)

    def test_09_every_immutable_command_field_change_conflicts(self) -> None:
        self.transition("Waiting", key="immutable-key")
        changed = (
            lambda: self.transition("Waiting", key="immutable-key", packet_id="other-packet"),
            lambda: self.transition("Waiting", key="immutable-key", version=2),
            lambda: self.transition("Blocked", key="immutable-key"),
            lambda: self.transition("Waiting", key="immutable-key", reason={**REASON, "reason_code": "OTHER"}),
            lambda: self.transition("Waiting", key="immutable-key", reason={**REASON, "detail_reference": "detail"}),
            lambda: self.transition("Waiting", key="immutable-key", actor=Actor("Other", "developer-1", "correlation-1")),
            lambda: self.transition("Waiting", key="immutable-key", actor=Actor("MaestroDeveloper", "other", "correlation-1")),
            lambda: self.transition("Waiting", key="immutable-key", actor=Actor("MaestroDeveloper", "developer-1", "other")),
            lambda: self.transition("Waiting", key="immutable-key", actor=Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)),
        )
        for command in changed:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.state_events()), 1)
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1")["version"], 2)

    def test_10_documented_fingerprint_and_exact_event_are_independently_reconstructed(self) -> None:
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        after = self.transition("Waiting", actor=actor)
        documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 1,
                "correlation_id": "correlation-1",
            },
            "operation": "transition_packet_eligibility",
            "payload": {
                "expected_version": 1,
                "packet_id": "packet-1",
                "reason": REASON,
                "target_state": "Waiting",
            },
        }
        encoded = json.dumps(
            documented,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        events = self.runtime.state_events()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(event["entity_type"], "Packet")
        self.assertEqual(event["entity_id"], "packet-1")
        self.assertEqual(event["event_type"], "PacketStateChanged")
        self.assertEqual(event["before_json"], state_payload("Planned", 1))
        self.assertEqual(event["after_json"], after)
        self.assertEqual(json.loads(event["reason"]), REASON)
        self.assertEqual(event["actor_type"], "MaestroDeveloper")
        self.assertEqual(event["actor_id"], "developer-1")
        self.assertEqual(event["correlation_id"], "correlation-1")
        self.assertEqual(event["causation_event_id"], 1)
        self.assertEqual(event["observed_at"], NOW)

    def test_11_forced_event_failure_rolls_back_packet_and_event(self) -> None:
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "CREATE TRIGGER force_packet_event_failure BEFORE INSERT ON events "
                "WHEN NEW.event_type='PacketStateChanged' BEGIN SELECT RAISE(ABORT,'forced'); END"
            )
            connection.commit()
        before = self.runtime.store.snapshot("Packet", "packet-1")
        before_events = self.runtime.store.events_after(0, 1000)
        with self.assertRaisesRegex(
            InvalidRecord, "^packet eligibility transition violates a durable constraint$"
        ):
            self.transition("Waiting")
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), before)
        self.assertEqual(self.runtime.store.events_after(0, 1000), before_events)

    def test_12_simultaneous_transitions_from_one_version_have_one_winner(self) -> None:
        barrier = threading.Barrier(2)

        def command(target: str):
            store = OperationalStateStore(self.runtime.config)
            barrier.wait()
            try:
                return store.transition_packet_eligibility(
                    "packet-1", 1, target, REASON, f"concurrent-{target}", ACTOR, NOW
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(command, ("Waiting", "Blocked")))
        winners = [result for result in results if isinstance(result, dict)]
        stale = [result for result in results if isinstance(result, StaleState)]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(stale), 1)
        row = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), (winners[0]["state"], 2))
        self.assertEqual(len(self.runtime.state_events()), 1)

    def test_13_restart_preserves_state_version_event_and_exact_replay(self) -> None:
        first = self.transition("Waiting")
        original_events = self.runtime.state_events()
        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("Waiting", 2))
        replay = reopened.transition_packet_eligibility(
            "packet-1", 1, "Waiting", REASON, "eligibility-1", ACTOR, LATER
        )
        self.assertEqual(replay, first)
        self.assertEqual(self.runtime.state_events(), original_events)

    def test_14_success_and_rejection_leave_all_companion_tables_unchanged(self) -> None:
        companions = self.runtime.companion_snapshot()
        self.transition("Waiting", key="companion-success")
        self.assertEqual(self.runtime.companion_snapshot(), companions)
        packet_before = self.runtime.store.snapshot("Packet", "packet-1")
        events_before = self.runtime.store.events_after(0, 1000)
        with self.assertRaises(InvalidTransition):
            self.transition("Leased", version=2, key="companion-rejection")
        self.assertEqual(self.runtime.companion_snapshot(), companions)
        self.assertEqual(self.runtime.store.snapshot("Packet", "packet-1"), packet_before)
        self.assertEqual(self.runtime.store.events_after(0, 1000), events_before)


if __name__ == "__main__":
    unittest.main()
