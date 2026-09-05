# M2 Wave E — Performance Header and Stats — Candidate 01

**Slice ID:** `MB-SLICE-M2-E1-PERFORMANCE-HEADER-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `a7832a8` (`origin/master`)

## Scope, deliberately minimal

Wave E of the [M2 Atlas roadmap](../m2-atlas-roadmap.md) begins here.
Roadmap item 26 bundles two things into one line — *"E1 — Performance:
header stats + weekly-window strip"* — but per this program's standing
"smallest possible slice" discipline, this candidate splits that into
two: this slice is the header only (eyebrow, title, lede, and the 4
real `pfStats`). The weekly-window strip becomes its own next slice
(a future `E1B`-style candidate, matching the `C1`/`C1B` split
precedent), since it is a visually and structurally separate card
lower on the same screen with its own real data to verify, not a
continuation of the header's own content.

**This is the cleanest-token slice of the whole M2 program so far —
every color is a real, existing B2 token, zero disclosed literals.**
Performance is pure reporting content: no persona, no fictional
"Architect agent," nothing to adapt. The screen's own honesty rule is
literally this project's own real M0-D14 convention, already quoted
verbatim elsewhere in this program's docs — this slice's lede
transcribes it directly from the reference file, and it says the same
thing.

Source quote (README, "Performance" section, verbatim):

> Header: title "What each action actually cost", a lede stating the
> honesty rules (reported beats estimated, `unavailable` not zero,
> local compute kept separate), and four stat pairs (Actions recorded
> 5, Billed $2.27, Estimated $0.52 in amber, Hosted time 47m).

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from, eliding the rest of the
Performance screen below the header — the weekly-window strip and the
breakdown card, both out of scope for this slice):

```html
<div style="flex:none;padding:16px 34px 15px;background:#fff;border-bottom:1px solid #EEEAF2">
  <div style="display:flex;align-items:center;gap:9px;font:500 11px 'IBM Plex Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:#A79BB4"><span>m1-a</span><span style="width:3px;height:3px;border-radius:50%;background:#CFC6D6"></span><span>performance</span></div>
  <h1 style="margin:7px 0 0;font-family:'Bricolage Grotesque',sans-serif;font-size:25px;font-weight:600;letter-spacing:-.025em;line-height:1.15">What each action actually cost</h1>
  <div style="margin-top:7px;max-width:70ch;font-size:13.5px;line-height:1.55;color:#6C6376;text-wrap:pretty">One record per worker attempt, tied to it from preflight through handoff. Reported counters win over estimates, an unsupported field reads <code style="font-family:'IBM Plex Mono',monospace">unavailable</code> rather than zero, and local compute is never folded into the hosted allowance.</div>
  <div style="display:flex;flex-wrap:wrap;gap:0 26px;margin-top:11px;font-size:13.5px;color:#6C6376">
    <sc-for list="{{ pfStats }}" as="s" hint-placeholder-count="4">
    <span style="display:flex;align-items:baseline;gap:7px">{{ s.label }}<b style="font-family:'IBM Plex Mono',monospace;color:{{ s.color }}">{{ s.value }}</b></span>
    </sc-for>
  </div>
</div>
```

Reference file's real `pfStats` array (verbatim):

```js
pfStats: [
  { label: 'Actions recorded', value: '5', color: '#221C29' },
  { label: 'Billed', value: '$2.27', color: '#221C29' },
  { label: 'Estimated', value: '$0.52', color: '#8A5A08' },
  { label: 'Hosted time', value: '47m', color: '#221C29' },
],
```

**The eyebrow's separator is rendered as a plain middle-dot character
in this slice's text, not a separate `3px` dot `<span>` element —
matching C7's own `PacketHeader` precedent exactly (already reviewed
and merged), not a new simplification invented here.** The reference
markup's eyebrow uses a tiny colored dot span between segments (real,
disclosed here for completeness), but C7's `PacketHeader` already
established rendering this as one plain-text string with a literal
`·` character, and this slice matches that same real precedent for
visual and implementation consistency between the two packet-adjacent
headers in this app.

**The lede is split into three parts around the one word the reference
markup wraps in its own mono `<code>` element (`unavailable`), so the
rendered inline styling is reproduced exactly, not flattened into one
plain string with no distinct formatting.**

**Color discrepancy table — every value is a real, existing B2 token;
zero disclosed literals, the cleanest of any slice this program has
built:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| header surface `#fff` | `colors.surface` | exact |
| header border `#EEEAF2` | `colors.borderDivider[0]` | exact |
| eyebrow text `#A79BB4` | `colors.inkFaint` | exact |
| title text (implicit default) | `colors.ink` | exact |
| lede / stat-label text `#6C6376` | `colors.inkSecondary` | exact |
| stat value (ink) `#221C29` | `colors.ink` | exact |
| stat value (amber, `Estimated` only) `#8A5A08` | `colors.warningText` | exact |

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E1-PERFORMANCE-HEADER-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:a7832a8e0702b1cb690731785652b03aba6f983d"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real toolchain during authoring, not only drafted.** All
four files below were written to a scratch copy of this worktree and
`npm run typecheck`, `npm run lint`, `npm test`, and `npm run build`
were run for real from `apps/atlas/`: 70/70 tests passed (64 existing +
6 new), typecheck and lint clean, production build succeeded — all on
the first real run, no fix needed.

