# Alpha-04 — Synthetic Control-Loop Qualification

- **Status:** Original planning release received Decision Fidelity APPROVE at
  exact head `0b416ac204a07285f2f5fe1f6e000c40a6f323b3` and merged in PR #11 at
  `dcca2174dd919aa204707961f1b33ad15de9af41`; Owner-approved patient-worker
  status amendment awaits fresh Decision Fidelity Review and merge
- **Project:** Maestro
- **Owner:** Jeremy Miedreich
- **Graph revision:** `maestro-alpha-04-plan-r1`
- **Source base:** `d0ec9c4593c42e4be5d3461f11ece8b9021ff141`
  (`master`)
- **Patient-worker amendment base:**
  `dcca2174dd919aa204707961f1b33ad15de9af41` (`master`)
- **Decision authority:**
  [M0-D13](../decisions/m0-d13-synthetic-control-loop-qualification.md) and
  [M0-D14](../decisions/m0-d14-context-and-token-reporting.md)
- **Source capture:**
  [2026-08-31 control-loop qualification direction](../../../sources/planning/2026-08-31-synthetic-control-loop-qualification.md)
  and
  [2026-08-31 context and token reporting direction](../../../sources/planning/2026-08-31-context-and-token-reporting.md)
- **Predecessor:** Alpha-03 must be implemented, independently approved,
  accepted, and merged before Alpha-04 can be released
- **Execution class:** one fixture-only, single-process qualification increment
- **Planned implementation route:** Local Qwen in a clean isolated worktree
  after an exact packet is approved and explicitly released
- **Independent implementation-review route:** GPT-5.6 Terra at high reasoning
- **Planning fidelity route:** GPT-5.6 Sol at high reasoning

## Plain outcome

Prove that Maestro can make and preserve the correct next-action decisions for
one synthetic project: identify the eligible packet, assign it once, route its
scripted result through Integration and an independent reviewer, ask a
non-terminal worker for honest progress before assuming it is stalled, apply
context/token budgeting from preflight through status, apply the bounded
correction rule, survive duplicates/restart, and stop for Owner acceptance.

This qualifies Maestro's control-loop logic before Foundry becomes the first
live proving project. It does not contact or dispatch a real agent.

## Authority and amendment boundary

This plan adds the bounded synthetic exception established by M0-D13 to the
earlier Alpha deferral of scheduler and Integration behavior. The exception is
limited to fixed fixtures, scripted local actors and observations, one
single-process run, and no external side effect. All other Alpha boundaries
remain controlling:

- `maestro run-packet` remains the only packet execution entry point;
- for this qualification only, it may replay an approved scripted sequence of
  actor observations; Maestro never generates the worker, Integration, or
  review judgment represented by those observations;
- SQLite through the Maestro service remains the only operational-state writer;
- Atlas remains read-only and is not part of this increment;
- M0-D05 permits no more than one eligible targeted correction;
- M0-D11's bounded filesystem assurance is unchanged; and
- passing the named packet proof will be sufficient under M0-D12.

## Proposed work-graph node

| Field | Value |
| --- | --- |
| Stable node | `MAESTRO-ALPHA-04-CONTROL-LOOP-QUALIFICATION` |
| Rank / serial order | First Alpha-04 node; serial after accepted Alpha-03 |
| Hard dependency | Alpha-03 complete, accepted, independently reviewed, and merged at an exact recorded head |
| Authority dependency | This plan and its future execution packet each receive fresh Decision Fidelity APPROVE and the packet receives explicit Owner implementation release |
| Change domains / locks | Synthetic graph/actor/model-usage fixtures, coordinator eligibility and transition logic, service-owned operational schema/evidence, Alpha-04 tests; one exclusive Alpha control-loop/schema lock |
| Planned route | One bounded local implementation worker after release; exact model and reviewer routes belong in the execution packet |
| Safe parallelism | None inside Alpha-04; the qualification simulates contention but performs one serial assignment |
| Terminal result | Independently reviewable implementation result or Architecture/Owner escalation; never live dispatch, merge, or successor selection |

## Required qualification model

### 1. Fixed synthetic authority

The execution packet must define exact, repository-owned fixture schemas for:

- one complete Alpha-03-style project binding;
- one approved graph revision and authority reference;
- candidate packets that demonstrate higher-ranked blocked work, eligible work,
  unmet review gates, and lock/resource contention;
