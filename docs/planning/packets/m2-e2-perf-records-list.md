# M2 Wave E — Performance Per-Action Records List (Collapsed) — Candidate 01

**Slice ID:** `MB-SLICE-M2-E2-PERF-RECORDS-LIST-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `5bea881` (full: `5bea8811da7d98f42ae76c2fa4b8228a548c27d6`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 27, *"E2 — Performance: per-action records list +
expand/collapse,"* split into two smaller candidates per this
program's standing "smallest possible slice" discipline — the same
split pattern already used for item 26 (E1/E1B). This slice renders
only the **collapsed row** for all 5 real `PERF` records (action,
packet/who, model, tokens, cost, elapsed, outcome tag). The expandable
detail groups (3 groups of `context`/`tokens`/`cost & time` rows per
record — a large, separate real dataset) and the click-to-expand
behavior are a future `E2B`-style candidate, exactly like the header/
strip split.

**Zero disclosed color literals — every value is a real, existing B2
token, matching E1's and E1B's own precedent.**

Reference file's real `PERF` array (verbatim, all 5 records, elided to
the fields this slice renders — `note` and `groups` are out of scope,
E2B's job):

```js
const PERF = [
  { id: 'p1', action: 'Dispatch preflight', packet: 'A.2', who: 'Terra', model: 'claude-opus-4 · hosted · ctx 200k',
    tokens: '18,400 in', cost: 'not billed', costKind: 'none', elapsed: '0.9s', outcome: 'passed', ... },
  { id: 'p2', action: 'Plan and read the A.1 contract', packet: 'A.2', who: 'Terra', model: 'claude-opus-4 · hosted',
    tokens: '46,900 total', cost: '$0.41 billed', costKind: 'billed', elapsed: '2m 04s', outcome: 'complete', ... },
  { id: 'p3', action: 'Implement RuntimePackageBuilder', packet: 'A.2', who: 'Terra', model: 'claude-opus-4 · hosted',
    tokens: '112,300 total', cost: '$1.86 billed', costKind: 'billed', elapsed: '38m 11s', outcome: 'blocked', ... },
  { id: 'p4', action: 'Review of the A.1 correction', packet: 'A.1', who: 'Claude Opus', model: 'claude-opus-4 · hosted',
    tokens: '31,200 total', cost: '$0.52 estimated', costKind: 'est', elapsed: '6m 40s', outcome: 'approved', ... },
  { id: 'p5', action: 'Source-home check', packet: 'A.0', who: 'local Qwen', model: 'qwen2.5-coder-32b · local · Q4_K_M',
    tokens: '9,700 est.', cost: 'local compute', costKind: 'none', elapsed: '4m 52s', outcome: 'passed', ... },
];
```

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from — **each record is its
own separately bordered, rounded card in a `gap:8px` column, not one
shared-border list with hairline dividers** — checked directly against
the real markup, not assumed):

```html
<div style="margin-top:14px;display:flex;flex-direction:column;gap:8px">
  <sc-for list="{{ perf }}" as="p" hint-placeholder-count="5">
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
    <!-- expanded detail panel: not rendered by this slice, see above -->
  </div>
  </sc-for>
</div>
```

`p.border` is `open ? '#D6CFE4' : '#E7E1EE'` — this slice always
renders the closed border (`#E7E1EE`), since no record is ever open
(no expand state exists yet). `p.rowCols` (desktop, non-mobile/
non-narrow) is `minmax(230px,1fr) minmax(84px,104px)
minmax(84px,104px) 62px 84px`; `p.align` is `right`; `p.justify` is
`center` — transcribed directly, not the mobile/narrow variants (this
is a desktop-Wave-E slice, matching E1/E1B's own desktop scope).

Reference file's real per-record derivation logic (verbatim, the
outcome-tag and cost-color mappings this slice's fixture/component
reproduce exactly):

```js
const tag = p.outcome === 'blocked' ? ['#FDF1DC', '#8A5A08']
  : p.outcome === 'approved' || p.outcome === 'passed' ? ['#E4F6EE', '#1F6B4E']
  : ['#F2EEF8', '#6C6376'];
// ...
costColor: p.costKind === 'billed' ? '#221C29' : p.costKind === 'est' ? '#8A5A08' : '#8E8299',
```

**"Options rendered but inert," matching C4's/C6's own established
implementation, not the reference file's live `cursor:pointer` /
`onClick` behavior.** Real `<button>` elements, no `onClick` handler at
all, `cursor: default` — the click-to-expand command doesn't exist yet
in this slice (that's E2B's job).

