# M2 Wave A — Attempts Snapshot Endpoint — Candidate 01

**Slice ID:** `MB-SLICE-M2-A3-ATTEMPTS-SNAPSHOT-01`
**Status:** `Pending Decision Fidelity Review`
**Base:** `7252ea0` (`origin/master`)

## Scope, deliberately minimal

Wave A3 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the third route
on the read API process (A1 merged, A2 merged). Exactly one new endpoint,
`GET /snapshot/attempts`, returns a read-only, paginated projection of the
existing `attempts` table, using the identical pagination/validation/
error-handling shape A2 already established for `/snapshot/packets`. No
reviews, no events, no event stream — those are A4 and A5. No write path.

This slice reads the real, current `services/maestro/maestro/read_api.py`
(merged A1+A2 state — this contract's description of `_ROUTES`,
`_validate_snapshot_packets_query`, `_VALID_SNAPSHOT_PACKETS_QUERY_KEYS`,
`_PACKETS_SNAPSHOT_COLUMNS`, `_PACKETS_SNAPSHOT_QUERY`,
`_handle_snapshot_packets`, `_ReadApiHTTPServer`, `canonical_response_json`
is a byte-accurate description of what is actually in that file on
`origin/master` right now — verified against it directly, not
reconstructed from memory) and `services/maestro/maestro/storage.py`'s
`CREATE TABLE attempts` plus its schema-5 `ALTER TABLE attempts ADD COLUMN`
additions and the `attempts_execution_shape_insert`/`_update` triggers
(all unmodified). Controlling authority is the Bootstrap Convergence
Policy, the M2 roadmap, and M0-D01, read from current `origin/master`.

This slice also generalizes the one piece of A2's code that is now proven
identical across two endpoints: `_validate_snapshot_packets_query` and
`_VALID_SNAPSHOT_PACKETS_QUERY_KEYS` are renamed to
`_validate_snapshot_query` and `_VALID_SNAPSHOT_QUERY_KEYS` (both stay
`{"limit", "after"}` — the query contract is the same for every
snapshot-style endpoint) and are called by both `_handle_snapshot_packets`
(zero behavior change — same function body, same error strings, same
order of checks) and the new `_handle_snapshot_attempts`. This is not new
scope: it removes duplication that would otherwise be copy-pasted a third
and fourth time in A4 and A5, and it is a pure rename-and-reuse with no
observable change to `/snapshot/packets`.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-A3-ATTEMPTS-SNAPSHOT-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:7252ea0"]` |

## Exact route contract

`GET /snapshot/attempts[?limit=<n>][&after=<attempt_id>]`

Query-string parsing, validation, defaults, and the four literal `400
invalid_query` `detail` strings (unknown key, repeated key, malformed
`limit`, empty `after`, checked in that precedence order) are **byte-for-
byte identical** to `/snapshot/packets`' contract — this is exactly what
the `_validate_snapshot_query` generalization (above) makes true by
construction, not by parallel maintenance of two copies.

Success response, `200`, `Content-Type: application/json`, via the
existing `canonical_response_json` (unmodified):

```json
{"attempts":[{"attempt_id":"...","attempt_kind":"Initial","attempt_number":1,"completion_evidence_reference":null,"correction_for_review_id":null,"created_at":"...","executor_class":"...","execution_handle":null,"expected_result":null,"finished_at":null,"heartbeat_at":null,"lease_id":"...","model_identity":"...","packet_id":"...","result_commit":null,"runtime_identity":"...","started_at":null,"state":"Planned","updated_at":"...","version":1}],"next_after":"<attempt_id-or-null>"}
```

Exactly these 20 fields per attempt — every column `attempts` has,
including the 4 schema-5 execution-carrier columns
(`execution_handle`, `expected_result`, `heartbeat_at`,
`completion_evidence_reference`). Unlike `packets`, `attempts` has no
oversized JSON-blob columns, so there is nothing to exclude on
proportionality grounds this time; all 20 are exposed. Alphabetical wire
order (canonical JSON sorts keys): `attempt_id`, `attempt_kind`,
`attempt_number`, `completion_evidence_reference`,
`correction_for_review_id`, `created_at`, `execution_handle`,
`executor_class`, `expected_result`, `finished_at`, `heartbeat_at`,
`lease_id`, `model_identity`, `packet_id`, `result_commit`,
`runtime_identity`, `started_at`, `state`, `updated_at`, `version`.

