# M2 Wave A — Packets Snapshot Endpoint — Candidate 01

**Slice ID:** `MB-SLICE-M2-A2-PACKETS-SNAPSHOT-01`
**Status:** `Pending Targeted Verification` — targeted planning correction applied after Decision Fidelity `REQUEST_CHANGES` found the `RuntimeConfig`/`RuntimePathError` failure path was not covered by the 503 contract and an internal contradiction over when `RuntimeConfig` is resolved
**Base:** `08ac872` (`origin/master`)

## Scope, deliberately minimal

Wave A2 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the second route on
the read API process built in A1
(`MB-SLICE-M2-A1-READ-API-SCAFFOLD-01`, merged). Exactly one new endpoint,
`GET /snapshot/packets`, returns a read-only, paginated projection of the
existing `packets` table. No attempts, no reviews, no events, no event
stream — those are A3, A4, and A5. No write path of any kind.

This slice reads `services/maestro/maestro/read_api.py` and
`services/maestro/maestro/storage.py` (both unmodified except where named
below) and `services/maestro/maestro/config.py` (`RuntimeConfig`, read
only, not modified) from current `origin/master`, and the `packets` table
schema in `storage.py`'s `CREATE TABLE packets` (unmodified). Controlling
authority is the Bootstrap Convergence Policy, the M2 roadmap, and M0-D01,
read from current `origin/master`.

This slice also fixes a recorded non-blocking observation from A1's
implementation review at zero extra risk, since it already touches this
file: `ReadApiServer` gains a public `wait_forever()` method, and
`cli.py`'s `serve-read-api` calls it instead of reaching into the private
`_thread` attribute. This is not new scope; it removes a call into another
module's private attribute now that a natural place to fix it exists.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-A2-PACKETS-SNAPSHOT-01` |
| `phase` | `PendingTargetedVerification` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:08ac872","git:full-planning-review-head:32cfd9efe937feb9c369892369c2d49d9c91319e","review:decision-fidelity:request-changes:2-blocking-findings"]` |

## Exact route contract

`GET /snapshot/packets[?limit=<n>][&after=<packet_id>]`

Query-string parsing: the query string is parsed with
`urllib.parse.parse_qs(query, strict_parsing=False, keep_blank_values=True)`.
The route recognizes exactly two keys, `limit` and `after`. Any of the
following is a `400` with body `{"error":"invalid_query","detail":<string>}`,
where `<string>` is exactly the literal given (no interpolation beyond what
is shown), so two implementers produce byte-identical bodies:

- an unknown key `k` is present → `"unknown query parameter: {k}"`;
- `limit` or `after` appears more than once → `"query parameter appears more than once: limit"`
  or `"query parameter appears more than once: after"` (name the one that repeated);
- `limit` is present and is not an ASCII base-10 integer literal (no sign,
  no leading zero except the literal `"0"`) in the closed range `1`–`500`
  → `"limit must be an integer from 1 through 500"`;
- `after` is present and is an empty string →
  `"after must not be empty"`.

If more than one of these is true at once, report the first that matches
in the order listed above (unknown key, then repeated key, then malformed
`limit`, then empty `after`).

`limit` defaults to `100` when absent. `after` defaults to "no lower
bound" when absent.

Success response, `200`, `Content-Type: application/json`, body produced
by the existing `canonical_response_json` (unmodified):

```json
{"next_after":"<packet_id-or-null>","packets":[{"base_commit":"...","correction_count":0,"created_at":"...","current_head":null,"packet_id":"...","packet_revision":"...","run_id":"...","state":"Planned","updated_at":"...","version":1,"work_item_id":"..."}]}
```

