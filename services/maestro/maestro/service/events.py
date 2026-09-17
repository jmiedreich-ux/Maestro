"""Authenticated delivery of committed outbox events over SSE.

The durable cursor is the foundation outbox sequence.  Projection readers take
that cursor in the same SQLite snapshot as their data, so a subscriber can
request every committed event after the snapshot without a race.  Heartbeats
are transport comments only and never cross the database write boundary.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import MappingProxyType
from urllib.parse import urlsplit

from maestro.foundation import Database, DatabaseError, StorageConfigurationError

from .authentication import HTTPRejection, OwnerAuthenticator


HEARTBEAT_SECONDS = 15
REPLAY_BATCH_SIZE = 100
POLL_INTERVAL_SECONDS = 0.25
_MAX_SQLITE_INTEGER = 9_223_372_036_854_775_807


class EventStreamRejection(HTTPRejection):
    """A safe error returned before an event stream is established."""


@dataclass(frozen=True)
class CommittedEvent:
    """One committed outbox event and its durable stream position."""

    cursor: int
    schema_version: int
    event_id: str
    occurred_at: str
    project_id: str | None
    activity_id: str | None
    type: str
    data: Mapping[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "project_id": self.project_id,
            "activity_id": self.activity_id,
            "type": self.type,
            "data": dict(self.data),
        }

    def as_sse(self) -> bytes:
        payload = json.dumps(
            self.as_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return (
            f"id: {self.cursor}\n"
            f"event: {self.type}\n"
            f"data: {payload}\n\n"
        ).encode("utf-8")


class EventSubscription:
    """A single monotonically advancing view of the committed outbox."""

    def __init__(
        self,
        database: Database,
        cursor: int,
        *,
        monotonic: Callable[[], float],
        waiter: Callable[[float], None],
        poll_interval_seconds: float,
    ) -> None:
        self._database = database
        self._cursor = cursor
        self._monotonic = monotonic
        self._waiter = waiter
        self._poll_interval_seconds = poll_interval_seconds

    @property
    def cursor(self) -> int:
        return self._cursor

    def next_batch(self) -> tuple[CommittedEvent, ...]:
        """Return at most one bounded page visible after the last cursor."""
        try:
            with self._database.read_connection() as connection:
                rows = connection.execute(
                    """
                    SELECT sequence, schema_version, event_id, occurred_at,
                           project_id, activity_id, type, data_json
                    FROM outbox_events
                    WHERE sequence > ?
                    ORDER BY sequence
                    LIMIT ?
                    """,
                    (self._cursor, REPLAY_BATCH_SIZE),
                ).fetchall()
        except (
            DatabaseError,
            StorageConfigurationError,
            sqlite3.DatabaseError,
        ) as error:
            raise EventStreamRejection(
                503,
                "service_unavailable",
                "the committed event store is unavailable",
            ) from error

        events = tuple(_committed_event(row) for row in rows)
        if events:
            self._cursor = events[-1].cursor
        return events

    def frames(
        self, *, stopped: Callable[[], bool] = lambda: False
    ) -> Iterator[bytes]:
        """Yield replay, future committed events, and 15-second heartbeats."""
        heartbeat_at = self._monotonic() + HEARTBEAT_SECONDS
        while not stopped():
            events = self.next_batch()
            if events:
                for event in events:
                    yield event.as_sse()
                heartbeat_at = self._monotonic() + HEARTBEAT_SECONDS
                continue

            now = self._monotonic()
            if now >= heartbeat_at:
                yield b": heartbeat\n\n"
                heartbeat_at = self._monotonic() + HEARTBEAT_SECONDS
                continue
            self._waiter(min(self._poll_interval_seconds, heartbeat_at - now))


class EventStreamService:
    """Authenticate callers and establish a cursor-checked subscription."""

    def __init__(
        self,
        database: Database,
        authenticator: OwnerAuthenticator,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        waiter: Callable[[float], None] = time.sleep,
        poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
    ) -> None:
        if not isinstance(database, Database):
            raise TypeError("event stream requires the service Database")
        if not isinstance(authenticator, OwnerAuthenticator):
            raise TypeError("event stream requires the Owner authenticator")
        if (
            isinstance(poll_interval_seconds, bool)
            or not isinstance(poll_interval_seconds, (int, float))
            or not 0 < poll_interval_seconds <= HEARTBEAT_SECONDS
        ):
            raise ValueError("poll interval must be positive and at most 15 seconds")
        self._database = database
        self._authenticator = authenticator
        self._monotonic = monotonic
        self._waiter = waiter
        self._poll_interval_seconds = float(poll_interval_seconds)
        self._database.initialize()

    def subscribe(
        self,
        authorization: str | None,
        last_event_id: str | None,
    ) -> EventSubscription:
        """Return a stream after authenticating and validating its cursor.

        An omitted cursor starts at the current committed position.  Connected
        clients normally supply the cursor from their preceding snapshot; on
        reconnect they supply the most recently received SSE ID.
        """
        self._authenticator.authenticate_read(authorization)
        requested = None if last_event_id is None else _parse_cursor(last_event_id)
        cursor = self._available_cursor(requested)
        return EventSubscription(
            self._database,
            cursor,
            monotonic=self._monotonic,
            waiter=self._waiter,
            poll_interval_seconds=self._poll_interval_seconds,
        )

    def _available_cursor(self, requested: int | None) -> int:
        try:
            with self._database.read_connection() as connection:
                row = connection.execute(
                    "SELECT MIN(sequence), MAX(sequence) FROM outbox_events"
                ).fetchone()
        except (
            DatabaseError,
            StorageConfigurationError,
            sqlite3.DatabaseError,
        ) as error:
            raise EventStreamRejection(
                503,
                "service_unavailable",
                "the committed event store is unavailable",
            ) from error

        minimum = None if row[0] is None else int(row[0])
        maximum = 0 if row[1] is None else int(row[1])
        if requested is None:
            return maximum
        oldest_boundary = 0 if minimum is None else minimum - 1
        if oldest_boundary <= requested <= maximum:
            return requested
        raise EventStreamRejection(
            409,
            "event_cursor_unavailable",
            "the event cursor is unavailable; load a fresh snapshot",
        )


@dataclass(frozen=True)
class EventHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: Mapping[str, object] | Iterator[bytes]


class EventStreamHTTPApplication:
    """Transport-neutral authenticated ``GET /api/v1/events`` adapter."""

    def __init__(self, service: EventStreamService) -> None:
        if not isinstance(service, EventStreamService):
            raise TypeError("event HTTP application requires EventStreamService")
        self._service = service
        self._stop_event = threading.Event()

    def start(self) -> None:
        self._stop_event.clear()

    def stop(self) -> None:
        self._stop_event.set()

    def handle(
        self,
        method: str,
        path: str,
        headers: Mapping[str, str],
    ) -> EventHTTPResponse:
        try:
            parsed = urlsplit(path)
            if (
                method != "GET"
                or parsed.path != "/api/v1/events"
                or parsed.query
                or parsed.fragment
            ):
                raise EventStreamRejection(
                    404, "not_found", "the API route was not found"
                )
            subscription = self._service.subscribe(
                headers.get("Authorization"), headers.get("Last-Event-ID")
            )
            return EventHTTPResponse(
                200,
                MappingProxyType(
                    {
                        "Content-Type": "text/event-stream; charset=utf-8",
                        "Cache-Control": "no-cache",
                        "Connection": "close",
                    }
                ),
                subscription.frames(stopped=self._stop_event.is_set),
            )
        except HTTPRejection as error:
            response_headers = {"Content-Type": "application/json; charset=utf-8"}
            response_headers.update(error.headers)
            return EventHTTPResponse(
                error.status_code,
                MappingProxyType(response_headers),
                error.as_body(),
            )


class EventStreamHTTPServer:
    """A stoppable loopback server demonstrating the real SSE provider path."""

    def __init__(
        self,
        application: EventStreamHTTPApplication,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        if not isinstance(application, EventStreamHTTPApplication):
            raise TypeError("event HTTP server requires EventStreamHTTPApplication")
        self._application = application
        self._server = ThreadingHTTPServer((host, port), _handler(application))
        self._server.daemon_threads = False
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> tuple[str, int]:
        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def start(self) -> None:
        if self._thread is not None:
            raise RuntimeError("event HTTP server is already running")
        self._application.start()
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._application.stop()
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join()
            self._thread = None


def _parse_cursor(value: str) -> int:
    if (
        not isinstance(value, str)
        or not value
        or (value != "0" and (value.startswith("0") or not value.isascii()))
        or not value.isdecimal()
    ):
        raise EventStreamRejection(
            400, "invalid_event_cursor", "Last-Event-ID must be a durable event cursor"
        )
    cursor = int(value)
    if cursor > _MAX_SQLITE_INTEGER:
        raise EventStreamRejection(
            409,
            "event_cursor_unavailable",
            "the event cursor is unavailable; load a fresh snapshot",
        )
    return cursor


def _committed_event(row: tuple[object, ...]) -> CommittedEvent:
    try:
        data = json.loads(str(row[7]))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise EventStreamRejection(
            503,
            "service_unavailable",
            "a committed event cannot be read",
        ) from error
    if not isinstance(data, dict):
        raise EventStreamRejection(
            503,
            "service_unavailable",
            "a committed event cannot be read",
        )
    return CommittedEvent(
        cursor=int(row[0]),
        schema_version=int(row[1]),
        event_id=str(row[2]),
        occurred_at=str(row[3]),
        project_id=None if row[4] is None else str(row[4]),
        activity_id=None if row[5] is None else str(row[5]),
        type=str(row[6]),
        data=MappingProxyType(data),
    )


def _handler(application: EventStreamHTTPApplication):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            response = application.handle("GET", self.path, self.headers)
            self.send_response(response.status_code)
            for name, value in response.headers.items():
                self.send_header(name, value)
            if isinstance(response.body, Mapping):
                encoded = json.dumps(
                    response.body,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ).encode("utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)
                return

            self.end_headers()
            try:
                for frame in response.body:
                    self.wfile.write(frame)
                    self.wfile.flush()
            except (
                BrokenPipeError,
                ConnectionResetError,
                EventStreamRejection,
                OSError,
            ):
                return
            finally:
                close = getattr(response.body, "close", None)
                if close is not None:
                    close()

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return Handler
