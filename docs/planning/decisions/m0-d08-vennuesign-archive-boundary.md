# M0-D08 — VennueSign Archive Boundary

**Status:** Accepted  
**Scope:** Retired VennueSign material and its separation from active work.

## Decision

VennueSign archival material lives in a dedicated, separate private archive
repository. It is not a folder, branch, or working area inside the active
VennueSign repository.

The archive is reference-only. It does not supply active requirements, plans,
tasks, configuration, operational state, or agent instructions. An archived
item may return to active consideration only through an explicit new decision
that identifies the item and records why it is being revived.

## What belongs there

- superseded architecture, plans, roadmaps, specifications, and duplicate
  documents;
- abandoned or replaced UI mockups, prototypes, and design explorations;
- retired agent reports, raw planning captures, obsolete task packets, and
  historical evidence that no longer governs work;
- legacy data-model descriptions and sample/export artifacts that the current
  model replaces; and
- retired Atlas material that is not part of the fresh Maestro reporting path.

## What remains active

- the current approved VennueSign architecture, decisions, plans, milestones,
  handoff, Done Records, code, tests, and release records;
- accepted customer behavior that the renewed architecture must preserve; and
- the live product and operational data required by VennueSign.

Git history stays in its existing repositories. It is not copied into the
archive merely because older commits exist.

## Archive intake guardrails

Before an item is moved, its archive record states its source, reason for
retirement, replacement or current authority, sensitivity classification,
and every active reference that must be removed or redirected. Credentials,
payment/card data, and other prohibited secrets are never archived. Retention
and deletion obligations override preservation when applicable.

Maestro may catalogue archive records for traceability, but it must not use
them as dispatchable authority.
