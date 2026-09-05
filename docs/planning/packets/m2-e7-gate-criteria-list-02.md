# M2 Wave E — Gate Entry-Criteria List — Candidate 02

**Slice ID:** `MB-SLICE-M2-E7-GATE-CRITERIA-LIST-02`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `100c59e` (full: `100c59e190e57952a47f123676aa726e216772c0`, `origin/master`)

**Candidate `-01` is terminally `returned` and this is a fresh
candidate, not a correction of it.** `-01`'s sole targeted planning
correction fixed one real Decision Fidelity finding (an undisclosed
truncation dropping this same card's own real footer note) but its own
replacement reasoning for a second finding introduced a *new*,
confirmed false claim — asserting `DesktopShell.tsx` "uses ...
`navTextDim`," when that file actually consumes `colors.inkMuted` and
mentions `navTextDim` only in a comment about coincidental value
equality. Targeted verification caught it and returned
`REQUEST_CHANGES`; per this program's bounded-correction policy, `-01`
cannot be corrected again. This candidate does not reuse `-01`'s
specific wording for that disclosure — see below, where every claim
about which `colors.ts` nav-group properties are and are not consumed
has been checked exhaustively, one property at a time, not partially
enumerated.

## Scope, deliberately minimal

Identical scope to `-01`: roadmap item 32, *"E7 — Gate: criteria list +
gate-open state (disabled button, approver/what-opens panel),"* split
into two smaller candidates per this program's standing "smallest
possible slice" discipline — the same split pattern already used for
items 26 and 27 (E1/E1B, E2/E2B). This slice renders only the
**entry-criteria card in full**: the header label + met-count summary,
all 5 real criteria rows, and the card's own trailing footer note. The
gate's own separate header block (title, state line, `Open gate`
button, approver note, releases list) is a future `E7B`-style
candidate — deliberately deferred, for a real, checked reason: its
lede and approver note both reference the reference file's fictional
"Architect agent" (*"the Architect agent verifies them against
records"*; *"The Architect agent opens the gate on its own once the
criteria read true"*) and need the same real-mechanism adaptation
treatment Wave C used (C3/C4) before they can be rendered honestly.
This slice's own criteria-card content has no such issue — it names no
persona at all.

Reference file's real `GATE_CRITERIA` array (verbatim):

```js
const GATE_CRITERIA = [
  ['A.0 through A.7 accepted', 'Every M1-A packet closed by the Coordinator with locks released.', '2 of 8 accepted', 'no'],
  ['Frozen-presentation contract holds', 'No packet re-derived or widened the A.1 identity contract.', 'A.1 · 9d3e1a2', 'yes'],
  ['Every owner decision carries a fidelity check', 'Rulings that changed behaviour are recorded and binding on later packets.', 'DF-2 pending', 'part'],
  ['Fixture journey proven end to end', 'A.6 demonstrates the complete journey and its exclusions.', 'A.6 not dispatched', 'no'],
  ['No correction budget overdrawn', 'One correction per packet, same reviewer of record.', '1 spent · none over', 'yes'],
];
```

Reference file's real per-criterion derivation and header met-summary
(verbatim):

```js
metLabel: '2 met · 1 partial · 2 open', metColor: '#8E8299',
// ...
criteria: GATE_CRITERIA.map(([title, detail, evidence, met]) => ({
  title, detail, evidence,
  titleColor: met === 'no' ? '#6C6376' : '#221C29',
  evColor: met === 'yes' ? '#1F6B4E' : met === 'part' ? '#8A5A08' : '#A79BB4',
  markBg: met === 'yes' ? '#2E9B72' : met === 'part' ? '#E0A32E' : 'transparent',
  markBorder: met === 'no' ? '1.5px solid #CFC6D6' : '0',
})),
```

`'2 met · 1 partial · 2 open'` is independently checkable against the
5 real criteria's own `met` values: 2 `yes`, 1 `part`, 2 `no` — this
slice's test suite verifies the count itself, not just transcribes the
label.

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from — the full card,
including its own trailing footer row):

