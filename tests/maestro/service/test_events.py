from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path

from maestro.foundation import Database, StorageSettings
from maestro.service.activities import (
    ActivityRecord,
    ActivityRepository,
    ProjectRecord,
)
from maestro.service.authentication import (
    OwnerAuthenticationSettings,
    OwnerAuthenticator,
    token_digest,
)
from maestro.service.events import (
    HEARTBEAT_SECONDS,
    REPLAY_BATCH_SIZE,
    EventStreamHTTPApplication,
    EventStreamHTTPServer,
    EventStreamRejection,
    EventStreamService,
)
from maestro.service.projections import ProjectionReader
from maestro.service.registry import (
    OperationHandler,
    OperationRegistry,
    OperationResult,
    PreparedOperation,
)
from maestro.service.requests import RequestService
from maestro.terminal.connection import (
    ConnectionConfiguration,
    ServiceClient,
    ServiceError,
)


OWNER_TOKEN = "a" * 64
AUTHORIZATION = f"Bearer {OWNER_TOKEN}"


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def wait(self, seconds: float) -> None:
        self.now += seconds


class EventStreamTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.database = Database(
            StorageSettings(path=self.root / "maestro.sqlite3")
        )
        self.records = ActivityRepository(self.database)
        self.reader = ProjectionReader(self.database)
        self.authenticator = OwnerAuthenticator(
            OwnerAuthenticationSettings(
                owner_id="owner-local", token_sha256=token_digest(OWNER_TOKEN)
            )
        )
        self.requests = RequestService(
            self.database,
            self.authenticator,
            OperationRegistry(
                (OperationHandler("registration.start", self._create_project),)
            ),
        )
        self.stream = EventStreamService(self.database, self.authenticator)

    def _create_project(self, request) -> PreparedOperation:
        project_id = str(request.payload["project_id"])
        activity_id = str(request.payload["activity_id"])

        def apply(transaction, next_version: int) -> OperationResult:
            self.records.create_records(
                transaction,
                project=ProjectRecord(
                    project_id,
                    project_id.replace("-", " ").title(),
                    "registering",
                    next_version,
                ),
                activity=ActivityRecord(
                    activity_id,
                    project_id,
                    "registration",
                    f"Register {project_id}",
                    "working",
                    next_version,
                ),
            )
            return OperationResult(
                data={"project_id": project_id, "activity_id": activity_id},
                project_id=project_id,
                activity_id=activity_id,
            )

        return PreparedOperation(
            entity_id=project_id,
            event_type="project.created",
            event_data={"project_id": project_id, "activity_id": activity_id},
            apply=apply,
        )

    @staticmethod
    def envelope(number: int) -> dict[str, object]:
        return {
            "request_id": f"request-{number}",
            "operation": "registration.start",
            "project_id": None,
            "activity_id": None,
            "question_id": None,
            "expected_version": None,
            "payload": {
                "project_id": f"project-{number}",
                "activity_id": f"activity-{number}",
            },
        }

    def _client(self, token: str = OWNER_TOKEN, *, opener=None) -> ServiceClient:
        token_path = self.root / f"owner-{token[0]}.token"
        token_path.write_text(token, encoding="ascii")
        token_path.chmod(0o600)
        configuration = ConnectionConfiguration(
            service_url=self.base_url,
            credential_file=token_path,
            config_file=self.root / "cli.toml",
        )
        return ServiceClient(configuration, opener=opener)

    def _start_server(self) -> None:
        server = EventStreamHTTPServer(EventStreamHTTPApplication(self.stream))
        server.start()
        self.addCleanup(server.close)
        host, port = server.address
        self.base_url = f"http://{host}:{port}"

    def test_snapshot_intervening_commit_and_reconnect_use_real_client_path(
        self,
    ) -> None:
        snapshot = self.reader.workspace()
        self.requests.submit(AUTHORIZATION, self.envelope(1))
        self._start_server()
        client = self._client()

        first_stream = client.events(str(snapshot.event_cursor))
        first = next(first_stream)
        first_stream.close()

        self.assertEqual("1", first.event_id)
        self.assertEqual("project.created", first.event)
        self.assertEqual("project-1", first.data["project_id"])
        self.assertEqual("activity-1", first.data["activity_id"])
        self.assertEqual("request-", first.data["event_id"][:8])
        self.assertEqual(1, first.data["schema_version"])

        self.requests.submit(AUTHORIZATION, self.envelope(2))
        reconnected = client.events(first.event_id)
        second = next(reconnected)
        reconnected.close()

        self.assertEqual("2", second.event_id)
        self.assertEqual("project-2", second.data["project_id"])
        self.assertEqual("project-2", second.data["data"]["project_id"])

    def test_uncommitted_event_is_invisible_and_replay_is_bounded(self) -> None:
        subscription = self.stream.subscribe(AUTHORIZATION, "0")
        with self.database.transaction() as transaction:
            transaction.execute(
                """
                INSERT INTO outbox_events(
                    schema_version, event_id, occurred_at, project_id,
                    activity_id, type, data_json
                ) VALUES (1, ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    "event-uncommitted",
                    "2026-09-17T12:00:00.000000Z",
                    "service.changed",
                    "{}",
                ),
            )
            self.assertEqual((), subscription.next_batch())

        committed = subscription.next_batch()
        self.assertEqual(["event-uncommitted"], [event.event_id for event in committed])

        with self.database.transaction() as transaction:
            transaction.executemany(
                """
                INSERT INTO outbox_events(
                    schema_version, event_id, occurred_at, project_id,
                    activity_id, type, data_json
                ) VALUES (1, ?, ?, NULL, NULL, ?, ?)
                """,
                tuple(
                    (
                        f"event-{number}",
                        "2026-09-17T12:00:00.000000Z",
                        "service.changed",
                        json.dumps({"number": number}),
                    )
                    for number in range(REPLAY_BATCH_SIZE + 1)
                ),
            )

        self.assertEqual(REPLAY_BATCH_SIZE, len(subscription.next_batch()))
        final_page = subscription.next_batch()
        self.assertEqual(1, len(final_page))
        self.assertEqual(REPLAY_BATCH_SIZE, final_page[0].data["number"])

    def test_heartbeat_is_fifteen_second_transport_only_comment(self) -> None:
        clock = FakeClock()
        stream = EventStreamService(
            self.database,
            self.authenticator,
            monotonic=clock.monotonic,
            waiter=clock.wait,
            poll_interval_seconds=HEARTBEAT_SECONDS,
        )
        subscription = stream.subscribe(AUTHORIZATION, "0")
        with self.database.read_connection() as connection:
            before = connection.execute(
                "SELECT COUNT(*) FROM outbox_events"
            ).fetchone()[0]

        frames = subscription.frames()
        heartbeat = next(frames)
        frames.close()

        self.assertEqual(b": heartbeat\n\n", heartbeat)
        self.assertEqual(HEARTBEAT_SECONDS, clock.now)
        with self.database.read_connection() as connection:
            after = connection.execute(
                "SELECT COUNT(*) FROM outbox_events"
            ).fetchone()[0]
        self.assertEqual(before, after)

    def test_unavailable_cursor_requests_snapshot_and_stream_requires_owner(
        self,
    ) -> None:
        for number in range(1, 4):
            self.requests.submit(AUTHORIZATION, self.envelope(number))
        with self.database.transaction() as transaction:
            transaction.execute("DELETE FROM outbox_events WHERE sequence < 3")
        self._start_server()

        with self.assertRaises(ServiceError) as unavailable:
            self._client().events("0")
        self.assertEqual(409, unavailable.exception.status_code)
        self.assertEqual("event_cursor_unavailable", unavailable.exception.code)
        self.assertIn("fresh snapshot", str(unavailable.exception))

        with self.assertRaises(ServiceError) as unauthorized:
            self._client("b" * 64).events("2")
        self.assertEqual(401, unauthorized.exception.status_code)
        self.assertEqual("unauthorized", unauthorized.exception.code)

        with self.assertRaises(EventStreamRejection) as invalid:
            self.stream.subscribe(AUTHORIZATION, "01")
        self.assertEqual(400, invalid.exception.status_code)
        self.assertEqual("invalid_event_cursor", invalid.exception.code)

    def test_terminal_consumer_ignores_repeated_cursor_ids(self) -> None:
        class DuplicateOpener:
            def open(self, _request, *, timeout):
                self.timeout = timeout
                return io.BytesIO(
                    b"id: 8\n"
                    b"event: project.changed\n"
                    b'data: {"project_id":"project-one"}\n\n'
                    b"id: 8\n"
                    b"event: project.changed\n"
                    b'data: {"project_id":"duplicate"}\n\n'
                )

        self.base_url = "http://localhost:8787"
        events = list(self._client(opener=DuplicateOpener()).events("7"))

        self.assertEqual(1, len(events))
        self.assertEqual("8", events[0].event_id)
        self.assertEqual("project-one", events[0].data["project_id"])


if __name__ == "__main__":
    unittest.main()
