# M2 Wave A — Events Snapshot Endpoint — Candidate 01

**Slice ID:** `MB-SLICE-M2-A5-EVENTS-SNAPSHOT-01`
**Status:** `Pending Decision Fidelity Review`
**Base:** `34f5a8d` (`origin/master`)

## Scope, deliberately minimal

Wave A5 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the fifth and
**last snapshot route** on the read API process (A1-A4 merged) — the
roadmap's own text names this "the source for History" and requires it
**paginated, newest-first**, unlike A2/A3/A4's oldest-first-by-primary-key
convention. This is a real, deliberate direction difference from every
prior snapshot endpoint, justified below. A6 (the event *stream*, for
live tailing) and A7 (reconnect contract) are separate, later slices; this
one is a bounded historical query only.

This slice reads the real, current `services/maestro/maestro/read_api.py`
(merged A1-A4 state — this contract's description of `_ROUTES`,
`_validate_snapshot_query`, `_VALID_SNAPSHOT_QUERY_KEYS`,
`_LIMIT_LITERAL_RE`, `_REVIEWS_SNAPSHOT_COLUMNS`/`_QUERY`/
`_handle_snapshot_reviews`, `canonical_response_json`,
`_ReadApiHTTPServer` is byte-accurate against what is actually in that
file on `origin/master` right now — verified directly) and
`services/maestro/maestro/storage.py`'s `events` table definition
**plus** its schema-4 `_apply_schema_four` extension (the six
`ALTER TABLE events ADD COLUMN` additions), both unmodified. Controlling
authority is the Bootstrap Convergence Policy, the M2 roadmap, and
M0-D01, read from current `origin/master`.

## Why this endpoint's design differs from A2/A3/A4 (read this first)

**1. Newest-first ordering, not oldest-first.** `events.event_id` is
declared `INTEGER PRIMARY KEY` (a true SQLite `rowid` alias, monotonically
increasing on insert — unlike `packets.packet_id`/`attempts.attempt_id`/
`reviews.review_id`, which are ordinary `TEXT PRIMARY KEY` values with no
implied ordering). A History view wants the newest events first. This
slice therefore orders `DESC` and reinterprets the shared `after` cursor
as "strictly older than this `event_id`" (`event_id < after`) instead of
A2-A4's "strictly greater than" — the client still calls it `after`
because it still means "the next page after the one I already have," just
walking backward through time instead of forward through an opaque id
space. `next_after` is still "the last row's id in the page just
returned," mechanically identical in code shape to A2-A4, just now the
smallest `event_id` in a descending batch rather than the largest.

**2. `after` must be validated as an integer here, and `_validate_snapshot_query`
is reused unmodified, not extended, for that.** The shared validator
accepts any non-empty string for `after` (correct for the opaque `TEXT`
ids A2-A4 page over). `event_id` is `INTEGER`, so this slice adds exactly
one **new, additional** check on top of the shared one — never modifying
`_validate_snapshot_query` itself, which stays exactly as A3 last
generalized it: if `after` is present (and the shared check already
confirmed it's non-empty), it must also match `_LIMIT_LITERAL_RE` (the
same non-negative-integer-literal pattern `limit` already uses), else
`400` `{"error":"invalid_query","detail":"after must be a non-negative integer"}`.
This is intentionally a *new, small, endpoint-local* check layered after
the shared one runs clean — not a change to shared code, so A2/A3/A4 are
provably unaffected (they never call this new check at all).

**3. `before_json`/`after_json`/`reason` are projected as raw strings,
**not** decoded like A4's `findings_json`/`coverage_json`.** This is a
deliberate, evidence-based difference from A4, not an oversight:

- `events.before_json`/`after_json`/`reason` carry **no**
  `CHECK(json_valid(...))` constraint in the real schema (verified:
  `reviews.findings_json`/`coverage_json` have one; `events`'s three
  `TEXT NOT NULL` payload columns do not). A4's "infallible decode" design
  depended entirely on that schema-level guarantee; it does not exist here.
- `reason` is empirically **not always JSON** across the codebase's own
  history: `storage.py`'s older `record_binding`-era event insert (the
  `ProjectRegistrationRun`/`AuthorityLoaded` path, still live code) writes
  `reason` as a **plain human-readable string**
  (`"candidate authority is reviewable"` / `"authority load is blocked by
  missing or conflicting facts"`), while `operational_state.py`'s
  `_insert_event`/`_insert_packet_state_event` family writes `reason` as a
  `canonical_json({"kind": "reason", ...})` **object**. A single endpoint
  cannot decode a column that is legitimately either shape depending on
  which era of code wrote the row, without inventing a fragile
  try/fallback heuristic this slice has no mandate to design.
