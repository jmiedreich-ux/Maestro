# M0-D01 — Maestro Operational Database

**Status:** Accepted — amended to add Atlas operator actions (2026-09-05)
**Decision owner:** Maestro project owner  
**Scope:** V1 operating foundation only; no runtime implementation is authorized by this record.

## Decision

Maestro V1 will use one local SQLite database on the Linux AI box as its durable operational memory **and immediate operational source for local Atlas**.

Maestro's local service is the only database writer. Atlas reads current operational state from that service and, for the specific operator actions named below, submits them through the service's own guarded command API — the same API any other trusted caller uses. Atlas never opens or edits the database directly, never bypasses that guarded API, and never changes code or routing/policy outside a named, reviewed command. Project repositories and GitHub remain authoritative for approved plans, code, PRs, reviews, and CI, but they are **not** Atlas's refresh mechanism.

### Atlas operator-action authority

Atlas is the operator surface for the human and Architect decision points Maestro's process already defines: Owner decisions, Architect-ruling review, and crash/recovery choices, submitted through the service's guarded, idempotent command API — the same API the CLI and every other trusted caller use, with the same version-checked, idempotent, fully-audited command path. Atlas gains no authority beyond an already-named, already-reviewed command: it cannot edit code, alter routing or policy, merge, or act through any other path. An action becomes available through Atlas only once its own guarded command exists and has passed the same Decision Fidelity and implementation review every other Maestro capability requires; until then, Atlas shows the fact as a recorded record, not a control. The synthetic Alpha packet wrapper remains invoked locally through `maestro run-packet`, under the approved packet and Decision Fidelity Reviewer gates.

## Why this fits V1

- One coordinator and one AI box do not need distributed-database complexity.
- SQLite makes worker status, waits, evidence, and recovery durable across a chat/session restart or machine reboot.
- It is private to the local box and does not require exposing a database service.
- A later move to Postgres remains possible if Maestro needs multiple machines, remote Atlas access, or concurrent coordinators.

## Database boundary

| Authority | Lives here |
|---|---|
| Project repository / GitHub | Product decisions, feature records, approved work graph, code, PRs, reviews, CI |
| Maestro database | Project registration, observed repository facts, graph projection, runs, packet leases, attempts, worker events, evidence, waits, retries, notifications, and resource locks |
| Atlas | Live read projection, plus the named, reviewed operator-action commands as each becomes available; no independent durable truth and no authority beyond a named guarded command |

## Immediate operational visibility

Atlas must show the most recent Maestro state as soon as the coordinator records it. It does not wait for a GitHub write, a CI result, a scheduled build, or a static-site refresh.

Examples of immediately visible operational facts are:

- a packet being assigned or starting;
- the selected local/cloud agent and model;
- known waiting state, expected completion, timeout, and next permitted action;
- worker output/evidence arrival;
- a verification or review gate beginning, passing, failing, or requesting rework;
- a retry, resource lock, blocker, coordinator recovery, or notification.

GitHub/CI observations are also ingested into the database when they arrive. They refine the live state—for example, `CI passed` or `merge observed`—but their arrival never prevents Atlas from showing all newer Maestro-known facts.

The service exposes a local read API for Atlas. Atlas loads a current snapshot through that API and receives live state updates through a local event stream while open. If the event connection drops, Atlas reconnects and requests a fresh snapshot. This design does not rely on GitHub Actions, CI completion, or a static-site deployment.

## V1 logical records

| Record | Purpose |
|---|---|
| `projects` | Registered project identity, adapter/version, repository/default branch, and policy reference |
| `work_items` | Projection of approved milestone/packet identifiers and their observed planning state |
| `runs` | One Maestro coordination run for one approved milestone |
| `packets` | Bounded work packet, ownership, dependencies, validation, and planned routing |
| `leases` | Current agent/worker claim, expiry, and idempotency key |
| `attempts` | Actual executor/model/runtime, timestamps, result, retry count, and commit facts |
| `events` | Ordered observed and commanded lifecycle events, with correlation and deduplication keys |
| `evidence` | Commands, outputs, artifacts, commit SHA, CI/review result, and retention reference |
| `waits` | Expected completion, timeout, next permitted action, and current blocking gate |
| `resource_locks` | Serialized use of local-model inference, verification, browser, and database-container capacity |
| `notifications` | Sent/acknowledged status messages and failures |

## Operating rules

1. Enable SQLite write-ahead logging (WAL) and use short transactions.
2. Every state change records an event and has an idempotency key.
3. The coordinator rereads authoritative repository and database facts before retrying a stale or failed action.
4. The database file stays on encrypted local storage with owner-only permissions; no direct network listener is introduced for V1.
5. Secrets are never stored as command/event/evidence text. Records may store only a secret reference name and provider.
6. Atlas may submit only the named, reviewed operator-action commands described above; it performs no coordination outside those commands, and every action it takes is durably recorded exactly like a CLI-issued one, under the same approved project policy.

## Backup and recovery baseline

- Create an atomic SQLite backup once each day and before a Maestro service upgrade or database migration.
- Retain daily backups for **90 days** as the proposed V1 default.
- Retain structured run history and evidence metadata for 90 days; artifacts may use a separate project retention policy.
- Verify restore into an isolated test copy at least monthly; record the result as Maestro evidence.
- A restore never overwrites the live database in place. Stop the service, preserve the failed copy, restore to a new path, validate integrity, then perform a controlled switchover.

## V1 non-goals

- No remote database access.
- No Postgres cluster, high availability, or multi-coordinator election.
- No direct Atlas database connection.
- No automatic data deletion outside the defined retention process.

## Remaining M0 confirmation

The **90-day** local backup and structured-history retention remains the proposed default to confirm or replace before M0 is accepted.

## Atlas operator-action amendment — Owner-approved 2026-09-05

This decision's earlier restriction — Atlas strictly read-only, never a
command caller, with the `command_requests` record removed entirely — is
superseded. Atlas is the operator surface for the human and Architect
decision points Maestro's process already defines: Owner decisions,
Architect-ruling review, and crash/recovery choices. It submits those
actions through the service's own guarded, idempotent command API, the
same one every other trusted caller uses.

This does not reopen unrestricted control. Atlas still cannot open or edit
the database directly, change code, alter routing or policy, merge, or act
through any path other than a named, independently reviewed guarded
command. Each action is available through Atlas only once its own guarded
command exists and has passed the same Decision Fidelity and
implementation review every other Maestro capability requires; until a
given action's command exists, Atlas continues to show the underlying fact
as a read record, not a control.

Historical records that describe Atlas as read-only (completed Alpha
packets, earlier planning captures, proposed-but-unbuilt surfaces) reflect
the state at the time they were written and are not rewritten. This
amendment controls Atlas's architecture going forward.
