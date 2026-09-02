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

For a committed, in-scope result that can safely be reviewed,
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

- elapsed and active cycle time, queue/wait time, and time held at each gate;
- first-pass result, review count, correction count, correction cause linked to
  the combined finding IDs/classification, and hard escalation;
- finding class and whether it was discoverable by the pre-dispatch compiler;
- any late-discovered requirement and why it was absent from the frozen
  manifest; and
- the exact reusable compiler, template, invariant, or role-policy change, or an
  explicit reason that no general change is warranted.

Atlas reports these facts read-only. The Project Architect uses the learning
record when releasing later packets, but metrics cannot silently change
authority, quality thresholds, model routing, or acceptance.

## Bounded quality contracts

### Q1 — Closed packet compilation

1. **Protected outcome:** no executable packet can omit a requirement, carry an
   orphan proof, leave a universal set undefined, or change its completion gate
   after release.
2. **Operating/failure model:** versioned local graph, authority, packet, role,
   SOP, quality-contract, and deterministic enumeration inputs are in scope,
   including missing/duplicate IDs, missing or many-to-one coverage, reordered
   input, changed source digest, and every structural split condition in this
   decision.
3. **Explicit exclusions:** the compiler does not decide whether accepted
   product intent is wise, formally verify implementation behavior, fetch
   unapproved remote authority, or infer unstated requirements.
4. **Assurance level:** deterministic structural closure and byte-stable output
   for the exact supported packet schema and pinned local authority inputs.
5. **Sufficient acceptance proof:** the M3 compiler suite must prove: the same
   valid input compiled twice yields identical ordered IDs, expanded members,
   and digest; one isolated case each for an unmapped requirement, orphan proof,
   duplicate ID, missing M0-D12 field, universal claim without carrier, carrier
   member/digest change after release, and each of the five M0-D16 structural
   split/rejection conditions fails before claim with its exact reason; and a
   complete valid packet is accepted with exact two-way set equality.
6. **Implementation boundary:** the production packet schema/compiler/linter,
   local authority reader, deterministic serialization/digest support, and
   their tests; no network service or general formal-verification framework.
7. **Proportionality ceiling:** validate only declared packet authority and the
   supported schema; do not recursively interpret arbitrary prose or build a
   general-purpose source-language parser.
8. **Stop/escalation:** an authority set that cannot be enumerated
   deterministically, a required semantic inference, or a structurally
   inseparable packet that cannot fit the supported boundary returns to the
   Project Architect before dispatch.

### Q2 — Complete first review and combined correction

1. **Protected outcome:** the single correction is not spent before all named
   Integration and initial full-review defects are known, and follow-up does not
   restart general discovery.
2. **Operating/failure model:** every committed, in-scope delivery not rejected
   by M0-D05's no-diff/no-commit, scope, dependency, configuration, or
   placeholder classes is reviewable. Integration/review success or failure in
   either arrival order, duplicate/stale results, restart between results, and
   correction follow-up are in scope.
3. **Explicit exclusions:** an immediate M0-D05 rejection receives neither a
   correction nor a forced independent review; an architecture-contract return
   is not converted into implementation correction; reviewer perfection beyond
   the frozen contract is not claimed.
4. **Assurance level:** deterministic, idempotent aggregation of the two
   terminal gate results and complete frozen-manifest crosswalk for the initial
   exact review range.
5. **Sufficient acceptance proof:** M3/M4 tests must prove both arrival orders;
   both-pass, Integration-only-fail, review-only-fail, and both-fail outcomes;
   process restart after either first result; duplicate/stale result rejection;
   exactly one combined correction containing the union of unique finding IDs;
   no correction for each immediate M0-D05 rejection class; and a targeted
   follow-up limited to the named set, correction diff/evidence, and directly
   affected consistency.
6. **Implementation boundary:** Integration/review result records, correction
   aggregator, lifecycle transitions, immutable evidence links, and role
   contracts; no reviewer-authored implementation fix.
7. **Proportionality ceiling:** two initial terminal gate results and one
   correction record for the packet; no repeated general review or second
   correction.