- `before_json`/`after_json` themselves are, in practice, always written
  through `_json(...)`/`canonical_json(...)` in every current writer, so
  they likely *would* decode cleanly today — but exposing them decoded
  while leaving `reason` raw would be an inconsistent, confusing contract
  (two of three "_json"-suffixed columns decoded, one not, on the same
  row). This slice keeps all three raw and `_json`-suffixed, honestly
  matching what they actually are: opaque stored text, exactly as
  `packets`/`attempts` already treat every other column that isn't
  specifically decoded. Deciding whether/how to decode `events` payload
  columns for a specific Wave C history-rendering need is explicitly
  deferred to whichever later slice actually renders History — it is not
  this endpoint's job to guess that need now.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-A5-EVENTS-SNAPSHOT-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:34f5a8d"]` |

## Exact route contract

`GET /snapshot/events[?limit=<n>][&after=<event_id>]`

Validation order: (1) `_validate_snapshot_query` unmodified (unknown key →
repeated key → malformed limit → empty after — identical four literal
`detail` strings to every other snapshot endpoint); (2) only if that
returns no error, this endpoint's own new check: if `after` is present,
it must match `_LIMIT_LITERAL_RE`, else `400`
`{"error":"invalid_query","detail":"after must be a non-negative integer"}`.

Success response, `200`, `Content-Type: application/json`, via the
existing `canonical_response_json` (unmodified):

```json
{"events":[{"actor_id":null,"actor_type":null,"after_json":"...","before_json":"...","causation_event_id":null,"command_fingerprint":null,"correlation_id":null,"created_at":"...","entity_id":"...","entity_type":"...","event_id":42,"event_type":"...","idempotency_key":"...","observed_at":null,"reason":"..."}],"next_after":42}
```

Exactly these 15 fields per event — every `events` column, all raw
(no decoding, per the reasoning above). Verified alphabetical wire order:
`actor_id`, `actor_type`, `after_json`, `before_json`,
`causation_event_id`, `command_fingerprint`, `correlation_id`,
`created_at`, `entity_id`, `entity_type`, `event_id`, `event_type`,
`idempotency_key`, `observed_at`, `reason`. **`event_id` and
`causation_event_id` render as JSON numbers, not strings** — both are
`INTEGER` columns, and `sqlite3`'s driver already returns Python `int`
for them (or `None`), which `canonical_response_json`'s `json.dumps`
serializes as a bare number exactly like A2/A3's existing `version`/
`correction_count`/`attempt_number` integer fields already do today —
this is not new handling, just the first time this contract calls it out
for the specific fields being paged by.

Nullability (verified directly against the real base `CREATE TABLE
events` plus the schema-4 `ALTER TABLE` additions — not assumed):
`actor_id`, `actor_type`, `causation_event_id`, `command_fingerprint`,
`correlation_id`, `observed_at` are the 6 columns added by schema-4 with
no `NOT NULL` and no default — genuinely nullable, render as JSON `null`.
The remaining 9 (`after_json`, `before_json`, `created_at`, `entity_id`,
`entity_type`, `event_id`, `event_type`, `idempotency_key`, `reason`)
carry an explicit `NOT NULL` in the base `CREATE TABLE events` (`event_id`
as `INTEGER PRIMARY KEY` genuinely does imply `NOT NULL` in SQLite —
unlike the `TEXT PRIMARY KEY` case A3 and A4 each had to correct for
`attempt_id`/`review_id`; this is the one primary key in this whole
service that actually gets the implicit guarantee) and never render as
`null`.

Query semantics — **descending** keyset pagination over `event_id`:

```sql
SELECT <the 15 columns> FROM events
WHERE (? IS NULL OR event_id < ?)
ORDER BY event_id DESC
LIMIT ?+1
```

bound as `(after_int_or_none, after_int_or_none, limit)` where
`after_int_or_none` is `int(parsed["after"][0])` when `after` was supplied
(already validated as a non-negative integer literal by this point) or
`None` otherwise — plain `?` placeholders, matching A2-A4's real shipped
style. `next_after`/empty-table/page-boundary mechanics are otherwise
identical to A2-A4 (truncate to `limit`, `next_after` = last included
row's `event_id`, `null` when the page wasn't full), just walking toward
smaller ids instead of larger ones.

