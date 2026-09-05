# M2 Wave E — History Timeline — Candidate 02

**Slice ID:** `MB-SLICE-M2-E6-HISTORY-TIMELINE-02`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `edfa5ed` (full: `edfa5ed`, `origin/master`)

**Successor to `MB-SLICE-M2-E6-HISTORY-TIMELINE-01`, terminally
returned.** Candidate `-01`'s sole defect was a self-contradictory
count of its own disclosed color literals, scattered across four
separate locations in its prose; its one available targeted correction
fixed three of the four locations but missed the fourth (a code-comment
docstring inside `History.tsx`'s own "exact file contents"), and
targeted verification correctly caught the remaining inconsistency.
Every other claim in `-01` — all 10 `HISTORY_ENTRIES`, the
`HISTORY_KIND_STYLE` map, `HISTORY_STATS`, the `navText` disclosure
reasoning, the CSS variable cross-check, the 9 named tests, and the
toolchain results (90/90 baseline, 99/99 post-slice) — was
independently re-derived and confirmed correct twice (once by the
initial Decision Fidelity review, once again by targeted verification
re-checking everything untouched by the correction). This candidate
reuses that content verbatim and fixes the count discipline itself:
every location in this document that states or implies the number of
disclosed color literals — including code-comment docstrings inside
"exact file contents," not only narrative prose — was grepped for
explicitly and reconciled to the one real, exhaustively-recounted
total: **5 disclosed literals across the two new source files**
(`#CFC6D6` in `historyStyle.ts`; `#EDE8F2`, `rgba(224,163,46,.16)`,
`#E4DEEE`, `#FBFAFE` in `History.tsx`).

## Scope, deliberately minimal

Roadmap item 31, *"E6 — History: timeline."* Unlike items 26, 27, and
32 (Performance's two halves, Gate's two halves), this item is not
split further: the History screen's header (eyebrow, title, 4 real
stats) and its timeline (10 real entries plus a trailing placeholder
note) are one real, cohesive dataset with no natural sub-slice
boundary, the same granularity as E1's Performance header or E7's Gate
criteria card. This slice renders the whole screen, standalone — no
wiring into `DesktopShell`/`App.tsx`.

**No fictional "Architect agent" persona appears anywhere in this
slice — the cleanest content of any Wave-E slice so far.** Every
timeline entry describes a real M1-A event, and several are the exact
same real events C1's `PACKET_A2_ENTRIES`, C4's `OwnerDecisionCard`,
and C6's `CrashCard` already established (A.2's dispatch, blocked
report, and escalation) — this slice is independently, verbatim-
transcribed from the reference file's own `HISTORY` array, not derived
from those other slices' fixtures, but it is a real, checkable
consistency that the same underlying story is told the same way in
both places.

Reference file's real `HISTORY` array (verbatim, all 10 entries):

```js
const HISTORY = [
  ['13 Feb', 'dispatch', 'A.0', 'Source homes confirmed', 'Coordinator', 'Routed to local Qwen, reviewed PASS by Terra. Output was an issue comment — no code, no locks.', ''],
  ['12:40', 'dispatch', 'A.1', 'Sol dispatched on the Core contract', 'Coordinator', 'Base c246080f, one Core file and one Core test, review to Claude Opus.', ''],
  ['13:14', 'handoff', 'A.1', 'Branch m1-a-1 handed off', 'Sol', 'Two files changed, build passes, focused tests 4 of 4.', ''],
  ['13:28', 'review', 'A.1', 'Changes requested', 'Claude Opus', 'An empty theme version was still accepted by the identity contract. One finding, one file.', ''],
  ['13:30', 'correction', 'A.1', 'The packet’s one correction spent', 'Coordinator', 'Fix limited to the named finding, same reviewer. No budget left on A.1.', ''],
  ['13:48', 'accepted', 'A.1', 'A.1 accepted, contract frozen at 9d3e1a2', 'Coordinator', 'Locks released and A.2 became dispatchable.', 'A.1'],
  ['13:49', 'dispatch', 'A.2', 'Terra dispatched on the Runtime Package', 'Coordinator', 'Base 9d3e1a2, one Runtime file and one Runtime test, 60-minute response boundary.', ''],
  ['14:30', 'report', 'A.2', 'Status check answered', 'Terra', 'Step 3 of 5, no blocker, ETA unknown. Inside the boundary.', ''],
  ['14:52', 'blocked', 'A.2', 'Terra stopped rather than guess', 'Terra', 'Theme-free outputs still need a theme version, and the frozen contract rejects an empty one.', ''],
  ['14:56', 'escalated', 'A.2', 'Coordinator passed it up', 'Coordinator', 'Scope and corrections are the Coordinator’s to rule on; a frozen contract is not.', 'A.2'],
];
```

