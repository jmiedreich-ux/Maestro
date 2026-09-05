"""Loopback-only read API: `/health` and the `/snapshot/packets` projection."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import urllib.parse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

from .config import RuntimeConfig, RuntimePathError


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


_ROUTES = {
    "/health": _handle_health,
    "/snapshot/packets": _handle_snapshot_packets,
    "/snapshot/attempts": _handle_snapshot_attempts,
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
        route_handler = _ROUTES.get(split_path.path)
        if route_handler is None:
            self._respond(404, _NOT_FOUND_BODY)
            return
        if method != "GET":
            self._respond(405, _METHOD_NOT_ALLOWED_BODY)
            return
        route_handler(self, split_path.query)

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
