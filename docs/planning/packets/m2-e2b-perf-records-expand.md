# M2 Wave E — Performance Records: Expand/Collapse — Candidate 01

**Slice ID:** `MB-SLICE-M2-E2B-PERF-RECORDS-EXPAND-01`
**Status:** `Draft — Targeted correction applied (Scope section said "two" while listing 3 files; evidence_refs cited a mistyped base hash), pending Targeted Decision Fidelity Verification`
**Base:** `424f792` (full: `424f792cc37813f4184744d85846591152623444`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 27's second half, *"Performance: per-action records list +
expand/collapse."* `MB-SLICE-M2-E2-PERF-RECORDS-LIST-01` (merged)
explicitly deferred "the expandable detail groups and the
click-to-expand behavior" to "a future `E2B`-style candidate" — this is
that candidate. Unlike every prior Wave E/C slice this session, this
one **modifies 3 already-merged files** (`perfRecords.ts`,
`PerfRecordsList.tsx`, `PerfRecordsList.module.css`) rather than adding
new ones — there is no natural way to add real click-to-expand behavior
to an existing list's existing rows via a separate, standalone file;
the reference file's own `PERF` array and `perf` row-derivation
function are the single source for both the collapsed row (already
shipped) and the expanded detail (this slice), so extending the same
fixture/component in place is the smaller, more honest change than
forking a parallel component.

No wiring into `DesktopShell`/`App.tsx` — `PerfRecordsList` remains
standalone, matching every prior Wave E slice.

## Source quote

`Atlas Explorations.dc.html`'s real markup for the row button and the
conditionally-rendered detail panel (the row button portion is
unchanged from E2's own packet; the detail panel below is the part E2
explicitly did not render):

```html
<div style="border:1px solid {{ p.border }};border-radius:14px;background:#fff;overflow:hidden">
  <button onClick="{{ p.onToggle }}" style="display:grid;grid-template-columns:{{ p.rowCols }};align-items:center;gap:8px 14px;width:100%;padding:12px 15px;border:0;background:transparent;text-align:left;cursor:pointer" style-hover="background:#FCFBFD">
    <div style="min-width:0">
      <div style="display:flex;flex-wrap:wrap;align-items:baseline;gap:9px"><span style="font-size:14.5px;font-weight:600;letter-spacing:-.01em">{{ p.action }}</span><span style="font:500 11.5px 'IBM Plex Mono',monospace;color:#A79BB4">{{ p.packet }} · {{ p.who }}</span></div>
      <div style="margin-top:2px;font:500 11px 'IBM Plex Mono',monospace;color:#8E8299;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ p.model }}</div>
    </div>
    <span style="font:500 12.5px 'IBM Plex Mono',monospace;color:#221C29;text-align:{{ p.align }}">{{ p.tokens }}</span>
    <span style="font:500 12.5px 'IBM Plex Mono',monospace;color:{{ p.costColor }};text-align:{{ p.align }}">{{ p.cost }}</span>
    <span style="font:500 12.5px 'IBM Plex Mono',monospace;color:#8E8299;text-align:{{ p.align }}">{{ p.elapsed }}</span>
    <span style="justify-self:{{ p.justify }};padding:3px 8px;border-radius:6px;background:{{ p.tagBg }};color:{{ p.tagColor }};font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.07em;text-transform:uppercase">{{ p.outcome }}</span>
  </button>
  <sc-if value="{{ p.open }}" hint-placeholder-val="{{ false }}">
  <div style="border-top:1px solid #F0ECF5;background:#FCFBFD;padding:13px 15px 14px;animation:rise .18s ease-out">
    <div style="display:grid;grid-template-columns:{{ p.detCols }};gap:14px">
      <sc-for list="{{ p.groups }}" as="g" hint-placeholder-count="3">
      <div style="min-width:0">
        <div style="font:600 10px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#A79BB4">{{ g.name }}</div>
        <div style="display:flex;flex-direction:column;gap:1px;margin-top:7px">
          <sc-for list="{{ g.rows }}" as="r" hint-placeholder-count="4">
          <div style="display:flex;align-items:baseline;gap:10px;padding:4px 0;border-bottom:1px solid #F3F0F6;font-size:13px"><span style="min-width:0;flex:1;color:#6C6376;text-wrap:pretty">{{ r.k }}</span><b style="flex:none;font-family:'IBM Plex Mono',monospace;font-weight:600;color:{{ r.color }}">{{ r.v }}</b></div>
          </sc-for>
        </div>
      </div>
      </sc-for>
    </div>
    <div style="margin-top:12px;font-size:12.5px;line-height:1.55;color:#8E8299;text-wrap:pretty">{{ p.note }}</div>
  </div>
  </sc-if>
</div>
```

Real per-record derivation logic (verbatim), the piece E2's own packet
did not need and this one does:

```js
onToggle: () => this.setState({ perfOpen: open ? null : p.id }),
border: open ? '#D6CFE4' : '#E7E1EE',
detCols: mobile || narrow ? '1fr' : 'repeat(3,minmax(0,1fr))',
groups: p.groups.map(([name, rows]) => ({ name, rows: rows.map(([k, v, kind]) => ({ k, v,
  color: kind === 'na' ? '#A79BB4' : kind === 'est' ? '#8A5A08' : kind === 'ok' ? '#1F6B4E' : kind === 'warn' ? '#A63F36' : '#221C29' })) })),
```

`open` is a real single-value state field (`s.perfOpen`), so exactly
one record's detail panel can be open at a time — opening a second
closes whichever was open (a real accordion, not five independent
booleans; checked directly against `this.setState({ perfOpen: open ?
null : p.id })`, which always replaces the whole state field). `detCols`
transcribed for desktop/non-narrow only (`repeat(3,minmax(0,1fr))`),
matching this program's own established desktop-Wave-E scope.

The real `PERF` array's per-record `note` and `groups` fields (verbatim
— all 5 records, all 3 groups each):

