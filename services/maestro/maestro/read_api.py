"""Loopback-only read API: `/health`, `/snapshot/packets`, `/snapshot/attempts`,
`/snapshot/reviews`, and `/snapshot/events`."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping

from .config import RuntimeConfig, RuntimePathError
from .operational_state import (
    IdempotencyConflict,
    InvalidRecord,
    InvalidTransition,
    OperationalStateStore,
    ResourceBusy,
    StaleState,
)


_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})


class ReadApiBindError(ValueError):
    """Raised before any socket exists when a host is outside the loopback allowlist."""


@dataclass(frozen=True)
class ReadApiConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    runtime_dir: str | Path | None = None  # inert; RuntimeConfig's own default when None

    def __post_init__(self) -> None:
        if self.host not in _LOOPBACK_HOSTS:
            raise ReadApiBindError(f"Host is not in the loopback allowlist: {self.host}")


def canonical_response_json(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


_HEALTH_BODY = canonical_response_json({"status": "ready"})
_NOT_FOUND_BODY = canonical_response_json({"error": "not_found"})
_METHOD_NOT_ALLOWED_BODY = canonical_response_json({"error": "method_not_allowed"})
_INVALID_CONTENT_LENGTH_BODY = canonical_response_json({"error": "invalid_content_length"})
_INVALID_JSON_BODY = canonical_response_json({"error": "invalid_json"})
_PAYLOAD_TOO_LARGE_BODY = canonical_response_json({"error": "payload_too_large"})

# A guarded command's own JSON envelope is small (an idempotency key, an
# actor, and a handful of command-specific fields) — 1 MiB is generous
# headroom, not a real capacity limit. Rejecting an oversized
# Content-Length before ever calling `self.rfile.read()` is load-bearing:
# without this cap, a POST that honestly declares a huge Content-Length
# but never finishes sending that many bytes blocks the handling thread
# indefinitely (`BaseHTTPRequestHandler.timeout` is `None` by default, so
# the socket read has no timeout of its own).
_MAX_COMMAND_BODY_BYTES = 1_048_576

_VALID_SNAPSHOT_QUERY_KEYS = frozenset({"limit", "after"})
_LIMIT_LITERAL_RE = re.compile(r"^(0|[1-9][0-9]*)$")

_PACKETS_SNAPSHOT_COLUMNS = (
    "base_commit", "correction_count", "created_at", "current_head", "packet_id",
    "packet_revision", "run_id", "state", "updated_at", "version", "work_item_id",
)

_PACKETS_SNAPSHOT_QUERY = f"""
    SELECT {", ".join(_PACKETS_SNAPSHOT_COLUMNS)}
    FROM packets
    WHERE (? IS NULL OR packet_id > ?)
    ORDER BY packet_id ASC
    LIMIT ?+1
"""

_ATTEMPTS_SNAPSHOT_COLUMNS = (
    "attempt_id", "attempt_kind", "attempt_number", "completion_evidence_reference",
    "correction_for_review_id", "created_at", "execution_handle", "executor_class",
    "expected_result", "finished_at", "heartbeat_at", "lease_id", "model_identity",
    "packet_id", "result_commit", "runtime_identity", "started_at", "state",
    "updated_at", "version",
)

_ATTEMPTS_SNAPSHOT_QUERY = f"""
    SELECT {", ".join(_ATTEMPTS_SNAPSHOT_COLUMNS)}
    FROM attempts
    WHERE (? IS NULL OR attempt_id > ?)
    ORDER BY attempt_id ASC
    LIMIT ?+1
"""

_REVIEWS_SNAPSHOT_COLUMNS = (
    "attempt_id", "base_commit", "correction_number", "coverage_json", "created_at",
    "findings_json", "head_commit", "packet_id", "result", "review_id", "review_kind",
    "reviewer_instance", "reviewer_role",
)

_REVIEWS_SNAPSHOT_QUERY = f"""
    SELECT {", ".join(_REVIEWS_SNAPSHOT_COLUMNS)}
    FROM reviews
    WHERE (? IS NULL OR review_id > ?)
    ORDER BY review_id ASC
    LIMIT ?+1
