from __future__ import annotations

import contextlib
import http.client
import io
import json
import signal
import subprocess
import sys
import unittest
from unittest import mock

from maestro import read_api
from maestro.config import REPOSITORY_ROOT


SERVICES_MAESTRO_DIR = REPOSITORY_ROOT / "services" / "maestro"


def _request(port: int, method: str, path: str) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        return response.status, response.getheader("Content-Type"), body
    finally:
        connection.close()


class ReadApiScaffoldTests(unittest.TestCase):
    def test_01_non_loopback_host_rejected_before_bind(self) -> None:
        with mock.patch.object(read_api.ThreadingHTTPServer, "__init__") as mock_init:
            with self.assertRaises(read_api.ReadApiBindError):
                read_api.ReadApiConfig(host="0.0.0.0")
            with self.assertRaises(read_api.ReadApiBindError):
                read_api.ReadApiConfig(host="192.168.1.5")
        mock_init.assert_not_called()

    def test_02_health_returns_exact_body_with_no_log_output(self) -> None:
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

    def test_03_unknown_path_returns_404_regardless_of_method(self) -> None:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        server.start()
        self.addCleanup(server.stop)

        for method in ("GET", "POST"):
            status, _content_type, body = _request(server.bound_port, method, "/anything-else")
            self.assertEqual(status, 404)
            self.assertEqual(body, b'{"error":"not_found"}')

    def test_04_non_get_on_health_returns_405(self) -> None:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        server.start()
        self.addCleanup(server.stop)

        for method in ("POST", "DELETE"):
            status, _content_type, body = _request(server.bound_port, method, "/health")
            self.assertEqual(status, 405)
            self.assertEqual(body, b'{"error":"method_not_allowed"}')

    def test_05_double_start_raises_without_leaking_socket(self) -> None:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        server.start()
        self.addCleanup(server.stop)
        port = server.bound_port

        with mock.patch.object(read_api.ThreadingHTTPServer, "__init__") as mock_init:
            with self.assertRaises(RuntimeError):
                server.start()
        mock_init.assert_not_called()

        status, _content_type, body = _request(port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')

        httpd = server._httpd
        with mock.patch.object(httpd, "server_close", wraps=httpd.server_close) as mock_close:
            server.stop()
        mock_close.assert_called_once()

    def test_06_stop_is_idempotent_and_restart_works(self) -> None:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))

        server.stop()  # no-op before any start()

        server.start()
        self.addCleanup(server.stop)
        first_port = server.bound_port
        status, _content_type, body = _request(first_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')

        server.stop()
        server.stop()  # idempotent after a real stop too

        server.start()
        second_port = server.bound_port
        status, _content_type, body = _request(second_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, b'{"status":"ready"}')
        self.assertNotEqual(first_port, second_port)

    def test_07_bound_port_raises_before_start(self) -> None:
        server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        with self.assertRaises(RuntimeError):
            _ = server.bound_port

    def test_08_cli_serve_read_api_prints_status_and_stops_on_sigint(self) -> None:
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

    def test_09_cli_rejects_invalid_host_with_clean_exit_and_no_listening_line(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
