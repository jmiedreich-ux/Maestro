# M2 Wave D — Command: Crash Recovery — Candidate 01

**Slice ID:** `MB-SLICE-M2-D6-RESOLVE-CRASH-COMMAND-01`
**Status:** `Draft, pending Decision Fidelity Review`
**Base:** `cf0c25a` (full: `cf0c25ad7d1a5d7f4e659accda83e201adc1b632`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 24, *"D6 — Command: crash recovery choice (resume /
re-dispatch / hold-and-inspect)."* This slice registers the **second**
real command into D1/D2's already-guarded `_COMMAND_ROUTES` scaffold:
`POST /command/resolve-crash`, wrapping the real, already-tested
`OperationalStateStore.record_and_close_needs_replan`.

## The architecture gap this slice does NOT paper over

Before writing any code, I checked whether real backend support exists
for the roadmap item's own three-way choice. It does not — and unlike
D2 (which found 2 of 3 mockup concepts had no real backing but the
third did, cleanly), this slice found that **only one of the three
named options has any real backend counterpart at all**:

- `finish_attempt_execution`'s `Failed`/`TimedOut`/`Stale` outcomes all
  route the packet to the real `NeedsReplan` state
  (`operational_state.py:1403-1409`, the real `outcome_mapping` dict,
  quoted in full below).
- `record_and_close_needs_replan` (`operational_state.py:531-596`) is
  the **only** real transition out of `NeedsReplan` — and it is not
  parameterized at all: it hard-codes its target to `"Cancelled"`
  (`operational_state.py:574`), unlike D2's
  `transition_packet_eligibility`, which takes a real `target_state`
  argument. There is no `target_state` parameter to restrict here,
  because there is only one real destination in the first place.
- **"Resume from the last boundary" has no real command.** No method
  anywhere in `operational_state.py` re-opens or continues a dead
  attempt; `Running`/`Leased` attempts only ever terminate via
  `finish_attempt_execution`, never resume.
- **"Re-dispatch to a different worker" has no real command either.**
  `claim_packet_assignment` (`operational_state.py:598`) is the only
  real way to create a new attempt, and it requires the packet's
  source state to be `Dispatchable` (`operational_state.py:644-645`,
  checked directly) — never `NeedsReplan`. A `NeedsReplan` packet
  cannot be re-dispatched without first passing through real states
  this command does not create.