- declared worker, Integration, and independent-review role identities;
- scripted completion, verification, integration, review, correction, timeout,
  stale-event, and worker-progress observations, including a reliable estimate,
  an explicit unknown estimate, and no immediate reply; and
- scripted model/context/quantization fingerprints, packet context minimum and
  output reserve, exact/estimated/unavailable token and cost measurements,
  pressure thresholds, and checkpoint observations; and
- the expected coordinator decisions and evidence.

Unknown fields, malformed identities, absent authority, unapproved graph
revisions, or inconsistent scripted observations must fail validation before
assignment or operational mutation.

### 2. Eligibility and one assignment

From the approved synthetic graph, Maestro derives `Planned`, `Blocked`,
`Waiting`, `Ready`, and `Dispatchable` without rewriting graph priority or
dependencies. It selects only the highest-ranked Dispatchable candidate and
records why every higher-ranked candidate was skipped.

Claiming the selected packet atomically creates one lease/attempt and reserves
its declared path, shared-boundary, and finite-resource locks. A blocked,
unapproved, route-ineligible, base-incompatible, or lock-conflicting candidate
cannot be assigned.

### 3. Patient worker observation and Atlas-ready status

When an assigned local worker is non-terminal and has not produced the expected
result, the Coordinator must issue a bounded structured status request through
the executor adapter before classifying the worker as stalled or taking a
timeout, interruption, retry, or escalation action, unless the executor already
reports an unambiguous terminal/safety stop. The request asks for:

- ordered remaining/current plan steps;
- the current step and whether work is actively progressing;
- a blocker or an explicit none disposition;
- expected completion timing with confidence, or an explicit `unknown`; and
- the worker observation time.

The same status record includes the current context limit, used/remaining
measurement or estimate, output reserve, measurement type/confidence, pressure
state, and latest available token/cost counters under M0-D14. Unsupported
counters are `unavailable`; they are never inferred from a different counter.

Only one status request may be outstanding for an attempt, and the later packet
must define a minimum query interval plus the response/lease timeout policy.
The request is delivered without interrupting a healthy worker when the
executor supports non-interrupting observation. Otherwise it waits for the next
safe message boundary unless an approved timeout/safety condition already
requires action. A status query must never restart the worker, consume a
correction, change scope, or solicit a product or architecture decision.

Maestro stores the response as worker-reported operational evidence with the
attempt identity, source, and observation/receipt times. An absent or unreliable
ETA is stored as `unknown`; Maestro never invents or upgrades it. A healthy
worker that has not answered before the response window remains `Running` until
the applicable lease/timeout policy permits another action. At that boundary,
the Coordinator rereconciles durable and executor facts before interrupting,
retrying, expiring, or escalating.

The resulting bounded status record is suitable for a later read-only Atlas
projection. Alpha-04 does not build Atlas, a read API, or a UI, and Atlas never
sends the request.

### 4. Context preflight, usage measurement, and checkpoint

Before the synthetic assignment is launched, Maestro validates and records the
declared model/runtime identity, configured context limit, quantization when
applicable, packet minimum context, completion/output reserve, warning and
checkpoint/stop thresholds, and counting method. It rejects the assignment
before worker launch when the configured limit or known starting payload cannot
satisfy the minimum and reserve.

Known input is exact only when counted with the declared model tokenizer or
supplied as a valid runtime measurement. Unknown future tool/file growth is a
bounded estimate/range with confidence. During the run, valid runtime-reported
counters supersede estimates for the same measurement period. Input, output,
cached input, reasoning, and total tokens are distinct fields whose unsupported
values remain `unavailable`. Zero reasoning tokens does not change input/output
or remaining-context facts.

Cost is reported as billed, estimated, `not_billed`, or `unknown`, with amount
and currency only where applicable. Elapsed time and resource facts remain
separate from monetary cost.

At the declared context-pressure boundary, the Coordinator asks for one short
checkpoint at a safe message boundary. The scripted checkpoint records
completed work, current plan/step, changed synthetic artifacts, checks/evidence,
blocker, and next action. Maestro follows the declared checkpoint/stop rule and
does not silently truncate, summarize, or start a replacement session.

### 5. Role-separated handoffs

