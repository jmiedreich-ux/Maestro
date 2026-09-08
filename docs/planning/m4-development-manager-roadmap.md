# M4 — Persistent Development Manager Loop Roadmap

**Status:** Architect-authored draft, scoped in a 2026-09-08 planning
session with the Owner; not yet decomposed into packets.
**Scope:** Decomposes `maestro-master-plan.md`'s M4 line ("completes the
persistent Development Manager loop: real Integration, review,
notification, and recovery"), per
[M0-D15](decisions/m0-d15-real-m1-m4-implementation-path.md). Whether the
autonomous Architect ruling loop is real M4 scope is still open — see
"Open, not yet decided" below; this roadmap does not assume it.

## Why this exists

M1 already built real, tested durable state and routing logic for every
one of these four concerns — `record_and_observe_merge`,
`record_and_route_review`/`record_and_route_correction_review`,
`record_notification`, and the real state-machine outcome mapping that
`TimedOut`/`Failed` execution outcomes route through
(`finish_attempt_execution`). This session's own real M3 proving work
(dispatching, watching, and recovering Foundry packets by hand) surfaced
the same finding for all four: **the storage and routing exist; nothing
actually performs the action or detects the condition that should trigger
it.** Every one of these has been a human (this session, me) standing in
for automation that doesn't exist yet. M4 is that automation.

## What each concern concretely means, checked against real code today

- **Real Integration** — automatically merging/assembling an accepted
  packet's own real head into its real target branch, then recording that
  with `record_and_observe_merge`. Checked: no code anywhere calls `gh pr
  merge`, `git merge`, or equivalent — every real merge this session (CG-
  M4-19, this doc's own commits) was a human running the command by hand.
  `record_and_observe_merge` only records that a merge already happened;
  it never performs one. Fully greenfield on the execution side.
- **Real review** — an actual process that reconstructs a packet's real
  diff, checks it against `owned_paths_json`/`checks_json`, and calls
  `record_and_route_review` with real `coverage_json` — not a human
  running `git diff`/test commands by hand and typing the result in, which
  is what every real review this session actually was (CG-M4-19's
  redispatch coverage, this session's own dispatch scripts). Checked: no
  reviewer-agent or coverage-generation code exists anywhere in
  `services/maestro`; `record_and_route_review`'s own routing/validation
  logic is real and already tested (M1), only the thing that calls it for
  real is missing.
- **Real notification** — actually delivering a notification (the
  `Slack` channel `record_notification`'s own schema already names) to
  wherever it needs to go. Checked: `record_notification` durably stores
  a `Pending` row and nothing else — no webhook call, no delivery loop,
  no retry of the `next_attempt_at`/`attempt_count` fields the schema
  already carries for exactly this purpose. Fully greenfield.
- **Real recovery** — detecting that a claimed attempt has gone silent
  (no real heartbeat, an expired lease) and calling
  `finish_attempt_execution` with a real `TimedOut`/`Failed` outcome,
  which correctly routes the packet to `NeedsReplan` (real, tested M1
  logic) — then, per this session's own real CG-M4-19/CG-M4-20 precedent,
  redispatching through `record_and_close_needs_replan` +
  `materialize_packet`. Checked this session directly: `finish_attempt_
  execution` already accepts and correctly handles `TimedOut`; nothing
  calls it. This is the exact gap found live — Qwen went silent twice,
  and only a human noticed and acted.

## Open, not yet decided

- **The autonomous Architect ruling loop** — `m2-atlas-roadmap.md`'s own
  decision-card entry attributes this to M4 by name, but the surviving
  master-plan remap text `M0-D15` reconstructs from does not state it.
  Needs a real Owner decision before it's packetized as M4 scope: is an
  agent allowed to make the kind of ruling this session's own Project-
  Architect decisions (M0-D16, the CG-M4-19 acceptance-authority fix) have
  been human judgment calls, or does that stay a human role even once M4
  ships the other four?
- **Heartbeat cadence and staleness threshold** for real recovery — no
  real value chosen yet for how long a silent attempt is tolerated before
  recovery acts. `heartbeat_attempt_execution` already exists and is
  real/tested; nothing calls it from a real executor today (the local
  Qwen dispatches this session never called it), so recovery has no real
  heartbeat signal to key off yet even once built.
- **Real Slack (or other) delivery credentials/setup** — `record_
  notification`'s schema already supports a `Slack` channel; no real
  Slack app/webhook has been registered for Maestro's own use, unlike
  Foundry's real GitHub App credentials from M3.

## Wave ordering and dependency

Real recovery has no hard dependency on the other three and is the one
this session found a live, concrete need for — reasonable to build first.
Real review and real Integration are naturally sequential (nothing to
merge until something reviews it for real). Real notification can be
built independently of the other three but is most useful once recovery
exists (a stalled/recovered attempt is exactly the kind of event worth
notifying about).
