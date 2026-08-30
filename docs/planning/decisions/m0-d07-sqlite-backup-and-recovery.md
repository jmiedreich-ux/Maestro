# M0-D07 — SQLite Backup and Recovery

**Status:** Accepted  
**Scope:** Maestro's local SQLite operational database on the Linux AI box.

## Decision

A dedicated 32GB USB flash drive is Maestro's initial recovery-copy target.
It holds Maestro SQLite snapshots and their verification manifests only. It
never holds credentials, source code, or project worktrees.

Maestro creates a consistent SQLite snapshot:

- nightly while the USB drive is available;
- immediately before every database schema migration; and
- before a planned recovery or maintenance action that could change the
  operational database.

Each snapshot has a SHA-256 verification manifest. A failed copy, failed hash,
missing drive, or lack of free space creates a durable backup-health failure
and a Slack notification when notification delivery is configured. Atlas shows
that condition live. A backup problem never becomes invisible.

## Retention and verification

The recovery drive retains the newest 21 daily snapshots and 8 weekly
snapshots. An older snapshot is deleted only after its replacement has been
written and verified. If this retention would exceed the available drive space,
Maestro retains the verified copies already present and raises backup health
rather than silently deleting the only usable recovery point.

Once each month, Maestro restores the newest verified snapshot into a fresh
temporary database, runs SQLite integrity checks, and verifies that the durable
run, packet, attempt, event, evidence, notification, and wait records can be
read. The test result is retained as operational evidence.

## Recovery procedure

1. Stop the coordinator from making new state changes.
2. Preserve the damaged database and its logs for investigation; do not
   overwrite it.
3. Select the newest verified USB snapshot and restore it to a new database
   path.
4. Run integrity and read checks before making the restored database active.
5. Start Maestro in recovery mode. It reconciles repository and worker facts
   idempotently before taking the next safe action.
6. Record the recovery event and surface it in Atlas and notifications.

A restore is never automatic. It requires coordinator/owner action because
reconciliation may expose a real ownership or execution question.

## Guardrails

- Atlas remains reporting-only throughout backup or recovery.
- GitHub/repository records remain the authority for code and engineering
  history; the USB drive restores Maestro's operational memory.
- A missing USB drive does not erase live state or trigger an unsafe shutdown,
  but the backup-health failure remains visible until a verified copy succeeds.
- Implementation must use SQLite's safe backup mechanism; copying a live
  database file directly is not an acceptable snapshot method.
