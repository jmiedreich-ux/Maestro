# M0-D15 — Real M1–M4 Implementation and Non-Live Proving Path

**Status:** Accepted by the Owner on 2026-09-01  
**Scope:** Reconciliation of the already designed M1–M4 implementation path
with the proving-project and approval boundaries  
**Source:** [Owner direction — complete the real M1–M4 build path](../../../sources/planning/2026-09-01-real-m1-m4-implementation-direction.md)

## Decision

Maestro will implement the existing M1–M4 roadmap recorded in
`sources/planning/maestro-alpha-1-handoff.md`:

1. M1 builds the Linux service core, durable operational records, project
   create/register flows, authority loading, leases, idempotent transitions,
   and restart recovery.
2. M2 makes Atlas a local, read-only reporting application over Maestro's
   service-mediated operational projection.
3. M3 replaces fixture execution as the proving route with a real bounded
   packet compiler, isolated Git worktree, real agent executor, mechanical
   grading, evidence, and one M0-D05 correction.
4. M4 completes the persistent Development Manager loop through real
   Integration, independent review, reporting, notification, recovery, and
   the applicable acceptance stop.

The end-to-end proving target is a new non-live project established through
`maestro project create`. It is not Foundry, VennueSign, or another live
product project. Its repository, authority, work, agents, commits, checks,
handoffs, review, and operational events are real. Scripted actor identities,
fabricated observations, and fixture review outcomes cannot serve as
end-to-end acceptance evidence.

## Approval and return routing

The Project Architect is the normal approval and architecture-return authority.
After required independent review, the Project Architect may approve faithful
packets, accept routine milestone results, and resolve returns within accepted
project authority without a separate Owner turn.

The Development Manager owns operational next actions whose policy is already
defined. The Coordinator must not convert routine waiting, eligibility, locks,
polling, recovery, Integration, review, or the first permitted correction into
an Owner question.

Only a genuinely material reserved choice returns through the Project
Architect to the Owner: changed product/architecture/public contract,
security/data/credential/external-access boundary, accepted material risk,
spending/budget policy, production/deployment/merge authority, infeasible
quality contract, or another choice explicitly reserved by project policy.

## Superseded scope

- M0-D13's mandatory fixture-only Alpha-04 qualification before real
  implementation is superseded. Its useful eligibility, idempotency, patient
  status, correction, recovery, and stop semantics remain requirements, but
  they must be implemented and proven through real system behavior.
- M0-D10's choice of Foundry as the first proving project is superseded. Its
  read-only and non-disruption guardrails continue to apply if Foundry is
  registered later.
- M0-D14's honest context, usage, allowance, and `unavailable` rules remain
  controlling. Its Alpha-04 fixture-only proving restriction is superseded.
- The synthetic Alpha-04 proposal and readiness packet are not implementation
  authority and must not be merged or dispatched as the M1–M4 route.

## Preserved boundaries

- Repository/GitHub engineering facts remain authoritative; Maestro owns only
  operational state and observed projections.
- Maestro's Linux service is the only SQLite writer; Atlas is read-only and
  accesses state through the service.
- M0-D05's one-targeted-correction maximum and complete final-head review
  coverage remain mandatory.
- M0-D11 and M0-D12 continue to bound filesystem and quality assurance.
- Automatic merge, production deployment, autonomous successor milestones,
  live-product testing, multi-project parallelism, Murphy, and webhook
  transport are not inferred from this decision.
- The accepted USB provisioning deferral remains. USB backup/restore is not a
  gate for completing M1–M4 or beginning the attended non-live proving run.

## Release authority

The Owner authorized the Project Architect to materialize, independently
review, release, and accept routine M1–M4 implementation packets under this
decision. The dedicated Maestro Developer performs Maestro feature
implementation. The Coordinator manages bootstrap handoffs until the real
Development Manager can take them over. A separate Owner release is required
only when a packet crosses one of the reserved boundaries above.

