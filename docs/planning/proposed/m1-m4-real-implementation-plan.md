# M1–M4 Real Implementation Plan

**Status:** Proposed implementation graph; not an execution packet or dispatch
authorization
**Graph revision:** `maestro-m1-m4-real-r1`
**Authority:** [M0-D15 — Real M1–M4 Implementation and Non-Live Proving
Path](../decisions/m0-d15-real-m1-m4-implementation-path.md)
**Source base:** `c6eb7d83082a1ac75eb9b7798b6f2bdce74341c4`
**Proving target:** One newly created, non-live project with real repository
operations, agents, work, checks, Integration, review, waits, corrections, and
operational events

## Purpose and boundary

This graph materializes the already accepted M1–M4 roadmap into 22 bounded
implementation packet candidates plus one attended end-to-end acceptance
packet. It does not redesign Maestro, grant credentials, create an exact
execution packet, dispatch an agent, or authorize a merge.

Alpha-01 through Alpha-03 remain accepted foundations:

- retain Alpha-01's Linux runtime boundary, SQLite connection, WAL, foreign
  keys, and migration metadata;
- retain Alpha-02's packet-validation, atomic-claim, replay, M0-D05 grading,
  evidence, and handoff patterns;
- reuse Alpha-03's discovery fact categories and binding shape, but do not use
  its fixture validator as the production authority loader because of its
  accepted fixture-only malformed-array limitation; and
- keep every Alpha-01 through Alpha-03 test as a regression gate while leaving
  the synthetic executor, fixture worktree, scripted discovery, and Alpha-04
  packet outside the real proving route.

## Approval and role chain

Every packet follows this chain:

1. The **Project Architect** materializes the exact packet and its complete
   M0-D12 quality contracts.
2. A fresh **Decision Fidelity Reviewer** approves the exact planning range.
3. The bootstrap **Coordinator** creates the isolated worktree and dispatches
   the packet.
4. The dedicated **Maestro Developer** implements Maestro product features.
5. The **Integration Agent** validates or assembles the result.
6. A separate **Independent Implementation Reviewer** reviews the exact
   implementation range and any correction-only diff.
7. The **Project Architect** accepts routine packet and milestone results and
   releases the next eligible packet.

The Project Architect is the routine acceptance and architecture-return
authority. The Owner is contacted only for a changed product, architecture,
public-contract, security, data, credential, external-access, material-risk,
spending, production, deployment, merge, or other explicitly reserved choice,
or an infeasible quality contract. Ordinary eligibility, waiting, locks,
polling, recovery, Integration, review, and the one M0-D05 correction are not
Owner decisions.

## Dependency order

The milestone order is M1 → M2 → M3 → M4 → attended E2E. Within a milestone,
only the explicit dependencies below control release. The Coordinator may
prepare a later packet while another is under review, but may not dispatch it
until all listed dependencies are accepted.

## Fully materialized graph candidate

Only this node is fully materialized in graph revision
`maestro-m1-m4-real-r1`. It is currently a candidate, not runtime
`Dispatchable`. The remaining 21 implementation packets and E2E-01 are outline
candidates whose exact node records will be materialized and reviewed before
release.