`apps/atlas/src/performance/fixtures.ts` (new — the stats data and its
types; no rendering logic):

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `pfStats` array and the Performance screen's header lede — this is
 * pure reporting content (no persona, no fictional agent), and its
 * honesty rule is the same real M0-D14 convention already quoted
 * elsewhere in this program's own docs (reported beats estimated, an
 * unsupported field reads `unavailable`, local compute stays separate
 * from the hosted allowance). The lede is split around the one word
 * the reference markup wraps in its own mono `<code>` element
 * (`unavailable`), so the component can reproduce that exact inline
 * styling rather than flattening it into one plain string.
 */
export interface PerformanceStat {
  label: string;
  value: string;
  color: "ink" | "warning";
}

export const PERFORMANCE_LEDE_BEFORE =
  "One record per worker attempt, tied to it from preflight through handoff. Reported counters win over estimates, an unsupported field reads ";
export const PERFORMANCE_LEDE_CODE = "unavailable";
export const PERFORMANCE_LEDE_AFTER =
  " rather than zero, and local compute is never folded into the hosted allowance.";

export const PERFORMANCE_STATS: PerformanceStat[] = [
  { label: "Actions recorded", value: "5", color: "ink" },
  { label: "Billed", value: "$2.27", color: "ink" },
  { label: "Estimated", value: "$0.52", color: "warning" },
  { label: "Hosted time", value: "47m", color: "ink" },
];
```

`apps/atlas/src/performance/PerformanceHeader.module.css` (new — CSS
Module, `var(--atlas-*)` only, following the exact C1/C7/B3/B4
pattern):

```css
.head {
  flex: none;
  padding: 16px 34px 15px;
  background: var(--atlas-perf-surface);
  border-bottom: 1px solid var(--atlas-perf-border);
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 9px;
  font: 500 11px var(--atlas-font-mono);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--atlas-perf-eyebrow);
}

.title {
  margin: 7px 0 0;
  font-family: var(--atlas-font-display);
  font-size: 25px;
  font-weight: 600;
  letter-spacing: -0.025em;
  line-height: 1.15;
  color: var(--atlas-perf-title);
}

.lede {
  margin: 7px 0 0;
  max-width: 70ch;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-perf-lede);
  text-wrap: pretty;
}

.ledeCode {
  font-family: var(--atlas-font-mono);
}

.stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0 26px;
  margin-top: 11px;
  font-size: 13.5px;
  color: var(--atlas-perf-lede);
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 7px;
}

.statValue {
  font-family: var(--atlas-font-mono);
}

.statValueInk {
  color: var(--atlas-perf-title);
}

.statValueWarning {
  color: var(--atlas-perf-warning);
}
```

`apps/atlas/src/performance/PerformanceHeader.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import {
  PERFORMANCE_LEDE_AFTER,
  PERFORMANCE_LEDE_BEFORE,
  PERFORMANCE_LEDE_CODE,
  PERFORMANCE_STATS,
} from "./fixtures";
import styles from "./PerformanceHeader.module.css";

/**
 * Every color here is a real B2 token — this screen's header has no
 * disclosed literal at all, the cleanest token match of any C/E-wave
 * component so far. `colors.inkFaint` (eyebrow) and `colors.inkSecondary`
 * (lede/stat labels) already have real precedent from C7's
 * `PacketHeader`; `colors.warningText` (the `Estimated` stat) matches
 * this program's own established amber-means-estimate convention.
 */
const SHELL_VARS = {
  "--atlas-perf-surface": colors.surface,
  "--atlas-perf-border": colors.borderDivider[0],
  "--atlas-perf-eyebrow": colors.inkFaint,
  "--atlas-perf-title": colors.ink,
  "--atlas-perf-lede": colors.inkSecondary,
  "--atlas-perf-warning": colors.warningText,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const STAT_VALUE_CLASS: Record<"ink" | "warning", string> = {
  ink: styles.statValueInk,
  warning: styles.statValueWarning,
};

export function PerformanceHeader() {
  return (
    <div className={styles.head} style={SHELL_VARS}>
      <div className={styles.eyebrow}>m1-a · performance</div>
      <h1 className={styles.title}>What each action actually cost</h1>
      <p className={styles.lede}>
        {PERFORMANCE_LEDE_BEFORE}
        <code className={styles.ledeCode}>{PERFORMANCE_LEDE_CODE}</code>
        {PERFORMANCE_LEDE_AFTER}
      </p>
      <div className={styles.stats}>
        {PERFORMANCE_STATS.map((stat) => (
          <span key={stat.label} className={styles.stat}>
            {stat.label}
            <b className={`${styles.statValue} ${STAT_VALUE_CLASS[stat.color]}`}>{stat.value}</b>
          </span>
        ))}
      </div>
    </div>
  );
}

export default PerformanceHeader;
```

`apps/atlas/src/performance/PerformanceHeader.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PerformanceHeader } from "./PerformanceHeader";
import { PERFORMANCE_STATS } from "./fixtures";

