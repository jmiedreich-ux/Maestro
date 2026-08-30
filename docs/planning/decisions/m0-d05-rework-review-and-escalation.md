# M0-D05 — Rework, Independent Review, and Escalation

**Status:** Proposed baseline for M0 acceptance  
**Decision owner:** Maestro project owner  
**Scope:** Process policy only; it does not grant automatic merge or change a joined project's stricter review rule.

## Decision

Maestro uses bounded, evidence-based rework. A worker receives one targeted correction for a mechanically or behaviorally specific failure. A second failure, a scope conflict, or a missing/changed authority stops the normal loop and escalates visibly instead of allowing endless autonomous retries.

## Worker rework

| Situation | Required action |
|---|---|
| Scope, build, test, invariant, or explicitly stated acceptance check fails | Send the worker one rework instruction containing the exact failed evidence and a narrow fix boundary |
| Rework passes | Continue to Integration or independent review |
| Rework fails again | Stop that attempt; escalate to Maestro for a different eligible route or a stronger cloud agent |
| Failure exposes an unclear requirement, contract, dependency, or product decision | Stop and create a visible question/`NeedsReplan` state; do not guess or redesign locally |
| Failure is a transient environment/service issue | Retry only under the adapter's explicit recovery policy, recording each attempt |

## Independent review

1. Every mergeable PR or equivalent merge unit receives independent review by someone other than its author or integrator.
2. A review may approve, request a defined correction, or raise a planning/architecture question.
3. One defined review-correction cycle is allowed: author corrects the stated findings, then the same unit is independently re-reviewed.
4. A second request for changes on the same unit escalates to Maestro and the designated stronger review/implementation route. It does not silently start a third ordinary loop.
5. A finding that requires a changed plan, scope, dependency, authority, or product decision enters `NeedsReplan` or owner decision regardless of round count.

## Escalation destinations

| Reason | Destination |
|---|---|
| Bounded implementation failure | Stronger eligible implementation route or Maestro integration route |
| Integration conflict or shared-boundary issue | Integration Agent, then independent review if code changes |
| Architecture/contract ambiguity | Project Architecture Agent / `NeedsReplan` |
| Product trade-off or authority decision | Owner decision record |
| Security, credential, deployment, or production-risk issue | Stop and escalate under the project adapter's explicit policy |

## Visibility

Atlas and Slack show the current round, exact failure, evidence reference, chosen escalation destination, and whether work is blocked on a person, a new plan, or a stronger agent route. No retry happens invisibly.

## Guardrails

- Rework fixes the stated failure; it may not expand scope.
- An agent never reviews its own work as independent review.
- A stronger model route does not override a project's policy, locks, or acceptance gates.
- Owner escalation is for a genuine decision or delegated authority boundary, not ordinary routine fixes.
- Joined-project policies may require stricter review or fewer rework attempts, but never a weaker rule.