```html
<div style="margin-top:20px;border:1px solid #E7E1EE;border-radius:14px;background:#fff;overflow:hidden">
  <div style="display:flex;align-items:center;gap:10px;padding:12px 16px;border-bottom:1px solid #EEEAF2;font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#6C6376">entry criteria<span style="margin-left:auto;letter-spacing:.06em;color:{{ gate.metColor }}">{{ gate.metLabel }}</span></div>
  <sc-for list="{{ gate.criteria }}" as="c" hint-placeholder-count="5">
  <div style="display:grid;grid-template-columns:20px minmax(0,1fr) auto;align-items:start;gap:12px;padding:13px 16px;border-bottom:1px solid #F3F0F6">
    <span style="margin-top:2px;width:16px;height:16px;box-sizing:border-box;border-radius:5px;background:{{ c.markBg }};border:{{ c.markBorder }}"></span>
    <div style="min-width:0">
      <div style="font-size:14.5px;font-weight:600;line-height:1.4;color:{{ c.titleColor }};text-wrap:pretty">{{ c.title }}</div>
      <div style="margin-top:2px;font-size:13px;line-height:1.5;color:#6C6376;text-wrap:pretty">{{ c.detail }}</div>
    </div>
    <span style="flex:none;font:500 11.5px 'IBM Plex Mono',monospace;color:{{ c.evColor }}">{{ c.evidence }}</span>
  </div>
  </sc-for>
  <div style="padding:12px 16px;font-size:12.5px;color:#8E8299">Criteria were fixed when M1-A opened. Changing one is an owner decision and reopens the milestone plan.</div>
</div>
```

**"Options rendered but inert" is not applicable here — this card has
no interactive element at all**, real or otherwise; every row is a
plain, non-button `<div>`, matching the reference file's own markup
exactly (unlike the Performance records list, this card's rows were
never buttons in the reference file to begin with).

