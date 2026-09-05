# M2 Wave B — Desktop Shell — Candidate 02

**Slice ID:** `MB-SLICE-M2-B3-DESKTOP-SHELL-02`
**Status:** `Pending Decision Fidelity Review`
**Base:** `925b143` (`origin/master`)
**Supersedes:** `MB-SLICE-M2-B3-DESKTOP-SHELL-01`, terminally `returned`
(unmerged, never pushed to a PR). `-01`'s complete Decision Fidelity
review found 2 blocking findings (hand-copied CSS token values that had
already drifted from the real token files); its one targeted planning
correction fixed the CSS by having the component read real token values
at runtime via CSS custom properties, but the correction's targeted
verification found this made the component a real consumer of
`src/tokens/`, which trips B2's own frozen, already-merged
`tokens.test.ts` test ("no file outside src/tokens imports from
src/tokens") — a test `-01`'s writable-path boundary could not touch.
Per the Bootstrap Convergence Policy, that failed follow-up terminally
returned `-01`. This candidate is authored fresh, carrying forward the
sound parts of `-01`'s corrected design (the CSS-custom-properties
architecture, its disclosure fixes) and adding, as its own named scope
from the start, retiring the one B2 test whose assertion this slice is
always expected to make false by design.

## Scope, deliberately minimal

Wave B3 of the [M2 Atlas roadmap](../m2-atlas-roadmap.md): the desktop
shell. Adds a new `DesktopShell` component — top bar, two-column layout,
dark nav — and wires it into `App.tsx` as Atlas's first real rendered UI,
replacing B1's placeholder. **No packet data, no fixture packets, no
Performance/Agents/History/Gate view content** — this slice renders only
the shell chrome the README's "## Desktop screens" preamble describes,
plus local (non-persisted, non-routed) selection state so a click
visibly marks one nav row active. C1 (packet thread with static
fixtures) and Wave E (Performance/Agents/History/Gate content) are
separate, later slices that fill the content pane and the packet list
this slice deliberately leaves empty.

