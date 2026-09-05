# M2 Wave A — Reviews Snapshot Endpoint — Candidate 01

**Slice ID:** `MB-SLICE-M2-A4-REVIEWS-SNAPSHOT-01`
**Status:** `Pending Decision Fidelity Review`
**Base:** `7b6e4e5` (`origin/master`)

## Scope, deliberately minimal

Wave A4 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the fourth
route on the read API process (A1, A2, A3 merged). Exactly one new
endpoint, `GET /snapshot/reviews`, returns a read-only, paginated
projection of the existing `reviews` table — including its two JSON
payload columns, `findings_json` and `coverage_json`, **decoded** into
real JSON structures in the response rather than re-embedded as escaped
strings. No events, no event stream — that is A5. No write path.

This slice reads the real, current `services/maestro/maestro/read_api.py`
(merged A1+A2+A3 state — this contract's description of `_ROUTES`,
`_validate_snapshot_query`, `_VALID_SNAPSHOT_QUERY_KEYS`,
`_ATTEMPTS_SNAPSHOT_COLUMNS`/`_ATTEMPTS_SNAPSHOT_QUERY`/
`_handle_snapshot_attempts`, `canonical_response_json`,
`_ReadApiHTTPServer` is byte-accurate against what is actually in that
file on `origin/master` right now — verified directly) and
`services/maestro/maestro/storage.py`'s `CREATE TABLE reviews`
(unmodified). Controlling authority is the Bootstrap Convergence Policy,
the M2 roadmap, and M0-D01, read from current `origin/master`.

This slice adds no new shared infrastructure beyond what A3 already
generalized (`_validate_snapshot_query` is reused unmodified, as-is, with
zero further changes — this slice does not touch that function or its
constant at all).

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-A4-REVIEWS-SNAPSHOT-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:7b6e4e5"]` |

## Exact route contract

`GET /snapshot/reviews[?limit=<n>][&after=<review_id>]`

Query-string parsing, validation, defaults, and the four literal `400
invalid_query` `detail` strings are byte-for-byte identical to
`/snapshot/packets` and `/snapshot/attempts` — reusing
`_validate_snapshot_query` completely unmodified, called exactly the same
way `_handle_snapshot_attempts` already calls it.

**Field renaming (deliberate, not a 1:1 column-name projection like A2/A3):**
`reviews` stores two payload columns as JSON-encoded `TEXT`:
`findings_json` (a JSON array) and `coverage_json` (a JSON object), each
enforced by the schema's own `CHECK(json_valid(...) AND json_type(...)=...)`.
This slice decodes both with `json.loads` before building the response, so
the wire value is the actual array/object, not an escaped string
containing one. Naming the response fields `findings_json`/`coverage_json`
while their values are already-decoded JSON (not JSON-encoded strings)
would be misleading — a field suffixed `_json` should be a JSON-encoded
string, and this one is not. This slice therefore names the response
fields `findings` and `coverage` instead — the only two fields in this
endpoint's response whose name differs from the underlying database
column.

Success response, `200`, `Content-Type: application/json`, via the
existing `canonical_response_json` (unmodified) — which recursively
`sort_keys`s nested objects, so each decoded `findings` array element's
own keys and `coverage`'s own keys are also alphabetically ordered in the
wire bytes, exactly like every other nested object this service has ever
emitted:

```json
{"next_after":"<review_id-or-null>","reviews":[{"attempt_id":null,"base_commit":"...","correction_number":0,"coverage":{},"created_at":"...","findings":[],"head_commit":"...","packet_id":"...","result":"Approve","review_id":"...","review_kind":"IndependentImplementation","reviewer_instance":"...","reviewer_role":"..."}]}
```

Exactly these 13 fields per review (verified alphabetical wire order,
matching `sort_keys=True`): `attempt_id`, `base_commit`,
`correction_number`, `coverage`, `created_at`, `findings`, `head_commit`,
`packet_id`, `result`, `review_id`, `review_kind`, `reviewer_instance`,
`reviewer_role`. Every `reviews` column is exposed; there is no oversized
or internal-only column to exclude on this table (unlike `packets`).

**Nullability, verified directly against the real `CREATE TABLE reviews`
(not assumed — this exact class of claim was wrong in A3's first
planning draft and corrected there; getting it right the first time
here):**

- `attempt_id` is declared only `TEXT REFERENCES attempts(attempt_id)` —
  no `NOT NULL` — genuinely nullable; renders as JSON `null` when the
  column is `NULL` (a review that predates or is not tied to a specific
  attempt row is schema-legal).
- `review_id` is declared only `TEXT PRIMARY KEY CHECK(...)` — like
  `attempts.attempt_id` before it, a `TEXT` primary key does **not**
  imply `NOT NULL` in SQLite (that implication applies only to
  `INTEGER PRIMARY KEY`). `review_id` is therefore schema-nullable too,
  though — exactly as with `attempts.attempt_id` — no real writer code
  path ever supplies a `NULL` `review_id`, and no test in this slice
  asserts it can never be `null`.
