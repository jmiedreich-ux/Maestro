# Maestro Bootstrap Convergence Policy

**Status:** Owner-approved on 2026-09-03  
**Applies to:** Maestro's own development until the durable Development Manager
control loop has completed an accepted qualification run  
**Precedence:** This policy controls wherever an older planning, review,
execution, correction, handoff, or role instruction conflicts with it.

## Purpose

Maestro must preserve decision fidelity and implementation quality while also
reaching an executable and terminal result. A role may not satisfy its local
SOP by creating an unbounded planning, review, correction, or supersession
cycle for the system as a whole.

## Bootstrap work slice

A bootstrap work slice is the complete delivery episode from one approved
outcome contract through implementation, independent implementation review,
correction if authorized, acceptance, and merge or terminal return.

The slice identity and its correction budgets survive packet rewrites,
replacement packets, branch changes, role reassignment, and Coordinator
takeover. None of those events creates a fresh attempt or resets a review or
correction allowance.

Every slice records:

- one immutable slice ID;
- one accepted outcome and one canonical quality contract;
- exact authority, base, writable paths, named proof, and exclusions;
- the current actor and live execution evidence;
- planning-review and implementation-correction counts;
- one terminal state: merged, returned, cancelled, or owner-stopped.

## One canonical contract

M0-D12 is authored once for the slice and referenced by its milestone, packet,
build instruction, worker prompt, and reviews. Those carriers may narrow paths
or sequence without duplicating or silently strengthening the contract.

The Project Architect decides routine materiality, proportionality, and
not-applicable fields. Owner approval is required only for a reserved product,
security, data-ownership, irreversible, external-access, spending, production,
or direction choice.

Once Decision Fidelity approves the contract, it is frozen for that slice.
Passing its named proof is enough.

## Bounded review sequence

A slice receives:

1. one complete Decision Fidelity review before execution;
2. at most one targeted planning correction covering that review's complete
   blocking finding set;
3. execution against the frozen contract;
4. one complete independent implementation review of the exact final
   implementation candidate;
5. at most one targeted implementation correction; and
6. one targeted verification of that correction-only diff.

A mechanically derived build instruction does not receive another Decision
Fidelity review. Milestone acceptance does not repeat Decision Fidelity review;
it verifies that the reviewed slice evidence is complete.

A targeted follow-up may not add an ordinary blocker. A new concern blocks an
active slice only when reproducible evidence proves one of the following:

- the frozen named proof cannot establish its stated protected outcome;
- continuing would create a credible risk of data loss, credential disclosure,
  unauthorized external or production action, or an irreversible change; or
- the reviewed candidate contains unrelated or unreviewed changes, making the
  exact review range invalid.

Everything else is recorded as a non-blocking learning candidate for a later
slice. A disagreement about ordinary materiality is decided by the Project
Architect and does not return to the Owner.

## Terminal correction behavior

A failed targeted planning follow-up returns the slice; it does not create a
replacement packet with a fresh planning correction.

A failed targeted implementation verification returns the slice. No worker,
Coordinator takeover, additional correction, renewed full review, or additional
targeted verification remains for that slice.

Any critical exception immediately stops the current slice and records one
terminal state: `returned` for a proof/contract or candidate-integrity defect,
`cancelled` when the authorized work is withdrawn, or `owner-stopped` when
the Owner ends the slice. Safety or contract remediation requires a separately
approved slice with a new identity. It cannot resume, reclassify, or reset the
terminal slice or its exhausted allowances.

A new ordinary failure class discovered after an allowed correction is recorded
as a learning candidate and the current slice is approved or returned solely
against its frozen contract and named proof.

## Bootstrap Coordinator takeover

Coordinator takeover is available only while an implementation review allowance
still exists:

- Before the initial implementation review, the Coordinator may complete a
  delegated worker's non-delivery and submit the resulting exact candidate to
  the slice's one full implementation review.
- After the full review, but only while the sole implementation correction is
  unused, the Coordinator may perform that one named correction and submit its
  correction-only diff to the slice's one targeted verification.
- After the targeted verification fails, no takeover, correction, or review
  remains. The slice is `returned`.

The takeover:

- is recorded as a role change within the same slice;
- does not reset review or correction counts;
- may not change product behavior, architecture, scope, or the quality contract;
- must produce the candidate appropriate to the remaining review phase and
  rerunnable evidence; and
- is reviewed by an independent agent that did not author the takeover.

If completion requires a contract or reserved decision change, the Coordinator
terminally returns the slice instead of improvising. Any remediation is a new,
separately approved slice and cannot renew the returned episode.

## Learning quarantine

R3/R4 findings, process observations, and proposed invariants are written to a
learning-candidate record. They do not amend shared policy, templates, active
packets, or the current slice automatically.

After the slice is terminal, the Project Architect may propose a separate,
evidence-backed policy change. It becomes governing only after its own explicit
approval. Repeated prose generated by a failed loop is not authority.

## Progress and evidence

A slice is `Running` only with a live process or agent handle, a current packet
item, and a fresh observation. Assignment or conversation is not execution.

Each coordination check-in states the actor, completed item, active item,
latest command or artifact, next item, blocker, and ETA/confidence or
`unknown`.

Progress is measured by accepted code and passing named proof. Planning volume,
review length, messages, assignments, and status inquiries are not progress.

## Exit from bootstrap mode

This policy remains active until one Maestro slice completes the full
plan-to-merge path with durable claims, wake/reconciliation, exact review
coverage, correction accounting, and Atlas/repository agreement without Owner
intervention on a routine decision.

Exiting bootstrap mode requires a separate Owner-approved decision supported by
that qualification evidence.