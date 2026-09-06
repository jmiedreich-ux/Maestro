# M2 Wave F — Activity tab's "Per action" records list (mobile Cost segment) — Candidate 01

**Slice ID:** `MB-SLICE-M2-F3D-PER-ACTION-RECORDS-01`
**Status:** `MergeReady`
**Base:** `57b788f` (full: `57b788f54d45f663063c906df5138894e8c937e9`, `origin/master`)

## Scope, deliberately minimal

Completes roadmap item 35, *"F3 — Activity tab: History/Agents/Cost
segmented, reusing E6/E4/E1–E3 data."* F3/F3B/F3C already built the
History segment, the Agents segment, and the Cost segment's first two
real blocks (the weekly-window card and the "m1-a split" card). This
slice adds the Cost segment's third and final block: the **"Per
action" records list**, reusing E2/E2B's own real `PERF_RECORDS`
fixture data (already reviewed, already merged, already consumed by
the desktop `PerfRecordsList.tsx`) as fresh mobile-specific cards.

This slice is frontend-only — no backend file touched. It modifies
exactly 3 existing files (`apps/atlas/src/shell/ActivityTab.tsx`,
`.module.css`, `.test.tsx`). No fixture file, no desktop component
(`PerfRecordsList.tsx`), is modified.

## Evidence

The real mobile mockup (`Atlas Mobile.dc.html:311-337`, this session's
own cached copy of the design-handoff reference — not checked into
this repository, matching the sourcing this program's every prior
packet has already disclosed) is the exact real markup for this block,
immediately following the split card (`:280-309`, F3C) inside the same
`isCost` conditional:

```
311: <div style="display:flex;align-items:baseline;gap:10px;margin:20px 2px 8px"><span style="font-size:16px;font-weight:700">Per action</span><span style="margin-left:auto;font-size:12.5px;color:#8E8299">{{ pfCount }} records</span></div>
312: <div style="display:flex;flex-direction:column;gap:8px">
313: <sc-for list="{{ perf }}" as="p" hint-placeholder-count="4">
314: <div style="border-radius:18px;background:#fff;overflow:hidden">
315:   <button onClick="{{ p.onToggle }}" style="display:block;width:100%;padding:13px 15px;border:0;background:transparent;text-align:left;cursor:pointer">
316:     <div style="display:flex;align-items:baseline;gap:9px"><span style="min-width:0;font-size:14.5px;font-weight:600;text-wrap:pretty">{{ p.action }}</span><span style="flex:none;margin-left:auto;padding:2px 7px;border-radius:6px;background:{{ p.tagBg }};color:{{ p.tagColor }};font:600 9.5px 'IBM Plex Mono',monospace;letter-spacing:.07em;text-transform:uppercase">{{ p.outcome }}</span></div>
317:     <div style="margin-top:3px;font:500 11px 'IBM Plex Mono',monospace;color:#A79BB4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ p.packet }} · {{ p.who }} · {{ p.model }}</div>
318:     <div style="display:flex;gap:14px;margin-top:8px;font:500 12px 'IBM Plex Mono',monospace"><span>{{ p.tokens }}</span><span style="color:{{ p.costColor }}">{{ p.cost }}</span><span style="margin-left:auto;color:#8E8299">{{ p.elapsed }}</span></div>
319:   </button>
320:   <sc-if value="{{ p.open }}" hint-placeholder-val="{{ false }}">
321:   <div style="border-top:1px solid #F0ECF5;background:#FCFBFD;padding:12px 15px 14px;animation:rise .18s ease-out">
322-331: (per-group name + per-row label/value, identical shape to the desktop version's own `record.groups`)
333:   </div>
334:   </sc-if>
335: </div>
336: </sc-for>
337: </div>
```

**Real fact, checked directly:** the mockup's own `{{ p.tagBg }}`,
`{{ p.tagColor }}`, `{{ p.costColor }}`, and detail-row `{{ r.color
}}` are unresolved template placeholders with no literal value of
their own in this file — confirming the mobile surface shares the
identical underlying `perf` derivation function as the desktop
version, whose own resolved values `PerfRecordsList.tsx` already
derived and disclosed (`SHELL_VARS`, `COST_CLASS`,
`DETAIL_VALUE_CLASS`, `outcomeClass`). Reusing that exact mapping here
is a transcription of an already-established real fact, not a new
derivation.

`apps/atlas/src/shell/ActivityTab.tsx`'s own `CostSegment()` (as
merged by F3C) already contains an explicit doc-comment insertion
point: *"The 'Per action' records list (reusing E2/E2B's data) is
separate, future work... splitting an oversized roadmap item into
independently reviewable slices."* This slice is that future work.
There is no existing placeholder or stub to replace — this is purely
additive, appended inside `CostSegment()`'s returned fragment after
the `.splitCard` block.

## Design rationale

1. **A new `RecordsList`/`RecordCard` pair, not `<PerfRecordsList />`
   mounted as-is.** Matching this file's own already-established
   convention for every other segment (`HistoryRow`/`AgentCardMobile`
   reuse E6/E4's fixture *data* but write fresh mobile-specific
   JSX/CSS, never mount the desktop component): the real mobile markup
   is a single-column stacked card (action+tag, then packet·who·model,
   then tokens/cost/elapsed), not `PerfRecordsList.tsx`'s own 5-column
   CSS grid row, which has no mobile equivalent.
2. **Every color reused verbatim from `PerfRecordsList.tsx`'s own
   already-reviewed mapping** (`SHELL_VARS`, `COST_CLASS`→
   `RECORDS_COST_CLASS`, `DETAIL_VALUE_CLASS`→
   `RECORDS_DETAIL_VALUE_CLASS`, `outcomeClass`→`recordsOutcomeClass`)
   — not re-derived a third time, per the Evidence section's own
   confirmation that both surfaces share the identical underlying
   data-derivation function.
3. **Disclosed, minor adaptation:** the real mobile markup's own
   action/tokens spans (`Atlas Mobile.dc.html:316,318`) set no
   explicit color of their own, unlike the desktop `.action`/`.tokens`
   classes, which do (`colors.ink`). This slice applies the same real
   `colors.ink` explicitly here too, rather than leaving text to an
   unstyled browser default — consistent with this program's own
   "every color is a real token" discipline, not a fabricated value.
4. **Real accordion, matching `PerfRecordsList.tsx`'s own single
   `openId` state** (E2/E2B) — opening one record's detail closes
   whichever other record was open, not one independent boolean per
   record.
5. **Derived, not hand-typed, count:** `PERF_RECORDS.length` is read
   directly for the "N records" header, matching this program's own
   C7/E7B precedent for any displayed count that could drift from its
   own source fixture.
6. **Pre-disclosed test-scoping trap, respected:** the F3C Decision
   Fidelity review flagged that querying `getByRole("button", { name:
   "Cost" })` unscoped becomes ambiguous once the Cost segment is
   selected (the outer segmented control's own "Cost" tab and the
   split card's own basis toggle's "Cost" button coexist). This
   slice's own detail-row tests hit exactly this trap a second time —
   several real `PERF_RECORDS` rows use the literal label "Cost" — and
   scope every such query to the specific record's own card first,
   never a bare document-wide `getByText("Cost"...)`.

## Guards

1. This slice modifies exactly 3 existing files
   (`apps/atlas/src/shell/ActivityTab.tsx`, `.module.css`,
   `.test.tsx`) — no backend file, no fixture file, no desktop
   component, touched.
2. `apps/atlas/src/performance/perfRecords.ts`,
   `PerfRecordsList.tsx`, and `.module.css` are read-only imports
   (types and the `PERF_RECORDS` constant only) — never modified.
3. Every other segment (History, Agents) and the Cost segment's first
   two blocks (weekly-window card, split card) render byte-identical
   to their F3/F3B/F3C-merged state — this slice's own diff is
   strictly additive within `CostSegment()`.
4. Every displayed record field (action, packet, who, model, tokens,
   cost, elapsed, outcome, every detail group/row/note) is the real
   `PERF_RECORDS` fixture value — no new fixture data invented, no
   fictional persona, no fictional agent.
5. The records list starts fully closed (no `openId` pre-selected),
   matching the real mockup's own `hint-placeholder-val="{{ false }}"`
   default for `p.open`.

