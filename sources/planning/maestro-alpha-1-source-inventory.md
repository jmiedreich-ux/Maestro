# Maestro Alpha 1 — Source Inventory and Coverage Map

**Status:** Draft source capture for owner review  
**Purpose:** Prevent planning-session requirements, decisions, diagrams, constraints, and deferred ideas from disappearing during plan synthesis.

## Sources

| Source ID | Source |
|---|---|
| `S1` | `sources/planning/maestro-alpha-1-session.txt` |
| `S2` | `sources/planning/local-agent-notes.md` |
| `S3` | VennueSign `docs/design/proposed/maestro-dev-lead-agent-framework.md` |
| `S4` | Existing `jmiedreich-ux/Atlas` repository |
| `S5` | Murphy contract and VennueSign policy references; exact source-file inventory still required |

## Conversation agreements

| ID | Type | Agreement or requirement | Required destination | Status |
|---|---|---|---|---|
| `C-001` | Requirement | Maestro must be a persistent coordinator that continues after a chat turn ends. | Architecture, V1 roadmap | Captured |
| `C-002` | Requirement | Durable state belongs in a database/queue, not chat memory. | Architecture, data model | Captured |
| `C-003` | Process | Work moves through explicit recoverable states with blocked reasons recorded. | Lifecycle specification | Captured; state names require normalization |
| `C-004` | Requirement | A cloud background job must have its external response/job ID stored. | Job and attempt schema | Restored requirement |
| `C-005` | Requirement | Worker completion may arrive by webhook; polling is the initial fallback. | Event adapter, roadmap | Captured; implementation stage clarified |
| `C-006` | Requirement | On every event, Maestro re-reads authoritative GitHub/project facts before acting. | Coordinator transition rules | Restored requirement |
| `C-007` | Requirement | Each permitted coordinator action must be idempotent and execute exactly once. | State-transition contract | Captured; requires detailed design |
| `C-008` | Requirement | Notifications must not depend on reopening a chat. | Notification adapter | Captured |
| `C-009` | Requirement | GitHub App events eventually cover PR, review, check, and issue changes. | GitHub adapter, later roadmap | Restored requirement |
| `C-010` | Requirement | Milestone locks prevent two coordinators or workers from claiming the same work. | Database and lease model | Captured |
| `C-011` | Constraint | Plan changes and retained authority remain hard human gates. | Authority model | Captured |
| `C-012` | Security | Protected branches, signed webhooks, audit logs, retry limits, and budget limits are required. | Security and operations | Partially captured; signed webhooks and budgets restored |
| `C-013` | Outcome | Overnight work must end in a visible completed/blocked ledger, not an ambiguous silent screen. | Atlas requirements, acceptance | Restored requirement |
| `C-014` | Decision | Maestro is its own project-neutral system, separate from Foundry and VennueSign. | Charter | Captured |
| `C-015` | Boundary | Initial autonomous execution handles one owner-approved milestone and stops for owner acceptance. | V1 boundary | Captured |
| `C-016` | Deferred decision | Multi-milestone autonomous progression is not initial scope and requires a later explicit owner decision. | Open decisions, V3+ | Restored requirement |
| `C-017` | Requirement | Reboot, duplicate polls, timeouts, and stale completions must resume safely without duplicate claims, PRs, merges, or tasks. | Recovery contract | Captured; requires detailed design |
| `C-018` | Requirement | Resource locks serialize inference, builds, browsers, and database containers until capacity is proven. | Scheduler and operations | Captured |
| `C-019` | Decision | SQLite is the first operational database on the AI box. | Architecture, V1 | Captured |
| `C-020` | Data | SQLite records runs, packets, attempts, evidence, events, and notifications. | Data model | Partially captured; exact entities restored |
| `C-021` | Deferred architecture | Migrate to Postgres only if distributed runners or remote reporting later require it. | Evolution roadmap | Restored requirement |
| `C-022` | Authority | Versioned plans, code, PRs, reviews, and CI remain repository/GitHub authority. | Source-of-truth model | Captured |
| `C-023` | Authority | Execution state, ownership, attempts, retries, evidence, heartbeats, and notifications belong in Maestro's database. | Source-of-truth model | Captured |
| `C-024` | Decision | Atlas reads Maestro's operational database instead of repeatedly rebuilding state from GitHub Markdown. | Atlas integration | Captured |
| `C-025` | Constraint | Do not create two independently writable truths for the same fact. | Sync contract | Captured |
| `C-026` | Decision | Atlas is local on the AI box; it does not need to be a public/live site. | Architecture | Captured |
| `C-027` | Requirement | Universal process rules live centrally and are versioned in Maestro. | Shared process specification | Captured |
| `C-028` | Requirement | Each project keeps only a thin Maestro manifest/process binding plus genuine exceptions and project rules. | Project contract | Restored requirement |
| `C-029` | Requirement | `maestro project create` registers a new repository and creates its project foundation. | CLI/project bootstrap | Captured; full steps restored below |
| `C-030` | Requirement | `maestro project register` inventories and binds an existing project without overwriting its rules. | CLI/project bootstrap | Captured |
| `C-031` | Requirement | Project creation selects a profile such as library, web app, API, or deployed Azure application. | Project profiles | Restored requirement |
| `C-032` | Requirement | Project creation records repository identity, checkout, branch policy, checks, environments, secret references, and approval/merge policy. | Project manifest/schema | Restored requirement |
| `C-033` | Requirement | Project creation opens one bootstrap PR for repository-facing files. | Bootstrap workflow | Restored requirement |
| `C-034` | Requirement | Project creation finishes with a dry run proving repository read, branch/PR creation, a declared check, and reporting. | Bootstrap acceptance | Restored requirement |
| `C-035` | Decision | Murphy is a distinct remote Azure QA capability, not a local coding worker. | Murphy adapter | Captured |
| `C-036` | Constraint | Murphy remains owner-triggered/on-demand for VennueSign; M0 cannot contact Azure or alter that policy. | Project policy, M0 boundary | Captured |
| `C-037` | Requirement | Every new project completes Project Foundation before feature implementation. | Planning lifecycle | Captured |
| `C-038` | Requirement | Foundation defines purpose, non-goals, architecture, environments, deployment, branch/review/release policy, checks, roles, security, and decision boundaries. | Foundation schema | Restored requirement |
| `C-039` | Requirement | Planning records use versioned schemas for feature briefs, questions, decisions, milestones, packets, and coverage. | Planning contract | Captured |
| `C-040` | Gate | Features cannot implement with unresolved required questions. | Plan validator | Restored requirement |
| `C-041` | Gate | Packets cannot dispatch without owned paths, acceptance behavior, and validation commands. | Plan validator, wrapper | Captured |
| `C-042` | Gate | Milestones cannot become ready without linked approved feature/design records. | Plan validator | Restored requirement |
| `C-043` | Gate | Workers cannot silently change plans; insufficient contracts become questions/proposals. | Worker contract | Captured |
| `C-044` | Gate | Validator reports missing fields, conflicting ownership, stale references, and undocumented `UNTESTED` paths. | Plan validator | Restored requirement |
| `C-045` | UX | Task subjects are short, plain, and action-oriented; explanations remain in the body. | Planning schema, Atlas UI | Captured |
| `C-046` | Routing | Every roadmap task shows planned location, agent role/type, model/class, reviewer, validation, dependencies, and risk before execution. | Task schema, Atlas UI | Captured |
| `C-047` | Audit | Planned routing and actual executor/runtime facts are separate fields. | Database and reporting | Captured |
| `C-048` | Policy | Cloud coordinators must delegate suitable bounded implementation, test, indexing, and documentation work to local agents. | Routing policy | Captured |
| `C-049` | Policy | Cloud remains responsible for planning, contracts, integration, high-judgment work, security, and independent review. | Routing policy | Captured |
| `C-050` | Process | Planning intake registers supplied documents, archives, links, existing records, and session captures before synthesis. | Planning intake | Captured |
| `C-051` | Process | Intake classifies atomic items as requirement, decision, constraint/non-goal, question, task candidate, or deferral. | Planning intake schema | Captured |
| `C-052` | Process | Structured deltas are captured after decisions, source review, and before roadmap approval. | Session checkpoint workflow | Captured |
| `C-053` | Gate | Independent cloud audit maps every source item to an exact planning record or explicit deferral. | Completeness auditor | Captured |
| `C-054` | Gate | Source coverage must reach 100% before a plan is ready. | Planning acceptance | Captured |
| `C-055` | UX | A waiting task must show who/what is awaited, start time, expected result, next action, timeout/retry policy, and current state. | Atlas UI, coordinator | Restored requirement |
| `C-056` | Requirement | Exact worker assignment is known at roadmap creation; runtime facts are filled automatically at dispatch. | Routing and reporting | Captured |
| `C-057` | Process | Diagrams are retained as versioned source plus a one-sentence statement of meaning. | Documentation contract | Restored requirement |
| `C-058` | Boundary | M0 is planning-only: inventory first, then process/architecture design, completeness audit, and owner acceptance. | Roadmap | Captured; terminology was unclear |
| `C-059` | V1 outcome | After M0, first implementation proves project registration, SQLite persistence, local Atlas reporting, one bounded worker, draft PR, review, and owner stop. | V1 roadmap | Captured; milestone layering required |

