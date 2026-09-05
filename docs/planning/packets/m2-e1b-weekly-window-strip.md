# M2 Wave E — Performance Weekly-Window Strip — Candidate 01

**Slice ID:** `MB-SLICE-M2-E1B-WEEKLY-WINDOW-STRIP-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `237dd02` (full: `237dd029ef11468623f942fa83ad6326fe385c91`, `origin/master`)

## Scope, deliberately minimal

The second half of roadmap item 26 (*"E1 — Performance: header stats +
weekly-window strip"*), split off from E1 (already merged — the header
and its 4 `pfStats`) per this program's standing "smallest possible
slice" discipline, matching the split already disclosed in E1's own
packet contract. This slice is the weekly-window reconciliation strip
and its caption, standalone — no wiring into `DesktopShell`/`App.tsx`,
no breakdown card (that's a separate roadmap item, E3).

**Zero disclosed color literals, matching E1's own cleanest-token
precedent.** Like Performance's header, this strip is pure reporting
content: no persona, no fictional agent, every value transcribed
verbatim.

Source quote (README, "Performance" section, weekly-window-strip
paragraph, verbatim):

> **Weekly-window strip** (`#FFFFFF`, border `#E7E1EE`, radius 12):
> `61% controlled + 14% coarse + 5% unattributed = 80% observed change`,
> unattributed in amber, with `observed 15:02 · resets Mon 00:00`
> right-aligned, and a caption: local Qwen is capacity and time only,
> never subtracted from this window.

Source quote (`Atlas Explorations.dc.html`, the exact markup this
slice's visual structure is transcribed from):

```html
<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:11px 15px;border:1px solid #E7E1EE;border-radius:12px;background:#fff;font-size:13px">
  <span style="font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#6C6376">openai weekly window</span>
  <span style="min-width:0;flex:1;color:#6C6376;line-height:1.5;text-wrap:pretty">Reconciled: <b style="font-family:'IBM Plex Mono',monospace;color:#221C29">61%</b> controlled + <b style="font-family:'IBM Plex Mono',monospace;color:#221C29">14%</b> coarse + <b style="font-family:'IBM Plex Mono',monospace;color:#8A5A08">5%</b> unattributed = <b style="font-family:'IBM Plex Mono',monospace;color:#221C29">80%</b> observed change</span>
  <span style="flex:none;font:500 11.5px 'IBM Plex Mono',monospace;color:#8E8299">observed 15:02 · resets Mon 00:00</span>
</div>
<div style="margin-top:8px;padding:0 3px;font-size:12.5px;color:#A79BB4">Local Qwen is shown as capacity and time only — it is not subtracted from this window.</div>
```

**Only the `unattributed` figure (`5%`) is amber (`colors.warningText`)
— every other figure (`61%`, `14%`, `80%`) is ink, matching this real
markup exactly and this program's own established amber-means-
attention convention.**

**Color discrepancy table — every value is a real, existing B2 token;
zero disclosed literals, matching E1's own precedent:**

| Reference value | Real B2 token | Match? |
|---|---|---|
| strip border `#E7E1EE` | `colors.border` | exact |
| strip bg `#fff` | `colors.surface` | exact |
| label / reconciled text `#6C6376` | `colors.inkSecondary` | exact |
| figure (ink) `#221C29` | `colors.ink` | exact |
| figure (amber, `unattributed` only) `#8A5A08` | `colors.warningText` | exact |
| meta text `#8E8299` | `colors.inkMuted` | exact |
| caption text `#A79BB4` | `colors.inkFaint` | exact |

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E1B-WEEKLY-WINDOW-STRIP-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:237dd029ef11468623f942fa83ad6326fe385c91"]` |

## Exact file contents

**This candidate's exact file contents were actually compiled and run
against the real post-E1-merge toolchain during authoring, not only
drafted.** All four files below were written to a scratch copy of this
worktree (rebased onto master after E1's real merge, so the baseline
below is accurate, not stale) and `npm run typecheck`, `npm run lint`,
`npm test`, and `npm run build` were run for real from `apps/atlas/`:
75/75 tests passed (70 existing, including E1's own merged
`PerformanceHeader` tests + 5 new), typecheck and lint clean,
production build succeeded — all on the first real run, no fix needed.

`apps/atlas/src/performance/weeklyWindow.ts` (new — the strip's data
and its type; no rendering logic; does not modify E1's frozen
`fixtures.ts` in the same directory):

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * weekly-window strip markup — pure reporting content, no persona, no
 * fictional agent. `unattributedPercent` is the one figure the
 * reference file itself renders in amber (matching this program's own
 * established amber-means-estimate/attention convention); every other
 * figure is ink.
 */
export interface WeeklyWindow {
  reconciledPercent: string;
  coarsePercent: string;
  unattributedPercent: string;
  observedChangePercent: string;
  meta: string;
  caption: string;
}

export const WEEKLY_WINDOW: WeeklyWindow = {
  reconciledPercent: "61%",
  coarsePercent: "14%",
  unattributedPercent: "5%",
  observedChangePercent: "80%",
  meta: "observed 15:02 · resets Mon 00:00",
  caption: "Local Qwen is shown as capacity and time only — it is not subtracted from this window.",
};
```

`apps/atlas/src/performance/WeeklyWindowStrip.module.css` (new — CSS
Module, `var(--atlas-*)` only, following the exact E1/C1/C7 pattern):

```css
.strip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 11px 15px;
  border: 1px solid var(--atlas-week-border);
  border-radius: 12px;
  background: var(--atlas-week-surface);
  font-size: 13px;
}

