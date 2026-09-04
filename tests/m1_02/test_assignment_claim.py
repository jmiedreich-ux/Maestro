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


NOW = "2026-09-04T12:00:00.000000Z"
LATER = "2026-09-04T13:00:00.000000Z"
AFTER_EXPIRY = "2026-09-04T14:00:00.000000Z"
COMMIT = "a" * 40
DIGEST = "b" * 64
ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
REASON = {
    "kind": "reason",
    "reason_code": "ASSIGNMENT_CLAIMED",
    "detail_reference": None,
}
RESOURCES = [
    "finite:gpu",
    "path:services/maestro",
    "shared:operational-state",
]
LOCKS = [
    {"lock_id": "lock-z", "lock_kind": "FiniteResource", "resource_key": RESOURCES[0]},
    {"lock_id": "lock-a", "lock_kind": "Path", "resource_key": RESOURCES[1]},
    {"lock_id": "lock-m", "lock_kind": "SharedBoundary", "resource_key": RESOURCES[2]},
]
LEASE = {
    "executor_route": "codex-cloud/developer-1",
    "expires_at": LATER,
    "holder_id": "developer-1",
    "lease_id": "lease-1",
    "worktree_path": "/runtime/worktree-1",
}
ATTEMPT = {
    "attempt_id": "attempt-1",
    "model_identity": "gpt-5.6",
    "runtime_identity": "codex-runtime-1",
}


def state_payload(entity_type: str, entity_id: str, state: str, version: int):
    return {
        "entity_id": entity_id,
        "entity_type": entity_type,
        "kind": "state",
        "state": state,
        "version": version,
    }


def expected_result(packet_id="packet-1", lease_id="lease-1", attempt_id="attempt-1", locks=LOCKS):
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
        "packet": state_payload("Packet", packet_id, "Leased", 5),
    }


