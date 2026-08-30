# Alpha-02 — Establish Synthetic `maestro run-packet` Lifecycle Wrapper

**Status:** Approved for one isolated implementation run after this exact planning package merges to `master`. Decision Fidelity Review has complete coverage through `c54f5bb66315137f0b8bc9fe44ca168cf18cfcc3`; no implementation, merge, or successor work is authorized by this branch alone.  
**Owner:** Jeremy Miedreich  
**Authority:** [Maestro Alpha Decision-Fidelity Review](../maestro-alpha-decision-fidelity-review.md); [M0-D01 — Maestro Operational Database](../decisions/m0-d01-operational-database.md); [M0-D05 — Tested Escalation and Local-Worker Routing Rule](../decisions/m0-d05-rework-review-and-escalation.md); [M0-D12 — Bounded Quality Contracts and Proportionality](../decisions/m0-d12-bounded-quality-contracts.md)  
**Predecessor:** Alpha-01 complete at independently approved head `3124378f3ba885cb066d1426b1a0ed5a5d0ccb6f`, merged to `master` at `4cc8e6fa899574e27515f225be1976c9f9f1a6ff`.  
**Execution class:** One focused implementation run in a clean isolated worktree  
**Worker route:** Local synthetic-wrapper implementation route  
**Reviewer route:** Fresh Independent Implementation Reviewer after a full Decision Fidelity Review approves this exact packet  
**Timeout:** Stop and report if the complete synthetic lifecycle cannot be finished in one focused run.

## Outcome

Create Maestro's first complete, testable, **synthetic-only** `maestro run-packet` lifecycle wrapper. Given one already-approved synthetic packet, it validates the packet and its authority fields, obtains one exclusive local claim and isolated worktree, invokes one synthetic local worker, persists lifecycle and evidence facts in the existing SQLite database, grades named gates, makes at most one eligible targeted-correction handoff, and records a non-bypassable independent-review handoff before stopping.

This is a local proof of Maestro's control boundary. It does not join, inspect, modify, or coordinate a real project.

## Required public behavior

1. `maestro run-packet` is the sole Alpha packet-wrapper command. It accepts one local synthetic packet input and an explicitly supplied or safe-default runtime directory.
2. Before mutation or worker launch, it rejects a packet that lacks:
   - a concise task title and stable packet identifier;
   - an approved authority/fidelity reference;
   - declared owned paths;
   - named validation commands/gates;
   - a permitted synthetic executor declaration;
   - an independent-review route; or
   - an explicit owner-stop boundary.
3. A valid packet creates one durable run/packet attempt, acquires one idempotent local claim, creates one isolated temporary worktree for the synthetic fixture, and records start facts.
4. The wrapper invokes only the approved synthetic local executor declared by the fixture. It must capture its exit result, commit fact, scoped-diff fact, gate results, and bounded logs/evidence metadata.
5. A valid committed, in-scope result that passes every named gate becomes `AwaitingReview`; the wrapper records the independent-review handoff and stops. It does not perform independent review, merge, select a successor packet, or dispatch another packet.
6. A missing scoped diff, missing required commit, dependency/configuration/placeholder violation, or out-of-scope result is rejected immediately. The wrapper records a durable rejection/escalation handoff for coordinator ownership and stops; it does not receive a correction round or autonomously reassign work.
7. Only a committed, in-scope result that fails one named gate is eligible for one exact targeted-correction handoff under M0-D05. The wrapper records that eligibility and stops; it does not autonomously re-run a worker or invent the correction.
8. Duplicate invocation, replayed completion, restart after a recorded transition, and contention for the same packet claim do not launch a second worker, duplicate terminal evidence, or overwrite prior facts.
9. All lifecycle changes and evidence facts are persisted through the existing service-owned SQLite storage boundary. Atlas remains absent and has no command or database-write path.

## Owned implementation paths

Implementation is limited to:

- `services/maestro/maestro/packet_contract.py`
- `services/maestro/maestro/packet_wrapper.py`
- `services/maestro/maestro/lifecycle.py`
- `services/maestro/maestro/storage.py`
- `services/maestro/maestro/cli.py`
- `tests/alpha_02/**`
- `fixtures/alpha/**`
- `docs/architecture/alpha-02-run-packet-wrapper.md`
- `docs/operations/alpha-02-run-packet.md`

The implementation may make the smallest necessary test-support adjustment inside an owned Alpha-01 package path only if Alpha-02's named proof cannot otherwise execute. It must name and justify that adjustment in its result. No other path is permitted.

## Complete bounded quality contracts

### Q1 — Packet authority and permission validation

- **Protected outcome:** an incomplete, unapproved, or ambiguously permitted packet cannot cause local mutation or worker launch.
- **Operating model:** one trusted local Linux user provides a local synthetic packet file; malformed content and ordinary operator misuse are in scope.
- **Explicit exclusions:** malicious same-UID/root tampering after a safe local file has been opened, cryptographic signatures, remote packet delivery, external identity systems, and real project policy enforcement.
- **Assurance level:** deterministic local validation of every required field before claim, worktree creation, or executor launch.
- **Sufficient proof:** focused tests prove each missing/invalid required field is rejected with no run, claim, worktree, worker, or evidence artifact; a valid fixture proceeds.
- **Implementation boundary:** Python standard library, the existing service package, declarative synthetic fixtures, and SQLite only.
- **Proportionality ceiling:** no schema language, signature framework, provider integration, or general policy engine.
- **Stop and escalation:** stop and return to Architecture/Owner if a real-project authority, signature, credential, or remote-delivery requirement becomes necessary.

### Q2 — Single local execution and idempotent durable lifecycle

