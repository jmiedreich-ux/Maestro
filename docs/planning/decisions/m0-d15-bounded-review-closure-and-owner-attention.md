# M0-D15 — Bounded Review Closure and Owner Attention

- **Status:** Accepted by the Owner on 2026-08-31; planning amendment pending
  fresh Decision Fidelity Review and merge
- **Scope:** Review finding eligibility, Architecture's routine closure
  authority, unattended daily operation, and the material Owner-attention gate
- **Source:**
  [Non-material completion delegation and review boundary](../../../sources/planning/2026-08-31-non-material-completion-delegation.md)

## Decision

Maestro is intended to finish or advance approved daily development without
requiring the Owner to supervise routine code and review decisions. Architecture
and the Coordinator own the ordinary 90% operating path. The Owner is reserved
for the material 10% path defined below.

### Review is bounded by the approved contract

A reviewer may block only for a concrete failure of an accepted decision,
packet requirement, owned-path/scope rule, required evidence gate, or M0-D12
bounded quality contract. Every blocking finding must provide:

1. the exact governing criterion;
2. reproducible evidence and the affected path/behavior;
3. the material consequence inside the approved model; and
4. the smallest in-scope correction or the exact reason Architecture must
   replan.

When the named sufficient proof passes and no such demonstrated violation
remains, the reviewer returns `APPROVE` and stops. Preferences, alternative
implementations, general hardening, speculative edge cases, refactors, or
stronger quality/proof standards are recorded as non-blocking observations.
They do not delay approval, correction closure, merge readiness, or unrelated
work.

A targeted follow-up remains limited to its named findings, the correction
diff, and directly affected consistency under M0-D05. It cannot reopen general
defect discovery.

### Architecture closes routine scope

Architecture is authoritative for the meaning and boundary of an approved
packet. If a reviewer marks an observation blocking without the four required
elements, the Coordinator routes it to Architecture. Architecture records one
of:

- **in-contract defect:** preserve the block and route the allowed correction
  or replan action;
- **material contract defect:** freeze affected work and request Owner judgment;
  or
- **non-blocking observation:** retain it for later planning and continue the
  approved gate.

Architecture may not change the accepted contract after seeing code, approve
implementation it authored, discard reproducible in-contract failures, weaken
tests, or grant merge/release authority. Its closure role prevents review-scope
expansion; independent implementation approval remains required.

### Owner-attention gate

Return to the Owner only when at least one of these is required:

- a product outcome, architecture direction, public contract, or approved
  behavior must change;
- scope, security, privacy/data ownership, credential, external-access,
  irreversible action, or accepted-risk boundary changes materially;
- a new dependency/provider, material spending or allowance policy, production
  action, release/merge authority, or priority tradeoff needs approval;
- the approved quality contract is infeasible or materially incomplete; or
- one Architecture-delegated superseding completion also exhausts its normal
  correction allowance, indicating the plan may be wrong.

Routine implementation choices, test additions, exact schema enforcement,
clerical packet corrections, and completion of an already accepted behavior do
not require Owner approval when they stay inside their approved boundaries.

### Unattended daily operation and Slack

The Owner may release a bounded day's work in the morning. Maestro continues
eligible work through worker, Integration, review, and current acceptance gates;
one blocked item does not idle independent approved work.

If material Owner input is needed, Maestro creates a durable decision request
containing the exact question, known facts, options, Architecture
recommendation, impact, response deadline, and safe no-response action. Slack
is the first intended delivery/reply channel under M0-D04. Only a reply tied to
the active decision ID from the configured Owner identity is accepted as the
answer. Maestro records the reply before acting.

No response is never approval. The affected item remains blocked while other
eligible work continues. Informational progress is grouped into digests; the
Owner is not interrupted for routine review notes.

## Non-authorization

This decision does not configure Slack, contact an external service, grant
automatic merge/release/production authority, waive independent review, permit
unbounded Architecture-issued packets, change Alpha synthetic confinement, or
authorize any implementation by itself.