**Database-unavailable handling:** identical, unmodified pattern —
`except (RuntimePathError, sqlite3.Error)` → `503`
`{"error":"database_unavailable"}`, connection closed in `finally`.

## Guards, before any database access

Identical to A2-A4's guards (loopback allowlist, path/method dispatch
before query parsing, the shared query validation before any
`RuntimeConfig`/DB access, unified exception handling scoped to exactly
the resolve+connect+query span), plus this endpoint's one additional,
endpoint-local `after`-is-integer guard, itself checked before any
database access — same position in the sequence as the shared checks,
just layered after them.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `services/maestro/maestro/read_api.py` (extended: new
  `_EVENTS_SNAPSHOT_COLUMNS`, `_EVENTS_SNAPSHOT_QUERY`,
  `_handle_snapshot_events`, one new `_ROUTES` entry, and the module
  docstring updated to name all five routes — the same cheap, zero-risk
  piggyback precedent A2's `wait_forever()` and A4's docstring fix already
  established)
- `tests/m2_wave_a/test_events_snapshot.py` (new file)

No other file changes — none of the four existing test files in
`tests/m2_wave_a/` are edited. No new dependency.
`_validate_snapshot_query`/`_VALID_SNAPSHOT_QUERY_KEYS`/
`_LIMIT_LITERAL_RE` are read and reused unmodified, not edited.