"""


_EVENTS_SNAPSHOT_COLUMNS = (
    "actor_id", "actor_type", "after_json", "before_json", "causation_event_id",
    "command_fingerprint", "correlation_id", "created_at", "entity_id", "entity_type",
    "event_id", "event_type", "idempotency_key", "observed_at", "reason",
)

_EVENTS_SNAPSHOT_QUERY = f"""
    SELECT {", ".join(_EVENTS_SNAPSHOT_COLUMNS)}
    FROM events
    WHERE (? IS NULL OR event_id < ?)
    ORDER BY event_id DESC
    LIMIT ?+1
"""


def _validate_snapshot_query(parsed: dict[str, list[str]]) -> str | None:
    for key in parsed:
        if key not in _VALID_SNAPSHOT_QUERY_KEYS:
            return f"unknown query parameter: {key}"
    for key in ("limit", "after"):
        if key in parsed and len(parsed[key]) > 1:
            return f"query parameter appears more than once: {key}"
    if "limit" in parsed:
        raw_limit = parsed["limit"][0]
        if not _LIMIT_LITERAL_RE.match(raw_limit) or not (1 <= int(raw_limit) <= 500):
            return "limit must be an integer from 1 through 500"
    if "after" in parsed and parsed["after"][0] == "":
        return "after must not be empty"
    return None


def _handle_health(handler: "_ReadApiRequestHandler", query: str) -> None:
    handler._respond(200, _HEALTH_BODY)


def _handle_snapshot_packets(handler: "_ReadApiRequestHandler", query: str) -> None:
    parsed = urllib.parse.parse_qs(query, strict_parsing=False, keep_blank_values=True)
    error_detail = _validate_snapshot_query(parsed)
    if error_detail is not None:
        handler._respond(400, canonical_response_json({"error": "invalid_query", "detail": error_detail}))
        return

    limit = int(parsed["limit"][0]) if "limit" in parsed else 100
    after = parsed["after"][0] if "after" in parsed else None

    connection: sqlite3.Connection | None = None
    try:
        runtime_config = RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)
        connection = sqlite3.connect(
            f"file:{runtime_config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0,
        )
        rows = connection.execute(_PACKETS_SNAPSHOT_QUERY, (after, after, limit)).fetchall()
    except (RuntimePathError, sqlite3.Error):
        handler._respond(503, canonical_response_json({"error": "database_unavailable"}))
        return
    finally:
        if connection is not None:
            connection.close()

    next_after = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_after = rows[-1][_PACKETS_SNAPSHOT_COLUMNS.index("packet_id")]

    packets = [dict(zip(_PACKETS_SNAPSHOT_COLUMNS, row)) for row in rows]
    handler._respond(
        200, canonical_response_json({"next_after": next_after, "packets": packets}),
    )


def _handle_snapshot_attempts(handler: "_ReadApiRequestHandler", query: str) -> None:
    parsed = urllib.parse.parse_qs(query, strict_parsing=False, keep_blank_values=True)
    error_detail = _validate_snapshot_query(parsed)
    if error_detail is not None:
        handler._respond(400, canonical_response_json({"error": "invalid_query", "detail": error_detail}))
        return

    limit = int(parsed["limit"][0]) if "limit" in parsed else 100
    after = parsed["after"][0] if "after" in parsed else None

    connection: sqlite3.Connection | None = None
    try:
        runtime_config = RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)
        connection = sqlite3.connect(
            f"file:{runtime_config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0,
        )
        rows = connection.execute(_ATTEMPTS_SNAPSHOT_QUERY, (after, after, limit)).fetchall()
    except (RuntimePathError, sqlite3.Error):
        handler._respond(503, canonical_response_json({"error": "database_unavailable"}))
        return
    finally:
        if connection is not None:
            connection.close()

    next_after = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_after = rows[-1][_ATTEMPTS_SNAPSHOT_COLUMNS.index("attempt_id")]

    attempts = [dict(zip(_ATTEMPTS_SNAPSHOT_COLUMNS, row)) for row in rows]
    handler._respond(
        200, canonical_response_json({"attempts": attempts, "next_after": next_after}),
    )


def _handle_snapshot_reviews(handler: "_ReadApiRequestHandler", query: str) -> None:
    parsed = urllib.parse.parse_qs(query, strict_parsing=False, keep_blank_values=True)
    error_detail = _validate_snapshot_query(parsed)
    if error_detail is not None:
        handler._respond(400, canonical_response_json({"error": "invalid_query", "detail": error_detail}))
        return

    limit = int(parsed["limit"][0]) if "limit" in parsed else 100
    after = parsed["after"][0] if "after" in parsed else None

    connection: sqlite3.Connection | None = None
    try:
        runtime_config = RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)
        connection = sqlite3.connect(
            f"file:{runtime_config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0,
        )
        rows = connection.execute(_REVIEWS_SNAPSHOT_QUERY, (after, after, limit)).fetchall()
    except (RuntimePathError, sqlite3.Error):
        handler._respond(503, canonical_response_json({"error": "database_unavailable"}))
        return
    finally:
        if connection is not None:
            connection.close()

    next_after = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_after = rows[-1][_REVIEWS_SNAPSHOT_COLUMNS.index("review_id")]

    reviews = []
    for row in rows:
        review = dict(zip(_REVIEWS_SNAPSHOT_COLUMNS, row))
        review["coverage"] = json.loads(review.pop("coverage_json"))
        review["findings"] = json.loads(review.pop("findings_json"))
        reviews.append(review)
    handler._respond(
        200, canonical_response_json({"next_after": next_after, "reviews": reviews}),
    )


def _handle_snapshot_events(handler: "_ReadApiRequestHandler", query: str) -> None:
    parsed = urllib.parse.parse_qs(query, strict_parsing=False, keep_blank_values=True)
    error_detail = _validate_snapshot_query(parsed)
    if error_detail is not None:
        handler._respond(400, canonical_response_json({"error": "invalid_query", "detail": error_detail}))
        return
    if "after" in parsed and not _LIMIT_LITERAL_RE.match(parsed["after"][0]):
        handler._respond(
            400,
            canonical_response_json(
                {"error": "invalid_query", "detail": "after must be a non-negative integer"}
            ),
        )
        return

    limit = int(parsed["limit"][0]) if "limit" in parsed else 100
    after = int(parsed["after"][0]) if "after" in parsed else None

    connection: sqlite3.Connection | None = None
    try:
        runtime_config = RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)
        connection = sqlite3.connect(
            f"file:{runtime_config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0,
        )
        rows = connection.execute(_EVENTS_SNAPSHOT_QUERY, (after, after, limit)).fetchall()
    except (RuntimePathError, sqlite3.Error):
        handler._respond(503, canonical_response_json({"error": "database_unavailable"}))
        return
    finally:
        if connection is not None:
            connection.close()

    next_after = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_after = rows[-1][_EVENTS_SNAPSHOT_COLUMNS.index("event_id")]

    events = [dict(zip(_EVENTS_SNAPSHOT_COLUMNS, row)) for row in rows]
    handler._respond(
        200, canonical_response_json({"events": events, "next_after": next_after}),
    )


_ROUTES = {
    "/health": _handle_health,
    "/snapshot/packets": _handle_snapshot_packets,
    "/snapshot/attempts": _handle_snapshot_attempts,
    "/snapshot/reviews": _handle_snapshot_reviews,
    "/snapshot/events": _handle_snapshot_events,
}


def _validate_command_envelope(body: Any) -> str | None:
    if not isinstance(body, dict):
        return "request body must be a JSON object"
    idempotency_key = body.get("idempotency_key")
    if not isinstance(idempotency_key, str) or idempotency_key == "":
        return "idempotency_key is required and must be a non-empty string"
    actor = body.get("actor")
    if not isinstance(actor, dict):
        return "actor is required and must be a JSON object"
    return None


# The real, non-fictional resolution of an escalated packet decision. There
# is no real backend concept of a "frozen contract" or "sentinel version"
# anywhere in `operational_state.py` (checked directly — "sentinel" and
# "amend" do not appear at all; "frozen"/"contract" appear only in
# unrelated real spellings — `@dataclass(frozen=True)`,
# `input_contract_json`/`output_contract_json`/`role_contract_reference`
# work-item fields — none of which mean packet-decision freezing) — those
# are mockup narrative flavor text with no backend representation. This
# command instead reuses the real,
# already-tested `transition_packet_eligibility` and the real `Blocked`
# packet state (`_PACKET_ELIGIBILITY_TRANSITIONS["Blocked"] ==
# {"Waiting", "Ready", "Cancelled"}`) as the honest backend counterpart of
# "an escalated packet the owner must resolve" — no new persisted state or
# schema is introduced by this command. `target_state` is restricted to
# exactly those 3 real outcomes; the store's own real transition table
# remains the single source of truth for which source states may legally
# reach them (this command does not duplicate that check).
_RESOLVE_DECISION_TARGET_STATES = frozenset({"Cancelled", "Ready", "Waiting"})


def _validate_resolve_decision_command(envelope: dict[str, Any]) -> str | None:
    packet_id = envelope.get("packet_id")
    if not isinstance(packet_id, str) or packet_id == "":
        return "packet_id is required and must be a non-empty string"
    expected_version = envelope.get("expected_version")
    if (
        not isinstance(expected_version, int)
        or isinstance(expected_version, bool)
        or expected_version <= 0
    ):
        return "expected_version is required and must be a positive integer"
    target_state = envelope.get("target_state")
    if target_state not in _RESOLVE_DECISION_TARGET_STATES:
        return "target_state must be one of: Cancelled, Ready, Waiting"
    reason_payload = envelope.get("reason_payload")
    if not isinstance(reason_payload, dict):
        return "reason_payload is required and must be a JSON object"
    return None


def _handle_resolve_decision(handler: "_ReadApiRequestHandler", envelope: dict[str, Any]) -> None:
    error_detail = _validate_resolve_decision_command(envelope)
    if error_detail is not None:
        handler._respond(
            400, canonical_response_json({"error": "invalid_command", "detail": error_detail})
        )
        return

    store = OperationalStateStore(RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    try:
        result = store.transition_packet_eligibility(
            envelope["packet_id"],
            envelope["expected_version"],
            envelope["target_state"],
            envelope["reason_payload"],
            envelope["idempotency_key"],
            envelope["actor"],
            now,
        )
    except StaleState as error:
        handler._respond(409, canonical_response_json({"error": "stale_state", "detail": str(error)}))
        return
    except InvalidTransition as error:
        handler._respond(
            409, canonical_response_json({"error": "invalid_transition", "detail": str(error)})
        )
        return
    except IdempotencyConflict as error:
        handler._respond(
            409, canonical_response_json({"error": "idempotency_conflict", "detail": str(error)})
        )
        return
    except InvalidRecord as error:
        handler._respond(
            400, canonical_response_json({"error": "invalid_command", "detail": str(error)})
        )
        return
    except ResourceBusy as error:
        # Real, reachable path: `transition_packet_eligibility`'s own
        # internal `_raise_sqlite` (operational_state.py:2713-2717) raises
        # this when a competing writer holds the SQLite lock past the
        # store's real 5-second busy timeout (`storage.SQLITE_BUSY_TIMEOUT_MS`)
        # — already a real, tested outcome of this exact store
        # (`tests/m1_02/test_schema_and_records.py`'s
        # `test_held_writer_returns_resource_busy_on_health_reads_and_mutation`
        # exercises the identical `_raise_sqlite` path for other mutations).
        # A Decision Fidelity review of this slice's first draft found this
        # was left uncaught, which would have crashed the request thread
        # with no HTTP response under real write contention.
        handler._respond(503, canonical_response_json({"error": "resource_busy", "detail": str(error)}))
        return
    except sqlite3.OperationalError as error:
        # `_raise_sqlite` re-raises any `sqlite3.OperationalError` whose
        # message does not contain "locked" or "busy" completely unchanged
        # (see the same source cited above) — an operational-database
        # failure this command did not cause and cannot itself recover
        # from, mapped to the same `database_unavailable` convention the
        # existing GET snapshot routes already use for a broken database.
        handler._respond(
            503, canonical_response_json({"error": "database_unavailable", "detail": str(error)})
        )
        return

    handler._respond(200, canonical_response_json(result))


# Guarded, POST-only command routes. `envelope["idempotency_key"]`/
# `envelope["actor"]` are only checked by `_validate_command_envelope` for
# their outer shape (present, right JSON type) — the real closed-shape/field
# validation these values need (see `_actor()` in `operational_state.py`) is
# each real command's own job when it calls into `OperationalStateStore`,
# not this HTTP scaffold's; duplicating that validation here would let the
# two copies drift.
_COMMAND_ROUTES: dict[str, Callable[["_ReadApiRequestHandler", dict[str, Any]], None]] = {
    "/command/resolve-decision": _handle_resolve_decision,
}


class _ReadApiRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        return

    def do_GET(self) -> None:
        self._route("GET")

    def do_POST(self) -> None:
        self._route("POST")

    def do_PUT(self) -> None:
        self._route("PUT")

    def do_PATCH(self) -> None:
        self._route("PATCH")

    def do_DELETE(self) -> None:
        self._route("DELETE")

    def do_HEAD(self) -> None:
        self._route("HEAD")

    def do_OPTIONS(self) -> None:
        self._route("OPTIONS")

    def _route(self, method: str) -> None:
        split_path = urllib.parse.urlsplit(self.path)
        path = split_path.path
        if path in _COMMAND_ROUTES:
            if method != "POST":
                self._respond(405, _METHOD_NOT_ALLOWED_BODY)
                return
            self._dispatch_command(_COMMAND_ROUTES[path])
            return
        route_handler = _ROUTES.get(path)
        if route_handler is None:
            self._respond(404, _NOT_FOUND_BODY)
            return
        if method != "GET":
            self._respond(405, _METHOD_NOT_ALLOWED_BODY)
            return
        route_handler(self, split_path.query)

    def _dispatch_command(
        self, handler: Callable[["_ReadApiRequestHandler", dict[str, Any]], None]
    ) -> None:
        content_length_header = self.headers.get("Content-Length")
        try:
            content_length = int(content_length_header) if content_length_header is not None else 0
        except ValueError:
            content_length = -1
        if content_length < 0:
            self._respond(400, _INVALID_CONTENT_LENGTH_BODY)
            return
        if content_length > _MAX_COMMAND_BODY_BYTES:
            self._respond(413, _PAYLOAD_TOO_LARGE_BODY)
            return
        raw_body = self.rfile.read(content_length) if content_length > 0 else b""

        if raw_body == b"":
            body: Any = None
        else:
            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                self._respond(400, _INVALID_JSON_BODY)
                return

        error_detail = _validate_command_envelope(body)
        if error_detail is not None:
            self._respond(
                400, canonical_response_json({"error": "invalid_envelope", "detail": error_detail})
            )
            return

        handler(self, body)

    def _respond(self, status: int, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class _ReadApiHTTPServer(ThreadingHTTPServer):
    def __init__(self, address, handler_cls, runtime_dir_setting: str | Path | None) -> None:
        super().__init__(address, handler_cls)
        self.runtime_dir_setting = runtime_dir_setting


class ReadApiServer:
    def __init__(self, config: ReadApiConfig | None = None) -> None:
        self._config = config if config is not None else ReadApiConfig()
        self._httpd: _ReadApiHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def bound_port(self) -> int:
        if self._httpd is None:
            raise RuntimeError("ReadApiServer has not been started")
        return self._httpd.server_port

    def start(self) -> None:
        if self._httpd is not None:
            raise RuntimeError("ReadApiServer is already started")
        httpd = _ReadApiHTTPServer(
            (self._config.host, self._config.port), _ReadApiRequestHandler, self._config.runtime_dir,
        )
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        self._httpd = httpd
        self._thread = thread
        thread.start()

    def stop(self) -> None:
        if self._httpd is None:
            return
        httpd = self._httpd
        thread = self._thread
        httpd.shutdown()
        httpd.server_close()
        if thread is not None:
            thread.join(timeout=5.0)
        self._httpd = None
        self._thread = None

    def wait_forever(self) -> None:
        thread = self._thread
        if thread is not None:
            thread.join()

    def __enter__(self) -> "ReadApiServer":
        self.start()
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.stop()