| Field | Value |
|---|---|
| Stable ID | `MAESTRO-M1-01-REAL-PROJECT-AUTHORITY-LOADER` |
| Project / workstream / milestone | `maestro` / `project-registration` / `M1` |
| Task link | `docs/planning/packets/m1-01-real-project-authority-loader.md` |
| Outcome | Load strict project authority from one exact local Git commit and atomically record one candidate or blocked result. |
| Non-goals | Public create/register CLI, repository or network write, GitHub, worker dispatch, active registration, Atlas, merge, or deployment. |
| Priority / rank | `P0` / `1` |
| Risk | `medium`: strict authority parsing and an additive shared SQLite migration, bounded by real-repository and rollback proof |
| Planned location / role / model class | cloud collaboration worktree / dedicated Maestro Developer / session-inherited Codex model, with factual model and runtime recorded at preflight |
| Execution class | `codex-cloud-maestro-developer` |
| Hard dependencies | accepted Alpha-01, Alpha-02, Alpha-03; M0-D15; exact implementation base `c6eb7d83082a1ac75eb9b7798b6f2bdce74341c4` |
| Soft dependencies | none |
| Downstream unlock | M1-02 packet materialization after routine Project Architect acceptance |
| Owned domains | manifest/schema; exact-commit Git reader; authority loader; minimal registration persistence; `tests/m1_01/` |
| Resource locks | `path:maestro-registration-core`; `shared:sqlite-schema`; `file:services-maestro-pyproject` |
| Input contract version | `maestro-project-authority-load-v1` |
| Output contract version | `maestro-project-authority-load-result-v1` |
| Required checks | Alpha-01, Alpha-02, Alpha-03, M1-01 unit suites; Python compileall; exact changed-path review |
| Integration route | Integration Agent, `validate-only` unless assembly is required |
| Review route | fresh Independent Implementation Reviewer over exact implementation base/head and any targeted correction diff |
| Resource envelope | one isolated worktree; one Developer attempt; at most one eligible M0-D05 correction; no parallel writer in the locked domains |
| Approval state | `PendingDecisionFidelity`; no implementation lease or dispatch is permitted |
| Dispatchable transition | exact packet receives Decision Fidelity `APPROVE`; Project Architect releases that exact reviewed head; Coordinator then verifies the exact base, clean isolated worktree, execution route/context, unlocked resources, and all hard dependencies immediately before atomic claim |
| Approval boundary | Project Architect for routine packet acceptance; Owner only for a reserved M0-D15 material choice |

## M1 — Build the core and register projects

| Packet | Outcome | Dependencies | Owned path areas | Sufficient proof | Runtime role / acceptance authority |
|---|---|---|---|---|---|
| **M1-01 · Load and record a real project authority bundle** | Strictly validate `maestro.project.yaml`; read its declared authority from an exact commit in a real local non-live Git repository; atomically record one candidate/blocked authority-load result without changing or registering the project. | Accepted Alpha-01–03 | Manifest/schema, exact-commit Git reader, authority loader, minimal project/registration/event records, `tests/m1_01/` | Real temporary Git repositories prove exact-SHA loading, strict missing/conflicting facts, no repository mutation, idempotent persistence, schema-2 upgrade, and rejection of Alpha-03's malformed-array case. | Project adapter foundation; Project Architect accepts. |
| **M1-02 · Complete operational state and recovery primitives** | Expand the additive schema into the accepted V1 projects/bindings, graph/work projections, runs, packets, leases, attempts, evidence, waits, locks, notifications, reviews, usage/context, and acceptance records; add atomic transitions, event append, claims, and restart reconciliation primitives. | M1-01 | Storage, migration, state/event/lease/recovery modules; `tests/m1_02/` | Existing data survives upgrade; constraints and failed-migration rollback pass; duplicate commands/observations, stale transitions, expired leases, interrupted transactions, and lock contention preserve one exact state/event history. | Development Manager operational state; Project Architect accepts. |
| **M1-03 · Connect real repository and GitHub operations** | Observe repository state and perform only policy-scoped branch, commit, push, draft-PR, check, and review operations; provide no merge or branch-protection bypass. | M1-01, M1-02 | Git/GitHub adapters, secret-reference boundary, tests | Real Git and non-live remote integration prove idempotent branch/PR behavior, redacted outcomes, visible expired/missing credentials, and no default-branch write. | Development Manager repository adapter; Project Architect accepts code. New credential authority returns to the Owner. |
| **M1-04 · Create a new Maestro-bound project** | Implement `maestro project create`: create the project record, profile, foundation/templates, thin manifest, bootstrap branch/PR, pending state, and non-dispatching dry run. | M1-01, M1-02, M1-03 | CLI; project-create module; project templates; operations docs; tests | Create the dedicated non-live project with actual generated files and commit; registration remains pending until bootstrap merge and dry-run success; replay creates nothing twice. | Project adapter/Development Manager; Project Architect approves its foundation and accepts. |
| **M1-05 · Register an existing project without changing discovery state** | Implement `maestro project register`: read-only discovery, fact/missing/conflict inventory, proposed binding, approved binding PR, dry run, and final registration. | M1-01, M1-02, M1-03 | CLI; production discovery and project-register modules; docs/tests | Discovery makes no repository change; incomplete authority blocks; the approved PR is binding-only; merge plus successful dry run registers exactly once. | Project adapter/Development Manager; Project Architect accepts. |
| **M1-06 · Run Maestro as a restart-safe Linux service** | Add the persistent non-root service entry point, startup health, polling clock, orderly shutdown, and registration recovery; prove the created project survives service and machine restart. | M1-04, M1-05 | Service entry points and Linux service/install files; CLI health; operations docs/tests | Kill/restart and a controlled Linux host reboot prove service-on-boot, preserve database and binding, create no duplicate project/dry-run/branch/PR, stay under the physical `var/` boundary, and have no Windows dependency. The disruptive host-reboot observation is performed only in the attended approved environment. | Development Manager service; Project Architect accepts M1. |