Nullability (per the real schema, both the base `CREATE TABLE` and the
schema-5 shape trigger): `completion_evidence_reference`,
`correction_for_review_id`, `execution_handle`, `expected_result`,
`finished_at`, `heartbeat_at`, `result_commit`, `started_at` render as
JSON `null` when the column is `NULL` — this is normal and expected for a
`Planned` attempt (all 8 are `NULL`) and partially populated for
`Running`/terminal states, exactly per the trigger's own shape rules
(which this slice reads but does not change). The remaining 12 fields
(`attempt_id`, `attempt_kind`, `attempt_number`, `created_at`,
`executor_class`, `lease_id`, `model_identity`, `packet_id`,
`runtime_identity`, `state`, `updated_at`, `version`) are `NOT NULL` in
the schema and never render as `null`.

Query semantics: identical keyset-pagination shape to A2, over
`attempts.attempt_id` (the primary key) instead of `packets.packet_id`:

```sql
SELECT <the 20 columns> FROM attempts
WHERE (? IS NULL OR attempt_id > ?)
ORDER BY attempt_id ASC
LIMIT ?+1
```

bound as `(after, after, limit)`, using plain `?` placeholders — matching
A2's actual shipped code (which itself deviated from A1-style numbered
placeholders for Python 3.12+ compatibility; this slice follows the real
merged code, not the superseded numbered-placeholder prose from A2's
first planning draft). `next_after`/empty-table/page-boundary semantics
are identical to A2's, substituting `attempt_id` for `packet_id`
throughout.

**Database-unavailable handling:** identical to A2's corrected contract,
reusing the exact same pattern, not new logic: one try/except around
`RuntimeConfig.from_runtime_dir(handler.server.runtime_dir_setting)` and
the connection/query, catching `(RuntimePathError, sqlite3.Error)`
uniformly, responding `503` `{"error":"database_unavailable"}`, closing
any opened connection in a `finally` block. This slice does not touch
that exception-handling shape at all beyond repeating it for the new
table/columns/query — it is proven, reviewed code as of A2's merge.

## Guards, before any database access

Identical to A2's guards 1-4 (loopback allowlist, path/method dispatch
before query parsing, query validation before any `RuntimeConfig`/DB
access, unified exception handling scoped to exactly the
resolve+connect+query span) — this slice adds no new guard category, only
a new route entry exercising the same guard sequence.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `services/maestro/maestro/read_api.py` (extended: the rename described
  above, plus the new `_ATTEMPTS_SNAPSHOT_COLUMNS`, `_ATTEMPTS_SNAPSHOT_QUERY`,
  `_handle_snapshot_attempts`, and one new `_ROUTES` entry)
- `tests/m2_wave_a/test_attempts_snapshot.py` (new file)

No other file changes — in particular, `tests/m2_wave_a/test_packets_snapshot.py`
and `tests/m2_wave_a/test_read_api_scaffold.py` are **not** edited; the
rename is proven non-breaking by running those two existing files
unmodified against the new code (if the rename broke `/snapshot/packets`,
those existing tests would fail). No new dependency. `pyproject.toml` and
`storage.py`/`config.py` are not touched.

The 9 named tests, in `tests/m2_wave_a/test_attempts_snapshot.py`
following the repository's `test_NN_<description>` convention. Fixture
attempts rows are inserted with a raw, FK-pragma-off `sqlite3.connect`
(matching A2's own `test_packets_snapshot.py` fixture-insertion pattern
exactly — that file's `_insert_packet` helper never creates the
referenced `runs`/`work_items` rows either, because the ad-hoc test
connection never issues `PRAGMA foreign_keys=ON`, so SQLite does not
enforce those `REFERENCES` clauses on it). Fixture rows **must** still
satisfy the `attempts_execution_shape_*` triggers and the
`attempt_number`/`attempt_kind`/`correction_for_review_id` `CHECK`
(both are real triggers/constraints, not FK-pragma-gated), so every
fixture-builder call sets a table-shape-legal combination of columns for
its stated `state`:

1. `test_01_empty_table_returns_empty_page` — a freshly migrated, empty
   database returns `200` and exactly `{"attempts":[],"next_after":null}`.
2. `test_02_full_field_projection_planned_and_succeeded` — one fixture
   attempt in `Planned` shape (all 8 nullable execution/result columns
   `NULL`) and one in `Succeeded` shape (all 8 populated, `result_commit`
   a valid 40-hex string); both returned with exactly the 20 named fields,
   `Planned`'s nullable fields rendering as JSON `null`, `Succeeded`'s
   rendering as their real values.
3. `test_03_pagination_next_after_and_exact_page_boundary` — 5 fixture
   attempts with known sorted `attempt_id`s; identical boundary assertions
   to A2's test 3, substituting `attempt_id`/`after` for `packet_id`.
4. `test_04_limit_boundary_values` — identical assertions to A2's test 4
   against `/snapshot/attempts`.
