from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    StaleState,
)


NOW = "2026-09-03T12:00:00.000000Z"
LATER = "2026-09-03T13:00:00.000000Z"
COMMIT = "a" * 40
DIGEST = "b" * 64
ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
REASON = {"kind": "reason", "reason_code": "WORK_STARTED", "detail_reference": None}
STATES = (
    "Planned",
    "Running",
    "Blocked",
    "AwaitingArchitect",
    "AwaitingOwner",
    "Complete",
    "Cancelled",
)
EDGES = {
    ("Planned", "Running"),
    ("Planned", "Blocked"),
    ("Planned", "Cancelled"),
    ("Running", "Blocked"),
    ("Running", "AwaitingArchitect"),
    ("Running", "AwaitingOwner"),
    ("Running", "Complete"),
    ("Running", "Cancelled"),
    ("Blocked", "Running"),
    ("Blocked", "AwaitingArchitect"),
    ("Blocked", "AwaitingOwner"),
    ("Blocked", "Cancelled"),
    ("AwaitingArchitect", "Running"),
    ("AwaitingArchitect", "Blocked"),
    ("AwaitingArchitect", "AwaitingOwner"),
    ("AwaitingArchitect", "Cancelled"),
    ("AwaitingOwner", "Running"),
    ("AwaitingOwner", "Blocked"),
    ("AwaitingOwner", "Complete"),
    ("AwaitingOwner", "Cancelled"),
}


def state_payload(state: str, version: int) -> dict[str, object]:
    return {
        "entity_id": "run-1",
        "entity_type": "Run",
        "kind": "state",
        "state": state,
        "version": version,
    }


class LifecycleDatabase:
    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = DEFAULT_RUNTIME_DIR / self._temporary.name.rsplit("/", 1)[-1] / "runtime"
        self.config = RuntimeConfig(self.path)
        self.store = OperationalStateStore(self.config)
        self.store.health()
        with closing(sqlite3.connect(self.path / "maestro.sqlite3")) as connection:
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
            [],
            "seed-graph",
            ACTOR,
            NOW,
        )
        self.created = self.store.create_run(
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

    @property
    def database(self):
        return self.path / "maestro.sqlite3"

    def force_source(self, state: str) -> None:
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "UPDATE runs SET state=?,version=1,updated_at=? WHERE run_id='run-1'",
                (state, NOW),
            )
            connection.commit()

    def state_events(self):
        return [
            event
            for event in self.store.events_after(0, 1000)
            if event["event_type"] == "RunStateChanged"
        ]

    def close(self) -> None:
        self._temporary.cleanup()


class RunLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = LifecycleDatabase()

    def tearDown(self) -> None:
        self.runtime.close()

    def transition(
        self,
        target: str,
        *,
        version: int = 1,
        key: str = "transition-1",
        reason=REASON,
        actor=ACTOR,
        now: str = NOW,
        run_id: str = "run-1",
    ):
        return self.runtime.store.transition_run(
            run_id, version, target, reason, key, actor, now
        )

    def test_01_accepted_creation_is_planned_version_one(self) -> None:
        self.assertEqual(self.runtime.created["state"], "Planned")
        self.assertEqual(self.runtime.created["version"], 1)
        self.assertEqual(self.runtime.created["created_at"], NOW)
        self.assertEqual(self.runtime.created["updated_at"], NOW)
        self.assertEqual(self.runtime.store.snapshot("Run", "run-1"), self.runtime.created)
        self.assertEqual(self.runtime.state_events(), [])

    def test_02_planned_to_running_succeeds(self) -> None:
        result = self.transition("Running")
        self.assertEqual(result, state_payload("Running", 2))
        row = self.runtime.store.snapshot("Run", "run-1")
        self.assertEqual((row["state"], row["version"], row["updated_at"]), ("Running", 2, NOW))
        self.assertEqual(len(self.runtime.state_events()), 1)

    def test_03_running_to_complete_succeeds(self) -> None:
        self.runtime.force_source("Running")
        self.assertEqual(self.transition("Complete"), state_payload("Complete", 2))

    def test_04_blocked_and_authority_wait_paths_resume_only_on_listed_edges(self) -> None:
        versions_and_targets = (
            (1, "Running"),
            (2, "Blocked"),
            (3, "AwaitingArchitect"),
            (4, "AwaitingOwner"),
            (5, "Running"),
        )
        for number, (version, target) in enumerate(versions_and_targets, 1):
            self.assertEqual(
                self.transition(target, version=version, key=f"resume-{number}"),
                state_payload(target, version + 1),
            )
        self.assertEqual(len(self.runtime.state_events()), 5)

    def test_05_complete_and_cancelled_are_terminal(self) -> None:
        for source in ("Complete", "Cancelled"):
            self.runtime.close()
            self.runtime = LifecycleDatabase()
            self.runtime.force_source(source)
            for target in STATES:
                with self.subTest(source=source, target=target), self.assertRaises(InvalidTransition):
                    self.transition(target, key=f"terminal-{source}-{target}")
            row = self.runtime.store.snapshot("Run", "run-1")
            self.assertEqual((row["state"], row["version"]), (source, 1))
            self.assertEqual(self.runtime.state_events(), [])

    def test_06_all_49_source_target_pairs_match_the_closed_graph(self) -> None:
        observed: set[tuple[str, str]] = set()
        for source in STATES:
            for target in STATES:
                self.runtime.close()
                self.runtime = LifecycleDatabase()
                self.runtime.force_source(source)
                pair = (source, target)
                if pair in EDGES:
                    self.assertEqual(
                        self.transition(target, key=f"pair-{source}-{target}"),
                        state_payload(target, 2),
                    )
                    self.assertEqual(len(self.runtime.state_events()), 1)
                    observed.add(pair)
                else:
                    with self.subTest(source=source, target=target), self.assertRaises(InvalidTransition):
                        self.transition(target, key=f"pair-{source}-{target}")
                    row = self.runtime.store.snapshot("Run", "run-1")
                    self.assertEqual((row["state"], row["version"]), (source, 1))
                    self.assertEqual(self.runtime.state_events(), [])
        self.assertEqual(observed, EDGES)
        self.assertEqual(len(observed), 20)

    def test_07_stale_version_and_invalid_inputs_do_not_mutate(self) -> None:
        before = self.runtime.store.snapshot("Run", "run-1")
        before_events = self.runtime.store.events_after(0, 1000)
        cases = (
            (StaleState, lambda: self.transition("Running", version=2)),
            (InvalidRecord, lambda: self.transition("Running", run_id="")),
            (InvalidRecord, lambda: self.transition("Running", version=True)),
            (InvalidTransition, lambda: self.transition("Unknown")),
            (InvalidRecord, lambda: self.transition("Running", reason=state_payload("Planned", 1))),
            (InvalidRecord, lambda: self.transition("Running", key="")),
            (InvalidRecord, lambda: self.transition("Running", actor={"actor_type": "x"})),
            (InvalidRecord, lambda: self.transition("Running", now="later")),
        )
        for error, command in cases:
            with self.subTest(error=error.__name__), self.assertRaises(error):
                command()
            self.assertEqual(self.runtime.store.snapshot("Run", "run-1"), before)
            self.assertEqual(self.runtime.store.events_after(0, 1000), before_events)

    def test_08_missing_run_is_rejected_without_event(self) -> None:
        before = self.runtime.store.events_after(0, 1000)
        with self.assertRaisesRegex(InvalidRecord, "^unknown run$"):
            self.transition("Running", run_id="missing-run")
        self.assertEqual(self.runtime.store.events_after(0, 1000), before)

    def test_09_same_command_replay_retains_original_result_and_time_once(self) -> None:
        first = self.transition("Running", now=NOW)
        replay = self.transition("Running", now=LATER)
        self.assertEqual(replay, first)
        self.assertEqual(replay, state_payload("Running", 2))
        row = self.runtime.store.snapshot("Run", "run-1")
        self.assertEqual((row["state"], row["version"], row["updated_at"]), ("Running", 2, NOW))
        events = self.runtime.state_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["observed_at"], NOW)

    def test_10_changed_immutable_command_facts_conflict(self) -> None:
        self.transition("Running", key="immutable-key")
        changed_cases = (
            lambda: self.transition("Running", key="immutable-key", run_id="other-run"),
            lambda: self.transition("Running", key="immutable-key", version=2),
            lambda: self.transition("Blocked", key="immutable-key"),
            lambda: self.transition("Running", key="immutable-key", reason={**REASON, "reason_code": "OTHER"}),
            lambda: self.transition("Running", key="immutable-key", reason={**REASON, "detail_reference": "detail"}),
            lambda: self.transition("Running", key="immutable-key", actor=Actor("Other", "developer-1", "correlation-1")),
            lambda: self.transition("Running", key="immutable-key", actor=Actor("MaestroDeveloper", "other", "correlation-1")),
            lambda: self.transition("Running", key="immutable-key", actor=Actor("MaestroDeveloper", "developer-1", "other")),
            lambda: self.transition("Running", key="immutable-key", actor=Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)),
        )
        for command in changed_cases:
            with self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.state_events()), 1)
        self.assertEqual(self.runtime.store.snapshot("Run", "run-1")["version"], 2)

    def test_11_documented_fingerprint_and_exact_event_are_independently_reconstructed(self) -> None:
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        after = self.transition("Running", actor=actor)
        documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 1,
                "correlation_id": "correlation-1",
            },
            "operation": "transition_run",
            "payload": {
                "expected_version": 1,
                "reason": REASON,
                "run_id": "run-1",
                "target_state": "Running",
            },
        }
        encoded = json.dumps(
            documented,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        expected_digest = hashlib.sha256(encoded).hexdigest()
        events = self.runtime.state_events()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["command_fingerprint"], expected_digest)
        self.assertEqual(event["entity_type"], "Run")
        self.assertEqual(event["entity_id"], "run-1")
        self.assertEqual(event["event_type"], "RunStateChanged")
        self.assertEqual(event["before_json"], state_payload("Planned", 1))
        self.assertEqual(event["after_json"], after)
        self.assertEqual(json.loads(event["reason"]), REASON)
        self.assertEqual(event["actor_type"], "MaestroDeveloper")
        self.assertEqual(event["actor_id"], "developer-1")
        self.assertEqual(event["correlation_id"], "correlation-1")
        self.assertEqual(event["causation_event_id"], 1)
        self.assertEqual(event["observed_at"], NOW)

    def test_12_event_insert_failure_rolls_back_run_and_event(self) -> None:
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute(
                "CREATE TRIGGER force_run_event_failure BEFORE INSERT ON events "
                "WHEN NEW.event_type='RunStateChanged' BEGIN SELECT RAISE(ABORT,'forced'); END"
            )
            connection.commit()
        before = self.runtime.store.snapshot("Run", "run-1")
        before_events = self.runtime.store.events_after(0, 1000)
        with self.assertRaisesRegex(InvalidRecord, "^run transition violates a durable constraint$"):
            self.transition("Running")
        self.assertEqual(self.runtime.store.snapshot("Run", "run-1"), before)
        self.assertEqual(self.runtime.store.events_after(0, 1000), before_events)

    def test_13_two_concurrent_commands_have_one_winner_and_one_stale_result(self) -> None:
        barrier = threading.Barrier(2)

        def command(target: str):
            store = OperationalStateStore(self.runtime.config)
            barrier.wait()
            try:
                return store.transition_run(
                    "run-1", 1, target, REASON, f"concurrent-{target}", ACTOR, NOW
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(command, ("Running", "Blocked")))
        winners = [result for result in results if isinstance(result, dict)]
        stale = [result for result in results if isinstance(result, StaleState)]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(stale), 1)
        row = self.runtime.store.snapshot("Run", "run-1")
        self.assertEqual(row["version"], 2)
        self.assertEqual(row["state"], winners[0]["state"])
        self.assertEqual(len(self.runtime.state_events()), 1)

    def test_14_restart_preserves_state_event_and_nonduplicating_replay(self) -> None:
        first = self.transition("Running")
        original_events = self.runtime.state_events()
        reopened = OperationalStateStore(self.runtime.config)
        self.assertEqual(reopened.snapshot("Run", "run-1")["state"], "Running")
        replay = reopened.transition_run(
            "run-1", 1, "Running", REASON, "transition-1", ACTOR, LATER
        )
        self.assertEqual(replay, first)
        self.assertEqual(reopened.snapshot("Run", "run-1")["version"], 2)
        self.assertEqual(self.runtime.state_events(), original_events)


if __name__ == "__main__":
    unittest.main()
