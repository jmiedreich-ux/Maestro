# M2 — Atlas Operator Interface Roadmap

**Status:** Architect-authored, in force under delegated design authority (Owner granted 90% decision authority on design/blockers/merge for M2, 2026-09-05)
**Scope:** Slots every feature in `design_handoff_atlas/README.md` (the Owner-supplied Atlas UI handoff) into the M1-M4 real-implementation path ([M0-D01](decisions/m0-d01-operational-database.md), [master plan](maestro-master-plan.md)). Supersedes no prior decision; it is the missing detail the master plan's M2 line pointed at but did not itself enumerate.

## Why this exists

The design handoff is high-fidelity and complete as a *visual* spec, but it assumes some capabilities Maestro does not have yet (an autonomous "Architect agent" that rules on ~90% of decisions) and bundles five desktop views, a four-tab mobile app, and named operator commands into one document. Per the Bootstrap Convergence Policy, every slice must be the smallest complete outcome. This roadmap is the one place that decomposition happens, so no packet has to re-derive it.

## Architecture ruling on the one real gap: the "Architect agent"

The mockups show an autonomous agent that resolves ~90% of decisions and only escalates to the Owner when a ruling would break something the Owner froze. Maestro does not have that autonomous ruling loop yet — it is the [M0-D15](decisions/m0-d15-real-m1-m4-implementation-path.md) **M4 Development Manager loop**, not M2.

Ruling: M2 does not wait for M4. Maestro's M1 core already contains real, rule-based automated routing (`record_and_route_review`'s `_REVIEW_ROUTES`, `record_and_route_correction_review`'s `_CORRECTION_REVIEW_ROUTES`, and correction dispatch) that resolves some outcomes without a human today. Atlas's decision card renders **exactly two variants keyed off real recorded data**, not a simulated agent:
- an entry resolved by Maestro's existing automated routing renders the "ruling" variant, labeled by the actual mechanism (e.g. "resolved by routing policy"), with a link to the rule that fired;
- an entry that has no automated route and is durably waiting on a human renders the "owner decision" variant.

When the real M4 autonomous Architect loop ships, it becomes a third real source feeding the same "ruling" variant — the UI contract does not change. Nothing here invents an AI Architect; it reuses M1's already-reviewed routing tables as the ruling's evidence.

## Wave ordering and dependency

Waves are ordered by hard dependency, not by visual importance. Nothing in Wave B–G can be built against real data until Wave A exists; the design handoff's own "suggested build order" is followed within each wave.

### Wave A — Local read API and event stream (backend, unblocks everything)
Local-only (loopback-bound, no auth per Owner decision 2026-09-05: single local owner, no access-control change), read-only, additive on top of the existing Maestro SQLite service. This is the "local read API" and "event stream" M0-D01 already named as approved architecture — M2 is where it is actually built.

1. **A1 — Read-API service scaffold.** Process entrypoint, config, `/health`. No business data. Smallest possible: proves the process starts, binds loopback-only, and stops cleanly.
2. **A2 — Packets snapshot endpoint.** `GET /snapshot/packets`: current `packets` table projection, read-only, paginated.
3. **A3 — Attempts snapshot endpoint.** `GET /snapshot/attempts`.
4. **A4 — Reviews snapshot endpoint.** `GET /snapshot/reviews`, including `findings_json`.
5. **A5 — Events snapshot endpoint.** `GET /snapshot/events`, paginated, newest-first, the source for History.
6. **A6 — Event stream (SSE).** `GET /stream/events`: live-tails new `events` rows as they're recorded. No filtering/fan-out logic beyond a single subscriber loop.
7. **A7 — Reconnect/resync contract.** Client-supplied last-seen event id; server replies with the exact gap-fill or a "resync from snapshot" signal. Closes the disconnect/reconnect behavior the design's `disconnected` state depends on.

### Wave B — Atlas app shells (frontend scaffolding)
8. **B1 — `apps/atlas/` scaffold.** React + TypeScript + Vite (matches the earlier Owner-selected Atlas stack), build/lint/test wiring, no screens.
9. **B2 — Design tokens module.** Fonts (Bricolage Grotesque / Public Sans / IBM Plex Mono), the full color table, radii, spacing, from the README verbatim. No consumers yet.
10. **B3 — Desktop shell.** Top bar + two-column layout + dark nav with the 5 static nav rows (no data, no routing logic beyond selection state).
11. **B4 — Mobile shell.** Four-tab bottom bar + phone body, static.

### Wave C — Packet thread (desktop) / Chat (mobile) — the default view
12. **C1 — Packet thread, static fixtures.** Thread rendering (rows, avatars, grouping rule) against hardcoded fixtures, per the README's own step 2. No decision card yet.
13. **C2 — Packet thread wired to real data.** Same view, reads `A2`/`A5`
    snapshot + `A6` stream instead of fixtures. **Blocked, discovered
    2026-09-05 while sequencing Wave C execution — not merely a missing
    dependency, a real architecture gap:** `A6` (the event stream) and
    `A7` (the reconnect contract) were never built as their own slices —
    Wave A execution stopped at `A5` (the events *snapshot*, a bounded
    historical query) — so C2 cannot be *fully* built as scoped even
    once that gap is closed. More fundamentally, the actual backend data
    model (`packets`/`attempts`/`reviews`/`events` — all structured
    records) has no concept of the mockup's narrative chat messages
    ("Terra, base is 9d3e1a2. You can write one Runtime file...").
    `events` carries a machine `event_type`, `before_json`/`after_json`,
    and a `reason` payload — not authored prose. Producing something
    resembling C1's fixture thread from real data requires either a new
    backend concept (a real "thread message" record, itself a product
    decision about what a Maestro agent/coordinator actually writes and
    where) or a synthesis layer turning structured events into
    human-readable narrative (a nontrivial design choice with real
    fidelity/scope tradeoffs). Deciding which is a reserved product/
    architecture choice, not a routine implementation detail delegated
    authority should decide unilaterally — this is recorded here as an
    open question for the Owner, not silently resolved. **Not a blocker
    for the rest of Wave C**: C3-C7 all extend `PacketThread`'s existing,
    already-reviewed fixture data (rendering a decision card, a fidelity
    record, and a crash card on top of the same `A.2` messages) and need
    no real backend wiring at all — they proceed in C2's absence.