The 10 named tests, in `tests/m2_wave_a/test_events_snapshot.py`
following the repository's `test_NN_<description>` convention. Fixture
event rows are inserted with a raw, FK-pragma-off `sqlite3.connect`
(A2-A4's established pattern). `events.event_id` is an `INTEGER PRIMARY
KEY` alias for `rowid` — **do not** supply it explicitly in fixture
inserts; let SQLite assign it, and capture the assigned ids via
`cursor.lastrowid` (or a `RETURNING event_id` clause) so tests can assert
against real, sequential ids rather than guessed ones. `idempotency_key`
is `UNIQUE NOT NULL` — every fixture row needs a distinct value.

1. `test_01_empty_table_returns_empty_page` — a freshly migrated, empty
   database returns `200` and exactly `{"events":[],"next_after":null}`.
2. `test_02_full_field_projection_raw_strings_and_nulls` — one fixture
   event with every nullable column populated (non-null `actor_id`,
   `actor_type`, `causation_event_id` pointing at a second, earlier
   fixture event's real assigned id, `command_fingerprint`,
   `correlation_id`, `observed_at`) and one with all 6 nullable columns
   `NULL`; both returned with exactly the 15 named fields;
   `before_json`/`after_json`/`reason` render as their literal stored
   **strings** (proving no decode happens — one fixture's `reason` is
   deliberately set to a plain, non-JSON sentence like the real
   `ProjectRegistrationRun` writer produces, and the test asserts it comes
   back byte-identical, unparsed); `event_id`/`causation_event_id` render
   as JSON numbers (assert via the raw response bytes, not just a parsed
   comparison, that no quotes surround them).
3. `test_03_newest_first_pagination_and_after_semantics` — 5 fixture
   events inserted in order (ids assigned sequentially by SQLite); a bare
   `GET /snapshot/events?limit=3` returns the 3 **newest** (highest ids)
   in descending order and `next_after` equal to the 3rd-newest's
   `event_id`; `?limit=3&after=<that value>` returns the remaining 2,
   oldest-first-among-themselves-but-still-descending, with `next_after`
   `null`.
4. `test_04_limit_boundary_values` — identical assertions to A2-A4's
   test 4 against `/snapshot/events`.
5. `test_05_shared_query_validation_identical_across_all_four_endpoints`
   — the four shared malformed-query cases (unknown key, repeated
   `limit`, `limit=0`, `limit=501`) issued against `/snapshot/events`,
   `/snapshot/reviews`, `/snapshot/attempts`, and `/snapshot/packets`
   produce byte-identical `400` bodies across all four. (The
   empty-`after` case is included too — `after=` is rejected identically
   everywhere. A non-numeric non-empty `after`, e.g. `after=abc`, is
   **not** part of this cross-endpoint comparison — it is 400 only on
   `/snapshot/events` and a normal, valid opaque-id lookup attempt on the
   other three, per this endpoint's own new integer check.)
6. `test_06_after_must_be_integer` — `?after=abc` and `?after=1.5` are
   each `400` with exactly `{"error":"invalid_query","detail":"after must be a non-negative integer"}`;
   `?after=0` and a real large integer are both accepted.
7. `test_07_unknown_path_and_wrong_method_for_events_route` — `GET
   /snapshot/event` (singular) is `404`; `POST /snapshot/events` is
   `405`; bodies match the existing `_NOT_FOUND_BODY`/
   `_METHOD_NOT_ALLOWED_BODY` constants exactly.
8. `test_08_other_routes_unaffected_by_fifth_route_addition` — re-runs
   the `/health` byte-identity assertion and one full round trip each for
   `/snapshot/packets`, `/snapshot/attempts`, and `/snapshot/reviews`,
   proving the fifth route changed nothing observable on the other four.
9. `test_09_database_unavailable_returns_503` — exactly one sub-case (a
   `runtime_dir` whose directory exists but whose database file does
   not), matching A3/A4's established, justified reduction (the
   `RuntimePathError` branch is the same shared, unmodified code A2
   already proved).
10. `test_10_concurrent_requests_do_not_corrupt_pagination` — 20 fixture
    events, 10 concurrent threads, `?limit=3`, each thread's concatenated
    pages reconstruct the exact same 20 `event_id`s in the same
    (descending) order.

Run the existing 329 named tests (unaffected — no shared function is
modified by this slice) plus these 10 (339 total):

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

(`tests/m2_wave_a` now discovers 9+12+9+9+10 = 49, 339 overall.) Also run
`python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`; run
exact candidate hygiene before any readiness claim (never `rm -rf` any
`__pycache__` directory in this repository — several are tracked; use
`PYTHONDONTWRITEBYTECODE=1` and `git checkout --` to restore if dirtied).
The one pre-existing, unrelated `tests/m1_01` PyYAML-version environment
failure carried forward from A1-A4 is expected and out of scope.

### M0-D12 bounded quality contract

1. **Protected outcome:** `GET /snapshot/events` returns an accurate,
   stable, newest-first paginated read-only projection of the `events`
   table with all 15 columns raw and correct nullability/numeric typing,
   never mutates the database, and never crashes the process on a
   missing/malformed database or a non-integer `after` value.
2. **Operating and threat model:** identical to A2-A4's — a trusted local
   single-user Linux box; the writer service concurrently
   reading/writing the same WAL-mode SQLite file; malformed/missing/
   repeated/unexpected/wrong-type query parameters; a database file or
   runtime directory that does not yet exist; concurrent Atlas-side
   requests.
3. **Explicit exclusions:** any write path; any endpoint other than
   `/snapshot/events`; any ordering other than `event_id` descending; any
   decoding of `before_json`/`after_json`/`reason` (explicitly deferred,
   per the reasoning above, to whichever later slice actually needs it);
   any authentication (Owner decision 2026-09-05: none while single local
   owner); any behavior change to `/health` or the three prior snapshot
   routes; any change to `storage.py`'s schema, migrations, or the writer
   service's own connection handling; the event *stream* (A6) and
   reconnect contract (A7); re-proving the `RuntimePathError` sub-case
   already covered by A2.
4. **Assurance level:** identical to A1-A4 — practical trusted-local-
   process containment, proportionate to a read-only reporting endpoint
   over data this same trusted process already owns.
5. **Acceptance proof:** the 10 named tests, the 339-test full inventory,
   `compileall`, and exact candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above;
   Python standard library only; reuse of `RuntimeConfig`,
   `SQLiteFoundation`, `canonical_response_json`, `_validate_snapshot_query`,
   and `_LIMIT_LITERAL_RE` unmodified; no new dependency.
7. **Proportionality ceiling:** one new route, one new column tuple, one
   new query constant, one small additional endpoint-local validation
   check, one new test file; no decoding logic, no event stream, no write
   path, no additional business filtering (e.g. by `entity_type` or
   `packet_id`) beyond the shared `limit`/`after` shape.
8. **Stop and escalation rule:** if a future Wave view needs filtering by
   entity/packet, decoding of `before_json`/`after_json`/`reason`, or a
   materially different query contract, that is a new, separately
   reviewed slice — not an extension of this one after freeze. A
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