8. **Stop/escalation:** missing/unverifiable evidence, a new failure class after
   correction, failed/out-of-scope correction, contract defect, or exhausted
   correction follows M0-D05/M0-D15 to the Project Architect.

### Q3 — Durable return, restart, and automatic resume

1. **Protected outcome:** a return cannot be lost or resumed early, and a
   resolution/restart cannot create duplicate dispatch or require chat to
   continue eligible work.
2. **Operating/failure model:** durable return/resolution events, committed
   authority changes, poll observations, service termination before and after
   event commit/eligibility recomputation/atomic claim, duplicate events,
   concurrent scheduler ticks, stale authority, and lease/lock expiry are in
   scope on the single Linux service with SQLite/WAL.
3. **Explicit exclusions:** multi-host writers, hostile same-UID/root database
   mutation, automatic merge/deploy, autonomous successor milestones, and
   unapproved external credentials or event transports.
4. **Assurance level:** deterministic restart-safe, idempotent, exactly-once
   next-action selection within the accepted single-service/SQLite model.
5. **Sufficient acceptance proof:** M4 must use real service processes and a
   real non-live repository to prove: unresolved return never dispatches;
   Project Architect resolution makes the expected node eligible without chat;
   termination/restart at each pre-commit/post-commit/pre-claim/post-claim seam;
   duplicate resolution, poll, and scheduler tick; concurrent tick and lease
   expiry; stale authority replacement; and exactly one resulting claim/action
   with the recorded highest-ranked eligibility reason. Controlled component
   doubles may add rare failure cases but cannot replace this real proof.
6. **Implementation boundary:** operational event/state store, authority
   rereader, eligibility scheduler, lease/lock claim, service loop, and bounded
   recovery tests on Linux; polling/reconciliation remains authoritative.
7. **Proportionality ceiling:** one project, one active milestone, one service
   writer, and the approved M4 executor routes; no distributed consensus,
   webhook system, multi-project scheduler, or automatic merge.
8. **Stop/escalation:** ambiguous authority, inability to prove idempotent
   recovery inside SQLite, an external-access need, or a reserved material
   choice stops resume and returns to the Project Architect for M0-D15 routing.

### Q4 — Learning-record integrity and read-only reporting

1. **Protected outcome:** delay and rework cannot disappear into chat or counts
   that fail to identify why the packet was slow and which reusable prevention
   changed.
2. **Operating/failure model:** passing first attempt, immediate rejection, one
   combined correction, architecture return, exhausted correction, missing
   timestamps, late requirement, and each reusable-change category are in
   scope, including snapshot/event reconnect.
3. **Explicit exclusions:** metrics do not grade people/models, infer causation
   beyond recorded classifications, enforce budgets, alter routing/authority,
   or expose prompts, traces, credentials, or secrets.
4. **Assurance level:** exact durable field preservation and reproducible time
   arithmetic from recorded service timestamps, with unknown facts represented
   explicitly rather than inferred.
5. **Sufficient acceptance proof:** M1/M2 tests must persist and reopen one case
   for each listed outcome; verify elapsed/active/queue/wait/per-gate arithmetic;
   link a correction cause to the exact combined finding IDs/classification;
   record a late requirement and absence reason; record each `Compiler`,
   `Template`, `Invariant`, `RolePolicy`, and `NoGeneralChange(reason)` outcome;
   reproduce the same values through snapshot plus reconnect events; and prove
   Atlas has no mutation/control route.
6. **Implementation boundary:** additive operational records/events, service
   snapshot/event DTOs, Atlas read-only projection, and bounded tests; no raw
   agent transcript, external analytics platform, or provider scraping.
7. **Proportionality ceiling:** packet/gate-level timings and classifications
   only; no agent surveillance, speculative productivity score, or universal
   process-mining system.
8. **Stop/escalation:** unavailable timestamps remain `unknown`; inconsistent
   immutable events block the metric and return for reconciliation; a proposed
   policy or routing consequence requires its normal Project Architect/M0-D15
   authority rather than being inferred from a metric.

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