class AssignmentDatabase:
    def __init__(self, resources=RESOURCES):
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
        work_items = []
        for number in range(1, 4):
            work_items.append(
                {
                    "work_item_id": f"work-{number}",
                    "graph_projection_id": "graph-1",
                    "architecture_node_id": f"node-{number}",
                    "task_reference": f"task-{number}",
                    "workstream_ref": "operational-core",
                    "milestone_ref": "M1",
                    "title": f"Assignment claim {number}",
                    "priority": "P0",
                    "planned_rank": number,
                    "specialist_role": "MaestroDeveloper",
                    "execution_classes_json": ["codex-cloud"],
                    "dependencies_json": [],
                    "change_domains_json": ["operational-state"],
                    "input_contract_json": {"version": 4},
                    "output_contract_json": {"version": 4},
                    "planning_state": "Active",
                }
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
            work_items,
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
        self.store.transition_run("run-1", 1, "Running", REASON, "start-run", ACTOR, NOW)
        self.add_packet("packet-1", "work-1", resources)

    @property
    def database(self):
        return self.path / "maestro.sqlite3"

    def add_packet(self, packet_id, work_item_id, resources):
        self.store.materialize_packet(
            {
                "packet_id": packet_id,
                "run_id": "run-1",
                "work_item_id": work_item_id,
                "packet_revision": f"revision-{packet_id}",
                "authority_reference": "packet-authority",
                "base_commit": COMMIT,
                "current_head": None,
                "expected_branch": f"implementation/{packet_id}",
                "role_contract_reference": "role-1",
                "sop_reference": "sop-1",
                "executor_class": "codex-cloud",
                "integration_route": "validate-only",
                "reviewer_route": "independent",
                "owned_paths_json": ["services/maestro"],
                "forbidden_paths_json": ["live-project"],
                "checks_json": ["python", "unittest"],
                "resource_claims_json": list(resources),
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
            f"materialize-{packet_id}",
            ACTOR,
            NOW,
        )
        for version, target in ((1, "Waiting"), (2, "Ready"), (3, "Dispatchable")):
            self.store.transition_packet_eligibility(
                packet_id, version, target, REASON,
                f"eligibility-{packet_id}-{version}", ACTOR, NOW,
            )

    def claim(
        self,
        *,
        packet_id="packet-1",
        version=4,
        lease=LEASE,
        locks=LOCKS,
        attempt=ATTEMPT,
        reason=REASON,
        key="claim-1",
        actor=ACTOR,
        now=NOW,
    ):
        return self.store.claim_packet_assignment(
            packet_id, version, lease, locks, attempt, reason, key, actor, now
        )

    def rows(self, table):
        with closing(sqlite3.connect(self.database)) as connection:
            cursor = connection.execute(f'SELECT * FROM "{table}" ORDER BY 1')
            columns = [item[0] for item in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def claim_events(self):
        return [
            event for event in self.store.events_after(0, 1000)
            if event["event_type"] == "PacketClaimed"
        ]

    def claim_state(self):
        return {
            "packet": self.store.snapshot("Packet", "packet-1"),
            "leases": self.rows("leases"),
            "locks": self.rows("resource_locks"),
            "attempts": self.rows("attempts"),
            "events": self.claim_events(),
        }

    def insert_lease(
        self, lease_id, packet_id, worktree_path, *, state="Active", claim_key=None
    ):
        claim_key = claim_key or f"raw-{lease_id}"
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO leases(lease_id,packet_id,run_id,claim_key,run_fingerprint,"
                "base_commit,worktree_path,executor_route,holder_id,state,acquired_at,"
                "expires_at,heartbeat_at,released_at,version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
                (
                    lease_id, packet_id, "run-1", claim_key, DIGEST, COMMIT, worktree_path,
                    "raw-route", "raw-holder", state, NOW, LATER, NOW,
                    NOW if state != "Active" else None,
                ),
            )
            connection.commit()

    def insert_lock(self, lock_id, resource_key, lease_id, packet_id, state="Active"):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO resource_locks(lock_id,resource_key,lock_kind,packet_id,lease_id,"
                "state,acquired_at,expires_at,released_at,version) VALUES (?,?,?,?,?,?,?,?,?,1)",
                (
                    lock_id, resource_key, "SharedBoundary", packet_id, lease_id,
                    state, NOW, LATER, NOW if state != "Active" else None,
                ),
            )
            connection.commit()

    def insert_attempt(self, attempt_id, packet_id, lease_id):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO attempts(attempt_id,packet_id,lease_id,attempt_number,attempt_kind,"
                "executor_class,model_identity,runtime_identity,state,result_commit,"
                "correction_for_review_id,started_at,finished_at,created_at,updated_at,version) "
                "VALUES (?,?,?,1,'Initial','codex-cloud','model','runtime','Planned',"
                "NULL,NULL,NULL,NULL,?,?,1)",
                (attempt_id, packet_id, lease_id, NOW, NOW),
            )
            connection.commit()

    def close(self):
        self._temporary.cleanup()


class AssignmentClaimTests(unittest.TestCase):
    def setUp(self):
        self.runtime = AssignmentDatabase()

    def tearDown(self):
        self.runtime.close()

    def replace_runtime(self, resources=RESOURCES):
        self.runtime.close()
        self.runtime = AssignmentDatabase(resources)

    def assert_no_claim_mutation(self, before):
        self.assertEqual(self.runtime.claim_state(), before)

    def test_01_valid_claim_atomically_creates_exact_compound_result(self):
        result = self.runtime.claim()
        self.assertEqual(result, expected_result())
        packet = self.runtime.store.snapshot("Packet", "packet-1")
        self.assertEqual((packet["state"], packet["version"], packet["updated_at"]), ("Leased", 5, NOW))
        self.assertEqual(len(self.runtime.rows("leases")), 1)
        self.assertEqual(len(self.runtime.rows("resource_locks")), 3)
        self.assertEqual(len(self.runtime.rows("attempts")), 1)
        events = self.runtime.claim_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["after_json"], result)
        self.assertEqual(
            [event["event_type"] for event in self.runtime.store.events_after(0, 1000)].count("PacketStateChanged"),
            3,
        )
        self.assertNotIn("AttemptRecorded", [event["event_type"] for event in self.runtime.store.events_after(0, 1000)])

    def test_02_empty_declared_lock_set_creates_no_locks(self):
        self.replace_runtime([])
        result = self.runtime.claim(locks=[])
        self.assertEqual(result, expected_result(locks=[]))
        self.assertEqual(self.runtime.rows("resource_locks"), [])

    def test_03_run_fingerprint_base_run_id_and_executor_facts_are_derived(self):
        self.runtime.claim()
        lease = self.runtime.store.snapshot("Lease", "lease-1")
        attempt = self.runtime.store.snapshot("Attempt", "attempt-1")
        self.assertEqual(
            (lease["run_id"], lease["run_fingerprint"], lease["base_commit"], lease["claim_key"]),
            ("run-1", DIGEST, COMMIT, "claim-1"),
        )
        self.assertEqual(
            (attempt["packet_id"], attempt["lease_id"], attempt["attempt_number"], attempt["attempt_kind"], attempt["executor_class"]),
            ("packet-1", "lease-1", 1, "Initial", "codex-cloud"),
        )
        self.assertEqual(
            (attempt["state"], attempt["started_at"], attempt["finished_at"], attempt["result_commit"], attempt["correction_for_review_id"]),
            ("Planned", None, None, None, None),
        )

    def test_04_closed_inputs_follow_deterministic_first_error_precedence(self):
        before = self.runtime.claim_state()
        cases = (
            ("packet_id", lambda: self.runtime.claim(packet_id="", version=False, lease={})),
            ("expected_version", lambda: self.runtime.claim(version=False, lease={})),
            ("assignment lease request", lambda: self.runtime.claim(lease={}, locks="bad", attempt={})),
            ("executor_route", lambda: self.runtime.claim(lease={**LEASE, "executor_route": ""})),
            ("lock_requests", lambda: self.runtime.claim(locks=tuple(LOCKS))),
            ("lock_kind", lambda: self.runtime.claim(locks=[{**LOCKS[0], "lock_kind": "Unknown"}])),
            ("sorted and unique", lambda: self.runtime.claim(locks=list(reversed(LOCKS)))),
            ("lock IDs", lambda: self.runtime.claim(locks=[LOCKS[0], {**LOCKS[1], "lock_id": "lock-z"}, LOCKS[2]])),
            ("assignment attempt request", lambda: self.runtime.claim(attempt={})),
            ("model_identity", lambda: self.runtime.claim(attempt={**ATTEMPT, "model_identity": ""})),
            ("reason payload", lambda: self.runtime.claim(reason=state_payload("Packet", "packet-1", "Dispatchable", 4))),
            ("idempotency_key", lambda: self.runtime.claim(key="")),
            ("actor", lambda: self.runtime.claim(actor={"actor_type": "x"})),
            ("now", lambda: self.runtime.claim(now="later")),
        )
        for message, command in cases:
            with self.subTest(message=message), self.assertRaisesRegex(InvalidRecord, message):
                command()
            self.assert_no_claim_mutation(before)

    def test_05_requested_locks_exactly_cover_declared_resources(self):
        before = self.runtime.claim_state()
        cases = (
            LOCKS[:-1],
            LOCKS + [{"lock_id": "lock-x", "lock_kind": "Path", "resource_key": "zz:extra"}],
            [{**LOCKS[0], "resource_key": "finite:other"}, *LOCKS[1:]],
        )
        for number, locks in enumerate(cases, 1):
            with self.subTest(case=number), self.assertRaisesRegex(InvalidRecord, "exactly cover"):
                self.runtime.claim(locks=locks, key=f"coverage-{number}")
            self.assert_no_claim_mutation(before)

    def test_06_new_expiry_follows_observation_while_late_exact_replay_succeeds(self):
        before = self.runtime.claim_state()
        with self.assertRaisesRegex(InvalidRecord, "expiry must follow"):
            self.runtime.claim(lease={**LEASE, "expires_at": NOW})
        self.assert_no_claim_mutation(before)
        first = self.runtime.claim()
        replay = self.runtime.claim(now=AFTER_EXPIRY)
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.claim_events()), 1)
        self.assertEqual(self.runtime.claim_events()[0]["observed_at"], NOW)

    def test_07_missing_stale_nondispatchable_and_nonrunning_precedence_is_exact(self):
        with self.assertRaisesRegex(InvalidRecord, "^unknown packet$"):
            self.runtime.claim(packet_id="missing")
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute("UPDATE packets SET state='Ready' WHERE packet_id='packet-1'")
            connection.commit()
        with self.assertRaisesRegex(StaleState, "stale"):
            self.runtime.claim(version=3)
        with self.assertRaisesRegex(InvalidTransition, "Dispatchable"):
            self.runtime.claim()
        with closing(sqlite3.connect(self.runtime.database)) as connection:
            connection.execute("UPDATE packets SET state='Dispatchable' WHERE packet_id='packet-1'")
            connection.execute("UPDATE runs SET state='Blocked' WHERE run_id='run-1'")
            connection.commit()
        with self.assertRaisesRegex(InvalidTransition, "Running run"):
            self.runtime.claim()
        self.assertEqual(self.runtime.claim_events(), [])

    def test_08_active_packet_lease_conflict_makes_no_mutation(self):
        self.runtime.insert_lease("lease-existing", "packet-1", "/runtime/existing")
        before = self.runtime.claim_state()
        with self.assertRaisesRegex(ResourceConflict, "packet"):
            self.runtime.claim()
        self.assert_no_claim_mutation(before)

    def test_09_active_worktree_conflict_makes_no_mutation(self):
        self.runtime.add_packet("packet-2", "work-2", [])
        self.runtime.insert_lease("lease-existing", "packet-2", LEASE["worktree_path"])
        before = self.runtime.claim_state()
        with self.assertRaisesRegex(ResourceConflict, "worktree"):
            self.runtime.claim()
        self.assert_no_claim_mutation(before)

    def test_10_active_resource_conflicts_while_released_and_expired_do_not(self):
        self.runtime.add_packet("packet-2", "work-2", [])
        self.runtime.insert_lease("lease-existing", "packet-2", "/runtime/existing")
        self.runtime.insert_lock("lock-existing", RESOURCES[2], "lease-existing", "packet-2")
        before = self.runtime.claim_state()
        with self.assertRaisesRegex(ResourceConflict, RESOURCES[2]):
            self.runtime.claim()
        self.assert_no_claim_mutation(before)

        for state in ("Released", "Expired"):
            self.replace_runtime()
            self.runtime.add_packet("packet-2", "work-2", [])
            self.runtime.insert_lease("lease-existing", "packet-2", "/runtime/existing", state="Released")
            self.runtime.insert_lock("lock-existing", RESOURCES[2], "lease-existing", "packet-2", state=state)
            self.assertEqual(self.runtime.claim(), expected_result())

    def test_11_reused_ids_and_existing_initial_attempt_are_rejected(self):
        cases = ("lease-id", "claim-key", "lock-id", "attempt-id", "initial-attempt")
        for case in cases:
            with self.subTest(case=case):
                self.replace_runtime()
                self.runtime.add_packet("packet-2", "work-2", [])
                if case in {"lease-id", "claim-key"}:
                    self.runtime.insert_lease(
                        "lease-1" if case == "lease-id" else "lease-existing",
                        "packet-2",
                        "/runtime/existing",
                        state="Released",
                        claim_key="claim-1" if case == "claim-key" else None,
                    )
                elif case == "lock-id":
                    self.runtime.insert_lease("lease-existing", "packet-2", "/runtime/existing", state="Released")
                    self.runtime.insert_lock("lock-a", "old:resource", "lease-existing", "packet-2", state="Released")
                else:
                    self.runtime.insert_lease("lease-existing", "packet-1", "/runtime/existing", state="Released")
                    self.runtime.insert_attempt(
                        "attempt-1" if case == "attempt-id" else "attempt-existing",
                        "packet-1",
                        "lease-existing",
                    )
                before = self.runtime.claim_state()
                with self.assertRaises(InvalidRecord):
                    self.runtime.claim()
                self.assert_no_claim_mutation(before)

    def test_12_same_key_same_command_replays_exactly_once(self):
        first = self.runtime.claim()
        replay = self.runtime.claim(now="2026-09-04T12:30:00.000000Z")
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.rows("leases")), 1)
        self.assertEqual(len(self.runtime.rows("resource_locks")), 3)
        self.assertEqual(len(self.runtime.rows("attempts")), 1)
        self.assertEqual(len(self.runtime.claim_events()), 1)

    def test_13_every_changed_immutable_command_fact_conflicts(self):
        self.runtime.claim(key="immutable-key")
        changed = (
            lambda: self.runtime.claim(key="immutable-key", packet_id="other"),
            lambda: self.runtime.claim(key="immutable-key", version=5),
            lambda: self.runtime.claim(key="immutable-key", lease={**LEASE, "executor_route": "other"}),
            lambda: self.runtime.claim(key="immutable-key", lease={**LEASE, "expires_at": AFTER_EXPIRY}),
            lambda: self.runtime.claim(key="immutable-key", lease={**LEASE, "holder_id": "other"}),
            lambda: self.runtime.claim(key="immutable-key", lease={**LEASE, "lease_id": "other"}),
            lambda: self.runtime.claim(key="immutable-key", lease={**LEASE, "worktree_path": "/other"}),
            lambda: self.runtime.claim(key="immutable-key", locks=[{**LOCKS[0], "lock_id": "other"}, *LOCKS[1:]]),
            lambda: self.runtime.claim(key="immutable-key", locks=[{**LOCKS[0], "lock_kind": "Path"}, *LOCKS[1:]]),
            lambda: self.runtime.claim(key="immutable-key", locks=[{**LOCKS[0], "resource_key": "finite:other"}, *LOCKS[1:]]),
            lambda: self.runtime.claim(key="immutable-key", attempt={**ATTEMPT, "attempt_id": "other"}),
            lambda: self.runtime.claim(key="immutable-key", attempt={**ATTEMPT, "model_identity": "other"}),
            lambda: self.runtime.claim(key="immutable-key", attempt={**ATTEMPT, "runtime_identity": "other"}),
            lambda: self.runtime.claim(key="immutable-key", reason={**REASON, "reason_code": "OTHER"}),
            lambda: self.runtime.claim(key="immutable-key", reason={**REASON, "detail_reference": "other"}),
            lambda: self.runtime.claim(key="immutable-key", actor=Actor("Other", "developer-1", "correlation-1")),
            lambda: self.runtime.claim(key="immutable-key", actor=Actor("MaestroDeveloper", "other", "correlation-1")),
            lambda: self.runtime.claim(key="immutable-key", actor=Actor("MaestroDeveloper", "developer-1", "other")),
            lambda: self.runtime.claim(key="immutable-key", actor=Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)),
        )
        for number, command in enumerate(changed, 1):
            with self.subTest(case=number), self.assertRaises(IdempotencyConflict):
                command()
        self.assertEqual(len(self.runtime.claim_events()), 1)

    def test_14_independent_fingerprint_and_exact_packet_claimed_event_match(self):
        actor = Actor("MaestroDeveloper", "developer-1", "correlation-1", 1)
        result = self.runtime.claim(actor=actor)
        documented = {
            "actor": {
                "actor_id": "developer-1",
                "actor_type": "MaestroDeveloper",
                "causation_event_id": 1,
                "correlation_id": "correlation-1",
            },
            "operation": "claim_packet_assignment",
            "payload": {
                "attempt": ATTEMPT,
                "expected_version": 4,
                "lease": LEASE,
                "locks": LOCKS,
                "packet_id": "packet-1",
                "reason": REASON,
            },
        }
        encoded = json.dumps(
            documented, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        event = self.runtime.claim_events()[0]
        self.assertEqual(event["command_fingerprint"], hashlib.sha256(encoded).hexdigest())
        self.assertEqual(event["entity_type"], "Packet")
        self.assertEqual(event["entity_id"], "packet-1")
        self.assertEqual(event["event_type"], "PacketClaimed")
        self.assertEqual(event["before_json"], state_payload("Packet", "packet-1", "Dispatchable", 4))
        self.assertEqual(event["after_json"], result)
        self.assertEqual(json.loads(event["reason"]), REASON)
        self.assertEqual(
            (event["actor_type"], event["actor_id"], event["correlation_id"], event["causation_event_id"], event["observed_at"]),
            ("MaestroDeveloper", "developer-1", "correlation-1", 1, NOW),
        )

    def test_15_event_failure_rolls_back_packet_lease_locks_and_attempt(self):
        before = self.runtime.claim_state()
        with mock.patch.object(
            self.runtime.store, "_insert_packet_claim_event", side_effect=RuntimeError("event failure")
        ):
            with self.assertRaisesRegex(RuntimeError, "event failure"):
                self.runtime.claim()
        self.assert_no_claim_mutation(before)

    def test_16_each_intermediate_write_failure_rolls_back_every_table(self):
        stages = (("leases", 1), ("resource_locks", 1), ("resource_locks", 2), ("attempts", 1))
        for table, occurrence in stages:
            with self.subTest(table=table, occurrence=occurrence):
                self.replace_runtime()
                before = self.runtime.claim_state()
                original = self.runtime.store._insert
                seen = 0

                def failing_insert(connection, candidate_table, row):
                    nonlocal seen
                    if candidate_table == table:
                        seen += 1
                        if seen == occurrence:
                            raise RuntimeError(f"failure at {table}-{occurrence}")
                    return original(connection, candidate_table, row)

                with mock.patch.object(self.runtime.store, "_insert", side_effect=failing_insert):
                    with self.assertRaisesRegex(RuntimeError, f"failure at {table}-{occurrence}"):
                        self.runtime.claim()
                self.assert_no_claim_mutation(before)

    def test_17_concurrent_same_packet_and_shared_resource_claims_each_have_one_winner(self):
        barrier = threading.Barrier(2)

        def same_packet(number):
            barrier.wait()
            try:
                return self.runtime.claim(
                    lease={**LEASE, "lease_id": f"lease-{number}", "worktree_path": f"/runtime/worktree-{number}"},
                    locks=[{**item, "lock_id": f"{item['lock_id']}-{number}"} for item in LOCKS],
                    attempt={**ATTEMPT, "attempt_id": f"attempt-{number}"},
                    key=f"same-packet-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(same_packet, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, StaleState) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.claim_events()), 1)

        self.replace_runtime(["shared:one"])
        self.runtime.add_packet("packet-2", "work-2", ["shared:one"])
        barrier = threading.Barrier(2)

        def shared_resource(number):
            barrier.wait()
            packet_id = f"packet-{number}"
            try:
                return self.runtime.claim(
                    packet_id=packet_id,
                    lease={**LEASE, "lease_id": f"lease-{number}", "worktree_path": f"/runtime/shared-{number}"},
                    locks=[{"lock_id": f"lock-{number}", "lock_kind": "SharedBoundary", "resource_key": "shared:one"}],
                    attempt={**ATTEMPT, "attempt_id": f"attempt-{number}"},
                    key=f"shared-resource-{number}",
                )
            except Exception as error:
                return error

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(shared_resource, (1, 2)))
        self.assertEqual(sum(isinstance(item, dict) for item in outcomes), 1)
        self.assertEqual(sum(isinstance(item, ResourceConflict) for item in outcomes), 1)
        self.assertEqual(len(self.runtime.claim_events()), 1)

    def test_18_restart_replay_is_exact_and_has_no_execution_side_effect(self):
        first = self.runtime.claim()
        reopened = OperationalStateStore(self.runtime.config)
        reopened.health()
        replay = reopened.claim_packet_assignment(
            "packet-1", 4, LEASE, LOCKS, ATTEMPT, REASON, "claim-1", ACTOR, AFTER_EXPIRY
        )
        self.assertEqual(replay, first)
        self.assertEqual(len(self.runtime.claim_events()), 1)
        packet = reopened.snapshot("Packet", "packet-1")
        attempt = reopened.snapshot("Attempt", "attempt-1")
        self.assertEqual(packet["state"], "Leased")
        self.assertEqual((attempt["state"], attempt["started_at"]), ("Planned", None))
        self.assertEqual(self.runtime.rows("attempt_context_usage"), [])
        self.assertEqual(self.runtime.rows("worker_progress_observations"), [])
        self.assertEqual(self.runtime.rows("evidence"), [])


if __name__ == "__main__":
    unittest.main()