5. `test_05_query_validation_identical_across_both_snapshot_endpoints` —
   the exact same malformed query (each of: unknown key, repeated `limit`,
   `limit=0`, `limit=501`, empty `after`) issued against both
   `/snapshot/attempts` and `/snapshot/packets` produces byte-identical
   `400` bodies — the direct proof that `_validate_snapshot_query`'s
   generalization introduced no divergence between the two routes.
6. `test_06_unknown_path_and_wrong_method_for_attempts_route` — `GET
   /snapshot/attempt` (singular) is `404`; `POST /snapshot/attempts` is
   `405`; bodies match the existing `_NOT_FOUND_BODY`/
   `_METHOD_NOT_ALLOWED_BODY` constants exactly.
7. `test_07_health_and_packets_routes_unaffected_by_generalization` —
   re-runs the exact `/health` byte-identity assertion (A1's test 2) and
   one full `/snapshot/packets` request/response round trip (A2's test 2
   shape), proving the shared-validator rename changed nothing observable
   on either existing route.
8. `test_08_database_unavailable_returns_503` — exactly one sub-case (a
   `runtime_dir` whose directory exists but whose database file does not,
   exercising `sqlite3.Error`). The `RuntimePathError` branch is not
   re-tested here: it is the same shared, unmodified exception-handling
   code A2's `test_08` sub-case (b) already proved for this exact
   `except (RuntimePathError, sqlite3.Error)` clause, and this slice does
   not touch that clause's logic, only which table/query runs inside its
   `try`. Re-proving both sub-cases for every future snapshot endpoint
   would be pure duplication of already-reviewed code, not new coverage —
   this is a deliberate, justified proportionality reduction, not a gap.
9. `test_09_concurrent_requests_do_not_corrupt_pagination` — identical
   shape to A2's test 12 (20 fixture attempts, 10 concurrent threads,
   `?limit=3`, reconstructed order proof), substituting `attempt_id`.

Run the existing 311 named tests (unaffected — the rename is proven
non-breaking by test 7 and by A2's own untouched test file still passing
against the renamed function) plus these 9 (320 total):

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

(`tests/m2_wave_a` now discovers 9+12+9 = 30, 320 overall.) Also run
`python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`; run
exact candidate hygiene before any readiness claim (never `rm -rf` any
`__pycache__` directory in this repository — several are tracked; use
`PYTHONDONTWRITEBYTECODE=1` and `git checkout --` to restore if dirtied).
The one pre-existing, unrelated `tests/m1_01` PyYAML-version environment
failure carried forward from A1/A2 is expected and out of scope.

### M0-D12 bounded quality contract

1. **Protected outcome:** `GET /snapshot/attempts` returns an accurate,
   stable, paginated read-only projection of the `attempts` table with
   all 20 columns and correct nullability, never mutates the database,
   and never crashes the process on a missing/malformed database; the
   `_validate_snapshot_query` generalization introduces zero observable
   change to `/snapshot/packets`.
2. **Operating and threat model:** identical to A2's — a trusted local
   single-user Linux box; the writer service concurrently reading/writing
   the same WAL-mode SQLite file; malformed/missing/repeated/unexpected
   query parameters; a database file or runtime directory that does not
   yet exist; concurrent Atlas-side requests.
3. **Explicit exclusions:** any write path; any endpoint other than
   `/snapshot/attempts`; any ordering other than `attempt_id` ascending;
   any authentication (Owner decision 2026-09-05: none while single local
   owner); any behavior change to `/health` or `/snapshot/packets`; any
   change to `storage.py`'s schema, migrations, triggers, or the writer
   service's own connection handling; re-proving the `RuntimePathError`
   sub-case already covered by A2.
4. **Assurance level:** identical to A1/A2 — practical trusted-local-
   process containment, proportionate to a read-only reporting endpoint
   over data this same trusted process already owns.
5. **Acceptance proof:** the 9 named tests, the 320-test full inventory,
   `compileall`, and exact candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above;
   Python standard library only; reuse of `RuntimeConfig`,
   `SQLiteFoundation`, `canonical_response_json`, and the generalized
   `_validate_snapshot_query` unmodified in behavior; no new dependency.
7. **Proportionality ceiling:** one new route, one new column tuple, one
   new query constant, one rename-and-reuse of existing validation logic,
   one new test file; no event stream, no write path, no additional
   business ordering/filtering beyond what A2 already established as the
   pattern.
8. **Stop and escalation rule:** if a future Wave view needs
   business-ordering, filtering, or a materially different query contract
   than the `limit`/`after` shape now shared by every snapshot endpoint,
   that is a new, separately reviewed slice — not an extension of this
   one after freeze. A discovered proof/contract defect against a frozen
   slice terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