**The one real, disclosed gap: the unmet-criterion mark's border color
(`#CFC6D6`) — this time, every claim about which `colors.ts` nav-group
properties are and are not consumed has been checked one at a time,
exhaustively, not partially enumerated (the exact gap that returned
`-01`'s targeted verification with `REQUEST_CHANGES`).** `#CFC6D6`
equals `colors.navText`. Grepped directly, one property at a time,
against every property in that same `colors.ts` nav-color group
(`navGround`, `navText`, `navTextActive`, `navTextInactive`,
`navTextDim`, `navActiveBg`, `navHoverBg`):

| Property | Real consumer in `apps/atlas/src`? |
|---|---|
| `navGround` | yes — `DesktopShell.tsx`'s `--atlas-nav-ground` |
| `navText` | **no** — zero occurrences of `colors.navText` anywhere outside `colors.ts` itself |
| `navTextActive` | yes — `DesktopShell.tsx`'s `--atlas-nav-text-active` and `--atlas-nav-text-running` |
| `navTextInactive` | yes — `DesktopShell.tsx`'s `--atlas-nav-text-inactive` |
| `navTextDim` | **no** — appears only inside a `DesktopShell.tsx` comment noting it coincidentally equals `colors.inkMuted`, which is the value actually consumed there; `colors.navTextDim` itself is never read as a value anywhere |
| `navActiveBg` | yes — `DesktopShell.tsx`'s `--atlas-nav-active-bg` |
| `navHoverBg` | yes — `DesktopShell.tsx`'s `--atlas-nav-hover-bg` |

Five of the seven properties in this group are real, consumed values
in `DesktopShell.tsx`'s nav sidebar. `navText` is not one of them —
its scoping to the dark sidebar rests on its name and its position in
this real, mostly-consumed group, not on any actual usage of the
property itself. Reusing it here, for a completely different (light-
mode, criterion-mark) context, would be a coincidental-hex, wrong-
semantic substitution — exactly the failure mode this program's own
established convention (never reuse a near-but-wrong token) exists to
prevent. No other property anywhere in `colors.ts` matches `#CFC6D6`
either (checked directly against the full file).

**Color discrepancy table — every value is a real, existing B2 token
except the one disclosed above:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| card border `#E7E1EE` | `colors.border` | exact |
| card bg `#fff` | `colors.surface` | exact |
| header border `#EEEAF2` | `colors.borderDivider[0]` | exact |
| header label text `#6C6376` | `colors.inkSecondary` | exact |
| met-summary text `#8E8299` | `colors.inkMuted` | exact |
| row border `#F3F0F6` | `colors.borderDivider[1]` | exact |
| title (met/`part`) `#221C29` | `colors.ink` | exact |
| title (`no`) `#6C6376` | `colors.inkSecondary` | exact |
| detail text `#6C6376` | `colors.inkSecondary` | exact |
| evidence (`yes`) `#1F6B4E` | `colors.successText` | exact |
| evidence (`part`) `#8A5A08` | `colors.warningText` | exact |
| evidence (`no`) `#A79BB4` | `colors.inkFaint` | exact |
| mark bg (`yes`) `#2E9B72` | `colors.success` | exact |
| mark bg (`part`) `#E0A32E` | `colors.warning` | exact |
| mark border (`no`) `#CFC6D6` | none in `colors.ts` (equals `colors.navText`, exhaustively checked above as the one real, unconsumed exception in an otherwise-consumed group) | disclosed literal |
| footer note text `#8E8299` | `colors.inkMuted` (same real token as the met-summary text; reused, not a new variable) | exact |

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E7-GATE-CRITERIA-LIST-02` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:100c59e190e57952a47f123676aa726e216772c0","status:supersedes:MB-SLICE-M2-E7-GATE-CRITERIA-LIST-01-terminally-returned"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`: 90/90 tests passed (81 existing +
9 new), typecheck and lint clean, production build succeeded — all on
the first real run, no fix needed.

`apps/atlas/src/gate/fixtures.ts` (new — the criteria data and its
types; no rendering logic; a new top-level directory, matching
`thread/`, `decision/`, `crash/`, `performance/`):

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `GATE_CRITERIA` array, the entry-criteria header's real
 * `metLabel`/`metColor`, and the card's own trailing footer note —
 * pure reporting content, no persona, no fictional agent. This slice
 * renders only the entry-criteria card (header, all 5 criteria rows,
 * and the card's own footer note); the gate's separate header block
 * (title, state line, Open-gate button, approver note, releases list)
 * is a separate, later slice (a future `E7B`-style candidate) — its
 * lede and approver note both reference the reference file's
 * fictional "Architect agent" and need the same real-mechanism
 * adaptation treatment Wave C used (C3/C4), which this slice's own
 * real, persona-free content does not need.
 */
export type GateCriterionMet = "yes" | "part" | "no";

export interface GateCriterion {
  title: string;
  detail: string;
  evidence: string;
  met: GateCriterionMet;
}

export const GATE_CRITERIA: GateCriterion[] = [
  {
    title: "A.0 through A.7 accepted",
    detail: "Every M1-A packet closed by the Coordinator with locks released.",
    evidence: "2 of 8 accepted",
    met: "no",
  },
  {
    title: "Frozen-presentation contract holds",
    detail: "No packet re-derived or widened the A.1 identity contract.",
    evidence: "A.1 · 9d3e1a2",
    met: "yes",
  },
  {
    title: "Every owner decision carries a fidelity check",
    detail: "Rulings that changed behaviour are recorded and binding on later packets.",
    evidence: "DF-2 pending",
    met: "part",
  },
  {
    title: "Fixture journey proven end to end",
    detail: "A.6 demonstrates the complete journey and its exclusions.",
    evidence: "A.6 not dispatched",
    met: "no",
  },
  {
    title: "No correction budget overdrawn",
    detail: "One correction per packet, same reviewer of record.",
    evidence: "1 spent · none over",
    met: "yes",
  },
];

/** Real, verbatim — matches GATE_CRITERIA's own real counts (2 yes, 1 part, 2 no). */
export const GATE_MET_LABEL = "2 met · 1 partial · 2 open";

/** Real, verbatim — the card's own trailing footer row. */
export const GATE_FOOTER_NOTE =
  "Criteria were fixed when M1-A opened. Changing one is an owner decision and reopens the milestone plan.";
```

`apps/atlas/src/gate/GateCriteriaList.module.css` (new — CSS Module,
`var(--atlas-*)` only, following the exact E1/E2/C1/C7 pattern):

```css
.card {
  max-width: 66ch;
  margin-top: 20px;
  border: 1px solid var(--atlas-gate-border);
  border-radius: 14px;
  background: var(--atlas-gate-surface);
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--atlas-gate-header-border);
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-gate-label);
}

