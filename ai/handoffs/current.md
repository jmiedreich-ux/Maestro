# Maestro Repository Handoff

## Start here

- [Repository working rules](../../AGENTS.md) and [additional agent instructions](../../CLAUDE.md).
- [Project overview](../../docs/project-overview.md) — authoritative source entry and current-state evidence.
- [Architecture](../../docs/architecture.md) — system behavior and remaining mechanisms.
- [Runtime Service declaration](../../docs/milestones/runtime-service-milestones.md), [CLI declaration](../../docs/milestones/cli-milestones.md), and [registration declaration](../../docs/milestones/registration-milestones.md).
- [Architecture-loop declaration](../../docs/milestones/architecture-loop-milestones.md).
- [Planning Guide and templates](../../docs/planning-guide/README.md).
- [Maestro Project Architect — Software Architecture Role](../../docs/agents/architecture-agent.md).
- [Independent Fidelity Reviewer](../../docs/agents/decision-fidelity-reviewer.md).

## Where the discussion paused

Shared agent performance and context management are now defined in [Architecture](../../docs/architecture.md#agent-performance-and-context-management) and covered by the runtime, CLI, registration and architecture-loop declarations. Defaults warn at 75% context, hand off at 85%, and resume below 70%. Every runtime uses the same capacity classification; Qwen is not penalized for context exhaustion. Persistent sessions retain occupancy across runs. Capacity continuation preserves verified work and remaining active-time budget without consuming failure/correction/review allowances. Adapter capability verification remains implementation work; this does not select Qwen for registration or change exact model choices.

The pre-execution gap closures define stable saved finding references, the fixed architecture `decisions.json` snapshot, typed Owner decisions for one extra review/correction attempt, per-run deadlines with separate next-run duration exceptions, and the local Owner credential boundary. Architecture, schema, and affected delivery criteria are aligned. SQL backup and restore are explicitly out of scope; the contradictory backup procedure is removed. Ordinary restart and recorded-operation recovery remain included.

The architecture-loop agreements are saved in [Architecture](../../docs/architecture.md#architecture-loop) and the [architecture-loop declaration](../../docs/milestones/architecture-loop-milestones.md).

Settled behavior includes `/architecture start` and `/architecture`, selected-project and idle-only entry, exact tool/model selection, persistent-session replacement from verified records, active-run limits, fixed output names and paths, manifest hashes, separate working/confirmed references, stale-data rejection, targeted review, exact-version confirmation, interrupted-operation recovery, cancellation/restart without budget resets, and later-registration invalidation.

Specialist roles use `role-<role-title>.md` beside source, with assigned `context.md` and optional `memory.md`. The architect owns the role and starting context; specialists maintain verified knowledge without changing authority or overwriting a newer file. Wrapper errors return to the architect for bounded technical correction before independent review.

Session continuation, active/waiting mapping, assignment/response and API shapes, saved-record schemas, policy bindings, and canonical hashing are now defined. The schema bundle is `docs/schemas/architecture-loop.schema.json`. Replanning occurs only after confirmed re-registration and a manual architecture-loop start; there is no independent trigger or separate replanning-design task.

Independent decision-fidelity and consistency rechecks passed after contract corrections; the architecture-loop sources are sufficient for registration assessment. No further Owner decision was identified.

Next: use the current architecture and declarations as registration-assessment source. Actual registration confirmation remains separate. Implementing validators, checking installed tool releases, and proving the connected journey belong to development. Do not reopen these technical contracts as undefined merely because implementation evidence does not yet exist.

No implementation, runtime configuration installation, or live AI box verification has been performed. Those belong to development. Continue directly on `master` and retain no separate review reports.

## Decisions to preserve

- The architect is a software architecture role responsible for technical coherence and usable connected outcomes. It both assesses sources and prepares the candidate package.
- Routine technical choices within scope do not need Owner approval. Changed outcomes, expanded scope, conflicts with agreed requirements, reserved decisions, and final registration confirmation retain their agreed authority boundaries.
- The independent reviewer checks both assessment and candidate fidelity. Routine corrections go to the architect; justified material disagreement at the review limit reaches the Owner. No extra review loop was added.
- Role inputs and the [structured registration response](../../docs/architecture.md#registration-agent-response-contract) are already defined. Do not reopen them as unanswered questions.
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
