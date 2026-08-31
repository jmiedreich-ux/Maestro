# Alpha-03 — Synthetic Project Discovery and Binding Proposal

**Status:** Proposed architecture plan; non-executable
**Project:** Maestro
**Proposed graph revision:** `maestro-alpha-03-r1`
**Source base:** `8a088e400a479078acdc85801cab384414d820c8` (`master`)
**Owner direction:** On 2026-08-31, the Owner agreed to plan a synthetic
project-discovery and binding-proposal increment as Alpha-03. That agreement
authorizes this planning work only; it does not approve this packet or any
implementation.

## Outcome

Extend the existing local synthetic `maestro run-packet` lifecycle so one
approved, fixture-only Alpha-03 packet can:

1. read one declared synthetic project-discovery snapshot;
2. produce a deterministic inventory of confirmed, missing, and conflicting
   project-binding facts required by M0-D02;
3. produce a proposed binding only when every required fact is present and
   non-conflicting;
4. persist bounded synthetic evidence through Maestro's service-owned SQLite
   boundary; and
5. stop at either the existing independent-review handoff or an immediate,
   owner-readable escalation.

It proves the information contract for later real registration. It does not
inspect, register, bind, or modify a real project.

## Authority and confirmed facts

| Authority | Alpha-03 consequence |
| --- | --- |
| [Current handoff](../../../ai/handoffs/current.md) | Alpha-01 and Alpha-02 are complete; Alpha-03 has no implementation authority. Alpha stays synthetic-only. |
| [M0-D02 — Project Registration and Bootstrap](../decisions/m0-d02-project-registration.md) | The synthetic inventory and proposal carry M0-D02's required identity, authority, delivery, verification, role, operations, and exception facts. No real registration state is created. |
| [M0-D01 — Operational Database](../decisions/m0-d01-operational-database.md) | Maestro's local service remains the only SQLite writer. Atlas receives no command path or direct database access. |
| [M0-D05 — Rework, Review, and Escalation](../decisions/m0-d05-rework-review-and-escalation.md) | An insufficient or contradictory discovery is an immediate escalation, not a worker correction loop. A valid result stops at independent review. |
| [M0-D11 — Linux Runtime Filesystem Boundary](../decisions/m0-d11-linux-runtime-filesystem-boundary.md) | Existing runtime-path assurance remains unchanged. Alpha-03 adds no claim against hostile concurrent same-UID/root filesystem movement. |
| [M0-D12 — Bounded Quality Contracts](../decisions/m0-d12-bounded-quality-contracts.md) | Q1–Q3 below define the complete, proportional definition of enough. |
| [Alpha-02 done record](../done/alpha-02-run-packet-lifecycle-wrapper.md) | The existing wrapper, local claim, evidence, M0-D05 grade, and review-handoff stop boundary are the predecessor contract. |

## Proposed graph node

| Field | Value |
| --- | --- |
| Node | `MAESTRO-ALPHA-03` |
| Title | Establish synthetic project discovery and binding proposal |
| Rank / serial order | First and only proposed Alpha-03 node; serial after Alpha-02 |
| Upstream dependency | `hard`: Alpha-02 complete at `4a0ccc7d8bdaad6a8ac58fc9e3e6cd6e208a00fe`, merged through `16cfb9970e30a7b29192243540629be2dc2c0f40` |
| Change domains / locks | Synthetic packet contract, local lifecycle, service-owned SQLite schema, fixture set, and Alpha-03 tests; one serial local schema/lifecycle lock |
| Executor route | Local Qwen, only after packet approval and release; the work is fixture-bounded, standard-library Python/SQLite work and the tested wrapper is active |
| Reviewer route | Fresh Independent Implementation Reviewer, GPT-5.6 Terra at high reasoning |
| Planning fidelity route | Fresh Decision Fidelity Reviewer, GPT-5.6 Sol at high reasoning |
| Downstream unlock | A later Architecture/Owner decision on real read-only registration discovery; it does not itself unlock Foundry work |

