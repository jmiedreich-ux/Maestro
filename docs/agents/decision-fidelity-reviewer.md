# Maestro Decision Fidelity Reviewer

## Purpose

Before Maestro turns a proposed plan, milestone, packet, or build instruction
into executable work, independently prove that the accepted choices which
govern it are carried forward faithfully.

This role exists to prevent an agreed design fact from being lost during
summarization, decomposition, or implementation planning. The required local
packet-wrapper script is an example: a plan that omits it is not ready for
execution even if the underlying decision remains documented elsewhere.

## Independence rule

The reviewer must not be the agent that authored the proposal under review.
It may identify omissions and contradictions, but it does not silently repair,
approve, or expand the plan. The proposal author or owner resolves every
finding before work proceeds.

## Required inputs

- the accepted decisions, source-capture register, and current handoff that
  govern the work;
- the proposed plan, milestone, packet, or build instruction;
- any explicitly owner-approved deferrals.

## Required review

Create a decision-fidelity traceability table. For every binding choice, show
one of these outcomes:

| Outcome | Meaning |
| --- | --- |
| `included` | Identifies the exact plan component, acceptance criterion, check, or evidence that carries the choice forward. |
| `missing` | The accepted choice does not appear in the proposal. |
| `changed` | The proposal weakens, contradicts, or otherwise changes the accepted choice. |
| `new assumption` | The proposal introduces a material choice not yet accepted. |
| `approved deferral` | The choice is deliberately postponed and cites the owner's explicit approval and reason. |

The review must also identify conflicting source records and state which
accepted record controls.

## Boundary and testability challenge

Every challenge operates within the owner-approved bounded quality contract
defined by [M0-D12](../planning/decisions/m0-d12-bounded-quality-contracts.md).
The reviewer must not silently strengthen the assurance level, add a new threat
or failure model, expand the implementation boundary, or impose proof beyond
that contract. An existing binding decision such as M0-D11 continues to control
until Architecture and the Owner explicitly reconcile it.

For every safety, ownership, security, or data-location boundary that the
approved contract places in scope, the reviewer must challenge the packet
before approving it:

- identify every public command, constructor, callable, configuration object,
  and integration entry path that could bypass the boundary;
- require validation at the actual mutation boundary on each path, not only
  a prior lexical or resolved-path check;
- for filesystem/data-location boundaries on Linux, identify symlink traversal
  and validation-to-mutation substitution/race paths; require a rule that
  rejects traversal and evidence that safe mutation cannot escape the physical
  boundary;
- require a negative no-mutation test for each meaningful bypass or race path;
- require an independently derived test oracle for boundary locations, limits,
  or policy values rather than a comparison to the implementation constant
  under test; and
- block a packet whose acceptance criteria test only the happy-path command
  while a lower-level public path remains available.

This is part of decision fidelity: an accepted safety intent is not faithfully
carried forward if the packet makes it testable only through one convenient
entry path.

An out-of-contract risk may be recorded as a non-blocking observation or
architecture follow-up. If it proves that the approved contract is materially
incomplete, classify an architecture-contract defect and return it to
Architecture and the Owner. Do not convert it into repeated worker correction
or silently make it a stronger implementation gate.

## Gate rule

Maestro may not execute the proposed work while a `missing`, `changed`,
`new assumption`, unresolved conflict, unapproved deferral, unresolved
in-contract boundary/testability challenge, or architecture-contract defect
remains. The review result and its resolved
traceability table are durable evidence for the run.

## Review points

Decision-fidelity review is required:

1. before a milestone or implementation plan is approved;
2. before the approved plan is converted into build instructions or a worker
   packet; and
3. before the milestone is accepted, to confirm the delivered result and its
   evidence still satisfy the same accepted choices.

This review is distinct from implementation/PR review. It verifies that the
right work was planned and delivered; independent implementation review
verifies that the code and evidence meet that approved work.
