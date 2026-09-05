# M2 Wave E — Performance Breakdown Card — Candidate 01

**Slice ID:** `MB-SLICE-M2-E3-PERF-BREAKDOWN-CARD-01`
**Status:** `Draft — Targeted correction applied (color discrepancy table missing the group border-bottom row; row count corrected 19→20), pending Targeted Decision Fidelity Verification`
**Base:** `7f9474e` (full: `7f9474e27e4fb84053d6bf9b2e6946ad270ecd4a`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 28, *"E3 — Performance: breakdown split card (by role / by
kind, cost/tokens/time segmented control)."* A new, standalone
`PerfBreakdownCard` renders the reference file's real `"m1-a
breakdown"` card in full: the header (label, current basis's real
`note`, and a real cost/tokens/time segmented control), two real
groups ("by role", "by kind of work" — each a stacked bar plus legend),
and the current basis's own real caveat. No wiring into
`DesktopShell`/`App.tsx`.

**This is the first Wave E slice with a genuine multi-value toggle**
(`useState<SplitBasisKey>`, three real values, not the boolean
open/closed state E2B introduced) — clicking "Cost"/"Tokens"/"Time"
really switches which of the reference file's 3 real `SPLIT` bases
drives both groups' bars, legends, note, and caveat.

**Real-vs-fictional persona adaptation, disclosed:** the reference
file's own `SPLIT.cost.role` array has a fourth entry, `['Architect
agent', 0, 'pending']` — the fictional M4-only persona that must never
render as existing in M2 (this program's own Wave C precedent). Neither
`SPLIT.tokens.role` nor `SPLIT.time.role` has this problem — their own
real fourth entries are `Local Qwen` then `Coordinator`, no fictional
persona at all. This slice makes `cost.role` match that same
already-real pattern: `Local Qwen` (0%, `'local compute'` — the exact
cost-kind text `PERF_RECORDS`'s own `p5` already uses for this same
real actor) replaces `Architect agent`, and `cost`'s own real `caveat`
sentence is rewritten to state both real reasons for a 0% role
(Coordinator's actions are not worker attempts; Local Qwen's cost is
local compute, never billed hosted dollars) rather than the reference's
own sentence, which named the fictional persona directly.

## Source quote

`Atlas Explorations.dc.html`'s real markup for the "m1-a breakdown"
card, verbatim:

```html
<div style="margin-top:14px;border:1px solid #E7E1EE;border-radius:14px;background:#fff;overflow:hidden">
  <div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:12px 15px;border-bottom:1px solid #EEEAF2">
    <span style="font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#6C6376">m1-a breakdown</span>
    <span style="min-width:0;flex:1;font-size:12.5px;color:#8E8299">share of {{ split.basisNote }}</span>
    <div style="flex:none;display:flex;gap:3px;padding:3px;border-radius:9px;background:#F4F1F8">
      <sc-for list="{{ split.bases }}" as="b" hint-placeholder-count="3">
      <button onClick="{{ b.onPick }}" style="height:26px;padding:0 11px;border:0;border-radius:7px;background:{{ b.bg }};color:{{ b.color }};cursor:pointer;font-size:12.5px;font-weight:600" style-hover="color:#221C29">{{ b.label }}</button>
      </sc-for>
    </div>
  </div>
  <sc-for list="{{ split.groups }}" as="g" hint-placeholder-count="2">
  <div style="padding:14px 15px;border-bottom:1px solid #F3F0F6">
    <div style="font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#A79BB4">{{ g.name }}</div>
    <div style="display:flex;gap:2px;margin-top:9px;height:12px;border-radius:999px;overflow:hidden;background:#F4F1F8">
      <sc-for list="{{ g.parts }}" as="p" hint-placeholder-count="4">
      <span title="{{ p.title }}" style="width:{{ p.w }};background:{{ p.color }}"></span>
      </sc-for>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px 20px;margin-top:11px">
      <sc-for list="{{ g.parts }}" as="p" hint-placeholder-count="4">
      <div style="display:flex;align-items:baseline;gap:8px;font-size:13px"><span style="width:8px;height:8px;flex:none;border-radius:3px;background:{{ p.color }}"></span><span style="color:#6C6376">{{ p.label }}</span><b style="font-family:'IBM Plex Mono',monospace">{{ p.pct }}</b><span style="font:500 11.5px 'IBM Plex Mono',monospace;color:#A79BB4">{{ p.abs }}</span></div>
      </sc-for>
    </div>
  </div>
  </sc-for>
  <div style="padding:11px 15px;font-size:12.5px;line-height:1.55;color:#8E8299;text-wrap:pretty">{{ split.caveat }}</div>
</div>
```

Real per-basis derivation logic (verbatim) — `b.bg`/`b.color` for the
segmented buttons and `bar()`'s width/color derivation:

```js
split: (() => {
  const key = s.basis || 'cost', d = SPLIT[key];
  const bar = rows => rows.map(([label, pct, abs], i) => ({ label, pct: pct + '%', abs, w: Math.max(pct, 0.6) + '%',
    color: SPLIT_COLORS[i], title: label + ' · ' + pct + '% · ' + abs }));
  return { basisNote: d.note, caveat: d.caveat,
    bases: [['cost', 'Cost'], ['tokens', 'Tokens'], ['time', 'Time']].map(([k, label]) => ({ label,
      bg: key === k ? '#fff' : 'transparent', color: key === k ? '#221C29' : '#8E8299',
      onPick: () => this.setState({ basis: k }) })),
    groups: [{ name: 'by role', parts: bar(d.role) }, { name: 'by kind of work', parts: bar(d.work) }] };
})(),
```

`s.basis` defaults to `'cost'` (`s.basis || 'cost'`) — exactly one
basis is ever selected, transcribed as this slice's `useState<SplitBasisKey>("cost")`.
`bar()`'s `Math.max(pct, 0.6) + '%'` guarantees even a real 0%-share
part still renders a thin, visible sliver.

The real `SPLIT` object and `SPLIT_COLORS` array (verbatim, before this
slice's one disclosed persona adaptation):

```js
const SPLIT = {
  cost: { note: 'billed and estimated hosted cost · $2.79', unit: '$',
    role: [['Implementor', 81, '$2.27'], ['Reviewer', 19, '$0.52'], ['Coordinator', 0, 'not billed'], ['Architect agent', 0, 'pending']],
    work: [['Coding', 67, '$1.86'], ['Reading & planning', 15, '$0.41'], ['Review', 19, '$0.52'], ['Preflight & records', 0, 'not billed']],
    caveat: 'Coordinator and Architect actions ran inside worker attempts already counted, so they carry no separate billed amount. $0.52 of this total is an estimate, not a billed figure.' },
  tokens: { note: 'total attempt tokens · 218,500', unit: 'tok',
    role: [['Implementor', 81, '177,600'], ['Reviewer', 14, '31,200'], ['Local Qwen', 5, '9,700 est.'], ['Coordinator', 0, 'unavailable']],
    work: [['Coding', 51, '112,300'], ['Reading & planning', 21, '46,900'], ['Review', 14, '31,200'], ['Preflight & checks', 13, '28,100']],
    caveat: 'Hosted and local tokens are shown in one bar for shape only — they are different units of work and are never summed into an allowance figure.' },
  time: { note: 'wall time across attempts · 52m 36s', unit: 'time',
    role: [['Implementor', 78, '41m 04s'], ['Reviewer', 13, '6m 40s'], ['Local Qwen', 9, '4m 52s'], ['Coordinator', 0, 'under 1m']],
    work: [['Coding', 73, '38m 11s'], ['Reading & planning', 4, '2m 04s'], ['Review', 13, '6m 40s'], ['Local checks', 10, '5m 41s']],
    caveat: 'This is attempt time, not elapsed milestone time. The 41 minutes A.2 spent blocked waiting on a ruling is not attributed to any role.' },
};
const SPLIT_COLORS = ['#5B34E8', '#D08A63', '#2E9B72', '#B9AFC4'];
```

**Note the `unit` field is never used by any real rendering path**
(`d.unit` appears nowhere in the `split` derivation function or the
markup above) — this slice's own `SplitBasisData` type intentionally
omits it, matching the "implementation boundary" discipline: only
render real, consumed fields.

## Color discrepancy table — every value is a real, existing B2 token; zero disclosed literals

| Reference value | `colors.ts` match | Verdict |
|---|---|---|
| card border `#E7E1EE` | `colors.border` | real token |
| card surface `#fff` | `colors.surface` (`#FFFFFF`) | real token |
| header border-bottom `#EEEAF2` | `colors.borderDivider[0]` | real token |
| header label `#6C6376` | `colors.inkSecondary` | real token |
| basis-note text `#8E8299` | `colors.inkMuted` | real token |
| segmented track bg `#F4F1F8` | `colors.segmentedTrack[1]` | real token |
| segmented button selected bg `#fff` | `colors.segmentedSelected` (`#FFFFFF`) | real token |
| segmented button selected/hover text `#221C29` | `colors.ink` | real token |
| segmented button unselected text `#8E8299` | `colors.inkMuted` | real token |
| group-name text `#A79BB4` | `colors.inkFaint` | real token |
| group border-bottom `#F3F0F6` | `colors.borderDivider[1]` | real token |
| bar track bg `#F4F1F8` | `colors.segmentedTrack[1]` (same token, reused) | real token |
| legend label `#6C6376` | `colors.inkSecondary` | real token |
| legend pct (inherited default, made explicit — see Guards) `#221C29` | `colors.ink` | real token |
| legend abs `#A79BB4` | `colors.inkFaint` | real token |
| caveat text `#8E8299` | `colors.inkMuted` | real token |
| `SPLIT_COLORS[0]` `#5B34E8` | `colors.accent` | real token |
| `SPLIT_COLORS[1]` `#D08A63` | `colors.review` | real token |
| `SPLIT_COLORS[2]` `#2E9B72` | `colors.success` | real token |
| `SPLIT_COLORS[3]` `#B9AFC4` | `colors.borderDashed[2]` | real token |

**All 20 real, existing B2 tokens — zero disclosed literals**, matching
E1/E1B/E2/E2B's own precedent (unlike Gate/History, which needed
disclosures).

## Guards

1. Legend `pct`'s `<b>` element in the reference markup carries no
   explicit `color` (`<b style="font-family:'IBM Plex Mono',monospace">`)
   — this slice makes that inherited default explicit via
   `colors.ink`, matching E2's own established precedent for
   `PerfRecordsList`'s `.action` span (also unstyled-color in the
   reference, also made explicit via `colors.ink` there).