.metLabel {
  margin-left: auto;
  letter-spacing: 0.06em;
  color: var(--atlas-gate-met-label);
}

.row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  align-items: start;
  gap: 12px;
  padding: 13px 16px;
  border-bottom: 1px solid var(--atlas-gate-row-border);
}

.mark {
  margin-top: 2px;
  width: 16px;
  height: 16px;
  box-sizing: border-box;
  border-radius: 5px;
}

.markYes {
  background: var(--atlas-gate-mark-yes);
  border: 0;
}

.markPart {
  background: var(--atlas-gate-mark-part);
  border: 0;
}

.markNo {
  background: transparent;
  border: 1.5px solid var(--atlas-gate-mark-no-border);
}

.body {
  min-width: 0;
}

.title {
  font-size: 14.5px;
  font-weight: 600;
  line-height: 1.4;
  text-wrap: pretty;
}

.titleUnmet {
  color: var(--atlas-gate-title-unmet);
}

.titleDefault {
  color: var(--atlas-gate-title-default);
}

.detail {
  margin-top: 2px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--atlas-gate-detail);
  text-wrap: pretty;
}

.evidence {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
}

.evidenceYes {
  color: var(--atlas-gate-ev-yes);
}

.evidencePart {
  color: var(--atlas-gate-ev-part);
}

.evidenceNo {
  color: var(--atlas-gate-ev-no);
}

.footer {
  padding: 12px 16px;
  font-size: 12.5px;
  color: var(--atlas-gate-met-label);
}
```

`apps/atlas/src/gate/GateCriteriaList.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import {
  GATE_CRITERIA,
  GATE_FOOTER_NOTE,
  GATE_MET_LABEL,
  type GateCriterion,
  type GateCriterionMet,
} from "./fixtures";
import styles from "./GateCriteriaList.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real per-criterion
 * derivation logic (`titleColor`/`evColor`/`markBg`/`markBorder`).
 * Every semantic color is a real B2 token except the unmet-criterion
 * mark's border (`#CFC6D6`): that exact hex also happens to equal
 * `colors.navText`. Checked exhaustively against every other property
 * in that same nav-color group: `colors.navGround`, `.navTextActive`,
 * `.navTextInactive`, `.navActiveBg`, and `.navHoverBg` are all real,
 * consumed values in `DesktopShell.tsx`'s nav sidebar — but
 * `colors.navText` itself is not consumed anywhere in `apps/atlas/src`
 * (grepped directly, zero real usages), and its sibling
 * `colors.navTextDim` likewise has no real consumer — it appears only
 * inside a comment in `DesktopShell.tsx` noting that it happens to
 * equal `colors.inkMuted`, which is the value actually used there.
 * `navText`'s scoping to the dark nav sidebar rests on its name and
 * its position in this real, mostly-consumed group, not on any real
 * usage of the property itself — so it is not reused here as a
 * general-purpose light-mode border gray.
 */
const SHELL_VARS = {
  "--atlas-gate-border": colors.border,
  "--atlas-gate-surface": colors.surface,
  "--atlas-gate-header-border": colors.borderDivider[0],
  "--atlas-gate-label": colors.inkSecondary,
  "--atlas-gate-met-label": colors.inkMuted,
  "--atlas-gate-row-border": colors.borderDivider[1],
  "--atlas-gate-mark-yes": colors.success,
  "--atlas-gate-mark-part": colors.warning,
  "--atlas-gate-mark-no-border": "#CFC6D6",
  "--atlas-gate-title-unmet": colors.inkSecondary,
  "--atlas-gate-title-default": colors.ink,
  "--atlas-gate-detail": colors.inkSecondary,
  "--atlas-gate-ev-yes": colors.successText,
  "--atlas-gate-ev-part": colors.warningText,
  "--atlas-gate-ev-no": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const MARK_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.markYes,
  part: styles.markPart,
  no: styles.markNo,
};

const EVIDENCE_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.evidenceYes,
  part: styles.evidencePart,
  no: styles.evidenceNo,
};