## Local-agent and wrapper findings

| ID | Type | Agreement or finding | Required destination | Status |
|---|---|---|---|---|
| `L-001` | Component | Every local run is enclosed by an enforcement wrapper. | V1 architecture | Captured |
| `L-002` | Check | Wrapper rejects changed files outside packet allowed paths. | Wrapper contract | Captured |
| `L-003` | Check | Wrapper runs build plus explicit type-check where applicable. | Wrapper contract | Captured |
| `L-004` | Check | Wrapper verifies a real commit exists instead of trusting prose. | Wrapper contract | Captured |
| `L-005` | Check | Packet-specific invariants catch structural and behavioral requirements. | Packet compiler/wrapper | Captured |
| `L-006` | Policy | One failed check gets one exact rework message; second failure escalates. | Revision policy | Captured |
| `L-007` | Helper | Preflight ping detects a dead model before consuming a real attempt. | Wrapper backlog | Captured |
| `L-008` | Helper | Permission lock prevents writes outside allowed paths. | Wrapper hardening | Captured |
| `L-009` | Helper | Runaway timeout safely stops a run with no commit. | Wrapper hardening | Captured |
| `L-010` | Helper | Wrapper automatically appends performance results. | Evidence/reporting | Captured |
| `L-011` | Helper | Every run fingerprints model, context, and quantization. | Evidence schema | Captured |
| `L-012` | Helper | Agent event stream is inspected for real commit activity to detect fake completion. | Wrapper hardening | Captured |
| `L-013` | Helper | Packet linter checks explicit paths, prohibitions, filenames, and existing context. | Packet compiler | Captured |
| `L-014` | Helper | Every attempt uses a fresh worktree. | Worker contract | Captured |
| `L-015` | Helper | Context-length hard gate blocks runs below the configured threshold. | Worker preflight | Captured |
| `L-016` | Helper | Unattended runs close stdin and use detached execution. | Worker operations | Captured |
| `L-017` | Helper | Session exports are archived with run evidence. | Evidence schema | Captured |
| `L-018` | Research | Grammar-constrained tool calls, sampler path masks, and KV prefix snapshots are future llama.cpp research, not V1 requirements. | Research backlog | Needs explicit deferral in roadmap |
| `L-019` | Research | Best-of-N, fine-tuning data, packet compiler, second-model judge, and behavior debugger are later optimizations. | Research backlog | Packet compiler promoted; others deferred |
| `L-020` | Evidence | Qwen 3.6 27B completed six production packets in 11.7 minutes; two first-pass and four after one correction. | Qualification record/routing | Captured |
| `L-021` | Finding | Browser/integration-shaped work was weakest and needed stronger coordinator checks. | Routing thresholds | Restored requirement |
| `L-022` | Next test | Muse Glimmer 30B should run the same six packets and gates. | Qualification backlog | Restored requirement |

