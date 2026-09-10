# Owner Direction — Complete the Real M1–M4 Build Path

**Date:** 2026-09-01
**Status:** Accepted Owner direction
**Scope:** Maestro implementation sequencing, proving boundary, and delegated approval

## Direction

The Owner directed Maestro to return to the already documented M1–M4 build
path in `sources/planning/maestro-alpha-1-handoff.md` and complete all four
milestones before an attended end-to-end test with the Owner.

This is not a request to redesign Maestro. The existing project-registration,
operational-state, Atlas, packet-wrapper, coordinator, recovery, role, and
review designs remain the implementation authority, subject to the explicit
corrections below.

## Explicit corrections to the later proving sequence

1. Maestro will not prove the loop on Foundry, VennueSign, or another live
   product project.
2. The end-to-end proving run will not use scripted actors, fabricated worker
   observations, fixture review judgments, or synthetic outcomes.
3. `maestro project create` will establish a new non-live project. Its agents,
   work, repository operations, commits, checks, Integration, review, waits,
   corrections, and failures are real.
4. The synthetic Alpha-04 qualification is no longer a prerequisite for real
   implementation or the attended proving run.
5. The dedicated **Maestro Developer** implements Maestro product features.
   The **Maestro Development Manager** is the runtime coordinator being built;
   it is not the bootstrap implementation worker.
6. The existing USB backup/recovery provisioning deferral remains in force.
   USB work is not a prerequisite for completing M1–M4 or beginning the
   attended non-live end-to-end test.

## Delegated approval boundary

The Project Architect holds the routine delegated approval path, expected to
resolve roughly 90% of decisions and handoffs. That includes faithful
materialization of accepted design into graphs and packets, routine packet
approval after independent Decision Fidelity review, architecture returns that
can be resolved inside accepted authority, and routine milestone acceptance.

The Owner is involved only for the reserved minority of genuinely material
choices: a changed product or architecture boundary, security/data/credential
or external-access boundary, accepted material risk, spending/budget policy,
production/deployment/merge authority, an infeasible quality contract, or a
choice the project policy explicitly reserves to the Owner. Ordinary waiting,
eligibility, locks, retries, one permitted correction, Integration, review, and
recovery do not become Owner decisions.

Independent Decision Fidelity and implementation review remain mandatory.
They check the Project Architect's and implementor's work; they do not replace
the delegated approval split.

## Existing implementation sequence to execute

1. **M1 — Build the core and register projects.**
2. **M2 — Merge Atlas into Maestro reporting.**
3. **M3 — Build real packet dispatch and enforcement.**
4. **M4 — Complete the persistent control loop.**

The complete path must run on Linux without an open chat turn. The final
attended proving run uses the newly created non-live project and stops at the
Project Architect acceptance boundary unless a genuinely reserved Owner choice
arises.

## Implementation authority

The Owner authorized the Project Architect to proceed, deliver the required
prompts to the Coordinator, Maestro Developer, Integration Agent, Decision
Fidelity Reviewer, and Independent Implementation Reviewer, and carry M1–M4
through completion. Exact implementation packets still require independent
Decision Fidelity approval before dispatch. No separate Owner release is
required for a routine packet that stays inside this accepted direction.