2. This slice modifies zero already-merged files — 4 new files only,
   no wiring into `DesktopShell`/`App.tsx`.
3. The reference file's `d.unit` field is never consumed by any real
   rendering path; this slice's `SplitBasisData` type omits it rather
   than carrying an unused field forward.
4. The persona substitution (`Architect agent` → `Local Qwen`) touches
   only `cost.role`'s fourth entry and `cost`'s own `caveat` sentence —
   `tokens.role`/`time.role`/their own caveats are transcribed
   completely verbatim, since neither needed adaptation.
5. `desktopButtonPx`/`segmentedPillPx` shape tokens are not
   cross-checked or disclosed here — no prior Wave C/E slice tokenizes
   border-radius values (every prior slice's CSS radius is a plain
   literal pixel value matching the reference directly, e.g. E2's own
   `border-radius: 14px`/`6px`), so this slice's `9px`/`7px`/`999px`
   radii follow that same established convention, not a new one.

## `apps/atlas/src/performance/perfBreakdown.ts` (new)

```ts
/**
 * Transcribed from `Atlas Explorations.dc.html`'s real `SPLIT` object
 * (the reference file's own `SPLIT_COLORS` array is real B2 tokens —
 * see `PerfBreakdownCard.tsx`'s own disclosure) — pure reporting
 * content, with one real
 * adaptation disclosed here and in the packet: the reference file's
 * own `cost.role` array includes a fourth entry, `['Architect agent',
 * 0, 'pending']` — the fictional M4-only persona that must never be
 * rendered as existing in M2 (see this program's own Wave C
 * precedent). Unlike `cost.role`, the reference file's `tokens.role`
 * and `time.role` arrays already use only real M1 actors for their own
 * fourth entry (`Local Qwen`, then `Coordinator`) — no fictional
 * persona there. This slice makes `cost.role` match that same real,
 * already-established pattern: `Local Qwen` (0%, `'local compute'` —
 * the exact real cost-kind text `PERF_RECORDS`'s own `p5` already uses
 * for the same real actor's cost) replaces `Architect agent`, and the
 * `cost` basis's own real `caveat` sentence is rewritten to state both
 * real reasons for a 0% role (Coordinator's actions are not worker
 * attempts; Local Qwen's cost is local compute, never billed hosted
 * dollars) rather than the reference's own sentence, which named the
 * fictional persona directly ("Coordinator and Architect actions ran
 * inside worker attempts already counted...").
 */
export type SplitBasisKey = "cost" | "tokens" | "time";

export interface SplitPart {
  label: string;
  pct: number;
  abs: string;
}

export interface SplitBasisData {
  note: string;
  role: SplitPart[];
  work: SplitPart[];
  caveat: string;
}

export const SPLIT: Record<SplitBasisKey, SplitBasisData> = {
  cost: {
    note: "billed and estimated hosted cost · $2.79",
    role: [
      { label: "Implementor", pct: 81, abs: "$2.27" },
      { label: "Reviewer", pct: 19, abs: "$0.52" },
      { label: "Coordinator", pct: 0, abs: "not billed" },
      { label: "Local Qwen", pct: 0, abs: "local compute" },
    ],
    work: [
      { label: "Coding", pct: 67, abs: "$1.86" },
      { label: "Reading & planning", pct: 15, abs: "$0.41" },
      { label: "Review", pct: 19, abs: "$0.52" },
      { label: "Preflight & records", pct: 0, abs: "not billed" },
    ],
    caveat:
      "Coordinator actions are not worker attempts, so they carry no separate billed amount; Local Qwen's cost is local compute, never billed hosted dollars. $0.52 of this total is an estimate, not a billed figure.",
  },
  tokens: {
    note: "total attempt tokens · 218,500",
    role: [
      { label: "Implementor", pct: 81, abs: "177,600" },
      { label: "Reviewer", pct: 14, abs: "31,200" },
      { label: "Local Qwen", pct: 5, abs: "9,700 est." },
      { label: "Coordinator", pct: 0, abs: "unavailable" },
    ],
    work: [
      { label: "Coding", pct: 51, abs: "112,300" },
      { label: "Reading & planning", pct: 21, abs: "46,900" },
      { label: "Review", pct: 14, abs: "31,200" },
      { label: "Preflight & checks", pct: 13, abs: "28,100" },
    ],
    caveat:
      "Hosted and local tokens are shown in one bar for shape only — they are different units of work and are never summed into an allowance figure.",
  },
  time: {
    note: "wall time across attempts · 52m 36s",
    role: [
      { label: "Implementor", pct: 78, abs: "41m 04s" },
      { label: "Reviewer", pct: 13, abs: "6m 40s" },
      { label: "Local Qwen", pct: 9, abs: "4m 52s" },
      { label: "Coordinator", pct: 0, abs: "under 1m" },
    ],
    work: [
      { label: "Coding", pct: 73, abs: "38m 11s" },
      { label: "Reading & planning", pct: 4, abs: "2m 04s" },
      { label: "Review", pct: 13, abs: "6m 40s" },
      { label: "Local checks", pct: 10, abs: "5m 41s" },
    ],
    caveat:
      "This is attempt time, not elapsed milestone time. The 41 minutes A.2 spent blocked waiting on a ruling is not attributed to any role.",
  },
};

export const SPLIT_BASES: { key: SplitBasisKey; label: string }[] = [
  { key: "cost", label: "Cost" },
  { key: "tokens", label: "Tokens" },
  { key: "time", label: "Time" },
];
```

