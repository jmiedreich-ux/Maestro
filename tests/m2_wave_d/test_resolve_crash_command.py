from __future__ import annotations

import http.client
import json
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path

from maestro import read_api
from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig, RuntimePathError
from maestro.operational_state import Actor, OperationalStateStore


NOW = "2026-09-05T12:00:00.000000Z"
COMMIT = "a" * 40
DIGEST = "b" * 64
ACTOR = {"actor_type": "Owner", "actor_id": "owner-1", "correlation_id": "correlation-1"}
REASON = {"kind": "reason", "reason_code": "OwnerResolvedCrash", "detail_reference": None}


def _request(
    port: int, method: str, path: str, body: bytes | None = None
) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(method, path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        response_body = response.read()
        return response.status, response.getheader("Content-Type"), response_body
    finally:
        connection.close()


class _PacketDatabase:
    """A minimal, self-contained real seed, matching D2's own established
    convention (`tests/m2_wave_d/test_resolve_decision_command.py`'s
    `_PacketDatabase`) — one project/binding/graph projection/run/packet
    chain, then forced directly into `NeedsReplan` via the same real
    technique `tests/m1_02/test_packet_eligibility.py`'s own
    `PacketDatabase.force_source` already uses (a raw SQL `UPDATE`):
    reaching `NeedsReplan` through the real API requires a full real
    attempt lifecycle (claim -> start -> finish with a Failed/TimedOut/
    Stale outcome), which this command's own test scope does not need to
    exercise — only `record_and_close_needs_replan`'s own real behavior
    from a `NeedsReplan` packet does.
    """

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
            Actor(**ACTOR),
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
                    "title": "Resolve-crash seed",
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
            Actor(**ACTOR),
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
            Actor(**ACTOR),
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
                "expected_branch": "implementation/resolve-crash",
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
            Actor(**ACTOR),
            NOW,
        )
        self.force_needs_replan()

    def force_needs_replan(self) -> None:
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='NeedsReplan',version=1,updated_at=? WHERE packet_id='packet-1'",
                (NOW,),
            )
            connection.commit()

    @property
    def database(self) -> Path:
        return self.path / "maestro.sqlite3"


class ResolveCrashCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = _PacketDatabase()
        self.server = read_api.ReadApiServer(
            read_api.ReadApiConfig(port=0, runtime_dir=self.runtime.path)
        )
        self.server.start()
        self.addCleanup(self.server.stop)
        self.addCleanup(self.runtime._temporary.cleanup)

    def _post(self, envelope: dict) -> tuple[int, str | None, dict]:
        status, content_type, raw_body = _request(
            self.server.bound_port,
            "POST",
            "/command/resolve-crash",
            body=json.dumps(envelope).encode("utf-8"),
        )
        return status, content_type, json.loads(raw_body)

    def _base_envelope(self, **overrides) -> dict:
        envelope = {
            "idempotency_key": "resolve-crash-1",
            "actor": ACTOR,
            "packet_id": "packet-1",
            "expected_version": 1,
            "reason_payload": REASON,
        }
        envelope.update(overrides)
        return envelope

    def test_01_real_end_to_end_resolution_moves_the_real_packet_from_needsreplan_to_cancelled(self) -> None:
        row_before = OperationalStateStore(self.runtime.config).snapshot("Packet", "packet-1")
        self.assertEqual((row_before["state"], row_before["version"]), ("NeedsReplan", 1))

        status, content_type, body = self._post(self._base_envelope())
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(
            body,
            {"entity_id": "packet-1", "entity_type": "Packet", "kind": "state", "state": "Cancelled", "version": 2},
        )

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("Cancelled", 2))

    def test_02_every_other_source_state_returns_409_invalid_transition(self) -> None:
        for state in ("Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Cancelled"):
            with self.subTest(state=state):
                with closing(sqlite3.connect(self.runtime.database)) as connection:
                    connection.execute(
                        "UPDATE packets SET state=?,version=1 WHERE packet_id='packet-1'", (state,)
                    )
                    connection.commit()
                status, _content_type, body = self._post(
                    self._base_envelope(idempotency_key=f"other-{state}")
                )
                self.assertEqual(status, 409, state)
                self.assertEqual(body["error"], "invalid_transition", state)
        self.runtime.force_needs_replan()

    def test_03_stale_expected_version_returns_409_stale_state(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(expected_version=2))
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "stale_state")

    def test_04_true_idempotent_replay_returns_the_exact_original_result_without_a_second_write(self) -> None:
        first_status, _content_type, first_body = self._post(self._base_envelope())
        self.assertEqual(first_status, 200)

        second_status, _content_type, second_body = self._post(self._base_envelope())
        self.assertEqual(second_status, 200)
        self.assertEqual(second_body, first_body)

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual(row["version"], 2)

    def test_05_same_idempotency_key_with_different_facts_returns_409_idempotency_conflict(self) -> None:
        first_status, _content_type, _first_body = self._post(self._base_envelope())
        self.assertEqual(first_status, 200)

        conflicting_status, _content_type, conflicting_body = self._post(
            self._base_envelope(reason_payload={"kind": "reason", "reason_code": "Different", "detail_reference": None})
        )
        self.assertEqual(conflicting_status, 409)
        self.assertEqual(conflicting_body["error"], "idempotency_conflict")

    def test_06_missing_or_invalid_command_specific_fields_return_400_invalid_command(self) -> None:
        bad_bodies = [
            self._base_envelope(packet_id=""),
            {k: v for k, v in self._base_envelope().items() if k != "packet_id"},
            self._base_envelope(expected_version=0),
            self._base_envelope(expected_version="1"),
            self._base_envelope(reason_payload="not-an-object"),
        ]
        for payload in bad_bodies:
            with self.subTest(payload=payload):
                status, _content_type, body = self._post(payload)
                self.assertEqual(status, 400)
                self.assertEqual(body["error"], "invalid_command")

    def test_07_unknown_packet_returns_400_invalid_command(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(packet_id="does-not-exist"))
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_command")

    def test_08_no_fictional_resume_or_redispatch_semantics_appear_anywhere_in_the_real_response(self) -> None:
        status, _content_type, body = self._post(self._base_envelope())
        self.assertEqual(status, 200)
        serialized = json.dumps(body)
        for fictional_term in ("resume", "re-dispatch", "redispatch", "hold-and-inspect"):
            self.assertNotIn(fictional_term, serialized.lower())

    def test_09_real_writer_lock_contention_returns_503_resource_busy(self) -> None:
        with closing(sqlite3.connect(self.runtime.database, timeout=0)) as holder:
            holder.execute("PRAGMA journal_mode=WAL")
            holder.execute("BEGIN IMMEDIATE")
            holder.execute(
                "UPDATE packets SET version=version WHERE packet_id='packet-1'"
            )
            started = time.monotonic()
            status, _content_type, body = self._post(self._base_envelope())
            elapsed = time.monotonic() - started
        self.assertEqual(status, 503)
        self.assertEqual(body["error"], "resource_busy")
        self.assertGreaterEqual(elapsed, 4.5)

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("NeedsReplan", 1))

    def test_10_real_invalid_runtime_dir_returns_503_database_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as outside_var:
            with self.assertRaises(RuntimePathError):
                RuntimeConfig(outside_var)

            server = read_api.ReadApiServer(
                read_api.ReadApiConfig(port=0, runtime_dir=outside_var)
            )
            server.start()
            try:
                status, _content_type, raw_body = _request(
                    server.bound_port,
                    "POST",
                    "/command/resolve-crash",
                    body=json.dumps(self._base_envelope()).encode("utf-8"),
                )
                body = json.loads(raw_body)
            finally:
                server.stop()
        self.assertEqual(status, 503)
        self.assertEqual(body, {"error": "database_unavailable"})


if __name__ == "__main__":
    unittest.main()