No active graph release or implementation packet exists until this proposal receives
Owner approval, independent Decision Fidelity Review, and the required planning
merge. This proposal is therefore outside every operational queue.

## Proposed behavior

### Synthetic input contract

The approved Alpha-03 packet remains the sole CLI input to `maestro run-packet`.
It names one fixture snapshot by a safe relative identifier beneath a new
repository-controlled `fixtures/alpha/project-discovery/` root. The wrapper
rejects an absolute path, traversal, missing fixture, or fixture resolving
outside that root before SQLite mutation or executor launch.

The fixture represents an existing-project discovery result, not a repository.
It contains exactly these M0-D02 fact areas:

| Fact area | Required synthetic result |
| --- | --- |
| Identity | Project name, synthetic repository identifier, default branch, adapter version, process version |
| Authority | Architecture, handoff, rules/SOP, and task/issue paths or explicit missing/conflict dispositions |
| Delivery | Branch/PR/merge, owner-acceptance, deployment, and rollback policy facts |
| Verification | Declared build, test, integration, UI/QA, and evidence rules |
| Roles | Specialist-overlay, reviewer, QA/Murphy, and local/cloud eligibility facts |
| Operations | Environment-reference names, resource locks, and notification policy facts; never a secret value |
| Exceptions | A stricter project rule or a declared exception, or an explicit none disposition |

The discovery result is one of two bounded outcomes:

- **Complete and non-conflicting:** persist the fact inventory, deterministic
  proposed binding, fixture digest, and evidence; return the existing
  `AwaitingReview` / `IndependentReview` handoff and stop.
- **Missing or conflicting required fact:** persist the inventory and reason
  as bounded synthetic evidence; return the existing immediate
  `Rejected` / `CoordinatorEscalation` outcome and stop. It does not claim
  registration, request a correction, infer a default, or retry.

The result never says `Registered`. Real discovery, owner review of a real
binding, a project-repository binding PR, dry-run verification, and registration
remain later work under M0-D02.

### Permitted implementation shape

The implementation may add a small synthetic-discovery parser/normalizer, one
packet-contract extension for the declared fixture identifier, one synthetic
executor scenario, additive SQLite tables for discovery evidence/proposals, and
Alpha-03 fixtures/tests. The wrapper remains the local command boundary and
the SQLite service remains its sole writer.

Expected owned paths are limited to:

```text
docs/architecture/alpha-03-synthetic-project-discovery.md
docs/operations/alpha-03-synthetic-project-discovery.md
fixtures/alpha/project-discovery/
fixtures/alpha/alpha-03-*.json
services/maestro/maestro/cli.py
services/maestro/maestro/lifecycle.py
services/maestro/maestro/packet_contract.py
services/maestro/maestro/packet_wrapper.py
services/maestro/maestro/storage.py
services/maestro/maestro/synthetic_discovery.py
tests/alpha_03/test_synthetic_project_discovery.py
```

An implementation may omit an expected path when it is unnecessary, but it may
not change any other path without Architecture/Owner replan and a refreshed
Decision Fidelity Review.

## M0-D12 quality contracts

### Q1 — Fixture-only discovery authority and confinement

- **Protected outcome:** Alpha-03 cannot inspect a real repository, arbitrary
  host file, secret store, or path outside the declared fixture root.
- **Operating/threat/failure model:** one trusted local Maestro process reads
  an approved packet that names a fixture; malformed packet fields, absolute or
  traversal paths, missing fixtures, and pre-existing fixture symlinks that
  resolve outside the fixture root are in scope.
- **Explicit exclusions:** real repositories, Git/GitHub/CI, network access,
  credentials, general hostile same-UID/root concurrent source-tree mutation,
  recursive repository discovery, and M0-D11's excluded post-acquisition
  runtime-directory actor model.
