# Alpha-03 — Establish Synthetic Project Discovery and Binding Proposal

**Status:** Draft execution packet; non-executable pending Owner packet approval and Decision Fidelity Review
**Owner:** Jeremy Miedreich
**Architecture plan:** [Alpha-03 proposal](../proposed/alpha-03-synthetic-project-discovery.md), merged at `e89a850f1894351acc052a33471b53b90bcaee8f`
**Source base:** `e89a850f1894351acc052a33471b53b90bcaee8f` (`master`)
**Predecessor:** Alpha-02 implementation head `4a0ccc7d8bdaad6a8ac58fc9e3e6cd6e208a00fe`
**Execution class:** one fixture-only implementation in a clean isolated worktree
**Worker route:** Local Qwen, after this exact packet is approved and released
**Reviewer route:** fresh Independent Implementation Reviewer, GPT-5.6 Terra at high reasoning
**Planning fidelity route:** fresh Decision Fidelity Reviewer, GPT-5.6 Sol at high reasoning

## Outcome

Extend `maestro run-packet` so one approved Alpha-03 fixture packet reads one
safe synthetic project-discovery snapshot, returns an M0-D02 inventory, and
persists a proposed binding only when every required fact is complete and
non-conflicting. Missing or conflicting facts record immediate escalation and
stop. This rehearses registration; it never contacts a real project.

## Required behavior

1. `maestro run-packet` remains the only Alpha command. No project-register,
   project-create, or direct discovery command is added.
2. The packet declares one `discovery_fixture`: a single JSON filename beneath
   `fixtures/alpha/project-discovery/`. Empty, absolute, traversal,
   separator-containing, missing, or outside-root/symlink-resolving references
   are rejected before a claim, worktree, executor, or SQLite mutation.
3. The snapshot is a strict JSON object with only `identity`, `authority`,
   `delivery`, `verification`, `roles`, `operations`, and `exceptions` areas.
   Unknown fields are rejected. Required leaves are:

   | Area | Required leaves |
   | --- | --- |
   | Identity | `project_name`, `repository_identifier`, `default_branch`, `adapter_version`, `process_version` |
   | Authority | `architecture_paths`, `plan_paths`, `handoff_path`, `rules_sop_path`, `task_issue_conventions` |
   | Delivery | `branch_pr_merge_policy`, `owner_acceptance_policy`, `deployment_rollback_policy` |
   | Verification | `build_commands`, `test_commands`, `integration_commands`, `ui_qa_commands`, `evidence_rules`, `untested_handling` |
   | Roles | `specialist_overlays`, `reviewer_route`, `qa_murphy_policy`, `local_cloud_eligibility` |
   | Operations | `environment_reference_names`, `secret_reference_names`, `resource_locks`, `notification_policy` |
   | Exceptions | `disposition` (`none` or `declared`) and `items`; `none` has no items and `declared` has one or more |

   `secret_reference_names` accepts references only; no field accepts or resolves
   a secret value.
4. A complete, non-conflicting snapshot records a normalized inventory, a
   deterministic proposed binding, a SHA-256 fixture digest, bounded evidence,
   and `AwaitingReview` / `IndependentReview`; the wrapper stops.
5. A well-formed snapshot with a missing leaf, invalid exception disposition,
   or conflict records the named inventory/reason, `Rejected` /
   `CoordinatorEscalation`, and stops. It never defaults, retries, requests a
   correction, or claims registration.
6. The existing packet claim is the idempotency key. Duplicate invocation,
   replay, restart, and competing claim cannot rerun discovery or overwrite the
   initial inventory, proposal, digest, or handoff.
7. Discovery evidence passes only through the service-owned SQLite boundary.
   No direct database client, Atlas path, API, or UI is introduced.

## Owned implementation paths

```text
docs/architecture/alpha-03-synthetic-project-discovery.md
docs/operations/alpha-03-synthetic-project-discovery.md
fixtures/alpha/alpha-03-*.json
fixtures/alpha/project-discovery/**
services/maestro/maestro/cli.py
services/maestro/maestro/lifecycle.py
services/maestro/maestro/packet_contract.py
services/maestro/maestro/packet_wrapper.py
services/maestro/maestro/storage.py
services/maestro/maestro/synthetic_discovery.py
tests/alpha_03/**
```

No other path may change. If passing the named proof requires an out-of-scope
change, stop and return to Architecture/Owner.

## Complete bounded quality contracts

### Q1 — Fixture-only authority and confinement

- **Protected outcome:** no real repository, arbitrary host file, secret store,
  or outside-root fixture can be read.
- **Operating/threat/failure model:** one trusted local process reads an
  approved packet; malformed names, absolute/traversal/separator paths, missing
  files, and pre-existing links resolving outside the fixture root are in scope.