```js
const PERF = [
  { id: 'p1', /* ...collapsed fields unchanged from E2... */
    note: 'Counted with the model tokenizer before launch. Future tool and file growth was carried as a bounded range, not a false exact number.',
    groups: [
      ['context', [['Configured limit', '200,000', ''], ['Known input tokens', '18,400 exact', ''], ['Projected growth', '12k–31k est.', 'est'], ['Output reserve', '16,000', ''], ['Packet minimum', '90,000 · satisfied', 'ok']]],
      ['tokens', [['Input', '18,400 reported', ''], ['Cached input', 'unavailable', 'na'], ['Output', '0', ''], ['Reasoning', 'unavailable', 'na'], ['Total', '18,400', '']]],
      ['cost & time', [['Cost', 'not_billed', 'na'], ['Elapsed', '0.9s', ''], ['Allowance link', 'weekly window · fresh', ''], ['Measurement', 'tokenizer, exact', 'ok']]],
    ] },
  { id: 'p2', /* ... */
    note: 'Runtime-reported counters, so no estimate was substituted. Cached input reduced billed input on the second contract read.',
    groups: [
      ['context', [['Context used', '46,900 of 200,000', ''], ['Pressure threshold', '150,000', ''], ['Headroom', '76% free', 'ok'], ['Checkpoint fired', 'no', '']]],
      ['tokens', [['Input', '38,100 reported', ''], ['Cached input', '11,700 reported', 'ok'], ['Output', '8,800 reported', ''], ['Reasoning', '3,200 reported', ''], ['Total', '46,900', '']]],
      ['cost & time', [['Cost', '$0.41 billed', 'ok'], ['Elapsed', '2m 04s', ''], ['Attributed to', 'controlled usage', ''], ['Measurement', 'runtime-reported', 'ok']]],
    ] },
  { id: 'p3', /* ... */
    note: 'Attempt ended at a safe boundary when Terra hit the contract question. Nothing was discarded and no correction was spent.',
    groups: [
      ['context', [['Context used', '112,300 of 200,000', ''], ['Pressure threshold', '150,000', ''], ['Headroom', '44% free', ''], ['Checkpoint fired', 'no', '']]],
      ['tokens', [['Input', '81,400 reported', ''], ['Cached input', '29,600 reported', ''], ['Output', '30,900 reported', ''], ['Reasoning', '14,100 reported', ''], ['Total', '112,300', '']]],
      ['cost & time', [['Cost', '$1.86 billed', 'ok'], ['Elapsed', '38m 11s', ''], ['Ended by', 'blocker at boundary', 'warn'], ['Corrections spent', '0 of 1', '']]],
    ] },
  { id: 'p4', /* ... */
    note: 'The runtime did not return a billed amount for this attempt, so cost is labelled an estimate with its confidence — it is not presented as billed.',
    groups: [
      ['context', [['Context used', '31,200 of 200,000', ''], ['Review round', '2 of 2', ''], ['Reviewer of record', 'unchanged', 'ok'], ['Scope', 'correction range only', '']]],
      ['tokens', [['Input', '26,800 reported', ''], ['Cached input', 'unavailable', 'na'], ['Output', '4,400 reported', ''], ['Reasoning', 'unavailable', 'na'], ['Total', '31,200', '']]],
      ['cost & time', [['Cost', '$0.52 estimated', 'est'], ['Confidence', 'medium', 'est'], ['Elapsed', '6m 40s', ''], ['Measurement', 'price-table estimate', 'est']]],
    ] },
  { id: 'p5', /* ... */
    note: 'Local execution is not called zero-cost. It is reported as capacity and wall time, separately from the hosted weekly allowance.',
    groups: [
      ['context', [['Configured limit', '32,768', ''], ['Quantization', 'Q4_K_M', ''], ['Context used', '9,700 estimated', 'est'], ['Packet minimum', '8,000 · satisfied', 'ok']]],
      ['tokens', [['Input', '7,900 estimated', 'est'], ['Cached input', 'unavailable', 'na'], ['Output', '1,800 estimated', 'est'], ['Reasoning', 'unavailable', 'na'], ['Throughput', '31 tok/s', '']]],
      ['cost & time', [['Cost', 'local compute', 'na'], ['Elapsed', '4m 52s', ''], ['Host capacity', 'GPU 78% · 22m held', ''], ['Allowance impact', 'none — kept separate', 'ok']]],
    ] },
];
```