## VennueSign framework items

| ID | Type | Agreement or requirement | Required destination | Status |
|---|---|---|---|---|
| `V-001` | Process | Run lifecycle includes kickoff, orient, claim, decompose, dispatch, integrate, verify, review, done ledger, QA, sync, and stop. | Coordinator specification | Partially captured; full lifecycle restored |
| `V-002` | Boundary | One run produces one draft PR for one approved milestone and never starts the next milestone itself. | V1 boundary | Captured |
| `V-003` | Ownership | Maestro owns shared integration files and repository records. | Packet ownership policy | Restored requirement |
| `V-004` | Roles | Data, API, back-office UI, operations UI, display/player, specification/Playwright, and reviewer roles are project-configurable. | Role configuration | Restored requirement |
| `V-005` | Contract | GitHub assignments include base commit, class, risk, priority, goal, context, non-goals, allowed/forbidden paths, acceptance, budgets, network policy, and merge authority. | Job schema | Partially captured; full fields restored |
| `V-006` | State | Standard issue labels represent ready, claimed, running, testing, review, revision, blocked, complete, and cancelled. | GitHub adapter | Needs design decision: labels versus database-only projection |
| `V-007` | Worker | Worker atomically claims, verifies base, creates worktree, runs model, enforces limits, tests, pushes a predictable branch, opens a draft PR, and waits for review disposition. | V1 worker contract | Partially captured |
| `V-008` | Evidence | Durable run evidence is append-only and includes assignment hash, model digest, commits, timings, tests, diff, resource samples, retries, and final disposition. | Evidence schema | Partially captured |
| `V-009` | Review | Cloud review verifies scope, requirements, test integrity, architecture, security, error handling, concurrency, migrations, and conventions. | Review contract | Restored requirement |
| `V-010` | Failure | Infrastructure failures may get bounded clean retry; model/test failures are outcomes, not infrastructure retries. | Failure policy | Restored requirement |
| `V-011` | Security | Dedicated non-root account and scoped GitHub credential; no production credentials, customer data, deploy authority, admin rights, or sudo. | Security model | Captured |
| `V-012` | Health | Heartbeat exposes worker identity, state, current job, model/GPU health, and last seen without private prompts. | Operations/Atlas | Restored requirement |
| `V-013` | Gate | Long-term Linux verification uses disposable SQL Server 2022 containers and serialized resources. | V3 roadmap | Captured |
| `V-014` | Metrics | Record model, cost/tokens, elapsed time, review rounds, rework, gates, untested count, and post-merge QA escapes. | Reporting schema | Restored requirement |