**Why this slice retires one B2 test, as its own explicit scope, not an
afterthought:** B2's own packet said, in its own words, "No consumer
imports these modules yet — B3 (desktop shell) is the first slice that
renders anything with them." B2's mechanical enforcement of that claim
(`tokens.test.ts`'s "no file outside src/tokens imports from src/tokens"
test) was correct for B2's own moment in time, but its assertion was
always going to become false the instant B3 did exactly what B2's prose
said it would do. This is not a defect in B2 to be worked around — it is
a test whose job was to prove a temporary fact ("nothing consumes this
yet") that this slice's whole purpose is to end. Retiring that one test
function (and the `execSync`/`path`/`declare global` scaffolding that
existed only to support it) is therefore in scope for whichever slice
becomes the first real consumer — this one — rather than a boundary
violation of B2's frozen module files, which this slice does not touch:
`colors.ts`, `typography.ts`, `motion.ts`, `shape.ts`, and `index.ts` are
untouched; only their now-obsolete guard test is removed. The other 4
tests in that file (colors/typography/motion/shape transcription checks)
are untouched and continue to pass.

**Correcting the roadmap's own rough count:** the M2 roadmap's Wave B3
line says "the 5 static nav rows." Re-deriving the exact nav structure
from the README's own text (quoted below) found that count was an
imprecise estimate written before this level of detail existed, not an
exact requirement: the README's nav has exactly **four** static rows at
this shell layer — Performance, Agents, History, and the `M1-B gate`
row — plus a fifth *category* of row, the packet list (`A.0`…`A.7`),
which is fixture data C1 owns, not shell chrome. This slice builds the
four static rows; C1 adds the packet-list rows into the same nav between
History and the divider, exactly where the README places them.

Source quote (README, "## Desktop screens" preamble and "### Nav"
paragraph — the exact lines this slice implements):

> Shell: `display: flex; flex-direction: column; height: 100%`. Top bar
> (`#FFFFFF`, bottom border `#EEEAF2`) holds project name, milestone, and
> a right-aligned live indicator (`6px` dot + label; `live` purple
> `#A78BFF`, `reconnecting` amber `#E0A32E`, `idle` grey). Below it an
> optional full-width **connection strip**. Then a two-column grid:
> `minmax(230px,268px) minmax(0,1fr)` — collapses to `1fr` under 900px.
>
> Nav (dark, `padding:16px 10px 22px`, scrolls): Performance / Agents /
> History entries at top (each a 40px-min row with a small glyph, label,
> and mono count on the right), then the packet list (`A.0`…`A.7`, each
> with a state dot), then the `M1-B gate` row under a hairline divider.

Explicitly **not** built by this slice, per the source quote and the
roadmap's own wave boundaries:

- The connection strip (only meaningful once A6/A7's live event stream
  exists — later Wave A/D work, not yet scheduled as its own packet).
- The live indicator's `live`/`reconnecting` states (no data source
  exists yet; this slice renders the `idle` (grey) state only, since
  that's the only state true with zero data). **Named gap, not a
  transcription claim:** the shell quote above says only "idle grey"
  with no exact hex — unlike `live` (`#A78BFF`) and `reconnecting`
  (`#E0A32E`), which the quote does give. This slice uses the existing
  `colors.borderDashed[2]` token (`#B9AFC4`, already used elsewhere for
  "empty-state placeholders") as the closest already-tokenized grey, not
  a new invented color — but this is an inference, not a verified
  transcription, disclosed as such directly in the code (see
  `DesktopShell.tsx` below).
- Project name and milestone text (no real project/run data exists yet
  — this slice renders a literal placeholder string, clearly marked as
  one, not a fabricated-looking real name).
- The packet list and its per-row state dots (C1).
- Any mono count value (no data exists to count). The design handoff's
  own reporting-honesty rule ("never render a missing metric as `0` —
  `unavailable` is a real value with its own styling") is real and
  correctly cited, but its prescribed literal value is the word
  `unavailable`, not an em dash — rendering `—` here is this slice's own
  design inference for a cramped mono column where the full word would
  not fit the nav row's width, not a value the handoff itself specifies.
  It satisfies the rule's actual requirement (never a fabricated `0`)
  without claiming the rule dictated this exact character.
- Any glyph icon design. The higher-priority reference file (per the
  README's own Fidelity rule: "prefer the reference file... if they ever
  disagree") specifies distinct per-row glyphs (bars, dots, lines) built
  as styled `div`/`span` elements, consistent with the handoff's "no
  images, no icon fonts" asset rule. This slice still defers real
  per-row glyph design — that specific shape work belongs to whichever
  slice first builds each real view (Performance/Agents/History), not
  this shared shell — and renders a small, neutral, undecorated
  placeholder mark (a filled square) in the meantime, correctly
  described as deferring real reference-file content rather than
  filling a gap the source material simply left unspecified. A later
  slice may replace it once real iconography is specified.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-B3-DESKTOP-SHELL-02` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `Project Architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["git:base:925b143","slice:supersedes:MB-SLICE-M2-B3-DESKTOP-SHELL-01:terminally-returned"]` |

## Exact file contents

`apps/atlas/src/shell/DesktopShell.module.css` (new — a CSS Module.
Contains **zero literal hex colors or font-family strings** — every
declaration reads `var(--atlas-*)`, set at runtime in `DesktopShell.tsx`
from the real token module, so a future token change propagates here
automatically with no hand-copy step to drift):

```css
.shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.topBar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--atlas-surface);
  border-bottom: 1px solid var(--atlas-border-divider);
  padding: 16px 34px 15px;
  flex: 0 0 auto;
}

.projectInfo {
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: var(--atlas-ink);
  font: 600 16px var(--atlas-font-body);
}

.milestone {
  color: var(--atlas-ink-muted);
  font: 400 13.5px var(--atlas-font-body);
}

.liveIndicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.liveDot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
}

.liveDotIdle {
  background: var(--atlas-idle-grey);
}

.body {
  display: grid;
  grid-template-columns: minmax(230px, 268px) minmax(0, 1fr);
  flex: 1 1 auto;
  min-height: 0;
}

@media (max-width: 900px) {
  .body {
    grid-template-columns: 1fr;
  }
}

.nav {
  background: var(--atlas-nav-ground);
  padding: 16px 10px 22px;
  overflow-y: auto;
}

.navRow {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 0 10px;
  border-radius: 8px;
  color: var(--atlas-nav-text-inactive);
  font: 600 13.5px var(--atlas-font-body);
  cursor: pointer;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
}

.navRow:hover {
  background: var(--atlas-nav-hover-bg);
}

