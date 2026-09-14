# Maestro Repository Handoff

## Start here

- [Repository working rules](../../AGENTS.md) and [additional agent instructions](../../CLAUDE.md).
- [Project overview](../../docs/maestro-project-overview.md) — authoritative source entry and current-state evidence.
- [Architecture](../../docs/maestro-architecture.md) — system behavior and remaining mechanisms.
- [Runtime Service declaration](../../docs/maestro-runtime-service-project-milestones.md), [CLI declaration](../../docs/maestro-cli-project-milestones.md), and [registration declaration](../../docs/maestro-registration-project-milestones.md).
- [Planning Guide and templates](../../docs/planning-guide/README.md).
- [Maestro Project Architect — Software Architecture Role](../../docs/agents/architecture-agent.md).
- [Independent Fidelity Reviewer](../../docs/agents/decision-fidelity-reviewer.md).

## Where the discussion paused

The shared adapter behavior is documented in [Model Execution Adapters](../../docs/maestro-architecture.md#model-execution-adapters). The first integration remains the Maestro Project Architect performing registration, followed by an independent Fidelity Reviewer.

Claude Code or Codex can run either role, with separate exact model/version selections. The architect selection is explicit at registration initiation; no particular model version has been chosen. Workspaces, assignment snapshots, clarification follow-ups, progress, completion, cancellation, recovery, and retention behavior are agreed.

The adapter contracts now specify Codex App Server over stdio, Claude Code print-mode streaming, explicit assessment artifacts, separate assignment/run identities, protected inputs, process supervision, internal retry accounting, technical configuration, and the durable Retry activity request. Official documentation supports the selected tool interfaces; installed compatibility and connected behavior remain unverified.

Package records and locations, exact candidate references, publication operations, confirmation receipts, and SQL activation/recovery are now defined in the architecture. Idle-only enforcement and the per-attempt planning-review configuration are now defined. Cross-document alignment is complete, with corrections applied and independently rechecked. The Runtime Service declaration now gives service installation, durable records, API/event delivery, and agent supervision their own delivery outcomes. CLI owns the terminal; registration owns its process and package behavior. Runtime interfaces and CLI are implemented before registration integration; shared final acceptance uses real registration journeys. Next: review these Runtime Service outcomes before designing development milestones and work packets. Live adapter verification is deferred to implementation and is not required for the current architecture documentation work. Continue documenting and committing the design without attempting AI box checks at this stage.

Resolve routine technical details as the software architect and document their reasons; seek Owner input only at the role's stated authority boundaries.

## Decisions to preserve

- The architect is a software architecture role responsible for technical coherence and usable connected outcomes. It both assesses sources and prepares the candidate package.
- Routine technical choices within scope do not need Owner approval. Changed outcomes, expanded scope, conflicts with agreed requirements, reserved decisions, and final registration confirmation retain their agreed authority boundaries.
- The independent reviewer checks both assessment and candidate fidelity. Routine corrections go to the architect; justified material disagreement at the review limit reaches the Owner. No extra review loop was added.
- Role inputs and the [structured registration response](../../docs/maestro-architecture.md#registration-agent-response-contract) are already defined. Do not reopen them as unanswered questions.
- The adapter runs an agent tool; the service owns validation, durable records, budgets, question routing, and registration state. One adapter may run different roles in separate independent runs.
- For later execution work packets, the agent returns its implementation plan after reading the packet and then continues. Maestro records and displays it. No plan-review, approval, or pause gate is included now; such a gate is only a possible future addition.
- CLI implementation precedes registration development. Final connected CLI acceptance uses real initial registration integration. Re-registration display evidence belongs to REG-PM2 — Update a registration without losing approved history.
- Initial delivery remains CLI-only; the command center is excluded.

## Remaining design

Registration architect and reviewer runs each default to 30 minutes, configured separately; other planning and execution assignments do not inherit that setting. The automatic technical recovery maximum is two attempts per assignment, separate from fidelity reviews. Failure classification determines whether another run is appropriate. Timeouts pause after confirmed stopping. Manual retry follows intervention, permits one run, and preserves the automatic budget and history. Unknown original-run status blocks replacement. Workspaces remain until explicit removal and cannot be removed while needed by a run, review, or recovery. See the architecture for authoritative rules.

Broader implementation-review authority, coding corrections, merge authority, and development completion remain provisional for separate Execution design. Registration needs agents to perform its own work, but its controls must not be treated as approval of general Execution policy. Executable package schemas, physical SQL tables, publication operations, and adapter verification belong to implementation of the defined contracts. Technical adapter configuration is defined in `/etc/maestro/agents.toml`. Routine technical settings can be resolved by the architect within the agreed scope.

The current documents specify outcomes and behavior, not implementation completion. Existing code is assessed during relevant development preparation; registration only checks claimed dependencies as needed.

## Working rules

Commit authorized changes directly to `master`; no branches or pull requests. Use plain, concise wording and include subjects with coded references. Architecture explains behavior; declarations explain delivery outcomes. Keep each fact authoritative in one place and use references elsewhere.

Apply review corrections to the main documents. Do not create or present separate review reports unless requested. Resume from the current documents and this handoff, without reopening settled decisions.