Reference file's real `HIST_STYLE` map and per-entry derivation
(verbatim):

```js
const HIST_STYLE = {
  dispatch: ['#F2EEF8', '#4A4155', '#B9AFC4', 0],
  handoff: ['#EBE4FF', '#4A28CC', '#8C6BFF', 0],
  review: ['#FBEDE7', '#A9522B', '#D08A63', 0],
  correction: ['#FBEDE7', '#A9522B', '#D08A63', 0],
  accepted: ['#E4F6EE', '#1F6B4E', '#2E9B72', 0],
  report: ['#F2EEF8', '#6C6376', '#CFC6D6', 0],
  blocked: ['#FDF1DC', '#8A5A08', '#E0A32E', 1],
  escalated: ['#FDF1DC', '#8A5A08', '#E0A32E', 1],
};
// per entry: const st = HIST_STYLE[kind];
// tagBg: st[0], tagColor: st[1]
// dotBg: st[3] ? st[2] : '#fff', dotBorder: '2px solid ' + st[2]
// dotSize: st[3] ? '11px' : '10px'
// dotRing: st[3] ? '0 0 0 7px rgba(224,163,46,.16)' : '0 0 0 0 transparent'
// railColor: '#EDE8F2'
// hasRef: !!ref, ref: 'Open ' + ref + ' thread'
```

Reference file's real `histStats` (verbatim — `'Decisions recorded'`'s
value is the mockup's own real initial-state default, `s.decided ===
null`, the same "real default, not a fabricated branch" reasoning C7's
`derivePacketHeaderState` already used):

```js
histStats: [
  { label: 'Packets accepted', value: '2 of 8' },
  { label: 'Corrections spent', value: '1' },
  { label: 'Decisions recorded', value: s.decided ? '2' : '1' },
  { label: 'Elapsed', value: '3h 07m' },
],
```

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from):

```html
<div style="flex:none;padding:16px 34px 14px;background:#fff;border-bottom:1px solid #EEEAF2">
  <div style="display:flex;align-items:center;gap:9px;font:500 11px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:#A79BB4"><span>m1-a</span><span style="width:3px;height:3px;border-radius:50%;background:#CFC6D6"></span><span>history</span></div>
  <h1 style="margin:7px 0 0;font-family:'Bricolage Grotesque',sans-serif;font-size:25px;font-weight:600;letter-spacing:-.025em;line-height:1.15">Everything that happened, in order</h1>
  <div style="display:flex;flex-wrap:wrap;gap:0 26px;margin-top:9px;font-size:13.5px;color:#6C6376">
    <sc-for list="{{ histStats }}" as="s" hint-placeholder-count="4">
    <span style="display:flex;align-items:baseline;gap:7px">{{ s.label }}<b style="font-family:'IBM Plex Mono',monospace;color:#221C29">{{ s.value }}</b></span>
    </sc-for>
  </div>
</div>
<div style="flex:1 1 0;min-height:0;overflow:auto;padding:4px 0 26px">
  <sc-for list="{{ history }}" as="h" hint-placeholder-count="9">
  <div style="display:grid;grid-template-columns:58px 22px minmax(0,1fr);gap:0 14px;padding:0 34px">
    <div style="padding-top:14px;font:500 12px 'IBM Plex Mono',monospace;color:#A79BB4;text-align:right">{{ h.time }}</div>
    <div style="position:relative;display:flex;justify-content:center">
      <span style="position:absolute;top:0;bottom:0;width:1.5px;background:{{ h.railColor }}"></span>
      <span style="position:relative;margin-top:15px;width:{{ h.dotSize }};height:{{ h.dotSize }};box-sizing:border-box;border-radius:50%;background:{{ h.dotBg }};border:{{ h.dotBorder }};box-shadow:0 0 0 4px #FCFBFD,{{ h.dotRing }}"></span>
    </div>
    <div style="min-width:0;padding:12px 0 12px">
      <div style="display:flex;flex-wrap:wrap;align-items:baseline;gap:9px">
        <span style="flex:none;padding:2px 7px;border-radius:6px;background:{{ h.tagBg }};color:{{ h.tagColor }};font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.08em;text-transform:uppercase">{{ h.kind }}</span>
        <span style="font-size:15px;font-weight:600;letter-spacing:-.01em;text-wrap:pretty">{{ h.title }}</span>
        <span style="font:500 11.5px 'IBM Plex Mono',monospace;color:#A79BB4">{{ h.packet }}</span>
      </div>
      <div style="margin-top:3px;max-width:64ch;font-size:13.5px;line-height:1.55;color:#6C6376;text-wrap:pretty">{{ h.detail }}</div>
      <sc-if value="{{ h.hasRef }}" hint-placeholder-val="{{ false }}">
      <button onClick="{{ h.onOpen }}" style="margin-top:7px;height:26px;padding:0 10px;border:1px solid #E4DEEE;border-radius:7px;background:#fff;color:#5B34E8;cursor:pointer;font:600 12px 'Public Sans',sans-serif" style-hover="border-color:#C9BEDC;background:#FBFAFE">{{ h.ref }}</button>
      </sc-if>
    </div>
  </div>
  </sc-for>
  <div style="display:grid;grid-template-columns:58px 22px minmax(0,1fr);gap:0 14px;padding:0 34px">
    <span></span>
    <div style="display:flex;justify-content:center"><span style="width:1.5px;height:22px;background:linear-gradient(#E7E1EE,transparent)"></span></div>
    <div style="padding:4px 0 0;font-size:13px;color:#A79BB4">A.3 through A.7 have not been dispatched — nothing to record yet.</div>
  </div>