- **Protected outcome:** duplicate command invocation, replay, restart, or local contention cannot run the same synthetic packet twice or produce contradictory lifecycle records.
- **Operating model:** one Maestro process on the Linux AI box; duplicate CLI requests, process restart, stale completion, and ordinary local contention are in scope.
- **Explicit exclusions:** multi-coordinator leadership, network partitions, distributed locking, remote workers, crash-safe execution of arbitrary third-party programs, and hostile same-UID/root interference.
- **Assurance level:** one durable claim and monotonic, idempotent local state transitions for one packet key.
- **Sufficient proof:** tests demonstrate duplicate invocation/replayed completion/restart preserve one attempt and terminal result; a competing claim is rejected or reported as already held without launching another worker.
- **Implementation boundary:** SQLite transactions and the standard library only; storage remains the sole database writer.
- **Proportionality ceiling:** no queue scheduler, lease-renewal service, daemon, external lock provider, or multi-process coordinator.
- **Stop and escalation:** stop if delivery requires multi-machine coordination, real process supervision, or a lease/recovery model beyond one local synthetic run.

### Q3 — Evidence, grade, and review-handoff integrity

- **Protected outcome:** a synthetic result cannot be treated as reviewable without the named commit, scope, and gate evidence; no rejection becomes an unbounded retry loop.
- **Operating model:** the approved synthetic executor returns controlled fixture outputs for success, named-gate failure, missing commit/diff, and out-of-scope cases.
- **Explicit exclusions:** validating a real GitHub PR, executing real CI, parsing untrusted model prose, automatic correction, independent review execution, and merge authority.
- **Assurance level:** durable, inspectable evidence records tied to one packet attempt and a deterministic M0-D05 outcome.
- **Sufficient proof:** tests cover successful `AwaitingReview` handoff, immediate non-delivery rejection with durable coordinator-escalation handoff, dependency/configuration/placeholder and out-of-scope rejection, one eligible targeted-correction handoff, preservation of captured evidence, and wrapper stop after each outcome.
- **Implementation boundary:** synthetic fixture repository/worktree and local command output only; no external network, credentials, or real repository.
- **Proportionality ceiling:** evidence remains local structured metadata plus bounded captured output; no artifact store, notification system, or Atlas presentation.
- **Stop and escalation:** stop if required evidence needs a real project, external CI/provider, secret, or a second correction cycle.

## Required checks and sufficient acceptance evidence

The implementation result must run and record:

```bash
cd services/maestro
python -m unittest discover -s ../../tests/alpha_01 -v
python -m unittest discover -s ../../tests/alpha_02 -v
python -m maestro.cli run-packet --packet ../../fixtures/alpha/approved-success-packet.json --runtime-dir ../../var/alpha-02-check
```

The named proof is sufficient when it shows:

- Alpha-01's 11 focused foundation tests still pass;
- Alpha-02 tests cover every required public behavior and each Q1–Q3 proof case;
- the successful command records an `AwaitingReview` handoff and stops without review, merge, successor selection, or a second worker launch;
- all generated runtime, worktree, fixture, and cache artifacts stay inside the isolated worktree and its ignored `var/` area; and
- no Foundry, VennueSign, GitHub, network, credential, Atlas/API/UI, project registration, or USB recovery action occurs.

Passing these named checks is the definition of enough for Alpha-02.

## Explicit exclusions

This packet must not:

- register or inspect a real project, create an adapter, bind Foundry, or touch VennueSign;
- invoke a real coding/model agent, GitHub, CI, Slack, webhooks, cloud services, credentials, or secrets;
- create Atlas, a read API/SSE, a browser UI, project queues, scheduling, notifications, or multi-packet dispatch;
- independently review, merge, push to `master`, select a successor packet, or automatically perform a correction;
- introduce dependencies, background daemons, remote listeners, service accounts, privileged helpers, native extensions, or a distributed lock/queue;
- alter Alpha-01's bounded M0-D11 assurance or claim containment against malicious same-UID/root interference; or
- implement backup/restore, USB provisioning, retention, project registration, or post-Alpha onboarding.

## Proportionality and stop rule

This packet proves one synthetic wrapper lifecycle, not a production agent fleet. Use the smallest standard-library and SQLite design that satisfies the named evidence. M0-D05 permits one targeted correction only for an eligible committed, in-scope named-gate failure; a newly discovered missing quality model, real-project requirement, security/credential decision, distributed-execution need, or other excluded concern stops the work and returns it to Architecture/Owner.

## Completion and handoff

A valid implementation result has one scoped commit on a non-default branch, all named checks passing, complete fixture-only evidence, no external access, and no unsupported assurance claim. It receives one fresh full Independent Implementation Review against this exact approved packet. Approval does not merge or start the next Alpha increment.

## Decision-fidelity carrier map

| Governing choice | Alpha-02 carrier |
| --- | --- |
| Mandatory local `maestro run-packet` boundary | Sole wrapper command and required lifecycle behavior |
| Synthetic-only Alpha | Local synthetic packet, executor, fixture repository, and explicit external exclusions |
| M0-D05 graded escalation | Deterministic reject/eligible-correction/review-handoff outcomes; no autonomous retry |
| M0-D01 service-only operational writer | Lifecycle, evidence, claim, and attempt records pass through service storage |
| Atlas read-only boundary | No Atlas/API/UI or command path |
| One milestone then owner gate | Wrapper stops after its single review handoff |
| Linux-first local operation | Local Python/SQLite execution and isolated worktree |
| M0-D12 bounded quality contracts | Q1–Q3 define the required proof, exclusions, complexity limits, and stop points |
| Project registration deferred | Explicit exclusion; no project adapter or real repository |
| USB recovery deferred | Explicit exclusion; no backup/restore work |