Exactly these 11 fields per packet, in this set (canonical JSON sorts keys,
so exact key order in the wire bytes is alphabetical: `base_commit`,
`correction_count`, `created_at`, `current_head`, `packet_id`,
`packet_revision`, `run_id`, `state`, `updated_at`, `version`,
`work_item_id`). `current_head` is JSON `null` when the database column is
`NULL`; every other column in this projection is `NOT NULL` in the schema
and is never `null` in the response. No other `packets` column (
`authority_reference`, `expected_branch`, `role_contract_reference`,
`sop_reference`, `executor_class`, `integration_route`, `reviewer_route`,
`owned_paths_json`, `forbidden_paths_json`, `checks_json`,
`resource_claims_json`, `context_policy_json`) is exposed by this slice —
they are not needed by any Wave B/C packet yet named in the roadmap, and
adding an unused field is exactly the scope creep M0-D12's proportionality
ceiling exists to prevent. A later slice may add fields; it does not need
to remove any this slice adds.

Query semantics: rows are selected with
`SELECT <the 11 columns> FROM packets WHERE (?2 IS NULL OR packet_id > ?2) ORDER BY packet_id ASC LIMIT ?1+1`
(`?1`=`limit`, `?2`=`after` or `NULL`) — the smallest correct keyset-pagination
shape: ordering and pagination are by `packet_id` (the primary key; already
indexed), not by any business-meaningful field like `created_at` or `state`.
Business ordering for Atlas's UI is a Wave C rendering concern, not this
endpoint's contract. If the query returns `limit+1` rows, the response
includes only the first `limit` of them and `next_after` is set to the
`limit`-th row's `packet_id` (the last one included); if the query returns
`limit` rows or fewer, all are included and `next_after` is JSON `null`
(no more pages). An empty `packets` table returns `{"next_after":null,"packets":[]}`.

**Database-unavailable handling (corrected — blocking finding 1 and 2 from
Decision Fidelity review):** the read API never creates, migrates, or
writes the database, and **never validates or resolves `RuntimeConfig` at
`start()` time** — only inside the `/snapshot/packets` handler, per
request, inside one `try` block that covers both steps:

1. `RuntimeConfig.from_runtime_dir(runtime_dir_setting)` — this itself can
   raise `config.RuntimePathError` (a `ValueError` subclass), which is a
   real, reproducible, in-scope condition: it is what happens when the
   fixed `var/` root does not exist yet, before any `maestro health` or
   writer-service activity has ever run on this machine. This is not a
   hypothetical; it is the default state of a fresh checkout.
2. Opening `sqlite3.connect(f"file:{config.database_path.as_posix()}?mode=ro", uri=True, timeout=5.0)`
   and running the query — this can raise `sqlite3.Error` (file does not
   exist, is not a valid SQLite database, or any other read failure).

Both exception classes, `(RuntimePathError, sqlite3.Error)`, are caught by
the **same** `except` clause and produce the **same** response: `503` with
body `{"error":"database_unavailable"}` — no traceback, no partial body.
A `sqlite3.Connection`, if one was successfully opened before the failure,
is closed in a `finally` block before responding; if `RuntimeConfig`
resolution itself failed, no connection object ever existed and there is
nothing to close.

This makes `ReadApiServer.start()` and `ReadApiConfig` construction total
functions with respect to `runtime_dir`: neither one ever raises
`RuntimePathError` (only `ReadApiConfig.__post_init__`'s existing loopback
check can still raise, unchanged from A1), because neither one touches
`RuntimeConfig` at all. Only the request handler does, and only inside the
one unified try/except above.

## `ReadApiConfig` and `ReadApiServer` changes

`read_api.py` gains one new import: `from .config import RuntimeConfig,
RuntimePathError` (both read, neither modified).

`ReadApiConfig` gains one new field:

```python
@dataclass(frozen=True)
class ReadApiConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    runtime_dir: str | Path | None = None   # new; None = RuntimeConfig's own default
```

