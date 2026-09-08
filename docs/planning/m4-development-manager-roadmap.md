# M4 — Persistent Development Manager Loop Roadmap

**Status:** Architect-authored draft, scoped in a 2026-09-08 planning
session with the Owner; not yet decomposed into packets.
**Scope:** Decomposes `maestro-master-plan.md`'s M4 line ("completes the
persistent Development Manager loop: real Integration, review,
notification, and recovery"), per
[M0-D15](decisions/m0-d15-real-m1-m4-implementation-path.md), plus the
autonomous Architect ruling loop — confirmed as real M4 scope by the
Owner on 2026-09-08 (previously open; `m2-atlas-roadmap.md`'s own
decision-card entry already attributed it to M4 by name, the surviving
master-plan remap text `M0-D15` reconstructs from just didn't restate it).

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
- **Autonomous Architect ruling loop** — an agent making the kind of
  bounded, in-scope architecture ruling this session's own Project-
  Architect decisions have been human judgment calls for (M0-D16 adopting
  M5; the CG-M4-19 `acceptance_authority` fix; rejecting M4 as the wrong
  home for M5's own scope). Checked: no such agent or ruling-loop code
  exists anywhere in `services/maestro` — every real architectural
  decision this session made was a human (me) reasoning directly, not a
  bounded agent loop calling a real command. Real M1 primitives this
  would plug into already exist and are tested (`record_binding`,
  `record_graph_projection`, project-authority loading/validation); the
  ruling logic itself — what an agent is and is not allowed to decide
  unilaterally, and what still requires the real Owner — is fully
  greenfield and is the highest-uncertainty item in this roadmap.

## Open, not yet decided

- **The autonomous Architect ruling loop's own real boundary** — *that*
  it's real M4 scope is now confirmed (2026-09-08); *what* it's actually
  allowed to rule on unilaterally versus what still requires the real
  Owner is not fully specified. The Owner set the governing ratio the
  same day: **90% Maestro process, 10% Owner** — the loop should resolve
  the large majority of real architectural rulings itself, escalating
  only the real minority that genuinely needs a human. Still open: the
  concrete criteria that sort a given ruling into the 90% or the 10% —
  the four examples above (M5 adoption, an acceptance-authority fix, a
  rejected milestone-home ruling) are real instances to classify against
  once that criteria exists, not yet classified themselves.
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

Real recovery has no hard dependency on the other four and is the one
this session found a live, concrete need for — reasonable to build first.
Real review and real Integration are naturally sequential (nothing to
merge until something reviews it for real). Real notification can be
built independently of the rest but is most useful once recovery exists
(a stalled/recovered attempt is exactly the kind of event worth
notifying about). The autonomous Architect ruling loop depends on none of
the other four technically, but its own real boundary (see "Open, not
yet decided") has to be scoped before any of it is packetized — building
it before that boundary is real would mean guessing at what it's allowed
to decide.