.navRowActive {
  background: var(--atlas-nav-active-bg);
  color: var(--atlas-nav-text-active);
}

.navGlyph {
  width: 8px;
  height: 8px;
  border-radius: 3px;
  background: var(--atlas-ink-muted);
  flex: 0 0 auto;
}

.navLabel {
  flex: 1 1 auto;
}

.navCount {
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-ink-muted);
}

.navDivider {
  height: 1px;
  background: var(--atlas-nav-divider);
  margin: 12px 10px;
}

.content {
  background: var(--atlas-page-bg-desktop);
  overflow-y: auto;
  padding: 34px;
  color: var(--atlas-ink-muted);
  font: 400 13.5px var(--atlas-font-body);
}
```

`apps/atlas/src/shell/DesktopShell.tsx` (new — imports the real B2 token
module; this is the intentional first real consumer B2's own contract
anticipated):

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import styles from "./DesktopShell.module.css";

export type DesktopShellView = "performance" | "agents" | "history" | "gate";

const NAV_ROWS: ReadonlyArray<{ view: DesktopShellView; label: string }> = [
  { view: "performance", label: "Performance" },
  { view: "agents", label: "Agents" },
  { view: "history", label: "History" },
];

const VIEW_LABEL: Record<DesktopShellView, string> = {
  performance: "Performance",
  agents: "Agents",
  history: "History",
  gate: "M1-B gate",
};

/**
 * Every value here is either a direct property of the real, reviewed
 * `colors`/`fontFamily` tokens, or — where no token exists yet — a
 * literal with an inline comment naming its actual source, so nothing
 * is silently unsourced. This is the ONLY place any of these values are
 * written; `DesktopShell.module.css` only ever reads `var(--atlas-*)`.
 */
const SHELL_VARS = {
  "--atlas-surface": colors.surface,
  "--atlas-border-divider": colors.borderDivider[0],
  "--atlas-ink": colors.ink,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-nav-ground": colors.navGround,
  "--atlas-nav-text-inactive": colors.navTextInactive,
  "--atlas-nav-text-active": colors.navTextActive,
  "--atlas-nav-active-bg": colors.navActiveBg,
  "--atlas-nav-hover-bg": colors.navHoverBg,
  // Not a token: the reference file's own hairline nav divider
  // (Atlas Explorations.dc.html: border-top:1px solid rgba(255,255,255,.08)),
  // no equivalent value exists in colors.ts.
  "--atlas-nav-divider": "rgba(255,255,255,.08)",
  // Not a verified transcription: the README's shell paragraph names
  // exact hex for `live` and `reconnecting` but only says "idle grey"
  // for this state. colors.borderDashed[2] is the closest already-
  // tokenized grey (also used for empty-state placeholders elsewhere),
  // used here as the nearest reasonable value, not an invented one.
  "--atlas-idle-grey": colors.borderDashed[2],
  "--atlas-page-bg-desktop": colors.pageBgDesktop,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function DesktopShell() {
  const [selected, setSelected] = useState<DesktopShellView>("performance");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <header className={styles.topBar}>
        <div className={styles.projectInfo}>
          <span>Project name unavailable</span>
          <span className={styles.milestone}>milestone unavailable</span>
        </div>
        <div className={styles.liveIndicator}>
          <span className={`${styles.liveDot} ${styles.liveDotIdle}`} />
          <span>idle</span>
        </div>
      </header>
      <div className={styles.body}>
        <nav className={styles.nav} aria-label="Atlas views">
          {NAV_ROWS.map((row) => (
            <NavRow
              key={row.view}
              view={row.view}
              label={row.label}
              selected={selected === row.view}
              onSelect={setSelected}
            />
          ))}
          <div className={styles.navDivider} />
          <NavRow
            view="gate"
            label={VIEW_LABEL.gate}
            selected={selected === "gate"}
            onSelect={setSelected}
          />
        </nav>
        <main className={styles.content}>{VIEW_LABEL[selected]} view</main>
      </div>
    </div>
  );
}

function NavRow({
  view,
  label,
  selected,
  onSelect,
}: {
  view: DesktopShellView;
  label: string;
  selected: boolean;
  onSelect: (view: DesktopShellView) => void;
}) {
  return (
    <button
      type="button"
      className={`${styles.navRow} ${selected ? styles.navRowActive : ""}`}
      aria-current={selected ? "true" : undefined}
      onClick={() => onSelect(view)}
    >
      <span className={styles.navGlyph} aria-hidden="true" />
      <span className={styles.navLabel}>{label}</span>
      <span className={styles.navCount}>—</span>
    </button>
  );
}

export default DesktopShell;
```