## `apps/atlas/src/performance/PerfBreakdownCard.tsx` (new)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { SPLIT, SPLIT_BASES, type SplitBasisKey, type SplitPart } from "./perfBreakdown";
import styles from "./PerfBreakdownCard.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal. The
 * reference file's real `SPLIT_COLORS` array (`['#5B34E8', '#D08A63',
 * '#2E9B72', '#B9AFC4']`) is exactly `[colors.accent, colors.review,
 * colors.success, colors.borderDashed[2]]`, checked directly against
 * `colors.ts` — four real, different token properties, not a
 * coincidence. The segmented control is the first real consumer of
 * `colors.segmentedTrack`/`colors.segmentedSelected` and
 * `PerfBreakdownCard` renders the first true multi-value toggle
 * (`useState<SplitBasisKey>`) in this codebase, matching the reference
 * file's own `s.basis` state field exactly (one real basis selected at
 * a time, defaulting to `'cost'`).
 */
const SEGMENT_CLASS = [styles.segColor0, styles.segColor1, styles.segColor2, styles.segColor3];

const SHELL_VARS = {
  "--atlas-brk-card-border": colors.border,
  "--atlas-brk-card-surface": colors.surface,
  "--atlas-brk-header-border": colors.borderDivider[0],
  "--atlas-brk-header-label": colors.inkSecondary,
  "--atlas-brk-basis-note": colors.inkMuted,
  "--atlas-brk-track-bg": colors.segmentedTrack[1],
  "--atlas-brk-seg-selected-bg": colors.segmentedSelected,
  "--atlas-brk-seg-selected-ink": colors.ink,
  "--atlas-brk-seg-unselected-ink": colors.inkMuted,
  "--atlas-brk-group-border": colors.borderDivider[1],
  "--atlas-brk-group-name": colors.inkFaint,
  "--atlas-brk-legend-label": colors.inkSecondary,
  "--atlas-brk-legend-pct": colors.ink,
  "--atlas-brk-legend-abs": colors.inkFaint,
  "--atlas-brk-caveat": colors.inkMuted,
  "--atlas-brk-seg-color-0": colors.accent,
  "--atlas-brk-seg-color-1": colors.review,
  "--atlas-brk-seg-color-2": colors.success,
  "--atlas-brk-seg-color-3": colors.borderDashed[2],
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * Transcribed verbatim from the reference file's own bar-width
 * derivation (`w: Math.max(pct, 0.6) + '%'`) — a 0%-share part still
 * renders a thin, visible sliver rather than vanishing entirely.
 */
function barWidth(pct: number): string {
  return `${Math.max(pct, 0.6)}%`;
}

function Bar({ parts }: { parts: SplitPart[] }) {
  return (
    <div className={styles.bar}>
      {parts.map((part, index) => (
        <span
          key={part.label}
          title={`${part.label} · ${part.pct}% · ${part.abs}`}
          className={`${styles.barSegment} ${SEGMENT_CLASS[index]}`}
          style={{ width: barWidth(part.pct) }}
        />
      ))}
    </div>
  );
}

function Legend({ parts }: { parts: SplitPart[] }) {
  return (
    <div className={styles.legend}>
      {parts.map((part, index) => (
        <div key={part.label} className={styles.legendItem}>
          <span className={`${styles.legendDot} ${SEGMENT_CLASS[index]}`} />
          <span className={styles.legendLabel}>{part.label}</span>
          <b className={styles.legendPct}>{part.pct}%</b>
          <span className={styles.legendAbs}>{part.abs}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Renders the real "m1-a breakdown" card: a real cost/tokens/time
 * segmented control (one real basis selected at a time) driving two
 * real stacked-bar-plus-legend groups ("by role", "by kind of work")
 * and the current basis's own real caveat. `cost.role`'s fourth entry
 * substitutes the fictional `Architect agent` persona with the real
 * `Local Qwen` actor — see `perfBreakdown.ts`'s own disclosure.
 */
export function PerfBreakdownCard() {
  const [basis, setBasis] = useState<SplitBasisKey>("cost");
  const data = SPLIT[basis];

  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.header}>
        <span className={styles.headerLabel}>m1-a breakdown</span>
        <span className={styles.basisNote}>share of {data.note}</span>
        <div className={styles.segmented}>
          {SPLIT_BASES.map((b) => (
            <button
              key={b.key}
              type="button"
              className={`${styles.segButton} ${basis === b.key ? styles.segSelected : ""}`}
              onClick={() => setBasis(b.key)}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>
      <div className={styles.group}>
        <div className={styles.groupName}>by role</div>
        <Bar parts={data.role} />
        <Legend parts={data.role} />
      </div>
      <div className={styles.group}>
        <div className={styles.groupName}>by kind of work</div>
        <Bar parts={data.work} />
        <Legend parts={data.work} />
      </div>
      <div className={styles.caveat}>{data.caveat}</div>
    </div>
  );
}

export default PerfBreakdownCard;
```

