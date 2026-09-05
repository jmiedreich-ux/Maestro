# M2 Wave E — Contention Card — Candidate 01

**Slice ID:** `MB-SLICE-M2-E5-CONTENTION-CARD-01`
**Status:** `Draft — Pending Decision Fidelity Review`
**Base:** `0f329a8` (full: `0f329a80970f8b7d7c22a81ddc710d09e1d7b10c`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 30, *"E5 — Agents: contention/lock card."* The final Wave
E item. A new, standalone `ContentionCard` renders the reference
file's real contention/lock card in full: header ("contention" label,
"no overlap" status), all 3 real `CONTENTION` rows, and the card's own
real trailing caveat. No wiring into `DesktopShell`/`App.tsx`, no
wiring into `AgentsRoster` (E4) either — this is its own standalone
component, matching this program's own established pattern of not
composing components across slices until a dedicated wiring slice.

**No real-vs-fictional persona issue here** — checked directly: the
real `CONTENTION` array's `holder` values are `Terra`, `frozen`, and
`reserved`; there is no `Architect agent` or any other fictional
persona anywhere in this data.

## Source quote

`Atlas Explorations.dc.html`'s real markup for the contention card,
verbatim:

```html
<div style="margin-top:16px;border:1px solid #E7E1EE;border-radius:14px;background:#fff;overflow:hidden">
  <div style="display:flex;align-items:center;gap:10px;padding:12px 15px;border-bottom:1px solid #EEEAF2;font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.11em;text-transform:uppercase;color:#6C6376">contention<span style="margin-left:auto;letter-spacing:.06em;color:#1F6B4E">no overlap</span></div>
  <sc-for list="{{ contention }}" as="c" hint-placeholder-count="3">
  <div style="display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:baseline;gap:10px 14px;padding:11px 15px;border-bottom:1px solid #F3F0F6">
    <div style="min-width:0"><div style="font:500 13px 'IBM Plex Mono',monospace;color:#221C29;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ c.path }}</div><div style="margin-top:2px;font-size:12.5px;color:#6C6376">{{ c.note }}</div></div>
    <span style="flex:none;padding:3px 8px;border-radius:6px;background:{{ c.bg }};color:{{ c.color }};font:600 10.5px 'IBM Plex Mono',monospace;letter-spacing:.07em;text-transform:uppercase">{{ c.holder }}</span>
  </div>
  </sc-for>
  <div style="padding:11px 15px;font-size:12.5px;line-height:1.5;color:#8E8299;text-wrap:pretty">Locks are assigned at dispatch, so two agents can never be told to write the same file. A packet that needs a locked file waits rather than merges.</div>
</div>
```

Real per-row derivation logic and the real `CONTENTION` array
(verbatim):

```js
contention: CONTENTION.map(([path, note, holder, k]) => ({ path, note, holder,
  bg: k === 'run' ? '#EBE4FF' : '#F2EEF8', color: k === 'run' ? '#4A28CC' : '#6C6376' })),
```

```js
const CONTENTION = [
  ['runtime/package.ts', 'Write lock held for the length of A.2.', 'Terra', 'run'],
  ['core/identity.ts', 'Frozen by the A.1 contract — no packet may write it.', 'frozen', 'wait'],
  ['overlay/view.tsx', 'Reserved for A.3, released when A.2 is accepted.', 'reserved', 'wait'],
];
```

## Color discrepancy table — every value is a real, existing B2 token; zero disclosed literals

| Reference value | `colors.ts` match | Verdict |
|---|---|---|
| card border `#E7E1EE` | `colors.border` | real token |
| card surface `#fff` | `colors.surface` | real token |
| header border-bottom `#EEEAF2` | `colors.borderDivider[0]` | real token |
| header label `#6C6376` | `colors.inkSecondary` | real token |
| "no overlap" status `#1F6B4E` | `colors.successText` | real token |
| row border-bottom `#F3F0F6` | `colors.borderDivider[1]` | real token |
| path text `#221C29` | `colors.ink` | real token |
| note text `#6C6376` | `colors.inkSecondary` (same token, reused) | real token |
| `run` badge bg `#EBE4FF` | `colors.accentWash[0]` | real token |
| `run` badge ink `#4A28CC` | `colors.accentHover` | real token |
| `wait` badge bg `#F2EEF8` | `colors.neutralChip` | real token |
| `wait` badge ink `#6C6376` | `colors.inkSecondary` (same token, reused) | real token |
| caveat text `#8E8299` | `colors.inkMuted` | real token |

**All 13 real, existing B2 tokens — zero disclosed literals**, matching
E1/E1B/E2/E2B/E3's own precedent (unlike Gate/History/E4, which needed
disclosures).

## Guards

1. This slice adds 4 new files only — no wiring into
   `DesktopShell`/`App.tsx`, no wiring into `AgentsRoster` (E4), no
   modification of any already-merged file.