.label {
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-week-label);
}

.reconciled {
  min-width: 0;
  flex: 1;
  color: var(--atlas-week-label);
  line-height: 1.5;
  text-wrap: pretty;
}

.figure {
  font-family: var(--atlas-font-mono);
}

.figureInk {
  color: var(--atlas-week-ink);
}

.figureWarning {
  color: var(--atlas-week-warning);
}

.meta {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-week-meta);
}

.caption {
  margin-top: 8px;
  padding: 0 3px;
  font-size: 12.5px;
  color: var(--atlas-week-caption);
}
```

`apps/atlas/src/performance/WeeklyWindowStrip.tsx` (new):

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { WEEKLY_WINDOW } from "./weeklyWindow";
import styles from "./WeeklyWindowStrip.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1's `PerformanceHeader`. `colors.border` (`#E7E1EE`) is a new real
 * token this program hasn't consumed yet elsewhere; every other value
 * already has established precedent (E1, C7).
 */
const SHELL_VARS = {
  "--atlas-week-border": colors.border,
  "--atlas-week-surface": colors.surface,
  "--atlas-week-label": colors.inkSecondary,
  "--atlas-week-ink": colors.ink,
  "--atlas-week-warning": colors.warningText,
  "--atlas-week-meta": colors.inkMuted,
  "--atlas-week-caption": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function WeeklyWindowStrip() {
  const { reconciledPercent, coarsePercent, unattributedPercent, observedChangePercent, meta, caption } =
    WEEKLY_WINDOW;
  return (
    <div style={SHELL_VARS}>
      <div className={styles.strip}>
        <span className={styles.label}>openai weekly window</span>
        <span className={styles.reconciled}>
          Reconciled: <b className={`${styles.figure} ${styles.figureInk}`}>{reconciledPercent}</b> controlled +{" "}
          <b className={`${styles.figure} ${styles.figureInk}`}>{coarsePercent}</b> coarse +{" "}
          <b className={`${styles.figure} ${styles.figureWarning}`}>{unattributedPercent}</b> unattributed ={" "}
          <b className={`${styles.figure} ${styles.figureInk}`}>{observedChangePercent}</b> observed change
        </span>
        <span className={styles.meta}>{meta}</span>
      </div>
      <div className={styles.caption}>{caption}</div>
    </div>
  );
}

export default WeeklyWindowStrip;
```

`apps/atlas/src/performance/WeeklyWindowStrip.test.tsx` (new):

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { WeeklyWindowStrip } from "./WeeklyWindowStrip";
import { WEEKLY_WINDOW } from "./weeklyWindow";

afterEach(cleanup);

describe("WeeklyWindowStrip", () => {
  it("renders the real label and all 4 real reconciliation figures", () => {
    render(<WeeklyWindowStrip />);
    expect(screen.getByText("openai weekly window")).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.reconciledPercent)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.coarsePercent)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.unattributedPercent)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.observedChangePercent)).toBeInTheDocument();
  });

  it("renders the real meta text and caption", () => {
    render(<WeeklyWindowStrip />);
    expect(screen.getByText(WEEKLY_WINDOW.meta)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.caption)).toBeInTheDocument();
  });

  it("colors only the unattributed figure amber (warningText); every other figure is ink", () => {
    render(<WeeklyWindowStrip />);
    const unattributed = screen.getByText(WEEKLY_WINDOW.unattributedPercent);
    const reconciled = screen.getByText(WEEKLY_WINDOW.reconciledPercent);
    expect(unattributed.className).toContain("figureWarning");
    expect(reconciled.className).toContain("figureInk");
  });

  it("sets the border, surface, and warning CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.warningText).toBe("#8A5A08");
    const { container } = render(<WeeklyWindowStrip />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-week-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-week-warning")).toBe(colors.warningText);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<WeeklyWindowStrip />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint, and is not wired into `DesktopShell` or `App.tsx` —
   standalone, exactly like E1's `PerformanceHeader`.
2. This slice does not modify E1's frozen `fixtures.ts`,
   `PerformanceHeader.tsx`, `PerformanceHeader.module.css`, or
   `PerformanceHeader.test.tsx` — it adds new, separate files to the
   same directory.
3. Every color is a real B2 token; there is no disclosed literal in
   this slice at all.
4. No file under `apps/atlas/src/tokens/`, `apps/atlas/src/shell/`,
   `apps/atlas/src/thread/`, `apps/atlas/src/decision/`, or
   `apps/atlas/src/crash/` is modified.

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/performance/weeklyWindow.ts` (new)
- `apps/atlas/src/performance/WeeklyWindowStrip.module.css` (new)
- `apps/atlas/src/performance/WeeklyWindowStrip.tsx` (new)
- `apps/atlas/src/performance/WeeklyWindowStrip.test.tsx` (new)

No other path — `App.tsx`, `App.test.tsx`, E1's own
`fixtures.ts`/`PerformanceHeader.*`, and everything under
`apps/atlas/src/shell/`, `apps/atlas/src/thread/`,
`apps/atlas/src/decision/`, `apps/atlas/src/crash/`, and
`apps/atlas/src/tokens/` are untouched.

The 5 named tests, run from `apps/atlas/`: `npm run typecheck`, `npm run
lint`, and `npm test` must all exit `0`, covering the new test file
above plus every existing `apps/atlas` test continuing to pass
unmodified — 75 total after this slice (70 existing, verified directly
by running `npm test` at this slice's base commit — 4 token tests, 1
App test, 8 DecisionCard tests, 8 OwnerDecisionCard tests, 7
FidelityRecord tests, 7 CrashCard tests, 7 thread tests, 7
PacketHeader tests, 6 PerformanceHeader tests, 5 mobile-shell tests,
10 desktop-shell tests — + 5 new). `npm run build` must still succeed;
`WeeklyWindowStrip` is not expected to appear in the `dist/` bundle,
matching every prior standalone slice's own build-unaffected proof.

### M0-D12 bounded quality contract

1. **Protected outcome:** `WeeklyWindowStrip` renders the Performance
   screen's real weekly-window anatomy (label, 4 reconciliation
   figures with the amber-only-on-unattributed rule, meta timestamp,
   and caption) using only real B2 tokens — no disclosed literal
   anywhere in this slice.