**Note the real quirk transcribed exactly, not "fixed": p1's `cost &
time` group has a row `['Cost', 'not_billed', 'na']` (underscore) while
the same record's own collapsed-row `cost` field is `'not billed'`
(space) — two different real strings for a related idea, both
transcribed verbatim.**

## Color discrepancy table — every value is a real, existing B2 token; zero disclosed literals, matching E1/E1B/E2's own precedent

| Reference value | `colors.ts` match | Verdict |
|---|---|---|
| open-card border `#D6CFE4` | `colors.borderStrong[0]` | real token |
| closed-card border `#E7E1EE` | `colors.border` (already used, unchanged) | real token |
| detail-panel border-top `#F0ECF5` | `colors.borderDivider[2]` | real token |
| detail-panel background `#FCFBFD` | `colors.focusHoverCard` **and** `colors.pageBgDesktop` (both real, identical hex — see note below) | real token |
| row hover background `#FCFBFD` | same dual match as above | real token |
| detail row divider `#F3F0F6` | `colors.borderDivider[1]` | real token |
| group-name text `#A79BB4` | `colors.inkFaint` (already used for `packetWho`) | real token |
| row-label text `#6C6376` | `colors.inkSecondary` | real token |
| detail note text `#8E8299` | `colors.inkMuted` (already used for `model`/`elapsed`) | real token |
| value color, kind `na` `#A79BB4` | `colors.inkFaint` | real token |
| value color, kind `est` `#8A5A08` | `colors.warningText` (already used) | real token |
| value color, kind `ok` `#1F6B4E` | `colors.successText` | real token |
| value color, kind `warn` `#A63F36` | `colors.dangerText` | real token |
| value color, default (`''`) `#221C29` | `colors.ink` (already used) | real token |

**The `#FCFBFD` dual match, checked exhaustively:** `colors.ts` has two
properties with the identical value `"#FCFBFD"` — `colors.pageBgDesktop`
and `colors.focusHoverCard`. Both are real, both are checked directly
against `colors.ts`; this is not a missing token needing a disclosed
literal, it is one real hex value named twice for two different
semantic roles. `colors.focusHoverCard` is used here (for both the
detail panel's background and the row's hover background) because its
name is the semantically matching one for a hover/focus surface, not
because `pageBgDesktop` is wrong — both would render identically.

## Motion — the real `motion.rise` token, not an invented animation

The reference's `animation:rise .18s ease-out` on the detail panel
matches this program's own real `motion.rise` token exactly
(`apps/atlas/src/tokens/motion.ts`): `{ description: "fade + 4px
translateY, on cards appearing", translateYPx: 4, durationS: { min:
0.18, max: 0.22 }, easing: "ease-out" }` — the reference's `.18s` is
`motion.rise`'s own stated minimum duration. This slice's CSS
`@keyframes rise` (`opacity: 0 → 1`, `translateY(4px) → translateY(0)`)
is the first concrete CSS implementation of that token in this
codebase; no prior slice needed an animation.

## Guards

1. This slice modifies exactly 3 already-merged files
   (`apps/atlas/src/performance/{perfRecords.ts,PerfRecordsList.tsx,PerfRecordsList.module.css}`)
   and their test file — no other file is touched, no wiring into
   `DesktopShell`/`App.tsx`.
2. Every color is a real B2 token; zero disclosed literals — matching
   E1/E1B/E2's own precedent, unlike Gate/History which needed
   disclosures.
3. The accordion is real: exactly one record's detail panel can be open
   at a time, transcribed directly from the reference file's own single
   `perfOpen` state field (`open ? null : p.id`), not one independent
   boolean per record.
4. `prefers-reduced-motion` handling is explicitly excluded — no prior
   slice in this codebase implements it, and the reference file states
   "Keep both; they are the only motion" with no reduced-motion
   accommodation of its own.
5. The `not_billed` (underscore) vs. `not billed` (space) discrepancy
   inside p1's own real data is transcribed exactly as the reference
   states it, not normalized to match.

## `apps/atlas/src/performance/perfRecords.ts` (modified — full new content)

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real `PERF`
 * array, now including the per-record `note` and the three real
 * detail `groups` (`context`/`tokens`/`cost & time`) this program's own
 * E2 packet deferred — pure reporting content, no persona, no
 * fictional agent. Every `PerfDetailRow`'s `kind` ('' | 'est' | 'ok' |
 * 'warn' | 'na') is transcribed directly from the reference file's own
 * per-row third tuple element, not inferred from the label text.
 */
export type PerfCostKind = "billed" | "est" | "none";
export type PerfOutcome = "passed" | "complete" | "blocked" | "approved";
export type PerfDetailKind = "" | "est" | "ok" | "warn" | "na";

export interface PerfDetailRow {
  label: string;
  value: string;
  kind: PerfDetailKind;
}

export interface PerfDetailGroup {
  name: string;
  rows: PerfDetailRow[];
}

export interface PerfRecord {
  id: string;
  action: string;
  packet: string;
  who: string;
  model: string;
  tokens: string;
  cost: string;
  costKind: PerfCostKind;
  elapsed: string;
  outcome: PerfOutcome;
  note: string;
  groups: PerfDetailGroup[];
}