- The remaining 11 fields (`base_commit`, `correction_number`,
  `coverage`, `created_at`, `findings`, `head_commit`, `packet_id`,
  `result`, `review_kind`, `reviewer_instance`, `reviewer_role`) carry an
  explicit column-level `NOT NULL` (`findings`/`coverage` inherit this
  from their source columns `findings_json`/`coverage_json`, both
  declared `NOT NULL`) and never render as `null`. An empty findings
  array (`[]`) or empty coverage object (`{}`) is a normal, valid,
  non-null value distinct from `null`.

Query semantics: identical keyset-pagination shape to A2/A3, over
`reviews.review_id` (the primary key):

```sql
SELECT <the 11 raw DB columns, findings_json and coverage_json among them>
FROM reviews
WHERE (? IS NULL OR review_id > ?)
ORDER BY review_id ASC
LIMIT ?+1
```

bound as `(after, after, limit)`, plain `?` placeholders — matching A2's
and A3's real shipped style, not A1's superseded numbered-placeholder
prose. After fetching, `findings_json`/`coverage_json` are decoded via
`json.loads` and re-keyed to `findings`/`coverage` before the row
dict is built; every other column is projected by its own name unchanged.
`next_after`/empty-table/page-boundary semantics are identical to A2/A3,
substituting `review_id` for `packet_id`/`attempt_id`.

**Database-unavailable handling:** identical, unmodified pattern —
`except (RuntimePathError, sqlite3.Error)` → `503`
`{"error":"database_unavailable"}`, connection closed in `finally`. This
slice adds no new failure mode: a `json.loads` failure on
`findings_json`/`coverage_json` is **not** possible in practice (the
schema's own `CHECK(json_valid(...))` constraint guarantees every stored
value is valid JSON before it can ever be committed), so this slice adds
no `json.JSONDecodeError` handling — decoding a column the database
itself guarantees is valid JSON is treated as infallible, the same way
this codebase already treats other `CHECK`-guaranteed invariants (e.g.
`packets.owned_paths_json`'s `json_valid` guarantee is never re-validated
by a reader either).

## Guards, before any database access

Identical to A2/A3's guards 1-4 (loopback allowlist, path/method dispatch
before query parsing, query validation before any `RuntimeConfig`/DB
access, unified exception handling scoped to exactly the
resolve+connect+query span) — this slice adds no new guard category, only
a new route entry exercising the same guard sequence, plus the
decode-and-rekey step described above (which cannot fail, per the
`CHECK` guarantee, and is therefore not itself a guard).

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `services/maestro/maestro/read_api.py` (extended: new
  `_REVIEWS_SNAPSHOT_COLUMNS`, `_REVIEWS_SNAPSHOT_QUERY`,
  `_handle_snapshot_reviews`, one new `_ROUTES` entry — `import json` is
  already present in this file from A1's `canonical_response_json`, so no
  new import is needed)
- `tests/m2_wave_a/test_reviews_snapshot.py` (new file)

No other file changes — `test_packets_snapshot.py`,
`test_attempts_snapshot.py`, and `test_read_api_scaffold.py` are **not**
edited. No new dependency. `pyproject.toml` and `storage.py`/`config.py`
are not touched.

