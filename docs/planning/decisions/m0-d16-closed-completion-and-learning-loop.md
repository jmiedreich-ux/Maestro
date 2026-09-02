# M0-D16 — Closed Completion and Learning Loop

**Status:** Accepted under Owner direction on 2026-09-02
**Scope:** Graph/packet compilation, dispatch readiness, Integration, independent
review, correction, architecture return, automatic resumption, and learning
**Source:** [Owner direction — make completion closed and learn from rework](../../../sources/planning/2026-09-02-closed-completion-and-learning-direction.md)

## Decision

Maestro treats completion as a closed contract fixed before dispatch. Work does
not begin from an open-ended promise that reviewers can expand after delivery.

### 1. Closed definition-of-done manifest

Every executable packet contains an immutable, ordered definition-of-done
manifest. Each item has:

- a stable requirement/proof ID and its controlling authority reference;
- the exact behavior, invariant, or quality-contract claim being proved;
- the responsible executor or gate owner;
- the command, deterministic inspection, or bounded observation that proves it;
- the expected result and sufficient evidence format;
- the allowed result states, including an explicit reason and authority for any
  permitted `N/A` or `UNTESTED`; and
- its implementation slice, owned paths, locks, dependencies, and review route.

The manifest also includes a coverage ledger mapping every atomic packet
requirement to at least one proof item. Unmapped requirements and proof items
without a requirement are compiler errors.

Words such as `every`, `all`, `complete`, `safe`, `robust`, or
`production-ready` do not define executable proof by themselves. A universal
claim must either list the finite members or name a deterministic enumeration
rule, authoritative input, and digest whose result is expanded and frozen when
the packet is released. A later member changes authority and requires a
superseding packet; it cannot silently move the active gate.

### 2. Feasibility and packet-size gate

Before Decision Fidelity review and dispatch, the compiler rejects a packet
when:

- an outcome can be released independently and has no required shared atomic
  transition with the other outcomes;
- required work crosses incompatible owners, permission boundaries, execution
  routes, resource/lock lifetimes, or independent review units;
- a proof inventory cannot be closed from the named authority;
- the one permitted correction could not remain inside the packet's owned
  paths and proportionality ceiling; or
- dependencies, configuration, environment, or external authority needed for
  the named proof are unavailable.

The Project Architect splits or rematerializes rejected work. Packet size is
therefore controlled by structural cohesion and correctability, not an
arbitrary line or file count.

### 3. Bounded first review and one combined correction

The initial Independent Implementation Review examines the full exact range and
returns one complete set of findings against the frozen manifest and governing
contracts. The reviewer must finish that crosswalk before issuing its outcome;
it may not drip additional in-contract findings through successive general
reviews.

For a committed, in-scope result that is safe and complete enough to inspect,
the Coordinator obtains terminal Integration and independent-review results
before it issues M0-D05's single correction. Their named findings are combined
into one correction record. A no-diff/no-commit, scope, dependency,
configuration, or placeholder rejection remains an immediate M0-D05 rejection
and need not wait for review. A result that cannot safely enter review records
that reason as its terminal gate.

The correction follow-up verifies only the combined named findings, the
correction-only diff/evidence, and directly affected consistency. A different
failure class after correction, a failed or out-of-scope correction, or an
exhausted correction ends implementation and returns through the exact M0-D05
route.

### 4. Fixed completion and later improvements

A result is technically complete only when the exact final head:

1. passes every frozen manifest item and named gate;
2. has a terminal passing Integration result;
3. has complete independent review coverage over the initial range and every
   correction-only diff;
4. has a clean handoff with the required evidence, gaps, context/usage facts,
   and released locks; and
5. receives the project policy's routine Project Architect acceptance.

A direct violation of the approved contract remains blocking even if a packet
forgot to test it; that omission is also a packet-contract defect. A newly
imagined improvement outside accepted authority is recorded as a non-blocking
successor learning item. It does not enlarge the current definition of done.

### 5. Return, wake, and resume

Every terminal result and every resolution is a durable operational event with
the packet, exact head, failed manifest IDs, classification, responsible
authority, next permitted action, and idempotency key.

- Bootstrap/infrastructure failures and immediate M0-D05 rejections return to
  the Coordinator for an authorized reassignment or takeover.
- A missing/infeasible contract, architecture defect, new post-correction
  failure class, or exhausted correction returns to the Project Architect.
- The Project Architect resolves routine returns inside accepted authority and
  involves the Owner only for an M0-D15 reserved choice.
- An R3/R4 contract correction renews Decision Fidelity/review as applicable
  and records the reusable invariant, compiler, template, or role-policy update
  before another packet with the same pattern is released.

When the blocking authority or operational fact changes, its committed update,
poll/reconciliation observation, review result, lease/lock expiry, or service
restart triggers eligibility recomputation. The Coordinator/Development Manager
rereads the exact durable authority and state, atomically claims the
highest-ranked eligible node, and resumes. Chat is not a wake mechanism.

### 6. Learning record

For every packet Maestro records:

- active cycle time, queue/wait time, and time held at each gate;
- first-pass result, review count, correction count, and hard escalation;
- finding class and whether it was discoverable by the pre-dispatch compiler;
- any late-discovered requirement and why it was absent from the frozen
  manifest; and
- the exact reusable rule/template/invariant change, or an explicit reason that
  no general change is warranted.

Atlas reports these facts read-only. The Project Architect uses the learning
record when releasing later packets, but metrics cannot silently change
authority, quality thresholds, model routing, or acceptance.

## Implementation placement

- M1 stores the closed manifest, gate/finding, return, resolution, and learning
  records durably.
- M2 exposes their state and timing through the service-mediated read-only
  reporting projection.
- M3 implements packet compilation, frozen coverage validation, feasibility
  rejection, evidence grading, and combined correction creation.
- M4 implements durable return routing, event-driven reread, restart-safe
  eligibility recomputation, and automatic resume.

The attended non-live end-to-end proving run must exercise these behaviors with
real work, real agents, real omissions/failures, real review, and durable
restart/resume evidence. Scripted actor identities or fabricated outcomes do
not satisfy it.

## Non-authorization

This decision does not authorize automatic merge, production deployment,
live-project testing, external credentials, owner-reserved choices, autonomous
successor milestones, or an unbounded review/search process.