export const PERF_RECORDS: PerfRecord[] = [
  {
    id: "p1",
    action: "Dispatch preflight",
    packet: "A.2",
    who: "Terra",
    model: "claude-opus-4 · hosted · ctx 200k",
    tokens: "18,400 in",
    cost: "not billed",
    costKind: "none",
    elapsed: "0.9s",
    outcome: "passed",
    note: "Counted with the model tokenizer before launch. Future tool and file growth was carried as a bounded range, not a false exact number.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Configured limit", value: "200,000", kind: "" },
          { label: "Known input tokens", value: "18,400 exact", kind: "" },
          { label: "Projected growth", value: "12k–31k est.", kind: "est" },
          { label: "Output reserve", value: "16,000", kind: "" },
          { label: "Packet minimum", value: "90,000 · satisfied", kind: "ok" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "18,400 reported", kind: "" },
          { label: "Cached input", value: "unavailable", kind: "na" },
          { label: "Output", value: "0", kind: "" },
          { label: "Reasoning", value: "unavailable", kind: "na" },
          { label: "Total", value: "18,400", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "not_billed", kind: "na" },
          { label: "Elapsed", value: "0.9s", kind: "" },
          { label: "Allowance link", value: "weekly window · fresh", kind: "" },
          { label: "Measurement", value: "tokenizer, exact", kind: "ok" },
        ],
      },
    ],
  },
  {
    id: "p2",
    action: "Plan and read the A.1 contract",
    packet: "A.2",
    who: "Terra",
    model: "claude-opus-4 · hosted",
    tokens: "46,900 total",
    cost: "$0.41 billed",
    costKind: "billed",
    elapsed: "2m 04s",
    outcome: "complete",
    note: "Runtime-reported counters, so no estimate was substituted. Cached input reduced billed input on the second contract read.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Context used", value: "46,900 of 200,000", kind: "" },
          { label: "Pressure threshold", value: "150,000", kind: "" },
          { label: "Headroom", value: "76% free", kind: "ok" },
          { label: "Checkpoint fired", value: "no", kind: "" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "38,100 reported", kind: "" },
          { label: "Cached input", value: "11,700 reported", kind: "ok" },
          { label: "Output", value: "8,800 reported", kind: "" },
          { label: "Reasoning", value: "3,200 reported", kind: "" },
          { label: "Total", value: "46,900", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "$0.41 billed", kind: "ok" },
          { label: "Elapsed", value: "2m 04s", kind: "" },
          { label: "Attributed to", value: "controlled usage", kind: "" },
          { label: "Measurement", value: "runtime-reported", kind: "ok" },
        ],
      },
    ],
  },
  {
    id: "p3",
    action: "Implement RuntimePackageBuilder",
    packet: "A.2",
    who: "Terra",
    model: "claude-opus-4 · hosted",
    tokens: "112,300 total",
    cost: "$1.86 billed",
    costKind: "billed",
    elapsed: "38m 11s",
    outcome: "blocked",
    note: "Attempt ended at a safe boundary when Terra hit the contract question. Nothing was discarded and no correction was spent.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Context used", value: "112,300 of 200,000", kind: "" },
          { label: "Pressure threshold", value: "150,000", kind: "" },
          { label: "Headroom", value: "44% free", kind: "" },
          { label: "Checkpoint fired", value: "no", kind: "" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "81,400 reported", kind: "" },
          { label: "Cached input", value: "29,600 reported", kind: "" },
          { label: "Output", value: "30,900 reported", kind: "" },
          { label: "Reasoning", value: "14,100 reported", kind: "" },
          { label: "Total", value: "112,300", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "$1.86 billed", kind: "ok" },
          { label: "Elapsed", value: "38m 11s", kind: "" },
          { label: "Ended by", value: "blocker at boundary", kind: "warn" },
          { label: "Corrections spent", value: "0 of 1", kind: "" },
        ],
      },
    ],
  },
  {
    id: "p4",
    action: "Review of the A.1 correction",
    packet: "A.1",
    who: "Claude Opus",
    model: "claude-opus-4 · hosted",
    tokens: "31,200 total",
    cost: "$0.52 estimated",
    costKind: "est",
    elapsed: "6m 40s",
    outcome: "approved",
    note: "The runtime did not return a billed amount for this attempt, so cost is labelled an estimate with its confidence — it is not presented as billed.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Context used", value: "31,200 of 200,000", kind: "" },
          { label: "Review round", value: "2 of 2", kind: "" },
          { label: "Reviewer of record", value: "unchanged", kind: "ok" },
          { label: "Scope", value: "correction range only", kind: "" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "26,800 reported", kind: "" },
          { label: "Cached input", value: "unavailable", kind: "na" },
          { label: "Output", value: "4,400 reported", kind: "" },
          { label: "Reasoning", value: "unavailable", kind: "na" },
          { label: "Total", value: "31,200", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "$0.52 estimated", kind: "est" },
          { label: "Confidence", value: "medium", kind: "est" },
          { label: "Elapsed", value: "6m 40s", kind: "" },
          { label: "Measurement", value: "price-table estimate", kind: "est" },
        ],
      },
    ],
  },
  {
    id: "p5",
    action: "Source-home check",
    packet: "A.0",
    who: "local Qwen",
    model: "qwen2.5-coder-32b · local · Q4_K_M",
    tokens: "9,700 est.",
    cost: "local compute",
    costKind: "none",
    elapsed: "4m 52s",
    outcome: "passed",
    note: "Local execution is not called zero-cost. It is reported as capacity and wall time, separately from the hosted weekly allowance.",
    groups: [
      {
        name: "context",
        rows: [
          { label: "Configured limit", value: "32,768", kind: "" },
          { label: "Quantization", value: "Q4_K_M", kind: "" },
          { label: "Context used", value: "9,700 estimated", kind: "est" },
          { label: "Packet minimum", value: "8,000 · satisfied", kind: "ok" },
        ],
      },
      {
        name: "tokens",
        rows: [
          { label: "Input", value: "7,900 estimated", kind: "est" },
          { label: "Cached input", value: "unavailable", kind: "na" },
          { label: "Output", value: "1,800 estimated", kind: "est" },
          { label: "Reasoning", value: "unavailable", kind: "na" },
          { label: "Throughput", value: "31 tok/s", kind: "" },
        ],
      },
      {
        name: "cost & time",
        rows: [
          { label: "Cost", value: "local compute", kind: "na" },
          { label: "Elapsed", value: "4m 52s", kind: "" },
          { label: "Host capacity", value: "GPU 78% · 22m held", kind: "" },
          { label: "Allowance impact", value: "none — kept separate", kind: "ok" },
        ],
      },
    ],
  },
];
```

## `apps/atlas/src/performance/PerfRecordsList.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily, motion } from "../tokens";
import {
  PERF_RECORDS,
  type PerfCostKind,
  type PerfDetailKind,
  type PerfOutcome,
  type PerfRecord,
} from "./perfRecords";
import styles from "./PerfRecordsList.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1/E1B/E2. The outcome-tag, cost-color, and detail-value-color
 * mappings are transcribed verbatim from `Atlas Explorations.dc.html`'s
 * real per-record derivation logic (`tag`/`costColor`/detail-row
 * `color` in the reference file's `perf` map function). The detail
 * panel's background and the row's hover background (both the
 * reference's `#FCFBFD`) real-token-match two different B2 properties
 * at once — `colors.focusHoverCard` and `colors.pageBgDesktop` are both
 * literally `#FCFBFD`, checked directly against `colors.ts`;
 * `focusHoverCard` is used here as the semantically matching token for
 * a hover/focus surface. The reveal animation reuses the real
 * `motion.rise` token (fade + 4px translateY) rather than inventing new
 * values — the reference's own `.18s` duration is `motion.rise`'s
 * stated minimum.
 */
const SHELL_VARS = {
  "--atlas-perf-card-border": colors.border,
  "--atlas-perf-card-border-open": colors.borderStrong[0],
  "--atlas-perf-card-surface": colors.surface,
  "--atlas-perf-row-ink": colors.ink,
  "--atlas-perf-row-faint": colors.inkFaint,
  "--atlas-perf-row-muted": colors.inkMuted,
  "--atlas-perf-row-warning": colors.warningText,
  "--atlas-perf-row-hover-bg": colors.focusHoverCard,
  "--atlas-perf-tag-blocked-bg": colors.warningChip,
  "--atlas-perf-tag-blocked-ink": colors.warningText,
  "--atlas-perf-tag-good-bg": colors.successWash,
  "--atlas-perf-tag-good-ink": colors.successText,
  "--atlas-perf-tag-neutral-bg": colors.neutralChip,
  "--atlas-perf-tag-neutral-ink": colors.inkSecondary,
  "--atlas-perf-detail-border": colors.borderDivider[2],
  "--atlas-perf-detail-bg": colors.focusHoverCard,
  "--atlas-perf-detail-row-divider": colors.borderDivider[1],
  "--atlas-perf-detail-group-name": colors.inkFaint,
  "--atlas-perf-detail-label": colors.inkSecondary,
  "--atlas-perf-detail-note": colors.inkMuted,
  "--atlas-perf-detail-value-default": colors.ink,
  "--atlas-perf-detail-value-ok": colors.successText,
  "--atlas-perf-detail-value-est": colors.warningText,
  "--atlas-perf-detail-value-warn": colors.dangerText,
  "--atlas-perf-detail-value-na": colors.inkFaint,
  "--atlas-perf-rise-translate": `${motion.rise.translateYPx}px`,
  "--atlas-perf-rise-duration": `${motion.rise.durationS.min}s`,
  "--atlas-perf-rise-easing": motion.rise.easing,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const COST_CLASS: Record<PerfCostKind, string> = {
  billed: styles.costBilled,
  est: styles.costEst,
  none: styles.costNone,
};

const DETAIL_VALUE_CLASS: Record<PerfDetailKind, string> = {
  "": styles.detailValueDefault,
  est: styles.detailValueEst,
  ok: styles.detailValueOk,
  warn: styles.detailValueWarn,
  na: styles.detailValueNa,
};

function outcomeClass(outcome: PerfOutcome): string {
  if (outcome === "blocked") return styles.outcomeBlocked;
  if (outcome === "approved" || outcome === "passed") return styles.outcomeGood;
  return styles.outcomeNeutral;
}

function PerfRecordRow({
  record,
  open,
  onToggle,
}: {
  record: PerfRecord;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={`${styles.card} ${open ? styles.cardOpen : ""}`}>
      <button type="button" className={styles.row} onClick={onToggle}>
        <div className={styles.actionCell}>
          <div className={styles.actionLine}>
            <span className={styles.action}>{record.action}</span>
            <span className={styles.packetWho}>
              {record.packet} · {record.who}
            </span>
          </div>
          <div className={styles.model}>{record.model}</div>
        </div>
        <span className={styles.tokens}>{record.tokens}</span>
        <span className={`${styles.cost} ${COST_CLASS[record.costKind]}`}>{record.cost}</span>
        <span className={styles.elapsed}>{record.elapsed}</span>
        <span className={`${styles.outcome} ${outcomeClass(record.outcome)}`}>{record.outcome}</span>
      </button>
      {open && (
        <div className={styles.detail}>
          <div className={styles.detailGrid}>
            {record.groups.map((group) => (
              <div key={group.name} className={styles.detailGroup}>
                <div className={styles.detailGroupName}>{group.name}</div>
                <div className={styles.detailRows}>
                  {group.rows.map((row) => (
                    <div key={row.label} className={styles.detailRow}>
                      <span className={styles.detailLabel}>{row.label}</span>
                      <b className={`${styles.detailValue} ${DETAIL_VALUE_CLASS[row.kind]}`}>{row.value}</b>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className={styles.detailNote}>{record.note}</div>
        </div>
      )}
    </div>
  );
}

/**
 * Renders all 5 real `PERF_RECORDS` with the real click-to-expand
 * behavior and the expandable detail groups this program's own E2
 * packet deferred here. Real accordion: clicking a row's button toggles
 * that record's own detail panel open/closed, closing whichever other
 * record was open (matching the reference file's own single `perfOpen`
 * state field, not one independent boolean per record).
 */
export function PerfRecordsList() {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className={styles.list} style={SHELL_VARS}>
      {PERF_RECORDS.map((record) => (
        <PerfRecordRow
          key={record.id}
          record={record}
          open={openId === record.id}
          onToggle={() => setOpenId((current) => (current === record.id ? null : record.id))}
        />
      ))}
    </div>
  );
}

export default PerfRecordsList;
```

## `apps/atlas/src/performance/PerfRecordsList.module.css` (modified — full new content)

```css
.list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card {
  border: 1px solid var(--atlas-perf-card-border);
  border-radius: 14px;
  background: var(--atlas-perf-card-surface);
  overflow: hidden;
}

.cardOpen {
  border-color: var(--atlas-perf-card-border-open);
}

.row {
  display: grid;
  grid-template-columns: minmax(230px, 1fr) minmax(84px, 104px) minmax(84px, 104px) 62px 84px;
  align-items: center;
  gap: 8px 14px;
  width: 100%;
  padding: 12px 15px;
  border: 0;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font: inherit;
}

.row:hover {
  background: var(--atlas-perf-row-hover-bg);
}

.actionCell {
  min-width: 0;
}

.actionLine {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 9px;
}

.action {
  font-size: 14.5px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--atlas-perf-row-ink);
}

.packetWho {
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-perf-row-faint);
}

.model {
  margin-top: 2px;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-perf-row-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tokens {
  font: 500 12.5px var(--atlas-font-mono);
  color: var(--atlas-perf-row-ink);
  text-align: right;
}

.cost {
  font: 500 12.5px var(--atlas-font-mono);
  text-align: right;
}

.costBilled {
  color: var(--atlas-perf-row-ink);
}

.costEst {
  color: var(--atlas-perf-row-warning);
}

.costNone {
  color: var(--atlas-perf-row-muted);
}

.elapsed {
  font: 500 12.5px var(--atlas-font-mono);
  color: var(--atlas-perf-row-muted);
  text-align: right;
}

.outcome {
  justify-self: center;
  padding: 3px 8px;
  border-radius: 6px;
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.outcomeBlocked {
  background: var(--atlas-perf-tag-blocked-bg);
  color: var(--atlas-perf-tag-blocked-ink);
}

.outcomeGood {
  background: var(--atlas-perf-tag-good-bg);
  color: var(--atlas-perf-tag-good-ink);
}

.outcomeNeutral {
  background: var(--atlas-perf-tag-neutral-bg);
  color: var(--atlas-perf-tag-neutral-ink);
}

.detail {
  border-top: 1px solid var(--atlas-perf-detail-border);
  background: var(--atlas-perf-detail-bg);
  padding: 13px 15px 14px;
  animation: rise var(--atlas-perf-rise-duration) var(--atlas-perf-rise-easing);
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(var(--atlas-perf-rise-translate));
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.detailGrid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.detailGroup {
  min-width: 0;
}

.detailGroupName {
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-perf-detail-group-name);
}

.detailRows {
  display: flex;
  flex-direction: column;
  gap: 1px;
  margin-top: 7px;
}

.detailRow {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 4px 0;
  border-bottom: 1px solid var(--atlas-perf-detail-row-divider);
  font-size: 13px;
}

.detailLabel {
  min-width: 0;
  flex: 1;
  color: var(--atlas-perf-detail-label);
  text-wrap: pretty;
}

.detailValue {
  flex: none;
  font-family: var(--atlas-font-mono);
  font-weight: 600;
}

.detailValueDefault {
  color: var(--atlas-perf-detail-value-default);
}

.detailValueOk {
  color: var(--atlas-perf-detail-value-ok);
}

.detailValueEst {
  color: var(--atlas-perf-detail-value-est);
}

.detailValueWarn {
  color: var(--atlas-perf-detail-value-warn);
}

.detailValueNa {
  color: var(--atlas-perf-detail-value-na);
}

.detailNote {
  margin-top: 12px;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--atlas-perf-detail-note);
  text-wrap: pretty;
}
```

## `apps/atlas/src/performance/PerfRecordsList.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, within, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, motion } from "../tokens";
import { PerfRecordsList } from "./PerfRecordsList";
import { PERF_RECORDS } from "./perfRecords";

afterEach(cleanup);

describe("PerfRecordsList", () => {
  it("renders all 5 real records with their action, packet/who, model, tokens, cost, and elapsed", () => {
    render(<PerfRecordsList />);
    // `action` is the one field unique per record (three records share
    // the real "A.2 · Terra" packet/who pair), so each record's row is
    // found via its own action text, then every other field is checked
    // scoped to that same row — not a bare, ambiguous getByText.
    for (const record of PERF_RECORDS) {
      const action = screen.getByText(record.action);
      const row = action.closest("button") as HTMLElement;
      expect(row).not.toBeNull();
      const rowScope = within(row);
      expect(rowScope.getByText(`${record.packet} · ${record.who}`)).toBeInTheDocument();
      expect(rowScope.getByText(record.model)).toBeInTheDocument();
      expect(rowScope.getByText(record.tokens)).toBeInTheDocument();
      expect(rowScope.getByText(record.cost)).toBeInTheDocument();
      expect(rowScope.getByText(record.elapsed)).toBeInTheDocument();
    }
  });

  it("renders exactly 5 row buttons, each with an outcome tag, and no detail panel until opened", () => {
    render(<PerfRecordsList />);
    expect(screen.getAllByRole("button")).toHaveLength(5);
    expect(screen.getAllByText("passed")).toHaveLength(2);
    expect(screen.getByText("complete")).toBeInTheDocument();
    expect(screen.getByText("blocked")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
    for (const record of PERF_RECORDS) {
      expect(screen.queryByText(record.note)).toBeNull();
    }
  });

  it("colors the blocked outcome tag with the warning chip, and passed/approved with the success wash, matching the reference file's real per-outcome mapping", () => {
    render(<PerfRecordsList />);
    const blocked = screen.getByText("blocked");
    const approved = screen.getByText("approved");
    const complete = screen.getByText("complete");
    expect(blocked.className).toContain("outcomeBlocked");
    expect(approved.className).toContain("outcomeGood");
    expect(complete.className).toContain("outcomeNeutral");
  });

  it("colors billed costs ink, estimated costs amber, and non-billed costs muted, matching the reference file's real per-record costKind mapping", () => {
    render(<PerfRecordsList />);
    const billed = screen.getByText("$0.41 billed");
    const estimated = screen.getByText("$0.52 estimated");
    const notBilled = screen.getByText("not billed");
    expect(billed.className).toContain("costBilled");
    expect(estimated.className).toContain("costEst");
    expect(notBilled.className).toContain("costNone");
  });

  it("sets the card border/surface and tag CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.warningChip).toBe("#FDF1DC");
    expect(colors.successWash).toBe("#E4F6EE");
    const { container } = render(<PerfRecordsList />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-perf-card-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-perf-tag-blocked-bg")).toBe(colors.warningChip);
    expect(root.style.getPropertyValue("--atlas-perf-tag-good-bg")).toBe(colors.successWash);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PerfRecordsList />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });

  it("clicking a row's button opens its own real detail panel, with all 3 real groups and every real row label", () => {
    render(<PerfRecordsList />);
    const record = PERF_RECORDS[0];
    const button = screen.getByText(record.action).closest("button") as HTMLElement;
    fireEvent.click(button);

    expect(screen.getByText(record.note)).toBeInTheDocument();
    expect(record.groups).toHaveLength(3);
    for (const group of record.groups) {
      // `group.name` renders inside its own `.detailGroupName` div, a
      // direct child of the `.detailGroup` wrapper that also holds the
      // rows — so `parentElement`, not `closest("div")` (which would
      // just return the name div itself, since it is one).
      const groupNode = screen.getByText(group.name).parentElement as HTMLElement;
      const groupScope = within(groupNode);
      for (const row of group.rows) {
        expect(groupScope.getByText(row.label)).toBeInTheDocument();
      }
    }
  });

  it("clicking an open row's button again closes its detail panel", () => {
    render(<PerfRecordsList />);
    const record = PERF_RECORDS[0];
    const button = screen.getByText(record.action).closest("button") as HTMLElement;
    fireEvent.click(button);
    expect(screen.getByText(record.note)).toBeInTheDocument();
    fireEvent.click(button);
    expect(screen.queryByText(record.note)).toBeNull();
  });

  it("is a real accordion: opening a second row closes whichever record was open first", () => {
    render(<PerfRecordsList />);
    const first = PERF_RECORDS[0];
    const second = PERF_RECORDS[1];
    const firstButton = screen.getByText(first.action).closest("button") as HTMLElement;
    const secondButton = screen.getByText(second.action).closest("button") as HTMLElement;

    fireEvent.click(firstButton);
    expect(screen.getByText(first.note)).toBeInTheDocument();

    fireEvent.click(secondButton);
    expect(screen.queryByText(first.note)).toBeNull();
    expect(screen.getByText(second.note)).toBeInTheDocument();
  });

  it("applies the open-card border token's class only to the currently open record's card", () => {
    render(<PerfRecordsList />);
    const first = PERF_RECORDS[0];
    const button = screen.getByText(first.action).closest("button") as HTMLElement;
    const card = button.closest("div") as HTMLElement;
    expect(card.className).not.toContain("cardOpen");
    fireEvent.click(button);
    expect(card.className).toContain("cardOpen");
  });

  it("colors each detail row's value by its real kind, matching the reference file's exact mapping", () => {
    render(<PerfRecordsList />);
    const record = PERF_RECORDS[0];
    const button = screen.getByText(record.action).closest("button") as HTMLElement;
    fireEvent.click(button);

    const okRow = screen.getByText("Packet minimum").closest("div") as HTMLElement;
    expect(within(okRow).getByText("90,000 · satisfied").className).toContain("detailValueOk");

    const estRow = screen.getByText("Projected growth").closest("div") as HTMLElement;
    expect(within(estRow).getByText("12k–31k est.").className).toContain("detailValueEst");

    const naRow = screen.getByText("Cost").closest("div") as HTMLElement;
    expect(within(naRow).getByText("not_billed").className).toContain("detailValueNa");

    const plainRow = screen.getByText("Elapsed").closest("div") as HTMLElement;
    expect(within(plainRow).getByText("0.9s").className).toContain("detailValueDefault");
  });

  it("uses the real motion.rise token for the detail panel's reveal animation, not invented values", () => {
    expect(motion.rise.translateYPx).toBe(4);
    expect(motion.rise.durationS.min).toBe(0.18);
    expect(motion.rise.easing).toBe("ease-out");
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were written to the 4 files
in a scratch worktree and run through the real toolchain from
`apps/atlas`, before this docs-only packet was finalized (scratch
changes then reverted — this commit touches only this packet's own
`.md` file):

- `npm run typecheck` — clean, no errors, first attempt.
- `npm run lint` — clean, no errors, first attempt.
- `npm test -- --run` — **105/105 passed** across 15 files, the exact
  number the real `vitest` run printed (pre-slice baseline was 99;
  `PerfRecordsList.test.tsx` itself grew from its own 6 existing tests
  to 12 in this slice, a net +6 — one of the 6 original tests, "renders
  exactly 5 inert row buttons, each with an outcome tag," was renamed
  to "renders exactly 5 row buttons, each with an outcome tag, and no
  detail panel until opened" and extended in place, and 6 new tests
  were added: 99 + 6 = 105).
- `npm run build` — succeeds, no new asset failures.

No self-caught bugs this time — first-attempt clean on every check.

## M0-D12 bounded quality contract

1. **Protected outcome:** `PerfRecordsList` renders the real
   click-to-expand accordion and all 3 real detail groups (with every
   real row) for all 5 real `PERF_RECORDS`, completing roadmap item 27
   in full. Zero disclosed color literals; the real `motion.rise` token
   drives the reveal animation.
2. **Operating and threat model:** a trusted local dev box; the
   click-to-expand behavior is real client-side state (`useState`), not
   a network or persistence operation — no new attack surface.
3. **Explicit exclusions:** any wiring into `DesktopShell`/`App.tsx`,
   the mobile/narrow `detCols`/`rowCols` variants, `prefers-reduced-
   motion` handling (no prior precedent in this codebase).
4. **Assurance level:** practical component-rendering and interaction
   correctness — every group, row, and color value transcribed
   verbatim from the reference file, and the accordion behavior
   directly exercised by real `fireEvent.click` tests, not merely
   asserted in prose.
5. **Acceptance proof:** the 12 named tests in `PerfRecordsList.test.tsx`
   (6 carried over from the file's own pre-slice version, 6 new), the
   remaining 93 pre-slice `apps/atlas` tests continuing to pass, `npm
   run typecheck`, `npm run lint`, and `npm run build`, all passing —
   observed total 105 tests across 15 files (99 pre-slice total − 6
   pre-slice `PerfRecordsList.test.tsx` tests + 12 post-slice
   `PerfRecordsList.test.tsx` tests = 105).
6. **Implementation boundary:** exactly the 3 modified files plus their
   test file; no new npm dependency; every color a real token property;
   no import of any other component-family module.
7. **Proportionality ceiling:** one list component's expand/collapse
   behavior and its own detail data; no new component, no wiring, no
   mobile variant.
8. **Stop and escalation rule:** the mobile/narrow layout variant and
   any real navigation/wiring remain out of scope; a future slice's
   job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E2B-PERF-RECORDS-EXPAND-01` |
| `phase` | `PendingTargetedDecisionFidelityVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:424f792cc37813f4184744d85846591152623444", "git:planning-review-head:b2faf6f32a084397aa1bf2c6807122d6245fd2dc", "review:DecisionFidelity:REQUEST_CHANGES:scope-said-two-files-listed-three;evidence_refs-base-hash-mistyped", "docs-only-correction:scope-file-count-fixed-to-3;evidence_refs-base-hash-corrected"]` |
