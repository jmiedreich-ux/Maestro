# Maestro Repository Handoff

## Start here

- [Repository working rules](../../AGENTS.md) and [additional agent instructions](../../CLAUDE.md).
- [Project overview](../../docs/maestro-project-overview.md) — authoritative source entry and current-state evidence.
- [Architecture](../../docs/maestro-architecture.md) — system behavior and remaining mechanisms.
- [Runtime Service declaration](../../docs/maestro-runtime-service-project-milestones.md), [CLI declaration](../../docs/maestro-cli-project-milestones.md), and [registration declaration](../../docs/maestro-registration-project-milestones.md).
- [Architecture-loop declaration](../../docs/maestro-architecture-loop-project-milestones.md).
- [Planning Guide and templates](../../docs/planning-guide/README.md).
- [Maestro Project Architect — Software Architecture Role](../../docs/agents/architecture-agent.md).
- [Independent Fidelity Reviewer](../../docs/agents/decision-fidelity-reviewer.md).

## Where the discussion paused

The architecture-loop agreements are saved in [Architecture](../../docs/maestro-architecture.md#architecture-loop) and the [architecture-loop declaration](../../docs/maestro-architecture-loop-project-milestones.md).

Settled behavior includes `/architecture start` and `/architecture`, selected-project and idle-only entry, exact tool/model selection, persistent-session replacement from verified records, active-run limits, fixed output names and paths, manifest hashes, separate working/confirmed references, stale-data rejection, targeted review, exact-version confirmation, interrupted-operation recovery, cancellation/restart without budget resets, and later-registration invalidation.

Specialist roles use `role-<role-title>.md` beside source, with assigned `context.md` and optional `memory.md`. The architect owns the role and starting context; specialists maintain verified knowledge without changing authority or overwriting a newer file. Wrapper errors return to the architect for bounded technical correction before independent review.

Next: finish exact adapter continuation/event and structured response contracts and executable schema definitions, then check declaration readiness. Do not ask again about settled storage, names, limits, ownership, or start/confirmation behavior. The remaining [technical contracts](../../docs/maestro-architecture.md#architecture-loop-details-still-to-define) do not require new Owner choices unless an actual scope or authority conflict appears. General replanning and Execution design remain separate.

No implementation, runtime configuration installation, or live AI box verification has been performed. Those belong to development. Continue directly on `master` and retain no separate review reports.

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