No change to the existing `__post_init__` loopback guard; `runtime_dir` is
**never** resolved or validated by `ReadApiConfig` or `ReadApiServer`
themselves — not at construction, not at `start()`. It is carried as an
inert value only. This is the corrected design (see "Database-unavailable
handling" above): `RuntimeConfig.from_runtime_dir(...)` is called exactly
once per incoming `/snapshot/packets` request, inside that request's own
try/except, and nowhere else. `ReadApiServer.start()` is therefore
guaranteed to raise only what A1 already documented
(`RuntimeError` on double-start) plus `ReadApiConfig`'s own
`ReadApiBindError` on an invalid host — never `RuntimePathError`.

The HTTP server subclass carries the raw, unvalidated setting so the
handler can reach it per request:

```python
class _ReadApiHTTPServer(ThreadingHTTPServer):
    def __init__(self, address, handler_cls, runtime_dir_setting: str | Path | None) -> None:
        super().__init__(address, handler_cls)
        self.runtime_dir_setting = runtime_dir_setting
```

`ReadApiServer.start()` constructs `_ReadApiHTTPServer` (replacing the bare
`ThreadingHTTPServer` construction) instead of `ThreadingHTTPServer`
directly, passing `self._config.runtime_dir` straight through unexamined;
every other line of `start()`/`stop()`/`bound_port`/`__enter__`/`__exit__`
is unchanged.

`ReadApiServer` gains one new public method, `wait_forever(self) -> None`,
that calls `self._thread.join()` if a thread exists, else returns
immediately. `cli.py`'s `serve-read-api` handler is changed to call
`server.wait_forever()` instead of reaching into `server._thread.join()`
directly — this is the only change to `cli.py` in this slice, and it does
not alter any observable behavior (the exact same blocking call happens;
only which module performs the attribute access changes).

## Route dispatch generalization

`_ReadApiRequestHandler._route` is refactored from its A1 single-path
`if self.path != "/health"` check into a small dispatch keyed on the
**path component only** (the part of `self.path` before any `?`, via
`urllib.parse.urlsplit(self.path).path`):

```python
_ROUTES = {
    "/health": _handle_health,       # existing behavior, byte-identical
    "/snapshot/packets": _handle_snapshot_packets,  # new
}
```

Dispatch order, unchanged from A1's guarantee: an unrecognized path is
always `404` regardless of method; a recognized path with a method other
than `GET` is always `405`; `/health`'s exact behavior (body, status,
headers, no-op logging) is byte-identical to the merged A1 code — this
slice changes zero observable `/health` behavior, only the internal
dispatch mechanism.

## Guards, before any database access

1. Every guard already in A1 (loopback host allowlist before any socket;
   `start()`/`stop()` idempotency and double-start rejection; `bound_port`
   before-start error) is unchanged and unmodified by this slice.
2. Path/method dispatch (404 for unknown path, 405 for wrong method) is
   checked and resolved **before** any query-string parsing or database
   access for `/snapshot/packets`.
3. Query-string validation (unknown key, repeated key, malformed `limit`,
   empty `after`) is checked and resolved **before** any `RuntimeConfig`
   resolution or database connection is attempted.
4. `RuntimeConfig.from_runtime_dir(...)` resolution and the database
   connection open/query are both inside the one try/except described
   under "Database-unavailable handling," catching
   `(RuntimePathError, sqlite3.Error)` uniformly. The database connection,
   when one is opened, is read-only (`mode=ro`); this slice's code path
   contains no `INSERT`, `UPDATE`, `DELETE`, `CREATE`, or `PRAGMA ... = `
   statement of any kind, and no migration call, and no other exception
   type is caught or suppressed (a genuine bug elsewhere still surfaces
   normally rather than being silently reported as `database_unavailable`).

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `services/maestro/maestro/read_api.py` (extended)
- `services/maestro/maestro/cli.py` (the one-line `wait_forever()` call
  change only; no other line changes)
- `tests/m2_wave_a/test_read_api_scaffold.py` (extended with new tests;
  no existing named test 1-9 changes behavior or assertion)