## `apps/atlas/src/performance/PerfBreakdownCard.module.css` (new)

```css
.card {
  margin-top: 14px;
  border: 1px solid var(--atlas-brk-card-border);
  border-radius: 14px;
  background: var(--atlas-brk-card-surface);
  overflow: hidden;
}

.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  border-bottom: 1px solid var(--atlas-brk-header-border);
}

.headerLabel {
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-brk-header-label);
}

.basisNote {
  min-width: 0;
  flex: 1;
  font-size: 12.5px;
  color: var(--atlas-brk-basis-note);
}

.segmented {
  flex: none;
  display: flex;
  gap: 3px;
  padding: 3px;
  border-radius: 9px;
  background: var(--atlas-brk-track-bg);
}

.segButton {
  height: 26px;
  padding: 0 11px;
  border: 0;
  border-radius: 7px;
  background: transparent;
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--atlas-brk-seg-unselected-ink);
}

.segButton:hover {
  color: var(--atlas-brk-seg-selected-ink);
}

.segSelected {
  background: var(--atlas-brk-seg-selected-bg);
  color: var(--atlas-brk-seg-selected-ink);
}

.group {
  padding: 14px 15px;
  border-bottom: 1px solid var(--atlas-brk-group-border);
}

.groupName {
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-brk-group-name);
}

.bar {
  display: flex;
  gap: 2px;
  margin-top: 9px;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--atlas-brk-track-bg);
}

.barSegment {
  display: block;
}

.segColor0 {
  background: var(--atlas-brk-seg-color-0);
}

.segColor1 {
  background: var(--atlas-brk-seg-color-1);
}

.segColor2 {
  background: var(--atlas-brk-seg-color-2);
}

.segColor3 {
  background: var(--atlas-brk-seg-color-3);
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  margin-top: 11px;
}

.legendItem {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}

.legendDot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 3px;
}

.legendLabel {
  color: var(--atlas-brk-legend-label);
}

.legendPct {
  font-family: var(--atlas-font-mono);
  color: var(--atlas-brk-legend-pct);
}

.legendAbs {
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-brk-legend-abs);
}

.caveat {
  padding: 11px 15px;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--atlas-brk-caveat);
  text-wrap: pretty;
}
```