## Atlas migration items

| ID | Type | Agreement or requirement | Required destination | Status |
|---|---|---|---|---|
| `A-001` | Existing system | `jmiedreich-ux/Atlas` already contains Eleventy configuration, API, source, theme, fixtures, tests, docs, and a GitHub Action. | Atlas migration inventory | Captured at top-level only |
| `A-002` | Decision | Atlas becomes Maestro's local reporting application. | Architecture | Captured |
| `A-003` | Change | Atlas transitions from GitHub/Markdown-derived live state to Maestro's database projection. | Data adapter design | Captured |
| `A-004` | Migration | Reusable UI, parsing, rendering, fixtures, and tests must be inventoried before code moves. | V1 milestone | Captured |
| `A-005` | Open decision | Choose Atlas destination path and standalone-repository retirement/compatibility policy. | Decision register | Captured |
| `A-006` | Constraint | Preserve project-neutral behavior and move project-specific assumptions into adapters. | Migration acceptance | Captured |

## Coverage conclusion

The previous handoff captured the system's broad direction but was not a complete source-to-plan conversion. Items marked “Restored requirement,” “Partially captured,” “Needs design decision,” or “Needs explicit deferral” must be represented in the revised architecture, schemas, or roadmap before M0 can pass completeness review.

The next gate is owner review of this inventory, followed by an independent comparison against all five sources. M0 is not complete and V1 implementation is not yet authorized.
