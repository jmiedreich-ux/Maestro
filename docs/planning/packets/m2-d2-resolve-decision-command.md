# M2 Wave D — Command: Owner Resolves a Decision — Candidate 01

**Slice ID:** `MB-SLICE-M2-D2-RESOLVE-DECISION-COMMAND-01`
**Status:** `Draft, pending Decision Fidelity Verification`
**Base:** `09545e6` (full: `09545e6d2ba2d8fe7d0177c776618ee53f0ab930`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 20, *"D2 — Command: owner resolves a decision. Wires the
Atlas mockup's owner-decision affordance to a real backend command."*
This slice registers the **first real command** into the
`_COMMAND_ROUTES` registry that D1 shipped empty
(`services/maestro/maestro/read_api.py`, already merged): a new guarded
HTTP command, `POST /command/resolve-decision`, that wraps the real,
already-tested `OperationalStateStore.transition_packet_eligibility`
method.

D3 (a future slice) wires the Atlas owner-decision card's buttons to
this HTTP command. This slice adds no frontend change at all — it is
backend-only, exactly like D1.

## The architecture gap this slice does NOT paper over

Before writing any code, I checked whether a real backend concept of
"an escalated packet decision" — the mockup's "frozen contract,"
"sentinel version," "amend" language — exists anywhere in
`operational_state.py`. It does not, though the check is more nuanced
than a bare word search: `sentinel` and `amend` do not appear anywhere
in the file at all; `frozen` and `contract` do appear, but only in
spellings unrelated to the mockup's meaning —
`@dataclass(frozen=True)` (a Python stdlib decorator, unrelated to
packet decisions) and `input_contract_json`/`output_contract_json`/
`role_contract_reference` (real work-item I/O-shape fields, unrelated
to freezing a decision). Verified directly against
`operational_state.py` on this slice's own base commit (`grep -in
"sentinel\|frozen\|amend\|contract" operational_state.py`) — no
occurrence, in either category, represents "an escalated packet
decision the owner must resolve." Those are pure mockup narrative
flavor text with zero backend representation.

I surfaced this gap to the Project Architect (the user) directly rather
than either inventing new persisted state on my own initiative or
silently declining to build D2. Given the explicit instruction to
design the minimal real state machine myself, I looked for the
smallest existing real mechanism that is an honest (not invented)
backend counterpart of "an escalated packet the owner must resolve,"
and found one already real, already live, and already tested:

```python
# operational_state.py:61-67 — the real, live packet-eligibility transition table
_PACKET_ELIGIBILITY_TRANSITIONS = {
    "Planned": {"Waiting", "Blocked", "Cancelled"},
    "Waiting": {"Ready", "Blocked", "Cancelled"},
    "Blocked": {"Waiting", "Ready", "Cancelled"},
    "Ready": {"Waiting", "Blocked", "Dispatchable", "Cancelled"},
    "Dispatchable": {"Ready", "Waiting", "Blocked", "Cancelled"},
}
```

`Blocked` is the real state a packet is already placed into (by
existing, unrelated real mechanics not touched by this slice) when it
cannot currently proceed — the honest backend meaning of "waiting on
the owner." `Blocked`'s own real, already-live outgoing edges are
exactly `{Waiting, Ready, Cancelled}` — three real, already-meaningful
outcomes: send it back to the queue, clear it to proceed, or cancel it
outright. This slice's whole design is: expose exactly those three real
outcomes through one new guarded HTTP command, and introduce **zero**
new persisted state, zero new schema, and zero new columns.

This is a narrower claim than the mockup's own language suggests, and
this packet says so plainly rather than dressing up
`transition_packet_eligibility` as something it is not: this command
does not implement "sentinel versions," "amending a frozen contract,"
or any concept of contract freezing/versioning. It is the real,
minimal backend action available today for the one concrete thing the
mockup's button actually needs to do — move a blocked packet to one of
three legitimate next states, safely, with full idempotency and
optimistic-concurrency guarantees, exactly like every other real M1
command.

## Evidence: the real method this command wraps, unmodified

```python
# operational_state.py:465 — real method signature, called verbatim, not modified by this slice
def transition_packet_eligibility(
    self, packet_id, expected_version, target_state, reason_payload, idempotency_key, actor, now,
):
```

```python
# operational_state.py:89-110 — the 5 exception classes relevant to this
# slice (the real base class plus the 4 this command's handler catches;
# `operational_state.py` declares 2 more subclasses, `ResourceBusy` at
# :113 and `RecoveryConflict` at :121, neither of which
# `transition_packet_eligibility` can raise — see below)
class OperationalStateError(Exception):
    """Base class for closed operational-state failures."""

class InvalidRecord(OperationalStateError):
    ...

class InvalidTransition(OperationalStateError):
    ...

class StaleState(OperationalStateError):
    ...

class IdempotencyConflict(OperationalStateError):
    ...

class ResourceConflict(OperationalStateError):
    ...
```

This slice's handler catches exactly `StaleState`, `InvalidTransition`,
`IdempotencyConflict`, and `InvalidRecord` — the four exceptions
`transition_packet_eligibility` can actually raise (verified by reading
its full body at `operational_state.py:465-529`: it raises
`InvalidTransition`/`InvalidRecord`/`StaleState` directly, and
`IdempotencyConflict` via its own call to the real `self._replay`
helper quoted in D1's own evidence section — it never raises
`ResourceConflict`, `ResourceBusy`, or `RecoveryConflict`, so this
slice does not catch any of those three — catching an exception a
method cannot raise would be dead code, not a guard).

## Design rationale (decisions made under delegated Project Architect authority)

1. **Reuse `transition_packet_eligibility` and the real `Blocked`
   state; invent nothing new.** See "The architecture gap this slice
   does NOT paper over" above. This was an explicit delegation from
   the user (`AskUserQuestion` → "Design the minimal real state machine
   myself") after I disclosed that no real backend concept of
   escalation/sentinel/frozen-contract exists.
2. **`target_state` is restricted to exactly `{Cancelled, Ready,
   Waiting}` by this command's own validator**, in addition to (not
   instead of) the store's own real transition-table check. This
   command's validator rejects any other string outright with 400
   before ever calling into the store; the store's own
   `_PACKET_ELIGIBILITY_TRANSITIONS` table remains the single source of
   truth for which *source* states may legally reach them — this
   command does not duplicate or second-guess that check, it only
   narrows the *set of outcomes this specific HTTP command is willing
   to request* to the three that are meaningful for "owner resolves a
   decision." (A future, different command could legitimately request
   `Dispatchable`, say — that is out of scope for this command's own
   narrower purpose.)
3. **`now` is computed by the handler itself**, unlike D1's scaffold
   which deliberately left `now` unhandled (D1 had no real command to
   receive one). This is the first real command in `_COMMAND_ROUTES`,
   so it is this slice's job to supply it:
   `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"`
   — matching the exact microsecond-precision, `Z`-suffixed UTC string
   format `tests/m1_02/test_packet_eligibility.py`'s own `NOW`/`LATER`
   fixtures use (`"2026-01-01T00:00:00.000000Z"`-shaped), confirmed by
   reading that file directly rather than assumed.
4. **A fresh `OperationalStateStore` is constructed per request**,
   exactly matching every existing GET route's own pattern in this
   file (`RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)`
   appears identically at `read_api.py:163`, `:198`, `:233`, `:281` for
   the four existing snapshot routes) — this slice's new handler is the
   fifth, not a new pattern.
5. **Real closed-shape/field validation of `actor` is still not this
   command's job**, exactly as D1 established: `_validate_command_envelope`
   (unchanged, D1's own code) checks only that `actor` is *some* JSON
   object; the real `_actor()` closed-shape check inside
   `OperationalStateStore` (called internally by
   `transition_packet_eligibility`) is what actually validates it, and
   raises `InvalidRecord` (mapped to this command's 400 response) if it
   fails. This slice's own test `test_08` confirms a malformed
   command-specific field is caught by this command's validator before
   the store is ever reached; it does not separately re-test
   `_actor()`'s own internal shape rules, since those are already
   covered by `tests/m1_02`'s own suite and this slice changes nothing
   about them.
6. **`reason_payload` is passed through to the store verbatim, with
   only an outer "is it a JSON object" shape check.** The store's own
   real `_reason()`-equivalent internal validation (inside
   `transition_packet_eligibility`) is the single source of truth for
   what a well-formed reason payload contains — matching the same
   division of responsibility as decision 5 above for `actor`.

## Guards

1. This slice modifies exactly one already-merged file
   (`services/maestro/maestro/read_api.py`) and adds exactly one new
   test file (`tests/m2_wave_d/test_resolve_decision_command.py`); it
   also makes a one-line, additive edit to the existing
   `tests/m2_wave_d/test_command_api_scaffold.py` (see item 2) — no
   other file touched.
2. D1's own `test_11_no_real_command_is_registered_in_production_code`
   asserted `_COMMAND_ROUTES == {}`, which is now false by design —
   this slice's entire purpose is registering the first real command.
   Renamed to
   `test_11_only_the_real_resolve_decision_command_is_registered_in_production_code`
   and changed to assert the exact, closed route set
   (`{"/command/resolve-decision": _handle_resolve_decision}`), not
   merely "non-empty" — a future slice that accidentally registers an
   extra route is still caught by this same test. No other line in
   `test_command_api_scaffold.py` changed; all 11 other tests in that
   file re-run unmodified and still pass (see Pre-verification).
3. No `OperationalStateStore` method is added, modified, or removed by
   this slice — `transition_packet_eligibility` is called verbatim,
   with all 7 positional arguments in its own real declared order.
4. No new persisted state, schema, column, or table is introduced —
   this command is a thin HTTP wrapper around one pre-existing,
   pre-tested method.
5. `services/maestro/maestro/__pycache__/*.pyc` — several of which are
   tracked in this repository — were not left modified: any incidental
   changes from running the toolchain locally were reverted before
   finalizing this packet (`git checkout --` on the tracked `.pyc`
   files touched by this slice's own verification runs, plus removing
   the one new untracked `read_api.cpython-312.pyc`).
6. This slice does not implement the mockup's "sentinel version,"
   "frozen contract," or "amend" semantics — see "The architecture gap
   this slice does NOT paper over" above. Building those, if the user
   ever wants them built literally, would require new persisted state
   and is out of scope for this slice and this command.
7. This command does not implement D3 (wiring the Atlas owner-decision
   card's buttons to this endpoint) — that is explicitly a future
   slice's job, not this one's.

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
```

## `tests/m2_wave_d/test_command_api_scaffold.py` (existing — one test changed, per Guards item 2)

```python
    def test_11_only_the_real_resolve_decision_command_is_registered_in_production_code(self) -> None:
        # D1 shipped the scaffold with zero commands wired; D2 wires the
        # first real one (see tests/m2_wave_d/test_resolve_decision_command.py).
        # This asserts the exact, closed set — not just "non-empty" — so a
        # future slice accidentally registering an extra route is caught here.
        self.assertEqual(
            read_api._COMMAND_ROUTES,
            {"/command/resolve-decision": read_api._handle_resolve_decision},
        )
```

All 11 other tests in this file are byte-for-byte unchanged from the
merged D1 version.

## `tests/m2_wave_d/test_resolve_decision_command.py` (new)

```python
from __future__ import annotations

import http.client
import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from maestro import read_api
from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig
from maestro.operational_state import Actor, OperationalStateStore


NOW = "2026-09-05T12:00:00.000000Z"
COMMIT = "a" * 40
DIGEST = "b" * 64
ACTOR = {"actor_type": "Owner", "actor_id": "owner-1", "correlation_id": "correlation-1"}
REASON = {"kind": "reason", "reason_code": "OwnerResolvedDecision", "detail_reference": None}


def _request(
    port: int, method: str, path: str, body: bytes | None = None
) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        response_body = response.read()
        return response.status, response.getheader("Content-Type"), response_body
    finally:
        connection.close()


class _PacketDatabase:
    """A minimal, self-contained real seed: one project/binding/graph
    projection/run/packet chain, following the exact same real
    `OperationalStateStore` calls `tests/m1_02/test_packet_eligibility.py`'s
    own `PacketDatabase` fixture uses — copied rather than imported, so
    `tests/m2_wave_d` stays a fully independent test directory, matching
    every other M2 slice's own established convention.
    """

    def __init__(self) -> None:
        DEFAULT_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        self._temporary = tempfile.TemporaryDirectory(dir=DEFAULT_RUNTIME_DIR)
        self.path = Path(self._temporary.name) / "runtime"
        self.config = RuntimeConfig(self.path)
        self.store = OperationalStateStore(self.config)
        self.store.health()
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute(
                "INSERT INTO projects(project_id,repository_identity,default_branch,adapter_version,"
                "process_version,registration_state) VALUES (?,?,?,?,?,'Candidate')",
                ("project-1", "owner/repo", "main", "adapter-v1", "process-v1"),
            )
            connection.commit()
        self.store.record_binding(
            {
                "binding_id": "binding-1",
                "project_id": "project-1",
                "binding_revision": "revision-1",
                "source_commit": COMMIT,
                "manifest_digest": DIGEST,
                "adapter_version": "adapter-v1",
                "process_version": "process-v1",
                "authority_reference": "authority-1",
                "merge_policy": "no-automatic-merge",
                "acceptance_authority": "ProjectArchitect",
                "merge_execution_authority": "OwnerPerformed",
                "merge_delegation_reference": None,
                "binding_json": {"binding": "candidate"},
                "state": "Candidate",
                "activated_at": None,
                "superseded_at": None,
            },
            "seed-binding",
            Actor(**ACTOR),
            NOW,
        )
        self.store.record_graph_projection(
            {
                "graph_projection_id": "graph-1",
                "project_id": "project-1",
                "binding_id": "binding-1",
                "graph_revision": "graph-r1",
                "authority_reference": "graph-authority",
                "source_base_sha": COMMIT,
                "source_hash": DIGEST,
                "state": "Active",
                "observed_at": NOW,
            },
            [
                {
                    "work_item_id": "work-1",
                    "graph_projection_id": "graph-1",
                    "architecture_node_id": "node-1",
                    "task_reference": "task-1",
                    "workstream_ref": "operational-core",
                    "milestone_ref": "M1",
                    "title": "Resolve-decision seed",
                    "priority": "P0",
                    "planned_rank": 1,
                    "specialist_role": "MaestroDeveloper",
                    "execution_classes_json": ["codex-cloud"],
                    "dependencies_json": [],
                    "change_domains_json": ["operational-state"],
                    "input_contract_json": {"version": 4},
                    "output_contract_json": {"version": 4},
                    "planning_state": "Active",
                }
            ],
            "seed-graph",
            Actor(**ACTOR),
            NOW,
        )
        self.store.create_run(
            {
                "run_id": "run-1",
                "run_fingerprint": DIGEST,
                "project_id": "project-1",
                "binding_id": "binding-1",
                "graph_projection_id": "graph-1",
                "milestone_ref": "M1",
                "approved_authority_reference": "authority-1",
                "branch_name": None,
                "pull_request_reference": None,
                "current_head": None,
                "current_head_source_reference": None,
                "candidate_head": None,
                "candidate_head_source_reference": None,
                "state": "Planned",
                "acceptance_boundary": "ProjectArchitect",
            },
            "seed-run",
            Actor(**ACTOR),
            NOW,
        )
        self.created = self.store.materialize_packet(
            {
                "packet_id": "packet-1",
                "run_id": "run-1",
                "work_item_id": "work-1",
                "packet_revision": "packet-r1",
                "authority_reference": "packet-authority",
                "base_commit": COMMIT,
                "current_head": None,
                "expected_branch": "implementation/resolve-decision",
                "role_contract_reference": "role-1",
                "sop_reference": "sop-1",
                "executor_class": "codex-cloud",
                "integration_route": "validate-only",
                "reviewer_route": "independent",
                "owned_paths_json": ["services/maestro"],
                "forbidden_paths_json": ["live-project"],
                "checks_json": ["python", "unittest"],
                "resource_claims_json": ["shared:operational-state"],
                "context_policy_json": {
                    "minimum_context_tokens": 32768,
                    "output_reserve_tokens": 8192,
                    "warning_remaining_tokens": 16384,
                    "checkpoint_remaining_tokens": 12288,
                    "stop_remaining_tokens": 8192,
                },
                "state": "Planned",
                "correction_count": 0,
            },
            "seed-packet",
            Actor(**ACTOR),
            NOW,
        )
        # Real escalation: Planned -> Blocked is a real, already-enforced
        # edge in `_PACKET_ELIGIBILITY_TRANSITIONS` — this is the honest
        # backend stand-in for "the packet is now waiting on the owner."
        self.escalated = self.store.transition_packet_eligibility(
            "packet-1", 1, "Blocked", REASON, "seed-escalate", Actor(**ACTOR), NOW
        )

    @property
    def database(self) -> Path:
        return self.path / "maestro.sqlite3"


class ResolveDecisionCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = _PacketDatabase()
        self.server = read_api.ReadApiServer(
            read_api.ReadApiConfig(port=0, runtime_dir=self.runtime.path)
        )
        self.server.start()
        self.addCleanup(self.server.stop)

    def _post(self, envelope: dict) -> tuple[int, str | None, dict]:
        status, content_type, raw_body = _request(
            self.server.bound_port,
            "POST",
            "/command/resolve-decision",
            body=json.dumps(envelope).encode("utf-8"),
        )
        return status, content_type, json.loads(raw_body)

    def _base_envelope(self, **overrides) -> dict:
        envelope = {
            "idempotency_key": "resolve-1",
            "actor": ACTOR,
            "packet_id": "packet-1",
            "expected_version": 2,
            "target_state": "Waiting",
            "reason_payload": REASON,
        }
        envelope.update(overrides)
        return envelope

    def test_01_real_end_to_end_resolution_moves_the_real_packet_from_blocked_to_waiting(self) -> None:
        self.assertEqual(self.runtime.escalated["state"], "Blocked")
        self.assertEqual(self.runtime.escalated["version"], 2)

        status, content_type, body = self._post(self._base_envelope())
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(
            body,
            {"entity_id": "packet-1", "entity_type": "Packet", "kind": "state", "state": "Waiting", "version": 3},
        )

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("Waiting", 3))

    def test_02_each_real_resolution_target_succeeds_from_blocked(self) -> None:
        for target in ("Waiting", "Ready", "Cancelled"):
            with self.subTest(target=target):
                runtime = _PacketDatabase()
                server = read_api.ReadApiServer(
                    read_api.ReadApiConfig(port=0, runtime_dir=runtime.path)
                )
                server.start()
                try:
                    status, _content_type, body = self._post_to(
                        server.bound_port,
                        {
                            "idempotency_key": f"resolve-{target}",
                            "actor": ACTOR,
                            "packet_id": "packet-1",
                            "expected_version": 2,
                            "target_state": target,
                            "reason_payload": REASON,
                        },
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(body["state"], target)
                    self.assertEqual(body["version"], 3)
                finally:
                    server.stop()

    def _post_to(self, port: int, envelope: dict) -> tuple[int, str | None, dict]:
        status, content_type, raw_body = _request(
            port, "POST", "/command/resolve-decision", body=json.dumps(envelope).encode("utf-8")
        )
        return status, content_type, json.loads(raw_body)

    def test_03_rejects_a_target_state_outside_the_three_real_resolution_outcomes(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(target_state="Running"))
        self.assertEqual(status, 400)
        self.assertEqual(
            body, {"detail": "target_state must be one of: Cancelled, Ready, Waiting", "error": "invalid_command"}
        )

    def test_04_stale_expected_version_returns_409_stale_state(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(expected_version=1))
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "stale_state")

    def test_05_wrong_source_state_returns_409_invalid_transition(self) -> None:
        # packet-1 is real-seeded into "Blocked" (version 2); resolving
        # straight to "Cancelled" first, then trying to resolve it again
        # from what is now a real "Cancelled" packet must be rejected — the
        # store's own real transition table has no entry for "Cancelled" at
        # all, so `.get(source_state, set())` is genuinely empty.
        first_status, _content_type, first_body = self._post(
            self._base_envelope(target_state="Cancelled", idempotency_key="resolve-cancel")
        )
        self.assertEqual(first_status, 200)
        self.assertEqual(first_body["state"], "Cancelled")

        second_status, _content_type, second_body = self._post(
            self._base_envelope(
                target_state="Waiting", expected_version=3, idempotency_key="resolve-again"
            )
        )
        self.assertEqual(second_status, 409)
        self.assertEqual(second_body["error"], "invalid_transition")

    def test_06_true_idempotent_replay_returns_the_exact_original_result_without_a_second_write(self) -> None:
        first_status, _content_type, first_body = self._post(self._base_envelope())
        self.assertEqual(first_status, 200)

        second_status, _content_type, second_body = self._post(self._base_envelope())
        self.assertEqual(second_status, 200)
        self.assertEqual(second_body, first_body)

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        # still version 3 — the replayed call did not apply the transition
        # a second time.
        self.assertEqual(row["version"], 3)

    def test_07_same_idempotency_key_with_different_facts_returns_409_idempotency_conflict(self) -> None:
        first_status, _content_type, _first_body = self._post(self._base_envelope())
        self.assertEqual(first_status, 200)

        conflicting_status, _content_type, conflicting_body = self._post(
            self._base_envelope(target_state="Ready")
        )
        self.assertEqual(conflicting_status, 409)
        self.assertEqual(conflicting_body["error"], "idempotency_conflict")

    def test_08_missing_or_invalid_command_specific_fields_return_400_invalid_command(self) -> None:
        bad_bodies = [
            self._base_envelope(packet_id=""),
            {k: v for k, v in self._base_envelope().items() if k != "packet_id"},
            self._base_envelope(expected_version=0),
            self._base_envelope(expected_version="2"),
            {k: v for k, v in self._base_envelope().items() if k != "target_state"},
            self._base_envelope(reason_payload="not-an-object"),
        ]
        for payload in bad_bodies:
            with self.subTest(payload=payload):
                status, _content_type, body = self._post(payload)
                self.assertEqual(status, 400)
                self.assertEqual(body["error"], "invalid_command")

    def test_09_unknown_packet_returns_400_invalid_command(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(packet_id="does-not-exist"))
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_command")

    def test_10_no_fictional_contract_semantics_appear_anywhere_in_the_real_response(self) -> None:
        status, _content_type, body = self._post(self._base_envelope())
        self.assertEqual(status, 200)
        serialized = json.dumps(body)
        for fictional_term in ("sentinel", "amend", "frozen", "contract", "Architect agent"):
            self.assertNotIn(fictional_term, serialized)


if __name__ == "__main__":
    unittest.main()
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (`/tmp/maestro-m2-d2`, branch `architecture/m2-d2`, base
`09545e6`) and run through the real Python toolchain from
`services/maestro` (`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1`), before
this packet was finalized. Scratch `.pyc` churn was then reverted (3
tracked files restored with `git checkout --`, 1 new untracked file
deleted) so the worktree returned to a clean diff before running the
review-readiness gate.

- `python -m unittest discover -s ../../tests/m2_wave_d -v` — **22/22
  passed**: all 12 pre-existing `test_command_api_scaffold.py` tests
  (11 unchanged, `test_11` updated per Guards item 2) plus all 10 new
  `test_resolve_decision_command.py` tests.
  - First full run surfaced exactly one expected, self-caught failure:
    the pre-existing `test_11_no_real_command_is_registered_in_production_code`
    failed because `_COMMAND_ROUTES` is no longer empty — this is the
    correct, intended consequence of registering the first real
    command, not a defect. Fixed per Guards item 2 (renamed test,
    asserts the exact closed route set); re-run confirmed 22/22.
- `python -m unittest discover -s ../../tests/m2_wave_a -v` — **49/49
  passed**, unmodified — zero regression in the existing Wave A read
  API tests.
- `python -m unittest discover -s ../../tests/m1_02 -v` — **162/162
  passed**, unmodified — zero regression in
  `transition_packet_eligibility`'s own real, pre-existing test suite,
  which this slice calls but does not modify.
- `python -c "from maestro import read_api; print(read_api._COMMAND_ROUTES)"`
  — confirms the module imports cleanly and exposes exactly the one
  real route.

**Total: 233 tests directly re-verified across the 3 directories this
slice's diff can plausibly affect (49 + 162 + 22), zero new failures
beyond the one expected, self-caught, and fixed test-11 update.** Wave
D's other pre-existing directory (`m2_wave_e`) is Atlas frontend
TypeScript, not Python, and is unaffected by a backend-only slice; it
is not part of this backend toolchain run.

No targeted correction was needed against an external Decision
Fidelity review for this candidate — issues found during this slice's
own pre-verification (the `test_11` update) were fixed before this
packet was ever submitted for review, not after.

## M0-D12 bounded quality contract

1. **Protected outcome:** an owner (or any actor) can resolve a
   `Blocked` packet to one of exactly three real outcomes — `Waiting`,
   `Ready`, or `Cancelled` — through one new guarded HTTP command, with
   the same idempotency, optimistic-concurrency, and closed-exception
   guarantees every other real M1 command already provides, and zero
   change to any of D1's existing scaffold behavior for any other
   command path.
2. **Operating and threat model:** unchanged from D1 — a trusted local
   dev box, loopback only. This slice adds no new file I/O, subprocess,
   or network call beyond what `transition_packet_eligibility` already
   does internally (a single SQLite transaction, unchanged by this
   slice). The command's own envelope and body-size guards (D1's
   `_validate_command_envelope`, `_MAX_COMMAND_BODY_BYTES`) apply
   identically to this new route, since `_dispatch_command` is shared,
   unmodified code.
3. **Explicit exclusions:** the mockup's "sentinel version," "frozen
   contract," and "amend" semantics (no real backend representation
   exists — see "The architecture gap this slice does NOT paper over"
   above); D3's frontend wiring of the Atlas owner-decision card's
   buttons to this endpoint; any `target_state` outside
   `{Cancelled, Ready, Waiting}`; any change to
   `_PACKET_ELIGIBILITY_TRANSITIONS` or any other part of
   `operational_state.py`.
4. **Assurance level:** practical correctness for a thin HTTP command
   wrapper — every documented success path (all 3 real target states)
   and every documented failure path (`StaleState`, `InvalidTransition`,
   `IdempotencyConflict`, `InvalidRecord`-shaped 400s) is directly
   exercised by real HTTP requests over real sockets against a real
   running server, backed by a real seeded SQLite database — not
   mocked at the store or socket layer.
5. **Acceptance proof:** the 22 named `tests/m2_wave_d` tests, 49
   pre-existing Wave A tests, and 162 pre-existing `m1_02` tests all
   passing (233 total, zero regressions).
6. **Implementation boundary:** one modified production file
   (`read_api.py`), one modified test file (one test changed), one new
   test file; no new third-party dependency; no new module; no
   `operational_state.py` change.
7. **Proportionality ceiling:** one new frozenset, one new validator,
   one new handler function, one new registry entry — no new
   persisted state, no new `OperationalStateStore` method, no Atlas
   frontend change.
8. **Stop and escalation rule:** registering any *additional* real
   command, or implementing any literal "sentinel"/"frozen
   contract"/"amend" persisted-state mechanism, is explicitly out of
   scope — a future slice's job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-D2-RESOLVE-DECISION-COMMAND-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-d2-resolve-decision-command.md"]` |