`apps/atlas/src/App.tsx` (modified — replaces the B1 placeholder with the
real shell; this is the only change to this file):

```tsx
import DesktopShell from "./shell/DesktopShell";

export function App() {
  return <DesktopShell />;
}

export default App;
```

`apps/atlas/src/App.test.tsx` (modified — the B1 placeholder assertion no
longer applies once `App` renders the real shell instead of a bare
`Atlas` string; replaced with an equivalent-purpose smoke test proving
`App` renders *something* real without throwing):

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the desktop shell", () => {
    render(<App />);
    expect(screen.getByRole("navigation", { name: "Atlas views" })).toBeInTheDocument();
  });
});
```

`apps/atlas/src/shell/DesktopShell.test.tsx` (new):

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import DesktopShell from "./DesktopShell";

describe("DesktopShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, not a hand-copied literal", () => {
    const { container } = render(<DesktopShell />);
    const root = container.firstChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-surface")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-nav-ground")).toBe(colors.navGround);
    expect(root.style.getPropertyValue("--atlas-nav-active-bg")).toBe(colors.navActiveBg);
    expect(root.style.getPropertyValue("--atlas-font-mono")).toBe(fontFamily.mono);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
  });

  it("renders the top bar's idle live indicator", () => {
    render(<DesktopShell />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("renders exactly four static nav rows, in order", () => {
    render(<DesktopShell />);
    const rows = screen.getAllByRole("button");
    expect(rows.map((row) => row.textContent?.replace("—", "").trim())).toEqual([
      "Performance",
      "Agents",
      "History",
      "M1-B gate",
    ]);
  });

  it("defaults to Performance selected, with only one row marked current", () => {
    render(<DesktopShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Performance");
    expect(screen.getByText("Performance view")).toBeInTheDocument();
  });

  it("clicking a row makes it the sole selected row and updates the content pane", () => {
    render(<DesktopShell />);
    screen.getByRole("button", { name: /History/ }).click();
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
    expect(screen.getByText("History view")).toBeInTheDocument();
    expect(screen.queryByText("Performance view")).not.toBeInTheDocument();
  });

  it("never renders a literal 0 for the unavailable nav counts", () => {
    render(<DesktopShell />);
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(4);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<DesktopShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

`apps/atlas/src/tokens/tokens.test.ts` (**modified — this slice's named,
in-scope retirement of one now-obsolete B2 test**): remove exactly the
`test("no file outside src/tokens imports from src/tokens", ...)` block
and the scaffolding that existed only to support it — the
`@ts-expect-error`-guarded `import { execSync } from "child_process"` and
`import path from "path"` lines, and the `declare global { interface
ImportMeta { dirname: string } }` block. The other 4 `describe("design
tokens", ...)` tests (colors/typography/motion/shape transcription
checks) and their imports (`colors`, `SEMANTIC_COLOR_RULE`, `fontFamily`,
`fontWeight`, `displayHeading`, `bodyFontSizePx`, `eyebrowLabel`,
`typeScalePx`, `motion`, `radii`, `spacing`, `touchTargetPx`) are
byte-identical to the current file — untouched, not re-verified, not
re-derived; this slice's diff against `tokens.test.ts` is a pure deletion
of the one obsolete test and its now-unused imports, nothing added,
nothing else removed.

## Guards and boundary

1. This slice does not import from, or depend on, any A1-A5 backend
   endpoint — no `fetch`, no `EventSource`, no data of any kind. Every
   value rendered is a compile-time literal or a real token property.
2. `DesktopShell.module.css` contains no literal hex color or font-family
   string — verified directly by reading its full text in this contract;
   every declaration is `var(--atlas-*)`, each one set exactly once in
   `DesktopShell.tsx`'s `SHELL_VARS` from a real `colors`/`fontFamily`
   property, or from a literal with an inline comment naming its real,
   non-token source (the two named exceptions: the nav-divider color,
   the idle-indicator grey).
3. `App.tsx` and `App.test.tsx` are the only B1 files this slice
   modifies; `tokens.test.ts` is the only B2 file this slice modifies,
   and only by deleting the one obsolete test named above — `colors.ts`,
   `typography.ts`, `motion.ts`, `shape.ts`, and `index.ts` are
   byte-identical to their current, merged state.