## M2 — Make Atlas the live read-only reporting application

| Packet | Outcome | Dependencies | Owned path areas | Sufficient proof | Runtime role / acceptance authority |
|---|---|---|---|---|---|
| **M2-01 · Expose redacted snapshots and live state events** | Add the local read API, snapshot cursor, event stream, reconnect contract, and redaction boundary; expose no command endpoint or direct database access. | M1-02, M1-06 | Read-API, event-stream, and redaction modules; API tests | Snapshot and ordered live events pass; reconnect obtains a fresh snapshot; secrets, prompts, and traces are redacted; mutation requests are rejected. | Maestro service publishes and Atlas reads; Project Architect accepts. |
| **M2-02 · Integrate the approved Atlas reporting surface** | Bring the approved reusable Atlas presentation surface into Maestro under `apps/atlas/`, retain useful source history and tests, and replace repository/GitHub operational reads with M2-01. | M2-01 | `apps/atlas/**`; bounded workspace/build files | Retained/adapted Atlas tests and the Linux build pass; Atlas neither opens SQLite nor reconstructs live state from GitHub. | Atlas reporting; Maestro Developer implements and Integration Agent controls the source merge; Project Architect accepts. |
| **M2-03 · Show projects, work, agents, waits, and evidence** | Show projects, graph/milestones, packets, assignments, waits, locks, retries, heartbeats, evidence, reviews, context/usage, and the current acceptance authority. | M2-02, M1-04 | Atlas data models, views, components, styles, and tests | Browser/component proof uses actual M1 state; links return to repository/PR/check authority; unknown facts remain `unknown` or `unavailable`. | Atlas read-only projection; Project Architect accepts. |
| **M2-04 · Prove live reporting and reconnect behavior** | Complete the Atlas/service integration and M2 exit proof. | M2-03 | API/UI integration tests and operations docs; bounded corrections only | A real service state change appears without a GitHub rebuild; reconnect catches missed events; Atlas cannot route, retry, approve, or mutate work. | Atlas reporting; Project Architect accepts M2. |

## M3 — Build real packet dispatch and enforcement

