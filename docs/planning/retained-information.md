# Retained Maestro Information

This file gathers confirmed information from the former planning documents. It does not set priorities, choose future work, approve implementation, or answer unresolved questions. It also does not claim that every boundary below is fully implemented.

## Sources of truth

- A project repository owns that project's architecture, code, rules, reviews, and delivery evidence.
- Maestro's local operational database owns live coordination state such as work claims, leases, attempts, waits, events, evidence, retries, and resource reservations.
- The Maestro service is the only database writer. Atlas and other clients use supported service interfaces.
- The same fact must not have two writable sources of truth.

## Work coordination

- Agent roles use versioned contracts that state their authority, required inputs, expected outputs, and escalation boundary.
- Eligible work is chosen with dependency and resource constraints in view. Independent work may run in parallel. Dependent work, shared writable boundaries, and finite resources are serialized.
- Claims, leases, state changes, evidence, and recovery actions are durable and idempotent so restarts, repeated requests, and stale work can be handled safely.
- Report outcomes as proven, partial, blocked, or unknown. Stored activity is not by itself proof of approval or completion.
- Detailed role and review rules live in [the agent documentation](../agents/).

## Atlas boundary

- Atlas is the operator interface for Maestro's durable state. It is not an operational database or a second editor for project code, plans, or policy.
- Atlas reads supported snapshots and events through the local service and refreshes authoritative state after reconnecting.
- Any Atlas action must map to a named, guarded, version-checked, idempotent service command. Displaying a control does not give Atlas new authority.
- Operator actions and their results are audited.
- Real operational data must be distinguishable from fixtures. Fixture-backed screens are not evidence of working product behavior.
- Atlas must not read the database directly, scrape provider interfaces, expose secrets, or display raw prompts and traces.

## Access and secrets

- Use least-privilege service identities. Personal credentials are not durable runtime credentials.
- Inject secret values at runtime. Store only secret reference names in repositories, manifests, logs, events, evidence, notifications, and user interfaces.
- Missing, expired, or insufficient credentials block the affected operation visibly.
- Webhooks may accelerate updates only when they are authenticated, timestamp-checked, and idempotent. Polling and reconciliation remain the recovery path.

## Backup and recovery

- The accepted local backup target is a dedicated 32 GB USB device.
- Create database snapshots nightly and before schema migration, recovery, or maintenance that could affect data.
- Use SQLite's safe backup mechanism rather than copying a live database file.
- Record a SHA-256 manifest and make backup failures visible.
- Retain 21 daily snapshots and 8 weekly snapshots. Test a restore monthly.
- Restore to a new path, validate it, then reconcile it before use. Never overwrite the live database during restore.
- Do not place credentials, source repositories, or worktrees on the backup device.

## Notifications

- Record a notification durably before attempting external delivery. Atlas shows the same durable notification state.
- Slack is the first external delivery channel.
- Separate action-needed messages from informational messages. Group or rate-limit repeats.
- Delivery failure must remain visible. Acknowledging a message is not approval of the underlying action.
- Notifications must not contain secrets.

## Context, usage, and capacity

- Record context and usage per attempt when the provider supplies the facts.
- Unsupported or unavailable values are reported as unavailable, not zero.
- Estimates are labeled as estimates. Do not convert token counts into a percentage unless the provider supplies the required limit.
- Keep hosted-provider allowance information separate from local machine capacity.
- Do not scrape provider user interfaces for usage data.
- Preserve a durable checkpoint before context pressure makes a safe continuation unreliable.

Related confirmed foundations are summarized in [system foundations](../architecture/system-foundations.md), [local operating safety](../operations/local-operating-safety.md), and [project registration principles](../registrations/project-registration-principles.md).