2. Every field and every row of the real `CONTENTION` array is
   transcribed verbatim; no persona substitution or other correction
   was needed for this slice, unlike E3/E4.
3. Every color is a real B2 token; zero disclosed literals.

## `apps/atlas/src/agents/contention.ts` (new)

```ts
/**
 * Transcribed verbatim from `Atlas Explorations.dc.html`'s real
 * `CONTENTION` array and `contention` derivation function — pure
 * reporting content, no persona, no fictional agent. `holder` values
 * (`Terra`, `frozen`, `reserved`) are all real/neutral; there is no
 * `Architect agent` in this data at all.
 */
export type ContentionStyleKey = "run" | "wait";

export interface ContentionEntry {
  path: string;
  note: string;
  holder: string;
  styleKey: ContentionStyleKey;
}

export const CONTENTION: ContentionEntry[] = [
  {
    path: "runtime/package.ts",
    note: "Write lock held for the length of A.2.",
    holder: "Terra",
    styleKey: "run",
  },
  {
    path: "core/identity.ts",
    note: "Frozen by the A.1 contract — no packet may write it.",
    holder: "frozen",
    styleKey: "wait",
  },
  {
    path: "overlay/view.tsx",
    note: "Reserved for A.3, released when A.2 is accepted.",
    holder: "reserved",
    styleKey: "wait",
  },
];

export const CONTENTION_CAVEAT =
  "Locks are assigned at dispatch, so two agents can never be told to write the same file. A packet that needs a locked file waits rather than merges.";
```

## `apps/atlas/src/agents/ContentionCard.tsx` (new)

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { CONTENTION, CONTENTION_CAVEAT, type ContentionEntry, type ContentionStyleKey } from "./contention";
import styles from "./ContentionCard.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1/E1B/E2/E2B/E3's own precedent. The badge bg/ink mapping is
 * transcribed verbatim from the reference file's own real per-row
 * derivation logic (`bg`/`color` in the reference file's `contention`
 * map function).
 */
const SHELL_VARS = {
  "--atlas-ct-surface": colors.surface,
  "--atlas-ct-border": colors.border,
  "--atlas-ct-header-border": colors.borderDivider[0],
  "--atlas-ct-header-label": colors.inkSecondary,
  "--atlas-ct-status": colors.successText,
  "--atlas-ct-row-border": colors.borderDivider[1],
  "--atlas-ct-path": colors.ink,
  "--atlas-ct-note": colors.inkSecondary,
  "--atlas-ct-caveat": colors.inkMuted,
  "--atlas-ct-badge-run-bg": colors.accentWash[0],
  "--atlas-ct-badge-run-ink": colors.accentHover,
  "--atlas-ct-badge-wait-bg": colors.neutralChip,
  "--atlas-ct-badge-wait-ink": colors.inkSecondary,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const BADGE_CLASS: Record<ContentionStyleKey, string> = {
  run: styles.badgeRun,
  wait: styles.badgeWait,
};

function ContentionRow({ entry }: { entry: ContentionEntry }) {
  return (
    <div className={styles.row}>
      <div className={styles.info}>
        <div className={styles.path}>{entry.path}</div>
        <div className={styles.note}>{entry.note}</div>
      </div>
      <span className={`${styles.badge} ${BADGE_CLASS[entry.styleKey]}`}>{entry.holder}</span>
    </div>
  );
}

/**
 * Renders the real contention/lock card in full: header ("contention"
 * label, "no overlap" status), all 3 real `CONTENTION` rows, and the
 * card's own real trailing caveat.
 */
export function ContentionCard() {
  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.header}>
        contention
        <span className={styles.status}>no overlap</span>
      </div>
      {CONTENTION.map((entry) => (
        <ContentionRow key={entry.path} entry={entry} />
      ))}
      <div className={styles.caveat}>{CONTENTION_CAVEAT}</div>
    </div>
  );
}

export default ContentionCard;
```

## `apps/atlas/src/agents/ContentionCard.module.css` (new)

```css
.card {
  margin-top: 16px;
  border: 1px solid var(--atlas-ct-border);
  border-radius: 14px;
  background: var(--atlas-ct-surface);
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 15px;
  border-bottom: 1px solid var(--atlas-ct-header-border);
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--atlas-ct-header-label);
}

.status {
  margin-left: auto;
  letter-spacing: 0.06em;
  color: var(--atlas-ct-status);
}

.row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: baseline;
  gap: 10px 14px;
  padding: 11px 15px;
  border-bottom: 1px solid var(--atlas-ct-row-border);
}

.info {
  min-width: 0;
}