function CriterionRow({ criterion }: { criterion: GateCriterion }) {
  const titleClass = criterion.met === "no" ? styles.titleUnmet : styles.titleDefault;
  return (
    <div className={styles.row}>
      <span className={`${styles.mark} ${MARK_CLASS[criterion.met]}`} aria-hidden="true" />
      <div className={styles.body}>
        <div className={`${styles.title} ${titleClass}`}>{criterion.title}</div>
        <div className={styles.detail}>{criterion.detail}</div>
      </div>
      <span className={`${styles.evidence} ${EVIDENCE_CLASS[criterion.met]}`}>{criterion.evidence}</span>
    </div>
  );
}

/**
 * Renders the gate's real entry-criteria card in full (header,
 * met-count summary, all 5 real criteria rows, and the card's own
 * footer note) — the gate's separate header block (title, state line,
 * Open-gate button, approver note, releases list) is a separate, later
 * slice (a future `E7B`-style candidate) whose lede/approver copy needs
 * the fictional-"Architect agent" adaptation this slice's own content
 * never requires.
 */
export function GateCriteriaList() {
  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.header}>
        entry criteria
        <span className={styles.metLabel}>{GATE_MET_LABEL}</span>
      </div>
      {GATE_CRITERIA.map((criterion) => (
        <CriterionRow key={criterion.title} criterion={criterion} />
      ))}
      <div className={styles.footer}>{GATE_FOOTER_NOTE}</div>
    </div>
  );
}

export default GateCriteriaList;
```

`apps/atlas/src/gate/GateCriteriaList.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { GateCriteriaList } from "./GateCriteriaList";
import { GATE_CRITERIA, GATE_FOOTER_NOTE, GATE_MET_LABEL } from "./fixtures";

afterEach(cleanup);

