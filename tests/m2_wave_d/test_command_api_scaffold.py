from __future__ import annotations

import http.client
import json
import unittest
from unittest import mock

from maestro import read_api


def _request(
    port: int,
    method: str,
    path: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        response_body = response.read()
        return response.status, response.getheader("Content-Type"), response_body
    finally:
        connection.close()


class CommandApiScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = read_api.ReadApiServer(read_api.ReadApiConfig(port=0))
        self.server.start()
        self.addCleanup(self.server.stop)
        self.received: list[dict] = []

    def _fake_handler(self, handler: "read_api._ReadApiRequestHandler", envelope: dict) -> None:
        self.received.append(envelope)
        handler._respond(200, read_api.canonical_response_json({"ok": True}))

    def test_01_valid_envelope_reaches_the_registered_handler_verbatim(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            payload = {
                "idempotency_key": "abc-123",
                "actor": {"actor_type": "owner", "actor_id": "u1", "correlation_id": "c1"},
                "extra": "field",
            }
            status, content_type, response_body = _request(
                self.server.bound_port,
                "POST",
                "/command/example",
                body=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(response_body, b'{"ok":true}')
        self.assertEqual(self.received, [payload])

    def test_02_unregistered_command_path_returns_404(self) -> None:
        status, _content_type, body = _request(
            self.server.bound_port, "POST", "/command/does-not-exist", body=b"{}"
        )
        self.assertEqual(status, 404)
        self.assertEqual(body, b'{"error":"not_found"}')
        self.assertEqual(self.received, [])

    def test_03_get_on_registered_command_path_returns_405(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            status, _content_type, body = _request(self.server.bound_port, "GET", "/command/example")
        self.assertEqual(status, 405)
        self.assertEqual(body, b'{"error":"method_not_allowed"}')
        self.assertEqual(self.received, [])

    def test_04_missing_body_returns_400_invalid_envelope(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            status, _content_type, body = _request(self.server.bound_port, "POST", "/command/example")
        self.assertEqual(status, 400)
        self.assertEqual(body, b'{"detail":"request body must be a JSON object","error":"invalid_envelope"}')
        self.assertEqual(self.received, [])

    def test_05_malformed_json_returns_400_invalid_json(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            status, _content_type, body = _request(
                self.server.bound_port, "POST", "/command/example", body=b"{not json"
            )
        self.assertEqual(status, 400)
        self.assertEqual(body, b'{"error":"invalid_json"}')
        self.assertEqual(self.received, [])

    def test_06_non_object_json_body_returns_400_invalid_envelope(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            for literal in (b"[1,2,3]", b'"a string"', b"42", b"null", b"true"):
                status, _content_type, body = _request(
                    self.server.bound_port, "POST", "/command/example", body=literal
                )
                self.assertEqual(status, 400, literal)
                self.assertEqual(
                    body,
                    b'{"detail":"request body must be a JSON object","error":"invalid_envelope"}',
                    literal,
                )
        self.assertEqual(self.received, [])

    def test_07_missing_or_invalid_idempotency_key_returns_400(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            bad_bodies = [
                {"actor": {"actor_type": "owner", "actor_id": "u1", "correlation_id": "c1"}},
                {"idempotency_key": "", "actor": {"actor_type": "owner", "actor_id": "u1", "correlation_id": "c1"}},
                {"idempotency_key": 123, "actor": {"actor_type": "owner", "actor_id": "u1", "correlation_id": "c1"}},
            ]
            for payload in bad_bodies:
                status, _content_type, body = _request(
                    self.server.bound_port,
                    "POST",
                    "/command/example",
                    body=json.dumps(payload).encode("utf-8"),
                )
                self.assertEqual(status, 400, payload)
                self.assertEqual(
                    body,
                    b'{"detail":"idempotency_key is required and must be a non-empty string","error":"invalid_envelope"}',
                    payload,
                )
        self.assertEqual(self.received, [])

    def test_08_missing_or_invalid_actor_returns_400(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            bad_bodies = [
                {"idempotency_key": "abc-123"},
                {"idempotency_key": "abc-123", "actor": "not-an-object"},
                {"idempotency_key": "abc-123", "actor": ["a", "list"]},
            ]
            for payload in bad_bodies:
                status, _content_type, body = _request(
                    self.server.bound_port,
                    "POST",
                    "/command/example",
                    body=json.dumps(payload).encode("utf-8"),
                )
                self.assertEqual(status, 400, payload)
                self.assertEqual(
                    body,
                    b'{"detail":"actor is required and must be a JSON object","error":"invalid_envelope"}',
                    payload,
                )
        self.assertEqual(self.received, [])

    def test_09_negative_or_non_numeric_content_length_returns_400(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            for header_value in ("-1", "not-a-number"):
                status, _content_type, body = _request(
                    self.server.bound_port,
                    "POST",
                    "/command/example",
                    body=b"",
                    headers={"Content-Length": header_value},
                )
                self.assertEqual(status, 400, header_value)
                self.assertEqual(body, b'{"error":"invalid_content_length"}', header_value)
        self.assertEqual(self.received, [])

    def test_10_existing_health_route_is_unaffected(self) -> None:
        status, content_type, body = _request(self.server.bound_port, "GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(body, b'{"status":"ready"}')

        status, _content_type, body = _request(self.server.bound_port, "POST", "/health")
        self.assertEqual(status, 405)
        self.assertEqual(body, b'{"error":"method_not_allowed"}')

    def test_11_only_the_real_resolve_decision_command_is_registered_in_production_code(self) -> None:
        # D1 shipped the scaffold with zero commands wired; D2 wires the
        # first real one (see tests/m2_wave_d/test_resolve_decision_command.py).
        # This asserts the exact, closed set — not just "non-empty" — so a
        # future slice accidentally registering an extra route is caught here.
        self.assertEqual(
            read_api._COMMAND_ROUTES,
            {"/command/resolve-decision": read_api._handle_resolve_decision},
        )

    def test_12_oversized_content_length_rejected_before_reading_body(self) -> None:
        with mock.patch.dict(read_api._COMMAND_ROUTES, {"/command/example": self._fake_handler}):
            connection = http.client.HTTPConnection("127.0.0.1", self.server.bound_port, timeout=5)
            try:
                oversized = read_api._MAX_COMMAND_BODY_BYTES + 1
                connection.putrequest("POST", "/command/example")
                connection.putheader("Content-Length", str(oversized))
                connection.endheaders()
                # Deliberately send far fewer bytes than declared, and never
                # send the rest. If the server tried to read `oversized`
                # bytes before responding, this would hang until the
                # client's own 5s socket timeout fired instead of returning
                # promptly — proving the cap is checked before `rfile.read`.
                connection.send(b"{}")
                response = connection.getresponse()
                body = response.read()
                status = response.status
            finally:
                connection.close()
        self.assertEqual(status, 413)
        self.assertEqual(body, b'{"error":"payload_too_large"}')
        self.assertEqual(self.received, [])


if __name__ == "__main__":
    unittest.main()
