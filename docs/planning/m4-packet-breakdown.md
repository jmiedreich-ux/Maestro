# M4 Packet Breakdown — Revised After Independent Fidelity Review

**Status:** Architect-authored, revised 2026-09-08 after a real
independent fidelity review found two structural gaps that would have
hard-failed on first real use, one factual error, and several
undersold/underspecified packets. All findings below are fixed;
superseded content from the pre-review draft is not preserved here (see
git history for that version if needed). Decomposes
[m4-development-manager-roadmap.md](m4-development-manager-roadmap.md)
into the smallest real slices each concern supports, per this project's
own standing slice-sizing rule (default to the smallest possible scope,
split aggressively).

Each packet below states: what it builds, the real code/table it
touches, its real dependency, and any open question that blocks it.
None of these are materialized packets yet — this is the plan a real
`materialize_packet` call would be built from, one packet at a time, as
M2/M3's own packets were.

**For quick reference in conversation, use `M4.01`–`M4.16`** (not the
real eventual `MB-SLICE-M4-...` packet ID, which each packet gets when
actually dispatched):

| # | Packet | Concern |
|---|---|---|
| M4.01 | R1 — dispatch-orchestration loop, heartbeat wiring | Recovery |
| M4.02 | R2 — staleness detection | Recovery |
| M4.03 | R3 — auto-timeout | Recovery |
| M4.04 | R4 — auto-redispatch | Recovery |
| M4.05 | V1 — coverage reconstruction | Review |
| M4.06 | V2 — Integration/ValidateOnly review recording | Review |
| M4.07 | V3 — independent-review dispatch | Review |
| M4.08 | V4 — correction-review dispatch | Review |
| M4.09 | I0 — Owner-acceptance command wiring | Integration |
| M4.10 | I1 — merge executor, happy path only | Integration |
| M4.11 | I2 — observation wiring | Integration |
| M4.12 | N1 — delivery loop, LocalDurable only | Notification |
| M4.13 | N2 — retry/backoff wiring | Notification |
| M4.14 | N3 — real trigger wiring | Notification |
| M4.15 | N4 — Slack channel delivery (blocked) | Notification |
| M4.16 | A0 — ruling-loop 90/10 classification criteria | Ruling loop |

## Real recovery — build first, no dependency on the other four

- **M4.01 (R1) — Real dispatch-orchestration loop, with heartbeat wiring.**
  **Corrected scope** (the fidelity review found no orchestration module
  exists anywhere that owns both an `ExecutorAdapter` and calls into
  `operational_state` — `LocalQwenExecutorAdapter` is a bare subprocess
  wrapper with no knowledge of `attempt_id`/`lease_id`/version state).
  This packet builds that real loop: it owns the real attempt/lease
  version state, drives the executor, and calls the already-real,
  already-tested `heartbeat_attempt_execution` on a real interval while a
  worker runs. Touches: new orchestration module, `executor.py`. No
  schema change.