- **Practical assurance level:** pre-read safe-relative-path validation and
  resolved-root containment for one repository-controlled fixture.
- **Sufficient acceptance proof:** tests prove every unsafe/missing fixture
  reference is rejected before a SQLite claim, worktree, executor launch, or
  evidence record; the valid fixture uses only the declared root.
- **Permitted implementation boundary and complexity:** `pathlib`, standard
  library JSON, and existing packet validation only; no Git library, shell
  command, file crawler, network client, credential provider, or new package.
- **Proportionality ceiling:** one fixed fixture root and one declared fixture
  per packet; no generalized filesystem sandbox or source-tree threat claim.
- **Stop/escalation rule:** stop and return to Architecture/Owner if a real
  repository, arbitrary source path, credential, network lookup, or stronger
  filesystem assurance becomes necessary.

### Q2 — Complete, honest synthetic binding inventory

- **Protected outcome:** a synthetic discovery cannot be represented as a
  registration-ready binding unless all seven M0-D02 fact areas are explicit,
  complete, and non-conflicting.
- **Operating/threat/failure model:** fixture facts may be complete, missing,
  or mutually contradictory; ordinary malformed JSON and wrong field types are
  in scope.
- **Explicit exclusions:** deciding a project's real policy, resolving a real
  conflict, applying defaults to missing facts, reading a repository, creating
  an adapter, or creating a project binding PR.
- **Practical assurance level:** deterministic normalization into one
  owner-readable inventory with each area marked confirmed, missing, or
  conflicting, plus a proposed binding only for a complete result.
- **Sufficient acceptance proof:** fixtures/tests cover a complete result, one
  missing required fact, one conflicting fact, malformed input, and exact
  preservation of declared exception/no-exception dispositions. Only the
  complete fixture may receive `AwaitingReview`; every incomplete/conflicting
  fixture returns immediate escalation with the named reason.
- **Permitted implementation boundary and complexity:** one small local data
  model/normalizer and structured JSON evidence; no policy engine, natural
  language inference, repository parser, or automatic repair.
- **Proportionality ceiling:** support only the M0-D02 areas and finite
  fixture statuses; do not build a universal project manifest editor or
  multi-project registry.
- **Stop/escalation rule:** a requirement to infer, reconcile, or choose a
  missing/conflicting project policy stops the packet and returns the inventory
  to Architecture/Owner without a worker correction.

### Q3 — Durable, idempotent synthetic discovery evidence and handoff

- **Protected outcome:** a valid synthetic discovery creates one inspectable
  evidence/proposal record and one terminal wrapper outcome; a duplicate run
  cannot create a second discovery execution or overwrite the first record.
- **Operating/threat/failure model:** duplicate CLI invocation, replay after a
  completed local run, ordinary local contention, and restart after the
  existing durable claim are in scope.
- **Explicit exclusions:** distributed coordination, multi-coordinator
  leadership, real-project lifecycle state, lease renewal, external artifact
  storage, notifications, Atlas/API/UI, and crash containment beyond the
  current one-process synthetic model.
- **Practical assurance level:** the existing atomic packet claim governs one
  packet key; additive SQLite records are tied to that key and are immutable on
  replay.
- **Sufficient acceptance proof:** tests demonstrate that a complete run
  stores one inventory/proposed binding/digest and `AwaitingReview` handoff;
  an incomplete/conflicting run stores one inventory/reason and immediate
  escalation; duplicate/restart/competing-claim cases do not launch a second
  executor or alter evidence.
- **Permitted implementation boundary and complexity:** existing SQLite
  transaction pattern and standard-library hashing/JSON; the Maestro service
  is the only writer.
- **Proportionality ceiling:** additive local records only; no schema migration
  framework redesign, scheduler, daemon, queue, remote lock, or registration
  state machine.
- **Stop/escalation rule:** stop and return to Architecture/Owner if durable
  behavior requires a real project identity, multi-process/distributed lease,
  backup/recovery redesign, or a second correction cycle.