## Corrected — Decision Fidelity review findings (RESOLVED)

An independent Decision Fidelity review returned **PASS WITH
NON-BLOCKING NOTES** — two citation/bookkeeping defects, no functional
defects, both fixed at zero cost before finalizing this packet as
`MergeReady`:

1. **Wrong line citation in shipped code (fixed).** `ActivityTab.tsx`'s
   own `SHELL_VARS` doc comment cited `Atlas Mobile.dc.html:319,321`
   for the claim that the action/tokens spans set no explicit color of
   their own — real lines 319/321 are `</button>` and the detail
   panel's own opening `<div>`, neither the spans in question. The
   correct real lines are **316, 318** (confirmed directly against the
   mockup file). Corrected in the code block below.
2. **Miscounted collapsed line range in this packet's own Evidence
   section (fixed).** The quoted excerpt's collapsed placeholder
   ("322-336: (per-group name + per-row label/value...)") was followed
   by closing tags mislabeled 337-341; the real file's corresponding
   closing tags are at **333-337** (the collapsed range should have
   read "322-331," 10 lines, not 15). Every trailing line number in the
   Evidence section's quote was off by 4 — corrected above.

Neither finding affected the shipped component's behavior, the test
suite, or the build — both are transcription/citation defects (a
comment string), caught and fixed before merge. Re-verified after the
fix, in isolation: clean typecheck, clean lint, clean build, and
`ActivityTab.test.tsx` itself unchanged at 21/21 passing (the fix
touches only a code comment, not any executable line or test
assertion) — re-confirmed a second time alongside this session's own
concurrent, unrelated F4B work sharing the same scratch worktree at
verification time (25/25 test files, 216/216 tests passing there,
`ActivityTab.test.tsx` itself still exactly 21 tests within that
total).

## `apps/atlas/src/shell/ActivityTab.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily, motion } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "../history/fixtures";
import { HISTORY_KIND_STYLE } from "../history/historyStyle";
import { AGENTS, AGENTS_STATS, type AgentEntry, type AgentStat } from "../agents/agents";
import { AGENT_STYLE } from "../agents/agentStyle";
import { WEEKLY_WINDOW } from "../performance/weeklyWindow";
import { SPLIT, SPLIT_BASES, type SplitBasisKey, type SplitPart } from "../performance/perfBreakdown";
import {
  PERF_RECORDS,
  type PerfCostKind,
  type PerfDetailKind,
  type PerfOutcome,
  type PerfRecord,
} from "../performance/perfRecords";
import styles from "./ActivityTab.module.css";

type ActivitySegment = "hist" | "agents" | "cost";

const SEGMENTS: ReadonlyArray<{ key: ActivitySegment; label: string }> = [
  { key: "hist", label: "History" },
  { key: "agents", label: "Agents" },
  { key: "cost", label: "Cost" },
];

/**
 * Mobile Activity-tab colors from `Atlas Mobile.dc.html`'s real `isAct`
 * markup — the header and segmented control (lines 219-227) and the
 * History segment this slice builds (lines 230-249); the real `isAct`
 * block itself continues past line 249 through the Agents (252-278)
 * and Cost (280 onward) segments this slice deliberately does not
 * build yet (see "Scope, deliberately minimal" in this slice's own
 * packet) — checked directly against `colors.ts`. Real token matches: `colors.segmentedTrack[0]`
 * (the segmented control's own track background, `#EDE9F3`, line 222 —
 * a different real index of the same array E3's `PerfBreakdownCard`
 * already uses `[1]` from, both real, not invented), `colors.segmentedSelected`
 * (the selected segment's own white background, `#fff`, matching the
 * real `renderVals()` rule `bg: s.seg===k?'#fff':'transparent'`),
 * `colors.ink`/`colors.inkMuted` (selected/unselected label color,
 * matching the same rule's `color:` branch), and `colors.pageBgMobile`
 * (the timeline dot's own outer ring background, `#F7F5FA`, line 240 —
 * simpler than desktop History's own urgent-ring treatment, since the
 * real mobile markup has no second ring layer at all). The timeline
 * rail (`#E6E0EE`, line 239) has no equivalent token and stays a
 * disclosed literal — a different real value from desktop History's
 * own disclosed rail color (`#EDE8F2`), not a typo of it, checked
 * directly against both reference files.
 *
 * The trailing timeline note reuses the exact real
 * `HISTORY_EMPTY_NOTE` constant E6's own `History.tsx` already
 * established, rather than transcribing the mobile markup's own
 * shorter literal text at line 249 ("...have not been dispatched.",
 * missing the desktop constant's own "— nothing to record yet." tail)
 * — the same real fact, stated once, matching this program's own
 * single-source-of-identity precedent (F2 reused C7's eyebrow/title
 * pair rather than a mockup-specific abbreviation for the same
 * reason).
 *
 * The Agents segment this slice adds (`Atlas Mobile.dc.html:252-278`)
 * reuses E4's real `AGENTS`/`AGENTS_STATS`/`AGENT_STYLE` fixture data
 * verbatim, but is deliberately NOT `<AgentsRoster />` mounted as-is:
 * that component is desktop-only by E4's own written scope (its own
 * `.roster` grid hardcodes the reference file's own `agCols` desktop
 * branch, `repeat(auto-fit,minmax(300px,1fr))`, never the `mobile ?
 * '1fr'` branch; its `.head` renders an eyebrow/`<h1>` and its
 * `.footer` renders an "Open thread" button, neither of which exists
 * anywhere in the real mobile `isAgents` markup, checked directly).
 * `AgentCardMobile` below is new mobile-specific JSX/CSS, matching
 * this same file's own established convention for the History segment
 * (reuse E6's fixture/style *data*, write fresh mobile markup, not the
 * desktop component). Real token matches for the new
 * `--atlas-ag-*` vars: `colors.borderDivider[2]` (`#F0ECF5`, the
 * progress-bar track, line 271 — a different real index of the same
 * array this file's own History rail styling neighbors, not
 * `AgentsRoster`'s own `colors.borderDivider[0]`), `colors.inkSecondary`
 * (`#6C6376`, the agent line's own body text, line 269 — the same
 * token this file's own `--atlas-entry-detail` already uses),
 * `colors.inkFaint` (`#A79BB4`, the packet chip, line 267),
 * `colors.inkMuted` (`#8E8299`, the locks line, line 274), and
 * `colors.warningText`/`colors.inkMuted` (urgent/normal due-label
 * color, matching `AgentsRoster.tsx`'s own already-reviewed
 * `--atlas-ag-due-urgent`/`--atlas-ag-due` pair). The state dot's own
 * bg/hollow-border logic (`isWait` → transparent fill, hollow border)
 * reuses `AgentsRoster.tsx`'s own already-reviewed derivation exactly,
 * rather than inventing new logic for the mobile markup's own separate
 * `stateDotBg`/`stateDotBorder` template values (whose exact source
 * computation isn't present in any fixture this program has already
 * reviewed) — the real mobile card has no border/head/footer, so this
 * file's own `.agentCard` intentionally omits `--atlas-ag-card-border`
 * and any head var entirely, rather than declaring one that no rule
 * would ever consume. The locks row's own top-border literal
 * (`#F3F0F6`, line 274) is `colors.borderDivider[1]` — a different
 * real index of the same array from the bar track's own
 * `colors.borderDivider[2]`, checked directly, not a reused value.
 *
 * **Corrected — non-blocking finding from Decision Fidelity review:**
 * the per-stat value color (`AGENTS_STATS`' own `stat.color` enum) is
 * the exact same 4-value enum `AgentsRoster.tsx` already handles via
 * named CSS custom properties (`--atlas-ag-stat-accent` etc.) plus
 * static classes (`STAT_VALUE_CLASS`) — this file's first draft
 * instead applied it as a raw inline `style={{ color: ... }}`, an
 * undisclosed deviation from that sibling component's own established
 * convention for identical data (both render identically; this was a
 * consistency gap, not a functional defect). Fixed to match:
 * `STAT_VALUE_CLASS` below maps each `stat.color` to a static class
 * consuming one of four new `--atlas-ag-stat-*` vars, exactly mirroring
 * `AgentsRoster.tsx`'s own already-reviewed pattern.
 *
 * The Cost segment's first two real blocks this slice adds
 * (`Atlas Mobile.dc.html:280-309`) reuse E1B's real `WEEKLY_WINDOW`
 * fixture and E3's real `SPLIT`/`SPLIT_BASES` fixture data verbatim —
 * both already real, reviewed, and (for `SPLIT.cost.role`) already
 * carrying the real Local-Qwen persona correction for the fictional
 * "Architect agent," not re-litigated here. Real token matches for the
 * new `--atlas-week-*`/`--atlas-split-*` vars: `colors.inkMuted`
 * (`#8E8299`, both eyebrows — "openai weekly window" line 282,
 * "m1-a split" line 288), `colors.warningText` (`#8A5A08`, the
 * unattributed figure, line 283), `colors.inkFaint` (`#A79BB4` — the
 * weekly-window meta line, matching the real mobile mockup's own
 * literal directly, and separately the split card's own group-name/
 * legend-abs colors, matching E3's own `PerfBreakdownCard.tsx` token
 * choices exactly; **not** a `WeeklyWindowStrip.tsx` precedent for
 * those latter two fields, which has no group/legend layout at all —
 * `WeeklyWindowStrip.tsx`'s own meta field uses `colors.inkMuted`, not
 * `inkFaint` — corrected per Decision Fidelity review),
 * `colors.inkSecondary` (`#6C6376`, the legend label, line 303 — the
 * same token this file's own `--atlas-entry-detail` and `--atlas-ag-line`
 * already use), `colors.segmentedTrack[2]` (`#F2EFF7`, both the
 * segmented control's own track and the bar's own track, lines 289/298
 * — the third real index of the array this file's own outer segmented
 * control already uses `[0]` from), and the same 4 real
 * `SPLIT_COLORS` E3's own `PerfBreakdownCard.tsx` already discloses
 * (`colors.accent`/`colors.review`/`colors.success`/`colors.borderDashed[2]`),
 * applied here via inline per-index style rather than E3's own static
 * CSS classes — matching this file's own established convention for
 * per-item dynamic coloring (`HistoryRow`, `AgentCardMobile`), not
 * duplicating four new always-identical CSS classes. The weekly-window
 * sentence's own body-text color (`#4C4457`, line 283) is a disclosed
 * literal, checked against every color family in `colors.ts` — no
 * token matches.
 *
 * **Real fact, disclosed, not silently reused:** this slice reuses
 * `WEEKLY_WINDOW`'s own already-real `meta` ("observed 15:02 · resets
 * Mon 00:00") and `caption` ("Local Qwen is shown as capacity and time
 * only...") fields as two separate lines — exactly matching E1B's own
 * `WeeklyWindowStrip.tsx` rendering — rather than transcribing the
 * mobile mockup's own shorter, compressed single line ("observed 15:02
 * · local Qwen kept separate", line 284), which paraphrases both real
 * fields into one and drops real information. This is the same
 * single-source-of-identity precedent F3's own `HISTORY_EMPTY_NOTE`
 * reuse and F2's own C7 eyebrow/title reuse already established: state
 * the one real fact once, not a second, lossier mockup-specific
 * abbreviation of it.
 */