The scripted worker result records its exact attempt, base/result identity,
changed synthetic paths, checks, and evidence. Completion creates the declared
Integration route:

- `validate-only` verifies an isolated result without changing it;
- `assemble` records a distinct synthetic Integration actor and result; or
- `replan` stops with the missing boundary or conflict.

A result eligible for review is routed to a declared reviewer that is
independent of every actor that changed or assembled it. Missing independence,
evidence, or a required Integration result blocks review readiness.

### 6. Review, correction, and Owner stop

A scripted independent-review approval observation moves the result to
`MergeReady` and then `AwaitingOwner`; Maestro stops. The observation is fixed
fixture data, not a review performed by Maestro. It does not merge, accept on
the Owner's behalf, or select another packet.

One committed, in-scope result that fails only a named gate may receive one
exact targeted-correction assignment under M0-D05. The correction must retain
the original worker lineage and receive targeted review covering the exact
correction diff. A second correction, new failure class, scope breach,
architecture defect, missing contract, or unrelated change produces escalation
and no further assignment.

### 7. Recovery and stale-event behavior

Duplicate invocation, duplicate poll/event, restart, competing claim, stale
worker completion, timeout, and lease expiry must reread durable facts before
any transition. None may create a second active assignment, release another
attempt's lock, overwrite terminal evidence, or advance from an observation
that does not match the active attempt and expected state.

## Required evidence

The future execution packet must name focused tests that prove at least:

1. the happy path from approved graph to one assignment, Integration,
   independent review, and `AwaitingOwner` stop;
2. higher-ranked blocked work is skipped only for a recorded valid reason;
3. a ready but non-dispatchable lock/route/base candidate is not assigned;
4. assignment plus locks is atomic and idempotent;
5. a non-terminal worker status query records exact worker-reported plan,
   current step, blocker, ETA/confidence or `unknown`, and timestamps without
   interrupting, restarting, or changing the assignment;
6. no immediate status response remains `Running` before the response/lease
   boundary, and timeout reconciliation does not assume failure or duplicate
   the attempt;
7. context preflight rejects an undersized configured limit or a starting
   payload that cannot preserve the packet minimum plus output reserve;
8. exact tokenizer/runtime measurements, bounded estimates, confidence,
   `unavailable`, and runtime-supersedes-estimate behavior remain distinct;
9. zero/unavailable reasoning tokens cannot erase nonzero context use, and
   billed/estimated/not-billed/unknown cost states remain honest;
10. warning/checkpoint pressure produces the bounded worker checkpoint and
   declared stop action without silent truncation or replacement-session start;
11. validate-only, assemble, and replan Integration routes behave distinctly;
12. an actor cannot review a result it authored or integrated;
13. one eligible correction is routed and exactly covered, while a second round
   or new failure class escalates;
14. restart, duplicate, stale, timeout, and competing-claim cases do not
   double-dispatch or corrupt evidence; and
15. every terminal path prohibits merge, successor selection, and external
   access.

Exact fixture paths, implementation-owned paths, commands, schemas, and model
routes must be materialized in the later execution packet, not inferred from
this architecture proposal.

## Governing-choice traceability

