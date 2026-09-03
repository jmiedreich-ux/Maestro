from __future__ import annotations

import copy
import hashlib
import json
import re
import sqlite3
import tempfile
import threading
import time
import unittest
from contextlib import closing
from pathlib import Path
from unittest import mock

from maestro import operational_state as operational_state
from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig, RuntimePathError
from maestro.operational_state import (
    Actor,
    IdempotencyConflict,
    InvalidRecord,
    OperationalStateStore,
    ResourceBusy,
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


def _durable_state(connection: sqlite3.Connection):
    schema = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    ).fetchall()
    tables = [row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )]
    return schema, {
        table: connection.execute(f'SELECT * FROM "{table}" ORDER BY 1').fetchall()
        for table in tables
    }


def _measurement(value, quality="RuntimeReported", confidence="Exact", source="runtime"):
    return {"value": value, "quality": quality, "confidence": confidence, "source_reference": source, "observed_at": NOW}


def _redacted(text):
    return {"kind": "redacted-text", "text": text, "redaction_status": "Redacted", "redaction_receipt_reference": "receipt-1"}


class MigrationTests(unittest.TestCase):
    def test_ar_p02_static_schema_oracle_is_exact(self) -> None:
        runtime = Runtime()
        names = (
            "events", "project_bindings", "secret_reference_observations", "graph_projections",
            "work_items", "runs", "packets", "leases", "attempts", "resource_locks",
            "evidence", "waits", "reviews", "notifications", "acceptance_records",
            "merge_observations", "worker_progress_observations", "attempt_context_usage",
            "provider_allowance_windows", "usage_reconciliations",
            "one_active_binding_per_project", "one_active_graph_per_project",
            "one_active_lease_per_packet", "one_active_lease_per_worktree",
            "one_active_resource_key", "one_open_wait_per_packet_gate",
            "events_require_v4_metadata", "events_validate_v4_shape", "events_closed_event_type",
            "events_no_update", "events_no_delete", "evidence_no_update", "evidence_no_delete",
            "reviews_no_update", "reviews_no_delete", "secret_reference_observations_no_update",
            "secret_reference_observations_no_delete", "worker_progress_observations_no_update",
            "worker_progress_observations_no_delete", "provider_allowance_windows_no_update",
            "provider_allowance_windows_no_delete", "usage_reconciliations_no_update",
            "usage_reconciliations_no_delete", "acceptance_records_no_update",
            "acceptance_records_no_delete", "merge_observations_no_update",
            "merge_observations_no_delete",
        )
        try:
            runtime.path.mkdir()
            database = runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                _schema_three(connection)
            SQLiteFoundation(runtime.config()).health()
            with closing(sqlite3.connect(database)) as connection:
                rows = []
                for name in names:
                    row = connection.execute(
                        "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name=?", (name,)
                    ).fetchone()
                    self.assertIsNotNone(row, name)
                    rows.append({"type": row[0], "name": row[1], "table": row[2], "sql": row[3]})
            encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
            self.assertEqual(len(rows), 47)
            self.assertEqual(len(encoded), 36914)
            self.assertEqual(
                hashlib.sha256(encoded).hexdigest(),
                "3bf7930f669752d89590a7590cc580bbaf08dd21ff36ddcbe4042fa30a2084af",
            )
        finally:
            runtime.close()

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
        expected = {}
        expected[("ProjectBinding", "binding-1")] = self.store.record_binding(
            binding, "command-binding", ACTOR, NOW
        )
        expected[("SecretReferenceObservation", "secret-observation-1")] = (
            self.store.record_secret_reference(secret, "command-secret", ACTOR, NOW)
        )
        graph_result = self.store.record_graph_projection(
            graph, [work], "command-graph", ACTOR, NOW
        )
        expected[("GraphProjection", "graph-1")] = graph_result["graph"]
        expected[("WorkItem", "work-1")] = graph_result["work_items"][0]
        expected[("Run", "run-1")] = self.store.create_run(
            run, "command-run", ACTOR, NOW
        )
        expected[("Packet", "packet-1")] = self.store.materialize_packet(
            packet, "command-packet", ACTOR, NOW
        )
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
        expected[("Attempt", "attempt-1")] = self.store.record_attempt(
            attempt, "command-attempt", ACTOR, NOW
        )
        return expected

    def test_ar_p05_closed_mock_wiring_and_relation_carriers_are_exact(self) -> None:
        expected_maps = {
            "APP-MAP-01": "_actor: V02[actor_type,actor_id,correlation_id]; V10?[causation_event_id]; R17",
            "APP-MAP-02": "_binding: V02[binding_id,project_id,binding_revision,adapter_version,process_version,authority_reference,merge_policy,acceptance_authority,merge_execution_authority,state]; V04[source_commit]; V05[manifest_digest]; V03[merge_delegation_reference]; V14[binding_json]; V09[activated_at,superseded_at]; V08[now]; R01",
            "APP-MAP-03": "_secret_reference: V02[id,project_id,binding_id,owner_reference]; V06[provider]; V07[reference_name]; V09[rotation_at,expires_at]; V08[observed_at]; R02; id=secret_reference_observation_id",
            "APP-MAP-04": "_graph: V02[id,project_id,binding_id,graph_revision,authority_reference,state]; V04[source_base_sha]; V05[source_hash]; V08[observed_at,now]; R03; id=graph_projection_id",
            "APP-MAP-05": "_work_item: V02[id,graph_projection_id,architecture_node_id,task_reference,workstream_ref,milestone_ref,title,priority,specialist_role,planning_state]; V11[planned_rank]; V12[execution_classes_json,dependencies_json,change_domains_json]; V14[input_contract_json,output_contract_json]; V08[now]; R04; id=work_item_id",
            "APP-MAP-06": "_run: V02[run_id,project_id,binding_id,graph_projection_id,milestone_ref,approved_authority_reference,state,acceptance_boundary]; V05[run_fingerprint]; V03[branch_name,pull_request_reference,current_head_source_reference,candidate_head_source_reference]; V04?[current_head,candidate_head]; V08[now]; R05",
            "APP-MAP-07": "_packet: V02[packet_id,run_id,work_item_id,packet_revision,authority_reference,expected_branch,role_contract_reference,sop_reference,executor_class,integration_route,reviewer_route,state]; V04[base_commit]; V04?[current_head]; V12[owned_paths_json,forbidden_paths_json,resource_claims_json]; V13[checks_json]; V16[context_policy_json]; V11[correction_count]; V08[now]; R06",
            "APP-MAP-08": "_attempt: V02[attempt_id,packet_id,lease_id,executor_class,model_identity,runtime_identity]; V10[attempt_number]; V03[correction_for_review_id]; V04?[result_commit]; V09[started_at,finished_at]; V08[now]; R06",
            "APP-MAP-09": "_evidence: V02[evidence_id,idempotency_key,run_id,packet_id,evidence_kind]; V03[attempt_id,source_reference]; V17[payload_json]; V05[content_digest]; V08[created_at]; R07",
            "APP-MAP-10": "_wait: V02[wait_id,run_id,gate_type,awaited_role,awaited_reference,expected_result,next_permitted_action,state]; V03[packet_id]; V09[timeout_at]; V08[now]; R08[resolution_reason_payload_json,state]",
            "APP-MAP-11": "_review: V02[review_id,packet_id,reviewer_role,reviewer_instance]; V03[attempt_id]; V04[base_commit,head_commit]; V17[findings_json items]; V14[coverage_json]; V11[correction_number]; V08[created_at]; R09",
            "APP-MAP-12": "_notification: V02[notification_id,run_id,destination_reference,audience,message_type,grouping_key]; V10[event_id]; V03[packet_id]; V09[escalation_at]; V17[payload_json]; V08[now]; R10[channel,severity,state,attempt_count,last_error_payload_json,next_attempt_at]",
            "APP-MAP-13": "_worker_progress: V02[progress_id,attempt_id,next_permitted_action]; V17[plan_payload_json,current_step_payload_json,blocker_payload_json]; V08[observed_at,received_at]; R11[eta_text,confidence,status_request_state]",
            "APP-MAP-14": "_context_usage: V02[context_usage_id,attempt_id,model_identity,runtime_identity]; V03[quantization]; V10?[configured_context_limit]; V05[context_policy_digest]; V18[starting_input_measurement_json]; V21[token_measurements_json]; V19[cost_measurement_json]; V08[observed_at,now]; R12[future_growth_estimate_json,counting_method,availability_state]",
            "APP-MAP-15": "_allowance: V02[allowance_observation_id,account_reference,native_window_type,native_unit?]; V06[provider]; V15?[used_value,remaining_value]; V09[reset_at]; V08[observed_at]; R13[native_unit null relation,precision,measurement_quality,freshness]",
            "APP-MAP-16": "_reconciliation: V02[usage_reconciliation_id,allowance_observation_id,native_unit]; V15[window_change_value,tracked_controlled_value,registered_coarse_value,unattributed_value]; V08[observed_at]; R14[measurement_quality,balance]",
            "APP-MAP-17": "_acceptance: V02[acceptance_id,subject_id,authority_reference]; V03[packet_id,run_id,supersedes_acceptance_id]; V10[sequence_number]; V04[exact_head]; V14[review_coverage_json]; V17[reason_payload_json]; V08[created_at]; R15[subject_type,required_authority,decision]",
            "APP-MAP-18": "_merge_observation: V02[merge_observation_id,run_id,packet_id,repository_reference,default_branch,source_reference,performed_by_reference]; V03[acceptance_id,delegation_reference]; V04[accepted_head,merge_commit]; V14?[review_coverage_json]; V08[observed_at]; R16[source_kind,performed_by_authority]",
            "APP-MAP-19": "update_context_usage: V02[attempt_id]; V10[expected_version]; V01[update keys]; V21[token_measurements]; V19[cost_measurement]; V22[actor]; V08[observed_at,now]; R12[availability,version,precedence]",
            "APP-MAP-20": "snapshot/events_after: V02[entity_type,entity_id]; V11[event_id]; R19[entity allowlist,limit 1..1000]",
            "APP-MAP-21": "shared append: V02[idempotency_key]; V22[actor]; V08[now]; V23[replay/conflict]; V24[constraint mapping]; V25[busy exhaustion]",
        }
        expected_relations = {
            "APP-REL-01": "binding Candidate|Blocked, acceptance authority, merge delegation, null lifecycle times",
            "APP-REL-02": "secret status enum",
            "APP-REL-03": "graph Active-only and sorted unique work IDs",
            "APP-REL-04": "work graph identity and planning-state enum",
            "APP-REL-05": "run Planned-only, acceptance boundary, four initial head/source nulls",
            "APP-REL-06": "packet Planned/count-zero/head-null; attempt number/kind/correction/result/time",
            "APP-REL-07": "evidence digest, redaction enum, redacted-prose relation",
            "APP-REL-08": "wait Open and unresolved creation",
            "APP-REL-09": "review kind/result/correction and findings payload array",
            "APP-REL-10": "notification enums, source-event equality, pending unsent values",
            "APP-REL-11": "progress redacted payloads, ETA alternatives, confidence/request enums",
            "APP-REL-12": "context policy digest/fit, growth keys/quality/source/time/order, availability/precedence",
            "APP-REL-13": "allowance quality labels and available/unavailable value relation",
            "APP-REL-14": "reconciliation FK/unit/quality and exact decimal balance",
            "APP-REL-15": "acceptance Packet|Run identity/exactly-one, sequence/authority/decision/reason",
            "APP-REL-16": "merge source and performer/delegation relation",
            "APP-REL-17": "event legacy exception, metadata/shape/type/causation, append-only",
            "APP-REL-18": "public append FK/unique/check mapping plus replay/conflict",
            "APP-REL-19": "snapshot entity allowlist and events-after limit",
        }
        self.assertEqual(tuple(expected_maps), tuple(f"APP-MAP-{number:02d}" for number in range(1, 22)))
        self.assertEqual(tuple(expected_relations), tuple(f"APP-REL-{number:02d}" for number in range(1, 20)))
        self.assertEqual(
            canonical_digest({"maps": expected_maps, "relations": expected_relations}),
            "75f9d38db650cfeffdaf14731052f49c4e8f7dae449a90f030b4369a980e8521",
        )

        helper_names = (
            "_closed_mapping", "_text", "_optional_text", "_commit", "_digest",
            "_provider", "_reference_name", "_timestamp", "_optional_timestamp",
            "_positive_int", "_nonnegative_int", "_sorted_unique_text", "canonical_json",
            "_json_object", "_decimal_text", "validate_context_policy", "validate_payload",
            "validate_measurement", "validate_cost_measurement", "preferred_measurement",
            "_token_measurements", "_actor",
        )
        patches = {
            name: mock.patch.object(operational_state, name, wraps=getattr(operational_state, name))
            for name in helper_names
        }
        started = {name: patch.start() for name, patch in patches.items()}
        try:
            self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
        finally:
            for patch in reversed(tuple(patches.values())):
                patch.stop()
        for name, wrapped in started.items():
            with self.subTest(helper=name):
                self.assertGreater(wrapped.call_count, 0)

    def test_ar_p05_high_risk_builder_wiring_matches_the_frozen_map(self) -> None:
        binding, _, _, _, run, packet = self._records()
        with mock.patch.object(
            operational_state, "_optional_timestamp", wraps=operational_state._optional_timestamp
        ) as optional_timestamp:
            OperationalStateStore._binding(binding, NOW)
        self.assertEqual(
            [(call.args[1], call.args[0]) for call in optional_timestamp.call_args_list],
            [("activated_at", None), ("superseded_at", None)],
        )

        with mock.patch.object(operational_state, "_text", wraps=operational_state._text) as text_validator:
            OperationalStateStore._run(run, NOW)
        self.assertEqual(
            {call.args[1] for call in text_validator.call_args_list},
            {
                "run_id", "project_id", "binding_id", "graph_projection_id", "milestone_ref",
                "approved_authority_reference", "state", "acceptance_boundary",
            },
        )

        with mock.patch.object(
            operational_state, "_nonnegative_int", wraps=operational_state._nonnegative_int
        ) as nonnegative_int:
            OperationalStateStore._packet(packet, NOW)
        self.assertEqual(
            [(call.args[1], call.args[0]) for call in nonnegative_int.call_args_list],
            [("correction_count", 0)],
        )
        with self.assertRaisesRegex(
            InvalidRecord, "^correction_count must be a non-negative integer$"
        ):
            OperationalStateStore._packet(dict(packet, correction_count=False), NOW)

    def test_ar_p05_app_map_01_through_21_have_exact_per_route_mock_traces(self) -> None:
        builder_names = (
            "_binding", "_secret_reference", "_graph", "_work_item", "_run", "_packet",
            "_attempt", "_evidence", "_wait", "_review", "_notification",
            "_worker_progress", "_context_usage", "_allowance", "_reconciliation",
            "_acceptance", "_merge_observation",
        )
        originals = {name: getattr(OperationalStateStore, name) for name in builder_names}
        captured = {name: [] for name in builder_names}
        capture_patches = []
        for name in builder_names:
            def side_effect(*args, _name=name, **kwargs):
                captured[_name].append(copy.deepcopy(args[0]))
                return originals[_name](*args, **kwargs)
            patch = mock.patch.object(OperationalStateStore, name, side_effect=side_effect)
            patch.start()
            capture_patches.append(patch)
        try:
            self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
        finally:
            for patch in reversed(capture_patches):
                patch.stop()
        valid = {name: values[-1] for name, values in captured.items()}

        helper_codes = {
            "_closed_mapping": "V01", "_text": "V02", "_optional_text": "V03",
            "_commit": "V04", "_digest": "V05", "_provider": "V06",
            "_reference_name": "V07", "_timestamp": "V08",
            "_optional_timestamp": "V09", "_positive_int": "V10",
            "_nonnegative_int": "V11", "_sorted_unique_text": "V12",
            "canonical_json": "V13", "_json_object": "V14", "_decimal_text": "V15",
            "validate_context_policy": "V16", "validate_payload": "V17",
            "validate_measurement": "V18", "validate_cost_measurement": "V19",
            "_token_measurements": "V21", "_actor": "V22", "_replay": "V23",
        }
        aliases = {
            "APP-MAP-03": {"secret_reference_observation_id": "id"},
            "APP-MAP-04": {"graph_projection_id": "id"},
            "APP-MAP-05": {"work_item_id": "id"},
            "APP-MAP-19": {"context update observed_at": "observed_at"},
        }
        queued_labels = {
            "APP-MAP-07": {"V13": ["checks_json"], "V16": ["context_policy_json"]},
            "APP-MAP-09": {"V17": ["payload_json"]},
            "APP-MAP-11": {"V17": ["findings_json items"]},
            "APP-MAP-12": {"V17": ["payload_json"]},
            "APP-MAP-13": {"V17": ["plan_payload_json", "current_step_payload_json", "blocker_payload_json"]},
            "APP-MAP-14": {
                "V18": ["starting_input_measurement_json", None, None],
                "V21": ["token_measurements_json"], "V19": ["cost_measurement_json"],
            },
            "APP-MAP-17": {"V17": ["reason_payload_json"]},
            "APP-MAP-19": {
                "V01": ["update keys"], "V21": ["token_measurements"],
                "V19": ["cost_measurement"], "V22": ["actor"],
            },
            "APP-MAP-21": {"V22": ["actor"], "V23": ["replay/conflict"]},
        }

        def fields(code, *names):
            return {(code, name) for name in names}

        expected = {
            "APP-MAP-01": fields("V02", "actor_type", "actor_id", "correlation_id") | fields("V10", "causation_event_id") | {("R17", "")},
            "APP-MAP-02": fields("V02", "binding_id", "project_id", "binding_revision", "adapter_version", "process_version", "authority_reference", "merge_policy", "acceptance_authority", "merge_execution_authority", "state") | fields("V04", "source_commit") | fields("V05", "manifest_digest") | fields("V03", "merge_delegation_reference") | fields("V14", "binding_json") | fields("V09", "activated_at", "superseded_at") | fields("V08", "now") | {("R01", "")},
            "APP-MAP-03": fields("V02", "id", "project_id", "binding_id", "owner_reference") | fields("V06", "provider") | fields("V07", "reference_name") | fields("V09", "rotation_at", "expires_at") | fields("V08", "observed_at") | {("R02", "")},
            "APP-MAP-04": fields("V02", "id", "project_id", "binding_id", "graph_revision", "authority_reference", "state") | fields("V04", "source_base_sha") | fields("V05", "source_hash") | fields("V08", "observed_at", "now") | {("R03", "")},
            "APP-MAP-05": fields("V02", "id", "graph_projection_id", "architecture_node_id", "task_reference", "workstream_ref", "milestone_ref", "title", "priority", "specialist_role", "planning_state") | fields("V11", "planned_rank") | fields("V12", "execution_classes_json", "dependencies_json", "change_domains_json") | fields("V14", "input_contract_json", "output_contract_json") | fields("V08", "now") | {("R04", "")},
            "APP-MAP-06": fields("V02", "run_id", "project_id", "binding_id", "graph_projection_id", "milestone_ref", "approved_authority_reference", "state", "acceptance_boundary") | fields("V05", "run_fingerprint") | fields("V03", "branch_name", "pull_request_reference", "current_head_source_reference", "candidate_head_source_reference") | fields("V08", "now") | {("R05", "")},
            "APP-MAP-07": fields("V02", "packet_id", "run_id", "work_item_id", "packet_revision", "authority_reference", "expected_branch", "role_contract_reference", "sop_reference", "executor_class", "integration_route", "reviewer_route", "state") | fields("V04", "base_commit") | fields("V12", "owned_paths_json", "forbidden_paths_json", "resource_claims_json") | fields("V13", "checks_json") | fields("V16", "context_policy_json") | fields("V11", "correction_count") | fields("V08", "now") | {("R06", "")},
            "APP-MAP-08": fields("V02", "attempt_id", "packet_id", "lease_id", "executor_class", "model_identity", "runtime_identity") | fields("V10", "attempt_number") | fields("V03", "correction_for_review_id") | fields("V09", "started_at", "finished_at") | fields("V08", "now") | {("R06", "")},
            "APP-MAP-09": fields("V02", "evidence_id", "idempotency_key", "run_id", "packet_id", "evidence_kind") | fields("V03", "attempt_id", "source_reference") | fields("V17", "payload_json") | fields("V05", "content_digest") | fields("V08", "created_at") | {("R07", "")},
            "APP-MAP-10": fields("V02", "wait_id", "run_id", "gate_type", "awaited_role", "awaited_reference", "expected_result", "next_permitted_action", "state") | fields("V03", "packet_id") | fields("V09", "timeout_at") | fields("V08", "now") | {("R08", "")},
            "APP-MAP-11": fields("V02", "review_id", "packet_id", "reviewer_role", "reviewer_instance") | fields("V03", "attempt_id") | fields("V04", "base_commit", "head_commit") | fields("V17", "findings_json items") | fields("V14", "coverage_json") | fields("V11", "correction_number") | fields("V08", "created_at") | {("R09", "")},
            "APP-MAP-12": fields("V02", "notification_id", "run_id", "destination_reference", "audience", "message_type", "grouping_key") | fields("V10", "event_id") | fields("V03", "packet_id") | fields("V09", "escalation_at") | fields("V17", "payload_json") | fields("V08", "now") | {("R10", "")},
            "APP-MAP-13": fields("V02", "progress_id", "attempt_id", "next_permitted_action") | fields("V17", "plan_payload_json", "current_step_payload_json", "blocker_payload_json") | fields("V08", "observed_at", "received_at") | {("R11", "")},
            "APP-MAP-14": fields("V02", "context_usage_id", "attempt_id", "model_identity", "runtime_identity") | fields("V03", "quantization") | fields("V10", "configured_context_limit") | fields("V05", "context_policy_digest") | fields("V18", "starting_input_measurement_json") | fields("V21", "token_measurements_json") | fields("V19", "cost_measurement_json") | fields("V08", "observed_at", "now") | {("R12", "")},
            "APP-MAP-15": fields("V02", "allowance_observation_id", "account_reference", "native_window_type", "native_unit") | fields("V06", "provider") | fields("V15", "used_value", "remaining_value") | fields("V09", "reset_at") | fields("V08", "observed_at") | {("R13", "")},
            "APP-MAP-16": fields("V02", "usage_reconciliation_id", "allowance_observation_id", "native_unit") | fields("V15", "window_change_value", "tracked_controlled_value", "registered_coarse_value", "unattributed_value") | fields("V08", "observed_at") | {("R14", "")},
            "APP-MAP-17": fields("V02", "acceptance_id", "subject_id", "authority_reference") | fields("V03", "packet_id", "run_id", "supersedes_acceptance_id") | fields("V10", "sequence_number") | fields("V04", "exact_head") | fields("V14", "review_coverage_json") | fields("V17", "reason_payload_json") | fields("V08", "created_at") | {("R15", "")},
            "APP-MAP-18": fields("V02", "merge_observation_id", "run_id", "packet_id", "repository_reference", "default_branch", "source_reference", "performed_by_reference") | fields("V03", "acceptance_id", "delegation_reference") | fields("V04", "accepted_head", "merge_commit") | fields("V14", "review_coverage_json") | fields("V08", "observed_at") | {("R16", "")},
            "APP-MAP-19": fields("V02", "attempt_id") | fields("V10", "expected_version") | fields("V01", "update keys") | fields("V21", "token_measurements") | fields("V19", "cost_measurement") | fields("V22", "actor") | fields("V08", "observed_at", "now") | {("R12", "")},
            "APP-MAP-20": fields("V02", "entity_type", "entity_id") | fields("V11", "event_id") | {("R19", "")},
            "APP-MAP-21": fields("V02", "idempotency_key") | fields("V22", "actor") | fields("V08", "now") | fields("V23", "replay/conflict") | {("V24", "constraint mapping"), ("V25", "busy exhaustion")},
        }
        relation_internal = {
            "APP-MAP-19": {
                ("V02", "idempotency_key"), ("V02", "measurement source"),
                ("V08", "measurement observed_at"),
            },
        }

        def payloads_are_redacted(row):
            return all(
                row[field]["kind"] == "redacted-text"
                and row[field]["redaction_status"] == "Redacted"
                for field in (
                    "plan_payload_json", "current_step_payload_json", "blocker_payload_json"
                )
            )

        relation_observers = {
            ("APP-MAP-01", "R17"): lambda row: row == {
                "actor_type": "Developer", "actor_id": "developer-1",
                "correlation_id": "correlation-1", "causation_event_id": 1,
            },
            ("APP-MAP-02", "R01"): lambda row: row["state"] in {"Candidate", "Blocked"}
            and row["acceptance_authority"] in {"ProjectArchitect", "Owner"}
            and row["merge_execution_authority"] == "OwnerPerformed"
            and row["merge_delegation_reference"] is None
            and row["activated_at"] is None and row["superseded_at"] is None,
            ("APP-MAP-03", "R02"): lambda row: row["status"] in {
                "Active", "Stale", "Revoked", "Unavailable"
            },
            ("APP-MAP-04", "R03"): lambda result: result[0] == NOW
            and result[1]["state"] == "Active" and result[1]["version"] == 1,
            ("APP-MAP-05", "R04"): lambda result: result[0] == NOW
            and result[1]["graph_projection_id"] == valid["_work_item"]["graph_projection_id"]
            and result[1]["planning_state"] in {"Active", "NeedsReplan", "Superseded"},
            ("APP-MAP-06", "R05"): lambda row: row["state"] == "Planned"
            and row["acceptance_boundary"] in {"ProjectArchitect", "Owner"}
            and all(row[field] is None for field in (
                "current_head", "current_head_source_reference", "candidate_head",
                "candidate_head_source_reference",
            )),
            ("APP-MAP-07", "R06"): lambda row: row["state"] == "Planned"
            and row["correction_count"] == 0 and row["current_head"] is None,
            ("APP-MAP-08", "R06"): lambda row: row["attempt_number"] == 1
            and row["attempt_kind"] == "Initial" and row["state"] == "Planned"
            and row["correction_for_review_id"] is None
            and all(row[field] is None for field in ("result_commit", "started_at", "finished_at")),
            ("APP-MAP-09", "R07"): lambda row: row["content_digest"]
            == canonical_digest(row["payload_json"])
            and row["redaction_state"] in {"Redacted", "NotRequired"},
            ("APP-MAP-10", "R08"): lambda row: row["state"] == "Open"
            and row["resolution_reason_payload_json"] is None,
            ("APP-MAP-11", "R09"): lambda row: row["review_kind"] in {
                "Integration", "IndependentImplementation"
            } and row["result"] in {
                "ValidateOnly", "Assemble", "NeedsReplan", "Approve",
                "RequestChanges", "Comment",
            } and row["correction_number"] in {0, 1}
            and isinstance(row["findings_json"], list),
            ("APP-MAP-12", "R10"): lambda row: row["channel"] in {"LocalDurable", "Slack"}
            and row["payload_json"]["event_id"] == row["event_id"]
            and row["state"] == "Pending" and row["attempt_count"] == 0
            and row["last_error_payload_json"] is None and row["next_attempt_at"] is None,
            ("APP-MAP-13", "R11"): lambda row: payloads_are_redacted(row)
            and row["eta_text"] == "unknown" and row["confidence"] == "Unknown"
            and row["status_request_state"] == "NotRequested",
            ("APP-MAP-14", "R12"): lambda row: row["counting_method"] in {
                "Runtime", "Tokenizer", "Estimate", "Unavailable"
            } and row["availability_state"] in {"Available", "Partial", "Unavailable"}
            and row["future_growth_estimate_json"]["lower_bound"]["value"]
            <= row["future_growth_estimate_json"]["upper_bound"]["value"],
            ("APP-MAP-15", "R13"): lambda row: row["precision"] in {
                "Exact", "Coarse", "Unavailable"
            } and row["measurement_quality"] in {
                "RuntimeReported", "ProviderReported", "Estimated", "Unavailable"
            } and row["freshness"] in {"Fresh", "Stale", "Unavailable"}
            and row["native_unit"] is not None,
            ("APP-MAP-16", "R14"): lambda row: row["measurement_quality"] in {
                "Exact", "Coarse", "Estimated"
            } and row["window_change_value"] == "10.5"
            and (row["tracked_controlled_value"], row["registered_coarse_value"], row["unattributed_value"])
            == ("4", "5", "1.5"),
            ("APP-MAP-17", "R15"): lambda row: row["subject_type"] == "Packet"
            and row["subject_id"] == row["packet_id"] and row["run_id"] is None
            and row["sequence_number"] in {1, 2}
            and row["reason_payload_json"]["kind"] == "reason",
            ("APP-MAP-18", "R16"): lambda row: row["source_kind"] in {"Git", "GitHub"}
            and row["performed_by_authority"] == "DelegatedIdentity"
            and row["delegation_reference"] is not None,
            ("APP-MAP-19", "R12"): lambda row: row["version"] == 3
            and row["availability_state"] == "Available"
            and all(item["quality"] == "RuntimeReported" for item in row["token_measurements_json"].values()),
            ("APP-MAP-20", "R19"): lambda result: result[0]["binding_id"] == "binding-1"
            and len(result[1]) == 1 and result[1][0]["event_id"] > 0,
        }
        boundary_observers = {
            "V24": lambda evidence: isinstance(evidence["error"], InvalidRecord)
            and str(evidence["error"]) == "record violates a durable schema constraint"
            and isinstance(evidence["error"].__cause__, sqlite3.IntegrityError)
            and evidence["error"].__cause__.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE"
            and evidence["before"] == evidence["after"],
            "V25": lambda evidence: isinstance(evidence["error"], ResourceBusy)
            and str(evidence["error"]) == "SQLite busy timeout exhausted"
            and evidence["elapsed"] >= 4.5 and evidence["before"] == evidence["after"],
        }

        def trace(route_id, command, boundary_evidence=None):
            calls = set()
            depth = [0]
            queues = {code: list(values) for code, values in queued_labels.get(route_id, {}).items()}
            active_patches = []
            expected_codes = {code for code, _ in expected[route_id] if code.startswith("V")}

            def label_for(name, code, args):
                if code in queues:
                    return queues[code].pop(0) if queues[code] else None
                if name == "_provider":
                    return "provider"
                if name == "_reference_name":
                    return "reference_name"
                if len(args) > 1 and isinstance(args[1], str):
                    return aliases.get(route_id, {}).get(args[1], args[1])
                return None

            for name, code in helper_codes.items():
                if code not in expected_codes:
                    continue
                target = OperationalStateStore if name == "_replay" else operational_state
                original = getattr(target, name)

                def wrapper(*args, _name=name, _code=code, _original=original, **kwargs):
                    top = depth[0] == 0
                    depth[0] += 1
                    try:
                        result = _original(*args, **kwargs)
                    finally:
                        depth[0] -= 1
                    if top:
                        label = label_for(_name, _code, args)
                        if label is not None:
                            calls.add((_code, label))
                    return result

                patch = mock.patch.object(target, name, side_effect=wrapper)
                patch.start()
                active_patches.append(patch)
            try:
                result = command()
            finally:
                for patch in reversed(active_patches):
                    patch.stop()
            expected_relations = {
                item for item in expected[route_id] if item[0].startswith("R")
            }
            observed_relations = {
                item for item in expected_relations
                if relation_observers[(route_id, item[0])](result)
            }
            self.assertEqual(observed_relations, expected_relations, route_id)
            calls.update(observed_relations)
            expected_boundaries = {
                item for item in expected[route_id] if item[0] in boundary_observers
            }
            observed_boundaries = {
                item for item in expected_boundaries
                if boundary_evidence is not None
                and boundary_observers[item[0]](boundary_evidence[item[0]])
            }
            self.assertEqual(observed_boundaries, expected_boundaries, route_id)
            calls.update(observed_boundaries)
            internal = relation_internal.get(route_id, set())
            self.assertEqual(calls, expected[route_id] | internal, route_id)
            self.assertEqual(calls - internal, expected[route_id], route_id)

        trace("APP-MAP-01", lambda: operational_state._actor({"actor_type": "Developer", "actor_id": "developer-1", "correlation_id": "correlation-1", "causation_event_id": 1}))
        trace("APP-MAP-02", lambda: OperationalStateStore._binding(valid["_binding"], NOW))
        trace("APP-MAP-03", lambda: OperationalStateStore._secret_reference(valid["_secret_reference"]))
        trace("APP-MAP-04", lambda: (operational_state._timestamp(NOW, "now"), OperationalStateStore._graph(valid["_graph"], NOW)))
        trace("APP-MAP-05", lambda: (operational_state._timestamp(NOW, "now"), OperationalStateStore._work_item(valid["_work_item"], valid["_work_item"]["graph_projection_id"], NOW)))
        trace("APP-MAP-06", lambda: OperationalStateStore._run(valid["_run"], NOW))
        trace("APP-MAP-07", lambda: OperationalStateStore._packet(valid["_packet"], NOW))
        trace("APP-MAP-08", lambda: OperationalStateStore._attempt(valid["_attempt"], NOW))
        trace("APP-MAP-09", lambda: OperationalStateStore._evidence(valid["_evidence"]))
        trace("APP-MAP-10", lambda: OperationalStateStore._wait(valid["_wait"], NOW))
        review = dict(valid["_review"], findings_json=[{"kind": "reason", "reason_code": "NONE", "detail_reference": None}])
        trace("APP-MAP-11", lambda: OperationalStateStore._review(review))
        trace("APP-MAP-12", lambda: OperationalStateStore._notification(valid["_notification"], NOW))
        trace("APP-MAP-13", lambda: OperationalStateStore._worker_progress(valid["_worker_progress"]))
        trace("APP-MAP-14", lambda: OperationalStateStore._context_usage(valid["_context_usage"], NOW))
        trace("APP-MAP-15", lambda: OperationalStateStore._allowance(valid["_allowance"]))
        trace("APP-MAP-16", lambda: OperationalStateStore._reconciliation(valid["_reconciliation"]))
        trace("APP-MAP-17", lambda: OperationalStateStore._acceptance(valid["_acceptance"]))
        trace("APP-MAP-18", lambda: OperationalStateStore._merge_observation(valid["_merge_observation"]))

        context = self.store.snapshot("AttemptContextUsage", "context-1")
        update = {
            "token_measurements": {name: dict(value, value=value["value"] + 1) for name, value in context["token_measurements_json"].items()},
            "cost_measurement": context["cost_measurement_json"], "availability_state": "Available",
            "observed_at": LATER,
        }
        trace("APP-MAP-19", lambda: self.store.update_context_usage("attempt-1", 2, update, "trace-map-19", ACTOR, LATER))
        trace("APP-MAP-20", lambda: (self.store.snapshot("ProjectBinding", "binding-1"), self.store.events_after(0, 1)))

        append_row = OperationalStateStore._binding(dict(valid["_binding"], binding_id="trace-binding", binding_revision="trace-revision"), NOW)
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            constraint_before = _durable_state(connection)
        try:
            self.store.record_binding(
                dict(valid["_binding"], binding_id="trace-constraint"),
                "trace-map-21-constraint", ACTOR, NOW,
            )
        except InvalidRecord as error:
            constraint_error = error
        else:  # pragma: no cover - exact evidence assertion below
            self.fail("MAP-21 constraint route unexpectedly succeeded")
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            constraint_after = _durable_state(connection)

        database = self.runtime.path / "maestro.sqlite3"
        with closing(sqlite3.connect(database, timeout=0)) as holder:
            holder.execute("PRAGMA journal_mode=WAL")
            holder.execute("BEGIN IMMEDIATE")
            busy_before = _durable_state(holder)
            started = time.monotonic()
            try:
                self.store.record_binding(
                    dict(valid["_binding"], binding_id="trace-busy", binding_revision="trace-busy"),
                    "trace-map-21-busy", ACTOR, NOW,
                )
            except ResourceBusy as error:
                busy_error = error
            else:  # pragma: no cover - exact evidence assertion below
                self.fail("MAP-21 busy route unexpectedly succeeded")
            busy_elapsed = time.monotonic() - started
            busy_after = _durable_state(holder)
            holder.rollback()
        boundary_evidence = {
            "V24": {
                "error": constraint_error, "before": constraint_before,
                "after": constraint_after,
            },
            "V25": {
                "error": busy_error, "elapsed": busy_elapsed,
                "before": busy_before, "after": busy_after,
            },
        }
        trace(
            "APP-MAP-21",
            lambda: self.store._append(
                "record_project_bindings", append_row, "ProjectBinding", "trace-binding",
                "ProjectBindingRecorded", "trace-map-21", ACTOR, NOW,
                lambda connection: self.store._insert(connection, "project_bindings", append_row),
            ),
            boundary_evidence=boundary_evidence,
        )

    def test_ar_p05_app_rel_01_through_19_exact_negative_edges(self) -> None:
        builder_names = (
            "_binding", "_secret_reference", "_graph", "_work_item", "_run", "_packet",
            "_attempt", "_evidence", "_wait", "_review", "_notification",
            "_worker_progress", "_context_usage", "_allowance", "_reconciliation",
            "_acceptance", "_merge_observation",
        )
        originals = {name: getattr(OperationalStateStore, name) for name in builder_names}
        captured = {name: [] for name in builder_names}
        patches = []
        for name in builder_names:
            def side_effect(*args, _name=name, **kwargs):
                captured[_name].append(copy.deepcopy(args[0]))
                return originals[_name](*args, **kwargs)
            patch = mock.patch.object(OperationalStateStore, name, side_effect=side_effect)
            patch.start()
            patches.append(patch)
        try:
            self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
        finally:
            for patch in reversed(patches):
                patch.stop()

        valid = {name: values[-1] for name, values in captured.items()}

        def changed(name, **changes):
            return dict(valid[name], **changes)

        def invalid(case_id, message, command):
            with self.subTest(case=case_id, message=message), self.assertRaisesRegex(
                InvalidRecord, f"^{re.escape(message)}$"
            ):
                command()

        binding_cases = (
            ("record_binding accepts Candidate or Blocked only", {"state": "Active"}),
            ("binding acceptance authority is invalid", {"acceptance_authority": "Other"}),
            ("owner-performed merge cannot carry delegation", {"merge_delegation_reference": "policy"}),
            ("delegated merge requires its reviewed policy reference", {"merge_execution_authority": "PolicyDelegated", "merge_delegation_reference": None}),
            ("merge execution authority is invalid", {"merge_execution_authority": "Other"}),
            ("candidate/blocked binding has no activation/supersession time", {"activated_at": NOW}),
        )
        for message, changes in binding_cases:
            invalid("APP-REL-01", message, lambda changes=changes: OperationalStateStore._binding(changed("_binding", **changes), NOW))
        invalid("APP-REL-02", "secret reference status is invalid", lambda: OperationalStateStore._secret_reference(changed("_secret_reference", status="Other")))
        invalid("APP-REL-03", "record_graph_projection creates Active projections only", lambda: OperationalStateStore._graph(changed("_graph", state="Stale"), NOW))
        work = valid["_work_item"]
        invalid("APP-REL-03", "work_items must be sorted and unique by work_item_id", lambda: self.store.record_graph_projection(changed("_graph", graph_projection_id="graph-ar-rel03", graph_revision="graph-ar-rel03", source_hash="c" * 64), [dict(work, graph_projection_id="graph-ar-rel03", work_item_id="z"), dict(work, graph_projection_id="graph-ar-rel03", work_item_id="a", architecture_node_id="node-a")], "ar-rel03", ACTOR, NOW))
        invalid("APP-REL-04", "work item belongs to a different graph projection", lambda: OperationalStateStore._work_item(changed("_work_item", graph_projection_id="other"), "graph-1", NOW))
        invalid("APP-REL-04", "work-item planning state is invalid", lambda: OperationalStateStore._work_item(changed("_work_item", planning_state="Other"), "graph-1", NOW))

        run_cases = [
            ("create_run creates Planned runs only", {"state": "Running"}),
            ("run acceptance boundary is invalid", {"acceptance_boundary": "Other"}),
        ] + [("planned run cannot begin with observed/candidate head", {field: COMMIT_B if field in {"current_head", "candidate_head"} else "source"}) for field in ("current_head", "current_head_source_reference", "candidate_head", "candidate_head_source_reference")]
        for message, changes in run_cases:
            invalid("APP-REL-05", message, lambda changes=changes: OperationalStateStore._run(changed("_run", **changes), NOW))

        packet_cases = (
            ("materialized packet starts Planned with correction count zero", {"state": "Ready"}),
            ("materialized packet starts Planned with correction count zero", {"correction_count": 1}),
            ("materialized packet has no current head", {"current_head": COMMIT_B}),
        )
        for message, changes in packet_cases:
            invalid("APP-REL-06", message, lambda changes=changes: OperationalStateStore._packet(changed("_packet", **changes), NOW))
        attempt_cases = (
            ("attempt number is invalid", {"attempt_number": 3}),
            ("attempt creation facts are invalid", {"attempt_kind": "TargetedCorrection"}),
            ("initial attempt cannot reference a correction review", {"correction_for_review_id": "review-1"}),
            ("targeted correction requires a review reference", {"attempt_number": 2, "attempt_kind": "TargetedCorrection", "correction_for_review_id": None}),
            ("planned attempt has no result/start/finish facts", {"result_commit": COMMIT_B}),
            ("planned attempt has no result/start/finish facts", {"started_at": NOW}),
            ("planned attempt has no result/start/finish facts", {"finished_at": NOW}),
        )
        for message, changes in attempt_cases:
            invalid("APP-REL-06", message, lambda changes=changes: OperationalStateStore._attempt(changed("_attempt", **changes), NOW))

        evidence = valid["_evidence"]
        invalid("APP-REL-07", "evidence digest does not cover its canonical payload", lambda: OperationalStateStore._evidence(dict(evidence, content_digest="b" * 64)))
        invalid("APP-REL-07", "evidence redaction state is invalid", lambda: OperationalStateStore._evidence(dict(evidence, redaction_state="Other")))
        redacted = _redacted("safe")
        invalid("APP-REL-07", "redacted prose evidence must be marked Redacted", lambda: OperationalStateStore._evidence(dict(evidence, payload_json=redacted, content_digest=canonical_digest(redacted), redaction_state="NotRequired")))
        invalid("APP-REL-08", "open_wait creates unresolved Open waits only", lambda: OperationalStateStore._wait(changed("_wait", state="Resolved"), NOW))
        invalid("APP-REL-08", "open_wait creates unresolved Open waits only", lambda: OperationalStateStore._wait(changed("_wait", resolution_reason_payload_json={"kind": "reason", "reason_code": "DONE", "detail_reference": None}), NOW))
        review_cases = (
            ("review kind is invalid", {"review_kind": "Other"}),
            ("review result is invalid", {"result": "Other"}),
            ("review findings must be an array", {"findings_json": {}}),
            ("review correction number is invalid", {"correction_number": 2}),
        )
        for message, changes in review_cases:
            invalid("APP-REL-09", message, lambda changes=changes: OperationalStateStore._review(changed("_review", **changes)))
        notification_cases = (
            ("notification channel or severity is invalid", {"channel": "Other"}),
            ("notification channel or severity is invalid", {"severity": "Other"}),
            ("notification payload must reference its source event", {"payload_json": dict(valid["_notification"]["payload_json"], event_id=999)}),
            ("record_notification stores a pending unsent record", {"state": "Delivered"}),
            ("record_notification stores a pending unsent record", {"attempt_count": 1}),
            ("record_notification stores a pending unsent record", {"last_error_payload_json": {"kind": "reason", "reason_code": "X", "detail_reference": None}}),
            ("record_notification stores a pending unsent record", {"next_attempt_at": LATER}),
        )
        for message, changes in notification_cases:
            invalid("APP-REL-10", message, lambda changes=changes: OperationalStateStore._notification(changed("_notification", **changes), NOW))
        progress_cases = (
            ("worker progress prose must be pre-redacted with a receipt", {"plan_payload_json": {"kind": "reason", "reason_code": "X", "detail_reference": None}}),
            ("worker ETA must be unknown, UTC time, or ISO-8601 duration", {"eta_text": "soon"}),
            ("worker progress confidence/status request state is invalid", {"confidence": "Other"}),
            ("worker progress confidence/status request state is invalid", {"status_request_state": "Other"}),
        )
        for message, changes in progress_cases:
            invalid("APP-REL-11", message, lambda changes=changes: OperationalStateStore._worker_progress(changed("_worker_progress", **changes)))

        context = valid["_context_usage"]
        growth = context["future_growth_estimate_json"]
        context_cases = (
            ("future growth estimate has an invalid closed shape", {"future_growth_estimate_json": dict(growth, extra=True)}),
            ("future growth bounds must be explicit estimates", {"future_growth_estimate_json": dict(growth, lower_bound=_measurement(1))}),
            ("future growth bounds must share source and time", {"future_growth_estimate_json": dict(growth, upper_bound=_measurement(200, "Estimated", "Medium", "other"))}),
            ("future growth lower bound exceeds upper bound", {"future_growth_estimate_json": {"lower_bound": _measurement(300, "Estimated", "Medium", "estimate"), "upper_bound": _measurement(200, "Estimated", "Medium", "estimate")}}),
            ("context availability is invalid", {"availability_state": "Other"}),
        )
        for message, changes in context_cases:
            invalid("APP-REL-12", message, lambda changes=changes: OperationalStateStore._context_usage(dict(context, **changes), NOW))
        allowance_cases = (
            ("allowance quality state is invalid", {"precision": "Other"}),
            ("unavailable allowance values must remain null", {"precision": "Unavailable", "measurement_quality": "Unavailable", "freshness": "Unavailable"}),
            ("unavailable allowance labels must agree", {"precision": "Unavailable", "measurement_quality": "ProviderReported", "freshness": "Fresh", "used_value": None, "remaining_value": None, "native_unit": None, "reset_at": None}),
            ("available allowance needs a used or remaining value", {"used_value": None, "remaining_value": None}),
        )
        for message, changes in allowance_cases:
            invalid("APP-REL-13", message, lambda changes=changes: OperationalStateStore._allowance(changed("_allowance", **changes)))
        invalid("APP-REL-14", "reconciliation quality is invalid", lambda: OperationalStateStore._reconciliation(changed("_reconciliation", measurement_quality="Other")))
        invalid("APP-REL-14", "usage reconciliation does not balance exactly", lambda: OperationalStateStore._reconciliation(changed("_reconciliation", unattributed_value="1")))
        acceptance_cases = (
            ("acceptance closed enum is invalid", {"subject_type": "Other"}),
            ("acceptance closed enum is invalid", {"sequence_number": 3}),
            ("acceptance closed enum is invalid", {"required_authority": "Other"}),
            ("acceptance closed enum is invalid", {"decision": "Other"}),
            ("packet acceptance relation is invalid", {"subject_id": "other"}),
            ("packet acceptance relation is invalid", {"run_id": "run-1"}),
            ("acceptance reason must be a reason payload", {"reason_payload_json": {"kind": "state", "entity_type": "Packet", "entity_id": "packet-1", "state": "Planned", "version": 1}}),
        )
        for message, changes in acceptance_cases:
            invalid("APP-REL-15", message, lambda changes=changes: OperationalStateStore._acceptance(changed("_acceptance", **changes)))
        merge_cases = (
            ("merge source kind is invalid", {"source_kind": "Other"}),
            ("owner observation cannot carry delegation", {"performed_by_authority": "Owner", "delegation_reference": "policy"}),
            ("delegated observation requires delegation reference", {"delegation_reference": None}),
            ("merge performer authority is invalid", {"performed_by_authority": "Other"}),
        )
        for message, changes in merge_cases:
            invalid("APP-REL-16", message, lambda changes=changes: OperationalStateStore._merge_observation(changed("_merge_observation", **changes)))

        database = self.runtime.path / "maestro.sqlite3"
        with closing(sqlite3.connect(database)) as connection:
            trigger_names = {row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )}
            self.assertTrue({"events_require_v4_metadata", "events_validate_v4_shape", "events_closed_event_type", "events_no_update", "events_no_delete"} <= trigger_names)
            self.assertEqual(connection.execute(
                "SELECT COUNT(*) FROM events WHERE entity_type!='ProjectRegistrationRun' AND "
                "(correlation_id IS NULL OR actor_type IS NULL OR actor_id IS NULL OR "
                "command_fingerprint IS NULL OR observed_at IS NULL)"
            ).fetchone()[0], 0)
            before_event_rows = connection.execute("SELECT * FROM events ORDER BY event_id").fetchall()
            with self.subTest(case="APP-REL-17"), self.assertRaisesRegex(
                sqlite3.IntegrityError, "^events are append-only$"
            ):
                connection.execute("UPDATE events SET reason=reason WHERE event_id=(SELECT MIN(event_id) FROM events)")
            connection.rollback()
            self.assertEqual(connection.execute("SELECT * FROM events ORDER BY event_id").fetchall(), before_event_rows)

        with closing(sqlite3.connect(database)) as connection:
            before_append = _durable_state(connection)
        with self.subTest(case="APP-REL-18"), self.assertRaisesRegex(
            InvalidRecord, "^record violates a durable schema constraint$"
        ) as raised:
            self.store.record_binding(
                changed("_binding", binding_id="ar-rel18-duplicate"), "ar-rel18", ACTOR, NOW
            )
        self.assertEqual(raised.exception.__cause__.sqlite_errorname, "SQLITE_CONSTRAINT_UNIQUE")
        with closing(sqlite3.connect(database)) as connection:
            self.assertEqual(_durable_state(connection), before_append)

        invalid("APP-REL-19", "entity_type is not snapshot-readable", lambda: self.store.snapshot("Other", "id"))
        invalid("APP-REL-19", "event limit must be between 1 and 1000", lambda: self.store.events_after(0, 0))
        invalid("APP-REL-19", "event limit must be between 1 and 1000", lambda: self.store.events_after(0, 1001))

    def test_ar_p06_every_named_app_negative_edge_is_public_route_durable(self) -> None:
        builder_names = (
            "_binding", "_secret_reference", "_graph", "_work_item", "_run", "_packet",
            "_attempt", "_evidence", "_wait", "_review", "_notification",
            "_worker_progress", "_context_usage", "_allowance", "_reconciliation",
            "_acceptance", "_merge_observation",
        )
        originals = {name: getattr(OperationalStateStore, name) for name in builder_names}
        captured = {name: [] for name in builder_names}
        capture_patches = []
        for name in builder_names:
            def side_effect(*args, _name=name, **kwargs):
                captured[_name].append(copy.deepcopy(args[0]))
                return originals[_name](*args, **kwargs)
            patch = mock.patch.object(OperationalStateStore, name, side_effect=side_effect)
            patch.start()
            capture_patches.append(patch)
        try:
            self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
        finally:
            for patch in reversed(capture_patches):
                patch.stop()
        valid = {name: values[-1] for name, values in captured.items()}

        def record(name, **changes):
            return dict(valid[name], **changes)

        def no_prepare(store):
            return None

        def prepare_binding(store, key="durable-binding"):
            return store.record_binding(valid["_binding"], key, ACTOR, NOW)

        def prepare_context(store):
            self._seed_through_packet_and_attempt()
            return store.record_context_usage(
                valid["_context_usage"], "durable-context", ACTOR, NOW
            )

        def prepare_allowance(store):
            return store.record_allowance_window(
                valid["_allowance"], "durable-allowance", ACTOR, NOW
            )

        def busy_binding(store):
            database = self.runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database, timeout=0)) as holder:
                holder.execute("PRAGMA journal_mode=WAL")
                holder.execute("BEGIN IMMEDIATE")
                store.record_binding(valid["_binding"], "durable-v25", ACTOR, NOW)

        unavailable_bad = copy.deepcopy(valid["_context_usage"])
        unavailable_bad["starting_input_measurement_json"] = _measurement(
            0, "Unavailable", "Unavailable", None
        )
        missing_token = copy.deepcopy(valid["_context_usage"])
        missing_token["token_measurements_json"].pop("total")
        growth_bad = copy.deepcopy(valid["_context_usage"])
        growth_bad["future_growth_estimate_json"]["lower_bound"] = _measurement(
            300, "Estimated", "Medium", "estimate"
        )
        context_policy_bad = copy.deepcopy(valid["_packet"])
        context_policy_bad["context_policy_json"].pop("stop_remaining_tokens")
        payload_bad = copy.deepcopy(valid["_evidence"])
        payload_bad["payload_json"]["extra"] = True

        def lower_quality_update(store):
            current = store.snapshot("AttemptContextUsage", "context-1")
            proposed = {
                name: _measurement(value["value"], "Estimated", "Medium", "estimate")
                for name, value in current["token_measurements_json"].items()
            }
            return store.update_context_usage(
                "attempt-1", 1,
                {
                    "token_measurements": proposed,
                    "cost_measurement": current["cost_measurement_json"],
                    "availability_state": "Available", "observed_at": NOW,
                },
                "durable-v20", ACTOR, NOW,
            )

        cases = (
            ("APP-V01", InvalidRecord, "project binding has an invalid closed shape", no_prepare, lambda store: store.record_binding({**valid["_binding"], "extra": True}, "durable-v01", ACTOR, NOW)),
            ("APP-V02", InvalidRecord, "binding_id must be non-empty UTF-8 text up to 512 bytes", no_prepare, lambda store: store.record_binding(record("_binding", binding_id=""), "durable-v02", ACTOR, NOW)),
            ("APP-V03", InvalidRecord, "merge_delegation_reference must be non-empty UTF-8 text up to 512 bytes", no_prepare, lambda store: store.record_binding(record("_binding", merge_delegation_reference=""), "durable-v03", ACTOR, NOW)),
            ("APP-V04", InvalidRecord, "source_commit must be a lowercase full Git commit", no_prepare, lambda store: store.record_binding(record("_binding", source_commit="A" * 40), "durable-v04", ACTOR, NOW)),
            ("APP-V05", InvalidRecord, "manifest_digest must be a lowercase SHA-256 digest", no_prepare, lambda store: store.record_binding(record("_binding", manifest_digest="A" * 64), "durable-v05", ACTOR, NOW)),
            ("APP-V06", operational_state.SensitiveMaterialRejected, "provider must match the closed non-secret grammar", no_prepare, lambda store: store.record_secret_reference(record("_secret_reference", provider="OpenAI"), "durable-v06", ACTOR, NOW)),
            ("APP-V07", operational_state.SensitiveMaterialRejected, "reference_name must match the closed non-secret grammar", no_prepare, lambda store: store.record_secret_reference(record("_secret_reference", reference_name="ghp_value-carrier"), "durable-v07", ACTOR, NOW)),
            ("APP-V08", InvalidRecord, "now must be a canonical UTC timestamp", no_prepare, lambda store: store.record_binding(valid["_binding"], "durable-v08", ACTOR, "now")),
            ("APP-V09", InvalidRecord, "activated_at must be a canonical UTC timestamp", no_prepare, lambda store: store.record_binding(record("_binding", activated_at="now"), "durable-v09", ACTOR, NOW)),
            ("APP-V10", InvalidRecord, "attempt_number must be a positive integer", no_prepare, lambda store: store.record_attempt(record("_attempt", attempt_number=True), "durable-v10", ACTOR, NOW)),
            ("APP-V11", InvalidRecord, "correction_count must be a non-negative integer", no_prepare, lambda store: store.materialize_packet(record("_packet", correction_count=False), "durable-v11", ACTOR, NOW)),
            ("APP-V12", InvalidRecord, "owned_paths_json must be sorted and unique", no_prepare, lambda store: store.materialize_packet(record("_packet", owned_paths_json=["z", "a"]), "durable-v12", ACTOR, NOW)),
            ("APP-V13", operational_state.SensitiveMaterialRejected, "structured sensitive/raw field is rejected", no_prepare, lambda store: store.record_binding(record("_binding", binding_json={"secret": "value"}), "durable-v13", ACTOR, NOW)),
            ("APP-V14", InvalidRecord, "binding_json must be an object", no_prepare, lambda store: store.record_binding(record("_binding", binding_json=[]), "durable-v14", ACTOR, NOW)),
            ("APP-V15", InvalidRecord, "window_change_value is not normalized", no_prepare, lambda store: store.record_usage_reconciliation(record("_reconciliation", window_change_value="10.50"), "durable-v15", ACTOR, NOW)),
            ("APP-V16", InvalidRecord, "context policy has an invalid closed shape", no_prepare, lambda store: store.materialize_packet(context_policy_bad, "durable-v16", ACTOR, NOW)),
            ("APP-V17", InvalidRecord, "state payload has an invalid closed shape", no_prepare, lambda store: store.append_evidence(payload_bad, ACTOR)),
            ("APP-V18", InvalidRecord, "unavailable measurement must retain null value/source", no_prepare, lambda store: store.record_context_usage(unavailable_bad, "durable-v18", ACTOR, NOW)),
            ("APP-V19", InvalidRecord, "unknown cost retains no amount, currency, or source", no_prepare, lambda store: store.record_context_usage(record("_context_usage", cost_measurement_json=dict(valid["_context_usage"]["cost_measurement_json"], amount="0")), "durable-v19", ACTOR, NOW)),
            ("APP-V20", InvalidRecord, "lower-quality measurement cannot replace the retained value", prepare_context, lower_quality_update),
            ("APP-V21", InvalidRecord, "token measurements has an invalid closed shape", no_prepare, lambda store: store.record_context_usage(missing_token, "durable-v21", ACTOR, NOW)),
            ("APP-V22", InvalidRecord, "actor has an invalid closed shape", no_prepare, lambda store: store.record_binding(valid["_binding"], "durable-v22", {"actor_type": "Developer", "actor_id": "developer-1"}, NOW)),
            ("APP-V23", IdempotencyConflict, "idempotency key was already used for different command facts", lambda store: prepare_binding(store, "durable-v23"), lambda store: store.record_binding(record("_binding", authority_reference="other"), "durable-v23", ACTOR, NOW)),
            ("APP-V24", InvalidRecord, "record violates a durable schema constraint", prepare_binding, lambda store: store.record_binding(record("_binding", binding_id="durable-v24"), "durable-v24", ACTOR, NOW)),
            ("APP-V25", ResourceBusy, "SQLite busy timeout exhausted", no_prepare, busy_binding),
            ("APP-REL-01", InvalidRecord, "record_binding accepts Candidate or Blocked only", no_prepare, lambda store: store.record_binding(record("_binding", state="Active"), "durable-r01", ACTOR, NOW)),
            ("APP-REL-02", InvalidRecord, "secret reference status is invalid", no_prepare, lambda store: store.record_secret_reference(record("_secret_reference", status="Other"), "durable-r02", ACTOR, NOW)),
            ("APP-REL-03", InvalidRecord, "record_graph_projection creates Active projections only", no_prepare, lambda store: store.record_graph_projection(record("_graph", state="Stale"), [valid["_work_item"]], "durable-r03", ACTOR, NOW)),
            ("APP-REL-04", InvalidRecord, "work item belongs to a different graph projection", no_prepare, lambda store: store.record_graph_projection(valid["_graph"], [record("_work_item", graph_projection_id="other")], "durable-r04", ACTOR, NOW)),
            ("APP-REL-05", InvalidRecord, "create_run creates Planned runs only", no_prepare, lambda store: store.create_run(record("_run", state="Running"), "durable-r05", ACTOR, NOW)),
            ("APP-REL-06", InvalidRecord, "materialized packet starts Planned with correction count zero", no_prepare, lambda store: store.materialize_packet(record("_packet", correction_count=1), "durable-r06", ACTOR, NOW)),
            ("APP-REL-07", InvalidRecord, "evidence digest does not cover its canonical payload", no_prepare, lambda store: store.append_evidence(record("_evidence", content_digest="b" * 64), ACTOR)),
            ("APP-REL-08", InvalidRecord, "open_wait creates unresolved Open waits only", no_prepare, lambda store: store.open_wait(record("_wait", state="Resolved"), "durable-r08", ACTOR, NOW)),
            ("APP-REL-09", InvalidRecord, "review kind is invalid", no_prepare, lambda store: store.record_review(record("_review", review_kind="Other"), "durable-r09", ACTOR, NOW)),
            ("APP-REL-10", InvalidRecord, "notification channel or severity is invalid", no_prepare, lambda store: store.record_notification(record("_notification", channel="Other"), "durable-r10", ACTOR, NOW)),
            ("APP-REL-11", InvalidRecord, "worker progress prose must be pre-redacted with a receipt", no_prepare, lambda store: store.record_worker_progress(record("_worker_progress", plan_payload_json={"kind": "reason", "reason_code": "X", "detail_reference": None}), "durable-r11", ACTOR, NOW)),
            ("APP-REL-12", InvalidRecord, "future growth lower bound exceeds upper bound", no_prepare, lambda store: store.record_context_usage(growth_bad, "durable-r12", ACTOR, NOW)),
            ("APP-REL-13", InvalidRecord, "unavailable allowance values must remain null", no_prepare, lambda store: store.record_allowance_window(record("_allowance", precision="Unavailable", measurement_quality="Unavailable", freshness="Unavailable"), "durable-r13", ACTOR, NOW)),
            ("APP-REL-14", InvalidRecord, "reconciliation must retain the allowance native unit", prepare_allowance, lambda store: store.record_usage_reconciliation(record("_reconciliation", native_unit="tokens"), "durable-r14", ACTOR, NOW)),
            ("APP-REL-15", InvalidRecord, "packet acceptance relation is invalid", no_prepare, lambda store: store.record_acceptance(record("_acceptance", subject_id="other"), "durable-r15", ACTOR, NOW)),
            ("APP-REL-16", InvalidRecord, "owner observation cannot carry delegation", no_prepare, lambda store: store.record_merge_observation(record("_merge_observation", performed_by_authority="Owner", delegation_reference="policy"), "durable-r16", ACTOR, NOW)),
            ("APP-REL-17", InvalidRecord, "record violates a durable schema constraint", no_prepare, lambda store: store.record_binding(valid["_binding"], "durable-r17", {"actor_type": "Developer", "actor_id": "developer-1", "correlation_id": "correlation-1", "causation_event_id": 999}, NOW)),
            ("APP-REL-18", InvalidRecord, "record violates a durable schema constraint", prepare_binding, lambda store: store.record_binding(record("_binding", binding_id="durable-r18"), "durable-r18", ACTOR, NOW)),
            ("APP-REL-19", InvalidRecord, "entity_type is not snapshot-readable", no_prepare, lambda store: store.snapshot("Other", "id")),
        )
        self.assertEqual(
            {case[0] for case in cases},
            {f"APP-V{number:02d}" for number in range(1, 26)}
            | {f"APP-REL-{number:02d}" for number in range(1, 20)},
        )

        for case_id, error_type, message, prepare, command in cases:
            self.runtime.close()
            self.setUp()
            prepare(self.store)
            database = self.runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                before = _durable_state(connection)
                before_events = connection.execute(
                    "SELECT COUNT(*),COALESCE(MAX(event_id),0) FROM events"
                ).fetchone()
            with self.subTest(case=case_id), self.assertRaisesRegex(
                error_type, f"^{re.escape(message)}$"
            ):
                command(self.store)
            reopened = OperationalStateStore(self.runtime.config())
            self.assertEqual(reopened.health().schema_version, 4)
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                self.assertEqual(_durable_state(connection), before, case_id)
                self.assertEqual(
                    connection.execute("SELECT COUNT(*),COALESCE(MAX(event_id),0) FROM events").fetchone(),
                    before_events,
                )
            artifacts = {path.name for path in self.runtime.path.iterdir()}
            self.assertIn("maestro.sqlite3", artifacts)
            self.assertLessEqual(
                artifacts, {"maestro.sqlite3", "maestro.sqlite3-wal", "maestro.sqlite3-shm"}
            )

    def test_all_a_record_append_routes_persist_reopen_and_events_are_ordered(self) -> None:
        expected = self._seed_through_packet_and_attempt()
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
        expected[("Evidence", "evidence-1")] = self.store.append_evidence(evidence, ACTOR)
        expected[("Wait", "wait-1")] = self.store.open_wait(
            wait, "command-wait", ACTOR, NOW
        )
        expected[("Review", "review-1")] = self.store.record_review(
            review, "command-review", ACTOR, NOW
        )
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
        expected[("Notification", "notification-1")] = self.store.record_notification(
            notification, "command-notification", ACTOR, NOW
        )
        progress = {
            "progress_id": "progress-1", "attempt_id": "attempt-1", "plan_payload_json": _redacted("plan"),
            "current_step_payload_json": _redacted("step"), "blocker_payload_json": _redacted("none"),
            "eta_text": "unknown", "confidence": "Unknown", "status_request_state": "NotRequested",
            "next_permitted_action": "continue", "observed_at": NOW, "received_at": NOW,
        }
        expected[("WorkerProgress", "progress-1")] = self.store.record_worker_progress(
            progress, "command-progress", ACTOR, NOW
        )
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
        expected[("AttemptContextUsage", "context-1")] = self.store.record_context_usage(
            context, "command-context", ACTOR, NOW
        )
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
        expected[("AttemptContextUsage", "context-1")] = updated
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
        expected[("AllowanceWindow", "allowance-1")] = self.store.record_allowance_window(
            allowance, "command-allowance", ACTOR, NOW
        )
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
        expected[("UsageReconciliation", "reconciliation-1")] = (
            self.store.record_usage_reconciliation(
                reconciliation, "command-reconciliation", ACTOR, NOW
            )
        )
        acceptance = {
            "acceptance_id": "acceptance-1", "subject_type": "Packet", "subject_id": "packet-1",
            "packet_id": "packet-1", "run_id": None, "sequence_number": 1,
            "supersedes_acceptance_id": None, "required_authority": "ProjectArchitect",
            "decision": "Returned", "authority_reference": "architect-return", "exact_head": COMMIT_B,
            "review_coverage_json": {}, "reason_payload_json": {"kind": "reason", "reason_code": "CHANGES", "detail_reference": "review-1"},
            "created_at": NOW,
        }
        expected[("Acceptance", "acceptance-1")] = self.store.record_acceptance(
            acceptance, "command-acceptance", ACTOR, NOW
        )
        merge = {
            "merge_observation_id": "merge-1", "run_id": "run-1", "packet_id": "packet-1",
            "acceptance_id": None, "repository_reference": "owner/repo", "default_branch": "main",
            "accepted_head": COMMIT_B, "merge_commit": COMMIT_A, "source_kind": "Git",
            "source_reference": "git-observation", "performed_by_authority": "DelegatedIdentity",
            "performed_by_reference": "bot-1", "delegation_reference": "delegation-policy",
            "review_coverage_json": {}, "observed_at": NOW,
        }
        expected[("MergeObservation", "merge-1")] = self.store.record_merge_observation(
            merge, "command-merge", ACTOR, NOW
        )

        reopened = OperationalStateStore(self.runtime.config())
        for (entity, identifier), exact_record in expected.items():
            with self.subTest(entity=entity):
                self.assertEqual(reopened.snapshot(entity, identifier), exact_record)
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

    def test_held_writer_returns_resource_busy_on_health_reads_and_mutation(self) -> None:
        binding = self._records()[0]
        database = self.runtime.path / "maestro.sqlite3"
        with closing(sqlite3.connect(database, timeout=0)) as holder:
            holder.execute("PRAGMA journal_mode=WAL")
            holder.execute("BEGIN IMMEDIATE")
            before = {
                "bindings": holder.execute("SELECT COUNT(*) FROM project_bindings").fetchone()[0],
                "events": holder.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            }
            routes = (
                ("health", self.store.health),
                ("snapshot", lambda: self.store.snapshot("ProjectBinding", "binding-1")),
                ("events_after", lambda: self.store.events_after(0, 1)),
                (
                    "record_binding",
                    lambda: self.store.record_binding(
                        binding, "held-writer-binding", ACTOR, NOW
                    ),
                ),
            )
            for name, route in routes:
                started = time.monotonic()
                with self.subTest(route=name), self.assertRaises(ResourceBusy):
                    route()
                self.assertGreaterEqual(time.monotonic() - started, 4.5)
                self.assertEqual(
                    holder.execute("SELECT COUNT(*) FROM project_bindings").fetchone()[0],
                    before["bindings"],
                )
                self.assertEqual(
                    holder.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                    before["events"],
                )

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

    def test_all_declared_constraint_classes_reject_without_entity_or_event_mutation(self) -> None:
        binding, secret, _, _, _, _ = self._records()
        accepted = self.store.record_binding(binding, "constraint-seed", ACTOR, NOW)

        cases = (
            (
                "foreign-key",
                lambda: self.store.record_binding(
                    dict(binding, binding_id="binding-missing-project", project_id="missing"),
                    "constraint-fk",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "check-enum",
                lambda: self.store.record_binding(
                    dict(binding, binding_id="binding-bad-check", acceptance_authority="Nobody"),
                    "constraint-check",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "unique",
                lambda: self.store.record_binding(
                    dict(binding, binding_id="binding-duplicate-revision"),
                    "constraint-unique",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "json-root",
                lambda: self.store.record_binding(
                    dict(binding, binding_id="binding-json", binding_json=[]),
                    "constraint-json",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "empty-id",
                lambda: self.store.record_binding(
                    dict(binding, binding_id=""), "constraint-empty-id", ACTOR, NOW
                ),
            ),
            (
                "utf8-id-size",
                lambda: self.store.record_binding(
                    dict(binding, binding_id="é" * 257),
                    "constraint-long-id",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "digest",
                lambda: self.store.record_binding(
                    dict(binding, binding_id="binding-digest", manifest_digest="A" * 64),
                    "constraint-digest",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "timestamp",
                lambda: self.store.record_secret_reference(
                    dict(secret, secret_reference_observation_id="secret-time", observed_at="now"),
                    "constraint-time",
                    ACTOR,
                    NOW,
                ),
            ),
            (
                "json-row-size",
                lambda: self.store.record_binding(
                    dict(
                        binding,
                        binding_id="binding-oversize",
                        binding_revision="revision-oversize",
                        binding_json={"value": "x" * (1024 * 1024)},
                    ),
                    "constraint-size",
                    ACTOR,
                    NOW,
                ),
            ),
        )
        for name, command in cases:
            before_events = len(self.store.events_after(0, 1000))
            before_record = self.store.snapshot("ProjectBinding", "binding-1")
            with self.subTest(constraint=name), self.assertRaises(InvalidRecord):
                command()
            self.assertEqual(len(self.store.events_after(0, 1000)), before_events)
            self.assertEqual(self.store.snapshot("ProjectBinding", "binding-1"), before_record)
            self.assertEqual(before_record, accepted)

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

    def test_remaining_partial_active_constraints_reject_without_partial_rows_or_events(self) -> None:
        self._seed_through_packet_and_attempt()
        wait = {
            "wait_id": "wait-active", "run_id": "run-1", "packet_id": "packet-1",
            "gate_type": "Review", "awaited_role": "Reviewer",
            "awaited_reference": "review-route", "expected_result": "Approve",
            "timeout_at": LATER, "next_permitted_action": "Wait", "state": "Open",
            "resolution_reason_payload_json": None,
        }
        durable_wait = self.store.open_wait(wait, "partial-wait-seed", ACTOR, NOW)
        baseline_events = len(self.store.events_after(0, 1000))
        with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            packet = self.store.snapshot("Packet", "packet-1")
            self.assertIsNotNone(packet)
            self.store._insert(
                connection,
                "packets",
                dict(packet, packet_id="packet-2", packet_revision="packet-r2"),
            )

            lease_insert = (
                "INSERT INTO leases(lease_id,packet_id,run_id,claim_key,run_fingerprint,"
                "base_commit,worktree_path,executor_route,holder_id,state,acquired_at,"
                "expires_at,heartbeat_at,version) VALUES (?,?,?,?,?,?,?,?,?,'Active',?,?,?,1)"
            )
            before_leases = connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    lease_insert,
                    (
                        "lease-packet-conflict", "packet-1", "run-1", "claim-packet-conflict",
                        DIGEST_A, COMMIT_A, "/runtime/other-worktree", "executor", "holder-2",
                        NOW, LATER, NOW,
                    ),
                )
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0], before_leases)
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    lease_insert,
                    (
                        "lease-worktree-conflict", "packet-2", "run-1", "claim-worktree-conflict",
                        DIGEST_A, COMMIT_A, "/runtime/worktree", "executor", "holder-3",
                        NOW, LATER, NOW,
                    ),
                )
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM leases").fetchone()[0], before_leases)

            connection.execute(
                "INSERT INTO resource_locks(lock_id,resource_key,lock_kind,packet_id,lease_id,state,acquired_at,expires_at,version) "
                "VALUES ('lock-1','shared:sqlite-schema','SharedBoundary','packet-1','lease-1','Active',?,?,1)",
                (NOW, LATER),
            )
            before_locks = connection.execute("SELECT COUNT(*) FROM resource_locks").fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO resource_locks(lock_id,resource_key,lock_kind,packet_id,lease_id,state,acquired_at,expires_at,version) "
                    "VALUES ('lock-2','shared:sqlite-schema','SharedBoundary','packet-1','lease-1','Active',?,?,1)",
                    (NOW, LATER),
                )
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM resource_locks").fetchone()[0],
                before_locks,
            )

            before_waits = connection.execute("SELECT COUNT(*) FROM waits").fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                self.store._insert(
                    connection,
                    "waits",
                    dict(durable_wait, wait_id="wait-active-duplicate"),
                )
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM waits").fetchone()[0], before_waits)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], baseline_events)

    def test_every_declared_operational_foreign_key_rejects_without_row_or_event(self) -> None:
        # Populate one exact valid row for every A-owned record table, then
        # clone it with each declared foreign-key column independently broken.
        self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
        database = self.runtime.path / "maestro.sqlite3"
        with closing(sqlite3.connect(database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO resource_locks(lock_id,resource_key,lock_kind,packet_id,lease_id,state,acquired_at,expires_at,version) "
                "VALUES ('fk-lock-seed','fk:seed','Path','packet-1','lease-1','Released',?,?,1)",
                (NOW, LATER),
            )
            connection.commit()

        bases = {
            "project_bindings": {"binding_id": "fk-binding", "binding_revision": "fk-revision"},
            "secret_reference_observations": {
                "secret_reference_observation_id": "fk-secret", "observed_at": LATER
            },
            "graph_projections": {
                "graph_projection_id": "fk-graph", "graph_revision": "fk-graph-r",
                "source_hash": "c" * 64, "state": "Superseded",
            },
            "work_items": {"work_item_id": "fk-work", "architecture_node_id": "fk-node"},
            "runs": {"run_id": "fk-run", "run_fingerprint": "c" * 64},
            "packets": {"packet_id": "fk-packet", "packet_revision": "fk-packet-r"},
            "leases": {
                "lease_id": "fk-lease", "claim_key": "fk-claim",
                "worktree_path": "/runtime/fk-worktree", "state": "Released",
            },
            "attempts": {"attempt_id": "fk-attempt", "attempt_number": 2},
            "resource_locks": {
                "lock_id": "fk-lock", "resource_key": "fk:resource", "state": "Released"
            },
            "evidence": {"evidence_id": "fk-evidence", "idempotency_key": "fk-evidence-key"},
            "waits": {"wait_id": "fk-wait", "gate_type": "FK", "state": "Resolved"},
            "reviews": {"review_id": "fk-review", "reviewer_instance": "fk-reviewer"},
            "notifications": {"notification_id": "fk-notification"},
            "acceptance_records": {"acceptance_id": "fk-acceptance", "sequence_number": 2},
            "merge_observations": {"merge_observation_id": "fk-merge"},
            "worker_progress_observations": {"progress_id": "fk-progress"},
            "attempt_context_usage": {"context_usage_id": "fk-context"},
            "usage_reconciliations": {"usage_reconciliation_id": "fk-reconciliation"},
            "events": {"event_id": None, "idempotency_key": "fk-event"},
        }
        cases = (
            ("project_bindings", "project_id"),
            ("secret_reference_observations", "project_id"),
            ("secret_reference_observations", "binding_id"),
            ("graph_projections", "project_id"),
            ("graph_projections", "binding_id"),
            ("work_items", "graph_projection_id"),
            ("runs", "project_id"),
            ("runs", "binding_id"),
            ("runs", "graph_projection_id"),
            ("packets", "run_id"),
            ("packets", "work_item_id"),
            ("leases", "packet_id"),
            ("leases", "run_id"),
            ("attempts", "packet_id"),
            ("attempts", "lease_id"),
            ("attempts", "correction_for_review_id"),
            ("resource_locks", "packet_id"),
            ("resource_locks", "lease_id"),
            ("evidence", "run_id"),
            ("evidence", "packet_id"),
            ("evidence", "attempt_id"),
            ("waits", "run_id"),
            ("waits", "packet_id"),
            ("reviews", "packet_id"),
            ("reviews", "attempt_id"),
            ("notifications", "event_id"),
            ("notifications", "run_id"),
            ("notifications", "packet_id"),
            ("acceptance_records", "packet_id"),
            ("acceptance_records", "run_id"),
            ("acceptance_records", "supersedes_acceptance_id"),
            ("merge_observations", "run_id"),
            ("merge_observations", "packet_id"),
            ("merge_observations", "acceptance_id"),
            ("worker_progress_observations", "attempt_id"),
            ("attempt_context_usage", "attempt_id"),
            ("usage_reconciliations", "allowance_observation_id"),
            ("events", "causation_event_id"),
        )
        for index, (table, foreign_key) in enumerate(cases, start=1):
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                cursor = connection.execute(f"SELECT * FROM {table} LIMIT 1")
                columns = [item[0] for item in cursor.description]
                values = dict(zip(columns, cursor.fetchone()))
                values.update(bases[table])
                if table == "acceptance_records" and foreign_key == "run_id":
                    values.update(subject_type="Run", subject_id="missing-fk", packet_id=None)
                elif table == "acceptance_records" and foreign_key == "packet_id":
                    values.update(subject_type="Packet", subject_id="missing-fk", run_id=None)
                values[foreign_key] = 999999 if foreign_key in {"event_id", "causation_event_id"} else "missing-fk"
                before_rows = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                before_events = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                placeholders = ",".join("?" for _ in columns)
                with self.subTest(table=table, foreign_key=foreign_key, case=index), self.assertRaises(
                    sqlite3.IntegrityError
                ):
                    connection.execute(
                        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                        [values[column] for column in columns],
                    )
                    connection.commit()
                connection.rollback()
                self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], before_rows)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], before_events)

    def test_every_declared_nonpartial_unique_constraint_rejects_without_row_or_event(self) -> None:
        self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
        database = self.runtime.path / "maestro.sqlite3"
        cases = (
            ("project_bindings", {"binding_id": "unique-binding"}),
            (
                "secret_reference_observations",
                {"secret_reference_observation_id": "unique-secret"},
            ),
            (
                "graph_projections",
                {"graph_projection_id": "unique-graph", "state": "Superseded"},
            ),
            ("work_items", {"work_item_id": "unique-work"}),
            ("runs", {"run_id": "unique-run"}),
            ("packets", {"packet_id": "unique-packet"}),
            (
                "leases",
                {
                    "lease_id": "unique-lease", "state": "Released",
                    "worktree_path": "/runtime/unique-worktree",
                },
            ),
            ("attempts", {"attempt_id": "unique-attempt"}),
            ("evidence", {"evidence_id": "unique-evidence"}),
            ("reviews", {"review_id": "unique-review"}),
            ("acceptance_records", {"acceptance_id": "unique-acceptance"}),
            ("attempt_context_usage", {"context_usage_id": "unique-context"}),
            ("events", {"event_id": None}),
        )
        for table, overrides in cases:
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                cursor = connection.execute(f"SELECT * FROM {table} LIMIT 1")
                columns = [item[0] for item in cursor.description]
                values = dict(zip(columns, cursor.fetchone()))
                values.update(overrides)
                before_rows = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                before_events = connection.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                placeholders = ",".join("?" for _ in columns)
                with self.subTest(table=table), self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                        [values[column] for column in columns],
                    )
                    connection.commit()
                connection.rollback()
                self.assertEqual(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], before_rows)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], before_events)

    def test_ar_p03_p06_closed_database_constraint_manifest_is_durable(self) -> None:
        update_cases = (
            ("DB-R01", "leases", {"expires_at": NOW}),
            ("DB-R02", "attempts", {"attempt_number": 0}),
            ("DB-R03", "attempts", {"attempt_kind": "Other"}),
            ("DB-R04", "attempts", {"correction_for_review_id": "review-1"}),
            ("DB-R05", "attempts", {"attempt_number": 2, "attempt_kind": "TargetedCorrection", "correction_for_review_id": None}),
            ("DB-R15/graph_projections", "graph_projections", {"version": 0}),
            ("DB-R15/work_items", "work_items", {"version": 0}),
            ("DB-R15/runs", "runs", {"version": 0}),
            ("DB-R15/packets", "packets", {"version": 0}),
            ("DB-R15/leases", "leases", {"version": 0}),
            ("DB-R15/attempts", "attempts", {"version": 0}),
            ("DB-R15/resource_locks", "resource_locks", {"version": 0}),
            ("DB-R15/waits", "waits", {"version": 0}),
            ("DB-R15/notifications", "notifications", {"version": 0}),
            ("DB-R15/attempt_context_usage", "attempt_context_usage", {"version": 0}),
            ("DB-R16", "packets", {"correction_count": 2}),
            ("DB-R17", "notifications", {"attempt_count": -1}),
            ("DB-R18", "work_items", {"planned_rank": -1}),
            ("DB-R20", "attempt_context_usage", {"configured_context_limit": 0}),
        )
        insert_cases = (
            ("DB-R06", "acceptance_records", "acceptance_id", "ar-r06", {"subject_type": "Other", "subject_id": "other"}),
            ("DB-R07", "acceptance_records", "acceptance_id", "ar-r07", {"subject_id": "other-packet"}),
            ("DB-R08", "acceptance_records", "acceptance_id", "ar-r08", {"run_id": "run-1"}),
            ("DB-R09", "acceptance_records", "acceptance_id", "ar-r09", {"subject_type": "Run", "subject_id": "other-run", "packet_id": None, "run_id": "run-1"}),
            ("DB-R10", "acceptance_records", "acceptance_id", "ar-r10", {"subject_type": "Run", "subject_id": "run-1", "packet_id": "packet-1", "run_id": "run-1"}),
            ("DB-R11", "acceptance_records", "acceptance_id", "ar-r11", {"sequence_number": 0}),
            ("DB-R12", "merge_observations", "merge_observation_id", "ar-r12", {"performed_by_authority": "Other"}),
            ("DB-R13", "merge_observations", "merge_observation_id", "ar-r13", {"performed_by_authority": "Owner", "delegation_reference": "unexpected"}),
            ("DB-R14", "merge_observations", "merge_observation_id", "ar-r14", {"performed_by_authority": "DelegatedIdentity", "delegation_reference": None}),
            ("DB-R19", "reviews", "review_id", "ar-r19", {"correction_number": 2}),
        )
        primary_key_cases = (
            ("DB-PK01", "notifications"),
            ("DB-PK02", "merge_observations"),
            ("DB-PK03", "worker_progress_observations"),
            ("DB-PK04", "provider_allowance_windows"),
            ("DB-PK05", "usage_reconciliations"),
        )

        def fresh_seed():
            self.runtime.close()
            self.setUp()
            self.test_all_a_record_append_routes_persist_reopen_and_events_are_ordered()
            with closing(sqlite3.connect(self.runtime.path / "maestro.sqlite3")) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute(
                    "INSERT INTO resource_locks(lock_id,resource_key,lock_kind,packet_id,lease_id,state,acquired_at,expires_at,version) "
                    "VALUES ('ar-lock','ar:lock','SharedBoundary','packet-1','lease-1','Released',?,?,1)",
                    (NOW, LATER),
                )
                connection.commit()

        def prove(case_id, expected_error, operation):
            fresh_seed()
            database = self.runtime.path / "maestro.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                before = _durable_state(connection)
                with self.subTest(case=case_id), self.assertRaises(sqlite3.IntegrityError) as raised:
                    operation(connection)
                    connection.commit()
                self.assertEqual(raised.exception.sqlite_errorname, expected_error)
                connection.rollback()
            reopened = OperationalStateStore(self.runtime.config())
            self.assertEqual(reopened.health().schema_version, 4)
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA foreign_keys=ON")
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
                self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                self.assertEqual(_durable_state(connection), before, case_id)
            artifacts = {path.name for path in self.runtime.path.iterdir()}
            self.assertIn("maestro.sqlite3", artifacts)
            self.assertLessEqual(
                artifacts, {"maestro.sqlite3", "maestro.sqlite3-wal", "maestro.sqlite3-shm"}
            )

        for case_id, table, changes in update_cases:
            def operation(connection, table=table, changes=changes):
                assignments = ",".join(f'"{name}"=?' for name in changes)
                connection.execute(
                    f'UPDATE "{table}" SET {assignments} WHERE rowid=(SELECT rowid FROM "{table}" ORDER BY rowid LIMIT 1)',
                    list(changes.values()),
                )
            prove(case_id, "SQLITE_CONSTRAINT_CHECK", operation)

        for case_id, table, primary_key, primary_value, changes in insert_cases:
            def operation(connection, table=table, primary_key=primary_key, primary_value=primary_value, changes=changes):
                cursor = connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid LIMIT 1')
                columns = [item[0] for item in cursor.description]
                values = dict(zip(columns, cursor.fetchone()))
                values.update(changes)
                values[primary_key] = primary_value
                connection.execute(
                    f'INSERT INTO "{table}" ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
                    [values[column] for column in columns],
                )
            prove(case_id, "SQLITE_CONSTRAINT_CHECK", operation)

        for case_id, table in primary_key_cases:
            def operation(connection, table=table):
                cursor = connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid LIMIT 1')
                columns = [item[0] for item in cursor.description]
                values = cursor.fetchone()
                connection.execute(
                    f'INSERT INTO "{table}" ({",".join(columns)}) VALUES ({",".join("?" for _ in columns)})',
                    values,
                )
            prove(case_id, "SQLITE_CONSTRAINT_PRIMARYKEY", operation)

    def test_ar_p04_app_v23_v24_replay_conflict_and_constraint_mapping_are_durable(self) -> None:
        binding = self._records()[0]
        first = self.store.record_binding(binding, "ar-v23", ACTOR, NOW)
        reopened = OperationalStateStore(self.runtime.config())
        self.assertEqual(reopened.record_binding(binding, "ar-v23", ACTOR, LATER), first)
        database = self.runtime.path / "maestro.sqlite3"
        with closing(sqlite3.connect(database)) as connection:
            before_conflict = _durable_state(connection)
        with self.assertRaisesRegex(
            IdempotencyConflict,
            "^idempotency key was already used for different command facts$",
        ):
            reopened.record_binding(
                dict(binding, authority_reference="other-authority"), "ar-v23", ACTOR, NOW
            )
        with closing(sqlite3.connect(database)) as connection:
            self.assertEqual(_durable_state(connection), before_conflict)

        with self.assertRaisesRegex(
            InvalidRecord, "^record violates a durable schema constraint$"
        ) as raised:
            reopened.record_binding(
                dict(binding, binding_id="ar-v24", binding_revision="ar-v24", project_id="missing"),
                "ar-v24", ACTOR, NOW,
            )
        self.assertIsInstance(raised.exception.__cause__, sqlite3.IntegrityError)
        self.assertEqual(raised.exception.__cause__.sqlite_errorname, "SQLITE_CONSTRAINT_FOREIGNKEY")
        with closing(sqlite3.connect(database)) as connection:
            self.assertEqual(_durable_state(connection), before_conflict)

    def test_ar_p04_app_v25_busy_exhaustion_has_no_partial_mutation(self) -> None:
        binding = self._records()[0]
        database = self.runtime.path / "maestro.sqlite3"
        with closing(sqlite3.connect(database, timeout=0)) as holder:
            holder.execute("PRAGMA journal_mode=WAL")
            holder.execute("BEGIN IMMEDIATE")
            before = _durable_state(holder)
            started = time.monotonic()
            with self.assertRaisesRegex(ResourceBusy, "^SQLite busy timeout exhausted$"):
                self.store.record_binding(binding, "ar-v25", ACTOR, NOW)
            self.assertGreaterEqual(time.monotonic() - started, 4.5)
            self.assertEqual(_durable_state(holder), before)
            holder.rollback()
        reopened = OperationalStateStore(self.runtime.config())
        self.assertIsNone(reopened.snapshot("ProjectBinding", "binding-1"))
        self.assertEqual(reopened.events_after(0, 1000), [])

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
