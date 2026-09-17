from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from maestro.foundation import Database, StorageSettings
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.http import RequestHTTPApplication, RequestHTTPServer
from maestro.service.registry import (
    OperationHandler,
    OperationRegistry,
    OperationResult,
    PreparedOperation,
)
from maestro.service.requests import RequestService
from maestro.terminal.connection import (
    CONNECT_TIMEOUT_SECONDS,
    DEFAULT_SERVICE_URL,
    EVENT_SILENCE_TIMEOUT_SECONDS,
    RECONNECT_DELAYS_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
    ConfigurationError,
    ConnectionConfiguration,
    ConnectionState,
    ConnectionUnavailable,
    CredentialError,
    ServiceClient,
    ServiceError,
    TerminalConnection,
    load_configuration,
    load_owner_credential,
    validate_service_url,
)
from maestro.terminal.main import TerminalApplication


OWNER_TOKEN = "a" * 64


class ScriptedClient:
    outcomes: list[object] = []

    def __init__(self, configuration: ConnectionConfiguration) -> None:
        self.configuration = configuration

    def workspace(self, *, connect_timeout: bool = False):
        assert connect_timeout
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class TerminalConnectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config_root = self.root / "config"
        self.maestro_config = self.config_root / "maestro"
        self.maestro_config.mkdir(parents=True)
        self.environment = {"XDG_CONFIG_HOME": str(self.config_root)}

    def write_token(self, path: Path | None = None, token: str = OWNER_TOKEN) -> Path:
        token_path = path or (self.maestro_config / "owner.token")
        token_path.write_text(token, encoding="ascii")
        token_path.chmod(0o600)
        return token_path

    def write_config(self, text: str) -> Path:
        path = self.maestro_config / "cli.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_configuration_uses_valid_address_and_falls_back_with_explanation(self) -> None:
        credential = self.write_token(self.root / "alternate.token")
        self.write_config(
            f'service_url = "http://127.0.0.1:9123/"\n'
            f'owner_credential_file = "{credential}"\n'
        )

        configured = load_configuration(environ=self.environment)
        self.assertEqual("http://127.0.0.1:9123", configured.service_url)
        self.assertEqual(credential, configured.credential_file)
        self.assertIsNone(configured.fallback_reason)

        self.write_config('service_url = "http://example.test:9123"\n')
        fallback = load_configuration(environ=self.environment)
        self.assertEqual(DEFAULT_SERVICE_URL, fallback.service_url)
        self.assertTrue(fallback.used_fallback)
        self.assertIn("loopback", fallback.fallback_reason or "")

    def test_only_explicit_loopback_http_origin_is_valid(self) -> None:
        self.assertEqual(
            "http://[::1]:8787", validate_service_url("http://[::1]:8787/")
        )
        invalid = (
            "https://localhost:8787",
            "http://localhost",
            "http://localhost:0",
            "http://localhost:65536",
            "http://user@localhost:8787",
            "http://127.0.0.1:8787/api",
            "http://127.0.0.1:8787/?query=yes",
        )
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ConfigurationError):
                validate_service_url(value)

    def test_credentials_require_exact_format_and_protection(self) -> None:
        path = self.write_token()
        self.assertEqual(OWNER_TOKEN, load_owner_credential(path))
        path.chmod(0o644)
        with self.assertRaisesRegex(CredentialError, "0600"):
            load_owner_credential(path)
        path.chmod(0o600)
        path.write_text(OWNER_TOKEN + "\n", encoding="ascii")
        with self.assertRaisesRegex(CredentialError, "invalid format"):
            load_owner_credential(path)
        link = self.maestro_config / "linked.token"
        link.symlink_to(path)
        with self.assertRaisesRegex(CredentialError, "cannot read"):
            load_owner_credential(link)

    def test_real_client_submits_and_reads_authenticated_receipt(self) -> None:
        token_path = self.write_token()
        database = Database(StorageSettings(path=self.root / "maestro.sqlite3"))
        authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )

        def prepare(request):
            return PreparedOperation(
                entity_id="sample-one",
                event_type="sample.saved",
                event_data={"value": request.payload["value"]},
                apply=lambda _transaction, _version: OperationResult(
                    data={"value": request.payload["value"]}
                ),
            )

        service = RequestService(
            database,
            authenticator,
            OperationRegistry((OperationHandler("question.answer", prepare),)),
        )
        server = RequestHTTPServer(RequestHTTPApplication(service))
        server.start()
        self.addCleanup(server.close)
        host, port = server.address
        client = ServiceClient(
            ConnectionConfiguration(
                service_url=f"http://{host}:{port}",
                credential_file=token_path,
                config_file=self.maestro_config / "cli.toml",
            )
        )

        submitted = client.submit(
            {
                "request_id": "request-one",
                "operation": "question.answer",
                "project_id": None,
                "activity_id": None,
                "question_id": None,
                "expected_version": 0,
                "payload": {"value": "saved through the real boundary"},
            }
        )
        looked_up = client.receipt("request-one")

        self.assertEqual(submitted, looked_up)
        self.assertEqual("completed", looked_up["receipt"]["status"])
        self.assertEqual(
            "saved through the real boundary",
            looked_up["receipt"]["result"]["value"],
        )

        with self.assertRaises(ServiceError) as rejected:
            client.receipt("not-recorded")

        self.assertEqual(404, rejected.exception.status_code)
        self.assertEqual("request_not_found", rejected.exception.code)
        self.assertNotIn(OWNER_TOKEN, repr(rejected.exception))

    def test_fixed_connect_and_request_timeouts_reach_transport(self) -> None:
        token_path = self.write_token()
        configuration = ConnectionConfiguration(
            service_url="http://localhost:8787",
            credential_file=token_path,
            config_file=self.maestro_config / "cli.toml",
        )
        opener = mock.Mock()
        opener.open.side_effect = ConnectionRefusedError("controlled refusal")
        client = ServiceClient(configuration, opener=opener)

        with self.assertRaises(ConnectionUnavailable):
            client.workspace(connect_timeout=True)
        self.assertEqual(CONNECT_TIMEOUT_SECONDS, opener.open.call_args.kwargs["timeout"])
        with self.assertRaises(ConnectionUnavailable):
            client.receipt("request-one")
        self.assertEqual(REQUEST_TIMEOUT_SECONDS, opener.open.call_args.kwargs["timeout"])

    def test_event_stream_uses_cursor_credential_and_silence_timeout(self) -> None:
        token_path = self.write_token()
        configuration = ConnectionConfiguration(
            service_url="http://localhost:8787",
            credential_file=token_path,
            config_file=self.maestro_config / "cli.toml",
        )

        class EventOpener:
            request = None
            timeout = None

            def open(self, request, *, timeout):
                self.request = request
                self.timeout = timeout
                return io.BytesIO(
                    b": heartbeat\n"
                    b"id: cursor-one\n"
                    b"event: project.changed\n"
                    b'data: {"project_id":"already-seen"}\n\n'
                    b"id: event-one\n"
                    b"event: project.changed\n"
                    b'data: {"project_id":"project-one"}\n\n'
                    b"id: event-one\n"
                    b"event: project.changed\n"
                    b'data: {"project_id":"duplicate"}\n\n'
                )

        opener = EventOpener()
        client = ServiceClient(configuration, opener=opener)

        events = list(client.events("cursor-one"))

        self.assertEqual(EVENT_SILENCE_TIMEOUT_SECONDS, opener.timeout)
        headers = dict(opener.request.header_items())
        self.assertEqual("cursor-one", headers["Last-event-id"])
        self.assertEqual(f"Bearer {OWNER_TOKEN}", headers["Authorization"])
        self.assertEqual(1, len(events))
        self.assertEqual("event-one", events[0].event_id)
        self.assertEqual("project.changed", events[0].event)
        self.assertEqual({"project_id": "project-one"}, events[0].data)

    def test_initial_failure_waits_but_established_disconnect_uses_bounded_backoff(self) -> None:
        self.write_token()
        self.write_config('service_url = "http://localhost:8787"\n')
        ScriptedClient.outcomes = [
            ConnectionUnavailable("initial unavailable"),
            {"data": []},
            ConnectionUnavailable("lost again"),
            ConnectionUnavailable("lost again"),
            ConnectionUnavailable("lost again"),
            ConnectionUnavailable("lost again"),
            ConnectionUnavailable("lost again"),
            ConnectionUnavailable("lost again"),
            ConnectionUnavailable("lost again"),
        ]
        connection = TerminalConnection(
            environ=self.environment, client_factory=ScriptedClient
        )

        with self.assertRaises(ConnectionUnavailable):
            connection.connect()
        self.assertEqual(ConnectionState.UNAVAILABLE, connection.status.state)
        with self.assertRaisesRegex(RuntimeError, "no automatic retry"):
            connection.automatic_retry()

        connection.retry_now()
        self.assertEqual(1, connection.disconnected("controlled loss"))
        observed = []
        for expected in RECONNECT_DELAYS_SECONDS[1:]:
            with self.assertRaises(ConnectionUnavailable):
                connection.automatic_retry()
            observed.append(connection.status.retry_in_seconds)
            self.assertEqual(expected, connection.status.retry_in_seconds)
        with self.assertRaises(ConnectionUnavailable):
            connection.automatic_retry()
        self.assertEqual(30, connection.status.retry_in_seconds)
        self.assertEqual([2, 4, 8, 16, 30], observed)

    def test_retry_rereads_changed_address_and_requires_context_clear_without_replay(self) -> None:
        self.write_token()
        self.write_config('service_url = "http://localhost:8787"\n')
        ScriptedClient.outcomes = [{"data": []}, {"data": []}]
        connection = TerminalConnection(
            environ=self.environment, client_factory=ScriptedClient
        )
        statuses = []
        connection.subscribe(statuses.append)
        connection.connect()

        self.write_config('service_url = "http://127.0.0.1:9999"\n')
        connection.retry_now()

        clear = [status for status in statuses if status.clear_service_context]
        self.assertEqual(1, len(clear))
        self.assertEqual("http://127.0.0.1:9999", clear[0].service_url)
        self.assertEqual(ConnectionState.CONNECTED, connection.status.state)

    def test_main_keeps_help_retry_and_exit_available_offline(self) -> None:
        self.write_token()
        self.write_config('service_url = "http://localhost:8787"\n')
        ScriptedClient.outcomes = [
            ConnectionUnavailable("controlled outage"),
            ConnectionUnavailable("controlled outage"),
        ]
        connection = TerminalConnection(
            environ=self.environment, client_factory=ScriptedClient
        )
        output = io.StringIO()
        application = TerminalApplication(
            connection,
            input_stream=io.StringIO("/help\n/retry\n/exit\n"),
            output_stream=output,
        )

        self.assertEqual(0, application.run())
        rendered = output.getvalue()
        self.assertIn("Maestro service: http://localhost:8787", rendered)
        self.assertIn("Authentication: Owner credential ready", rendered)
        self.assertIn("/help", rendered)
        self.assertIn("Retry failed; no previous command or answer was replayed", rendered)
        self.assertIn("service work continues", rendered)
        self.assertNotIn(OWNER_TOKEN, rendered)


if __name__ == "__main__":
    unittest.main()