const SHELL_VARS = {
  "--atlas-seg-track": colors.segmentedTrack[0],
  "--atlas-seg-selected-bg": colors.segmentedSelected,
  "--atlas-seg-selected-ink": colors.ink,
  "--atlas-seg-ink": colors.inkMuted,
  "--atlas-stat-label": colors.inkMuted,
  "--atlas-stat-value": colors.ink,
  "--atlas-rail": "#E6E0EE",
  "--atlas-dot-ring": colors.pageBgMobile,
  "--atlas-entry-detail": colors.inkSecondary,
  "--atlas-empty-note": colors.inkFaint,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-ag-card-surface": colors.surface,
  "--atlas-ag-name": colors.ink,
  "--atlas-ag-packet": colors.inkFaint,
  "--atlas-ag-line": colors.inkSecondary,
  "--atlas-ag-bar-track": colors.borderDivider[2],
  "--atlas-ag-footer-border": colors.borderDivider[1],
  "--atlas-ag-due": colors.inkMuted,
  "--atlas-ag-due-urgent": colors.warningText,
  "--atlas-ag-locks": colors.inkMuted,
  "--atlas-ag-wait-dot-border": colors.borderDashed[2],
  "--atlas-ag-stat-accent": colors.accent,
  "--atlas-ag-stat-warning": colors.warningText,
  "--atlas-ag-stat-accent-hover": colors.accentHover,
  "--atlas-ag-stat-ink": colors.ink,
  "--atlas-cost-card-surface": colors.surface,
  "--atlas-week-label": colors.inkMuted,
  "--atlas-week-body": "#4C4457",
  "--atlas-week-warning": colors.warningText,
  "--atlas-week-meta": colors.inkFaint,
  "--atlas-week-caption": colors.inkFaint,
  "--atlas-split-track": colors.segmentedTrack[2],
  "--atlas-split-seg-selected-bg": colors.segmentedSelected,
  "--atlas-split-seg-selected-ink": colors.ink,
  "--atlas-split-seg-ink": colors.inkMuted,
  "--atlas-split-basis-note": colors.inkMuted,
  "--atlas-split-group-name": colors.inkFaint,
  "--atlas-split-legend-label": colors.inkSecondary,
  "--atlas-split-legend-pct": colors.ink,
  "--atlas-split-legend-abs": colors.inkFaint,
  "--atlas-split-caveat": colors.inkMuted,
  // The "Per action" records list's own colors — every one a real
  // token, transcribed verbatim from `PerfRecordsList.tsx`'s own
  // `SHELL_VARS` (E2/E2B), which already derived this exact mapping
  // from `Atlas Explorations.dc.html`'s real per-record derivation
  // logic. The mobile mockup (`Atlas Mobile.dc.html:311-337`) renders
  // the same `{{ p.tagBg }}`/`{{ p.costColor }}`/detail-row `{{ r.color
  // }}` template placeholders with no literal values of its own —
  // confirming both surfaces share the same underlying data-derivation
  // function, so reusing the desktop mapping exactly (rather than
  // re-deriving a third copy) is a real fact, not an assumption.
  "--atlas-records-card-surface": colors.surface,
  // The real mobile markup's own action/tokens spans set no explicit
  // color of their own (`Atlas Mobile.dc.html:316,318`) — unlike the
  // desktop `.action`/`.tokens` classes, which do (`colors.ink`). Since
  // both surfaces share the identical underlying `PERF_RECORDS` data
  // and derivation, and this program's own established discipline is
  // "every color is a real token, never an unset default," this slice
  // applies the same real `colors.ink` explicitly here too, rather than
  // leaving it to an unstyled browser default — a disclosed, minor
  // adaptation, not a fabricated value.
  "--atlas-records-row-ink": colors.ink,
  "--atlas-records-row-faint": colors.inkFaint,
  "--atlas-records-row-muted": colors.inkMuted,
  "--atlas-records-row-warning": colors.warningText,
  "--atlas-records-tag-blocked-bg": colors.warningChip,
  "--atlas-records-tag-blocked-ink": colors.warningText,
  "--atlas-records-tag-good-bg": colors.successWash,
  "--atlas-records-tag-good-ink": colors.successText,
  "--atlas-records-tag-neutral-bg": colors.neutralChip,
  "--atlas-records-tag-neutral-ink": colors.inkSecondary,
  "--atlas-records-detail-border": colors.borderDivider[2],
  "--atlas-records-detail-bg": colors.focusHoverCard,
  "--atlas-records-detail-row-divider": colors.borderDivider[1],
  "--atlas-records-detail-group-name": colors.inkFaint,
  "--atlas-records-detail-label": colors.inkSecondary,
  "--atlas-records-detail-note": colors.inkMuted,
  "--atlas-records-detail-value-default": colors.ink,
  "--atlas-records-detail-value-ok": colors.successText,
  "--atlas-records-detail-value-est": colors.warningText,
  "--atlas-records-detail-value-warn": colors.dangerText,
  "--atlas-records-detail-value-na": colors.inkFaint,
  "--atlas-records-rise-translate": `${motion.rise.translateYPx}px`,
  "--atlas-records-rise-duration": `${motion.rise.durationS.min}s`,
  "--atlas-records-rise-easing": motion.rise.easing,
} as CSSProperties;