Both missing options depend on real packet-compiler/executor machinery
this roadmap's own "What is explicitly out of scope for M2" section
already names as M3, not M2. This mirrors the exact rescheduling
reasoning the Owner already confirmed for D4/D5: a mockup feature that
depends on a later milestone's machinery is rescheduled to that
milestone, not forced into the current one or silently dropped. I am
applying that same standing policy here myself, under my existing
delegated design authority for this class of gap (the Owner's own
words, restated when D3's blocker was found: *"this is an Architectural
planning decision to complete work that is found not in scope in the
current Milestone and plan it into the correct Milestone when that
functionality becomes supported"*) — not treating it as a new, unasked
question.

**This command therefore implements exactly the one real outcome that
exists today**, honestly named `resolve-crash` rather than a
three-way choice: acknowledge a crashed/failed packet and cancel it.
"Resume" and "re-dispatch" are rescheduled to M3 (real executor/
dispatch machinery), matching D4/D5's own precedent — not built, not
silently dropped.

## Evidence

```python
# operational_state.py:1403-1409 — the real outcome mapping every
# crashed/failed/timed-out attempt already routes through
outcome_mapping = {
    "Succeeded": ("AwaitingIntegration", "Released", "Released"),
    "Failed": ("NeedsReplan", "Released", "Released"),
    "Cancelled": ("Cancelled", "Cancelled", "Released"),
    "TimedOut": ("NeedsReplan", "Expired", "Expired"),
    "Stale": ("NeedsReplan", "Released", "Released"),
}
```

```python
# operational_state.py:531-534 — real method signature, called verbatim, not modified by this slice
def record_and_close_needs_replan(
    self, packet_id, expected_packet_version, reason_payload,
    idempotency_key, actor, now,
):
```

```python
# operational_state.py:593-596 — the real exception fallback this
# command's own handler maps to HTTP, identical in shape to D2's
_except sqlite3.IntegrityError as error:
    raise InvalidRecord("needs-replan closure violates a durable constraint") from error
except sqlite3.OperationalError as error:
    self._raise_sqlite(error)
```

`record_and_close_needs_replan` can raise or propagate exactly:
`InvalidRecord` (unknown packet, malformed reason, or a durable
`IntegrityError`), `InvalidTransition` (source state is not
`NeedsReplan`), `StaleState` (version mismatch, checked twice — before
and after the update), `IdempotencyConflict` (via the real `_replay`
helper D1/D2's own evidence sections already quote), and `ResourceBusy`
or a bare `sqlite3.OperationalError` via the identical `_raise_sqlite`
fallback D2's own targeted correction already found and fixed for
`transition_packet_eligibility`. This slice's handler catches all six
from its first draft — the exact fix D2 needed only after an
independent review found the gap, applied here from the start instead
of repeating that review finding.

## Design rationale

1. **Reuses `record_and_close_needs_replan` verbatim; invents nothing
   new.** No new `OperationalStateStore` method, no new persisted
   state, no new schema.
2. **No `target_state` field in this command's envelope.** Unlike D2,
   there is genuinely only one real destination
   (`record_and_close_needs_replan` doesn't accept one either), so
   adding a parameter with a single legal value would be dead
   flexibility, not a guard.
3. **Applies D2's own hard-won exception-handling lesson from the
   first draft, not after a review finds it.** The store-construction
   guard (`try/except (RuntimePathError, sqlite3.Error)`) and the full
   `ResourceBusy`/bare-`sqlite3.OperationalError` exception coverage
   are both present from this slice's first draft — D2 needed two
   separate targeted corrections (one at planning, one at
   implementation review) to reach this same coverage; this slice
   starts there.
4. **"Resume"/"re-dispatch" are rescheduled to M3, not built, not
   dropped.** See "The architecture gap this slice does NOT paper
   over" above.

## Guards

1. This slice modifies exactly one already-merged file
   (`services/maestro/maestro/read_api.py`) and adds exactly one new
   test file (`tests/m2_wave_d/test_resolve_crash_command.py`); it also
   makes a one-method, additive edit to the existing
   `tests/m2_wave_d/test_command_api_scaffold.py` (renaming and
   extending `test_11` to assert the new, exact two-entry
   `_COMMAND_ROUTES` set) — no other file touched.
2. No `OperationalStateStore` method is added, modified, or removed —
   `record_and_close_needs_replan` is called verbatim, with all 6
   positional arguments in its own real declared order.
3. No new persisted state, schema, column, or table is introduced.
4. `services/maestro/maestro/__pycache__/*.pyc` — several of which are
   tracked in this repository — were not left modified: any incidental
   changes from running the toolchain locally were reverted before
   finalizing this packet.
5. This slice does not implement "resume from the last boundary" or
   "re-dispatch to a different worker" — see the architecture-gap
   section above. A dedicated test
   (`test_08_no_fictional_resume_or_redispatch_semantics...`) confirms
   neither "resume" nor "re-dispatch"/"redispatch" nor
   "hold-and-inspect" appears anywhere in this command's real response.
6. This slice does not implement D7 (wiring the Atlas crash card's
   recovery buttons to this endpoint, and rendering the post-choice
   confirmation state) — that is explicitly a future slice's job. Like
   D3 before it, D7 will need its own real-packet-identity check
   before design (the crash card's own fixture data may face the same
   standalone-fixture-vs-real-backend-row gap D3 found) — flagged here
   for whoever picks up D7 next, not resolved by this slice.

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

    # Constructing the store (and resolving its runtime dir) is guarded the
    # same way every existing GET route already guards the identical call
    # (`read_api.py`'s four snapshot handlers) — an independent implementation
    # review of this slice's first draft found this call left unguarded here,
    # a real, reproduced uncaught-`RuntimePathError` crash of the request
    # thread with no HTTP response under a real misconfigured runtime dir.
    try:
        store = OperationalStateStore(
            RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)
        )
    except (RuntimePathError, sqlite3.Error):
        handler._respond(503, canonical_response_json({"error": "database_unavailable"}))
        return

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


# The real, non-fictional resolution of a crashed/failed packet. The
# roadmap's own D6 wording names a three-way choice ("resume / re-dispatch
# / hold-and-inspect"), but only one of those three has any real backend
# counterpart at all: `finish_attempt_execution`'s `Failed`/`TimedOut`/
# `Stale` outcomes all route the packet to the real `NeedsReplan` state
# (operational_state.py:1403-1409), and `record_and_close_needs_replan`
# is the ONLY real transition out of it — a single, hard-coded, non-
# parameterized move to `Cancelled` (operational_state.py:531-596; it
# takes no target_state argument at all, unlike `transition_packet_eligibility`).
# There is no real "resume from the last boundary" (no command re-opens
# a dead attempt) and no real "re-dispatch to a different worker"
# (`claim_packet_assignment`, defined at operational_state.py:598,
# requires a `Dispatchable` source packet at its own check,
# operational_state.py:644-645 — never `NeedsReplan` — checked directly).
# Those two options depend on real M3 packet-compiler/executor machinery
# that does not exist in M2 (same rescheduling the Owner already
# confirmed for D4/D5): this command implements only the one real
# outcome, honestly named `resolve-crash`, not a three-way choice.
def _validate_resolve_crash_command(envelope: dict[str, Any]) -> str | None:
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
    reason_payload = envelope.get("reason_payload")
    if not isinstance(reason_payload, dict):
        return "reason_payload is required and must be a JSON object"
    return None


def _handle_resolve_crash(handler: "_ReadApiRequestHandler", envelope: dict[str, Any]) -> None:
    error_detail = _validate_resolve_crash_command(envelope)
    if error_detail is not None:
        handler._respond(
            400, canonical_response_json({"error": "invalid_command", "detail": error_detail})
        )
        return

    try:
        store = OperationalStateStore(
            RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)
        )
    except (RuntimePathError, sqlite3.Error):
        handler._respond(503, canonical_response_json({"error": "database_unavailable"}))
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
    try:
        result = store.record_and_close_needs_replan(
            envelope["packet_id"],
            envelope["expected_version"],
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
        # Same real, reachable contention path D2's own targeted correction
        # already found and fixed for `transition_packet_eligibility` —
        # `record_and_close_needs_replan` shares the identical
        # `except sqlite3.OperationalError: self._raise_sqlite(error)`
        # fallback (operational_state.py:595-596), so this slice applies
        # the same fix from its first draft rather than repeating that
        # review finding.
        handler._respond(503, canonical_response_json({"error": "resource_busy", "detail": str(error)}))
        return
    except sqlite3.OperationalError as error:
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
    "/command/resolve-crash": _handle_resolve_crash,
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

## `tests/m2_wave_d/test_command_api_scaffold.py` (existing — one test changed)

```python
    def test_11_only_the_real_resolve_decision_and_resolve_crash_commands_are_registered_in_production_code(self) -> None:
        # D1 shipped the scaffold with zero commands wired; D2 wired the
        # first real one, D6 the second (see
        # tests/m2_wave_d/test_resolve_decision_command.py and
        # tests/m2_wave_d/test_resolve_crash_command.py). This asserts the
        # exact, closed set — not just "non-empty" — so a future slice
        # accidentally registering an extra route is caught here.
        self.assertEqual(
            read_api._COMMAND_ROUTES,
            {
                "/command/resolve-decision": read_api._handle_resolve_decision,
                "/command/resolve-crash": read_api._handle_resolve_crash,
            },
        )
```

All 11 other tests in this file are byte-for-byte unchanged from the
merged D2 version.

## `tests/m2_wave_d/test_resolve_crash_command.py` (new)

```python
from __future__ import annotations

import http.client
import json
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from pathlib import Path

from maestro import read_api
from maestro.config import DEFAULT_RUNTIME_DIR, RuntimeConfig, RuntimePathError
from maestro.operational_state import Actor, OperationalStateStore


NOW = "2026-09-05T12:00:00.000000Z"
COMMIT = "a" * 40
DIGEST = "b" * 64
ACTOR = {"actor_type": "Owner", "actor_id": "owner-1", "correlation_id": "correlation-1"}
REASON = {"kind": "reason", "reason_code": "OwnerResolvedCrash", "detail_reference": None}


def _request(
    port: int, method: str, path: str, body: bytes | None = None
) -> tuple[int, str | None, bytes]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    try:
        connection.request(method, path, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        response_body = response.read()
        return response.status, response.getheader("Content-Type"), response_body
    finally:
        connection.close()


class _PacketDatabase:
    """A minimal, self-contained real seed, matching D2's own established
    convention (`tests/m2_wave_d/test_resolve_decision_command.py`'s
    `_PacketDatabase`) — one project/binding/graph projection/run/packet
    chain, then forced directly into `NeedsReplan` via the same real
    technique `tests/m1_02/test_packet_eligibility.py`'s own
    `PacketDatabase.force_source` already uses (a raw SQL `UPDATE`):
    reaching `NeedsReplan` through the real API requires a full real
    attempt lifecycle (claim -> start -> finish with a Failed/TimedOut/
    Stale outcome), which this command's own test scope does not need to
    exercise — only `record_and_close_needs_replan`'s own real behavior
    from a `NeedsReplan` packet does.
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
                    "title": "Resolve-crash seed",
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
                "expected_branch": "implementation/resolve-crash",
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
        self.force_needs_replan()

    def force_needs_replan(self) -> None:
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute(
                "UPDATE packets SET state='NeedsReplan',version=1,updated_at=? WHERE packet_id='packet-1'",
                (NOW,),
            )
            connection.commit()

    @property
    def database(self) -> Path:
        return self.path / "maestro.sqlite3"


class ResolveCrashCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = _PacketDatabase()
        self.server = read_api.ReadApiServer(
            read_api.ReadApiConfig(port=0, runtime_dir=self.runtime.path)
        )
        self.server.start()
        self.addCleanup(self.server.stop)
        self.addCleanup(self.runtime._temporary.cleanup)

    def _post(self, envelope: dict) -> tuple[int, str | None, dict]:
        status, content_type, raw_body = _request(
            self.server.bound_port,
            "POST",
            "/command/resolve-crash",
            body=json.dumps(envelope).encode("utf-8"),
        )
        return status, content_type, json.loads(raw_body)

    def _base_envelope(self, **overrides) -> dict:
        envelope = {
            "idempotency_key": "resolve-crash-1",
            "actor": ACTOR,
            "packet_id": "packet-1",
            "expected_version": 1,
            "reason_payload": REASON,
        }
        envelope.update(overrides)
        return envelope

    def test_01_real_end_to_end_resolution_moves_the_real_packet_from_needsreplan_to_cancelled(self) -> None:
        row_before = OperationalStateStore(self.runtime.config).snapshot("Packet", "packet-1")
        self.assertEqual((row_before["state"], row_before["version"]), ("NeedsReplan", 1))

        status, content_type, body = self._post(self._base_envelope())
        self.assertEqual(status, 200)
        self.assertEqual(content_type, "application/json")
        self.assertEqual(
            body,
            {"entity_id": "packet-1", "entity_type": "Packet", "kind": "state", "state": "Cancelled", "version": 2},
        )

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("Cancelled", 2))

    def test_02_every_other_source_state_returns_409_invalid_transition(self) -> None:
        for state in ("Planned", "Waiting", "Blocked", "Ready", "Dispatchable", "Cancelled"):
            with self.subTest(state=state):
                with closing(sqlite3.connect(self.runtime.database)) as connection:
                    connection.execute(
                        "UPDATE packets SET state=?,version=1 WHERE packet_id='packet-1'", (state,)
                    )
                    connection.commit()
                status, _content_type, body = self._post(
                    self._base_envelope(idempotency_key=f"other-{state}")
                )
                self.assertEqual(status, 409, state)
                self.assertEqual(body["error"], "invalid_transition", state)
        self.runtime.force_needs_replan()

    def test_03_stale_expected_version_returns_409_stale_state(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(expected_version=2))
        self.assertEqual(status, 409)
        self.assertEqual(body["error"], "stale_state")

    def test_04_true_idempotent_replay_returns_the_exact_original_result_without_a_second_write(self) -> None:
        first_status, _content_type, first_body = self._post(self._base_envelope())
        self.assertEqual(first_status, 200)

        second_status, _content_type, second_body = self._post(self._base_envelope())
        self.assertEqual(second_status, 200)
        self.assertEqual(second_body, first_body)

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual(row["version"], 2)

    def test_05_same_idempotency_key_with_different_facts_returns_409_idempotency_conflict(self) -> None:
        first_status, _content_type, _first_body = self._post(self._base_envelope())
        self.assertEqual(first_status, 200)

        conflicting_status, _content_type, conflicting_body = self._post(
            self._base_envelope(reason_payload={"kind": "reason", "reason_code": "Different", "detail_reference": None})
        )
        self.assertEqual(conflicting_status, 409)
        self.assertEqual(conflicting_body["error"], "idempotency_conflict")

    def test_06_missing_or_invalid_command_specific_fields_return_400_invalid_command(self) -> None:
        bad_bodies = [
            self._base_envelope(packet_id=""),
            {k: v for k, v in self._base_envelope().items() if k != "packet_id"},
            self._base_envelope(expected_version=0),
            self._base_envelope(expected_version="1"),
            self._base_envelope(reason_payload="not-an-object"),
        ]
        for payload in bad_bodies:
            with self.subTest(payload=payload):
                status, _content_type, body = self._post(payload)
                self.assertEqual(status, 400)
                self.assertEqual(body["error"], "invalid_command")

    def test_07_unknown_packet_returns_400_invalid_command(self) -> None:
        status, _content_type, body = self._post(self._base_envelope(packet_id="does-not-exist"))
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "invalid_command")

    def test_08_no_fictional_resume_or_redispatch_semantics_appear_anywhere_in_the_real_response(self) -> None:
        status, _content_type, body = self._post(self._base_envelope())
        self.assertEqual(status, 200)
        serialized = json.dumps(body)
        for fictional_term in ("resume", "re-dispatch", "redispatch", "hold-and-inspect"):
            self.assertNotIn(fictional_term, serialized.lower())

    def test_09_real_writer_lock_contention_returns_503_resource_busy(self) -> None:
        with closing(sqlite3.connect(self.runtime.database, timeout=0)) as holder:
            holder.execute("PRAGMA journal_mode=WAL")
            holder.execute("BEGIN IMMEDIATE")
            holder.execute(
                "UPDATE packets SET version=version WHERE packet_id='packet-1'"
            )
            started = time.monotonic()
            status, _content_type, body = self._post(self._base_envelope())
            elapsed = time.monotonic() - started
        self.assertEqual(status, 503)
        self.assertEqual(body["error"], "resource_busy")
        self.assertGreaterEqual(elapsed, 4.5)

        reopened = OperationalStateStore(self.runtime.config)
        row = reopened.snapshot("Packet", "packet-1")
        self.assertEqual((row["state"], row["version"]), ("NeedsReplan", 1))

    def test_10_real_invalid_runtime_dir_returns_503_database_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as outside_var:
            with self.assertRaises(RuntimePathError):
                RuntimeConfig(outside_var)

            server = read_api.ReadApiServer(
                read_api.ReadApiConfig(port=0, runtime_dir=outside_var)
            )
            server.start()
            try:
                status, _content_type, raw_body = _request(
                    server.bound_port,
                    "POST",
                    "/command/resolve-crash",
                    body=json.dumps(self._base_envelope()).encode("utf-8"),
                )
                body = json.loads(raw_body)
            finally:
                server.stop()
        self.assertEqual(status, 503)
        self.assertEqual(body, {"error": "database_unavailable"})


if __name__ == "__main__":
    unittest.main()
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (`/tmp/maestro-m2-d6`, branch `architecture/m2-d6`, base
`cf0c25a`) and run through the real Python toolchain from
`services/maestro` (`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1`), before
this packet was finalized.

- `python -m unittest discover -s ../../tests/m2_wave_d -v` — **34/34
  passed** on the first full run: all 12 pre-existing
  `test_command_api_scaffold.py` tests (11 unchanged, `test_11`
  updated to the new 2-entry closed route set), all 12 pre-existing
  `test_resolve_decision_command.py` tests (unmodified), and all 10 new
  `test_resolve_crash_command.py` tests.
- `python -m unittest discover -s ../../tests/m2_wave_a -v` — **49/49
  passed**, unmodified — zero regression in the existing Wave A read
  API tests.
- `python -m unittest discover -s ../../tests/m1_02 -v` — **162/162
  passed**, unmodified — zero regression in
  `record_and_close_needs_replan`'s own real, pre-existing test suite
  (`tests/m1_02/test_needsreplan_closure.py`), which this slice calls
  but does not modify.
- `python -c "from maestro import read_api; print(read_api._COMMAND_ROUTES)"`
  — confirms the module imports cleanly and exposes exactly the two
  real routes.

**Total: 245 tests directly re-verified across the 3 directories this
slice's diff can plausibly affect (49 + 162 + 34), zero failures.**
Every line-number citation in this packet's own Evidence and code
comments was independently re-verified against the real
`operational_state.py` on this branch's own base commit before
finalizing (two citation slips were self-caught and fixed during
authoring: the `claim_packet_assignment` `Dispatchable` check is at
line 644-645, not within the function's own opening range as first
drafted; `record_and_close_needs_replan`'s own closing
`except`/`_raise_sqlite` lines are 595-596, not 593-595).

No targeted correction was needed against an external Decision
Fidelity review for this candidate — the two citation slips above were
found during this slice's own pre-verification and fixed before
submission, not after. This slice also applied D2's own two-phase
lesson (the `ResourceBusy`/guarded-construction exception coverage)
from its first draft, rather than needing a review to find the gap
first.

## M0-D12 bounded quality contract

1. **Protected outcome:** a crashed or failed packet (real
   `NeedsReplan` state, reached via `finish_attempt_execution`'s
   `Failed`/`TimedOut`/`Stale` outcomes) can be acknowledged and
   cancelled through one new guarded HTTP command, with the same
   idempotency, optimistic-concurrency, and closed-exception
   guarantees every other real M1/M2 command already provides, and
   zero change to any of D1/D2's existing scaffold behavior for any
   other command path.
2. **Operating and threat model:** unchanged from D1/D2 — a trusted
   local dev box, loopback only. Applies the full exception coverage
   (including `ResourceBusy` and guarded store construction) from the
   first draft, matching D2's post-correction state rather than
   repeating its gap.
3. **Explicit exclusions:** "resume from the last boundary" and
   "re-dispatch to a different worker" (no real backend command exists
   for either — rescheduled to M3, real executor/dispatch machinery,
   matching D4/D5's own precedent); D7's frontend wiring of the Atlas
   crash card's recovery buttons to this endpoint; any change to
   `record_and_close_needs_replan` or any other part of
   `operational_state.py`.
4. **Assurance level:** practical correctness for a thin HTTP command
   wrapper — the one documented success path and every documented
   failure path (`StaleState`, `InvalidTransition`, `IdempotencyConflict`,
   `InvalidRecord`-shaped 400s, `ResourceBusy`-shaped 503, and a bare
   `sqlite3.OperationalError`-shaped 503) is directly exercised by real
   HTTP requests over real sockets against a real running server,
   backed by a real seeded SQLite database — not mocked at the store or
   socket layer. The `ResourceBusy` path is exercised against a real
   held writer lock and the real 5-second busy timeout, not simulated.
5. **Acceptance proof:** the 34 named `tests/m2_wave_d` tests, 49
   pre-existing Wave A tests, and 162 pre-existing `m1_02` tests all
   passing (245 total, zero regressions).
6. **Implementation boundary:** one modified production file
   (`read_api.py`), one modified test file (one test changed), one new
   test file; no new third-party dependency; no new module; no
   `operational_state.py` change.
7. **Proportionality ceiling:** one new validator, one new handler
   function, one new registry entry — no new persisted state, no new
   `OperationalStateStore` method, no Atlas frontend change, no
   `target_state` parameter (none is needed — there is only one real
   destination).
8. **Stop and escalation rule:** implementing "resume" or "re-dispatch"
   with anything other than real M3 executor/dispatch machinery, or
   registering any additional real command, is explicitly out of scope
   — future work's job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-D6-RESOLVE-CRASH-COMMAND-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-d6-resolve-crash-command.md"]` |