- **Explicit exclusions:** Git/GitHub/CI, network, credentials, source-tree
  crawling, real repositories, hostile concurrent source mutation, and the
  excluded M0-D11 post-acquisition runtime actor model.
- **Assurance level:** safe-basename validation plus resolved-root containment
  before opening one fixture.
- **Sufficient acceptance proof:** parameterized tests reject every unsafe or
  missing reference before claim, worktree, executor launch, or SQLite evidence;
  the valid fixture resolves inside the fixed root.
- **Implementation boundary:** `pathlib`, standard-library JSON, existing
  packet validation; no dependency, shell/Git, network, or credential client.
- **Proportionality ceiling:** one fixture root and one fixture per packet; no
  general filesystem sandbox or broader containment claim.
- **Stop and escalation:** stop for real repository, arbitrary path, credential,
  network lookup, or stronger filesystem assurance requirements.

### Q2 — Complete and honest binding inventory

- **Protected outcome:** no result is registration-ready unless every leaf in
  the required-facts table is present, valid, and non-conflicting.
- **Operating/threat/failure model:** trusted synthetic JSON may omit any leaf,
  include an unknown/wrong-typed field, invalid exception disposition, or a
  declared conflict.
- **Explicit exclusions:** real policy reconciliation, defaults, repository
  parsing, adapter/binding-PR creation, and secret value collection or lookup.
- **Assurance level:** strict normalization to an owner-readable inventory;
  only a complete snapshot gets a proposed binding.
- **Sufficient acceptance proof:** a complete-fixture test asserts the exact
  normalized schema and every required leaf; parameterized tests remove each
  leaf and prove non-reviewability; fixtures cover a conflict, malformed/unknown
  input, and both exception dispositions.
- **Implementation boundary:** one parser/normalizer and structured JSON
  evidence; no policy engine, language inference, or auto-repair.
- **Proportionality ceiling:** only the seven M0-D02 areas and finite fixture
  dispositions; no universal editor or multi-project registry.
- **Stop and escalation:** a need to infer, reconcile, or choose project policy
  returns the named inventory to Architecture/Owner without worker correction.

### Q3 — Durable idempotent evidence and bounded handoff

- **Protected outcome:** one packet produces one immutable inventory,
  proposal-or-escalation result, digest, and terminal handoff.
- **Operating/threat/failure model:** duplicate CLI requests, local contention,
  and replay/restart after an existing claim or terminal state are in scope.
- **Explicit exclusions:** distributed coordination, multiple coordinators,
  real-project state, lease renewal, artifact stores, notifications, Atlas/API,
  and guarantees beyond the existing one-process synthetic model.
- **Assurance level:** the existing atomic claim controls one packet key; new
  SQLite evidence is tied to it and preserved on replay.
- **Sufficient acceptance proof:** complete/missing/conflict cases have one
  durable result; duplicate/restart/competing-claim tests prove no second
  executor or overwritten result; outcomes have review or escalation handoff.
- **Implementation boundary:** existing SQLite transaction pattern plus
  standard-library JSON/SHA-256; Maestro storage is sole writer.
- **Proportionality ceiling:** additive local evidence only; no migration
  framework redesign, queue, daemon, scheduler, remote lock, or state machine.
- **Stop and escalation:** stop for real identity, distributed lease,
  backup/recovery redesign, or a second correction cycle.

## Required checks

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m unittest discover -s ../../tests/alpha_03 -v
python -m maestro.cli run-packet \
  --packet ../../fixtures/alpha/alpha-03-complete-discovery-packet.json \
  --runtime-dir ../../var/alpha-03-check
```

Passing is sufficient when every named suite passes, the command records a
complete synthetic inventory/proposed binding and `AwaitingReview`, and runtime
artifacts remain in the ignored isolated runtime directory.

## Explicit exclusions

- Foundry, VennueSign, or any real repository/project access or modification.
- Git/GitHub, CI, network, webhooks, cloud services, credentials, secret
  providers, or secret values.
- Project commands, adapters, binding PRs, dry runs, or real registration.
- Atlas/API/UI, notifications, queues, scheduling, worker dispatch, backup,
  recovery, USB, retention, review execution, merge, or successor selection.
- Any change to Alpha-01's M0-D11 boundary.

## Rework and handoff

M0-D05 permits one targeted correction only for committed in-scope work that
fails a named gate. Missing commits/diffs, scope/dependency/configuration/
placeholder violations, or a missing/infeasible contract escalate immediately.

A valid result is one scoped non-default-branch commit, all checks passing,
fixture-only evidence, and no prohibited access. Fresh independent
implementation review follows. Approval does not merge or authorize real
registration.