- `tests/m2_wave_a/test_packets_snapshot.py` (new file)

No other file changes. No new dependency — Python standard library only
(`sqlite3`, `urllib.parse`, already-used `http.server`/`threading`/
`dataclasses`/`json`). `pyproject.toml` is not touched. `storage.py` and
`config.py` are read, not modified.

The 12 named tests, in `tests/m2_wave_a/test_packets_snapshot.py` following
the repository's `test_NN_<description>` convention (a shared test helper
in this new file creates a temporary `RuntimeConfig`, runs the existing,
unmodified `SQLiteFoundation(config).health()` once to create and migrate
a real database, then inserts fixture `packets` rows directly with
parameterized SQL matching the exact `CREATE TABLE packets` schema — no
new fixture-building code is added to any production module):

1. `test_01_empty_table_returns_empty_page` — a freshly migrated, empty
   database returns `200` and exactly `{"next_after":null,"packets":[]}`.
2. `test_02_default_limit_and_field_projection` — 3 fixture packets
   inserted; a bare `GET /snapshot/packets` returns all 3, each with
   exactly the 11 named fields and no others, `current_head` rendering as
   `null` for a fixture row whose column is `NULL`, and `next_after` is
   `null`.
3. `test_03_pagination_next_after_and_exact_page_boundary` — 5 fixture
   packets with known sorted `packet_id`s; `?limit=2` returns exactly the
   first 2 in `packet_id` order and `next_after` equal to the 2nd
   `packet_id`; following with `?limit=2&after=<that value>` returns the
   next 2 and a new `next_after`; a final `?limit=2&after=<4th packet_id>`
   returns exactly the 5th and `next_after` is `null`.
4. `test_04_limit_boundary_values` — `?limit=1` and `?limit=500` are
   accepted; `?limit=0`, `?limit=501`, `?limit=-1`, `?limit=1.5`,
   `?limit=abc`, and `?limit=007` are each `400` `invalid_query`.
5. `test_05_after_and_unknown_key_and_repeated_key_rejected` — `?after=`
   (empty value) is `400`; `?bogus=1` is `400`; `?limit=1&limit=2` is
   `400`; `?after=x&after=y` is `400`.
