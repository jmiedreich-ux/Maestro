# Alpha-03 Synthetic Project Discovery — Architecture

## Overview

Extends `maestro run-packet` to process one synthetic discovery fixture,
normalize it into an M0-D02 inventory, produce a proposed binding only when
all facts are complete and non-conflicting, and persist bounded evidence
through the service-owned SQLite boundary. Missing or conflicting facts
trigger immediate `CoordinatorEscalation`; malformed input is rejected before
claim or any runtime mutation.

## Boundary

- **Entry point:** `maestro run-packet --packet path.json --runtime-dir path`
  (`services/maestro/maestro/cli.py:42`)
- **No new CLI subcommands, no real repository, no network access.**

## Components

### `packet_contract.py` — Discovery-scenario dispatch

- Adds `discovery_fixture` field (nullable string) to `ApprovedPacket`.
- `_ALPHA03_SCENARIOS` set: `discovery-complete`, `discovery-missing`,
  `discovery-conflicting`.
- `is_discovery` property returns `True` when scenario is in
  `_ALPHA03_SCENARIOS`.
- Discovery-scenario packets require a non-empty `discovery_fixture` string;
  other packets may omit it.

### `synthetic_discovery.py` — Fixture validation, schema, normalization

| Function | Responsibility |
|----------|---------------|
| `validate_discovery_fixture_name()` | Rejects empty, absolute/traversal/separator paths |
| `load_and_validate_discovery_fixture()` | Opens file under `fixtures/alpha/project-discovery/`, validates resolved path inside root, parses JSON, delegates to `_validate_discovery_schema()` |
| `compute_fixture_digest()` | Raw SHA-256 hex of fixture file |
| `build_inventory()` | Normalizes all seven areas + required leaves. Each leaf receives `confirmed`, `missing`, or `conflicting` status. Returns inventory dict with `areas`, `summary`, `reviewable`. |
| `build_proposed_binding()` | Returns seven-area binding dict only when `reviewable=True`; else `None`. |
| `build_escalation_reason()` | Returns comma-separated dotted paths of non-confirmed leaves; `None` if reviewable. |

Schema validation enforces:
- No unknown top-level, area, or leaf keys.
- Correct types (`string` / `array`) per `_REQUIRED_AREAS`.
- Non-empty string values and array entries; no duplicate array entries.
- Exceptions: `disposition` is `none` or `declared`; `items` always a unique
  string array; `none` requires `[]`; `declared` requires >=1 items.
- Conflicts: dotted path must be a required leaf; each conflict's value array
  has >=2 distinct, type-valid entries.

### `packet_wrapper.py` — Lifecycle integration

- `_scenario_result()` routes discovery scenarios through
  `_discovery_result()`, which loads fixture, builds inventory, binding, and
  digest, then returns a `SyntheticWorkerResult` with discovery fields set.
- `PacketWrapper.run()` validates the fixture name and content _before_ claim.
  After executor run, records discovery evidence via
  `storage.record_discovery_evidence()`.
- `_result_evidence()` extends worker evidence dict with inventory, proposed
  binding, and fixture digest when present.

### `lifecycle.py` — Grading

- `grade_result()` dispatches to `_grade_discovery()` for discovery scenarios.
- Reviewable inventory (all leaves confirmed) produces
  `AWAITING_REVIEW` / `IndependentReview`.
- Non-reviewable inventory produces `REJECTED` / `CoordinatorEscalation` with
  escalation reason from worker log.

### `storage.py` — Discovery evidence table

- Schema version incremented to 2; migration inserts both v1 and v2.
- New table `discovery_evidence(packet_id, inventory_json,
  proposed_binding_json, fixture_digest, created_at)`.
- `record_discovery_evidence()` uses `INSERT OR IGNORE` — idempotent per
  packet_id.
- `_json()` helper serializes with sorted keys and compact separators.

## Data flow

```
CLI -> ApprovedPacket.from_file() -> PacketWrapper.run()
  -> validate_discovery_fixture_name()  (pre-claim)
  -> load_and_validate_discovery_fixture()  (pre-claim)
  -> storage.claim_packet()
  -> executor.execute() -> _discovery_result()
     -> build_inventory(), build_proposed_binding(), compute_fixture_digest()
  -> grade_result() -> _grade_discovery()
  -> storage.record_discovery_evidence()
  -> storage.finish_packet()
  -> RunPacketResult (AwaitingReview or Rejected)
```

## Idempotency

- The existing atomic packet claim is the idempotency key.
- `INSERT OR IGNORE` on `discovery_evidence` prevents duplicate evidence rows.
- Replay after terminal state returns existing status without launching executor.

## Evidence shape

All JSON persisted through `_json()` uses `sort_keys=True, separators=(",",":")`.
Proposed binding contains exactly seven areas with normalized confirmed values;
excludes `conflicts` or inventory status metadata.