.path {
  font: 500 13px var(--atlas-font-mono);
  color: var(--atlas-ct-path);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.note {
  margin-top: 2px;
  font-size: 12.5px;
  color: var(--atlas-ct-note);
}

.badge {
  flex: none;
  padding: 3px 8px;
  border-radius: 6px;
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.badgeRun {
  background: var(--atlas-ct-badge-run-bg);
  color: var(--atlas-ct-badge-run-ink);
}

.badgeWait {
  background: var(--atlas-ct-badge-wait-bg);
  color: var(--atlas-ct-badge-wait-ink);
}

.caveat {
  padding: 11px 15px;
  font-size: 12.5px;
  line-height: 1.5;
  color: var(--atlas-ct-caveat);
  text-wrap: pretty;
}
```

## `apps/atlas/src/agents/ContentionCard.test.tsx` (new)

```tsx
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { ContentionCard } from "./ContentionCard";
import { CONTENTION, CONTENTION_CAVEAT } from "./contention";

afterEach(cleanup);

describe("ContentionCard", () => {
  it("renders the real header label and 'no overlap' status", () => {
    render(<ContentionCard />);
    expect(screen.getByText("contention")).toBeInTheDocument();
    expect(screen.getByText("no overlap")).toBeInTheDocument();
  });

  it("renders all 3 real contention rows with their path, note, and holder", () => {
    render(<ContentionCard />);
    for (const entry of CONTENTION) {
      const path = screen.getByText(entry.path);
      const row = path.closest('[class*="row"]') as HTMLElement;
      expect(row).not.toBeNull();
      const rowScope = within(row);
      expect(rowScope.getByText(entry.note)).toBeInTheDocument();
      expect(rowScope.getByText(entry.holder)).toBeInTheDocument();
    }
  });

  it("renders the real trailing caveat", () => {
    render(<ContentionCard />);
    expect(screen.getByText(CONTENTION_CAVEAT)).toBeInTheDocument();
  });

  it("colors the 'Terra' holder badge with the real accent wash, and the 'frozen'/'reserved' badges with the real neutral chip, matching the reference file's real per-row mapping", () => {
    render(<ContentionCard />);
    const terra = screen.getByText("Terra");
    const frozen = screen.getByText("frozen");
    const reserved = screen.getByText("reserved");
    expect(terra.className).toContain("badgeRun");
    expect(frozen.className).toContain("badgeWait");
    expect(reserved.className).toContain("badgeWait");
  });

  it("sets the card border/surface and status CSS variables to the real, checked tokens", () => {
    expect(colors.border).toBe("#E7E1EE");
    expect(colors.successText).toBe("#1F6B4E");
    expect(colors.accentWash[0]).toBe("#EBE4FF");
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<ContentionCard />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-ct-border")).toBe(colors.border);
    expect(root.style.getPropertyValue("--atlas-ct-status")).toBe(colors.successText);
    expect(root.style.getPropertyValue("--atlas-ct-badge-run-bg")).toBe(colors.accentWash[0]);
    expect(root.style.getPropertyValue("--atlas-ct-badge-wait-bg")).toBe(colors.neutralChip);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ContentionCard />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were written to 4 new files
in a scratch worktree and run through the real toolchain from
`apps/atlas`, before this docs-only packet was finalized:

- `npm run typecheck` — clean, no errors, first attempt.
- `npm run lint` — clean, no errors, first attempt.
- `npm test -- --run` — **129/129 passed** across 18 files (the exact
  number the real `vitest` run printed; pre-slice baseline was 123, and
  this slice's own new `ContentionCard.test.tsx` adds exactly 6 tests:
  123 + 6 = 129).
- `npm run build` — succeeds, no new asset failures.

No self-caught bugs — first-attempt clean on every check.

## M0-D12 bounded quality contract

1. **Protected outcome:** `ContentionCard` renders the real
   contention/lock card in full — header, all 3 real rows, and the
   real caveat — completing roadmap item 30, the final Wave E item.
   Zero disclosed color literals.
2. **Operating and threat model:** a trusted local dev box; a
   read-only reporting card with no interactive elements at all (no
   buttons, no state) — no attack surface whatsoever.
3. **Explicit exclusions:** any wiring into `DesktopShell`/`App.tsx`,
   any wiring into `AgentsRoster` (E4) — this remains a separate,
   standalone component.
4. **Assurance level:** practical component-rendering correctness —
   every row and the caveat transcribed verbatim from the reference
   file.
5. **Acceptance proof:** the 6 named tests, the existing 123 pre-slice
   `apps/atlas` tests continuing to pass, `npm run typecheck`, `npm run
   lint`, and `npm run build`, all passing — observed total 129 tests
   across 18 files.
6. **Implementation boundary:** exactly the 4 new files; no new npm
   dependency; every color a real token property; no import of any
   other component-family module.
7. **Proportionality ceiling:** one card component, one fixtures
   module, one CSS Module, one test file; no wiring, no interactivity,
   no second dataset.
8. **Stop and escalation rule:** wiring `ContentionCard` alongside
   `AgentsRoster` into a single Agents screen remains out of scope — a
   future wiring slice's job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E5-CONTENTION-CARD-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:0f329a80970f8b7d7c22a81ddc710d09e1d7b10c"]` |