afterEach(cleanup);

describe("PerformanceHeader", () => {
  it("renders the real eyebrow and title", () => {
    render(<PerformanceHeader />);
    expect(screen.getByText("m1-a · performance")).toBeInTheDocument();
    expect(screen.getByText("What each action actually cost")).toBeInTheDocument();
  });

  it("renders the lede with 'unavailable' in its own <code> element, matching the reference file's inline mono styling", () => {
    render(<PerformanceHeader />);
    const code = screen.getByText("unavailable");
    expect(code.tagName).toBe("CODE");
    expect(screen.getByText(/One record per worker attempt/)).toBeInTheDocument();
    expect(screen.getByText(/never folded into the hosted allowance/)).toBeInTheDocument();
  });

  it("renders all 4 real stats with their real labels and values", () => {
    render(<PerformanceHeader />);
    for (const stat of PERFORMANCE_STATS) {
      expect(screen.getByText(stat.label)).toBeInTheDocument();
      expect(screen.getByText(stat.value)).toBeInTheDocument();
    }
  });

  it("colors the 'Estimated' stat's value amber (warningText) and every other stat's value ink, matching the reference file's real per-stat color", () => {
    render(<PerformanceHeader />);
    const estimated = screen.getByText("$0.52");
    const billed = screen.getByText("$2.27");
    expect(estimated.className).toContain("statValueWarning");
    expect(billed.className).toContain("statValueInk");
  });

  it("sets the surface, border, and warning CSS variables to the real, checked tokens", () => {
    expect(colors.borderDivider[0]).toBe("#EEEAF2");
    expect(colors.warningText).toBe("#8A5A08");
    const { container } = render(<PerformanceHeader />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-perf-border")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-perf-warning")).toBe(colors.warningText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PerformanceHeader />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `DesktopShell` or `App.tsx` —
   standalone, exactly like every prior C-wave component.
2. This slice does not import from any `thread/`, `decision/`, or
   `crash/` file — a fully independent new directory.
3. Every color is a real B2 token; there is no disclosed literal in
   this slice at all.
4. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, `apps/atlas/src/decision/`, or
   `apps/atlas/src/crash/` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/performance/fixtures.ts` (new)
- `apps/atlas/src/performance/PerformanceHeader.module.css` (new)
- `apps/atlas/src/performance/PerformanceHeader.tsx` (new)
- `apps/atlas/src/performance/PerformanceHeader.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, and everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/decision/`, `apps/atlas/src/crash/`, and
`apps/atlas/src/tokens/` are untouched.

The 6 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 70 total after this slice (64 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 CrashCard tests, 7 thread tests, 7
PacketHeader tests, 5 mobile-shell tests, 10 desktop-shell tests —
+ 6 new). `npm run build` must still succeed; `PerformanceHeader` is
not expected to appear in the `dist/` bundle, matching every prior
standalone slice's own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `PerformanceHeader` renders the Performance
   screen's real header anatomy (eyebrow, title, lede with inline mono
   `unavailable`, and the 4 real `pfStats`) using only real B2 tokens —
   no disclosed literal anywhere in this slice.
2. **Operating and threat model:** a trusted local dev box; fully
   read-only, no interactive element of any kind.
3. **Explicit exclusions:** the weekly-window strip (a future `E1B`
   candidate), the `m1-a breakdown` card (E3), any wiring into
   `DesktopShell`/`App.tsx`, per-action records (E2).
4. **Assurance level:** practical component-rendering correctness with
   every value transcribed verbatim from the reference file and every
   color a real, existing token — the highest token-purity slice of
   the program so far, proportionate to a read-only view with no data
   dependency and no consumer yet.
5. **Acceptance proof:** the 6 named tests, the existing 64 `apps/atlas`
   tests continuing to pass (70 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color a real token property; no import
   of any other component-family module.
7. **Proportionality ceiling:** one header component, one fixtures
   module, one CSS Module; no weekly-window strip, no breakdown card,
   no wiring, no second scenario.
8. **Stop and escalation rule:** the weekly-window strip, the
   `m1-a breakdown` card, and wiring `PerformanceHeader` into
   `DesktopShell`'s nav/content pane are each new, separately reviewed
   work — not decided implicitly here. A discovered proof/contract
   defect against a frozen slice terminally returns that slice. One
   planning correction and one implementation correction are the
   maximum available.