</div>
```

**The `detail` field concatenates `who + ' — ' + detail` (verbatim
reference logic), not two separately styled fields — this slice
renders that one concatenated string, matching the real markup
exactly.**

**The eyebrow's separator uses the same plain-text middle-dot
convention already established by C7's `PacketHeader` and E1's
`PerformanceHeader`** (`m1-a · history`), not a separate colored dot
`<span>` — consistent with precedent, not a new simplification.

**"Open … thread" buttons are rendered as real, inert `<button>`
elements with no `onClick`, matching C4's/C6's established pattern** —
there is no real navigation destination wired anywhere in this program
yet (`History` is not wired into `DesktopShell`, and even if it were,
`PacketThread` only has `A.2`'s real fixture data, not `A.1`'s).
`cursor: default`, not the reference file's `cursor: pointer`, for the
same real reason C4/C6 already established.

**Color discrepancy table — every semantic color is a real B2 token
except five, all disclosed and checked directly:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| header border `#EEEAF2` | `colors.borderDivider[0]` | exact |
| eyebrow / packet / time text `#A79BB4` | `colors.inkFaint` | exact |
| title text (implicit default) | `colors.ink` | exact |
| stats label / entry-detail text `#6C6376` | `colors.inkSecondary` | exact |
| `dispatch` tag `#F2EEF8`/`#4A4155` | `colors.neutralChip`/`colors.neutralChipText` | exact |
| `dispatch` dot `#B9AFC4` | `colors.borderDashed[2]` | exact |
| `handoff` tag `#EBE4FF`/`#4A28CC` | `colors.accentWash[0]`/`colors.accentHover` | exact |
| `handoff` dot `#8C6BFF` | `colors.accentLight` | exact |
| `review`/`correction` tag `#FBEDE7`/`#A9522B` | `colors.reviewWash`/`colors.reviewText` | exact |
| `review`/`correction` dot `#D08A63` | `colors.review` | exact |
| `accepted` tag `#E4F6EE`/`#1F6B4E` | `colors.successWash`/`colors.successText` | exact |
| `accepted` dot `#2E9B72` | `colors.success` | exact |
| `report` tag `#F2EEF8`/`#6C6376` | `colors.neutralChip`/`colors.inkSecondary` | exact |
| `report` dot `#CFC6D6` | none in `colors.ts` (equals `colors.navText`; see the exhaustive, checked exception below) | disclosed literal |
| `blocked`/`escalated` tag `#FDF1DC`/`#8A5A08` | `colors.warningChip`/`colors.warningText` | exact |
| `blocked`/`escalated` dot `#E0A32E` | `colors.warning` | exact |
| outer dot ring `#FCFBFD` | `colors.pageBgDesktop` | exact |
| timeline rail `#EDE8F2` | none in `colors.ts` (`colors.borderDivider`'s three real values are `#EEEAF2`/`#F3F0F6`/`#F0ECF5` — none of them; checked directly, not a rounding) | disclosed literal |
| urgent-dot ring `rgba(224,163,46,.16)` | none in `colors.ts` as a ring value (derived from `colors.warning`'s own RGB, `224,163,46`) | disclosed literal |
| empty-row rail-stub gradient start `#E7E1EE` | `colors.border` | exact |
| button border `#E4DEEE` | none in `colors.ts` (`colors.border` `#E7E1EE` and `colors.borderStrong`'s two values `#D6CFE4`/`#DAD2EC` are all real, different values — checked directly) | disclosed literal |
| button text `#5B34E8` | `colors.accent` | exact |
| button hover border `#C9BEDC` | `colors.focusHoverBorderNeutral` | exact |
| button hover bg `#FBFAFE` | none in `colors.ts` (the same real literal C3's `DecisionCard` and C5's `FidelityRecord` already disclosed for their own cards) | disclosed literal |

**The `#CFC6D6`/`colors.navText` exception is checked with the exact
same rigor this program's Gate-criteria slice (E7-02) established after
its own predecessor was terminally returned for under-checking this
same class of claim.** `colors.navText` has no real consumer anywhere
in `apps/atlas/src` today (checked directly, one property at a time,
against every property in that same `colors.ts` nav-color group —
`navGround`, `navTextActive`, `navTextInactive`, `navActiveBg`, and
`navHoverBg` are all real, consumed values in `DesktopShell.tsx`;
`navText` and its sibling `navTextDim` are the only two that are not).
Its scoping to the dark sidebar rests on its name and its position in
this real, mostly-consumed group, not on any actual usage of the
property itself — so it is disclosed as a literal here, exactly like
in `GateCriteriaList`, not reused as a general-purpose light-mode dot
color.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E6-HISTORY-TIMELINE-02` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:edfa5ed", "predecessor:MB-SLICE-M2-E6-HISTORY-TIMELINE-01(terminally-returned; disclosed-literal-count-self-contradiction, one location missed by its correction)"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
five files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`. The first real test run found one
genuine defect in the test file (not the component): the first test
used a bare `screen.getByText(...)` for a stat's value, but two real
stats (`Corrections spent` and `Decisions recorded`) share the
identical real value `"1"`, so the query matched multiple elements and
failed with a real `getByText` ambiguity error — the same class of
self-caught defect E2's own packet already disclosed once for a
different duplicate value. Fixed by scoping each stat's value query to
that stat's own container, found via its unique label, not a bare
query. After that fix: 99/99 tests passed (90 existing + 9 new),
typecheck and lint clean, production build succeeded.

`apps/atlas/src/history/fixtures.ts` (new — the timeline data and its
types; no rendering logic; a new top-level directory, matching
`thread/`, `decision/`, `crash/`, `performance/`, `gate/`):

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `HISTORY` array, `HIST_STYLE` map, and `histStats` — pure reporting
 * content, no persona, no fictional agent. Every entry describes real
 * M1-A events already established elsewhere in this program (A.1's
 * acceptance, A.2's dispatch/blocked/escalation — the same real
 * scenario C1's `PACKET_A2_ENTRIES`, C4's `OwnerDecisionCard`, and C6's
 * `CrashCard` already use). `histStats`'s "Decisions recorded" value
 * (`'1'`) is the reference file's own real initial-state default
 * (`s.decided` is `null` at initialization), not a fabricated number —
 * the same reasoning C7's `derivePacketHeaderState` used for its own
 * real-default values.
 */
export type HistoryKind =
  | "dispatch"
  | "handoff"
  | "review"
  | "correction"
  | "accepted"
  | "report"
  | "blocked"
  | "escalated";

export interface HistoryEntry {
  time: string;
  kind: HistoryKind;
  packet: string;
  title: string;
  who: string;
  detail: string;
  ref: string;
}

export interface HistoryStat {
  label: string;
  value: string;
}

export const HISTORY_STATS: HistoryStat[] = [
  { label: "Packets accepted", value: "2 of 8" },
  { label: "Corrections spent", value: "1" },
  { label: "Decisions recorded", value: "1" },
  { label: "Elapsed", value: "3h 07m" },
];

export const HISTORY_ENTRIES: HistoryEntry[] = [
  {
    time: "13 Feb",
    kind: "dispatch",
    packet: "A.0",
    title: "Source homes confirmed",
    who: "Coordinator",
    detail: "Routed to local Qwen, reviewed PASS by Terra. Output was an issue comment — no code, no locks.",
    ref: "",
  },
  {
    time: "12:40",
    kind: "dispatch",
    packet: "A.1",
    title: "Sol dispatched on the Core contract",
    who: "Coordinator",
    detail: "Base c246080f, one Core file and one Core test, review to Claude Opus.",
    ref: "",
  },
  {
    time: "13:14",
    kind: "handoff",
    packet: "A.1",
    title: "Branch m1-a-1 handed off",
    who: "Sol",
    detail: "Two files changed, build passes, focused tests 4 of 4.",
    ref: "",
  },
  {
    time: "13:28",
    kind: "review",
    packet: "A.1",
    title: "Changes requested",
    who: "Claude Opus",
    detail: "An empty theme version was still accepted by the identity contract. One finding, one file.",
    ref: "",
  },
  {
    time: "13:30",
    kind: "correction",
    packet: "A.1",
    title: "The packet’s one correction spent",
    who: "Coordinator",
    detail: "Fix limited to the named finding, same reviewer. No budget left on A.1.",
    ref: "",
  },
  {
    time: "13:48",
    kind: "accepted",
    packet: "A.1",
    title: "A.1 accepted, contract frozen at 9d3e1a2",
    who: "Coordinator",
    detail: "Locks released and A.2 became dispatchable.",
    ref: "A.1",
  },
  {
    time: "13:49",
    kind: "dispatch",
    packet: "A.2",
    title: "Terra dispatched on the Runtime Package",
    who: "Coordinator",
    detail: "Base 9d3e1a2, one Runtime file and one Runtime test, 60-minute response boundary.",
    ref: "",
  },
  {
    time: "14:30",
    kind: "report",
    packet: "A.2",
    title: "Status check answered",
    who: "Terra",
    detail: "Step 3 of 5, no blocker, ETA unknown. Inside the boundary.",
    ref: "",
  },
  {
    time: "14:52",
    kind: "blocked",
    packet: "A.2",
    title: "Terra stopped rather than guess",
    who: "Terra",
    detail: "Theme-free outputs still need a theme version, and the frozen contract rejects an empty one.",
    ref: "",
  },
  {
    time: "14:56",
    kind: "escalated",
    packet: "A.2",
    title: "Coordinator passed it up",
    who: "Coordinator",
    detail: "Scope and corrections are the Coordinator’s to rule on; a frozen contract is not.",
    ref: "A.2",
  },
];

/** Real, verbatim — the timeline's own trailing placeholder note. */
export const HISTORY_EMPTY_NOTE = "A.3 through A.7 have not been dispatched — nothing to record yet.";
```

`apps/atlas/src/history/historyStyle.ts` (new — the per-kind style
derivation; no rendering logic):

```ts
import { colors } from "../tokens";
import type { HistoryKind } from "./fixtures";

/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `HIST_STYLE` map: `[tagBg, tagColor, dotColor, urgent]` per kind.
 * Every value below is a real B2 token except `report`'s dot color
 * (`#CFC6D6`): that exact hex also happens to equal `colors.navText`,
 * which — per this program's own exhaustively-checked precedent from
 * the Gate-criteria slice — has no real consumer anywhere in this
 * codebase and is scoped to the dark nav sidebar by name and grouping,
 * not a general-purpose light-mode dot color. It is disclosed as a
 * literal here too, not reused from that unrelated token.
 */
export interface HistoryKindStyle {
  tagBg: string;
  tagColor: string;
  dotColor: string;
  urgent: boolean;
}

export const HISTORY_KIND_STYLE: Record<HistoryKind, HistoryKindStyle> = {
  dispatch: { tagBg: colors.neutralChip, tagColor: colors.neutralChipText, dotColor: colors.borderDashed[2], urgent: false },
  handoff: { tagBg: colors.accentWash[0], tagColor: colors.accentHover, dotColor: colors.accentLight, urgent: false },
  review: { tagBg: colors.reviewWash, tagColor: colors.reviewText, dotColor: colors.review, urgent: false },
  correction: { tagBg: colors.reviewWash, tagColor: colors.reviewText, dotColor: colors.review, urgent: false },
  accepted: { tagBg: colors.successWash, tagColor: colors.successText, dotColor: colors.success, urgent: false },
  report: { tagBg: colors.neutralChip, tagColor: colors.inkSecondary, dotColor: "#CFC6D6", urgent: false },
  blocked: { tagBg: colors.warningChip, tagColor: colors.warningText, dotColor: colors.warning, urgent: true },
  escalated: { tagBg: colors.warningChip, tagColor: colors.warningText, dotColor: colors.warning, urgent: true },
};
```

`apps/atlas/src/history/History.module.css` (new — CSS Module,
`var(--atlas-*)` only for the static parts; per-entry dynamic values —
dot size/color/box-shadow, tag background/color — are inline styles,
matching the reference file's own per-item derivation):

```css
.head {
  flex: none;
  padding: 16px 34px 14px;
  background: var(--atlas-hist-surface);
  border-bottom: 1px solid var(--atlas-hist-header-border);
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  font: 500 11px var(--atlas-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--atlas-hist-eyebrow);
}

.title {
  margin: 7px 0 0;
  font-family: var(--atlas-font-display);
  font-size: 25px;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.15;
  color: var(--atlas-hist-title);
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0 26px;
  margin-top: 9px;
  font-size: 13.5px;
  color: var(--atlas-hist-lede);
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.statValue {
  font-family: var(--atlas-font-mono);
  color: var(--atlas-hist-title);
}

.timeline {
  flex: 1 1 0;
  min-height: 0;
  overflow: auto;
  padding: 4px 0 26px;
}

.row {
  display: grid;
  grid-template-columns: 58px 22px minmax(0, 1fr);
  gap: 0 14px;
  padding: 0 34px;
}

.time {
  padding-top: 14px;
  font: 500 12px var(--atlas-font-mono);
  color: var(--atlas-hist-eyebrow);
  text-align: right;
}

.railWrap {
  position: relative;
  display: flex;
  justify-content: center;
}

.rail {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1.5px;
  background: var(--atlas-hist-rail);
}

.dot {
  position: relative;
  margin-top: 15px;
  box-sizing: border-box;
  border-radius: 50%;
}

.body {
  min-width: 0;
  padding: 12px 0;
}

.entryLine {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 9px;
}

.tag {
  flex: none;
  padding: 2px 7px;
  border-radius: 6px;
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.entryTitle {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  text-wrap: pretty;
  color: var(--atlas-hist-title);
}

.entryPacket {
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-hist-eyebrow);
}

.entryDetail {
  margin-top: 3px;
  max-width: 64ch;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-hist-lede);
  text-wrap: pretty;
}

.openButton {
  margin-top: 7px;
  height: 26px;
  padding: 0 10px;
  border: 1px solid var(--atlas-hist-button-border);
  border-radius: 7px;
  background: var(--atlas-hist-surface);
  color: var(--atlas-hist-button-text);
  cursor: default;
  font: 600 12px var(--atlas-font-body);
}

.openButton:hover {
  border-color: var(--atlas-hist-button-hover-border);
  background: var(--atlas-hist-button-hover-bg);
}

.emptyRow {
  display: grid;
  grid-template-columns: 58px 22px minmax(0, 1fr);
  gap: 0 14px;
  padding: 0 34px;
}

.emptyRail {
  display: flex;
  justify-content: center;
}

.emptyRailStub {
  width: 1.5px;
  height: 22px;
  background: linear-gradient(var(--atlas-hist-empty-rail), transparent);
}

.emptyNote {
  padding: 4px 0 0;
  font-size: 13px;
  color: var(--atlas-hist-eyebrow);
}
```

`apps/atlas/src/history/History.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "./fixtures";
import { HISTORY_KIND_STYLE } from "./historyStyle";
import styles from "./History.module.css";

/**
 * Real B2 tokens plus four disclosed literals in this file, checked
 * directly against the reference file: the timeline rail color
 * (`#EDE8F2` — a real, different value from `colors.borderDivider`'s
 * own three entries, not a rounding of one of them), the urgent-dot
 * ring (`rgba(224,163,46,.16)` — derived from `colors.warning`'s RGB,
 * no token for the ring itself), the "Open … thread" button's border
 * (`#E4DEEE` — distinct from `colors.border`/`colors.borderStrong`),
 * and the button's hover background (`#FBFAFE` — the same real
 * literal C3's and C5's own cards already disclosed, reused here, not
 * newly derived). Four in this file; a fifth (`historyStyle.ts`'s
 * `report`-dot `#CFC6D6`) is disclosed separately in that module's own
 * comment — five disclosed literals total across the two new files.
 */
const SHELL_VARS = {
  "--atlas-hist-surface": colors.surface,
  "--atlas-hist-header-border": colors.borderDivider[0],
  "--atlas-hist-eyebrow": colors.inkFaint,
  "--atlas-hist-title": colors.ink,
  "--atlas-hist-lede": colors.inkSecondary,
  "--atlas-hist-rail": "#EDE8F2",
  "--atlas-hist-empty-rail": colors.border,
  "--atlas-hist-button-border": "#E4DEEE",
  "--atlas-hist-button-text": colors.accent,
  "--atlas-hist-button-hover-border": colors.focusHoverBorderNeutral,
  "--atlas-hist-button-hover-bg": "#FBFAFE",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-font-body": fontFamily.body,
} as CSSProperties;

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const style = HISTORY_KIND_STYLE[entry.kind];
  const dotSize = style.urgent ? "11px" : "10px";
  const dotBg = style.urgent ? style.dotColor : colors.surface;
  const dotBoxShadow = style.urgent
    ? `0 0 0 4px ${colors.pageBgDesktop}, 0 0 0 7px rgba(224,163,46,.16)`
    : `0 0 0 4px ${colors.pageBgDesktop}`;
  return (
    <div className={styles.row}>
      <div className={styles.time}>{entry.time}</div>
      <div className={styles.railWrap}>
        <span className={styles.rail} aria-hidden="true" />
        <span
          className={styles.dot}
          aria-hidden="true"
          style={{
            width: dotSize,
            height: dotSize,
            background: dotBg,
            border: `2px solid ${style.dotColor}`,
            boxShadow: dotBoxShadow,
          }}
        />
      </div>
      <div className={styles.body}>
        <div className={styles.entryLine}>
          <span className={styles.tag} style={{ background: style.tagBg, color: style.tagColor }}>
            {entry.kind}
          </span>
          <span className={styles.entryTitle}>{entry.title}</span>
          <span className={styles.entryPacket}>{entry.packet}</span>
        </div>
        <div className={styles.entryDetail}>
          {entry.who} — {entry.detail}
        </div>
        {entry.ref ? (
          <button type="button" className={styles.openButton}>
            Open {entry.ref} thread
          </button>
        ) : null}
      </div>
    </div>
  );
}

/**
 * Renders the History screen in full: header (eyebrow, title, 4 real
 * stats), the full real 10-entry timeline, and its own trailing
 * placeholder note. Every "Open … thread" button is a real `<button>`
 * with no `onClick` — genuinely inert, matching C4's/C6's established
 * pattern, since there is no real navigation destination wired yet.
 */
export function History() {
  return (
    <div style={SHELL_VARS}>
      <div className={styles.head}>
        <div className={styles.eyebrow}>m1-a · history</div>
        <h1 className={styles.title}>Everything that happened, in order</h1>
        <div className={styles.stats}>
          {HISTORY_STATS.map((stat) => (
            <span key={stat.label} className={styles.stat}>
              {stat.label}
              <b className={styles.statValue}>{stat.value}</b>
            </span>
          ))}
        </div>
      </div>
      <div className={styles.timeline}>
        {HISTORY_ENTRIES.map((entry) => (
          <HistoryRow key={`${entry.time}-${entry.title}`} entry={entry} />
        ))}
        <div className={styles.emptyRow}>
          <span />
          <div className={styles.emptyRail}>
            <span className={styles.emptyRailStub} aria-hidden="true" />
          </div>
          <div className={styles.emptyNote}>{HISTORY_EMPTY_NOTE}</div>
        </div>
      </div>
    </div>
  );
}

export default History;
```

`apps/atlas/src/history/History.test.tsx` (new):

```tsx
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { History } from "./History";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "./fixtures";
import { HISTORY_KIND_STYLE } from "./historyStyle";

afterEach(cleanup);

describe("History", () => {
  it("renders the real eyebrow, title, and all 4 real stats", () => {
    render(<History />);
    expect(screen.getByText("m1-a · history")).toBeInTheDocument();
    expect(screen.getByText("Everything that happened, in order")).toBeInTheDocument();
    // Two real stats ("Corrections spent" and "Decisions recorded")
    // share the identical real value "1", so each value is checked
    // scoped to its own label's container, not with a bare, ambiguous
    // getByText.
    for (const stat of HISTORY_STATS) {
      const label = screen.getByText(stat.label);
      const statScope = within(label.closest("span[class*='stat']") as HTMLElement);
      expect(statScope.getByText(stat.value)).toBeInTheDocument();
    }
  });

  it("renders all 10 real entries with their title, packet, kind tag, and who/detail line", () => {
    render(<History />);
    for (const entry of HISTORY_ENTRIES) {
      const title = screen.getByText(entry.title);
      const row = title.closest("div[class*='row']") as HTMLElement;
      expect(row).not.toBeNull();
      const rowScope = within(row);
      expect(rowScope.getByText(entry.time)).toBeInTheDocument();
      expect(rowScope.getByText(entry.kind)).toBeInTheDocument();
      expect(rowScope.getByText(`${entry.who} — ${entry.detail}`)).toBeInTheDocument();
    }
  });

  it("renders exactly 2 real, inert 'Open ... thread' buttons, for the 2 entries with a real ref", () => {
    render(<History />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(2);
    expect(screen.getByText("Open A.1 thread")).toBeInTheDocument();
    expect(screen.getByText("Open A.2 thread")).toBeInTheDocument();
  });

  it("renders the timeline's own real trailing placeholder note", () => {
    render(<History />);
    expect(screen.getByText(HISTORY_EMPTY_NOTE)).toBeInTheDocument();
  });

  it("marks blocked/escalated entries as urgent (filled dot, warning color) and every other kind as non-urgent", () => {
    expect(HISTORY_KIND_STYLE.blocked.urgent).toBe(true);
    expect(HISTORY_KIND_STYLE.escalated.urgent).toBe(true);
    expect(HISTORY_KIND_STYLE.dispatch.urgent).toBe(false);
    expect(HISTORY_KIND_STYLE.accepted.urgent).toBe(false);
    expect(HISTORY_KIND_STYLE.blocked.dotColor).toBe(colors.warning);
  });

  it("gives review and correction kinds the identical real review-colored tag, matching the reference file's shared style entry", () => {
    expect(HISTORY_KIND_STYLE.review).toEqual(HISTORY_KIND_STYLE.correction);
    expect(HISTORY_KIND_STYLE.review.tagColor).toBe(colors.reviewText);
  });

  it("discloses the report kind's dot color as a literal distinct from colors.navText's real, unrelated usage context", () => {
    expect(colors.navText).toBe("#CFC6D6");
    expect(HISTORY_KIND_STYLE.report.dotColor).toBe("#CFC6D6");
  });

  it("sets the header border and rail CSS variables to the real, checked values", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    const { container } = render(<History />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-hist-header-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-hist-rail")).toBe("#EDE8F2");
    expect(root.style.getPropertyValue("--atlas-hist-rail")).not.toBe(colors.borderDivider[0]);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<History />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `DesktopShell` or `App.tsx` —
   standalone, exactly like every prior Wave-E component.
2. This slice does not import from any `thread/`, `decision/`,
   `crash/`, `performance/`, or `gate/` file — a fully independent new
   directory, even though several entries describe the same real
   events those other slices' fixtures also use.
3. Every color is a real B2 token except the five explicitly
   disclosed (`#CFC6D6`, `#EDE8F2`/rail, `rgba(224,163,46,.16)`/urgent
   ring, `#E4DEEE`/button-border, and `#FBFAFE`/button-hover-background
   — five total, all individually checked directly against
   `colors.ts`).
4. Every "Open … thread" button is a real `<button>` with no
   `onClick` — genuinely inert, matching C4's/C6's established
   pattern.
5. No fictional "Architect agent" persona appears anywhere in this
   slice's rendered copy.
6. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, `apps/atlas/src/decision/`,
   `apps/atlas/src/crash/`, `apps/atlas/src/performance/`, or
   `apps/atlas/src/gate/` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/history/fixtures.ts` (new)
- `apps/atlas/src/history/historyStyle.ts` (new)
- `apps/atlas/src/history/History.module.css` (new)
- `apps/atlas/src/history/History.tsx` (new)
- `apps/atlas/src/history/History.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, and everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/decision/`, `apps/atlas/src/crash/`,
`apps/atlas/src/performance/`, `apps/atlas/src/gate/`, and
`apps/atlas/src/tokens/` are untouched.

The 9 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 99 total after this slice (90 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 CrashCard tests, 7 thread tests, 7
PacketHeader tests, 6 PerformanceHeader tests, 5 WeeklyWindowStrip
tests, 6 PerfRecordsList tests, 9 GateCriteriaList tests, 5
mobile-shell tests, 10 desktop-shell tests — + 9 new). `npm run build`
must still succeed; `History` is not expected to appear in the `dist/`
bundle, matching every prior standalone slice's own build-unaffected
proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `History` renders the History screen's real
   anatomy in full (header, 4 real stats, all 10 real timeline
   entries, and the timeline's own trailing placeholder note) using
   real B2 tokens with exactly five disclosed, checked literals.
2. **Operating and threat model:** a trusted local dev box; the two
   "Open … thread" buttons are real `<button>` elements (for correct
   semantics/focus) but carry no `onClick` — clicking one does nothing,
   by construction.
3. **Explicit exclusions:** any wiring into `DesktopShell`/`App.tsx`,
   any real navigation behind an "Open … thread" button (would require
   both `DesktopShell` wiring and a real `A.1` fixture thread, neither
   of which exists), the mobile layout variant.
4. **Assurance level:** practical component-rendering correctness with
   every entry, stat, and style value transcribed verbatim from the
   reference file, and every color either a real token or one
   explicitly disclosed and checked — proportionate to a read-only
   view with no data dependency and no consumer yet.
5. **Acceptance proof:** the 9 named tests, the existing 90 `apps/atlas`
   tests continuing to pass (99 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the five writable paths above;
   no new npm dependency; every color a real token property except the
   disclosed literals; no import of any other component-family module.
7. **Proportionality ceiling:** one timeline component, one fixtures
   module, one style-derivation module, one CSS Module; no wiring, no
   real navigation, no mobile variant, no second dataset.
8. **Stop and escalation rule:** wiring `History` into `DesktopShell`'s
   nav/content pane, or wiring a real "Open … thread" navigation
   (which would also require a real `A.1` fixture thread to open), is
   new, separately reviewed work — not decided implicitly here. A
   discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
