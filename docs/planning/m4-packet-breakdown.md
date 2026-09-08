# M4 Packet Breakdown — Draft, Pending Independent Fidelity Review

**Status:** Architect-authored draft, 2026-09-08. Not yet reviewed,
not yet approved for dispatch. Decomposes
[m4-development-manager-roadmap.md](m4-development-manager-roadmap.md)
into the smallest real slices each concern supports, per this project's
own standing slice-sizing rule (default to the smallest possible scope,
split aggressively).

Each packet below states: what it builds, the real code/table it
touches, its real dependency, and any open question that blocks it.
None of these are materialized packets yet — this is the plan a
real `materialize_packet` call would be built from, one packet at a
time, as M2/M3's own packets were.

## Real recovery — build first, no dependency on the other four

- **R1 — Heartbeat wiring.** The real local-executor dispatch path
  (`LocalQwenExecutorAdapter` / the dispatch scripts this session wrote
  by hand) calls the already-real, already-tested
  `heartbeat_attempt_execution` on a real interval while a worker runs.
  Touches: `executor.py` only. No schema change.
- **R2 — Staleness detection.** A real read-only check: query `attempts`/
  `leases` for a `Running` attempt whose heartbeat is older than a real
  threshold, or whose lease has expired. Touches: new small module,
  read-only against existing tables. **Blocked on an open question:**
  the real threshold value (see roadmap's "Open, not yet decided").
- **R3 — Auto-timeout.** When R2 detects staleness, call the already-real
  `finish_attempt_execution(outcome="TimedOut")`. Small — this command
  already exists and is already tested; R3 is only "call it for real
  instead of a human doing it." Depends on R2.
- **R4 — Auto-redispatch after a recovery-driven NeedsReplan.** Reuses
  this session's own proven, real pattern
  (`record_and_close_needs_replan` + `materialize_packet`) but triggered
  automatically by R3's own outcome instead of a human deciding to. Depends
  on R3.

## Real review — no dependency on recovery; blocks Integration

- **V1 — Coverage reconstruction.** A real function that reconstructs a
  packet's base→head diff and runs its own declared `checks_json`
  commands, producing real `coverage_json` — the exact manual work done
  by hand for CG-M4-19 this session, automated. Touches: new module,
  reuses `check_runner.py` (already real). No schema change.
- **V2 — Independent-review dispatch.** Wraps V1's output and calls the
  already-real `record_and_route_review` with `review_kind=
  "IndependentImplementation"`. Depends on V1.
- **V3 — Correction-review dispatch.** Same as V2 for the correction path
  (`record_and_route_correction_review`), reusing V1. Depends on V1; can
  build in parallel with V2.

## Real Integration — depends on real review existing (V2/V3)

- **I1 — Merge executor.** A real function that performs the actual merge
  (`gh pr merge` or equivalent) for a packet whose real state allows it.
  Touches: new module only; no existing command performs a merge today.
- **I2 — Observation wiring.** Calls the already-real
  `record_and_observe_merge` immediately after I1 succeeds, instead of a
  human running it by hand (as done for CG-M4-19, this doc's own commits,
  and every merge this session). Depends on I1.

## Real notification — independent; most useful once recovery exists

- **N1 — Delivery loop, `LocalDurable` channel only.** Reads `Pending`
  rows from `notifications` and delivers them (`LocalDurable` has no
  real external dependency — this is the smallest real slice that proves
  the loop). No schema change.
- **N2 — Retry/backoff wiring.** Uses the already-real
  `next_attempt_at`/`attempt_count` fields the schema already carries for
  this. Depends on N1.
- **N3 — Real trigger wiring.** Decides which real events actually create
  a notification (e.g., R3's recovery firing, a real `NeedsReplan`, a
  real `MergeReady`) and calls `record_notification` from those real
  call sites. This is itself a design decision as much as code — which
  events warrant a notification is not yet chosen anywhere. Depends on
  N1; benefits from R3/I2 existing first (nothing to notify about yet
  otherwise).
- **N4 — `Slack` channel delivery.** **Blocked**: no real Slack app/
  webhook has been registered for Maestro's own use (see roadmap's
  "Open, not yet decided"). Not packetized until that credential exists.

## Autonomous Architect ruling loop — one prerequisite packet only

- **A0 — Define the real 90/10 classification criteria.** A real
  decision doc (not code): the concrete test a ruling loop would use to
  sort "already Owner-approved, slot it in" from "genuinely new, escalate
  to the Owner" — classified against the real instances already on
  record (M5's own adoption, the CG-M4-19 `acceptance_authority` fix, the
  M4-vs-M5 milestone-home rejection). **No implementation packet for the
  ruling loop itself is proposed here** — per the roadmap's own explicit
  note, building execution before this criteria is real would mean
  guessing at what it's allowed to decide, which is exactly the kind of
  sudden, undiscovered scope this review is meant to catch.

## What this breakdown deliberately does not include

- No packet for the ruling loop's own real implementation (blocked on
  A0; premature).
- No packet for `Slack` delivery (blocked on real credentials; N4 stays
  a placeholder until they exist).
- No packet assumes a real staleness threshold value exists yet — R2 is
  scoped to include picking one as part of its own work, not a silent
  guess.
