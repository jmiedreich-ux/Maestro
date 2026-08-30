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

## Gate rule

Maestro may not execute the proposed work while a `missing`, `changed`,
`new assumption`, unresolved conflict, or unapproved deferral remains. The
review result and its resolved traceability table are durable evidence for the
run.

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