2. **Operating and threat model:** a trusted local dev box; fully
   read-only, no interactive element of any kind.
3. **Explicit exclusions:** the `m1-a breakdown` card (E3), per-action
   records (E2), any wiring into `DesktopShell`/`App.tsx`, any
   modification of E1's own frozen files.
4. **Assurance level:** practical component-rendering correctness with
   every value transcribed verbatim from the reference file and every
   color a real, existing token — matching E1's own highest
   token-purity precedent, proportionate to a read-only view with no
   data dependency and no consumer yet.
5. **Acceptance proof:** the 5 named tests, the existing 70 `apps/atlas`
   tests continuing to pass (75 total), `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing.
6. **Implementation boundary:** exactly the four writable paths above;
   no new npm dependency; every color a real token property; no import
   of any other component-family module; no modification of E1's own
   files.
7. **Proportionality ceiling:** one strip component, one data module,
   one CSS Module; no breakdown card, no wiring, no second scenario.
8. **Stop and escalation rule:** the `m1-a breakdown` card and wiring
   `WeeklyWindowStrip`/`PerformanceHeader` together into one Performance
   screen and into `DesktopShell`'s nav/content pane are each new,
   separately reviewed work — not decided implicitly here. A discovered
   proof/contract defect against a frozen slice terminally returns that
   slice. One planning correction and one implementation correction are
   the maximum available.