14. **C3 — Decision card, ruling variant.** Read-only rendering, driven by the real routing-table evidence per the ruling above.
15. **C4 — Decision card, owner-decision variant, read-only.** Options rendered but inert (no command wiring yet — that is Wave D).
16. **C5 — Decision Fidelity record (`DF-2`) rendering.**
17. **C6 — Crash card rendering (read-only).**
18. **C7 — Header summary / boundary timestamps single-state-source wiring.** Enforces the README's rule: header summary, hero card, boundary timestamps, and "what happens next" all derive from one state value — done once, reused everywhere it recurs (C, F).

### Wave D — Guarded operator-action commands (the actual authority change)
Each command is its own slice: a new guarded, idempotent backend command plus the one UI control that calls it. Matches M0-D01's amendment: a command is available through Atlas only once its own guarded command exists and passes review.
19. **D1 — Guarded command API scaffold.** POST endpoint shape, idempotency-key handling, actor/causation envelope — no real command registered yet.
20. **D2 — Command: Owner resolves a decision (`sentinel` / `amend` / `defer` options).** The smallest real operator-action command; only the owner-decision variant may call it (per the design's own rule that ruling-variant options are read-only).
21. **D3 — Wire owner-decision card buttons to D2.**
22. ~~**D4 — Command: "Decide this myself" (Architect variant → Owner takes it over).**~~
    **Rescheduled to M4.** Depends on the real M4 autonomous Architect
    loop ([M0-D15](decisions/m0-d15-real-m1-m4-implementation-path.md)),
    which does not exist in M2. This roadmap's own architecture ruling
    above renders exactly two real decision-card variants (ruling,
    owner-decision) — not a third "Architect variant." The already-merged
    C3/C4 packets explicitly exclude any Architect-variant option or
    footer button for this exact reason (`m2-c4-decision-card-owner.md`
    excludes "Send back to the Architect agent" as depending on "the
    nonexistent M4 Architect agent," with a test asserting it never
    renders). D4 as originally worded presupposes UI that is real
    content for M4, not M2. Owner confirmed 2026-09-05: a feature
    visible in the mockup that depends on a later milestone's machinery
    is rescheduled to that milestone when reached — never forced into
    the current one, never silently dropped. The mockup was built to
    Maestro's full end-state vision, not just M2's.
23. ~~**D5 — Wire the Architect-variant footer button to D4.**~~
    **Rescheduled to M4**, same dependency as D4 — there is no
    Architect-variant footer button to wire in M2.
24. **D6 — Command: crash recovery choice (resume / re-dispatch / hold-and-inspect).**
25. **D7 — Wire crash card recovery buttons to D6; render the post-choice confirmation state.**

### Wave E — Remaining desktop reporting views (read-only; can run in parallel with D once C7 lands)
26. **E1 — Performance: header stats + weekly-window strip.**
27. **E2 — Performance: per-action records list + expand/collapse.**
28. **E3 — Performance: breakdown split card (by role / by kind, cost/tokens/time segmented control).**
29. **E4 — Agents: roster cards.**
30. **E5 — Agents: contention/lock card.**
31. **E6 — History: timeline.**
32. **E7 — Gate: criteria list + gate-open state (disabled button, approver/what-opens panel).**

### Wave F — Mobile remaining tabs (reuse Wave C/E logic; no new backend)
33. **F1 — Now tab:** hero card, state-table-driven headline/bar/timestamps, "what happens next" panel.
34. **F2 — Chat tab:** reuses C1–C6 in the mobile bubble layout.
35. **F3 — Activity tab:** History/Agents/Cost segmented, reusing E6/E4/E1–E3 data.
36. **F4 — Plan tab:** packet list + gate bottom sheet (reuses E7 data).

### Wave G — Failure and empty states (desktop + mobile; last, per the README's own ordering)
37. **G1 — `disconnected` state:** connection strip + live-indicator flip, driven by A7's reconnect contract.
38. **G2 — `crashed` state:** already covered by C6/D6/D7; this slice is the top-level system banner only.
39. **G3 — `empty` state:** desktop + mobile empty-state screens (no packets yet).

## What is explicitly out of scope for M2

- The autonomous Architect-agent ruling loop itself (M4).
- A real packet compiler / real agent executor (M3) — Wave C/D read and act on whatever M1 data exists today, fixture-project or real.
- Any authentication/access-control layer (Owner decision 2026-09-05: no change while single local owner).
- Any network exposure beyond loopback.

## Execution order

Waves A and B run first (nothing else has real data or a shell to render into). C and D follow, in that order (D depends on C's decision-card rendering). E can start once C7 lands and does not block D. F depends on C/D/E's data logic existing. G is last, per the design handoff's own instruction.

Each numbered item above becomes its own canonical packet contract (`docs/planning/packets/m2-*.md`), reviewed and executed one at a time under the Bootstrap Convergence Policy's bounded review sequence.