const SPLIT_COLORS = [colors.accent, colors.review, colors.success, colors.borderDashed[2]];

/**
 * Transcribed verbatim from `PerfBreakdownCard.tsx`'s own bar-width
 * derivation (`w: Math.max(pct, 0.6) + '%'`) — a 0%-share part still
 * renders a thin, visible sliver rather than vanishing entirely.
 */
function barWidth(pct: number): string {
  return `${Math.max(pct, 0.6)}%`;
}

const STAT_VALUE_CLASS: Record<AgentStat["color"], string> = {
  accent: styles.statValueAccent,
  warningText: styles.statValueWarning,
  accentHover: styles.statValueAccentHover,
  ink: styles.statValueInk,
};

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const style = HISTORY_KIND_STYLE[entry.kind];
  const dotSize = style.urgent ? 11 : 10;
  const dotBg = style.urgent ? style.dotColor : colors.surface;
  return (
    <div className={styles.row}>
      <div className={styles.railCol}>
        <span className={styles.rail} aria-hidden="true" />
        <span
          className={styles.dot}
          aria-hidden="true"
          style={{ width: dotSize, height: dotSize, background: dotBg, borderColor: style.dotColor }}
        />
      </div>
      <div className={styles.body}>
        <div className={styles.entryLine}>
          <span className={styles.tag} style={{ background: style.tagBg, color: style.tagColor }}>
            {entry.kind}
          </span>
          <span className={styles.entryMeta}>
            {entry.time} · {entry.packet}
          </span>
        </div>
        <div className={styles.entryTitle}>{entry.title}</div>
        <div className={styles.entryDetail}>{entry.detail}</div>
      </div>
    </div>
  );
}

function AgentCardMobile({ agent }: { agent: AgentEntry }) {
  const style = AGENT_STYLE[agent.styleKey];
  const isWait = agent.styleKey === "wait";
  return (
    <div className={styles.agentCard}>
      <div className={styles.agentTop}>
        <span className={styles.agentAvatar} style={{ background: style.avBg, color: style.avColor }}>
          {agent.av}
        </span>
        <div className={styles.agentIdentity}>
          <div className={styles.agentName}>{agent.name}</div>
          <div className={styles.agentState} style={{ color: style.stateColor }}>
            <span
              className={`${styles.agentStateDot} ${isWait ? styles.agentStateDotHollow : ""}`}
              style={{ background: isWait ? "transparent" : style.barColor }}
            />
            {agent.state}
          </div>
        </div>
        <span className={styles.agentPacket}>{agent.packet}</span>
      </div>
      <div className={styles.agentLine}>{agent.line}</div>
      <div className={styles.agentBarBlock}>
        <div className={styles.agentBarTrack}>
          <span className={styles.agentBarFill} style={{ width: agent.pct, background: style.barColor }} />
        </div>
        <div className={styles.agentProgressRow}>
          <span>{agent.progress}</span>
          <span className={agent.urgent ? styles.agentDueUrgent : styles.agentDue}>{agent.due}</span>
        </div>
      </div>
      <div className={styles.agentLocks}>{agent.locks}</div>
    </div>
  );
}

