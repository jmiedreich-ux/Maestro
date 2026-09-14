# Maestro Information Review

This file preserves consolidated reference information. The new design is in [Maestro Architecture](maestro-architecture.md); this reference material does not automatically define that architecture.

## System purpose

Maestro is a project-neutral system for controlled AI-assisted engineering work. The repository contains a local Python service, SQLite-backed operational state, repository discovery and registration components, agent-role definitions, and the Reporting and Command Interface.


## Sources of truth

A joined project repository owns that project's architecture, code, rules, reviews, and delivery evidence.

Maestro's local operational database owns live coordination state. This includes work claims, leases, attempts, waits, events, evidence, retries, notifications, and resource reservations.

The Maestro service is the only database writer. The Reporting and Command Interface and other clients use supported service interfaces. The same fact must not have two writable sources of truth.

Agent responsibilities and review boundaries are defined separately in the [agent role library](agents/).

## Local service and operational data

Maestro uses a local Python service and SQLite. The runtime-data directory is configurable and defaults to the repository's `var/` directory.

SQLite uses foreign-key enforcement, write-ahead logging, versioned schema migrations, transactional writes, and concurrency controls where needed.

Durable operations use stable request identities. Repeating an unchanged request returns the existing result or rejects conflicting reuse. A request with changed identifying facts must be recorded as a new reviewed request.

Claims, leases, state changes, evidence, and recovery actions are durable and idempotent so restarts, repeated requests, timeouts, and stale work can be handled safely.

Do not edit SQLite records, schema metadata, or migration history manually.

## Packet processing and evidence

Packet inputs are validated before durable state changes.

Claims, execution records, results, checks, evidence, and handoffs are stored so work can be inspected after a process restart.

Execution may be restricted to approved paths and named checks. Invalid configuration, unauthorized paths, missing evidence, and failed checks are controlled outcomes. They must not be reported as successful work.

Report outcomes as proven, partial, blocked, or unknown. A stored result proves only what was recorded; it does not by itself prove approval, completion, or successful product operation.

## Project discovery and registration

The following retained registration details are reference material, not fixed requirements for the [evolving registration process](maestro-architecture.md#planning-evolving-registration-concepts).

Registration connects Maestro to a project without transferring ownership of the project's architecture, plans, code, or delivery rules.

Discovery is read-only and tied to an exact repository revision. It must not change the source repository, working tree, or Git state.

Repository facts are recorded as confirmed, missing, or conflicting. Missing information is not guessed. A proposed project binding is produced only when required facts are complete and conflict-free.

The loader reads authority files from the pinned Git commit rather than mutable index or working-tree content. It rejects unsafe paths, unsupported Git objects, unknown fields, malformed references, and oversized inputs before related project state is written.

Registration must identify:

- The project, repository, default branch, and exact source revision.
- Authoritative architecture, planning, work-graph, handoff, and working-rule paths.
- Build, verification, integration, and user-interface verification commands.
- Branch, review, merge, acceptance, deployment, and rollback rules.
- Agent roles, execution routes, resource limits, notifications, and declared exceptions.
- Environment and secret reference names.

Registration is blocked when required facts are missing, conflicting, unsafe, or not tied to an exact revision.

The Owner must approve a proposed registration before it becomes active. Registration confirms that Maestro can understand and coordinate the project safely. It does not approve implementation work.

## Project-manifest contract

This retained manifest contract is reference material. It does not define the future Maestro Planning Guide or registration-file format.

The project manifest uses schema version 1, rejects unknown properties, and requires every top-level section below.

| Section | Required information |
|---|---|
| Identity | Project identifier, plain name, repository, default branch, adapter version, and process version |
| Authority | Architecture paths, planning paths, work-graph path, handoff path, working-rule path, and task-issue convention |
| Delivery | Branch policy, pull-request policy, merge policy, acceptance authority, deployment policy, and rollback policy |
| Verification | Build commands, integration commands, user-interface verification commands, evidence rules, and handling for unverified work |
| Routing | Specialist overlays, worker routes, Integration route, independent-review route, and quality-assurance policy |
| Operations | Environment references, secret references, resource locks, and notification policy |
| Exceptions | Whether exceptions are absent or declared, plus the declared items |

Existing validation rules:

- The project identifier starts with a lowercase letter, contains only lowercase letters, numbers, and hyphens, and is between 3 and 64 characters.
- The repository uses an `owner/name` form and is limited to 512 characters.
- General text values are non-empty, trimmed, free of control characters, and limited to 512 characters.
- Repository paths are relative. Absolute paths, backslashes, repeated separators, and path segments for the current directory, parent directory, or Git metadata are rejected.
- Lists contain unique values. Required authority-path lists cannot be empty.
- Secret references use uppercase environment-style names and contain no secret values.
- Acceptance authority is either the Project Architect or the Owner.
- When exceptions are absent, the exception list is empty. When exceptions are declared, at least one item is required.

## Reporting and Command Interface boundary

The Reporting and Command Interface is the operator interface for Maestro's durable state. It is not the operational database and is not a second editor for project code, plans, or policy.

The Reporting and Command Interface reads supported snapshots and events through the local service and refreshes authoritative state after reconnecting. It must not read SQLite directly.

Any Reporting and Command Interface action must map to a named, guarded, version-checked, idempotent service command. Displaying a control does not give the Reporting and Command Interface new authority. Operator actions and their results are audited.

The Reporting and Command Interface must distinguish live operational data from demonstration data. It must not scrape provider interfaces, expose secrets, or display raw prompts and traces.

## Access and secrets

Use least-privilege service identities. Personal credentials are not durable runtime credentials.

Secret values are injected at runtime. Repositories, manifests, logs, events, evidence, notifications, and user interfaces store only secret reference names.

Missing, expired, or insufficient credentials block the affected operation visibly.

Authenticated, timestamp-checked, idempotent webhooks may accelerate updates. Polling and reconciliation remain the recovery path.

## Local operating safety

Use an explicit runtime-data directory under the repository's `var/` directory unless an approved configuration defines another safe location.

Delete only a specifically named disposable runtime directory. Never broadly delete `var/` or another shared path. Preserve the database and error details after a failed operation.

Use a non-live repository for any verification that may alter files or Git state. Reject unsafe paths, malformed configuration, unsupported Git objects, and oversized inputs.

## Backup and recovery

SQL backup and restore are out of scope. Ordinary service restart and recorded-operation recovery remain defined in the [architecture](maestro-architecture.md).

## Notifications

Record a notification durably before attempting external delivery. The Reporting and Command Interface shows the same durable notification state.

Slack is the first external delivery channel. Separate action-needed messages from informational messages and group or rate-limit repeats.

Delivery failure remains visible. Acknowledging a notification is not approval of the underlying action. Notifications never contain secrets.

## Context, usage, and capacity

Record context and usage per attempt when the provider supplies the facts.

Unsupported or unavailable values are reported as unavailable, not zero. Estimates are labeled. Token counts are not converted into percentages unless the provider supplies the required limit.

Hosted-provider allowance information remains separate from local-machine capacity. Provider user interfaces are not scraped for usage data.

Preserve a durable checkpoint before context pressure makes safe continuation unreliable.