**Color discrepancy table — every value is a real, existing B2 token;
zero disclosed literals, matching E1's and E1B's own precedent:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| card border (closed) `#E7E1EE` | `colors.border` | exact |
| card bg `#fff` | `colors.surface` | exact |
| action / tokens text `#221C29` (implicit default / explicit) | `colors.ink` | exact |
| packet·who text `#A79BB4` | `colors.inkFaint` | exact |
| model / elapsed text `#8E8299` | `colors.inkMuted` | exact |
| cost (est) `#8A5A08` | `colors.warningText` | exact |
| tag `blocked` `#FDF1DC`/`#8A5A08` | `colors.warningChip`/`colors.warningText` | exact |
| tag `approved`/`passed` `#E4F6EE`/`#1F6B4E` | `colors.successWash`/`colors.successText` | exact |
| tag other (`complete`) `#F2EEF8`/`#6C6376` | `colors.neutralChip`/`colors.inkSecondary` | exact |

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E2-PERF-RECORDS-LIST-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:5bea8811da7d98f42ae76c2fa4b8228a548c27d6"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real post-E1B-merge toolchain during authoring, not only
drafted.** All four files below were written to a scratch copy of this
worktree (rebased onto master after E1B's real merge, so the baseline
below is accurate, not stale) and `npm run typecheck`, `npm run lint`,
`npm test`, and `npm run build` were run for real from `apps/atlas/`.
The first real test run found one genuine defect in the test file (not
the component): the first test used a bare `screen.getByText(...)` for
the `"A.2 · Terra"` packet/who pair, but three of the five real records
(`p1`, `p2`, `p3`) share that exact real value, so the query matched
multiple elements and failed with a real `getByText` ambiguity error.
Fixed by finding each record's row via its own unique `action` text
first, then scoping every other field assertion to that row with
`within(row)` — not a component bug, a real test-design gap this
program's own fixture data exposed. After that fix: 81/81 tests passed
(75 existing + 6 new), typecheck and lint clean, production build
succeeded.

`apps/atlas/src/performance/perfRecords.ts` (new — the records data
and its types; no rendering logic; does not modify E1's/E1B's frozen
files in the same directory):

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real `PERF`
 * array — pure reporting content, no persona, no fictional agent.
 * This slice renders only the collapsed row (action/packet/who/model/
 * tokens/cost/elapsed/outcome) for all 5 real records; the expandable
 * detail groups and the click-to-expand behavior are a separate,
 * later slice (a future `E2B`-style candidate), matching this
 * program's own established header/strip split pattern (E1/E1B).
 */
export type PerfCostKind = "billed" | "est" | "none";
export type PerfOutcome = "passed" | "complete" | "blocked" | "approved";

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
  },
];
```

`apps/atlas/src/performance/PerfRecordsList.module.css` (new — CSS
Module, `var(--atlas-*)` only, following the exact E1/E1B/C1/C7
pattern):

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
  cursor: default;
  font: inherit;
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
```

`apps/atlas/src/performance/PerfRecordsList.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { PERF_RECORDS, type PerfCostKind, type PerfOutcome, type PerfRecord } from "./perfRecords";
import styles from "./PerfRecordsList.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1/E1B. The outcome-tag and cost-color mappings are transcribed
 * verbatim from `Atlas Explorations.dc.html`'s real per-record
 * derivation logic (`tag`/`costColor` in the reference file's `perf`
 * map function).
 */
const SHELL_VARS = {
  "--atlas-perf-card-border": colors.border,
  "--atlas-perf-card-surface": colors.surface,
  "--atlas-perf-row-ink": colors.ink,
  "--atlas-perf-row-faint": colors.inkFaint,
  "--atlas-perf-row-muted": colors.inkMuted,
  "--atlas-perf-row-warning": colors.warningText,
  "--atlas-perf-tag-blocked-bg": colors.warningChip,
  "--atlas-perf-tag-blocked-ink": colors.warningText,
  "--atlas-perf-tag-good-bg": colors.successWash,
  "--atlas-perf-tag-good-ink": colors.successText,
  "--atlas-perf-tag-neutral-bg": colors.neutralChip,
  "--atlas-perf-tag-neutral-ink": colors.inkSecondary,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const COST_CLASS: Record<PerfCostKind, string> = {
  billed: styles.costBilled,
  est: styles.costEst,
  none: styles.costNone,
};

function outcomeClass(outcome: PerfOutcome): string {
  if (outcome === "blocked") return styles.outcomeBlocked;
  if (outcome === "approved" || outcome === "passed") return styles.outcomeGood;
  return styles.outcomeNeutral;
}

function PerfRecordRow({ record }: { record: PerfRecord }) {
  return (
    <div className={styles.card}>
      <button type="button" className={styles.row}>
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
    </div>
  );
}

/**
 * Renders the collapsed row only for all 5 real `PERF_RECORDS` — the
 * expandable detail groups and the click-to-expand behavior are a
 * separate, later slice (a future `E2B`-style candidate), matching
 * this program's own established header/strip split pattern (E1/E1B).
 * Each row is a real `<button>` (matching the reference file's own
 * markup) with no `onClick` — genuinely inert, not wired yet.
 */
export function PerfRecordsList() {
  return (
    <div className={styles.list} style={SHELL_VARS}>
      {PERF_RECORDS.map((record) => (
        <PerfRecordRow key={record.id} record={record} />
      ))}
    </div>
  );
}

export default PerfRecordsList;
```