| Packet | Outcome | Dependencies | Owned path areas | Sufficient proof | Runtime role / acceptance authority |
|---|---|---|---|---|---|
| **M3-01 · Compile approved graph nodes into exact packets** | Implement the production packet schema, node materializer, packet linter, role/SOP binding, quality-contract validation, exact base/paths/checks/routes, and invariant-library input. | M1-01, M1-02 | Production packet/compiler/linter/invariant modules; tests | Complete packets compile deterministically; any missing authority, M0-D12 field, path, check, route, context reserve, or stop rule blocks before claim. | Development Manager packet compiler; Project Architect accepts. |
| **M3-02 · Prepare isolated branches, worktrees, and resource locks** | Create real branches/worktrees at pinned bases, atomically acquire path/shared/resource locks, apply write permissions, and clean up safely. | M3-01, M1-02, M1-03 | Worktree, permission, and resource modules; tests | Real Git proof covers dirty/stale bases, conflicting locks, outside-path writes, restart cleanup, and duplicate-claim suppression. | Development Manager; Project Architect accepts. |
| **M3-03 · Run and observe the real local developer agent** | Implement submit, poll, bounded status, cancel, and evidence retrieval plus the fixed OpenCode/Qwen route with closed stdin, timeout, model/context preflight, and honest usage facts. | M3-01, M3-02 | Executor base and OpenCode/Qwen adapter; usage/status modules; docs/tests | Real preflight, model/runtime/context fingerprint, insufficient-context rejection, status reply or `unknown`, timeout/cancel, session export, and honest unavailable counters pass. | Development Manager dispatches; a real Specialist Agent works; Project Architect accepts. |
| **M3-04 · Grade evidence and allow one exact correction** | Grade scope, commit, declared checks, invariants, and evidence; distinguish self-correction from coordinator correction; enforce the exact M0-D05 routes; update accepted invariant records. | M3-03 | Grading, evidence, rework, lifecycle, and storage modules; tests | Real diff/commit/check evidence passes; missing delivery and prohibited violations reject immediately; one named-gate correction is allowed; a second or new failure class escalates; evidence stays immutable. | Development Manager grades and Specialist performs at most one correction; Project Architect accepts. |
| **M3-05 · Prove one real seven-phase packet lifecycle** | Run Author → Compile → Dispatch → Grade → permitted correction → Record → Learn on the non-live project with a real agent and real Git work. | M3-04, M2-04, M1-04 | Proving-project approved paths; M3 end-to-end tests; bounded corrections | Actual agent session, branch, commit, diff, checks, evidence, Atlas state, and invariant result pass. Scripted actors or fabricated judgments cannot satisfy exit. | Runtime roles through the Integration handoff; Project Architect accepts M3. |

## M4 — Complete the persistent Development Manager loop

| Packet | Outcome | Dependencies | Owned path areas | Sufficient proof | Runtime role / acceptance authority |
|---|---|---|---|---|---|
| **M4-01 · Project approved work into eligible queues** | Ingest the exact approved graph; derive planned/waiting/blocked/ready states; calculate dispatchability; record skipped-candidate reasons; atomically lease the highest-ranked eligible item. | M1-01, M1-02, M3-01 | Graph-projection, queue, scheduler, and lease modules; tests | Graph revision/hash, stale-graph `NeedsReplan`, dependency/route/WIP/path/resource gates, and duplicate-tick safety pass. | Development Manager; Project Architect accepts. |
| **M4-02 · Operate the persistent observation and recovery loop** | Implement poll → record → reread authority → verify state/lease → perform one safe next action → persist → report/notify, including patient status and timeout/cancel behavior. | M4-01, M1-06, M3-03 | Manager, reconciliation, status-policy, and service-loop modules; tests | Real worker polling, bounded status before stall, restart during work, duplicate observation, stale completion, timeout/cancel, and exactly-once next action pass. | Development Manager; Project Architect accepts. |
| **M4-03 · Route real Integration and independent review agents** | Invoke separate real role instances, preserve independence, and process `validate only`, `assemble`, `needs replan`, `APPROVE`, and `REQUEST_CHANGES` outcomes. | M4-02 | Role router, executor adapters, handoff/evidence records; tests | A real Specialist → Integration → different Independent Reviewer chain passes; integrator changes force a different reviewer; architecture defects return to the Project Architect; fixture judgments do not qualify. | Development Manager routes; Integration and Independent Review decide in scope; Project Architect accepts. |
| **M4-04 · Drive the draft PR and review-coverage gates** | Create/observe the real draft PR, checks, commits, review results, one correction diff, and exact final-head review coverage; never merge automatically. | M4-03, M1-03 | Delivery and review-coverage modules; GitHub adapter extensions; tests | Real draft PR and checks pass; full reviewed range plus targeted correction diffs covers final head; stale/uncovered changes block; duplicate polls create no duplicate request. | Development Manager and Independent Reviewer; Project Architect accepts. |
| **M4-05 · Notify the correct acceptance authority** | Implement durable notification storage, delivery, acknowledgement, and retry; route ordinary acceptance to the Project Architect and reserved choices through the Project Architect to the Owner. | M4-02, M4-03, M4-04, M2-04 | Notification, Slack-adapter, and acceptance modules; Atlas extensions/tests | Store-before-send, retry/rate limit, visible delivery failure, non-approving acknowledgement, routine Architect routing, and reserved Owner routing pass. | Development Manager notifies; Project Architect accepts code. New Slack/external authority returns to Owner. |
| **M4-06 · Qualify real restart and failure recovery** | Prove service/process restart, duplicate poll, stale completion, timeout, expired lease, contention, notification failure, Integration return, review correction, and architecture return without duplicate actions. | M4-01 through M4-05 | M4 end-to-end tests and operations runbook; bounded fixes | Evidence includes real killed/restarted processes and repository reconciliation. Controlled component doubles may cover rare branches but cannot replace real milestone-exit evidence. | Development Manager recovers; Project Architect accepts. |
| **M4-07 · Arm the attended non-live proving run** | Register the created project, load its approved useful graph, validate all identities/routes/checks, start Maestro and Atlas, and stop before dispatch for the attended test. | M4-06, M3-05 | Non-live project authority records; Maestro configuration and operations records | Service, database, repository/GitHub, local worker, Integration, reviewer, Atlas, and notification routes are healthy; no fixture or live-product binding is active. | Bootstrap Coordinator hands control to Development Manager; Project Architect declares test-ready and accepts M4 implementation readiness. |