6. `test_06_unknown_path_and_wrong_method_unchanged` — `GET
   /snapshot/packet` (singular, not a real route) is `404`; `POST
   /snapshot/packets` is `405`; both bodies match the existing A1
   `_NOT_FOUND_BODY`/`_METHOD_NOT_ALLOWED_BODY` constants exactly (proves
   the dispatch refactor didn't change these).
7. `test_07_health_route_byte_identical_after_refactor` — re-runs A1's
   exact `test_02` assertion (body, status, headers, no stderr output)
   against the refactored dispatcher, proving zero behavior change to
   `/health`.
8. `test_08_database_unavailable_returns_503` — two sub-cases, both
   proving the unified `(RuntimePathError, sqlite3.Error)` handling
   (blocking findings 1 and 2 from Decision Fidelity review):
   (a) a `runtime_dir` whose containing `var/`-relative directory exists
   but whose database file does not (no `SQLiteFoundation(...).health()`
   call made for this config) — exercises the `sqlite3.Error` branch;
   (b) a `runtime_dir` whose path does not exist at all yet (nothing
   under the fixed `var/` root has ever been created for it) — exercises
   the `RuntimePathError` branch. Both sub-cases assert `GET
   /snapshot/packets` returns `503` and exactly
   `{"error":"database_unavailable"}`, no exception propagates past the
   handler (confirmed by the server continuing to serve `/health`
   correctly on a subsequent request in the same test), and — for
   sub-case (a), where a connection could have been opened —  a
   monkeypatched `sqlite3.connect` call counter confirms no connection is
   leaked open.
9. `test_09_query_parsing_uses_path_only_not_query_string_for_routing` —
   `GET /snapshot/packets?limit=1` and `GET /health?ignored=1` are both
   routed correctly (the latter still returns the exact `/health` body;
   an extra query string on `/health` is accepted and ignored, since
   `/health` itself defines no query parameters and this slice's new
   closed-key query validation applies only to the new route).
10. `test_10_wait_forever_replaces_private_thread_access` — `grep`-based
    source assertion: `cli.py` contains no occurrence of `_thread` after
    this slice (proves the private-attribute access is gone), and a
    behavioral assertion: `ReadApiServer.wait_forever()` blocks until
    `stop()` is called from another thread, then returns.
11. `test_11_cli_serve_read_api_still_passes` — re-runs A1's exact test 8
    and test 9 (CLI subprocess SIGINT/invalid-host behavior) unchanged,
    proving the `wait_forever()` substitution didn't change CLI behavior.
12. `test_12_concurrent_requests_do_not_corrupt_pagination` — 20 fixture
    packets; 10 concurrent threads each independently page through the
    full set with `?limit=3`; each thread's concatenated pages reconstruct
    the exact same 20 `packet_id`s in the same order (proves the
    read-only connection and stateless per-request query design has no
    shared mutable pagination state).

Run the existing 299 named tests (test 7's and test 11's re-assertions are
new test functions with new names re-proving old behavior, not
replacements of the original 9 — the original A1 test file's 9 tests are
untouched) plus these 12 (311 total):

```
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m unittest discover -s ../../tests/m1_02 -v
python -m unittest discover -s ../../tests/review_readiness -v
python -m unittest discover -s ../../tests/m2_wave_a -v
```

(`tests/m2_wave_a` now discovers both `test_read_api_scaffold.py`'s 9 and
`test_packets_snapshot.py`'s 12 = 21 in that directory, 311 overall.) Also
run `python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`; and
run exact candidate hygiene before any readiness claim. The one
pre-existing, unrelated `tests/m1_01` PyYAML-version environment failure
carried forward from A1 is expected and out of scope.

### M0-D12 bounded quality contract

1. **Protected outcome:** `GET /snapshot/packets` returns an accurate,
   stable, paginated read-only projection of the `packets` table and never
   mutates the database, never crashes the process on a missing or
   malformed database, and never leaks a column beyond the 11 named.
2. **Operating and threat model:** a trusted local single-user Linux box;
   the Maestro writer service may be concurrently reading/writing the same
   SQLite file (WAL mode, already established by `storage.py`) while this
   process reads; a caller supplying malformed, missing, repeated, or
   unexpected query parameters; a database file that does not yet exist or
   is mid-migration; concurrent Atlas-side requests against the same
   process.
3. **Explicit exclusions:** any write path; any column beyond the 11
   named; any endpoint other than `/snapshot/packets`; any ordering other
   than `packet_id` ascending; any authentication (Owner decision
   2026-09-05: none while single local owner); any behavior change to
   `/health`; any change to `storage.py`'s schema, migrations, or the
   writer service's own connection handling.
4. **Assurance level:** practical trusted-local-process containment,
   consistent with A1 — proportionate to a read-only reporting endpoint
   over data this same trusted process already owns; not a hardened
   public API (no rate limiting, no request-size ceiling beyond what
   `http.server` itself imposes).
5. **Acceptance proof:** the 12 named tests, the 311-test full inventory,
   `compileall`, and exact candidate hygiene, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   Python standard library only; reuse of `RuntimeConfig` and
   `SQLiteFoundation` unmodified; no new dependency.
7. **Proportionality ceiling:** one new route, one new config field, one
   new server subclass, one new public method (the recorded A1 follow-up),
   two test files; no event stream, no write path, no new business
   ordering logic, no additional columns.
8. **Stop and escalation rule:** if a future Wave view genuinely needs a
   business-ordering, filtering, or additional-column capability, that is
   a new, separately reviewed slice — not an extension of this one after
   freeze. A discovered proof/contract defect against a frozen slice
   terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