- **M4.02 (R2) — Staleness detection.** A real read-only check: query `attempts`/
  `leases` for a `Running` attempt whose heartbeat is older than a real
  threshold, or whose lease has expired. Touches: new small module,
  read-only against existing tables. **Blocked on an open question:**
  the real threshold value (see roadmap's "Open, not yet decided"). Must
  share R1/R3's own optimistic-version discipline (`expected_attempt_
  version`/`expected_lease_version`) so a late-finishing real attempt and
  a timeout detection can never both win — verified safe by construction
  in the existing `StaleState` rejection logic, but R2 must read the same
  version fields R1/R3 use, not a stale snapshot.
- **M4.03 (R3) — Auto-timeout.** When R2 detects staleness, call the already-real
  `finish_attempt_execution(outcome="TimedOut")`. Small — this command
  already exists and is already tested; R3 is only "call it for real
  instead of a human doing it." Depends on R2.
- **M4.04 (R4) — Auto-redispatch after a recovery-driven NeedsReplan.**
  **Corrected scope** (the fidelity review found `record_and_close_
  needs_replan` only cancels the old packet — it does not create a
  replacement; `materialize_packet` requires a full new packet
  definition, and `packets`' own `UNIQUE(run_id,work_item_id,
  packet_revision)` constraint plus `attempts`' 2-attempt cap mean a real
  redispatch is structurally a new `packet_id`/`packet_revision`, not a
  reuse of the old one). This packet is real replanning logic: construct
  a full new packet definition (owned paths, checks, instructions,
  context policy) from the cancelled packet's own real facts, then call
  `record_and_close_needs_replan` + `materialize_packet` — triggered
  automatically by R3's own outcome instead of a human deciding to, per
  this session's own proven manual precedent (CG-M4-19, CG-M4-20).
  Depends on R3.

## Real review — no dependency on recovery; blocks Integration

- **M4.05 (V1) — Coverage reconstruction.** **Corrected reuse target** (the
  fidelity review found `check_runner.py` does not produce the shape
  `_validate_review_coverage` actually requires; the real match is
  `review_readiness.py`'s already-built, already-CLI-wired
  `evaluate_review_readiness`, whose result schema lines up field-for-
  field with what coverage validation checks). V1's real, now-smaller job
  is wrapping that existing result as
  `{"kind": "review-readiness-coverage", "result": ...}` — no code
  anywhere does this wrapping today. Touches: new small module, reuses
  `review_readiness.py`. No schema change.
- **M4.06 (V2) — Integration/`ValidateOnly` review recording.** **New packet,
  added by the fidelity review** — `_REVIEW_ROUTES` hard-requires exactly
  one prior review with `review_kind="Integration"`,
  `result="ValidateOnly"`, `reviewer_role="IntegrationAgent"` on the same
  head before an `IndependentImplementation` review can route at all;
  without this, the first real call to V3 would raise `InvalidRecord`.
  Calls the already-real `record_and_route_review` with V1's coverage
  output and `review_kind="Integration"`. Depends on V1.
- **M4.07 (V3) — Independent-review dispatch.** (Renumbered from the pre-review
  draft's V2.) Wraps V1's output and calls the already-real
  `record_and_route_review` with `review_kind="IndependentImplementation"`.
  Depends on V1 and V2 (V2's own prior review must already exist on the
  same head).
- **M4.08 (V4) — Correction-review dispatch.** (Renumbered from V3.) Same as V3
  for the correction path (`record_and_route_correction_review`), reusing
  V1. Depends on V1 and V2; can build in parallel with V3.

## Real Integration — depends on real review (V3/V4) and real Owner acceptance (I0)

- **M4.09 (I0) — Owner-acceptance command wiring.** **New packet, added by the
  fidelity review** — `record_and_observe_merge` only accepts a packet
  already in `AwaitingOwner` state, reached via `record_and_accept_
  packet` transitioning `MergeReady → AwaitingOwner`; a full repo grep
  found **zero real callers of `record_and_accept_packet` anywhere**, not
  even a CLI command. I1/I2 cannot run against a real packet without this
  existing first. Scope: expose the already-real, already-tested command
  through a real, callable interface (a CLI command, matching `cli.py`'s
  existing pattern), so a human — or, per the ruling-loop's own real
  authority model once A0 lands, a bounded Architect-tier ruling — can
  actually invoke it. **Open question, does not block I0 itself:** whether
  Owner acceptance ever becomes something the ruling loop can grant
  itself under the 90% tier, or stays permanently human — I0 only makes
  the command reachable, it does not decide who calls it.
- **M4.10 (I1) — Merge executor, happy path only.** **Corrected/descoped scope**
  (the fidelity review found the pre-review draft never addressed merge-
  authority/delegation requirements or conflict/gating handling — an
  automated merge executor is definitionally a `DelegatedIdentity` per
  `merge_observations.performed_by_authority`'s own constraint, which
  requires a non-null `delegation_reference`). I1's real scope: perform
  the actual merge (`gh pr merge` or equivalent) for a packet already in
  `AwaitingOwner` and successfully accepted (depends on I0), recording
  Maestro's own service account as a real `DelegatedIdentity` with a real
  delegation reference. **Explicitly out of scope, not silently assumed:**
  merge conflicts, branch-protection/required-checks gating, and CI-check
  state — I1 only handles the case where the merge succeeds cleanly;
  those cases are real, disclosed follow-up scope, not yet packetized.
  Touches: new module only; no existing command performs a merge today.
- **M4.11 (I2) — Observation wiring.** Calls the already-real `record_and_
  observe_merge` immediately after I1 succeeds, instead of a human
  running it by hand (as done for CG-M4-19, this doc's own commits, and
  every merge this session). Depends on I1.

## Real notification — independent; most useful once recovery exists

- **M4.12 (N1) — Delivery loop, `LocalDurable` channel only.** Reads `Pending`
  rows from `notifications` and delivers them (`LocalDurable` has no
  real external dependency — this is the smallest real slice that proves
  the loop). No schema change.
- **M4.13 (N2) — Retry/backoff wiring.** Uses the already-real `next_attempt_at`/
  `attempt_count` fields the schema already carries for this. Depends on
  N1.
- **M4.14 (N3) — Real trigger wiring.** Decides which real events actually create
  a notification (e.g., R3's recovery firing, a real `NeedsReplan`, a
  real `MergeReady`) and calls `record_notification` from those real
  call sites. **Corrected scope** (the fidelity review found the
  `notifications` table has no natural-key uniqueness — unlike `reviews`'
  own `UNIQUE(...)` constraint — so `record_notification`'s idempotency-
  key/replay protection only guards against the exact same call
  repeating, not a crashed/restarted trigger re-firing with a fresh key).
  N3 must derive each real idempotency key deterministically from the
  triggering source (e.g. the source event's own id, or the attempt_id +
  outcome pair), never generate one fresh per call, or a restarted
  trigger will silently double-notify. Depends on N1; benefits from
  R3/I2 existing first (nothing to notify about yet otherwise).
- **M4.15 (N4) — `Slack` channel delivery.** **Blocked**: no real Slack app/
  webhook has been registered for Maestro's own use (see roadmap's
  "Open, not yet decided"). Not packetized until that credential exists.

## Autonomous Architect ruling loop — one prerequisite packet only

- **M4.16 (A0) — Define the real 90/10 classification criteria.** A real
  decision doc (not code): the concrete test a ruling loop would use to
  sort "already Owner-approved, slot it in" from "genuinely new, escalate
  to the Owner" — classified against the real instances already on
  record (M5's own adoption, the CG-M4-19 `acceptance_authority` fix, the
  M4-vs-M5 milestone-home rejection). **No implementation packet for the
  ruling loop itself is proposed here** — per the roadmap's own explicit
  note, building execution before this criteria is real would mean
  guessing at what it's allowed to decide.

## What this breakdown deliberately does not include

- No packet for the ruling loop's own real implementation (blocked on
  A0; premature).
- No packet for `Slack` delivery (blocked on real credentials; N4 stays
  a placeholder until they exist).
- No packet assumes a real staleness threshold value exists yet — R2 is
  scoped to include picking one as part of its own work, not a silent
  guess.
- No packet for merge conflicts, branch-protection gating, or CI-check
  state in I1 — explicitly descoped as real, disclosed follow-up work,
  not silently assumed away.
- No packet decides who is authorized to call I0's own Owner-acceptance
  command (human vs. a future ruling-loop grant) — I0 only makes the
  real command reachable.

## Independent fidelity review — verified-correct claims

For traceability: the review also independently verified several claims
as factually correct against the real code, not just found problems —
R3's `TimedOut` outcome mapping, N1/N2's `notifications` schema fields
and channel enum, R2/R3's version-discipline safety by construction, and
A0's own scoping as a decision doc rather than code.