function CostSplitGroup({ name, parts }: { name: string; parts: SplitPart[] }) {
  return (
    <div className={styles.splitGroup}>
      <div className={styles.splitGroupName}>{name}</div>
      <div className={styles.splitBar}>
        {parts.map((part, index) => (
          <span
            key={part.label}
            className={styles.splitBarSegment}
            style={{ width: barWidth(part.pct), background: SPLIT_COLORS[index] }}
          />
        ))}
      </div>
      <div className={styles.splitLegend}>
        {parts.map((part, index) => (
          <div key={part.label} className={styles.splitLegendItem}>
            <span className={styles.splitLegendDot} style={{ background: SPLIT_COLORS[index] }} />
            <span className={styles.splitLegendLabel}>{part.label}</span>
            <b className={styles.splitLegendPct}>{part.pct}%</b>
            <span className={styles.splitLegendAbs}>{part.abs}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const RECORDS_COST_CLASS: Record<PerfCostKind, string> = {
  billed: styles.recordCostBilled,
  est: styles.recordCostEst,
  none: styles.recordCostNone,
};

const RECORDS_DETAIL_VALUE_CLASS: Record<PerfDetailKind, string> = {
  "": styles.recordDetailValueDefault,
  est: styles.recordDetailValueEst,
  ok: styles.recordDetailValueOk,
  warn: styles.recordDetailValueWarn,
  na: styles.recordDetailValueNa,
};

function recordsOutcomeClass(outcome: PerfOutcome): string {
  if (outcome === "blocked") return styles.recordsOutcomeBlocked;
  if (outcome === "approved" || outcome === "passed") return styles.recordsOutcomeGood;
  return styles.recordsOutcomeNeutral;
}

/**
 * The mobile-specific row/card markup transcribed from `Atlas Mobile
 * .dc.html:314-337` — a single stacked card per record (action + tag,
 * then packet·who·model, then tokens/cost/elapsed), not the desktop
 * `PerfRecordsList.tsx`'s own 5-column grid row, which has no mobile
 * equivalent (real markup confirms a narrower single-column layout
 * throughout). The expandable detail panel below reuses the exact
 * same real per-group/per-row shape and color derivation as the
 * desktop version (`record.groups`), since both surfaces render the
 * identical real `PERF_RECORDS` data.
 */
function RecordCard({
  record,
  open,
  onToggle,
}: {
  record: PerfRecord;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={styles.recordCard}>
      <button type="button" className={styles.recordButton} onClick={onToggle}>
        <div className={styles.recordTopLine}>
          <span className={styles.recordAction}>{record.action}</span>
          <span className={`${styles.recordOutcome} ${recordsOutcomeClass(record.outcome)}`}>
            {record.outcome}
          </span>
        </div>
        <div className={styles.recordMeta}>
          {record.packet} · {record.who} · {record.model}
        </div>
        <div className={styles.recordStatLine}>
          <span>{record.tokens}</span>
          <span className={RECORDS_COST_CLASS[record.costKind]}>{record.cost}</span>
          <span className={styles.recordElapsed}>{record.elapsed}</span>
        </div>
      </button>
      {open && (
        <div className={styles.recordDetail}>
          {record.groups.map((group) => (
            <div key={group.name} className={styles.recordDetailGroup}>
              <div className={styles.recordDetailGroupName}>{group.name}</div>
              <div className={styles.recordDetailRows}>
                {group.rows.map((row) => (
                  <div key={row.label} className={styles.recordDetailRow}>
                    <span className={styles.recordDetailLabel}>{row.label}</span>
                    <b
                      className={`${styles.recordDetailValue} ${RECORDS_DETAIL_VALUE_CLASS[row.kind]}`}
                    >
                      {row.value}
                    </b>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <div className={styles.recordDetailNote}>{record.note}</div>
        </div>
      )}
    </div>
  );
}

/**
 * Real accordion: matching `PerfRecordsList.tsx`'s own single `openId`
 * state (E2/E2B) — opening one record's detail closes whichever other
 * record was open, not one independent boolean per record. `pfCount`
 * is derived from the real `PERF_RECORDS.length`, never a hand-typed
 * literal that happens to currently match (this program's own C7/E7B
 * precedent for any displayed count).
 */
function RecordsList() {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <>
      <div className={styles.recordsHead}>
        <span className={styles.recordsTitle}>Per action</span>
        <span className={styles.recordsCount}>{PERF_RECORDS.length} records</span>
      </div>
      <div className={styles.recordsList}>
        {PERF_RECORDS.map((record) => (
          <RecordCard
            key={record.id}
            record={record}
            open={openId === record.id}
            onToggle={() => setOpenId((current) => (current === record.id ? null : record.id))}
          />
        ))}
      </div>
    </>
  );
}

function CostSegment() {
  const [basis, setBasis] = useState<SplitBasisKey>("cost");
  const data = SPLIT[basis];

  return (
    <>
      <div className={styles.weekCard}>
        <div className={styles.weekLabel}>openai weekly window</div>
        <div className={styles.weekBody}>
          {WEEKLY_WINDOW.reconciledPercent} controlled + {WEEKLY_WINDOW.coarsePercent} coarse +{" "}
          <b className={styles.weekWarning}>{WEEKLY_WINDOW.unattributedPercent} unattributed</b> ={" "}
          <b>{WEEKLY_WINDOW.observedChangePercent}</b> observed change
        </div>
        <div className={styles.weekMeta}>{WEEKLY_WINDOW.meta}</div>
        <div className={styles.weekCaption}>{WEEKLY_WINDOW.caption}</div>
      </div>

      <div className={styles.splitCard}>
        <div className={styles.splitHead}>
          <span className={styles.splitLabel}>m1-a split</span>
        </div>
        <div className={styles.splitSegmented}>
          {SPLIT_BASES.map((b) => (
            <button
              key={b.key}
              type="button"
              className={`${styles.splitSegButton} ${basis === b.key ? styles.splitSegSelected : ""}`}
              onClick={() => setBasis(b.key)}
            >
              {b.label}
            </button>
          ))}
        </div>
        <div className={styles.splitBasisNote}>share of {data.note}</div>
        <CostSplitGroup name="by role" parts={data.role} />
        <CostSplitGroup name="by kind of work" parts={data.work} />
        <div className={styles.splitCaveat}>{data.caveat}</div>
      </div>

      <RecordsList />
    </>
  );
}

/**
 * Mobile "Activity" tab — the reference file's own `isAct` view: a
 * page title, a real 3-way segmented control (History/Agents/Cost,
 * defaulting to History, matching the reference file's own real
 * `seg: 'hist'` initial state), and the History segment's real content
 * reusing E6's own `HISTORY_STATS`/`HISTORY_ENTRIES`/`HISTORY_KIND_STYLE`
 * fixture and style data restyled as a simpler mobile timeline (no
 * "Open … thread" button — the real mobile markup has no such control
 * on this surface, checked directly), and the Agents segment's real
 * content reusing E4's own `AGENTS`/`AGENTS_STATS`/`AGENT_STYLE`
 * fixture and style data as fresh mobile-specific cards (see
 * `AgentCardMobile` above — not `<AgentsRoster />`, which is
 * desktop-only by its own established scope). The Cost segment's real
 * content, reusing E1B's/E3's own fixture data — the weekly-window
 * card and the "m1-a split" card (F3C) — plus the "Per action" records
 * list (F3D, this slice), reusing E2/E2B's own `PERF_RECORDS` fixture
 * data as fresh mobile-specific cards (see `RecordsList`/`RecordCard`
 * above — not `<PerfRecordsList />`, which is desktop-only by its own
 * established scope, matching `AgentCardMobile`'s own precedent).
 * Completes roadmap item 35.
 */
export function ActivityTab() {
  const [segment, setSegment] = useState<ActivitySegment>("hist");

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Activity</h1>
        <div className={styles.segmented}>
          {SEGMENTS.map((seg) => (
            <button
              key={seg.key}
              type="button"
              className={`${styles.segButton} ${segment === seg.key ? styles.segSelected : ""}`}
              aria-current={segment === seg.key ? "true" : undefined}
              onClick={() => setSegment(seg.key)}
            >
              {seg.label}
            </button>
          ))}
        </div>
      </div>
      <div className={styles.content}>
        {segment === "hist" ? (
          <>
            <div className={styles.stats}>
              {HISTORY_STATS.map((stat) => (
                <span key={stat.label} className={styles.stat}>
                  {stat.label}
                  <b className={styles.statValue}>{stat.value}</b>
                </span>
              ))}
            </div>
            <div className={styles.timeline}>
              {HISTORY_ENTRIES.map((entry) => (
                <HistoryRow key={`${entry.time}-${entry.title}`} entry={entry} />
              ))}
            </div>
            <div className={styles.emptyNote}>{HISTORY_EMPTY_NOTE}</div>
          </>
        ) : segment === "agents" ? (
          <>
            <div className={styles.stats}>
              {AGENTS_STATS.map((stat) => (
                <span key={stat.label} className={styles.stat}>
                  {stat.label}
                  <b className={`${styles.statValue} ${STAT_VALUE_CLASS[stat.color]}`}>{stat.value}</b>
                </span>
              ))}
            </div>
            <div className={styles.agentList}>
              {AGENTS.map((agent) => (
                <AgentCardMobile key={agent.ref + agent.name} agent={agent} />
              ))}
            </div>
          </>
        ) : (
          <CostSegment />
        )}
      </div>
    </div>
  );
}

export default ActivityTab;
```

## `apps/atlas/src/shell/ActivityTab.module.css` (modified — full new content)

```css
.tab {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header {
  flex: none;
  padding: 8px 18px 10px;
}

.pageTitle {
  margin: 0 0 10px;
  font-family: var(--atlas-font-display);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.segmented {
  display: flex;
  gap: 3px;
  padding: 3px;
  border-radius: 13px;
  background: var(--atlas-seg-track);
}

.segButton {
  flex: 1;
  min-height: 38px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--atlas-seg-ink);
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 600;
}

.segSelected {
  background: var(--atlas-seg-selected-bg);
  color: var(--atlas-seg-selected-ink);
}

.content {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 4px 18px 22px;
}

.timeline {
  display: flex;
  flex-direction: column;
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  padding: 4px 2px 12px;
  font-size: 12.5px;
  color: var(--atlas-stat-label);
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.statValue {
  font-family: var(--atlas-font-mono);
  color: var(--atlas-stat-value);
}

.row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr);
  gap: 12px;
}

.railCol {
  position: relative;
  display: flex;
  justify-content: center;
}

.rail {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1.5px;
  background: var(--atlas-rail);
}

.dot {
  position: relative;
  margin-top: 16px;
  box-sizing: border-box;
  border-radius: 50%;
  border-width: 2px;
  border-style: solid;
  box-shadow: 0 0 0 4px var(--atlas-dot-ring);
}

.body {
  min-width: 0;
  padding: 12px 0 4px;
}

.entryLine {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.tag {
  flex: none;
  padding: 2px 7px;
  border-radius: 6px;
  font: 600 9.5px var(--atlas-font-mono);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.entryMeta {
  margin-left: auto;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-empty-note);
}

.entryTitle {
  margin-top: 5px;
  font-size: 14.5px;
  font-weight: 600;
  line-height: 1.35;
}

.entryDetail {
  margin-top: 3px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--atlas-entry-detail);
}

.emptyNote {
  padding: 8px 0 0 32px;
  font-size: 12.5px;
  color: var(--atlas-empty-note);
}

.statValueAccent {
  color: var(--atlas-ag-stat-accent);
}

.statValueWarning {
  color: var(--atlas-ag-stat-warning);
}

.statValueAccentHover {
  color: var(--atlas-ag-stat-accent-hover);
}

.statValueInk {
  color: var(--atlas-ag-stat-ink);
}

.agentList {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agentCard {
  border-radius: 20px;
  background: var(--atlas-ag-card-surface);
  overflow: hidden;
}

.agentTop {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 14px 15px 10px;
}

.agentAvatar {
  width: 34px;
  height: 34px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font: 600 11.5px var(--atlas-font-mono);
}

.agentIdentity {
  min-width: 0;
  flex: 1;
}

.agentName {
  font-size: 15px;
  font-weight: 700;
  color: var(--atlas-ag-name);
}

.agentState {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 1px;
  font-size: 12.5px;
  font-weight: 600;
}

.agentStateDot {
  width: 6px;
  height: 6px;
  box-sizing: border-box;
  border-radius: 50%;
  border: 0;
}

.agentStateDotHollow {
  border: 1.5px solid var(--atlas-ag-wait-dot-border);
}

.agentPacket {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-ag-packet);
}

.agentLine {
  padding: 0 15px 12px;
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--atlas-ag-line);
}

.agentBarBlock {
  padding: 0 15px 13px;
}

.agentBarTrack {
  height: 5px;
  border-radius: 999px;
  background: var(--atlas-ag-bar-track);
  overflow: hidden;
}

.agentBarFill {
  display: block;
  height: 100%;
  border-radius: 999px;
}

.agentProgressRow {
  display: flex;
  justify-content: space-between;
  margin-top: 7px;
  font: 500 11px var(--atlas-font-mono);
}

.agentDue {
  color: var(--atlas-ag-due);
}

.agentDueUrgent {
  color: var(--atlas-ag-due-urgent);
}

.agentLocks {
  padding: 10px 15px;
  border-top: 1px solid var(--atlas-ag-footer-border);
  font-size: 12px;
  color: var(--atlas-ag-locks);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weekCard {
  padding: 14px 15px;
  border-radius: 18px;
  background: var(--atlas-cost-card-surface);
}

.weekLabel {
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-week-label);
}

.weekBody {
  margin-top: 8px;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-week-body);
  text-wrap: pretty;
}

.weekWarning {
  color: var(--atlas-week-warning);
}

.weekMeta {
  margin-top: 7px;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-week-meta);
}

.weekCaption {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--atlas-week-caption);
  text-wrap: pretty;
}

.splitCard {
  margin-top: 10px;
  padding: 14px 15px;
  border-radius: 18px;
  background: var(--atlas-cost-card-surface);
}

.splitHead {
  display: flex;
  align-items: center;
  gap: 8px;
}

.splitLabel {
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-week-label);
}

.splitSegmented {
  display: flex;
  gap: 3px;
  margin-top: 10px;
  padding: 3px;
  border-radius: 11px;
  background: var(--atlas-split-track);
}

.splitSegButton {
  flex: 1;
  min-height: 34px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--atlas-split-seg-ink);
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
}

.splitSegSelected {
  background: var(--atlas-split-seg-selected-bg);
  color: var(--atlas-split-seg-selected-ink);
}

.splitBasisNote {
  margin-top: 9px;
  font-size: 12.5px;
  color: var(--atlas-split-basis-note);
}

.splitGroup {
  margin-top: 14px;
}

.splitGroupName {
  font: 600 9.5px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-split-group-name);
}

.splitBar {
  display: flex;
  gap: 2px;
  margin-top: 8px;
  height: 11px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--atlas-split-track);
}

.splitBarSegment {
  display: block;
}

.splitLegend {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 9px;
}

.splitLegendItem {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}

.splitLegendDot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 3px;
}