`apps/atlas/src/performance/PerfRecordsList.test.tsx` (new):

```tsx
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
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

  it("renders exactly 5 inert row buttons, each with an outcome tag", () => {
    render(<PerfRecordsList />);
    expect(screen.getAllByRole("button")).toHaveLength(5);
    expect(screen.getAllByText("passed")).toHaveLength(2);
    expect(screen.getByText("complete")).toBeInTheDocument();
    expect(screen.getByText("blocked")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
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
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `DesktopShell` or `App.tsx` —
   standalone, exactly like E1's `PerformanceHeader` and E1B's
   `WeeklyWindowStrip`.
2. This slice does not modify E1's/E1B's frozen `fixtures.ts`,
   `PerformanceHeader.*`, `weeklyWindow.ts`, or `WeeklyWindowStrip.*`
   in the same directory — it adds new, separate files.
3. Every color is a real B2 token; there is no disclosed literal in
   this slice at all.
4. Every row is a real `<button>` with no `onClick` — genuinely inert,
   matching C4's/C6's established pattern, not merely styled to look
   disabled.
5. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, `apps/atlas/src/decision/`, or
   `apps/atlas/src/crash/` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/performance/perfRecords.ts` (new)
- `apps/atlas/src/performance/PerfRecordsList.module.css` (new)
- `apps/atlas/src/performance/PerfRecordsList.tsx` (new)
- `apps/atlas/src/performance/PerfRecordsList.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, E1's/E1B's own files, and
everything under `apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/decision/`, `apps/atlas/src/crash/`, and
`apps/atlas/src/tokens/` are untouched.

The 6 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 81 total after this slice (75 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 CrashCard tests, 7 thread tests, 7
PacketHeader tests, 6 PerformanceHeader tests, 5 WeeklyWindowStrip
tests, 5 mobile-shell tests, 10 desktop-shell tests — + 6 new). `npm
run build` must still succeed; `PerfRecordsList` is not expected to
appear in the `dist/` bundle, matching every prior standalone slice's
own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `PerfRecordsList` renders the Performance
   screen's real collapsed-row anatomy (action/packet-who/model/
   tokens/cost/elapsed/outcome tag) for all 5 real `PERF_RECORDS`
   using only real B2 tokens — no disclosed literal anywhere in this
   slice.
2. **Operating and threat model:** a trusted local dev box; fully
   read-only, no interactive element with any effect (real `<button>`
   elements, no `onClick`).
3. **Explicit exclusions:** the expandable detail groups and
   click-to-expand behavior (a future `E2B`-style candidate), the
   `m1-a breakdown` card (E3), any wiring into `DesktopShell`/
   `App.tsx`, any modification of E1's/E1B's own frozen files, the
   mobile/narrow row layout variant.
4. **Assurance level:** practical component-rendering correctness with
   every value transcribed verbatim from the reference file and every
   color a real, existing token — matching E1's/E1B's own
   highest-token-purity precedent, proportionate to a read-only view
   with no data dependency and no consumer yet.
5. **Acceptance proof:** the 6 named tests, the existing 75 `apps/atlas`
   tests continuing to pass (81 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color a real token property; no import
   of any other component-family module; no modification of E1's/E1B's
   own files.
7. **Proportionality ceiling:** one records-list component, one data
   module, one CSS Module; no detail groups, no expand behavior, no
   breakdown card, no wiring, no mobile variant.
8. **Stop and escalation rule:** the expandable detail groups, the
   click-to-expand behavior, the `m1-a breakdown` card, and wiring
   `PerfRecordsList`/`PerformanceHeader`/`WeeklyWindowStrip` together
   into one Performance screen and into `DesktopShell`'s nav/content
   pane are each new, separately reviewed work — not decided implicitly
   here. A discovered proof/contract defect against a frozen slice
   terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
