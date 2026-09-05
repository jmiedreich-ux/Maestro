from __future__ import annotations

import concurrent.futures
import contextlib
import http.client
import io
import json
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from maestro import config as config_module
from maestro import read_api
from maestro.config import DEFAULT_RUNTIME_DIR, REPOSITORY_ROOT, RuntimeConfig
from maestro.storage import SQLiteFoundation


SERVICES_MAESTRO_DIR = REPOSITORY_ROOT / "services" / "maestro"
CLI_SOURCE_PATH = SERVICES_MAESTRO_DIR / "maestro" / "cli.py"

FIXED_TIME = "2026-01-01T00:00:00.000000Z"
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40


def _request(port: int, method: str, path: str) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), body
    finally:
        connection.close()


def _insert_packet(
    connection: sqlite3.Connection,
    *,
    packet_id: str,
    run_id: str = "run-1",
    work_item_id: str = "work-1",
    state: str = "Planned",
    current_head: str | None = None,
    base_commit: str = COMMIT_A,
    correction_count: int = 0,
    created_at: str = FIXED_TIME,
    updated_at: str = FIXED_TIME,
    version: int = 1,
) -> None:
    connection.execute(
        """
        INSERT INTO packets(
            packet_id, run_id, work_item_id, packet_revision, authority_reference,
            base_commit, current_head, expected_branch, role_contract_reference,
            sop_reference, executor_class, integration_route, reviewer_route,
            owned_paths_json, forbidden_paths_json, checks_json, resource_claims_json,
            context_policy_json, state, correction_count, created_at, updated_at, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            packet_id, run_id, work_item_id, f"{packet_id}-revision", f"{packet_id}-authority",
            base_commit, current_head, f"{packet_id}-branch", f"{packet_id}-role-contract",
            f"{packet_id}-sop", f"{packet_id}-executor-class", f"{packet_id}-integration",
            f"{packet_id}-reviewer", "[]", "[]", "[]", "[]", "{}", state, correction_count,
            created_at, updated_at, version,
        ),
    )


class _RuntimeFixture:
    """A real, migrated database under the fixed var/ root, plus fixture packets."""

    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.runtime_dir = Path(self._temporary.name) / "runtime"
        self.config = RuntimeConfig.from_runtime_dir(self.runtime_dir)
        SQLiteFoundation(self.config).health()

    def insert_packets(self, packet_ids: list[str], **shared_kwargs) -> None:
        connection = sqlite3.connect(str(self.config.database_path))
        try:
            for packet_id in packet_ids:
                _insert_packet(connection, packet_id=packet_id, **shared_kwargs)
            connection.commit()
        finally:
            connection.close()

    def insert_packet_specs(self, specs: list[dict]) -> None:
        connection = sqlite3.connect(str(self.config.database_path))
        try:
            for spec in specs:
                _insert_packet(connection, **spec)
            connection.commit()
        finally:
            connection.close()

    def close(self) -> None:
        self._temporary.cleanup()


class _ConnectionLeakTracker:
    """Wraps sqlite3.connect to prove every successfully opened connection is closed."""

    def __init__(self, real_connect) -> None:
        self._real_connect = real_connect
        self.opened = 0
        self.closed = 0

    def __call__(self, *args, **kwargs):
        connection = self._real_connect(*args, **kwargs)
        self.opened += 1
        original_close = connection.close

        def _tracked_close(*close_args, **close_kwargs):
            self.closed += 1
            return original_close(*close_args, **close_kwargs)

        connection.close = _tracked_close
        return connection


class PacketsSnapshotTests(unittest.TestCase):
    def _start_server(self, runtime_dir) -> read_api.ReadApiServer:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=runtime_dir))
        server.start()
        self.addCleanup(server.stop)
        return server

    def test_01_empty_table_returns_empty_page(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/packets")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"next_after":null,"packets":[]}')

    def test_02_default_limit_and_field_projection(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_packet_specs(
            [
                {"packet_id": "packet-01", "current_head": None},
                {"packet_id": "packet-02", "current_head": COMMIT_B},
                {"packet_id": "packet-03", "current_head": COMMIT_B},
            ]
        )
        server = self._start_server(fixture.runtime_dir)

        status, content_type, body = _request(server.bound_port, "GET", "/snapshot/packets")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        payload = json.loads(body)
        self.assertIsNone(payload["next_after"])
        self.assertEqual(len(payload["packets"]), 3)

        expected_fields = {
            "base_commit", "correction_count", "created_at", "current_head", "packet_id",
            "packet_revision", "run_id", "state", "updated_at", "version", "work_item_id",
        }
        for packet in payload["packets"]:
            self.assertEqual(set(packet.keys()), expected_fields)

        by_id = {packet["packet_id"]: packet for packet in payload["packets"]}
        self.assertIsNone(by_id["packet-01"]["current_head"])
        self.assertEqual(by_id["packet-02"]["current_head"], COMMIT_B)
        self.assertEqual(by_id["packet-01"]["base_commit"], COMMIT_A)
        self.assertEqual(by_id["packet-01"]["state"], "Planned")
        self.assertEqual(by_id["packet-01"]["correction_count"], 0)
        self.assertEqual(by_id["packet-01"]["version"], 1)
        self.assertEqual(by_id["packet-01"]["run_id"], "run-1")
        self.assertEqual(by_id["packet-01"]["work_item_id"], "work-1")

    def test_03_pagination_next_after_and_exact_page_boundary(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        packet_ids = [f"packet-{i:02d}" for i in range(1, 6)]
        fixture.insert_packets(packet_ids)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/packets?limit=2")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([p["packet_id"] for p in payload["packets"]], packet_ids[0:2])
        self.assertEqual(payload["next_after"], packet_ids[1])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/packets?limit=2&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([p["packet_id"] for p in payload["packets"]], packet_ids[2:4])
        self.assertEqual(payload["next_after"], packet_ids[3])

        status, _content_type, body = _request(
            server.bound_port, "GET", f"/snapshot/packets?limit=2&after={payload['next_after']}"
        )
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual([p["packet_id"] for p in payload["packets"]], packet_ids[4:5])
        self.assertIsNone(payload["next_after"])

    def test_04_limit_boundary_values(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_packets(["packet-01"])
        server = self._start_server(fixture.runtime_dir)

        for accepted in ("1", "500"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/packets?limit={accepted}"
            )
            self.assertEqual(status, 200, f"limit={accepted} should be accepted, got body {body!r}")

        for rejected in ("0", "501", "-1", "1.5", "abc", "007"):
            status, _content_type, body = _request(
                server.bound_port, "GET", f"/snapshot/packets?limit={rejected}"
            )
            self.assertEqual(status, 400, f"limit={rejected} should be rejected, got body {body!r}")
            payload = json.loads(body)
            self.assertEqual(payload["error"], "invalid_query")
            self.assertEqual(payload["detail"], "limit must be an integer from 1 through 500")

    def test_05_after_and_unknown_key_and_repeated_key_rejected(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/packets?after=")
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body), {"error": "invalid_query", "detail": "after must not be empty"})

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/packets?bogus=1")
        self.assertEqual(status, 400)
        self.assertEqual(
            json.loads(body), {"error": "invalid_query", "detail": "unknown query parameter: bogus"}
        )

        status, _content_type, body = _request(
            server.bound_port, "GET", "/snapshot/packets?limit=1&limit=2"
        )
        self.assertEqual(status, 400)
        self.assertEqual(
            json.loads(body),
            {"error": "invalid_query", "detail": "query parameter appears more than once: limit"},
        )

        status, _content_type, body = _request(
            server.bound_port, "GET", "/snapshot/packets?after=x&after=y"
        )
        self.assertEqual(status, 400)
        self.assertEqual(
            json.loads(body),
            {"error": "invalid_query", "detail": "query parameter appears more than once: after"},
        )

    def test_06_unknown_path_and_wrong_method_unchanged(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/packet")
        self.assertEqual(status, 404)
        self.assertEqual(body, read_api._NOT_FOUND_BODY)

        status, _content_type, body = _request(server.bound_port, "POST", "/snapshot/packets")
        self.assertEqual(status, 405)
        self.assertEqual(body, read_api._METHOD_NOT_ALLOWED_BODY)

    def test_07_health_route_byte_identical_after_refactor(self) -> None:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        server.start()
        self.addCleanup(server.stop)

        captured_stderr = io.StringIO()
        with contextlib.redirect_stderr(captured_stderr):
            status, content_type, body = _request(server.bound_port, "GET", "/health")

        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"status":"ready"}')
        self.assertEqual(captured_stderr.getvalue(), "")

    def test_08_database_unavailable_returns_503(self) -> None:
        # Sub-case (a): containing directory exists, database file does not.
        fixture_root = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.addCleanup(fixture_root.cleanup)
        no_database_runtime_dir = Path(fixture_root.name) / "runtime-without-database"
        no_database_runtime_dir.mkdir(parents=True)

        real_connect = sqlite3.connect
        tracker = _ConnectionLeakTracker(real_connect)
        server_a = self._start_server(no_database_runtime_dir)
        with mock.patch.object(read_api.sqlite3, "connect", side_effect=tracker):
            status, _content_type, body = _request(server_a.bound_port, "GET", "/snapshot/packets")
        self.assertEqual(status, 503)
        self.assertEqual(body, b'{"error":"database_unavailable"}')
        self.assertEqual(tracker.opened, tracker.closed, "a successfully opened connection leaked")

        # The server keeps serving /health correctly after the failed request.
        status, _content_type, body = _request(server_a.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')

        # Sub-case (b): the fixed var/ root itself has never been created for this path.
        never_created_root = Path(tempfile.mkdtemp()) / "never-created-var-root"
        self.assertFalse(never_created_root.exists())
        server_b = read_api.ReadApiServer(read_api.ReadApiConfig(port=0, runtime_dir=None))
        with mock.patch.object(config_module, "DEFAULT_RUNTIME_DIR", never_created_root):
            server_b.start()
            self.addCleanup(server_b.stop)
            status, _content_type, body = _request(server_b.bound_port, "GET", "/snapshot/packets")
            self.assertEqual(status, 503)
            self.assertEqual(body, b'{"error":"database_unavailable"}')

            status, _content_type, body = _request(server_b.bound_port, "GET", "/health")
            self.assertEqual(status, 200)
            self.assertEqual(body, b'{"status":"ready"}')

    def test_09_query_parsing_uses_path_only_not_query_string_for_routing(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        fixture.insert_packets(["packet-01"])
        server = self._start_server(fixture.runtime_dir)

        status, _content_type, body = _request(server.bound_port, "GET", "/snapshot/packets?limit=1")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(len(payload["packets"]), 1)

        status, content_type, body = _request(server.bound_port, "GET", "/health?ignored=1")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"status":"ready"}')

    def test_10_wait_forever_replaces_private_thread_access(self) -> None:
        cli_source = CLI_SOURCE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("_thread", cli_source)

        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        server.start()
        self.addCleanup(server.stop)

        waiter_returned = threading.Event()

        def _wait() -> None:
            server.wait_forever()
            waiter_returned.set()

        waiter = threading.Thread(target=_wait, daemon=True)
        waiter.start()
        try:
            self.assertFalse(waiter_returned.wait(timeout=0.5), "wait_forever returned before stop()")
            server.stop()
            self.assertTrue(waiter_returned.wait(timeout=5.0), "wait_forever did not return after stop()")
        finally:
            waiter.join(timeout=5.0)

    def test_11_cli_serve_read_api_still_passes(self) -> None:
        process = subprocess.Popen(
            [sys.executable, "-m", "maestro.cli", "serve-read-api", "--host", "127.0.0.1", "--port", "0"],
            cwd=SERVICES_MAESTRO_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            line = process.stdout.readline()
            payload = json.loads(line)
            self.assertEqual(set(payload.keys()), {"host", "port", "status"})
            self.assertEqual(payload["status"], "listening")
            self.assertEqual(payload["host"], "127.0.0.1")
            self.assertIsInstance(payload["port"], int)
            self.assertGreater(payload["port"], 0)

            status, _content_type, body = _request(payload["port"], "GET", "/health")
            self.assertEqual(status, 200)
            self.assertEqual(body, b'{"status":"ready"}')

            process.send_signal(signal.SIGINT)
            returncode = process.wait(timeout=5)
            self.assertEqual(returncode, 0)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()

        result = subprocess.run(
            [sys.executable, "-m", "maestro.cli", "serve-read-api", "--host", "0.0.0.0", "--port", "0"],
            cwd=SERVICES_MAESTRO_DIR,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        error_payload = json.loads(result.stderr.strip())
        self.assertEqual(error_payload["error"], "invalid_host")

    def test_12_concurrent_requests_do_not_corrupt_pagination(self) -> None:
        fixture = _RuntimeFixture()
        self.addCleanup(fixture.close)
        packet_ids = [f"packet-{i:02d}" for i in range(1, 21)]
        fixture.insert_packets(packet_ids)
        server = self._start_server(fixture.runtime_dir)

        def _page_through() -> list[str]:
            collected: list[str] = []
            after: str | None = None
            while True:
                path = "/snapshot/packets?limit=3" + (f"&after={after}" if after else "")
                status, _content_type, body = _request(server.bound_port, "GET", path)
                self.assertEqual(status, 200)
                payload = json.loads(body)
                collected.extend(p["packet_id"] for p in payload["packets"])
                after = payload["next_after"]
                if after is None:
                    break
            return collected

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_page_through) for _ in range(10)]
            results = [future.result() for future in futures]

        for result in results:
            self.assertEqual(result, packet_ids)


if __name__ == "__main__":
    unittest.main()
