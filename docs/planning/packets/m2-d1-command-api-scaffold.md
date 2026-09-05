# M2 Wave D — Guarded Command API Scaffold — Candidate 01

**Slice ID:** `MB-SLICE-M2-D1-COMMAND-API-SCAFFOLD-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `ccfdb3a` (full: `ccfdb3a559cb6c45448040d075b0546145e6f775`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 19, *"D1 — Guarded command API scaffold. POST endpoint
shape, idempotency-key handling, actor/causation envelope — no real
command registered yet."* The first Wave D slice, and **the first
backend (Python) slice this session** — every prior M2 slice this
session was Atlas frontend (TypeScript/React) work. This slice adds a
generic, guarded POST-command dispatch mechanism to the existing
loopback-only HTTP server in `services/maestro/maestro/read_api.py`
(Wave A, already merged), with:

- a new, empty command-route registry (`_COMMAND_ROUTES`) — genuinely
  no real command is registered in production code by this slice, per
  the roadmap item's own wording, verified by a dedicated test
  (`test_11_no_real_command_is_registered_in_production_code`);
- real POST request-body reading (`Content-Length` + `self.rfile.read`)
  — the existing file has **no body-reading code at all** for any verb
  today (checked directly: zero references to `self.rfile` or
  `self.headers` anywhere in the pre-existing file);
- envelope shape validation (`idempotency_key` present and a non-empty
  string; `actor` present and a JSON object) — deliberately a *shape*
  check only, not the same as the real M1 `_actor()` closed-shape/field
  validation (see "Design rationale" below for why).

D2 (a future slice) will register the first real command — an
"owner resolves a decision" command backed by a new
`OperationalStateStore` method — into `_COMMAND_ROUTES`. This slice
adds no such method and calls no `OperationalStateStore` method at all.

## Evidence: the real M1 envelope this scaffold is designed to feed

The idempotency-key/actor/causation envelope this scaffold's
`_COMMAND_ROUTES` handlers will eventually pass into a real
`OperationalStateStore` command already exists and is already
real, reviewed M1 code — this slice does not invent it, quoted here
verbatim with exact line numbers, independently re-verified against
`services/maestro/maestro/operational_state.py` on this branch's own
base commit (not assumed from memory):

```python
# operational_state.py:125-130
@dataclass(frozen=True)
class Actor:
    actor_type: str
    actor_id: str
    correlation_id: str
    causation_event_id: int | None = None
```

```python
# operational_state.py:3133-3148 — the real actor normalizer/validator
def _actor(value: Actor | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Actor):
        raw = asdict(value)
    else:
        if not isinstance(value, Mapping) or set(value) not in (
            {"actor_type", "actor_id", "correlation_id"},
            {"actor_type", "actor_id", "correlation_id", "causation_event_id"},
        ):
            raise InvalidRecord("actor has an invalid closed shape")
        raw = dict(value)
        raw.setdefault("causation_event_id", None)
    for field in ("actor_type", "actor_id", "correlation_id"):
        raw[field] = _text(raw[field], field)
    if raw["causation_event_id"] is not None:
        raw["causation_event_id"] = _positive_int(raw["causation_event_id"], "causation_event_id")
    return raw
```

```python
# operational_state.py:2516-2525 — the real idempotency-replay check
@staticmethod
def _replay(connection: sqlite3.Connection, key: str, fingerprint: str):
    row = connection.execute(
        "SELECT command_fingerprint,after_json FROM events WHERE idempotency_key=?", (key,)
    ).fetchone()
    if row is None:
        return None
    if row[0] != fingerprint:
        raise IdempotencyConflict("idempotency key was already used for different command facts")
    return json.loads(str(row[1]))
