# Maestro — Current Project Handoff

**Status:** M1–M4 real implementation is authorized under
[M0-D15](../../docs/planning/decisions/m0-d15-real-m1-m4-implementation-path.md).
Alpha-01 through Alpha-03 remain completed historical foundation work. The
synthetic Alpha-04 prerequisite and Foundry-first proving target are
superseded. The active objective is to complete M1–M4 and prepare a newly
created non-live project for an attended, real-agent end-to-end test with the
Owner.

**Planning base:** `8aa4cb517dcb902060cf5acd1d58806787e03841`
(`origin/master` when the M1 readiness branch was created)

## Current Owner direction

The accepted source is
[2026-09-01 real M1–M4 implementation direction](../../sources/planning/2026-09-01-real-m1-m4-implementation-direction.md).

- Execute the already documented M1–M4 roadmap; do not redesign it.
- Do not use Foundry, VennueSign, or another live product project as the proving
  target.
- Use `maestro project create` to establish a new non-live project.
- End-to-end actors, work, Git operations, commits, checks, Integration,
  independent review, waits, corrections, and failures are real—not scripted
  fixture judgments or fabricated observations.
- The dedicated Maestro Developer implements Maestro product features. The
  Coordinator manages bootstrap handoffs until the runtime Development Manager
  exists.
- The Project Architect handles routine approval and architecture returns.
  Only an M0-D15 reserved material choice goes to the Owner.
- The USB provisioning deferral remains and is not a readiness gate for the
  attended non-live proving run.

## Active build path

### M1 — Build the core and create/register projects

Implement production operational records, migrations, the project manifest,
exact authority loader, `project create`, `project register`, the
binding/bootstrap PR flow, non-dispatching dry run, leases, idempotent
transitions, the persistent Linux service, and restart reconciliation.

### M2 — Merge Atlas into Maestro reporting

Provide a service-mediated snapshot/event API and local read-only Atlas views
for projects, work graphs, queues, agents, waits, evidence, Integration/review,
architecture returns, notifications, usage/capacity, and acceptance boundaries.
Atlas has no write, route, approval, retry, merge, provider-query, or direct
SQLite path.

### M3 — Build real packet dispatch and enforcement

Materialize approved graph nodes into exact packets; use a real executor adapter
and clean Git worktree; enforce owned paths, commits, named checks, context and
usage preflight, time/resource policy, evidence, M0-D05 rejection rules, and one
eligible targeted correction.

### M4 — Complete the persistent Development Manager loop

Poll and reconcile authority and executor/GitHub facts, atomically select and
claim eligible work, create the branch/draft PR, route real Integration and
independent review, recover from restart/duplicates/stale results/timeouts/lease
expiry, notify the correct authority, and stop at Project Architect acceptance
unless a genuinely reserved Owner decision is required.

## Role and approval chain

1. Project Architect materializes and routinely approves faithful graph/packet
   releases.
2. A fresh Decision Fidelity Reviewer verifies each exact planning range.
3. The Coordinator creates isolated implementation work and hands it to the
   dedicated Maestro Developer until the Development Manager can self-host
   those operations.
4. Integration verifies or assembles the result.
5. A fresh Independent Implementation Reviewer verifies the exact result.
6. The Project Architect accepts routine results and releases the next packet.
7. The Owner receives only an M0-D15 reserved material choice.

No role may treat review approval as merge, deployment, automatic successor,
or production authority.

## Existing implementation to preserve

- Alpha-01 provides the bounded Linux runtime directory and SQLite/WAL
  foundation. Its accepted implementation head is
  `3124378f3ba885cb066d1426b1a0ed5a5d0ccb6f`.
- Alpha-02 provides the fixture-only `maestro run-packet` wrapper foundation.
  Its accepted implementation head is
  `4a0ccc7d8bdaad6a8ac58fc9e3e6cd6e208a00fe`.
- Alpha-03 provides fixture discovery/schema lessons only. Its Owner-accepted
  official head is `f21e4a2ff25cead8b972b4433da33f0e9910efc5`, with the
  trusted-fixture limitation recorded in its done record.
- Existing bounded filesystem, one-correction, review-coverage, secret,
  read-only Atlas, and honest context/usage contracts remain controlling.

Synthetic paths may remain as unit/regression fixtures, but they cannot serve
as the M1–M4 end-to-end acceptance route.

## Current implementation gate

Before a Maestro Developer packet is dispatched:

1. its exact graph/packet authority must be committed;
2. a fresh Decision Fidelity Reviewer must approve the exact base/head range;
3. the Project Architect must record routine release under M0-D15; and
4. the Coordinator must create a clean isolated worktree from the approved
   implementation base.

Implementation then follows the Coding Agent SOP, M0-D05 correction cap,
Integration route, independent implementation review, and exact final-head
coverage gate.

## Explicit non-goals for M1–M4 test readiness

- Foundry, VennueSign, or another live product proving run.
- Synthetic/scripted end-to-end actors or review judgments.
- USB provisioning or recovery acceptance.
- Multiple-project parallel dispatch or mature resource optimization.
- Webhook transport; polling/reconciliation is the recovery authority.
- Murphy/Azure QA, production deployment, automatic merge, or autonomous
  successor milestones.

## External setup boundary

Adapter code and tests may be completed under Project Architect authority.
Activating a new GitHub, executor/provider, Slack, secret-provider, or other
external credential/scope remains an M0-D15 reserved Owner action. The final
attended proving run cannot begin until its specifically scoped non-live
repository and agent/notification identities are configured and verified.