| Governing choice | Alpha-04 carrier |
| --- | --- |
| Repository/GitHub remain project engineering authority | Fixed synthetic graph/packet authority only; no Git/GitHub access or write path |
| M0-D01 service-only SQLite writer and read-only Atlas | Maestro service is the sole synthetic operational-state writer; Atlas/API/UI are excluded |
| M0-D02/M0-D06 project discovery and thin binding | Consume only an accepted Alpha-03 synthetic binding; no registration, adapter, or real-project claim |
| M0-D03 least privilege and no retained secrets | Reject credential/secret/external-route fields; no provider or network client |
| M0-D05 one targeted correction maximum | One eligible exact correction and targeted review; second round/new failure class escalates |
| M0-D11 bounded Linux filesystem assurance | Preserve the existing boundary; add no stronger containment claim |
| M0-D12 bounded quality and proportionality | Q1-Q5 below carry all eight mandatory fields and name sufficient proof/ceilings |
| M0-D14 context and token reporting from preflight | Attempt-bound model/context/quantization fingerprint, minimum/reserve gate, exact/estimated/unavailable counters, cost state, pressure checkpoint, and Atlas-ready reporting |
| C-22 one milestone and Owner gate | One synthetic assignment reaches `AwaitingOwner` and stops |
| C-19 durable visible waiting state | Structured worker-reported plan/current step/blocker/ETA-or-unknown plus source/time; no premature failure assumption |
| V-014/L-011/L-015/P-004/P-007 retained source requirements | Model/context fingerprint, context hard gate, cost/tokens/elapsed evidence, and run outcome begin at preflight rather than as later metrics |
| C-28 Maestro manages operational eligibility | Deterministic graph projection, dispatchability decision, atomic assignment, and durable reasons |
| C-31/C-32 planned versus dispatchable and safe bypass | Fixed candidates prove blocked/ready/dispatchable distinctions and valid skip reasons |
| C-33 locks and designed concurrency | One atomic lock set; contention is simulated; actual execution remains serial |
| C-34 Integration is first-class | Distinct validate-only, assemble, and replan routes with actor/result lineage |
| C-36 independent review | Scripted reviewer identity must differ from every result-changing worker/integrator; Maestro does not produce the judgment |
| C-42 no implicit merge or successor authority | Terminal approval reaches the Owner stop only; no merge or next-packet action exists |
| M0-D13 pre-V1 synthetic qualification | This complete proposal; Alpha-03 unchanged, live Foundry gated, production workforce remains V2 |

## Complete bounded quality contracts

### Q1 — Authority-faithful eligibility and assignment

- **Protected outcome:** Maestro assigns only the highest-ranked packet that is
  genuinely dispatchable under the approved graph, gates, route, base, locks,
  and resources.
- **Operating/threat/failure model:** one trusted local process consumes fixed
  synthetic authority; missing/unknown authority, blocked dependencies,
  incompatible bases, route denial, and lock contention are in scope.
- **Explicit exclusions:** real project adapters, policy inference, dynamic
  reprioritization, multiple projects, remote schedulers, and parallel runs.
- **Practical assurance level:** deterministic fixture-derived eligibility and
  one atomic assignment with a complete recorded decision reason.
- **Sufficient acceptance proof:** the named happy, blocked, gate, route, base,
  lock, and atomic-claim cases pass and their exact decisions/evidence match.
- **Permitted implementation boundary and complexity:** additive Python/SQLite
  logic within the existing single service, standard library, fixed fixtures,
  and focused tests; no new service, dependency, daemon, or general scheduler.
- **Proportionality ceiling:** one synthetic project, one graph revision, one
  active assignment, and a finite candidate set.
- **Exact stop/escalation rule:** stop before assignment when authority or
  eligibility cannot be determined exactly; return missing policy or graph
  meaning to Architecture/Owner.

### Q2 — Role separation and bounded routing

- **Protected outcome:** worker, Integration, and review handoffs preserve
  declared ownership, evidence, and reviewer independence.
- **Operating/threat/failure model:** scripted results may omit evidence, use a
  wrong actor/attempt, require validate/assemble/replan, request one correction,
  or attempt self-review.
- **Explicit exclusions:** real model quality, code correctness outside
  fixture assertions, provider identity, GitHub review APIs, and multi-result
  production integration.
- **Practical assurance level:** exact actor/attempt lineage and deterministic
  transition gates for all three Integration modes and review outcomes.
- **Sufficient acceptance proof:** named route-mode, evidence, lineage,
  self-review, approval, one-correction, and escalation tests pass.
- **Permitted implementation boundary and complexity:** structured synthetic
  actor/result records and explicit transition functions; no role inference,
  general workflow engine, or automatic repair.
- **Proportionality ceiling:** one worker result, at most one Integration result,
  one independent review chain, and one permitted correction.
- **Exact stop/escalation rule:** stop on missing lineage/evidence,
  self-review, replan, scope breach, second correction, new failure class, or
  architecture-contract defect.

### Q3 — Durable idempotency and recovery

- **Protected outcome:** duplicates, restarts, contention, timeouts, lease
  expiry, and stale observations cannot duplicate work or corrupt accepted
  state/evidence.
- **Operating/threat/failure model:** one local SQLite service receives repeated
  or reordered scripted observations around one active attempt; process restart
  may occur between durable transitions.
- **Explicit exclusions:** distributed consensus, hostile database writers,
  remote event delivery guarantees, multiple coordinators, and real worker
  heartbeat transport.
