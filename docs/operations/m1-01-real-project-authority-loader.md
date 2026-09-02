# Operating the M1-01 Authority Loader

## Preconditions

- Use a newly created non-live local Git repository, never a live product
  repository.
- Supply the repository path, expected `owner/name` identity, and a full
  40-hex commit object ID.
- The commit must contain a strict UTF-8 `maestro.project.yaml` and its declared
  authority blobs. Its declared local default branch must contain the commit.
- Use the service-owned `SQLiteFoundation`; no client writes SQLite directly.

## Internal invocation

```python
from pathlib import Path

from maestro.config import RuntimeConfig
from maestro.project_authority import ProjectAuthorityLoader
from maestro.storage import SQLiteFoundation

storage = SQLiteFoundation(RuntimeConfig.from_runtime_dir())
loader = ProjectAuthorityLoader(storage)
result = loader.load(
    repository_path=Path("/path/to/non-live-project"),
    source_revision="0123456789abcdef0123456789abcdef01234567",
    expected_repository="owner/non-live-project",
)
```

This is an internal API. There is intentionally no `maestro project` command
in M1-01.

## Interpreting results

- `Reviewable` means every required leaf and authority path was confirmed and
  the database contains one Candidate project, one authority-load run, and one
  event. It does not mean Registered or accepted.
- `Blocked` means the well-formed manifest had one or more missing or
  conflicting facts. The database contains one run and event and no project.
- An exception means input was malformed, the source was not an exact commit,
  a prohibited Git entry was encountered, or a size/read boundary failed. No
  authority-load row or event is written.

Inspect `facts` and `summary`; do not fill a missing value with a default.
Secret reference fields contain identifiers matching
`[A-Z][A-Z0-9_]{2,127}` only. They never contain credential values.

## Recovery and replay

Retry only the exact same request facts. The deterministic idempotency key
returns the original durable result without another project, run, or event.
After service restart, `project_authority_snapshot(request_id)` returns that
same result. A reused request ID or idempotency key with changed facts is an
error and needs a new reviewed operation, not an overwrite.

SQLite transaction or migration failure rolls back completely. Preserve the
exception and database for review; do not alter schema metadata manually.

## Verification

Run from `services/maestro`:

```text
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m unittest discover -s ../../tests/m1_01 -v
python -m compileall -q maestro
```

The M1-01 suite uses real temporary Git repositories and SQLite databases. It
checks pinned-commit isolation, success and failure non-mutation snapshots,
strict manifest rejection, missing/conflicting facts, object and size bounds,
additive migration preservation and rollback, transaction rollback,
idempotency, reopen recovery, and concurrent duplicate calls.