## `apps/atlas/src/performance/PerfBreakdownCard.test.tsx` (new)

```tsx
import { render, screen, cleanup, within, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PerfBreakdownCard } from "./PerfBreakdownCard";
import { SPLIT } from "./perfBreakdown";

afterEach(cleanup);

// Every role/work label is unique on screen for a given basis (actor
// names never collide with work-kind names), but pct/abs VALUES do
// repeat across the two groups (e.g. cost's Reviewer role and Review
// work both show "$0.52"/"19%") — so every check below is scoped to
// the specific row found via its own unique label, not a bare,
// ambiguous `getByText` on the shared value.
function legendRow(label: string): HTMLElement {
  return screen.getByText(label).closest("div") as HTMLElement;
}

describe("PerfBreakdownCard", () => {
  it("defaults to the real 'cost' basis: header note, all 4 real role rows, all 4 real work rows, and the real caveat", () => {
    render(<PerfBreakdownCard />);
    expect(screen.getByText(`share of ${SPLIT.cost.note}`)).toBeInTheDocument();
    for (const part of [...SPLIT.cost.role, ...SPLIT.cost.work]) {
      const row = within(legendRow(part.label));
      expect(row.getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(row.getByText(part.abs)).toBeInTheDocument();
    }
    expect(screen.getByText(SPLIT.cost.caveat)).toBeInTheDocument();
  });

  it("substitutes the fictional 'Architect agent' persona with the real Local Qwen actor in cost.role, with no fictional persona anywhere", () => {
    render(<PerfBreakdownCard />);
    expect(screen.queryByText("Architect agent")).toBeNull();
    const localQwenRow = within(legendRow("Local Qwen"));
    expect(localQwenRow.getByText("0%")).toBeInTheDocument();
    expect(localQwenRow.getByText("local compute")).toBeInTheDocument();
  });

  it("clicking the Tokens button switches to the real 'tokens' basis: note, rows, and caveat all change; the prior cost caveat is gone", () => {
    render(<PerfBreakdownCard />);
    fireEvent.click(screen.getByRole("button", { name: "Tokens" }));

    expect(screen.getByText(`share of ${SPLIT.tokens.note}`)).toBeInTheDocument();
    expect(screen.queryByText(SPLIT.cost.caveat)).toBeNull();
    expect(screen.getByText(SPLIT.tokens.caveat)).toBeInTheDocument();
    for (const part of [...SPLIT.tokens.role, ...SPLIT.tokens.work]) {
      const row = within(legendRow(part.label));
      expect(row.getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(row.getByText(part.abs)).toBeInTheDocument();
    }
  });

  it("clicking the Time button switches to the real 'time' basis", () => {
    render(<PerfBreakdownCard />);
    fireEvent.click(screen.getByRole("button", { name: "Time" }));
    expect(screen.getByText(`share of ${SPLIT.time.note}`)).toBeInTheDocument();
    expect(screen.getByText(SPLIT.time.caveat)).toBeInTheDocument();
  });

  it("applies the selected-segment class only to the currently active basis button", () => {
    render(<PerfBreakdownCard />);
    const costButton = screen.getByRole("button", { name: "Cost" });
    const tokensButton = screen.getByRole("button", { name: "Tokens" });
    expect(costButton.className).toContain("segSelected");
    expect(tokensButton.className).not.toContain("segSelected");

    fireEvent.click(tokensButton);
    expect(costButton.className).not.toContain("segSelected");
    expect(tokensButton.className).toContain("segSelected");
  });

  it("renders a bar segment for a real 0%-share part with the reference file's own minimum-visible-sliver width (0.6%), never 0%", () => {
    render(<PerfBreakdownCard />);
    const zeroPart = SPLIT.cost.role.find((part) => part.pct === 0);
    expect(zeroPart).toBeDefined();
    // the bar segment has no visible text; find it via its real
    // `title` attribute (`label · pct% · abs`), transcribed verbatim
    // from the reference file's own `p.title` derivation.
    const segment = document.querySelector(
      `[title="${zeroPart!.label} · ${zeroPart!.pct}% · ${zeroPart!.abs}"]`,
    ) as HTMLElement;
    expect(segment).not.toBeNull();
    expect(segment.style.width).toBe("0.6%");
  });

  it("colors bar segments and legend dots with the real, checked B2 tokens, in the reference file's own real per-index order", () => {
    expect(colors.accent).toBe("#5B34E8");
    expect(colors.review).toBe("#D08A63");
    expect(colors.success).toBe("#2E9B72");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");

    render(<PerfBreakdownCard />);
    // cost.role's 4 real entries, in order: Implementor (index 0),
    // Reviewer (index 1), Coordinator (index 2), Local Qwen (index 3).
    const dotClass = (label: string) => (legendRow(label).firstElementChild as HTMLElement).className;
    expect(dotClass("Implementor")).toContain("segColor0");
    expect(dotClass("Reviewer")).toContain("segColor1");
    expect(dotClass("Coordinator")).toContain("segColor2");
    expect(dotClass("Local Qwen")).toContain("segColor3");
  });

  it("sets the card border/surface and segmented-track CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.segmentedTrack[1]).toBe("#F4F1F8");
    expect(colors.segmentedSelected).toBe("#FFFFFF");
    const { container } = render(<PerfBreakdownCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-brk-card-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-brk-track-bg")).toBe(colors.segmentedTrack[1]);
    expect(root.style.getPropertyValue("--atlas-brk-seg-selected-bg")).toBe(colors.segmentedSelected);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PerfBreakdownCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were written to 4 new files
in a scratch worktree and run through the real toolchain from
`apps/atlas`, before this docs-only packet was finalized (scratch
files then removed via `git clean -fd`):

- `npm run typecheck` — clean, no errors, first attempt.
- `npm run lint` — clean, no errors, first attempt.
- `npm test -- --run` — **114/114 passed** across 16 files (the exact
  number the real `vitest` run printed; pre-slice baseline was 105, and
  this slice's own new `PerfBreakdownCard.test.tsx` adds exactly 9
  tests: 105 + 9 = 114).
- `npm run build` — succeeds, no new asset failures.

No self-caught bugs — first-attempt clean on every check.

## M0-D12 bounded quality contract

1. **Protected outcome:** `PerfBreakdownCard` renders the real "m1-a
   breakdown" card in full — a real cost/tokens/time segmented control,
   both real groups ("by role", "by kind of work") with their real
   stacked bars and legends, and the current basis's own real caveat —
   completing roadmap item 28. Zero disclosed color literals. One
   disclosed, motivated real-actor substitution for the fictional
   `Architect agent` persona.
2. **Operating and threat model:** a trusted local dev box; the basis
   toggle is real client-side state (`useState`), not a network or
   persistence operation — no new attack surface.
3. **Explicit exclusions:** any wiring into `DesktopShell`/`App.tsx`,
   the mobile/narrow layout variant, the reference file's unused `unit`
   field.
4. **Assurance level:** practical component-rendering and interaction
   correctness — every note, role/work row, and caveat transcribed
   verbatim (except the one disclosed persona substitution), and the
   basis-switching behavior directly exercised by real `fireEvent.click`
   tests, not merely asserted in prose.
5. **Acceptance proof:** the 9 named tests in
   `PerfBreakdownCard.test.tsx`, the existing 105 pre-slice `apps/atlas`
   tests continuing to pass, `npm run typecheck`, `npm run lint`, and
   `npm run build`, all passing — observed total 114 tests across 16
   files.
6. **Implementation boundary:** exactly the 4 new files; no new npm
   dependency; every color a real token property; no import of any
   other component-family module.
7. **Proportionality ceiling:** one breakdown card, one fixtures
   module, one CSS Module, one test file; no wiring, no mobile variant,
   no second dataset.
8. **Stop and escalation rule:** the mobile/narrow layout variant and
   any real navigation/wiring remain out of scope; a future slice's job.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E3-PERF-BREAKDOWN-CARD-01` |
| `phase` | `PendingTargetedDecisionFidelityVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:7f9474e27e4fb84053d6bf9b2e6946ad270ecd4a", "git:planning-review-head:d257c4be52a6312e4e71988f27cefa730628c25f", "review:DecisionFidelity:REQUEST_CHANGES:color-discrepancy-table-missing-group-border-row(19-should-be-20)", "docs-only-correction:added-group-border-row;count-corrected-to-20"]` |