```

```python
# operational_state.py:598-601 — one real example command's real signature
def claim_packet_assignment(
    self, packet_id, expected_version, lease_request, lock_requests,
    attempt_request, reason_payload, idempotency_key, actor, now,
):
```

Every existing internal M1 command already takes `(idempotency_key,
actor, now, ...)`; this envelope is not invented by this slice, only
plumbed through an HTTP body for the first time.

## The real, pre-existing HTTP layer this slice extends

`services/maestro/maestro/read_api.py` (Wave A, merged) already wires
every HTTP verb to a shared `_route` dispatcher, but rejects every
non-`GET` verb unconditionally, before ever touching the request body:

```python
# read_api.py:317-326, before this slice
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
```

Checked directly and confirmed: no existing code in this file reads
`self.rfile` (a request body) or `self.headers` (a request header) for
any verb, on any route, anywhere. The server class hierarchy
(`_ReadApiRequestHandler(BaseHTTPRequestHandler)`,
`_ReadApiHTTPServer(ThreadingHTTPServer)`, the `ReadApiServer` wrapper)
and the existing `_respond()` response-writing helper are unchanged by
this slice and reused exactly as-is.

## Design rationale (decisions made under delegated Project Architect authority)

1. **A new, separate `_COMMAND_ROUTES` dict, not an extension of the
   existing GET-only `_ROUTES` dict.** This keeps the diff to the
   existing, already-merged `_ROUTES`/GET-handler code at zero lines
   changed — every one of Wave A's 49 existing tests passes unmodified
   (re-run and confirmed, see Pre-verification). `_route()` gains one
   new branch, checked first, that only activates for a path actually
   registered in `_COMMAND_ROUTES`.
2. **`_COMMAND_ROUTES` starts empty in production code.** The roadmap
   item says "no real command registered yet" — this is genuinely true
   of the shipped code, not just prose; tests exercise the scaffold by
   temporarily registering a fake handler via
   `unittest.mock.patch.dict`, the same dependency-injection idiom
   `unittest.mock` already provides, rather than baking a placeholder
   "example" command into the module that could be mistaken for real
   content.
3. **The scaffold validates only the envelope's outer *shape*
   (`idempotency_key` is a non-empty string; `actor` is a JSON object)
   — not the same full closed-shape/field validation `_actor()`
   performs.** The real `_actor()` (quoted above) is called by every
   real command from inside `OperationalStateStore`, on the actual
   dict a real command receives. Duplicating that same closed-shape
   check here, in the generic HTTP scaffold, before any real command
   exists, would create two independent copies of the same validation
   rule that could silently drift apart as either one changes. The
   store stays the single source of truth for what an `actor` value
   must contain; this scaffold's job is only to safely extract a
   same-shaped JSON value from an HTTP body and hand it to whichever
   real command gets registered.
4. **Command routes are placed at a new URL prefix, `/command/...`**,
   parallel to the existing `/snapshot/...` read routes, with no
   real path chosen yet (this slice registers zero real paths).
5. **`now` is not part of this slice.** A real command (D2+) will
   supply `now` itself when it calls into `OperationalStateStore` —
   there is nothing for the generic scaffold to do with a timestamp
   before any real command exists to receive one.

## Guards

1. This slice modifies exactly one already-merged file
   (`services/maestro/maestro/read_api.py`) and adds exactly one new
   test file (`tests/m2_wave_d/test_command_api_scaffold.py`) — no
   other file touched, no real command registered, no
   `OperationalStateStore` method added or called.
2. Zero existing tests were modified; all 49 of Wave A's own
   `tests/m2_wave_a` tests were re-run unmodified and confirmed still
   passing (see Pre-verification) — proof this slice's one new
   `_route()` branch changes nothing observable about the 5 existing
   GET routes.
3. `services/maestro/maestro/__pycache__/*.pyc` — several of which are
   tracked in this repository — must never be modified or deleted by
   this slice's own verification process; any incidental changes from
   running the toolchain locally were reverted before finalizing this
   packet (`git checkout --` on the 3 tracked `.pyc` files that were
   incidentally touched, plus removing the one new untracked
   `read_api.cpython-312.pyc`).
4. A pre-existing, wholly unrelated test failure exists on this
   slice's own base commit, before any change in this packet:
   `tests/m1_01/test_project_manifest.py`'s
   `test_imported_pyyaml_version_satisfies_packet_range` fails because
   the local environment's installed PyYAML (6.0.1) does not satisfy
   the packet's required range (`>=6.0.2,<7`) — an environment/dependency
   version mismatch, unrelated to this slice's own code, `read_api.py`,
   or anything in `tests/m2_wave_d`. Confirmed present identically
   before and after this slice's change (same single failure, same
   message, in both runs). Not fixed by this slice — out of scope, a
   local environment condition, not a code defect this slice's diff
   could cause or is responsible for.
5. Real closed-shape/field validation of `actor` (e.g. rejecting an
   `actor` object with unexpected extra keys, or a
   non-positive-integer `causation_event_id`) is explicitly excluded
   from this slice — see Design rationale item 3. A future real
   command (D2+) performs that validation via the real, already-tested
   `_actor()`.

## `services/maestro/maestro/read_api.py` (modified — full new content)

```python
"""Loopback-only read API: `/health`, `/snapshot/packets`, `/snapshot/attempts`,
`/snapshot/reviews`, and `/snapshot/events`."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import urllib.parse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping

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
_INVALID_CONTENT_LENGTH_BODY = canonical_response_json({"error": "invalid_content_length"})
_INVALID_JSON_BODY = canonical_response_json({"error": "invalid_json"})

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


# Guarded, POST-only command routes. Deliberately empty in this slice — no
# real command is registered yet (Wave D's D2 onward each add exactly one
# real entry here). A handler has the signature `(handler, envelope) -> None`,
# the same shape as a `_ROUTES` handler except it receives the request's
# already-parsed, already-shape-checked JSON body (a `dict`) instead of a
# raw query string. `envelope["idempotency_key"]`/`envelope["actor"]` are
# only checked here for their outer shape (present, right JSON type) — the
# real closed-shape/field validation these values need (see `_actor()` in
# `operational_state.py`) is the eventual real command's own job when it
# calls into `OperationalStateStore`, not this HTTP scaffold's; duplicating
# that validation here would let the two copies drift.
_COMMAND_ROUTES: dict[str, Callable[["_ReadApiRequestHandler", dict[str, Any]], None]] = {}


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
```

## `tests/m2_wave_d/test_command_api_scaffold.py` (new)

```python
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

    def test_11_no_real_command_is_registered_in_production_code(self) -> None:
        self.assertEqual(read_api._COMMAND_ROUTES, {})


if __name__ == "__main__":
    unittest.main()
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree and run through the real Python toolchain from
`services/maestro` (`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1`), before
this docs-only packet was finalized (scratch changes then reverted;
3 tracked `.pyc` files that were incidentally touched by running the
suite were restored with `git checkout --`, and the 1 new untracked
`.pyc` was deleted):

- `python -m unittest discover -s ../../tests/m2_wave_d -v` — **11/11
  passed**, first attempt, no self-caught bugs.
- `python -m unittest discover -s ../../tests/m2_wave_a -v` — **49/49
  passed**, unmodified — zero regression in the existing Wave A read
  API tests.
- Every other pre-existing test directory re-run for a full baseline:
  `alpha_01` (11 passed), `alpha_02` (7 passed), `alpha_03` (56
  passed), `m1_01` (27 tests, **1 pre-existing failure**, unrelated —
  see Guards item 4), `m1_02` (162 passed), `review_readiness` (27
  passed).
- `python -m compileall -q maestro ../../tests/m2_wave_d` — clean,
  exit 0.

**Total: 350 tests across all 8 directories (339 pre-slice baseline +
11 new), with the same 1 pre-existing, unrelated `m1_01` failure
present identically before and after this slice's change** — this
slice introduces zero new failures and fixes none of the pre-existing
one (out of scope).

## M0-D12 bounded quality contract

1. **Protected outcome:** the read API server can accept a POST
   request to a registered command path, safely parse and
   shape-validate its JSON body's `idempotency_key`/`actor` envelope,
   and hand the parsed body to a registered handler — with genuinely
   zero real commands registered in shipped code, and zero change to
   any of the 5 existing GET routes' behavior.
2. **Operating and threat model:** a trusted local dev box, loopback
   only (unchanged from Wave A — `ReadApiConfig.__post_init__`'s
   loopback allowlist enforcement is untouched by this slice). This
   slice adds request-body parsing for the first time; a malformed or
   oversized body is handled by existing, battle-tested stdlib
   (`json.loads`, `int()`) wrapped in explicit `try`/`except`, with no
   new file I/O, subprocess, or network call introduced.
3. **Explicit exclusions:** any real command (D2 onward), any
   `OperationalStateStore` call, real closed-shape/field validation of
   `actor` (deferred to the real command that will eventually receive
   it), a real idempotency-replay check (inherently the receiving
   command's own responsibility once one exists — there is nothing to
   replay against without a real command), any URL path beyond the
   `/command/...` prefix convention this slice merely establishes.
4. **Assurance level:** practical correctness for a generic HTTP
   dispatch scaffold — envelope-shape validation, body-size handling,
   and dispatch are all directly exercised by real HTTP requests over
   real sockets against a real running server (matching this
   codebase's own established `http.client.HTTPConnection`-based test
   convention), not mocked at the socket layer.
5. **Acceptance proof:** the 11 named tests, the existing 339
   pre-slice tests continuing to pass (with the one pre-existing,
   unrelated `m1_01` failure unchanged), `python -m compileall`
   passing — observed total 350 tests across 8 directories.
6. **Implementation boundary:** exactly one modified file
   (`read_api.py`) and one new test file; no new third-party
   dependency; no new module.
7. **Proportionality ceiling:** one dispatch branch, one envelope
   validator, one empty registry dict — no real command, no wiring to
   `OperationalStateStore`, no Atlas frontend change.
8. **Stop and escalation rule:** registering any real command into
   `_COMMAND_ROUTES`, or calling any `OperationalStateStore` method,
   is explicitly out of scope — D2's job, not this slice's to
   silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-D1-COMMAND-API-SCAFFOLD-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:ccfdb3a559cb6c45448040d075b0546145e6f775"]` |