- **Practical assurance level:** transactionally guarded state/attempt checks,
  idempotency keys, and rereconciliation before the next synthetic action.
- **Sufficient acceptance proof:** named duplicate, restart, competing claim,
  timeout, expiry, stale completion, wrong-attempt, and terminal replay tests
  prove one assignment and immutable accepted evidence.
- **Permitted implementation boundary and complexity:** existing SQLite
  transaction patterns and bounded additive records; no distributed lock,
  message broker, background daemon, or migration-framework redesign.
- **Proportionality ceiling:** single-process recovery semantics for one active
  synthetic assignment only.
- **Exact stop/escalation rule:** stop when durable state cannot identify one
  unambiguous next action; never guess, overwrite, or start a replacement run.

### Q4 — Synthetic confinement and Owner authority

- **Protected outcome:** qualification cannot affect a real project, invoke a
  real actor, or pass the Owner acceptance/merge boundary.
- **Operating/threat/failure model:** fixtures may attempt external paths,
  repository/GitHub/network/credential references, real executor routes,
  merge, or successor actions.
- **Explicit exclusions:** assurance against hostile same-UID/root movement
  beyond M0-D11, production sandboxing, provider security, and live repository
  containment.
- **Practical assurance level:** strict fixture allowlist plus no implementation
  path for network, Git/GitHub, credential, real model, merge, or successor
  operations.
- **Sufficient acceptance proof:** prohibited-field/path/route cases fail before
  assignment or mutation; the happy path reaches `AwaitingOwner` and records a
  stop with zero external calls and no merge/successor state.
- **Permitted implementation boundary and complexity:** fixed repository-owned
  fixtures and existing local runtime confinement; no subprocess, Git library,
  network client, provider SDK, credential reader, or merge integration.
- **Proportionality ceiling:** prove absence through bounded interfaces and
  focused tests, not a general OS sandbox.
- **Exact stop/escalation rule:** any need for real access, real actor dispatch,
  stronger isolation, merge, or automatic successor authority returns to
  Architecture/Owner and is not implemented in Alpha-04.

### Q5 — Patient worker status and honest timing

- **Protected outcome:** Maestro does not mistake a quiet but active local
  worker for a failed worker, take premature interrupt/retry action, or present
  an invented completion promise to the Owner.
- **Operating/threat/failure model:** one assigned synthetic worker may be
  actively reasoning/generating, may report a plan/current step/blocker and a
  reliable ETA or `unknown`, may reply late, or may not reply before the bounded
  response window; duplicate status requests and stale replies are in scope.
- **Explicit exclusions:** guaranteed completion times, token-level progress,
  raw chain-of-thought/prompts/traces, arbitrary worker chat, hostile-worker
  truth verification, infinite waiting, and operation beyond an approved
  timeout or authorization stop.
- **Practical assurance level:** one rate-limited outstanding structured status
  request per attempt, source/timestamp-labeled worker evidence, honest
  `unknown` handling, and reconciliation before any timeout action.
- **Sufficient acceptance proof:** named tests prove exact reliable/unknown
  status capture, Atlas-ready projection fields, duplicate/stale-reply
  rejection, no pre-boundary interruption/retry/state failure, and correct
  timeout reconciliation from durable plus executor facts.
- **Permitted implementation boundary and complexity:** a bounded executor-
  adapter status operation, explicit status schema, and service-owned evidence;
  no conversational agent framework, raw transcript store, Atlas write path,
  background chat daemon, or new provider SDK.
- **Proportionality ceiling:** one active synthetic attempt, one outstanding
  request, packet-defined minimum interval/response window, and a short bounded
  status payload.
- **Exact stop/escalation rule:** a reported blocker routes to its declared
  Coordinator/Architecture/Owner boundary; an unanswered request remains
  non-terminal until timeout policy allows reconciliation; ambiguity never
  authorizes a duplicate run, invented ETA, or silent scope decision.

### Q6 — Context budget and honest token/cost reporting

- **Protected outcome:** Maestro does not launch a packet that cannot fit its
  declared context/reserve, misstate estimated usage as exact, confuse one token
  counter for another, or let context exhaustion silently lose work.
