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
- [M0-D12 — Bounded Quality Contracts and Proportionality](../../docs/planning/decisions/m0-d12-bounded-quality-contracts.md) applies to every material quality requirement. Architecture must define the protected outcome, operating/threat/failure model, explicit exclusions, practical assurance level, sufficient acceptance proof, permitted implementation boundary and complexity, proportionality ceiling, and exact stop/escalation rule before dispatch. Passing the named proof is the definition of enough; a materially incomplete contract returns to Architecture and the Owner instead of creating repeated worker corrections.
- Independent review is full once. After correction, the same independent reviewer normally performs a targeted follow-up limited to the named findings, correction-only diff, and directly affected consistency. Full scope reopens only for a recorded base/range, unrelated-scope, shared-contract, evidence, or independence change.
- Every default-branch merge has complete current review coverage: one exact full reviewed range plus all targeted-reviewed correction-only diffs covering the final head. Uncovered or materially stale changes block merge.
- Every plan, milestone, packet, and build instruction must pass independent
  Decision Fidelity Review before execution. The review records every accepted
  choice as `included`, `missing`, `changed`, `new assumption`, or
  `approved deferral`. Any unresolved non-included result blocks execution.

## Current checkpoint

The owner-approved M0-D12 process package, M0-D05 targeted-review rule, and
complete Architecture, Decision-Fidelity, and Implementation-Review job roles
merged to `master` at `ac6471484268d8d6b11fb302dd1190ef85cbdae2`.
Default-branch merge candidates now require complete, current review coverage
without redundant rereview of unchanged material.

Alpha-01-R1 ran once at `e2c8a08`; its nine tests and repeated health checks
passed. Fresh Independent Implementation Review returned `REQUEST_CHANGES`
after demonstrating a same-UID post-directory-FD move outside `var/` and
finding incomplete outside-path CLI/direct-constructor coverage.

The Owner reconciled M0-D11 with M0-D12 for Alpha. The bounded model uses a
trusted local Linux identity and protects incorrect, outside, source-tree, and
pre-acquisition symlinked paths. It explicitly excludes a malicious concurrent
same-UID/root actor moving an already-open directory during SQLite's internal
opens. Alpha remains standard-library/`sqlite3` only. Stronger host assurance
is deferred to a separately approved future quality contract.

The prolonged earlier cycle remains recorded as an Architecture Agent failure.
The excluded post-FD move is not another Alpha gate. The coverage omission is
the only in-scope implementation defect.

[Alpha-01-R2 — Complete Bounded Local Foundation](../../docs/planning/packets/alpha-01-r2-complete-bounded-foundation.md)
is the proposed final repair. Its exact next gate is one fresh complete Decision
Fidelity Review of the planning branch. If approved and merged with complete
review coverage, it authorizes one isolated implementation run only. No
Alpha-01 code merge or Alpha-02 action is authorized.

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