4. No routing library, no URL state, no persisted selection — `selected`
   is local `useState`, lost on reload, exactly matching "no routing
   logic beyond selection state."

## Boundary, proof, and M0-D12

Writable paths are exactly:

- `apps/atlas/src/shell/DesktopShell.module.css` (new)
- `apps/atlas/src/shell/DesktopShell.tsx` (new)
- `apps/atlas/src/shell/DesktopShell.test.tsx` (new)
- `apps/atlas/src/App.tsx` (modified)
- `apps/atlas/src/App.test.tsx` (modified)
- `apps/atlas/src/tokens/tokens.test.ts` (modified — deletion only, per
  the exact scope named above)

No other path — `colors.ts`, `typography.ts`, `motion.ts`, `shape.ts`,
and `index.ts` under `apps/atlas/src/tokens/` are read (imported) but
not modified.

The 8 named tests (7 in `DesktopShell.test.tsx`, 1 replaced in
`App.test.tsx`), run from `apps/atlas/`:

`npm run typecheck`, `npm run lint`, and `npm test` must all exit `0`,
covering: the two updated/new test files above, plus B2's remaining 4
token tests (colors/typography/motion/shape — unaffected in content,
only the 5th, obsolete test is gone) all still passing. Total
`apps/atlas` test count after this slice: 12 (7 new/updated component
tests + 4 remaining token tests + B1's original scaffold tests already
counted within those files' totals — exact count confirmed by the
implementer's `npm test` summary line, not asserted as a fixed number
here, since it depends on the real merged file's current test count at
implementation time). `npm run build` must still succeed and now produce
a `dist/index.html` whose bundle actually renders the shell content when
served — confirmed via a dev-server smoke test (B1's `check_06` pattern:
real free port, `npx vite --port <port> --strictPort` invoked directly,
`curl` the served page) asserting the response body contains the text
"Performance" and "M1-B gate".

### M0-D12 bounded quality contract

1. **Protected outcome:** the desktop shell renders the exact structural
   chrome (top bar, two-column grid, four static nav rows, one active
   selection at a time, a content pane reflecting that selection) the
   README specifies for this layer, using only real B2 token values
   (read at runtime, not hand-copied), with zero fabricated data, and
   B2's now-obsolete no-consumer guard is retired without touching any
   of B2's actual token content.
2. **Operating and threat model:** a trusted local dev box; a user
   clicking any nav row in any order; a narrow (<900px) viewport.
3. **Explicit exclusions:** any real project/milestone/count data; the
   connection strip; the live/reconnecting indicator states; the packet
   list and any packet-thread content; any Performance/Agents/History/
   Gate view content; any icon/glyph beyond a placeholder mark; any
   routing library or persisted selection; any change to B2's actual
   token values or its other 4 tests.
4. **Assurance level:** practical component-rendering correctness,
   proportionate to static shell chrome with no data dependency —
   verified by JSDOM-rendered component tests, not a full browser
   visual-regression suite (none exists in this project and creating one
   is out of proportion for this slice).
5. **Acceptance proof:** the 8 named tests, the 4 remaining B2 token
   tests continuing to pass, `npm run typecheck`, `npm run lint`, and
   `npm run build` (including the dev-server smoke test), all passing.
6. **Implementation boundary:** exactly the six writable paths above; no
   new npm dependency (CSS Modules and `useState` are already available
   via Vite/React); every CSS custom property set from a real token
   property or a disclosed literal.
7. **Proportionality ceiling:** one shell component, one CSS Module, one
   test-file deletion, no router, no global state library, no animation
   library (the README's `rise`/`sheet` motions are deferred to
   whichever slice first animates a card or sheet).
8. **Stop and escalation rule:** the CSS-custom-property pattern this
   slice establishes (a component's own `SHELL_VARS`-style object
   reading real tokens, consumed by its CSS Module via `var(--atlas-*)`)
   is the intended reusable pattern for B4 and every later screen slice.
   B4 (the next consumer) does not need to touch `tokens.test.ts` again —
   the obsolete guard this slice retires is retired exactly once, here.
   A discovered proof/contract defect against a frozen slice terminally
   returns that slice. One planning correction and one implementation
   correction are the maximum available.