## Required checks and acceptance evidence

The eventual implementation must run and record:

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m maestro.cli run-packet \
  --packet ../../fixtures/alpha/alpha-03-complete-discovery-packet.json \
  --runtime-dir ../../var/alpha-03-check
```

Passing the named proof is enough only when it shows:

- all preceding Alpha tests remain green;
- Alpha-03 covers every Q1–Q3 proof case, including unsafe fixture rejection,
  complete/missing/conflicting inventories, idempotent replay, and contention;
- the successful command stores an owner-readable synthetic proposed binding,
  records `AwaitingReview`, and stops; and
- generated data remains in the isolated ignored runtime directory and no
  real project, network, secret, GitHub, CI, Atlas/API/UI, backup/USB, queue,
  scheduler, worker/model, review execution, merge, or successor selection is
  invoked.

## Explicit non-goals and deferrals

- Foundry and VennueSign discovery, registration, binding, or modification.
- Any real repository scan, Git/GitHub interaction, CI, webhook, network,
  service account, credential reference resolution, or secret handling.
- `maestro project register`, `maestro project create`, actual project state,
  project adapter implementation, binding PRs, or dry-run execution.
- Atlas, API/SSE, browser UI, reporting views, notifications, project queues,
  scheduling, worker dispatch, or multi-packet execution.
- Backup/restore, USB provisioning, retention, and the M0-D07 recovery gate.
- Changes to Alpha-01's M0-D11 assurance boundary.
- Review execution, automatic correction, merge, auto-merge, or autonomous
  selection of later work.

## Feasibility and proportionality conclusion

This is feasible within the existing Python/SQLite service and the Alpha-02
wrapper because it uses one fixed local fixture root, a finite M0-D02 schema,
and the already-tested durable claim/handoff model. It does not need an
external identity, real repository, credential, or daemon. The smallest
plausible implementation is a parser/normalizer plus additive local evidence
records and focused fixtures/tests.

The plan must stop—not expand—if it discovers that realistic registration,
real project policy, or a filesystem/security guarantee beyond Q1 is required.
Those are later Architecture/Owner choices.

## Decision-fidelity carrier map

| Governing choice | Alpha-03 carrier |
| --- | --- |
| Alpha stays synthetic-only | Fixture-only input root, no real repository, and explicit non-goals |
| Mandatory `maestro run-packet` lifecycle boundary | Existing wrapper remains the sole CLI entry point |
| M0-D02 registration starts read-only and requires an inventory/proposed binding | Seven-area synthetic inventory and conditional proposed binding; no registration state |
| Project repository remains authoritative | No repository is read or changed; fixture evidence is not project authority |
| M0-D01 service-only SQLite writer | Discovery evidence/proposals are written only through the existing service |
| M0-D05 bounded escalation | Missing/conflicting facts receive immediate escalation; no defaulting or correction loop |
| M0-D11 bounded Linux assurance | Runtime boundary unchanged; Q1 explicitly excludes stronger actor claims |
| M0-D12 bounded quality definition | Q1–Q3 include all eight required fields and define enough |
| Atlas read-only | No Atlas/API/UI path |
| M0-D07 USB recovery deferral | No backup/recovery work |
| Owner-gated successor work | Valid output stops at independent-review handoff; this proposal authorizes no later work |

## Required next gates

1. Owner reviews and either approves, changes, or rejects this proposed
   Alpha-03 plan.
2. A fresh Decision Fidelity Reviewer independently reviews the exact planning
   range at GPT-5.6 Sol high reasoning.
3. Only an Owner-approved, fidelity-approved, merged packet can be released
   for the bounded Local Qwen implementation route.
4. A fresh Independent Implementation Reviewer then reviews the exact result
   at GPT-5.6 Terra high reasoning.

Until those gates finish, Alpha-03 is planning only.
