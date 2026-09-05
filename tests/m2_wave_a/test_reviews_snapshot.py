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


def _request(port: int, method: str, path: str) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), body
    finally:
        connection.close()


_REVIEWS_SNAPSHOT_FIELDS = {
    "attempt_id", "base_commit", "correction_number", "coverage", "created_at",
    "findings", "head_commit", "packet_id", "result", "review_id", "review_kind",
    "reviewer_instance", "reviewer_role",
}


def _insert_review(
    connection: sqlite3.Connection,
    *,
    review_id: str,
    packet_id: str | None = None,
    attempt_id: str | None = None,
    review_kind: str = "IndependentImplementation",
    reviewer_role: str = "reviewer-role-1",
    reviewer_instance: str = "reviewer-instance-1",
    base_commit: str = "a" * 40,
    head_commit: str = "b" * 40,
    result: str = "Approve",
    findings_json: str = "[]",
    coverage_json: str = "{}",
    correction_number: int = 0,
    created_at: str = FIXED_TIME,
) -> None:
    if packet_id is None:
        packet_id = f"packet-for-{review_id}"
    connection.execute(
        """
        INSERT INTO reviews(
            review_id, packet_id, attempt_id, review_kind, reviewer_role,
            reviewer_instance, base_commit, head_commit, result, findings_json,
            coverage_json, correction_number, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            review_id, packet_id, attempt_id, review_kind, reviewer_role,
            reviewer_instance, base_commit, head_commit, result, findings_json,
            coverage_json, correction_number, created_at,
        ),
    )


class _RuntimeFixture:
    """A real, migrated database under the fixed var/ root, plus fixture reviews."""

    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary.name) / "runtime"
        self.config = RuntimeConfig.from_runtime_dir(self.runtime_dir)
        SQLiteFoundation(self.config).health()

    def insert_reviews(self, review_ids: list[str], **shared_kwargs) -> None:
        connection = sqlite3.connect(str(self.config.database_path))
        try:
            for review_id in review_ids:
                _insert_review(connection, review_id=review_id, **shared_kwargs)
            connection.commit()
        finally:
            connection.close()

    def insert_review_specs(self, specs: list[dict]) -> None:
        connection = sqlite3.connect(str(self.config.database_path))
        try:
            for spec in specs:
                _insert_review(connection, **spec)
            connection.commit()
        finally:
            connection.close()

    def close(self) -> None:
        self._temporary.cleanup()


def _hex_commit(prefix: int) -> str:
    return f"{prefix:040x}"


class ReviewsSnapshotTests(unittest.TestCase):
    def _start_server(self, runtime_dir) -> read_api.ReadApiServer:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=runtime_dir))
        server.start()
        self.addCleanup(server.stop)
        return server

    def test_01_empty_table_returns_empty_page(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/reviews")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"next_after":null,"reviews":[]}')

    def test_02_full_field_projection_decoded_findings_and_null_attempt_id(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        # Key insertion order is deliberately non-alphabetical ("severity" before
        # "path") to prove the response re-sorts nested object keys rather than
        # merely preserving JSON decode order.
        findings = [{"severity": "minor", "path": "services/maestro/maestro/read_api.py"}]
        coverage = {"lines_covered": 42, "lines_total": 50}
        fixture.insert_review_specs(
            [
                {
                    "review_id": "review-with-findings",
                    "attempt_id": "attempt-1",
                    "findings_json": json.dumps(findings),
                    "coverage_json": json.dumps(coverage),
                },
                {
                    "review_id": "review-empty",
                    "attempt_id": None,
                    "findings_json": "[]",
                    "coverage_json": "{}",
                    "head_commit": "c" * 40,
                },
            ]
        )
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/reviews")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        payload = json.loads(body)
        self.assertIsNone(payload["next_after"])
        self.assertEqual(len(payload["reviews"]), 2)

        for review in payload["reviews"]:
            self.assertEqual(set(review.keys()), _REVIEWS_SNAPSHOT_FIELDS)

        by_id = {review["review_id"]: review for review in payload["reviews"]}

        with_findings = by_id["review-with-findings"]
        self.assertEqual(with_findings["attempt_id"], "attempt-1")
        self.assertEqual(with_findings["findings"], findings)
        self.assertEqual(with_findings["coverage"], coverage)
        self.assertIsInstance(with_findings["findings"], list)
        self.assertIsInstance(with_findings["coverage"], dict)

        # Prove nested-key alphabetical sorting in the raw wire bytes: "path" (p)
        # sorts before "severity" (s), so the encoded finding object must show
        # "path" first even though the fixture dict above was built as
        # {"path": ..., "severity": ...} (already alphabetical) -- assert the
        # exact expected substring is present verbatim.
        self.assertIn(
            '{"path":"services/maestro/maestro/read_api.py","severity":"minor"}',
            body.decode("utf-8"),
        )

        empty = by_id["review-empty"]
        self.assertIsNone(empty["attempt_id"])
        self.assertEqual(empty["findings"], [])
        self.assertEqual(empty["coverage"], {})

    def test_03_pagination_next_after_and_exact_page_boundary(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        review_ids = [f"review-{i:02d}" for i in range(1, 6)]
        specs = [
            {"review_id": review_id, "head_commit": _hex_commit(i)}
            for i, review_id in enumerate(review_ids, start=1)
        ]
        fixture.insert_review_specs(specs)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/reviews?limit=2")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([r["review_id"] for r in payload["reviews"]], review_ids[0:2])
        self.assertEqual(payload["next_after"], review_ids[1])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/reviews?limit=2&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([r["review_id"] for r in payload["reviews"]], review_ids[2:4])
        self.assertEqual(payload["next_after"], review_ids[3])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/reviews?limit=2&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([r["review_id"] for r in payload["reviews"]], review_ids[4:5])
        self.assertIsNone(payload["next_after"])

    def test_04_limit_boundary_values(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_reviews(["review-01"])
        server = self._start_server(fixture.runtime_dir)

        for accepted in ("1", "500"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/reviews?limit={accepted}"
            )
            self.assertEqual(status, 200, f"limit={accepted} should be accepted, got body {body!r}")

        for rejected in ("0", "501", "-1", "1.5", "abc", "007"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/reviews?limit={rejected}"
            )
            self.assertEqual(status, 400, f"limit={rejected} should be rejected, got body {body!r}")
            payload = json.loads(body)
            self.assertEqual(payload["error"], "invalid_query")
            self.assertEqual(payload["detail"], "limit must be an integer from 1 through 500")

    def test_05_query_validation_identical_across_all_three_snapshot_endpoints(self) -> None:
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
            status_reviews, _ct, body_reviews = _request(
                server.bound_port, "GET", f"/snapshot/reviews{suffix}"
            )
            status_attempts, _ct, body_attempts = _request(
                server.bound_port, "GET", f"/snapshot/attempts{suffix}"
            )
            status_packets, _ct, body_packets = _request(
                server.bound_port, "GET", f"/snapshot/packets{suffix}"
            )
            self.assertEqual(status_reviews, 400)
            self.assertEqual(status_attempts, 400)
            self.assertEqual(status_packets, 400)
            self.assertEqual(body_reviews, body_attempts, f"bodies diverged for {suffix}")
            self.assertEqual(body_reviews, body_packets, f"bodies diverged for {suffix}")

    def test_06_unknown_path_and_wrong_method_for_reviews_route(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/review")
        self.assertEqual(status, 404)
        self.assertEqual(body, read_api._NOT_FOUND_BODY)

        status, _content_type, body = _request(server.bound_port, "POST", "/snapshot/reviews")
        self.assertEqual(status, 405)
        self.assertEqual(body, read_api._METHOD_NOT_ALLOWED_BODY)

    def test_07_other_routes_unaffected_by_new_route_addition(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_reviews(["review-01"])
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"status":"ready"}')

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/packets")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"next_after":null,"packets":[]}')

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/attempts")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"attempts":[],"next_after":null}')

    def test_08_database_unavailable_returns_503(self) -> None:
        fixture_root = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.addCleanup(fixture_root.cleanup)
        no_database_runtime_dir = Path(fixture_root.name) / "runtime-without-database"
        no_database_runtime_dir.mkdir(parents=True)

        server = self._start_server(no_database_runtime_dir)
        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/reviews")
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"database_unavailable"}')

        status, _content_type, body = _request(server.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')

    def test_09_concurrent_requests_do_not_corrupt_pagination(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        review_ids = [f"review-{i:02d}" for i in range(1, 21)]
        specs = [
            {"review_id": review_id, "head_commit": _hex_commit(i)}
            for i, review_id in enumerate(review_ids, start=1)
        ]
        fixture.insert_review_specs(specs)
        server = self._start_server(fixture.runtime_dir)

        def _page_through() -> list[str]:
            collected: list[str] = []
            after: str | None = None
            while True:
                path = "/snapshot/reviews?limit=3" + (f"&after={after}" if after else "")
                status, _content_type, body = _request(server.bound_port, "GET", path)
                self.assertEqual(status, 200)
                payload = json.loads(body)
                collected.extend(r["review_id"] for r in payload["reviews"])
                after = payload["next_after"]
                if after is None:
                    break
            return collected

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_page_through) for _ in range(10)]
            results = [future.result() for future in futures]

        for result in results:
            self.assertEqual(result, review_ids)


if __name__ == "__main__":
    unittest.main()
