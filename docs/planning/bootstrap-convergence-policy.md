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

## Risk-based finding disposition

A reproducible defect is not automatically mandatory rework. Before any
correction is authorized, the independent reviewer reports the finding and the
Project Architect decides its release disposition.

For every finding, the review records:

- the reproduction and affected behavior;
- the real operating conditions required to encounter it;
- measured occurrence data when available, otherwise an evidence-based
  likelihood of `rare`, `unlikely`, `possible`, `likely`, or `expected`;
- consequence, affected reach, detectability, recovery, and workaround;
- the cost and regression risk of fixing it now; and
- whether it threatens the slice's primary outcome or a critical exception.

The Project Architect assigns exactly one disposition:

1. **correct now** — the expected operational risk justifies using the slice's
   one correction;
2. **accept known limitation** — the defect is real, but the primary product
   outcome works and its expected likelihood and consequence are acceptable for
   this release;
3. **reject finding** — evidence does not establish the claimed defect; or
4. **return slice** — the primary outcome does not work, the risk is
   unacceptable, or correction cannot fit the remaining boundary.

An accepted known limitation may be inside the frozen contract. It is an
explicit release variance, not a claim that the failed criterion passed and not
a silent contract rewrite. It requires a linked backlog issue recording the
exact reviewed head, evidence, occurrence conditions, likelihood basis,
consequence and reach, detection/recovery/workaround, acceptance rationale, and
a concrete revisit trigger such as an observed occurrence, exposure change,
threshold, or named later milestone.

Accepting a known limitation changes no code, consumes no correction allowance,
and requires no targeted implementation verification. The exact independently
reviewed candidate may advance with status `accepted-with-known-limitations`.
The reviewer finding remains truthful and the backlog issue remains open.

A reviewer `REQUEST_CHANGES` is a recommendation pending Architect
disposition; it does not automatically dispatch the developer. Routine risk is
the Project Architect's authority. Only reserved product, legal/compliance,
security, data-loss, authorization, external/production, irreversible,
spending, or direction risk returns to the Owner.

A critical exception, unverifiable review range, or failure of the primary
promised outcome cannot be accepted through this path. High likelihood combined
with material impact is presumptively corrected or returned; any routine
exception requires explicit evidence and rationale.

This rule is prospective. It does not reopen, refund, or reclassify a completed
or terminal slice.

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