describe("GateCriteriaList", () => {
  it("renders the header label and the real met-count summary", () => {
    render(<GateCriteriaList />);
    expect(screen.getByText("entry criteria")).toBeInTheDocument();
    expect(screen.getByText(GATE_MET_LABEL)).toBeInTheDocument();
  });

  it("renders all 5 real criteria with their title, detail, and evidence", () => {
    render(<GateCriteriaList />);
    for (const criterion of GATE_CRITERIA) {
      expect(screen.getByText(criterion.title)).toBeInTheDocument();
      expect(screen.getByText(criterion.detail)).toBeInTheDocument();
      expect(screen.getByText(criterion.evidence)).toBeInTheDocument();
    }
  });

  it("renders the card's own real footer note", () => {
    render(<GateCriteriaList />);
    expect(screen.getByText(GATE_FOOTER_NOTE)).toBeInTheDocument();
  });

  it("matches the real met-count breakdown: 2 yes, 1 part, 2 no", () => {
    const counts = { yes: 0, part: 0, no: 0 };
    for (const criterion of GATE_CRITERIA) {
      counts[criterion.met] += 1;
    }
    expect(counts).toEqual({ yes: 2, part: 1, no: 2 });
  });

  it("dims the title only for unmet ('no') criteria; met and partial criteria use the default ink title color", () => {
    render(<GateCriteriaList />);
    const unmet = screen.getByText("A.0 through A.7 accepted");
    const met = screen.getByText("Frozen-presentation contract holds");
    const partial = screen.getByText("Every owner decision carries a fidelity check");
    expect(unmet.className).toContain("titleUnmet");
    expect(met.className).toContain("titleDefault");
    expect(partial.className).toContain("titleDefault");
  });

  it("colors evidence text by met status: yes -> successText, part -> warningText, no -> inkFaint", () => {
    render(<GateCriteriaList />);
    const yesEvidence = screen.getByText("A.1 · 9d3e1a2");
    const partEvidence = screen.getByText("DF-2 pending");
    const noEvidence = screen.getByText("2 of 8 accepted");
    expect(yesEvidence.className).toContain("evidenceYes");
    expect(partEvidence.className).toContain("evidencePart");
    expect(noEvidence.className).toContain("evidenceNo");
  });

  it("sets the border, success-mark, and warning-mark CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.success).toBe("#2E9B72");
    expect(colors.warning).toBe("#E0A32E");
    const { container } = render(<GateCriteriaList />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-gate-mark-yes")).toBe(colors.success);
    expect(root.style.getPropertyValue("--atlas-gate-mark-part")).toBe(colors.warning);
  });

  it("disclosed literal's identity: colors.navText really does equal the mark-no-border literal, and colors.border (a different token) is really different from it", () => {
    // Guards against the exact class of defect the -01 candidate's
    // correction introduced: assert the two token facts this
    // component's own disclosure depends on, not just eyeball them.
    expect(colors.navText).toBe("#CFC6D6");
    expect(colors.border).not.toBe(colors.navText);
    const { container } = render(<GateCriteriaList />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-gate-mark-no-border")).toBe(colors.navText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<GateCriteriaList />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `DesktopShell` or `App.tsx` —
   standalone, exactly like every prior Wave-E component.
2. This slice does not import from any `thread/`, `decision/`,
   `crash/`, or `performance/` file — a fully independent new
   directory.
3. Every color is a real B2 token except the one explicitly disclosed
   (`#CFC6D6`), checked directly against `colors.ts` — every other
   property in the same nav-color group was checked one at a time
   (see the table in Scope above) for whether it has a real consumer,
   not partially enumerated.
4. No fictional "Architect agent" persona appears anywhere in this
   slice's rendered copy — the card's content names no persona at all.
5. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, `apps/atlas/src/decision/`,
   `apps/atlas/src/crash/`, or `apps/atlas/src/performance/` is
   modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/gate/fixtures.ts` (new)
- `apps/atlas/src/gate/GateCriteriaList.module.css` (new)
- `apps/atlas/src/gate/GateCriteriaList.tsx` (new)
- `apps/atlas/src/gate/GateCriteriaList.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, and everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/decision/`, `apps/atlas/src/crash/`,
`apps/atlas/src/performance/`, and `apps/atlas/src/tokens/` are
untouched.

The 9 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 90 total after this slice (81 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 CrashCard tests, 7 thread tests, 7
PacketHeader tests, 6 PerformanceHeader tests, 5 WeeklyWindowStrip
tests, 6 PerfRecordsList tests, 5 mobile-shell tests, 10 desktop-shell
tests — + 9 new). `npm run build` must still succeed;
`GateCriteriaList` is not expected to appear in the `dist/` bundle,
matching every prior standalone slice's own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `GateCriteriaList` renders the gate's real
   entry-criteria card anatomy in full (header, met-count summary, all
   5 real criteria rows, and the card's own footer note) using real B2
   tokens with exactly one disclosed, exhaustively-checked literal.
2. **Operating and threat model:** a trusted local dev box; fully
   read-only — this card has no interactive element in the reference
   file to begin with.
3. **Explicit exclusions:** the gate header (title, state line,
   `Open gate` button, approver note, releases list — a future `E7B`
   candidate needing fictional-persona adaptation), any wiring into
   `DesktopShell`/`App.tsx`, the mobile bottom-sheet variant.
4. **Assurance level:** practical component-rendering correctness with
   every criterion and the footer note transcribed verbatim, and every
   color either a real token or one exhaustively disclosed literal —
   proportionate to a read-only view with no data dependency and no
   consumer yet.
5. **Acceptance proof:** the 9 named tests, the existing 81 `apps/atlas`
   tests continuing to pass (90 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color a real token property except the
   one disclosed literal; no import of any other component-family
   module.
7. **Proportionality ceiling:** one list component, one fixtures
   module, one CSS Module; no gate header, no button, no approver note,
   no releases list, no wiring, no mobile variant.
8. **Stop and escalation rule:** the gate header/button/approver-note/
   releases-list slice, and wiring `GateCriteriaList` into
   `DesktopShell`'s nav/content pane, are each new, separately reviewed
   work — not decided implicitly here. Any adaptation of the fictional
   "Architect agent" references in the deferred gate-header content
   must follow Wave C's own established real-mechanism-substitution
   discipline (C3/C4), not be invented ad hoc when that slice is
   written. A discovered proof/contract defect against a frozen slice
   terminally returns that slice. One planning correction and one
   implementation correction are the maximum available.
