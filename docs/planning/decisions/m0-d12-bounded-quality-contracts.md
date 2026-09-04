# M0-D12 — Bounded Quality Contracts and Proportionality

**Status:** Accepted  
**Scope:** Every Maestro architecture plan, milestone, packet, build instruction, implementation review, and quality gate  
**Authority:** Owner decision, 2026-08-30

## Decision

A quality requirement is not executable merely because it uses a desirable word
such as secure, safe, robust, reliable, scalable, fast, compatible, accessible,
complete, production-ready, or race-safe. Before work is dispatched, the
Architecture Agent must turn every material quality requirement into a bounded
quality contract that tells every agent what is required, what is not required,
what proof is sufficient, and when to stop.

This rule applies to every material quality requirement, including security,
privacy, correctness, data integrity, concurrency, performance, availability,
recovery, compatibility, accessibility, observability, and maintainability.

## Required quality contract

Each material quality requirement must state:

1. **Protected outcome:** the concrete harm or failure the requirement prevents.
2. **Operating and threat model:** the actors, privileges, environments,
   concurrency, inputs, failures, and misuse that are in scope.
3. **Explicit exclusions:** actors, privileges, failures, adversarial behavior,
   platforms, and assurance levels that are out of scope.
4. **Assurance level:** the practical level required for this milestone, rather
   than an implied absolute guarantee.
5. **Acceptance proof:** named checks, observations, and evidence that are
   sufficient to pass.
6. **Implementation boundary:** permitted dependencies, platform facilities,
   complexity, and owned components.
7. **Proportionality ceiling:** the effort and design complexity justified by
   the packet's value and milestone.
8. **Stop and escalation rule:** the exact condition that ends implementation
   work and returns a missing assumption, infeasible guarantee, or newly
   discovered risk to Architecture and the Owner.

All eight elements are required. If an element is genuinely inapplicable, the
contract must state the reason and carry an explicit owner-approved
not-applicable disposition. An unstated or unjustified omission makes the
packet unready for Decision Fidelity Review or implementation.

## Definition of enough

When the named acceptance proof passes within the approved model and boundary,
the requirement is satisfied. Implementors and reviewers may not silently
strengthen the requirement, introduce a new threat model, or continue pursuing
unbounded edge cases.

A reviewer may record an out-of-contract risk as a non-blocking observation or
architecture follow-up. If the risk shows that the approved contract itself is
materially incomplete, the reviewer must identify an **architecture-contract
defect** and stop the packet. The finding returns to Architecture and the Owner;
it is not sent through repeated worker corrections.

M0-D05 still permits only one targeted correction for committed, in-scope work
that fails a named gate. A later finding from a different failure class, a
missing model assumption, or an infeasible guarantee is an architecture
escalation, not another correction round.

## Architecture accountability

The Architecture Agent owns the completeness, feasibility, proportionality, and
stopping boundary of the quality contract. Decision Fidelity Review checks that
the contract carries the owner's accepted expectations before dispatch.
Implementors build only that contract. Independent reviewers judge the result
against it.

Security or quality language without these boundaries is an architecture
failure, even when downstream agents correctly follow the words they were
given.

## Alpha-01 lesson

Alpha-01 was intended to establish a small Linux-first Python and SQLite local
foundation. M0-D11 stated an absolute runtime-containment rule without fully
defining the threat model, assurance level, feasible implementation boundary,
sufficient proof, or point at which agents must stop. This allowed a small
foundation packet to expand through repeated implementation and review cycles.

That delay is recorded as an Architecture Agent failure. It is not assigned to
the implementors or independent reviewers that correctly applied the approved
language. Alpha-01 remains paused until M0-D11 is reconciled with this decision;
no merge or Alpha-02 action is authorized by M0-D12.

## Bootstrap convergence amendment — Owner-approved 2026-09-03

The [Maestro Bootstrap Convergence Policy](../bootstrap-convergence-policy.md) controls Maestro's own development until the durable loop completes its accepted qualification run. Its slice-wide identity, frozen-contract rule, bounded review sequence, correction budgets, terminal return behavior, Coordinator takeover, and learning quarantine override any conflicting earlier language in this decision.

The eight fields are authored once in the slice's canonical contract and referenced rather than recopied into every carrier. The Project Architect approves routine materiality and not-applicable dispositions. Owner approval is reserved for the policy's named material choices. After Decision Fidelity approval, the contract is frozen; an ordinary later concern cannot strengthen it or reopen planning for the active slice.

## Risk-based release variance — Owner-approved 2026-09-04

Named proof remains the definition of contract satisfaction, but contract
satisfaction and release acceptance are recorded separately. A failed
individual criterion is never reported as `PASS`; the Project Architect may
nevertheless accept the exact reviewed candidate with a known limitation when
the primary outcome still works and the evidence-based likelihood and
consequence are acceptable under the approved operating model.

The [risk-based finding disposition](../bootstrap-convergence-policy.md#risk-based-finding-disposition)
governs that variance. It requires a durable issue and rationale, consumes no
correction when code is unchanged, and cannot waive a critical exception,
reserved Owner risk, unverifiable evidence/range, or failure of the primary
promised outcome.