- **Operating/threat/failure model:** one synthetic attempt has a declared
  model/runtime/context/quantization fingerprint, known starting input, uncertain
  future tool/file growth, optional runtime counters, cost availability states,
  and warning/checkpoint/stop thresholds; missing/malformed counters,
  estimate/report disagreement, zero reasoning tokens, and pressure crossings
  are in scope.
- **Explicit exclusions:** universal token prediction accuracy, raw prompt/
  transcript storage, chain-of-thought collection, provider billing
  reconciliation, automatic prompt optimization, silent compaction, automatic
  session rollover, and global thresholds chosen without run data.
- **Practical assurance level:** strict preflight schema and minimum/reserve
  gate; exact values only from the declared tokenizer/runtime; otherwise labeled
  ranges/estimates with confidence; distinct unavailable/zero and cost states;
  deterministic pressure/checkpoint decisions.
- **Sufficient acceptance proof:** named tests cover undersized context and
  oversized-start rejection, exact versus estimated counts, runtime replacement
  of estimates, malformed/stale counters, unavailable fields, nonzero context
  with zero reasoning tokens, all cost states, pressure transitions, checkpoint
  evidence, and an Atlas-ready usage projection.
- **Permitted implementation boundary and complexity:** explicit synthetic
  model/usage fixtures, additive attempt/evidence fields, arithmetic derived
  values, and transition rules in the existing Python/SQLite service; no real
  tokenizer/model/billing call, new dependency, background meter, or Atlas UI.
- **Proportionality ceiling:** one fingerprint and bounded sequence of usage
  observations for one synthetic attempt, packet-declared thresholds, and one
  checkpoint action; no optimization engine or cross-run forecasting model.
- **Exact stop/escalation rule:** reject before launch if minimum/reserve cannot
  be satisfied; on malformed/ambiguous measurement preserve the last valid fact
  and stop usage-driven action; at checkpoint/stop pressure follow the declared
  rule and return any need for compaction/session continuation or new global
  policy to Architecture/Owner.

## Explicit non-goals and deferrals

- Alpha-03 implementation, project registration, or a real binding.
- Foundry, VennueSign, or any other repository/project access.
- Real local/cloud model invocation, agent process management, Git/GitHub/CI,
  webhooks, network, secrets, or notifications.
- Production specialist queues, multiple projects, parallel execution,
  resource optimization, fairness/aging, or general scheduling.
- Atlas/API/UI implementation, backup/USB/recovery, deployment, merge, owner
  acceptance automation, or successor selection. Alpha-04 stores only the
  bounded Atlas-ready worker-status and usage evidence required by Q5/Q6.
- Proving the quality of real worker code or real Integration/reviewer judgment.

These remain V1/V2 or separately approved work. Alpha-04 proves only the
control-loop decisions and durable handoff semantics using synthetic data.

## Open questions

There is no unresolved material architecture choice in this planning release.
The later packet must make the fixture schemas, public result shapes, owned
paths, exact checks, and stop-before-mutation cases explicit before it can enter
Decision Fidelity Review. It must also declare exact context minimum, output
reserve, warning/checkpoint/stop thresholds, measurement fallbacks, and cost
states for its synthetic route. If doing so requires a production scheduler, a
real actor/tokenizer/billing service, a second command/control surface, or a
broader threat model, that is a material replan and returns to
Architecture/Owner.

## Feasibility and proportionality conclusion

The proposal is feasible within the existing one-service Python/SQLite and
fixture-test model. Fixed schemas, deterministic transition functions, and a
single active assignment can prove the required semantics without a production
scheduler, external actor, or new infrastructure. The six quality contracts
bound both the expected assurance and the implementation ceiling.

If an exact execution packet cannot provide the named proof inside that class,
Architecture must narrow or replan the qualification with the Owner. A worker
must not compensate by building V2 infrastructure.

## Gates and handoff

1. Fresh Decision Fidelity Review must approve this complete planning range.
2. The reviewed plan must receive Owner acceptance and merge as a planning-only
   graph release.
3. Alpha-03 must complete its own release, implementation, independent review,
   Owner acceptance, and merge path.
4. Architecture may then draft a separate Alpha-04 execution packet with exact
   schemas, paths, commands, routes, and checks.
5. That packet requires fresh Decision Fidelity APPROVE and explicit Owner
   implementation release before any build begins.

This proposal creates no executable packet or operational queue state and does
not authorize implementation, dispatch, Foundry access, review execution, or
merge.
