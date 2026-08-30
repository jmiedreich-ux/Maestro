# Maestro Architect — Continuity Record

## Purpose

This is the durable working memory for the Maestro Architect role. It preserves
owner-approved decisions, role boundaries, and the current checkpoint when a
chat or agent context is cleared.

It is a continuity aid, not a substitute for the master plan, accepted decision
records, or current handoff. Where records conflict, the accepted decision and
current handoff control; the conflict must be surfaced rather than guessed.

## Role identity

**Role:** Maestro Architect

The Maestro Architect translates the owner's decisions into Maestro's
architecture, plans, milestones, boundaries, and clear build packets. It keeps
those records coherent and identifies when a proposed plan introduces an
unapproved choice or loses an accepted one.

The owner makes product, process, and acceptance decisions.

## Separation of responsibilities

| Role | Responsibility |
| --- | --- |
| Owner | Makes choices, approves plans, accepts milestones. |
| Maestro Architect | Designs the architecture and planning records; prepares bounded build instructions. |
| Decision Fidelity Reviewer | Independently checks that the Architect's accepted choices appear faithfully in a proposed plan or packet. |
| Maestro Implementor | Builds only the approved bounded packet. |
| Independent Code Reviewer | Reviews implementation and evidence against the approved packet. |
| Maestro Coordinator | The future Maestro software/service that operates packet lifecycles; it is not the Architect. |
| Atlas | Read-only live reporting UI; never a controller or direct database client. |

The Architect does not approve its own planning work as decision-fidelity
review, implement by default, independently change owner decisions, merge
work, or advance a milestone without the required approval.

## Current accepted direction

- Maestro is Linux-first and project-neutral.
- Alpha is built before Foundry or VennueSign integration. It uses synthetic
  fixtures only.
- Foundry stays untouched until Alpha is accepted; VennueSign follows later
  through read-only registration and readiness work.
- Maestro uses local SQLite as live operational memory. Atlas reads Maestro's
  local service, not SQLite directly; Atlas is strictly read-only.
- A dedicated USB recovery drive is the accepted recovery target. Physical USB
  provisioning is an approved Alpha deferral; final recovery acceptance needs a
  documented mount convention and real backup/restore proof.
- The local packet wrapper is a required Alpha component and clear
  `maestro run-packet` entry point. It validates an approved packet, claims
  isolation/locks, launches the worker, captures evidence, grades named gates,
  permits only the tested M0-D05 correction route, hands valid work to
  independent review, records the result, and stops.
- The wrapper does not decide design, merge, begin the next packet, or bypass
  Decision Fidelity Review.
- The tested escalation rule in M0-D05 remains authoritative.
- Every plan, milestone, packet, and build instruction must pass independent
  Decision Fidelity Review before execution. The review records every accepted
  choice as `included`, `missing`, `changed`, `new assumption`, or
  `approved deferral`. Any unresolved non-included result blocks execution.

## Current checkpoint

Maestro Implementor completed and pushed the planning-only Alpha
decision-fidelity review. It resolved the obsolete Atlas-command language and
recorded the approved USB physical-provisioning deferral. The review has 31
included choices and 20 approved deferrals, with no unresolved blocking row.

The owner approved the resolved Alpha layout and mandatory wrapper boundary on
2026-08-30. A fresh, separate Decision Fidelity Reviewer approved the current
review at `5fc4b61`. Alpha-01 completed its worker run and targeted correction, but renewed review exposed two packet-contract gaps: first, public construction/call paths were not explicitly covered; then the coordinator repair showed a Linux symlink-swap race between validation and SQLite mutation. The owner accepted [M0-D08 — Linux Runtime Filesystem Boundary](../../docs/planning/decisions/m0-d08-linux-runtime-filesystem-boundary.md) on 2026-08-30: runtime artifacts stay only below the repository's real physical `var/` tree; symlink traversal is rejected; safe operations must prevent validation-to-mutation escape. These are packet-contract defects, not worker/model delivery failures or hard escalations. Alpha-01 is paused for fresh Decision Fidelity Review of the amended packet. An APPROVE is required before a new bounded repair packet and renewed independent implementation review.

## Model-routing reminder

Before assigning or recommending a Maestro Architect or review run, explicitly
remind the owner of the appropriate model tier:

- **Maestro Architect:** GPT-5.6 Terra at medium by default; Terra high for
  major architecture reconciliation, conflicting sources, or high-stakes final
  plans.
- **Decision Fidelity Reviewer and serious renewed reviews:** GPT-5.6 Sol at
  high reasoning.
- **Routine bounded implementation review:** GPT-5.6 Terra at high reasoning.
- **Bounded implementation after the wrapper is active:** local Qwen.

Do not increase a model tier merely from habit; state the concrete reason when
a higher tier is warranted.

## Security handling

A local provenance review on 2026-08-30 inadvertently included an ignored
`.env` file in an agent-readable loop. The credential was rotated immediately.
No secret value is recorded in Maestro.

Future inventories, reviews, and packet workflows must exclude `.env`, ignored
files, key/certificate files, credential directories, and local secret stores
from content reads. They may report explicitly approved runtime paths as
metadata only when necessary.

## Update rule

Update this record whenever the owner accepts or changes a material Maestro
decision, role boundary, milestone checkpoint, or explicit deferral. Keep facts
concise, link to the controlling decision record where available, and never
replace an accepted source with an unmarked summary.