The 9 named tests, in `tests/m2_wave_a/test_reviews_snapshot.py`
following the repository's `test_NN_<description>` convention. Fixture
review rows are inserted with a raw, FK-pragma-off `sqlite3.connect`
(matching A2/A3's established pattern — fake `packet_id`/`attempt_id`
values need no real referenced rows). Fixture rows must still satisfy the
real `CHECK` constraints (`review_kind IN ('Integration',
'IndependentImplementation')`, `result IN ('ValidateOnly','Assemble',
'NeedsReplan','Approve','RequestChanges','Comment')`,
`correction_number IN (0,1)`, `findings_json`/`coverage_json` must be
valid JSON of the required array/object type) and the real
`UNIQUE(packet_id, review_kind, reviewer_instance, head_commit,
correction_number)` constraint — bulk-fixture tests (pagination,
concurrency) must vary at least one of those five columns per row (e.g. a
distinct 40-hex `head_commit` per row, following A2's `COMMIT_A`/`COMMIT_B`-
style pattern extended to as many distinct values as fixture rows
require) to avoid a real `IntegrityError`, exactly the class of pitfall
A3's fixtures already had to navigate for `attempts.UNIQUE(packet_id,
attempt_number)`.

1. `test_01_empty_table_returns_empty_page` — a freshly migrated, empty
   database returns `200` and exactly `{"next_after":null,"reviews":[]}`.
2. `test_02_full_field_projection_decoded_findings_and_null_attempt_id` —
   two fixture reviews: one with a non-trivial `findings_json` array
   (at least one finding object with more than one key, to prove nested
   key sorting) and a non-empty `coverage_json` object, and a real
   `attempt_id`; one with `findings_json="[]"`, `coverage_json="{}"`, and
   `attempt_id=NULL`. Both returned with exactly the 13 named fields;
   the first row's `findings`/`coverage` are the actual decoded
   structures (not strings) with their own keys alphabetically ordered;
   the second row's `attempt_id` renders as JSON `null` and its
   `findings`/`coverage` render as `[]`/`{}` (empty, not null).
3. `test_03_pagination_next_after_and_exact_page_boundary` — 5 fixture
   reviews with known sorted `review_id`s (each with a distinct
   `head_commit` to satisfy the `UNIQUE` constraint); identical boundary
   assertions to A2/A3's test 3, substituting `review_id`/`after`.
4. `test_04_limit_boundary_values` — identical assertions to A2/A3's
   test 4 against `/snapshot/reviews`.
5. `test_05_query_validation_identical_across_all_three_snapshot_endpoints`
   — the exact same malformed query (unknown key, repeated `limit`,
   `limit=0`, `limit=501`, empty `after`) issued against
   `/snapshot/reviews`, `/snapshot/attempts`, and `/snapshot/packets`
   produces byte-identical `400` bodies across all three.
6. `test_06_unknown_path_and_wrong_method_for_reviews_route` — `GET
   /snapshot/review` (singular) is `404`; `POST /snapshot/reviews` is
   `405`; bodies match the existing `_NOT_FOUND_BODY`/
   `_METHOD_NOT_ALLOWED_BODY` constants exactly.
7. `test_07_other_routes_unaffected_by_new_route_addition` — re-runs the
   `/health` byte-identity assertion and one full round trip each for
   `/snapshot/packets` and `/snapshot/attempts`, proving adding the third
   route changed nothing observable on the other three.
8. `test_08_database_unavailable_returns_503` — exactly one sub-case (a
   `runtime_dir` whose directory exists but whose database file does
   not, exercising `sqlite3.Error`) — the `RuntimePathError` branch is
   the same shared, unmodified exception-handling code A2's test already
   proved; not re-tested here, matching A3's established, justified
   reduction.
9. `test_09_concurrent_requests_do_not_corrupt_pagination` — identical
   shape to A2/A3's concurrency test (20 fixture reviews, each with a
   distinct `head_commit`, 10 concurrent threads, `?limit=3`,
   reconstructed-order proof), substituting `review_id`.

Run the existing 320 named tests (unaffected — no shared function is
modified by this slice) plus these 9 (329 total):

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

(`tests/m2_wave_a` now discovers 9+12+9+9 = 39, 329 overall.) Also run
`python -m compileall -q maestro ../../tests/m2_wave_a` from
`services/maestro` with an external, isolated `PYTHONPYCACHEPREFIX`; run
exact candidate hygiene before any readiness claim (never `rm -rf` any
`__pycache__` directory in this repository — several are tracked; use
`PYTHONDONTWRITEBYTECODE=1` and `git checkout --` to restore if dirtied).
The one pre-existing, unrelated `tests/m1_01` PyYAML-version environment
failure carried forward from A1/A2/A3 is expected and out of scope.

### M0-D12 bounded quality contract

1. **Protected outcome:** `GET /snapshot/reviews` returns an accurate,
   stable, paginated read-only projection of the `reviews` table with all
   13 fields, `findings`/`coverage` correctly decoded to real JSON
   structures (not double-encoded strings) with correct nullability for
   `attempt_id`, never mutates the database, and never crashes the
   process on a missing/malformed database.
2. **Operating and threat model:** identical to A2/A3's — a trusted local
   single-user Linux box; the writer service concurrently
   reading/writing the same WAL-mode SQLite file; malformed/missing/
   repeated/unexpected query parameters; a database file or runtime
   directory that does not yet exist; concurrent Atlas-side requests.
3. **Explicit exclusions:** any write path; any endpoint other than
   `/snapshot/reviews`; any ordering other than `review_id` ascending;
   any authentication (Owner decision 2026-09-05: none while single
   local owner); any behavior change to `/health`, `/snapshot/packets`,
   or `/snapshot/attempts`; any change to `storage.py`'s schema,
   migrations, or the writer service's own connection handling;
   defensive handling of a `findings_json`/`coverage_json` decode failure
   that the schema's own `CHECK` constraint already makes impossible;
   re-proving the `RuntimePathError` sub-case already covered by A2.
4. **Assurance level:** identical to A1/A2/A3 — practical trusted-local-
   process containment, proportionate to a read-only reporting endpoint
   over data this same trusted process already owns.
5. **Acceptance proof:** the 9 named tests, the 329-test full inventory,
   `compileall`, and exact candidate hygiene, all passing.
6. **Implementation boundary:** exactly the two writable paths above;
   Python standard library only (`json` already imported); reuse of
   `RuntimeConfig`, `SQLiteFoundation`, `canonical_response_json`, and
   `_validate_snapshot_query` unmodified; no new dependency.
7. **Proportionality ceiling:** one new route, one new column tuple, one
   new query constant, one small decode-and-rekey step, one new test
   file; no event stream, no write path, no additional business
   ordering/filtering beyond the shared `limit`/`after` pattern.
8. **Stop and escalation rule:** if a future Wave view needs
   business-ordering, filtering, or a materially different query contract
   than the shared `limit`/`after` shape, that is a new, separately
   reviewed slice — not an extension of this one after freeze. A
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