.splitLegendLabel {
  color: var(--atlas-split-legend-label);
}

.splitLegendPct {
  margin-left: auto;
  font-family: var(--atlas-font-mono);
  color: var(--atlas-split-legend-pct);
}

.splitLegendAbs {
  flex: none;
  width: 82px;
  text-align: right;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-split-legend-abs);
}

.splitCaveat {
  margin-top: 12px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--atlas-split-caveat);
  text-wrap: pretty;
}

.recordsHead {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin: 20px 2px 8px;
}

.recordsTitle {
  font-size: 16px;
  font-weight: 700;
  color: var(--atlas-records-row-ink);
}

.recordsCount {
  margin-left: auto;
  font-size: 12.5px;
  color: var(--atlas-records-row-muted);
}

.recordsList {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recordCard {
  border-radius: 18px;
  background: var(--atlas-records-card-surface);
  overflow: hidden;
}

.recordButton {
  display: block;
  width: 100%;
  padding: 13px 15px;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font: inherit;
}

.recordTopLine {
  display: flex;
  align-items: baseline;
  gap: 9px;
}

.recordAction {
  min-width: 0;
  font-size: 14.5px;
  font-weight: 600;
  text-wrap: pretty;
  color: var(--atlas-records-row-ink);
}

.recordOutcome {
  flex: none;
  margin-left: auto;
  padding: 2px 7px;
  border-radius: 6px;
  font: 600 9.5px var(--atlas-font-mono);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.recordsOutcomeBlocked {
  background: var(--atlas-records-tag-blocked-bg);
  color: var(--atlas-records-tag-blocked-ink);
}

.recordsOutcomeGood {
  background: var(--atlas-records-tag-good-bg);
  color: var(--atlas-records-tag-good-ink);
}

.recordsOutcomeNeutral {
  background: var(--atlas-records-tag-neutral-bg);
  color: var(--atlas-records-tag-neutral-ink);
}

.recordMeta {
  margin-top: 3px;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-records-row-faint);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recordStatLine {
  display: flex;
  gap: 14px;
  margin-top: 8px;
  font: 500 12px var(--atlas-font-mono);
  color: var(--atlas-records-row-ink);
}

.recordCostBilled {
  color: var(--atlas-records-row-ink);
}

.recordCostEst {
  color: var(--atlas-records-row-warning);
}

.recordCostNone {
  color: var(--atlas-records-row-muted);
}

.recordElapsed {
  margin-left: auto;
  color: var(--atlas-records-row-muted);
}

.recordDetail {
  border-top: 1px solid var(--atlas-records-detail-border);
  background: var(--atlas-records-detail-bg);
  padding: 12px 15px 14px;
  animation: recordsRise var(--atlas-records-rise-duration) var(--atlas-records-rise-easing);
}

@keyframes recordsRise {
  from {
    opacity: 0;
    transform: translateY(var(--atlas-records-rise-translate));
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.recordDetailGroup {
  margin-bottom: 12px;
}

.recordDetailGroupName {
  font: 600 9.5px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-records-detail-group-name);
}

.recordDetailRows {
  margin-top: 6px;
}

.recordDetailRow {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 5px 0;
  border-bottom: 1px solid var(--atlas-records-detail-row-divider);
  font-size: 13px;
}

.recordDetailLabel {
  min-width: 0;
  flex: 1;
  color: var(--atlas-records-detail-label);
}

.recordDetailValue {
  flex: none;
  font-family: var(--atlas-font-mono);
  font-weight: 600;
}

.recordDetailValueDefault {
  color: var(--atlas-records-detail-value-default);
}

.recordDetailValueOk {
  color: var(--atlas-records-detail-value-ok);
}

.recordDetailValueEst {
  color: var(--atlas-records-detail-value-est);
}

.recordDetailValueWarn {
  color: var(--atlas-records-detail-value-warn);
}

.recordDetailValueNa {
  color: var(--atlas-records-detail-value-na);
}

.recordDetailNote {
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--atlas-records-detail-note);
  text-wrap: pretty;
}
```

## `apps/atlas/src/shell/ActivityTab.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";
import { AGENTS, AGENTS_STATS } from "../agents/agents";
import { WEEKLY_WINDOW } from "../performance/weeklyWindow";
import { SPLIT, SPLIT_BASES } from "../performance/perfBreakdown";
import { PERF_RECORDS } from "../performance/perfRecords";
import { colors } from "../tokens";

const SPLIT_COLORS = [colors.accent, colors.review, colors.success, colors.borderDashed[2]];

/**
 * jsdom (like real browsers) silently re-serializes a raw inline hex
 * color to `rgb(...)` when read back via `.style.background` — so an
 * exact-string comparison against the original hex literal must
 * convert through the same normalization first, matching the
 * discipline this program's own `connectionState.ts` (G1) already
 * established for exactly this defect class.
 */
function hexToRgb(hex: string): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

afterEach(cleanup);

describe("ActivityTab", () => {
  it("renders the real page title and defaults to the History segment selected", () => {
    render(<ActivityTab />);
    expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
  });

  it("renders exactly three segments, in the reference file's own order", () => {
    render(<ActivityTab />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.map((b) => b.textContent)).toEqual(["History", "Agents", "Cost"]);
  });

  it("renders all 4 real HISTORY_STATS", () => {
    const { container } = render(<ActivityTab />);
    // Two real stats ("Corrections spent" and "Decisions recorded")
    // share the same real value ("1"), so each stat's label+value pair
    // is checked as one concatenated text run (each label is unique,
    // even though two values collide) rather than querying the value
    // alone document-wide.
    for (const stat of HISTORY_STATS) {
      const label = screen.getByText(stat.label);
      expect(label.textContent).toBe(`${stat.label}${stat.value}`);
    }
    expect(container.textContent).toContain(HISTORY_STATS[0].label);
  });

  it("renders all 10 real HISTORY_ENTRIES, in order, with their exact titles", () => {
    render(<ActivityTab />);
    const titles = screen.getAllByText(/./, { selector: "[class*='entryTitle']" });
    expect(titles.map((t) => t.textContent)).toEqual(HISTORY_ENTRIES.map((e) => e.title));
  });

  it("renders the real trailing empty-timeline note, reusing E6's own established constant", () => {
    render(<ActivityTab />);
    expect(screen.getByText(HISTORY_EMPTY_NOTE)).toBeInTheDocument();
  });

  it("renders no 'Open ... thread' button, unlike desktop History (the real mobile markup has no such control here)", () => {
    render(<ActivityTab />);
    expect(screen.queryByRole("button", { name: /open .* thread/i })).toBeNull();
  });

  it("tapping Cost switches the segmented control's own selection and renders the real weekly-window card", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));
    const current = screen.getAllByRole("button", { current: true });
    // Scoped to the outer segmented control only: the split card's own
    // segmented control (Cost/Tokens/Time) also uses `aria-current`-free
    // plain buttons here, but its own selected button carries no
    // `current` role attribute, so this stays unambiguous.
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Cost");

    expect(screen.getByText("openai weekly window")).toBeInTheDocument();
    // Real fixture fields, not the mobile mockup's own shorter,
    // compressed single line — see this file's own doc comment.
    expect(screen.getByText(WEEKLY_WINDOW.meta)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.caption)).toBeInTheDocument();
    expect(screen.getByText(`${WEEKLY_WINDOW.unattributedPercent} unattributed`)).toBeInTheDocument();
    expect(screen.getByText(`${WEEKLY_WINDOW.observedChangePercent}`)).toBeInTheDocument();
  });

  it("renders the real 'm1-a split' card defaulting to the Cost basis, with all real role and work parts", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    expect(screen.getByText("m1-a split")).toBeInTheDocument();
    expect(screen.getByText("by role")).toBeInTheDocument();
    expect(screen.getByText("by kind of work")).toBeInTheDocument();

    const data = SPLIT.cost;
    expect(screen.getByText(`share of ${data.note}`)).toBeInTheDocument();
    expect(screen.getByText(data.caveat)).toBeInTheDocument();
    for (const part of [...data.role, ...data.work]) {
      const label = screen.getByText(part.label);
      const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
      expect(within(item).getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(within(item).getByText(part.abs)).toBeInTheDocument();
    }
  });

  it("renders each real split part's own bar-segment width (with the real 0.6% floor) and legend-dot color by real index", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const group of [SPLIT.cost.role, SPLIT.cost.work]) {
      group.forEach((part, index) => {
        const label = screen.getByText(part.label);
        const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
        const dot = item.querySelector('[class*="splitLegendDot"]') as HTMLElement;
        expect(dot.style.background).toBe(hexToRgb(SPLIT_COLORS[index]));

        // Every real 0%-share part still renders a thin, visible sliver
        // (Math.max(pct, 0.6)), never a fully collapsed 0% bar segment.
        const group2 = item.closest('[class*="splitGroup"]') as HTMLElement;
        const bar = group2.querySelector('[class*="splitBar"]') as HTMLElement;
        const segment = bar.children[index] as HTMLElement;
        const expectedWidth = `${Math.max(part.pct, 0.6)}%`;
        expect(segment.style.width).toBe(expectedWidth);
        expect(segment.style.background).toBe(hexToRgb(SPLIT_COLORS[index]));
      });
    }
  });

  it("tapping Tokens or Time in the split card's own segmented control switches to that basis's real data", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const basis of SPLIT_BASES) {
      if (basis.key === "cost") continue;
      fireEvent.click(screen.getByRole("button", { name: basis.label }));
      const data = SPLIT[basis.key];
      expect(screen.getByText(`share of ${data.note}`)).toBeInTheDocument();
      expect(screen.getByText(data.caveat)).toBeInTheDocument();
      // The previous basis's own caveat must not linger.
      for (const other of SPLIT_BASES) {
        if (other.key === basis.key) continue;
        expect(screen.queryByText(SPLIT[other.key].caveat)).toBeNull();
      }
      // Every real role/work part for this basis, not just the note/caveat
      // strings — proves the switch re-derives the whole group, not just
      // the two summary lines.
      for (const part of [...data.role, ...data.work]) {
        const label = screen.getByText(part.label);
        const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
        expect(within(item).getByText(`${part.pct}%`)).toBeInTheDocument();
        expect(within(item).getByText(part.abs)).toBeInTheDocument();
      }
    }
  });

  it("(F3D) renders the real 'Per action' header with a derived, not hand-typed, record count", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    expect(screen.getByText("Per action")).toBeInTheDocument();
    expect(screen.getByText(`${PERF_RECORDS.length} records`)).toBeInTheDocument();
  });

  it("(F3D) renders every real PERF_RECORDS card, closed by default, with its exact action/outcome/meta/stat-line text", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const card = action.closest('[class*="recordCard"]') as HTMLElement;
      expect(within(card).getByText(record.outcome)).toBeInTheDocument();
      expect(
        within(card).getByText(`${record.packet} · ${record.who} · ${record.model}`),
      ).toBeInTheDocument();
      expect(within(card).getByText(record.tokens)).toBeInTheDocument();
      expect(within(card).getByText(record.cost)).toBeInTheDocument();
      expect(within(card).getByText(record.elapsed)).toBeInTheDocument();
      // Closed by default: no detail group name or note text is present.
      for (const group of record.groups) {
        expect(within(card).queryByText(group.name)).toBeNull();
      }
      expect(within(card).queryByText(record.note)).toBeNull();
    }
  });

  it("(F3D) each real record's own outcome tag and cost carry the exact real token color class, transcribed from PerfRecordsList's own mapping", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    // These colors are applied via a CSS-module class (matching
    // PerfRecordsList.tsx's own established convention for this exact
    // outcome/cost mapping), not an inline style — so, matching that
    // file's own test convention, this asserts class membership, not
    // `.style`, which jsdom never populates for CSS-module rules.
    const outcomeClassName: Record<string, string> = {
      blocked: "recordsOutcomeBlocked",
      approved: "recordsOutcomeGood",
      passed: "recordsOutcomeGood",
      complete: "recordsOutcomeNeutral",
    };
    const costClassName: Record<string, string> = {
      billed: "recordCostBilled",
      est: "recordCostEst",
      none: "recordCostNone",
    };

    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const card = action.closest('[class*="recordCard"]') as HTMLElement;
      const outcome = within(card).getByText(record.outcome);
      expect(outcome.className).toContain(outcomeClassName[record.outcome]);

      const cost = within(card).getByText(record.cost);
      expect(cost.className).toContain(costClassName[record.costKind]);
    }
  });

  it("(F3D) clicking a record's own button opens its real detail groups/rows/note, and closes whichever other record was open (single accordion state)", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    const first = PERF_RECORDS[0];
    const second = PERF_RECORDS[1];

    fireEvent.click(screen.getByText(first.action));
    const firstCard = screen.getByText(first.action).closest('[class*="recordCard"]') as HTMLElement;
    expect(first.groups).toHaveLength(3);
    for (const group of first.groups) {
      // Some real records repeat a value string across two rows within
      // the same open card (e.g. p1's "unavailable" appears twice, and
      // p1's own elapsed "0.9s" repeats between the closed button row
      // and its own detail row) — so, matching PerfRecordsList.test.tsx's
      // own established pattern, this scopes to each group's own name
      // node's `parentElement` and only asserts row *labels* here
      // (always unique per group), not row values.
      const groupNode = screen.getByText(group.name).parentElement as HTMLElement;
      const groupScope = within(groupNode);
      for (const row of group.rows) {
        expect(groupScope.getByText(row.label)).toBeInTheDocument();
      }
    }
    expect(within(firstCard).getByText(first.note)).toBeInTheDocument();

    // Opening the second record closes the first — a single shared
    // `openId`, not one independent boolean per record.
    fireEvent.click(screen.getByText(second.action));
    const secondCard = screen.getByText(second.action).closest('[class*="recordCard"]') as HTMLElement;
    expect(within(secondCard).getByText(second.note)).toBeInTheDocument();
    expect(within(firstCard).queryByText(first.note)).toBeNull();

    // Clicking the open record again closes it.
    fireEvent.click(screen.getByText(second.action));
    expect(within(secondCard).queryByText(second.note)).toBeNull();
  });

  it("(F3D) each real detail row's own value carries the exact real token color class for its PerfDetailKind, transcribed from PerfRecordsList's own mapping", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    const detailValueClassName: Record<string, string> = {
      "": "recordDetailValueDefault",
      est: "recordDetailValueEst",
      ok: "recordDetailValueOk",
      warn: "recordDetailValueWarn",
      na: "recordDetailValueNa",
    };

    // Every kind must appear at least once across the real fixture, or
    // this test would pass vacuously without ever exercising a branch.
    const seenKinds = new Set<string>();

    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const card = action.closest('[class*="recordCard"]') as HTMLElement;
      fireEvent.click(action);
      for (const group of record.groups) {
        for (const row of group.rows) {
          seenKinds.add(row.kind);
          // Scoped to this record's own card first (its row label, e.g.
          // "Cost", would otherwise collide with the outer segmented
          // control's own "Cost" tab and the split card's own "Cost"
          // basis button — the exact latent test-scoping trap the F3C
          // Decision Fidelity review pre-disclosed for this slice), then
          // to the row's own label -> parentElement, matching
          // PerfRecordsList.test.tsx's own established pattern (some
          // real records also repeat a value string across two rows).
          const rowNode = within(card).getByText(row.label).parentElement as HTMLElement;
          const value = within(rowNode).getByText(row.value);
          expect(value.className).toContain(detailValueClassName[row.kind]);
        }
      }
      fireEvent.click(action);
    }

    expect(seenKinds.size).toBeGreaterThan(1);
  });

  it("tapping Agents switches the segmented control's own selection and renders the real AGENTS_STATS", () => {
    const { container } = render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Agents");

    // Every real AGENTS_STATS label is unique, so a bare label lookup
    // is unambiguous here (unlike HISTORY_STATS' shared "1" value).
    for (const stat of AGENTS_STATS) {
      const label = screen.getByText(stat.label);
      expect(label.textContent).toBe(`${stat.label}${stat.value}`);
    }
    expect(container.textContent).toContain(AGENTS_STATS[0].label);
  });

  it("renders all 4 real AGENTS cards with their exact name, state, and line", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      // "Coordinator" is both this real agent's name and its own role —
      // scope each assertion to that one card, found via its unique
      // real `line` text, to avoid an ambiguous document-wide query.
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      expect(within(card).getByText(agent.name)).toBeInTheDocument();
      expect(within(card).getByText(agent.state)).toBeInTheDocument();
      expect(within(card).getByText(agent.packet)).toBeInTheDocument();
      expect(within(card).getByText(agent.locks)).toBeInTheDocument();
    }
  });

  it("renders each real agent's exact progress-bar width, progress label, and due label with the correct urgent styling", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      const fill = card.querySelector('[class*="agentBarFill"]') as HTMLElement;
      expect(fill.style.width).toBe(agent.pct);

      const due = within(card).getByText(agent.due);
      expect(within(card).getByText(agent.progress)).toBeInTheDocument();
      // Only Coordinator's real fixture entry has `urgent: true` — every
      // other real agent must render the non-urgent due class instead.
      expect(due.className).toContain(agent.urgent ? "agentDueUrgent" : "agentDue");
      if (!agent.urgent) {
        expect(due.className).not.toContain("agentDueUrgent");
      }
    }
  });

  it("renders a hollow state dot only for Sol (the real fixture's only 'wait' styleKey), filled for the other 3", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      const dot = card.querySelector('[class*="agentStateDot"]') as HTMLElement;
      const isWait = agent.styleKey === "wait";
      expect(dot.className.includes("agentStateDotHollow")).toBe(isWait);
      if (isWait) {
        expect(dot.style.background).toBe("transparent");
      } else {
        expect(dot.style.background).not.toBe("");
        expect(dot.style.background).not.toBe("transparent");
      }
    }
  });

  it("renders no 'Open thread' button on the mobile Agents cards (the real mobile markup has no such control here)", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    expect(screen.queryByRole("button", { name: /open thread/i })).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ActivityTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (`/tmp/maestro-m2-f3d-records`, branch
`architecture/m2-f3d-per-action-records`, base `57b788f`) and run
through the real frontend toolchain from `apps/atlas` (`npm install`,
then each script below) before this packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **24/24 test files, 201/201 tests
  passed** (21 in `ActivityTab.test.tsx`, up from 16; zero regressions
  in the other 23 files, including `PerfRecordsList.test.tsx`, which
  this slice does not modify).
- `npm run build` (`vite build`) — clean, `45 modules transformed`, no
  warnings.
- Every declared `--atlas-*` custom property, and every CSS class
  declared in `ActivityTab.module.css`, was cross-checked
  programmatically against `ActivityTab.tsx`'s own references — zero
  orphans in either direction.

Two real test-authoring corrections were made during this
verification pass, both caught by the toolchain itself before this
packet was finalized (not disclosed-but-unfixed, since they were free
to fix immediately):
1. Two color-mapping tests initially asserted `.style.background`/
   `.style.color`, which jsdom never populates for a CSS-module class
   (as opposed to an inline `style` prop) — corrected to assert
   `className` membership, matching `PerfRecordsList.test.tsx`'s own
   established convention for this exact same class-based color
   pattern.
2. Two other tests initially queried `row.value`/`row.label` text
   unscoped or card-wide — several real `PERF_RECORDS` rows repeat a
   value string within the same open card (e.g. p1's "unavailable"
   appears twice; p1's own elapsed "0.9s" repeats between the closed
   button row and its own detail row), and one row's label ("Cost")
   collides with the outer segmented control's own "Cost" tab and the
   split card's own basis-toggle "Cost" button — exactly the latent
   test-scoping trap the F3C Decision Fidelity review pre-disclosed
   for this slice. Corrected to scope every such query to the specific
   record's own card, and then to the specific row's own label ->
   `parentElement`, matching `PerfRecordsList.test.tsx`'s own
   established scoping pattern.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** the Activity tab's Cost segment renders a
   real, exhaustive "Per action" records list (reusing E2/E2B's own
   `PERF_RECORDS` fixture, click-to-expand accordion, real per-row
   color coding), completing roadmap item 35 (F3), with zero backend
   change and zero regression to any of the 23 other existing test
   files.
2. **Operating and threat model:** none — pure frontend rendering of
   already-real, already-reviewed fixture data; no network call, no
   command dispatch.
3. **Explicit exclusions:** any modification to
   `PerfRecordsList.tsx`/`perfRecords.ts` themselves (both stay exactly
   as already reviewed and merged, read-only imports); the desktop
   5-column grid layout (mobile uses its own single-column stacked
   card, per the real mockup).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering + accordion-state component — every rendered surface,
   every color-class mapping, and the accordion's open/close/exclusive
   behavior are exercised by a React Testing Library render/interaction
   test; no browser-based visual verification was performed (tooling
   limitation already disclosed for every prior M2 slice this session,
   same root cause) — the mockup source itself is this session's own
   cached copy, not part of this repository, also already-disclosed
   sourcing.
5. **Acceptance proof:** 24/24 test files, 201/201 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 3 modified files, all within
   `apps/atlas/src/shell`; zero backend files; no new third-party
   dependency; `apps/atlas/src/performance/*` read-only, never
   modified.
7. **Proportionality ceiling:** two new components
   (`RecordsList`/`RecordCard`), reusing an already-real fixture and an
   already-reviewed color mapping verbatim — no new fixture data
   invented, no new design tokens invented beyond the disclosed
   `colors.ink` application already covered by Design rationale #3.
8. **Stop and escalation rule:** modifying `PerfRecordsList.tsx` or
   `perfRecords.ts` to better fit this slice, or building any
   interaction beyond click-to-expand (e.g. sort/filter controls not
   present in the real mockup), is explicitly out of scope — no such
   control exists in `Atlas Mobile.dc.html`'s own real markup, and
   none should be silently added.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F3D-PER-ACTION-RECORDS-01` |
| `phase` | `MergeReady` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f3d-per-action-records.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
