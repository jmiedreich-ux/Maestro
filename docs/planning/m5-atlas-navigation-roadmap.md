# M5 — Atlas Navigation and Coordination Visibility

**Status:** Architect-authored draft, scoped in a 2026-09-06 planning
session with the Owner; not yet decomposed into packets.
**Scope:** Per [M0-D16](decisions/m0-d16-real-m5-atlas-navigation-and-visibility.md),
covers six real gaps found while reviewing a redesign of Atlas's mobile
Now screen — none of which any prior milestone (M1–M4) or the M2 Atlas
roadmap's own Wave A–G plans anywhere.

## Why this exists

M3 wired Atlas's Chat/PacketThread to one real, hardcoded packet
(`REAL_ACTIVE_PACKET_ID`) — a disclosed stopgap, not a real "which packet
am I looking at" mechanism. Everything downstream of that stopgap —
Now's status, Plan's packet list, Activity's History and Agents segments —
is either hardcoded to that one packet or still fixture data. M5 replaces
the stopgap with the real thing.

## The six items

1. **Milestone→packet hierarchy for Plan.** Plan becomes a real, full
   browsable list: milestones, each expanding to its own real packets
   (state, id) — not the current flat 8-fixture-packet list. Reads
   `/snapshot/packets` (already real) grouped by a real milestone field;
   Foundry's own packets currently carry a milestone string
   (`milestone_ref`, e.g. `"M4"`) already present in `work_items` — no new
   packet-side schema needed, only a new read path.
2. **Single-packet navigation for Now and Events (renamed from Chat).**
   Both default to whichever packet is real, current, and active; both
   gain real prev/next-style navigation across packets and milestones —
   not a full list (that's Plan's job). Needs a real "current selection"
   concept shared across the app, replacing `REAL_ACTIVE_PACKET_ID`.
3. **Surface real worker check-ins on Now.** `record_worker_progress` is a
   real, implemented command (`worker_progress_observations` table) with
   zero frontend wiring and no read route. Now shows only the single most
   recent check-in for the active packet's current attempt — not a
   history/timeline of every one.
4. **Project-wide History under Activity.** The real event log, filtered
   to milestones that matter across every packet (merges, acceptances,
   corrections, needs-replan) — not the granular per-transition detail
   Events shows for one packet.
5. **Project-wide Agents roster under Activity.** One real card per agent
   that has ever worked in this project, each showing real current state
   and a link into that agent's own check-in — the same card style
   already designed for Now's per-packet sub-agent list, generalized
   beyond one packet. `AgentsRoster` today is 100% fixture; this replaces
   it with real data.
6. **Backend: milestone-aware read routes.** `read_api.py` has no
   milestone concept in any route today. Needs at minimum: a real
   `/snapshot/worker_progress` route (for item 3, filterable to one
   attempt's most recent record), and either a new route or a query
   parameter on `/snapshot/packets` for grouping/filtering by
   `milestone_ref` (for items 1, 2, 4).

7. **Real project/packet onboarding surfaced in Atlas.** Slotted in
   2026-09-08, Architect-tier ("slot pre-approved work into the
   process" — see [M0-D17](decisions/m0-d17-real-m4-16-ruling-loop-classification-criteria.md)):
   the Owner asked for plain steps to start Maestro and found there was
   no real path at all — registering a project and creating a packet
   existed only as Python call sequences, never a command. M4.17 (D0,
   see `m4-packet-breakdown.md`) built the real CLI for this
   (`maestro register-project`, `maestro materialize-packet`), but it is
   a terminal-only path today. This item is Atlas's own front end for
   it: a real "register a project" / "create a packet" flow reachable
   from the app, not a JSON file and a CLI invocation. **Still real,
   disclosed, unclosed after M4.17**: claiming a materialized packet
   (`Dispatchable -> Leased`, real lease/lock/attempt allocation) has no
   command anywhere yet — a real resource-allocation decision (M3's own
   territory). Item 7 cannot offer a real, complete "start to finish in
   Atlas" flow until that exists either.

## Open, not yet decided

- Exact shape of the "current active packet" selection state: is it
  server-recorded (a real concept Maestro itself tracks) or purely
  client-side (Atlas's own local selection, defaulting to whichever real
  packet is furthest along)? Item 2 cannot be packetized until this is
  decided.
- Whether History/Agents (items 4–5) need their own new read routes or
  can reuse `/snapshot/events` and `/snapshot/packets` with wider,
  unfiltered queries than Events/Now use today.
- Accent color: the Owner does not want purple as Atlas's primary accent
  going forward (`colors.ts`'s current `accent*` family is entirely
  purple-based); a "deep blue" direction was chosen in the same planning
  session, but a real token change has not been scoped or packetized.

## Wave ordering and dependency

Item 6 (backend routes) blocks items 1, 2, 3, and 4 — none of the real
frontend work in those items can start against real data until the read
routes it needs exist. Item 5 depends only on item 6's `/snapshot/events`
or `/snapshot/packets` widening, not on items 1–4. Item 2's "current
active packet" selection is a real, shared mechanism items 1 and 2 both
need — build it once, not per-tab.
