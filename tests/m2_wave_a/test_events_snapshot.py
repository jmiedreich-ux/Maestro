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

_EVENTS_SNAPSHOT_FIELDS = {
    "actor_id", "actor_type", "after_json", "before_json", "causation_event_id",
    "command_fingerprint", "correlation_id", "created_at", "entity_id", "entity_type",
    "event_id", "event_type", "idempotency_key", "observed_at", "reason",
}


def _request(port: int, method: str, path: str) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), body
    finally:
        connection.close()


def _hex_fingerprint(prefix: int) -> str:
    return f"{prefix:064x}"


def _insert_modern_event(
    connection: sqlite3.Connection,
    *,
    idempotency_key: str,
    entity_type: str = "Packet",
    entity_id: str = "packet-1",
    event_type: str = "PacketStateChanged",
    before_json: str = '{"state":"Planned"}',
    after_json: str = '{"state":"Claimed"}',
    reason: str = '{"kind":"reason"}',
    created_at: str = FIXED_TIME,
    correlation_id: str = "correlation-1",
    causation_event_id: int | None = None,
    actor_type: str = "system",
    actor_id: str = "actor-1",
    command_fingerprint: str = "a" * 64,
    observed_at: str = FIXED_TIME,
) -> int:
    """Insert a modern-shape event row satisfying all schema-4 triggers."""
    cursor = connection.execute(
        """
        INSERT INTO events(
            idempotency_key, entity_type, entity_id, event_type, before_json,
            after_json, reason, created_at, correlation_id, causation_event_id,
            actor_type, actor_id, command_fingerprint, observed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            idempotency_key, entity_type, entity_id, event_type, before_json,
            after_json, reason, created_at, correlation_id, causation_event_id,
            actor_type, actor_id, command_fingerprint, observed_at,
        ),
    )
    return int(cursor.lastrowid)


def _insert_legacy_event(
    connection: sqlite3.Connection,
    *,
    idempotency_key: str,
    entity_id: str = "project-1",
    before_json: str = '{"facts":[]}',
    after_json: str = '{"facts":["loaded"]}',
    reason: str = "candidate authority is reviewable",
    created_at: str = FIXED_TIME,
) -> int:
    """Insert the one legacy-shape event row the triggers exempt from schema-4 shape checks."""
    cursor = connection.execute(
        """
        INSERT INTO events(
            idempotency_key, entity_type, entity_id, event_type, before_json,
            after_json, reason, created_at
        ) VALUES (?, 'ProjectRegistrationRun', ?, 'AuthorityLoaded', ?, ?, ?, ?)
        """,
        (idempotency_key, entity_id, before_json, after_json, reason, created_at),
    )
    return int(cursor.lastrowid)


class _RuntimeFixture:
    """A real, migrated database under the fixed var/ root, plus fixture events."""

    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary.name) / "runtime"
        self.config = RuntimeConfig.from_runtime_dir(self.runtime_dir)
        SQLiteFoundation(self.config).health()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.config.database_path))

    def insert_modern_events(self, count: int, *, prefix: str = "event") -> list[int]:
        connection = self.connect()
        ids: list[int] = []
        try:
            for i in range(count):
                event_id = _insert_modern_event(
                    connection,
                    idempotency_key=f"{prefix}-idempotency-{i:03d}",
                    entity_id=f"{prefix}-entity-{i:03d}",
                    command_fingerprint=_hex_fingerprint(i + 1),
                )
                ids.append(event_id)
            connection.commit()
        finally:
            connection.close()
        return ids

    def close(self) -> None:
        self._temporary.cleanup()


class EventsSnapshotTests(unittest.TestCase):
    def _start_server(self, runtime_dir) -> read_api.ReadApiServer:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=runtime_dir))
        server.start()
        self.addCleanup(server.stop)
        return server

    def test_01_empty_table_returns_empty_page(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/events")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"events":[],"next_after":null}')

    def test_02_full_field_projection_raw_strings_and_nulls(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        connection = fixture.connect()
        try:
            legacy_reason = "candidate authority is reviewable"
            legacy_id = _insert_legacy_event(
                connection,
                idempotency_key="legacy-idempotency-001",
                reason=legacy_reason,
            )
            # One key deliberately nested and out of alphabetical order ("b" before
            # "a") to prove no re-sorting or decoding happens: the raw stored text
            # must come back byte-for-byte.
            modern_reason = json.dumps({"kind": "reason", "nested": {"b": 2, "a": 1}})
            modern_before = json.dumps({"state": "Planned"})
            modern_after = json.dumps({"state": "Claimed"})
            modern_id = _insert_modern_event(
                connection,
                idempotency_key="modern-idempotency-001",
                entity_type="Packet",
                entity_id="packet-modern-1",
                event_type="PacketStateChanged",
                before_json=modern_before,
                after_json=modern_after,
                reason=modern_reason,
                correlation_id="correlation-modern-1",
                causation_event_id=legacy_id,
                actor_type="system",
                actor_id="actor-modern-1",
                command_fingerprint=_hex_fingerprint(99),
                observed_at=FIXED_TIME,
            )
            connection.commit()
        finally:
            connection.close()

        server = self._start_server(fixture.runtime_dir)
        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/events")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        payload = json.loads(body)
        self.assertIsNone(payload["next_after"])
        self.assertEqual(len(payload["events"]), 2)

        for event in payload["events"]:
            self.assertEqual(set(event.keys()), _EVENTS_SNAPSHOT_FIELDS)

        by_id = {event["event_id"]: event for event in payload["events"]}

        modern = by_id[modern_id]
        self.assertEqual(modern["entity_type"], "Packet")
        self.assertEqual(modern["entity_id"], "packet-modern-1")
        self.assertEqual(modern["event_type"], "PacketStateChanged")
        self.assertEqual(modern["before_json"], modern_before)
        self.assertEqual(modern["after_json"], modern_after)
        self.assertEqual(modern["reason"], modern_reason)
        self.assertEqual(modern["correlation_id"], "correlation-modern-1")
        self.assertEqual(modern["actor_type"], "system")
        self.assertEqual(modern["actor_id"], "actor-modern-1")
        self.assertEqual(modern["command_fingerprint"], _hex_fingerprint(99))
        self.assertEqual(modern["observed_at"], FIXED_TIME)
        self.assertEqual(modern["causation_event_id"], legacy_id)

        legacy = by_id[legacy_id]
        self.assertEqual(legacy["entity_type"], "ProjectRegistrationRun")
        self.assertEqual(legacy["event_type"], "AuthorityLoaded")
        self.assertEqual(legacy["reason"], legacy_reason)
        self.assertIsNone(legacy["correlation_id"])
        self.assertIsNone(legacy["actor_type"])
        self.assertIsNone(legacy["actor_id"])
        self.assertIsNone(legacy["command_fingerprint"])
        self.assertIsNone(legacy["observed_at"])
        self.assertIsNone(legacy["causation_event_id"])

        # event_id and causation_event_id must render as bare JSON numbers, not
        # quoted strings -- check the raw response bytes directly.
        raw = body.decode("utf-8")
        self.assertIn(f'"event_id":{modern_id}', raw)
        self.assertIn(f'"event_id":{legacy_id}', raw)
        self.assertIn(f'"causation_event_id":{legacy_id}', raw)
        self.assertNotIn(f'"causation_event_id":"{legacy_id}"', raw)

    def test_03_newest_first_pagination_and_after_semantics(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        ids = fixture.insert_modern_events(5)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/events?limit=3")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([e["event_id"] for e in payload["events"]], list(reversed(ids))[0:3])
        self.assertEqual(payload["next_after"], ids[2])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/events?limit=3&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([e["event_id"] for e in payload["events"]], list(reversed(ids))[3:5])
        self.assertIsNone(payload["next_after"])

    def test_04_limit_boundary_values(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_modern_events(1)
        server = self._start_server(fixture.runtime_dir)

        for accepted in ("1", "500"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/events?limit={accepted}"
            )
            self.assertEqual(status, 200, f"limit={accepted} should be accepted, got body {body!r}")

        for rejected in ("0", "501", "-1", "1.5", "abc", "007"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/events?limit={rejected}"
            )
            self.assertEqual(status, 400, f"limit={rejected} should be rejected, got body {body!r}")
            payload = json.loads(body)
            self.assertEqual(payload["error"], "invalid_query")
            self.assertEqual(payload["detail"], "limit must be an integer from 1 through 500")

    def test_05_shared_query_validation_identical_across_all_four_endpoints(self) -> None:
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
            status_events, _ct, body_events = _request(
                server.bound_port, "GET", f"/snapshot/events{suffix}"
            )
            status_reviews, _ct, body_reviews = _request(
                server.bound_port, "GET", f"/snapshot/reviews{suffix}"
            )
            status_attempts, _ct, body_attempts = _request(
                server.bound_port, "GET", f"/snapshot/attempts{suffix}"
            )
            status_packets, _ct, body_packets = _request(
                server.bound_port, "GET", f"/snapshot/packets{suffix}"
            )
            self.assertEqual(status_events, 400, f"suffix={suffix}")
            self.assertEqual(status_reviews, 400, f"suffix={suffix}")
            self.assertEqual(status_attempts, 400, f"suffix={suffix}")
            self.assertEqual(status_packets, 400, f"suffix={suffix}")
            self.assertEqual(body_events, body_reviews, f"bodies diverged for {suffix}")
            self.assertEqual(body_events, body_attempts, f"bodies diverged for {suffix}")
            self.assertEqual(body_events, body_packets, f"bodies diverged for {suffix}")

    def test_06_after_must_be_integer(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_modern_events(1)
        server = self._start_server(fixture.runtime_dir)

        expected_body = read_api.canonical_response_json(
            {"error": "invalid_query", "detail": "after must be a non-negative integer"}
        )
        for rejected in ("abc", "1.5"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/events?after={rejected}"
            )
            self.assertEqual(status, 400, f"after={rejected} should be rejected, got body {body!r}")
            self.assertEqual(body, expected_body)

        for accepted in ("0", "999999999"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/events?after={accepted}"
            )
            self.assertEqual(status, 200, f"after={accepted} should be accepted, got body {body!r}")

    def test_07_unknown_path_and_wrong_method_for_events_route(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/event")
        self.assertEqual(status, 404)
        self.assertEqual(body, read_api._NOT_FOUND_BODY)

        status, _content_type, body = _request(server.bound_port, "POST", "/snapshot/events")
        self.assertEqual(status, 405)
        self.assertEqual(body, read_api._METHOD_NOT_ALLOWED_BODY)

    def test_08_other_routes_unaffected_by_fifth_route_addition(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
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

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/reviews")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"next_after":null,"reviews":[]}')

    def test_09_database_unavailable_returns_503(self) -> None:
        fixture_root = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.addCleanup(fixture_root.cleanup)
        no_database_runtime_dir = Path(fixture_root.name) / "runtime-without-database"
        no_database_runtime_dir.mkdir(parents=True)

        server = self._start_server(no_database_runtime_dir)
        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/events")
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"database_unavailable"}')

        status, _content_type, body = _request(server.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')

    def test_10_concurrent_requests_do_not_corrupt_pagination(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        ids = fixture.insert_modern_events(20)
        expected_order = list(reversed(ids))
        server = self._start_server(fixture.runtime_dir)

        def _page_through() -> list[int]:
            collected: list[int] = []
            after: int | None = None
            while True:
                path = "/snapshot/events?limit=3" + (f"&after={after}" if after is not None else "")
                status, _content_type, body = _request(server.bound_port, "GET", path)
                self.assertEqual(status, 200)
                payload = json.loads(body)
                collected.extend(e["event_id"] for e in payload["events"])
                after = payload["next_after"]
                if after is None:
                    break
            return collected

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_page_through) for _ in range(10)]
            results = [future.result() for future in futures]

        for result in results:
            self.assertEqual(result, expected_order)


if __name__ == "__main__":
    unittest.main()
