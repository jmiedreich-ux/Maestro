from __future__ import annotations

import copy
import json
import sqlite3
import tempfile
import threading
import unittest
from contextlib import closing
from pathlib import Path

from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig, RuntimePathError
from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    OperationalStateStore,
    canonical_digest,
    context_policy_digest,
)
from maestro.storage import SCHEMA_VERSION, SQLiteFoundation


NOW = "2026-09-02T12:00:00.000000Z"
LATER = "2026-09-02T13:00:00.000000Z"
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
DIGEST_A = "a" * 64
ACTOR = Actor("MaestroDeveloper", "developer-1", "correlation-1")
POLICY = {
    "minimum_context_tokens": 32768,
    "output_reserve_tokens": 8192,
    "warning_remaining_tokens": 16384,
    "checkpoint_remaining_tokens": 12288,
    "stop_remaining_tokens": 8192,
}


class Runtime:
    def __init__(self):
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = Path(self._temporary.name) / "runtime"

    def config(self):
        return RuntimeConfig(self.path)

    def close(self):
        self._temporary.cleanup()


def _schema_three(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE schema_versions(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO schema_versions(version) VALUES (3);
        CREATE TABLE packet_runs(packet_id TEXT PRIMARY KEY,status TEXT NOT NULL,authority_json TEXT NOT NULL,worktree_path TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE packet_attempts(packet_id TEXT PRIMARY KEY REFERENCES packet_runs(packet_id),attempt_number INTEGER NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE packet_evidence(packet_id TEXT NOT NULL REFERENCES packet_runs(packet_id),evidence_kind TEXT NOT NULL,payload_json TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(packet_id,evidence_kind));
        CREATE TABLE packet_handoffs(packet_id TEXT NOT NULL REFERENCES packet_runs(packet_id),handoff_kind TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(packet_id,handoff_kind));
        CREATE TABLE discovery_evidence(packet_id TEXT PRIMARY KEY REFERENCES packet_runs(packet_id),inventory_json TEXT NOT NULL,proposed_binding_json TEXT,fixture_digest TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE projects(project_id TEXT PRIMARY KEY,repository_identity TEXT UNIQUE NOT NULL,default_branch TEXT NOT NULL,adapter_version TEXT NOT NULL,process_version TEXT NOT NULL,registration_state TEXT NOT NULL CHECK(registration_state IN ('Candidate','Registered','Blocked')),active_binding_revision TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE project_registration_runs(request_id TEXT PRIMARY KEY,idempotency_key TEXT UNIQUE NOT NULL,mode TEXT NOT NULL CHECK(mode='AuthorityLoad'),project_id TEXT REFERENCES projects(project_id),repository_identity TEXT NOT NULL,repository_path TEXT NOT NULL,source_commit TEXT NOT NULL,manifest_path TEXT NOT NULL,manifest_digest TEXT NOT NULL,inventory_json TEXT NOT NULL,candidate_binding_json TEXT,authority_files_json TEXT NOT NULL,result TEXT NOT NULL CHECK(result IN ('Reviewable','Blocked')),created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE events(event_id INTEGER PRIMARY KEY,idempotency_key TEXT UNIQUE NOT NULL,entity_type TEXT NOT NULL,entity_id TEXT NOT NULL,event_type TEXT NOT NULL,before_json TEXT NOT NULL,after_json TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO packet_runs(packet_id,status,authority_json) VALUES ('alpha-row','Claimed','{"a":1}');
        INSERT INTO packet_attempts(packet_id,attempt_number,status) VALUES ('alpha-row',1,'Claimed');
        INSERT INTO discovery_evidence(packet_id,inventory_json,fixture_digest) VALUES ('alpha-row','{"preserved":true}','alpha-digest');
        INSERT INTO projects(project_id,repository_identity,default_branch,adapter_version,process_version,registration_state) VALUES ('project-1','owner/repo','main','adapter-v1','process-v1','Candidate');
        INSERT INTO project_registration_runs(request_id,idempotency_key,mode,project_id,repository_identity,repository_path,source_commit,manifest_path,manifest_digest,inventory_json,candidate_binding_json,authority_files_json,result) VALUES ('request-1','legacy-key','AuthorityLoad','project-1','owner/repo','/tmp/repo','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','maestro.project.yaml','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','{}','{}','[]','Reviewable');
        INSERT INTO events(idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason) VALUES ('legacy-key','ProjectRegistrationRun','request-1','AuthorityLoaded','{}','{"result":"Reviewable"}','legacy');
        """
    )


def _inventory(connection: sqlite3.Connection):
    schema = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    ).fetchall()
    rows = {}
    for table in (
        "schema_versions", "packet_runs", "packet_attempts", "discovery_evidence",
        "projects", "project_registration_runs", "events",
    ):
        rows[table] = connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
    return schema, rows


def _measurement(value, quality="RuntimeReported", confidence="Exact", source="runtime"):
    return {"value": value, "quality": quality, "confidence": confidence, "source_reference": source, "observed_at": NOW}


def _redacted(text):
    return {"kind": "redacted-text", "text": text, "redaction_status": "Redacted", "redaction_receipt_reference": "receipt-1"}


class MigrationTests(unittest.TestCase):
    def test_schema_three_upgrades_additively_and_preserves_every_original_value(self) -> None:
        runtime = Runtime()
        try:
            runtime.path.mkdir()
            database = runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                _schema_three(connection)
                before_columns = {
                    table: connection.execute(f"PRAGMA table_info({table})").fetchall()
                    for table in ("packet_runs", "projects", "project_registration_runs", "events")
                }
                before_rows = _inventory(connection)[1]
            health = SQLiteFoundation(runtime.config()).health()
            self.assertEqual(health.schema_version, 4)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(
                    connection.execute("SELECT version FROM schema_versions ORDER BY version").fetchall(),
                    [(3,), (4,)],
                )
                after_rows = _inventory(connection)[1]
                for table in before_rows:
                    if table == "schema_versions":
                        continue
                    original_width = len(before_rows[table][0]) if before_rows[table] else 0
                    self.assertEqual(
                        [row[:original_width] for row in after_rows[table]], before_rows[table], table
                    )
                for table in ("packet_runs", "projects", "project_registration_runs"):
                    self.assertEqual(connection.execute(f"PRAGMA table_info({table})").fetchall(), before_columns[table])
                event_columns = [row[1] for row in connection.execute("PRAGMA table_info(events)")]
                self.assertEqual(event_columns[-6:], ["correlation_id", "causation_event_id", "actor_type", "actor_id", "command_fingerprint", "observed_at"])
                expected = {
                    "project_bindings", "secret_reference_observations", "graph_projections", "work_items",
                    "runs", "packets", "leases", "attempts", "resource_locks", "evidence", "waits",
                    "reviews", "notifications", "acceptance_records", "merge_observations",
                    "worker_progress_observations", "attempt_context_usage", "provider_allowance_windows",
                    "usage_reconciliations",
                }
                tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                self.assertTrue(expected <= tables)
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            runtime.close()

    def test_injected_schema_four_failure_rolls_back_columns_tables_version_and_data_exactly(self) -> None:
        runtime = Runtime()
        try:
            runtime.path.mkdir()
            database = runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                _schema_three(connection)
                before = _inventory(connection)

                def fail(stage):
                    if stage == "after_m1_02_schema":
                        raise RuntimeError("injected schema-four DDL failure")

                with self.assertRaisesRegex(RuntimeError, "injected schema-four"):
                    SQLiteFoundation._apply_migrations(connection, fail)
                self.assertEqual(_inventory(connection), before)
                self.assertEqual([row[1] for row in connection.execute("PRAGMA table_info(events)")][-1], "created_at")
                self.assertIsNone(connection.execute("SELECT 1 FROM sqlite_master WHERE name='project_bindings'").fetchone())
        finally:
            runtime.close()

    def test_reopen_is_noop_and_two_migrators_produce_one_version_four_row(self) -> None:
        runtime = Runtime()
        try:
            runtime.path.mkdir()
            database = runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                _schema_three(connection)
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
                first = _inventory(connection)[0]
            SQLiteFoundation(runtime.config()).health()
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("SELECT version,COUNT(*) FROM schema_versions GROUP BY version").fetchall(), [(3, 1), (4, 1)])
                self.assertEqual(_inventory(connection)[0], first)
        finally:
            runtime.close()

    def test_legacy_event_is_grandfathered_but_other_metadata_and_all_event_mutation_are_rejected(self) -> None:
        runtime = Runtime()
        try:
            SQLiteFoundation(runtime.config()).health()
            with closing(sqlite3.connect(runtime.path / "maestro.sqlite3")) as connection:
                connection.execute(
                    "INSERT INTO events(idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason) VALUES ('legacy','ProjectRegistrationRun','r','AuthorityLoaded','{}','{}','legacy')"
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "INSERT INTO events(idempotency_key,entity_type,entity_id,event_type,before_json,after_json,reason) VALUES ('bad','Packet','p','PacketMaterialized','{}','{}','bad')"
                    )
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("UPDATE events SET reason='changed' WHERE idempotency_key='legacy'")
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute("DELETE FROM events WHERE idempotency_key='legacy'")
                legacy = connection.execute("SELECT correlation_id,causation_event_id,actor_type,actor_id,command_fingerprint,observed_at FROM events WHERE idempotency_key='legacy'").fetchone()
                self.assertEqual(legacy, (None, None, None, None, None, None))
        finally:
            runtime.close()


class RecordRouteTests(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()
        self.store = OperationalStateStore(self.runtime.config())
        self.store.health()
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO projects(project_id,repository_identity,default_branch,adapter_version,process_version,registration_state) VALUES ('project-1','owner/repo','main','adapter-v1','process-v1','Candidate')"
            )
            connection.commit()

    def tearDown(self):
        self.runtime.close()

    def _records(self):
        binding = {
            "binding_id": "binding-1", "project_id": "project-1", "binding_revision": "revision-1",
            "source_commit": COMMIT_A, "manifest_digest": DIGEST_A, "adapter_version": "adapter-v1",
            "process_version": "process-v1", "authority_reference": "authority-1",
            "merge_policy": "no-automatic-merge", "acceptance_authority": "ProjectArchitect",
            "merge_execution_authority": "OwnerPerformed", "merge_delegation_reference": None,
            "binding_json": {"binding": "candidate"}, "state": "Candidate",
            "activated_at": None, "superseded_at": None,
        }
        secret = {
            "secret_reference_observation_id": "secret-observation-1", "project_id": "project-1",
            "binding_id": "binding-1", "provider": "secret-provider",
            "reference_name": "GITHUB_APP_PRIVATE_KEY", "owner_reference": "owner-policy-1",
            "rotation_at": None, "expires_at": LATER, "status": "Active", "observed_at": NOW,
        }
        graph = {
            "graph_projection_id": "graph-1", "project_id": "project-1", "binding_id": "binding-1",
            "graph_revision": "graph-r1", "authority_reference": "graph-authority", "source_base_sha": COMMIT_A,
            "source_hash": DIGEST_A, "state": "Active", "observed_at": NOW,
        }
        work = {
            "work_item_id": "work-1", "graph_projection_id": "graph-1", "architecture_node_id": "node-1",
            "task_reference": "task-1", "workstream_ref": "operational-core", "milestone_ref": "M1",
            "title": "Schema records", "priority": "P0", "planned_rank": 1,
            "specialist_role": "MaestroDeveloper", "execution_classes_json": ["codex-cloud"],
            "dependencies_json": ["m1-01"], "change_domains_json": ["sqlite-schema"],
            "input_contract_json": {"version": 3}, "output_contract_json": {"version": 4},
            "planning_state": "Active",
        }
        run = {
            "run_id": "run-1", "run_fingerprint": DIGEST_A, "project_id": "project-1",
            "binding_id": "binding-1", "graph_projection_id": "graph-1", "milestone_ref": "M1",
            "approved_authority_reference": "authority-1", "branch_name": None,
            "pull_request_reference": None, "current_head": None, "current_head_source_reference": None,
            "candidate_head": None, "candidate_head_source_reference": None,
            "state": "Planned", "acceptance_boundary": "ProjectArchitect",
        }
        packet = {
            "packet_id": "packet-1", "run_id": "run-1", "work_item_id": "work-1",
            "packet_revision": "packet-r1", "authority_reference": "packet-authority",
            "base_commit": COMMIT_A, "current_head": None, "expected_branch": "implementation/m1-02a",
            "role_contract_reference": "role-1", "sop_reference": "sop-1",
            "executor_class": "codex-cloud", "integration_route": "validate-only",
            "reviewer_route": "independent", "owned_paths_json": ["services/maestro"],
            "forbidden_paths_json": ["live-project"], "checks_json": ["python", "unittest"],
            "resource_claims_json": ["shared:sqlite-schema"], "context_policy_json": POLICY,
            "state": "Planned", "correction_count": 0,
        }
        return binding, secret, graph, work, run, packet

    def _seed_through_packet_and_attempt(self):
        binding, secret, graph, work, run, packet = self._records()
        self.store.record_binding(binding, "command-binding", ACTOR, NOW)
        self.store.record_secret_reference(secret, "command-secret", ACTOR, NOW)
        self.store.record_graph_projection(graph, [work], "command-graph", ACTOR, NOW)
        self.store.create_run(run, "command-run", ACTOR, NOW)
        self.store.materialize_packet(packet, "command-packet", ACTOR, NOW)
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO leases(lease_id,packet_id,run_id,claim_key,run_fingerprint,base_commit,worktree_path,executor_route,holder_id,state,acquired_at,expires_at,heartbeat_at,version) VALUES (?,?,?,?,?,?,?,?,?,'Active',?,?,?,1)",
                ("lease-1", "packet-1", "run-1", "claim-1", DIGEST_A, COMMIT_A, "/runtime/worktree", "executor", "holder", NOW, LATER, NOW),
            )
            connection.commit()
        attempt = {
            "attempt_id": "attempt-1", "packet_id": "packet-1", "lease_id": "lease-1",
            "attempt_number": 1, "attempt_kind": "Initial", "executor_class": "codex-cloud",
            "model_identity": "gpt-5", "runtime_identity": "codex", "state": "Planned",
            "result_commit": None, "correction_for_review_id": None, "started_at": None, "finished_at": None,
        }
        self.store.record_attempt(attempt, "command-attempt", ACTOR, NOW)

    def test_all_a_record_append_routes_persist_reopen_and_events_are_ordered(self) -> None:
        self._seed_through_packet_and_attempt()
        payload = {"kind": "state", "entity_type": "Attempt", "entity_id": "attempt-1", "state": "Planned", "version": 1}
        evidence = {
            "evidence_id": "evidence-1", "idempotency_key": "command-evidence", "run_id": "run-1",
            "packet_id": "packet-1", "attempt_id": "attempt-1", "evidence_kind": "State",
            "payload_json": payload, "content_digest": canonical_digest(payload),
            "source_reference": "test-source", "redaction_state": "NotRequired", "created_at": NOW,
        }
        wait = {
            "wait_id": "wait-1", "run_id": "run-1", "packet_id": "packet-1", "gate_type": "Review",
            "awaited_role": "IndependentReviewer", "awaited_reference": "review-route",
            "expected_result": "Approve", "timeout_at": LATER, "next_permitted_action": "Wait",
            "state": "Open", "resolution_reason_payload_json": None,
        }
        review = {
            "review_id": "review-1", "packet_id": "packet-1", "attempt_id": "attempt-1",
            "review_kind": "Integration", "reviewer_role": "IntegrationAgent", "reviewer_instance": "integration-1",
            "base_commit": COMMIT_A, "head_commit": COMMIT_B, "result": "ValidateOnly",
            "findings_json": [], "coverage_json": {"base": COMMIT_A, "head": COMMIT_B},
            "correction_number": 0, "created_at": NOW,
        }
        self.store.append_evidence(evidence, ACTOR)
        self.store.open_wait(wait, "command-wait", ACTOR, NOW)
        self.store.record_review(review, "command-review", ACTOR, NOW)
        first_event = self.store.events_after(0, 100)[0]["event_id"]
        notification_payload = {
            "kind": "notification", "event_id": first_event, "audience": "ProjectArchitect",
            "severity": "ActionNeeded", "subject_reference": "packet-1",
            "evidence_references": ["evidence-1"], "next_action_reference": "review",
        }
        notification = {
            "notification_id": "notification-1", "event_id": first_event, "run_id": "run-1",
            "packet_id": "packet-1", "channel": "LocalDurable", "destination_reference": "local-db",
            "audience": "ProjectArchitect", "severity": "ActionNeeded", "message_type": "ReviewReady",
            "grouping_key": "run-1", "escalation_at": LATER, "payload_json": notification_payload,
            "state": "Pending", "attempt_count": 0, "last_error_payload_json": None, "next_attempt_at": None,
        }
        self.store.record_notification(notification, "command-notification", ACTOR, NOW)
        progress = {
            "progress_id": "progress-1", "attempt_id": "attempt-1", "plan_payload_json": _redacted("plan"),
            "current_step_payload_json": _redacted("step"), "blocker_payload_json": _redacted("none"),
            "eta_text": "unknown", "confidence": "Unknown", "status_request_state": "NotRequested",
            "next_permitted_action": "continue", "observed_at": NOW, "received_at": NOW,
        }
        self.store.record_worker_progress(progress, "command-progress", ACTOR, NOW)
        token_measurements = {
            "input": _measurement(1000), "output": _measurement(0), "cached_input": _measurement(0),
            "reasoning": _measurement(0), "total": _measurement(1000),
        }
        context = {
            "context_usage_id": "context-1", "attempt_id": "attempt-1", "model_identity": "gpt-5",
            "runtime_identity": "codex", "quantization": None, "configured_context_limit": 40960,
            "context_policy_digest": context_policy_digest(POLICY), "counting_method": "Runtime",
            "starting_input_measurement_json": _measurement(1000),
            "future_growth_estimate_json": {
                "lower_bound": _measurement(100, "Estimated", "Medium", "estimate"),
                "upper_bound": _measurement(200, "Estimated", "Medium", "estimate"),
            },
            "token_measurements_json": token_measurements,
            "cost_measurement_json": {"status": "Unknown", "amount": None, "currency": None, "quality": "Unavailable", "confidence": "Unavailable", "source_reference": None, "observed_at": NOW},
            "availability_state": "Partial", "observed_at": NOW,
        }
        with self.assertRaises(InvalidRecord):
            self.store.record_context_usage(
                dict(context, context_usage_id="bad-context", context_policy_digest="b" * 64),
                "command-bad-context", ACTOR, NOW,
            )
        self.store.record_context_usage(context, "command-context", ACTOR, NOW)
        upgraded_tokens = {
            name: dict(value, value=value["value"] + 1 if value["value"] is not None else None)
            for name, value in token_measurements.items()
        }
        context_update = {
            "token_measurements": upgraded_tokens,
            "cost_measurement": context["cost_measurement_json"],
            "availability_state": "Available",
            "observed_at": NOW,
        }
        updated = self.store.update_context_usage(
            "attempt-1", 1, context_update, "command-context-update", ACTOR, LATER
        )
        self.assertEqual(updated["version"], 2)
        self.assertIsInstance(updated["starting_input_measurement_json"], dict)
        self.assertEqual(
            self.store.update_context_usage(
                "attempt-1", 1, context_update, "command-context-update", ACTOR, NOW
            ),
            updated,
        )
        lower_quality = copy.deepcopy(context_update)
        lower_quality["token_measurements"] = {
            name: _measurement(value["value"], "Estimated", "Medium", "estimate")
            for name, value in upgraded_tokens.items()
        }
        with self.assertRaises(InvalidRecord):
            self.store.update_context_usage(
                "attempt-1", 2, lower_quality, "command-context-lower", ACTOR, LATER
            )
        allowance = {
            "allowance_observation_id": "allowance-1", "provider": "openai", "account_reference": "account-1",
            "native_window_type": "provider-window", "used_value": "10.5", "remaining_value": "89.5",
            "native_unit": "requests", "reset_at": LATER, "precision": "Exact",
            "measurement_quality": "ProviderReported", "freshness": "Fresh", "observed_at": NOW,
        }
        self.store.record_allowance_window(allowance, "command-allowance", ACTOR, NOW)
        reconciliation = {
            "usage_reconciliation_id": "reconciliation-1", "allowance_observation_id": "allowance-1",
            "window_change_value": "10.5", "tracked_controlled_value": "4",
            "registered_coarse_value": "5", "unattributed_value": "1.5", "native_unit": "requests",
            "measurement_quality": "Exact", "observed_at": NOW,
        }
        with self.assertRaises(InvalidRecord):
            self.store.record_usage_reconciliation(
                dict(reconciliation, usage_reconciliation_id="bad-reconciliation", native_unit="tokens"),
                "command-bad-reconciliation", ACTOR, NOW,
            )
        self.store.record_usage_reconciliation(reconciliation, "command-reconciliation", ACTOR, NOW)
        acceptance = {
            "acceptance_id": "acceptance-1", "subject_type": "Packet", "subject_id": "packet-1",
            "packet_id": "packet-1", "run_id": None, "sequence_number": 1,
            "supersedes_acceptance_id": None, "required_authority": "ProjectArchitect",
            "decision": "Returned", "authority_reference": "architect-return", "exact_head": COMMIT_B,
            "review_coverage_json": {}, "reason_payload_json": {"kind": "reason", "reason_code": "CHANGES", "detail_reference": "review-1"},
            "created_at": NOW,
        }
        self.store.record_acceptance(acceptance, "command-acceptance", ACTOR, NOW)
        merge = {
            "merge_observation_id": "merge-1", "run_id": "run-1", "packet_id": "packet-1",
            "acceptance_id": None, "repository_reference": "owner/repo", "default_branch": "main",
            "accepted_head": COMMIT_B, "merge_commit": COMMIT_A, "source_kind": "Git",
            "source_reference": "git-observation", "performed_by_authority": "DelegatedIdentity",
            "performed_by_reference": "bot-1", "delegation_reference": "delegation-policy",
            "review_coverage_json": {}, "observed_at": NOW,
        }
        self.store.record_merge_observation(merge, "command-merge", ACTOR, NOW)

        reopened = OperationalStateStore(self.runtime.config())
        for entity, identifier in (
            ("ProjectBinding", "binding-1"), ("SecretReferenceObservation", "secret-observation-1"),
            ("GraphProjection", "graph-1"), ("WorkItem", "work-1"), ("Run", "run-1"),
            ("Packet", "packet-1"), ("Attempt", "attempt-1"), ("Evidence", "evidence-1"),
            ("Wait", "wait-1"), ("Review", "review-1"), ("Notification", "notification-1"),
            ("WorkerProgress", "progress-1"), ("AttemptContextUsage", "context-1"),
            ("AllowanceWindow", "allowance-1"), ("UsageReconciliation", "reconciliation-1"),
            ("Acceptance", "acceptance-1"), ("MergeObservation", "merge-1"),
        ):
            with self.subTest(entity=entity):
                self.assertIsNotNone(reopened.snapshot(entity, identifier))
        events = reopened.events_after(0, 1000)
        ids = [event["event_id"] for event in events]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(events), 17)

        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            for table in (
                "evidence", "reviews", "secret_reference_observations", "worker_progress_observations",
                "provider_allowance_windows", "usage_reconciliations", "acceptance_records", "merge_observations",
            ):
                primary_key = connection.execute(f"PRAGMA table_info({table})").fetchone()[1]
                value = connection.execute(f"SELECT {primary_key} FROM {table}").fetchone()[0]
                with self.subTest(table=table, action="update"), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(f"UPDATE {table} SET {primary_key}={primary_key} WHERE {primary_key}=?", (value,))
                with self.subTest(table=table, action="delete"), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(f"DELETE FROM {table} WHERE {primary_key}=?", (value,))

    def test_idempotent_replay_after_reopen_and_conflict_do_not_mutate(self) -> None:
        binding = self._records()[0]
        first = self.store.record_binding(binding, "same-command", ACTOR, NOW)
        reopened = OperationalStateStore(self.runtime.config())
        self.assertEqual(reopened.record_binding(binding, "same-command", ACTOR, LATER), first)
        changed = copy.deepcopy(binding)
        changed["authority_reference"] = "different-authority"
        with self.assertRaises(IdempotencyConflict):
            reopened.record_binding(changed, "same-command", ACTOR, NOW)
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM project_bindings").fetchone()[0], 1)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM events WHERE idempotency_key='same-command'").fetchone()[0], 1)

    def test_fk_unique_partial_active_checks_and_invalid_records_fail_without_event(self) -> None:
        binding = self._records()[0]
        before = len(self.store.events_after(0, 1000))
        with self.assertRaises(InvalidRecord):
            self.store.record_binding(dict(binding, project_id="missing"), "missing-project", ACTOR, NOW)
        with self.assertRaises(InvalidRecord):
            self.store.record_binding(dict(binding, state="Active"), "active-via-api", ACTOR, NOW)
        with self.assertRaises(InvalidRecord):
            self.store.record_binding(dict(binding, source_commit="A" * 40), "upper-commit", ACTOR, NOW)
        secret = self._records()[1]
        with self.assertRaises(InvalidRecord):
            self.store.record_secret_reference(
                {**secret, "secret_value": "github_pat_value"}, "secret-value", ACTOR, NOW
            )
        self.assertEqual(len(self.store.events_after(0, 1000)), before)

    def test_database_partial_active_constraints_reject_second_binding_and_graph_without_event(self) -> None:
        binding = self.store._binding(self._records()[0], NOW)
        binding.update(state="Active", activated_at=NOW)
        second_binding = dict(
            binding, binding_id="binding-2", binding_revision="revision-2", source_commit=COMMIT_B
        )
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            self.store._insert(connection, "project_bindings", binding)
            with self.assertRaises(sqlite3.IntegrityError):
                self.store._insert(connection, "project_bindings", second_binding)

            graph = self.store._graph(self._records()[2], NOW)
            self.store._insert(connection, "graph_projections", graph)
            second_graph = dict(
                graph, graph_projection_id="graph-2", graph_revision="graph-r2", source_hash="b" * 64
            )
            with self.assertRaises(sqlite3.IntegrityError):
                self.store._insert(connection, "graph_projections", second_graph)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)

    def test_store_construction_and_public_reads_reject_forged_or_swapped_runtime_before_artifacts(self) -> None:
        outside_parent = Path(tempfile.mkdtemp())
        outside = outside_parent / "outside"
        unsafe = object.__new__(RuntimeConfig)
        object.__setattr__(unsafe, "runtime_dir", outside)
        source_path = REPOSITORY_ROOT / "services" / "maestro" / "maestro" / "m1-02-route-check"
        unsafe_source = object.__new__(RuntimeConfig)
        object.__setattr__(unsafe_source, "runtime_dir", source_path)
        link_container = DEFAULT_RUNTIME_DIR / "m1-02a-symlink-route-check"
        link_container.mkdir()
        linked = link_container / "outside-link"
        linked.symlink_to(outside_parent, target_is_directory=True)
        unsafe_link = object.__new__(RuntimeConfig)
        object.__setattr__(unsafe_link, "runtime_dir", linked / "runtime")
        try:
            for forged in (unsafe, unsafe_source, unsafe_link):
                with self.subTest(forged=forged), self.assertRaises(RuntimePathError):
                    OperationalStateStore(forged)
            self.assertFalse(outside.exists())
            self.assertFalse(source_path.exists())

            swapped = OperationalStateStore(self.runtime.config())
            swapped._foundation.config = unsafe
            binding, secret, graph, work, run, packet = self._records()
            attempt = {
                "attempt_id": "attempt-1", "packet_id": "packet-1", "lease_id": "lease-1",
                "attempt_number": 1, "attempt_kind": "Initial", "executor_class": "codex-cloud",
                "model_identity": "gpt-5", "runtime_identity": "codex", "state": "Planned",
                "result_commit": None, "correction_for_review_id": None,
                "started_at": None, "finished_at": None,
            }
            state_payload = {"kind": "state", "entity_type": "Attempt", "entity_id": "attempt-1", "state": "Planned", "version": 1}
            evidence = {
                "evidence_id": "evidence-1", "idempotency_key": "evidence-command", "run_id": "run-1",
                "packet_id": "packet-1", "attempt_id": "attempt-1", "evidence_kind": "State",
                "payload_json": state_payload, "content_digest": canonical_digest(state_payload),
                "source_reference": None, "redaction_state": "NotRequired", "created_at": NOW,
            }
            wait = {
                "wait_id": "wait-1", "run_id": "run-1", "packet_id": "packet-1", "gate_type": "Review",
                "awaited_role": "Reviewer", "awaited_reference": "review-route", "expected_result": "Approve",
                "timeout_at": LATER, "next_permitted_action": "Wait", "state": "Open",
                "resolution_reason_payload_json": None,
            }
            review = {
                "review_id": "review-1", "packet_id": "packet-1", "attempt_id": None,
                "review_kind": "Integration", "reviewer_role": "IntegrationAgent",
                "reviewer_instance": "integration-1", "base_commit": COMMIT_A, "head_commit": COMMIT_B,
                "result": "ValidateOnly", "findings_json": [], "coverage_json": {},
                "correction_number": 0, "created_at": NOW,
            }
            notification_payload = {"kind": "notification", "event_id": 1, "audience": "ProjectArchitect", "severity": "ActionNeeded", "subject_reference": "packet-1", "evidence_references": [], "next_action_reference": "review"}
            notification = {
                "notification_id": "notification-1", "event_id": 1, "run_id": "run-1", "packet_id": "packet-1",
                "channel": "LocalDurable", "destination_reference": "local", "audience": "ProjectArchitect",
                "severity": "ActionNeeded", "message_type": "Review", "grouping_key": "run-1",
                "escalation_at": None, "payload_json": notification_payload, "state": "Pending",
                "attempt_count": 0, "last_error_payload_json": None, "next_attempt_at": None,
            }
            progress = {
                "progress_id": "progress-1", "attempt_id": "attempt-1", "plan_payload_json": _redacted("plan"),
                "current_step_payload_json": _redacted("step"), "blocker_payload_json": _redacted("none"),
                "eta_text": "unknown", "confidence": "Unknown", "status_request_state": "NotRequested",
                "next_permitted_action": "continue", "observed_at": NOW, "received_at": NOW,
            }
            unavailable = _measurement(None, "Unavailable", "Unavailable", None)
            estimated_lower = _measurement(0, "Estimated", "Low", "estimate")
            context = {
                "context_usage_id": "context-1", "attempt_id": "attempt-1", "model_identity": "gpt-5",
                "runtime_identity": "codex", "quantization": None, "configured_context_limit": 40960,
                "context_policy_digest": context_policy_digest(POLICY), "counting_method": "Unavailable",
                "starting_input_measurement_json": unavailable,
                "future_growth_estimate_json": {"lower_bound": estimated_lower, "upper_bound": estimated_lower},
                "token_measurements_json": {name: unavailable for name in ("input", "output", "cached_input", "reasoning", "total")},
                "cost_measurement_json": {"status": "Unknown", "amount": None, "currency": None, "quality": "Unavailable", "confidence": "Unavailable", "source_reference": None, "observed_at": NOW},
                "availability_state": "Unavailable", "observed_at": NOW,
            }
            context_update = {
                "token_measurements": context["token_measurements_json"],
                "cost_measurement": context["cost_measurement_json"],
                "availability_state": "Unavailable", "observed_at": NOW,
            }
            allowance = {
                "allowance_observation_id": "allowance-1", "provider": "openai", "account_reference": "account",
                "native_window_type": "window", "used_value": None, "remaining_value": None,
                "native_unit": None, "reset_at": None, "precision": "Unavailable",
                "measurement_quality": "Unavailable", "freshness": "Unavailable", "observed_at": NOW,
            }
            reconciliation = {
                "usage_reconciliation_id": "reconciliation-1", "allowance_observation_id": "allowance-1",
                "window_change_value": "0", "tracked_controlled_value": "0",
                "registered_coarse_value": "0", "unattributed_value": "0", "native_unit": "requests",
                "measurement_quality": "Exact", "observed_at": NOW,
            }
            acceptance = {
                "acceptance_id": "acceptance-1", "subject_type": "Packet", "subject_id": "packet-1",
                "packet_id": "packet-1", "run_id": None, "sequence_number": 1,
                "supersedes_acceptance_id": None, "required_authority": "ProjectArchitect",
                "decision": "Returned", "authority_reference": "architect", "exact_head": COMMIT_B,
                "review_coverage_json": {}, "reason_payload_json": {"kind": "reason", "reason_code": "RETURN", "detail_reference": None},
                "created_at": NOW,
            }
            merge = {
                "merge_observation_id": "merge-1", "run_id": "run-1", "packet_id": "packet-1",
                "acceptance_id": None, "repository_reference": "owner/repo", "default_branch": "main",
                "accepted_head": COMMIT_B, "merge_commit": COMMIT_A, "source_kind": "Git",
                "source_reference": "git-observation", "performed_by_authority": "Owner",
                "performed_by_reference": "owner-action", "delegation_reference": None,
                "review_coverage_json": None, "observed_at": NOW,
            }
            record_calls = (
                lambda: swapped.record_binding(binding, "k-binding", ACTOR, NOW),
                lambda: swapped.record_secret_reference(secret, "k-secret", ACTOR, NOW),
                lambda: swapped.record_graph_projection(graph, [work], "k-graph", ACTOR, NOW),
                lambda: swapped.create_run(run, "k-run", ACTOR, NOW),
                lambda: swapped.materialize_packet(packet, "k-packet", ACTOR, NOW),
                lambda: swapped.record_attempt(attempt, "k-attempt", ACTOR, NOW),
                lambda: swapped.append_evidence(evidence, ACTOR),
                lambda: swapped.open_wait(wait, "k-wait", ACTOR, NOW),
                lambda: swapped.record_review(review, "k-review", ACTOR, NOW),
                lambda: swapped.record_notification(notification, "k-notification", ACTOR, NOW),
                lambda: swapped.record_worker_progress(progress, "k-progress", ACTOR, NOW),
                lambda: swapped.record_context_usage(context, "k-context", ACTOR, NOW),
                lambda: swapped.update_context_usage("attempt-1", 1, context_update, "k-update", ACTOR, NOW),
                lambda: swapped.record_allowance_window(allowance, "k-allowance", ACTOR, NOW),
                lambda: swapped.record_usage_reconciliation(reconciliation, "k-reconciliation", ACTOR, NOW),
                lambda: swapped.record_acceptance(acceptance, "k-acceptance", ACTOR, NOW),
                lambda: swapped.record_merge_observation(merge, "k-merge", ACTOR, NOW),
            )
            for call in (
                lambda: swapped.health(),
                lambda: swapped.snapshot("ProjectBinding", "binding-1"),
                lambda: swapped.events_after(0, 1),
                *record_calls,
            ):
                with self.subTest(call=call), self.assertRaises(RuntimePathError):
                    call()
            self.assertFalse(outside.exists())
        finally:
            linked.unlink()
            link_container.rmdir()
            outside_parent.rmdir()


if __name__ == "__main__":
    unittest.main()