## Attended end-to-end acceptance packet

### E2E-01 · Run one real non-live milestone through Maestro

**Dependency:** M4-07
**Owned paths:** Only the Project Architect-approved paths in the non-live
project plus Maestro operational state; no Maestro implementation expansion is
implicit.
**Runtime chain:** Project Architect release → Development Manager claim → real
Specialist Agent → real Integration Agent → different real Independent
Reviewer → Project Architect acceptance.
**Sufficient proof:** Maestro creates the real branch/worktree, obtains real
code, checks, commit, and evidence, creates or updates the real draft PR,
reports live state in Atlas, delivers durable notifications, applies no more
than one eligible M0-D05 correction, routes an architecture-contract defect
back to the Project Architect, and stops at the correct acceptance boundary.
No scripted actor, fixture review result, fabricated observation, or
live-product repository can satisfy this proof.
**Acceptance authority:** Project Architect for the normal result; Owner only
if the run exposes a reserved material decision.

## External setup gates

These gates are configuration or provisioning, not new architecture packets:

- a dedicated non-live repository and repository-scoped GitHub service
  identity;
- a non-root Linux Maestro service identity and approved runtime directories;
- a working OpenCode/Ollama/Qwen route with the approved context capacity;
- a real callable Integration Agent and a separate Independent Reviewer route
  that operate without an open chat turn; and
- an approved Slack destination with a least-privilege notification identity.

The Project Architect validates setup that stays inside accepted authority. A
new or expanded credential, external-access, security, or spending boundary
returns to the Owner before activation.

## Explicit exclusions

This graph does not require or authorize:

- Alpha-04 synthetic qualification or scripted end-to-end actors;
- Foundry, VennueSign, or another live product project;
- USB backup/restore acceptance;
- webhook transport;
- Murphy;
- automatic merge or production deployment;
- autonomous successor-milestone selection; or
- multi-project parallel execution.

## Ready for the attended test

Maestro is ready for the Owner-attended test only when:

1. all 22 implementation packets have Decision Fidelity approval, complete
   implementation review coverage, passing named proof, and routine Project
   Architect acceptance;
2. every Alpha-01 through Alpha-03 regression and every M1–M4 required check
   passes from the exact final implementation head;
3. the new non-live project has an approved foundation and graph, a merged
   bootstrap binding, successful dry run, and no live-product dependency;
4. the persistent Linux service, SQLite state, Atlas snapshot/event stream,
   repository/GitHub adapter, real worker route, Integration route,
   independent-review route, and notification route all pass preflight;
5. restart and reconciliation evidence proves that duplicate observations,
   stale completion, timeout, and process restart cannot duplicate a claim,
   branch, PR, review request, evidence result, or notification;
6. Atlas shows the actual pending run and acceptance authority while remaining
   unable to control Maestro; and
7. no unresolved setup issue or reserved material choice remains hidden in a
   routine packet.

At that point M4-07 stops without dispatching E2E-01. The attended test begins
only when the Project Architect releases E2E-01 with the Owner following.
