from __future__ import annotations

import concurrent.futures
import http.client
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from maestro import read_api
from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.storage import SQLiteFoundation


FIXED_TIME = "2026-01-01T00:00:00.000000Z"
RESULT_COMMIT = "c" * 40


def _request(port: int, method: str, path: str) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), body
    finally:
        connection.close()

_ATTEMPTS_SNAPSHOT_FIELDS = {
    "attempt_id", "attempt_kind", "attempt_number", "completion_evidence_reference",
    "correction_for_review_id", "created_at", "execution_handle", "executor_class",
    "expected_result", "finished_at", "heartbeat_at", "lease_id", "model_identity",
    "packet_id", "result_commit", "runtime_identity", "started_at", "state",
    "updated_at", "version",
}


def _insert_attempt(
    connection: sqlite3.Connection,
    *,
    attempt_id: str,
    packet_id: str | None = None,
    lease_id: str = "lease-1",
    attempt_number: int = 1,
    attempt_kind: str = "Initial",
    executor_class: str = "claude-code",
    model_identity: str = "claude-sonnet-5",
    runtime_identity: str = "runtime-1",
    state: str = "Planned",
    result_commit: str | None = None,
    correction_for_review_id: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    created_at: str = FIXED_TIME,
    updated_at: str = FIXED_TIME,
    version: int = 1,
    execution_handle: str | None = None,
    expected_result: str | None = None,
    heartbeat_at: str | None = None,
    completion_evidence_reference: str | None = None,
) -> None:
    if packet_id is None:
        packet_id = f"packet-for-{attempt_id}"
    connection.execute(
        """
        INSERT INTO attempts(
            attempt_id, packet_id, lease_id, attempt_number, attempt_kind,
            executor_class, model_identity, runtime_identity, state, result_commit,
            correction_for_review_id, started_at, finished_at, created_at, updated_at,
            version, execution_handle, expected_result, heartbeat_at,
            completion_evidence_reference
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            attempt_id, packet_id, lease_id, attempt_number, attempt_kind,
            executor_class, model_identity, runtime_identity, state, result_commit,
            correction_for_review_id, started_at, finished_at, created_at, updated_at,
            version, execution_handle, expected_result, heartbeat_at,
            completion_evidence_reference,
        ),
    )


class _RuntimeFixture:
    """A real, migrated database under the fixed var/ root, plus fixture attempts."""

    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary.name) / "runtime"
        self.config = RuntimeConfig.from_runtime_dir(self.runtime_dir)
        SQLiteFoundation(self.config).health()

    def insert_attempts(self, attempt_ids: list[str], **shared_kwargs) -> None:
        connection = sqlite3.connect(str(self.config.database_path))
        try:
            for attempt_id in attempt_ids:
                _insert_attempt(connection, attempt_id=attempt_id, **shared_kwargs)
            connection.commit()
        finally:
            connection.close()

    def insert_attempt_specs(self, specs: list[dict]) -> None:
        connection = sqlite3.connect(str(self.config.database_path))
        try:
            for spec in specs:
                _insert_attempt(connection, **spec)
            connection.commit()
        finally:
            connection.close()

    def close(self) -> None:
        self._temporary.cleanup()


class AttemptsSnapshotTests(unittest.TestCase):
    def _start_server(self, runtime_dir) -> read_api.ReadApiServer:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=runtime_dir))
        server.start()
        self.addCleanup(server.stop)
        return server

    def test_01_empty_table_returns_empty_page(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/attempts")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"attempts":[],"next_after":null}')

    def test_02_full_field_projection_planned_and_succeeded(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_attempt_specs(
            [
                {
                    "attempt_id": "attempt-planned",
                    "attempt_number": 1,
                    "attempt_kind": "Initial",
                    "state": "Planned",
                    "correction_for_review_id": None,
                    "result_commit": None,
                    "started_at": None,
                    "finished_at": None,
                    "execution_handle": None,
                    "expected_result": None,
                    "heartbeat_at": None,
                    "completion_evidence_reference": None,
                },
                {
                    "attempt_id": "attempt-succeeded",
                    "attempt_number": 2,
                    "attempt_kind": "TargetedCorrection",
                    "state": "Succeeded",
                    "correction_for_review_id": "review-1",
                    "result_commit": RESULT_COMMIT,
                    "started_at": FIXED_TIME,
                    "finished_at": FIXED_TIME,
                    "execution_handle": "execution-handle-1",
                    "expected_result": "expected-result-1",
                    "heartbeat_at": FIXED_TIME,
                    "completion_evidence_reference": "evidence-1",
                },
            ]
        )
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/attempts")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        payload = json.loads(body)
        self.assertIsNone(payload["next_after"])
        self.assertEqual(len(payload["attempts"]), 2)

        for attempt in payload["attempts"]:
            self.assertEqual(set(attempt.keys()), _ATTEMPTS_SNAPSHOT_FIELDS)

        by_id = {attempt["attempt_id"]: attempt for attempt in payload["attempts"]}

        planned = by_id["attempt-planned"]
        self.assertEqual(planned["attempt_number"], 1)
        self.assertEqual(planned["attempt_kind"], "Initial")
        self.assertEqual(planned["state"], "Planned")
        self.assertIsNone(planned["completion_evidence_reference"])
        self.assertIsNone(planned["correction_for_review_id"])
        self.assertIsNone(planned["execution_handle"])
        self.assertIsNone(planned["expected_result"])
        self.assertIsNone(planned["finished_at"])
        self.assertIsNone(planned["heartbeat_at"])
        self.assertIsNone(planned["result_commit"])
        self.assertIsNone(planned["started_at"])

        succeeded = by_id["attempt-succeeded"]
        self.assertEqual(succeeded["attempt_number"], 2)
        self.assertEqual(succeeded["attempt_kind"], "TargetedCorrection")
        self.assertEqual(succeeded["state"], "Succeeded")
        self.assertEqual(succeeded["completion_evidence_reference"], "evidence-1")
        self.assertEqual(succeeded["correction_for_review_id"], "review-1")
        self.assertEqual(succeeded["execution_handle"], "execution-handle-1")
        self.assertEqual(succeeded["expected_result"], "expected-result-1")
        self.assertEqual(succeeded["finished_at"], FIXED_TIME)
        self.assertEqual(succeeded["heartbeat_at"], FIXED_TIME)
        self.assertEqual(succeeded["result_commit"], RESULT_COMMIT)
        self.assertEqual(succeeded["started_at"], FIXED_TIME)

    def test_03_pagination_next_after_and_exact_page_boundary(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        attempt_ids = [f"attempt-{i:02d}" for i in range(1, 6)]
        fixture.insert_attempts(attempt_ids)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/attempts?limit=2")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([a["attempt_id"] for a in payload["attempts"]], attempt_ids[0:2])
        self.assertEqual(payload["next_after"], attempt_ids[1])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/attempts?limit=2&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([a["attempt_id"] for a in payload["attempts"]], attempt_ids[2:4])
        self.assertEqual(payload["next_after"], attempt_ids[3])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/attempts?limit=2&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([a["attempt_id"] for a in payload["attempts"]], attempt_ids[4:5])
        self.assertIsNone(payload["next_after"])

    def test_04_limit_boundary_values(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_attempts(["attempt-01"])
        server = self._start_server(fixture.runtime_dir)

        for accepted in ("1", "500"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/attempts?limit={accepted}"
            )
            self.assertEqual(status, 200, f"limit={accepted} should be accepted, got body {body!r}")

        for rejected in ("0", "501", "-1", "1.5", "abc", "007"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/attempts?limit={rejected}"
            )
            self.assertEqual(status, 400, f"limit={rejected} should be rejected, got body {body!r}")
            payload = json.loads(body)
            self.assertEqual(payload["error"], "invalid_query")
            self.assertEqual(payload["detail"], "limit must be an integer from 1 through 500")

    def test_05_query_validation_identical_across_both_snapshot_endpoints(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        malformed_queries = (
            "?bogus=1",
            "?limit=1&limit=2",
            "?limit=0",
            "?limit=501",
            "?after=",
        )
        for suffix in malformed_queries:
            status_attempts, _ct, body_attempts = _request(
                server.bound_port, "GET", f"/snapshot/attempts{suffix}"
            )
            status_packets, _ct, body_packets = _request(
                server.bound_port, "GET", f"/snapshot/packets{suffix}"
            )
            self.assertEqual(status_attempts, 400)
            self.assertEqual(status_packets, 400)
            self.assertEqual(status_attempts, status_packets)
            self.assertEqual(body_attempts, body_packets, f"bodies diverged for {suffix}")

    def test_06_unknown_path_and_wrong_method_for_attempts_route(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/attempt")
        self.assertEqual(status, 404)
        self.assertEqual(body, read_api._NOT_FOUND_BODY)

        status, _content_type, body = _request(server.bound_port, "POST", "/snapshot/attempts")
        self.assertEqual(status, 405)
        self.assertEqual(body, read_api._METHOD_NOT_ALLOWED_BODY)

    def test_07_health_and_packets_routes_unaffected_by_generalization(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_attempts(["attempt-01"])
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"status":"ready"}')

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/packets")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"next_after":null,"packets":[]}')

    def test_08_database_unavailable_returns_503(self) -> None:
        fixture_root = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.addCleanup(fixture_root.cleanup)
        no_database_runtime_dir = Path(fixture_root.name) / "runtime-without-database"
        no_database_runtime_dir.mkdir(parents=True)

        server = self._start_server(no_database_runtime_dir)
        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/attempts")
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"database_unavailable"}')

        status, _content_type, body = _request(server.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')

    def test_09_concurrent_requests_do_not_corrupt_pagination(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        attempt_ids = [f"attempt-{i:02d}" for i in range(1, 21)]
        fixture.insert_attempts(attempt_ids)
        server = self._start_server(fixture.runtime_dir)

        def _page_through() -> list[str]:
            collected: list[str] = []
            after: str | None = None
            while True:
                path = "/snapshot/attempts?limit=3" + (f"&after={after}" if after else "")
                status, _content_type, body = _request(server.bound_port, "GET", path)
                self.assertEqual(status, 200)
                payload = json.loads(body)
                collected.extend(a["attempt_id"] for a in payload["attempts"])
                after = payload["next_after"]
                if after is None:
                    break
            return collected

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_page_through) for _ in range(10)]
            results = [future.result() for future in futures]

        for result in results:
            self.assertEqual(result, attempt_ids)


if __name__ == "__main__":
    unittest.main()
