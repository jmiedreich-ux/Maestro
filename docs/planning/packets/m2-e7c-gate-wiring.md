# M2 Wave E — Wire GateHeader and GateCriteriaList into DesktopShell — Candidate 01

**Slice ID:** `MB-SLICE-M2-E7C-GATE-WIRING-01`
**Status:** `MergeReady`
**Base:** `b744d0e` (full: `b744d0e305f7f981a952cff25f24e5b4d6667965`, `origin/master`)

## Scope, deliberately minimal

Completes roadmap item 32, *"E7 — Gate: criteria list + gate-open
state."* Both real halves already exist and are already merged
standalone: `GateCriteriaList.tsx` (the entry-criteria card) and
`GateHeader.tsx` (title/state/button/lede/approver/releases panels).
Neither is wired into any shell yet — selecting the "gate" nav row in
`DesktopShell` still shows the literal placeholder string "M1-B gate
view." This slice is the final, smallest remaining piece: **wire both
already-real components into `DesktopShell`'s existing "gate" nav
view** — no new component, no new fixture data, no persona work
(already done in E7/E7B).

This slice is frontend-only — no backend file touched. It modifies
exactly 2 existing files (`apps/atlas/src/shell/DesktopShell.tsx`,
`DesktopShell.module.css`) and the accompanying
`DesktopShell.test.tsx`. `GateHeader.tsx` and `GateCriteriaList.tsx`
(E7B's and E7's own files) are read-only imports, never modified.

## Evidence

`DesktopShell.tsx`'s own existing render logic (`selected === "packet"
? <PacketThread /> : ${VIEW_LABEL[selected]} view`) falls through to
the generic placeholder string for every view except "packet" — this
is the exact mechanism F1/F2/F3/F4A each already replaced for their
own tabs, one at a time, as each tab's real content became available.
"gate" is the last `DesktopShellView` still on the placeholder branch.

**Real layout fact, checked directly against both components' own
CSS**: `GateHeader.tsx` already carries its own full padding — a
full-bleed `.headBlock` (`padding: 16px 34px 15px`, its own
background/border) plus a `.body` wrapper (`padding: 22px 34px 30px`)
— matching the real mockup's own unpadded `<main>` (`Atlas
Explorations.dc.html:215`, `<main style="...background:#FCFBFD">`,
no padding of its own; `GateHeader`'s own two sub-sections carry all
the real padding). `DesktopShell`'s existing `.content` class
(`padding: 34px`, used by every other view) would double this padding
if reused for the gate view. `GateCriteriaList.tsx`'s own `.card`
(`max-width: 66ch; margin-top: 20px`) was built assuming its own
container already supplies the horizontal gutter — it has no gutter of
its own.

## Design rationale

1. **A new `.contentGate` class (no padding) replaces `.content` only
   for the "gate" view** — every other view keeps using `.content`
   unchanged. This lets `GateHeader`'s own chrome reach the real edges
   instead of doubling the 34px gutter.
2. **A new `.gateCriteriaWrap` wrapper (horizontal gutter + bottom
   breathing room only) hosts `GateCriteriaList`** — since that
   component was built assuming an ambient gutter it no longer gets
   from `.contentGate`.
3. **Disclosed, not silently accepted: a real, minor spacing
   difference from the mockup.** The real mockup's own vertical gap
   between the releases panel and the criteria card is one continuous
   ~20px. Composing these two already-merged, already-reviewed
   components without modifying either yields a slightly larger real
   gap (`GateHeader`'s own 30px bottom padding plus
   `GateCriteriaList`'s own 20px top margin, ~50px total) — more
   generous whitespace, not a broken or reversed layout. Modifying
   either component's own already-reviewed internals to close this gap
   exactly would be a larger change than this wiring-only slice's own
   scope justifies; disclosed here rather than silently accepted or
   over-engineered.
4. **Neither `GateHeader` nor `GateCriteriaList` is modified.** This
   slice only composes two already-real components — no new fixture
   data, no new persona work, no new design tokens.

## Guards

1. This slice modifies exactly 2 existing files
   (`apps/atlas/src/shell/DesktopShell.tsx`, `DesktopShell.module.css`)
   plus `DesktopShell.test.tsx` — no backend file, no other frontend
   file, touched. `apps/atlas/src/gate/GateHeader.tsx` and
   `GateCriteriaList.tsx` are read-only imports, never modified.
2. Every other `DesktopShellView` (`performance`, `agents`, `history`)
   still renders its own existing placeholder unchanged — this slice's
   scope is the "gate" view only.
3. Selecting a different nav row after the gate view correctly
   unmounts both `GateHeader` and `GateCriteriaList` — a dedicated test
   proves this (React's own conditional-render unmount, not a
   `display: none` hide).
4. The literal placeholder string "M1-B gate view" no longer renders
   for the gate view — a dedicated test proves its absence.

## Corrected — Decision Fidelity review findings (RESOLVED)

An independent Decision Fidelity review returned **PASS WITH
NON-BLOCKING NOTES**, and fixed both at zero cost before finalizing
this packet as `MergeReady`:

1. **Mockup file not present in this repository.** The reviewer could
   not independently verify the `Atlas Explorations.dc.html:215`
   `<main>`-padding citation (Design rationale / Evidence sections)
   because that mockup file lives outside version control. This
   matches an already-disclosed, session-wide tooling limitation (no
   browser-based visual verification was available for this or any
   prior M2 slice this session) — not fixed, since there is nothing in
   this repository to fix; disclosed here explicitly rather than
   silently accepted.
2. **Real, fixed test-coverage gap (fixed):** the reviewer proved, via
   mutation-testing, that reverting the gate view's `<main>` className
   from `styles.contentGate` back to `styles.content` — the exact
   layout regression Design rationale #1 exists to prevent (doubling
   `GateHeader`'s own 34px gutter) — left all 14 original tests
   passing, since none of them asserted on `<main>`'s own className.
   **Fix:** added `data-testid="desktop-shell-main"` to the `<main>`
   element, and a new test that imports the real `DesktopShell.module
   .css` identifiers and asserts `<main>`'s className switches exactly
   between `styles.content` and `styles.contentGate` across every nav
   selection. I re-ran the reviewer's own mutation (reverting the
   className to `styles.content` for the gate case) against the
   corrected suite and confirmed the new test — and only the new
   test — now fails, then reverted the mutation. Test count: 14 → 15
   in `DesktopShell.test.tsx`; suite total 184 → 185.

No other files, no other behavior, changed by this correction.

## `apps/atlas/src/shell/DesktopShell.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import PacketThread from "../thread/PacketThread";
import { GateHeader } from "../gate/GateHeader";
import { GateCriteriaList } from "../gate/GateCriteriaList";
import { deriveConnectionState, type SystemState } from "./connectionState";
import styles from "./DesktopShell.module.css";

export type DesktopShellView = "performance" | "agents" | "history" | "gate" | "packet";

export interface DesktopShellProps {
  systemState?: SystemState;
}

const NAV_ROWS: ReadonlyArray<{ view: DesktopShellView; label: string }> = [
  { view: "performance", label: "Performance" },
  { view: "agents", label: "Agents" },
  { view: "history", label: "History" },
];

const VIEW_LABEL: Record<Exclude<DesktopShellView, "packet">, string> = {
  performance: "Performance",
  agents: "Agents",
  history: "History",
  gate: "M1-B gate",
};

const PACKET_A2_LABEL = "A.2 · Runtime Package";

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
  // The live indicator's own dot/text colors, and the connection
  // strip's own bg/border/ink/dot, are no longer static here — they
  // vary by `systemState` (idle vs. reconnecting), so they are
  // computed per-render by `deriveConnectionState` below and applied
  // as their own small per-render custom-property object (`connVars`),
  // the same established convention the private `AgentCard` function's
  // own `cardVars` uses (`apps/atlas/src/agents/AgentsRoster.tsx`) for
  // per-item dynamic colors — never as a raw inline `style.color`/
  // `style.background`, which a real browser (and jsdom) silently
  // re-serializes to `rgb(...)`, breaking an exact-string test
  // assertion against the original hex token. See
  // `connectionState.ts`'s own doc comment for the real token sourcing
  // (this slice's own G1 packet; the prior "idle grey" finding this
  // comment used to cite is now folded into that file).
  "--atlas-page-bg-desktop": colors.pageBgDesktop,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-nav-text-running": colors.navTextActive,
  "--atlas-dot-need": colors.warning,
  // Not a token: the reference file's own halo alpha value for this
  // exact dot state (Atlas Explorations.dc.html's dot() function,
  // 'need' branch) — colors.warning's RGB (224,163,46) at .26 alpha,
  // no equivalent token exists for a translucent halo.
  "--atlas-dot-need-halo": "rgba(224,163,46,.26)",
  // The connection strip's own body text color is a real, fixed token
  // (not state-dependent, unlike the strip's bg/border/ink/dot which
  // do vary by `systemState` and are applied inline) —
  // `colors.inkSecondary`, matching the reference file's own real
  // `color:#6C6376` on `conn.body` (Atlas Explorations.dc.html:32).
  "--atlas-conn-body": colors.inkSecondary,
} as CSSProperties;

/**
 * The "gate" nav view renders E7's two already-real, already-reviewed
 * components stacked — `GateHeader` (title/state/button/lede/approver/
 * releases) then `GateCriteriaList` (the entry-criteria card) — the
 * first real wiring of either into any shell. Neither component is
 * modified here: this slice only composes them.
 *
 * `GateHeader` already carries its own full real padding (a full-bleed
 * top bar plus its own `22px 34px 30px` body wrapper), matching the
 * real mockup's own unpadded `<main>` — so the "gate" view uses
 * `.contentGate` (no padding) instead of the generic `.content` (which
 * every other view already relies on for its own 34px gutter), letting
 * `GateHeader`'s own chrome reach the real edges instead of doubling
 * up. `GateCriteriaList` is wrapped in `.gateCriteriaWrap` (horizontal
 * gutter + bottom breathing room only) since it was built as a
 * standalone component assuming its own container already supplies
 * that gutter. **Disclosed, not silently accepted:** the real mockup's
 * own vertical gap between the releases panel and the criteria card is
 * one continuous ~20px; composing these two already-merged components
 * without modifying either yields a slightly larger real gap (`
 * GateHeader`'s own 30px bottom padding plus `GateCriteriaList`'s own
 * 20px top margin) — more generous whitespace, not a broken or
 * reversed layout, and a smaller compromise than modifying either
 * component's own already-reviewed internals for a wiring-only slice.
 */
export function DesktopShell({ systemState = "normal" }: DesktopShellProps = {}) {
  const [selected, setSelected] = useState<DesktopShellView>("performance");
  const conn = deriveConnectionState(systemState, "desktop");
  const connVars = {
    "--atlas-conn-live-dot": conn.liveDotColor,
    "--atlas-conn-live-text": conn.liveTextColor,
    "--atlas-conn-strip-bg": conn.strip.bg,
    "--atlas-conn-strip-border": conn.strip.border,
    "--atlas-conn-strip-ink": conn.strip.ink,
    "--atlas-conn-strip-dot": conn.strip.dot,
  } as CSSProperties;

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <header className={styles.topBar}>
        <div className={styles.projectInfo}>
          <span>Project name unavailable</span>
          <span className={styles.milestone}>milestone unavailable</span>
        </div>
        <div className={styles.liveIndicator} style={connVars}>
          <span className={styles.liveDot} />
          <span>{conn.liveLabel}</span>
        </div>
      </header>
      {conn.strip.show ? (
        <div className={styles.connectionStrip} style={connVars}>
          <span className={styles.connectionTitle}>
            <span className={styles.connectionDot} />
            {conn.strip.title}
          </span>
          <span className={styles.connectionBody}>{conn.strip.body}</span>
          <span className={styles.connectionMeta}>{conn.strip.meta}</span>
        </div>
      ) : null}
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
          <button
            type="button"
            className={`${styles.packetRow} ${selected === "packet" ? styles.packetRowActive : ""}`}
            aria-current={selected === "packet" ? "true" : undefined}
            onClick={() => setSelected("packet")}
          >
            <span className={styles.packetDot} aria-hidden="true" />
            <span className={styles.packetLabel}>{PACKET_A2_LABEL}</span>
          </button>
          <div className={styles.navDivider} />
          <NavRow
            view="gate"
            label={VIEW_LABEL.gate}
            selected={selected === "gate"}
            onSelect={setSelected}
          />
        </nav>
        <main
          data-testid="desktop-shell-main"
          className={selected === "gate" ? styles.contentGate : styles.content}
        >
          {selected === "packet" ? (
            <PacketThread />
          ) : selected === "gate" ? (
            <>
              <GateHeader />
              <div className={styles.gateCriteriaWrap}>
                <GateCriteriaList />
              </div>
            </>
          ) : (
            `${VIEW_LABEL[selected]} view`
          )}
        </main>
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

## `apps/atlas/src/shell/DesktopShell.module.css` (modified — full new content)

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
  color: var(--atlas-conn-live-text);
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.liveDot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--atlas-conn-live-dot);
}

.connectionStrip {
  flex: none;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 9px 16px;
  background: var(--atlas-conn-strip-bg);
  border-bottom: 1px solid var(--atlas-conn-strip-border);
  color: var(--atlas-conn-strip-ink);
  font-size: 13px;
}

.connectionTitle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.connectionDot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--atlas-conn-strip-dot);
}

.connectionBody {
  min-width: 0;
  flex: 1;
  line-height: 1.5;
  color: var(--atlas-conn-body);
  text-wrap: pretty;
}

.connectionMeta {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-conn-strip-ink);
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

.contentGate {
  background: var(--atlas-page-bg-desktop);
  overflow-y: auto;
}

.gateCriteriaWrap {
  padding: 0 34px 30px;
}

.packetRow {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 40px;
  padding: 8px 10px;
  border-radius: 8px;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font: 400 14px var(--atlas-font-body);
  color: var(--atlas-nav-text-running);
}

.packetRow:hover {
  background: var(--atlas-nav-hover-bg);
}

.packetRowActive {
  background: var(--atlas-nav-active-bg);
  font-weight: 600;
}

.packetLabel {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.packetDot {
  flex: none;
  display: inline-block;
  box-sizing: border-box;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--atlas-dot-need);
  box-shadow: 0 0 0 3px var(--atlas-dot-need-halo);
}
```

## `apps/atlas/src/shell/DesktopShell.test.tsx` (modified — full new content)

```tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import DesktopShell from "./DesktopShell";
import styles from "./DesktopShell.module.css";

afterEach(cleanup);

describe("DesktopShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, not a hand-copied literal", () => {
    const { container } = render(<DesktopShell />);
    const root = container.firstChild as HTMLElement;
    // Corrected — non-blocking finding from Decision Fidelity review:
    // exhaustively checks every SHELL_VARS entry, including the
    // disclosed non-token literals — a prior draft spot-checked only 5
    // of 14 entries, which would not have caught the wrong-value
    // idle-grey defect review found by hand. G1 removed
    // `--atlas-idle-grey`/`--atlas-idle-label` (the live indicator's
    // colors are now computed per-render by `deriveConnectionState`
    // and applied via inline style, not a fixed custom property) and
    // added `--atlas-conn-body` (the connection strip's own fixed body
    // text color) — this list is updated to match.
    expect(root.style.getPropertyValue("--atlas-surface")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-border-divider")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-nav-ground")).toBe(colors.navGround);
    expect(root.style.getPropertyValue("--atlas-nav-text-inactive")).toBe(colors.navTextInactive);
    expect(root.style.getPropertyValue("--atlas-nav-text-active")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-nav-active-bg")).toBe(colors.navActiveBg);
    expect(root.style.getPropertyValue("--atlas-nav-hover-bg")).toBe(colors.navHoverBg);
    expect(root.style.getPropertyValue("--atlas-nav-divider")).toBe("rgba(255,255,255,.08)");
    expect(root.style.getPropertyValue("--atlas-page-bg-desktop")).toBe(colors.pageBgDesktop);
    expect(root.style.getPropertyValue("--atlas-font-mono")).toBe(fontFamily.mono);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-nav-text-running")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-dot-need")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-dot-need-halo")).toBe("rgba(224,163,46,.26)");
    expect(root.style.getPropertyValue("--atlas-conn-body")).toBe(colors.inkSecondary);
  });

  it("defaults to systemState 'normal': live indicator says 'idle' with real idle-token colors, no connection strip", () => {
    render(<DesktopShell />);
    const live = screen.getByText("idle").closest('[class*="liveIndicator"]') as HTMLElement;
    expect(live.style.getPropertyValue("--atlas-conn-live-text")).toBe(colors.inkFaint);
    expect(live.style.getPropertyValue("--atlas-conn-live-dot")).toBe(colors.inkMuted);
    expect(screen.queryByText("Reconnecting")).toBeNull();
  });

  it("systemState 'disconnected': live indicator flips to 'reconnecting' and the real connection strip renders", () => {
    render(<DesktopShell systemState="disconnected" />);
    expect(screen.getByText("reconnecting")).toBeInTheDocument();
    expect(screen.getByText("Reconnecting")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Atlas lost its connection at 14:58. Agents keep working — they report to the Coordinator, not to this window. What you see below is the last state Atlas received.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("retry 3 · 0:12")).toBeInTheDocument();
  });

  it("renders the top bar's idle live indicator", () => {
    render(<DesktopShell />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("renders the four static nav rows plus the packet row, in order", () => {
    render(<DesktopShell />);
    const rows = screen.getAllByRole("button");
    expect(rows.map((row) => row.textContent?.replace("—", "").trim())).toEqual([
      "Performance",
      "Agents",
      "History",
      "A.2 · Runtime Package",
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
    fireEvent.click(screen.getByRole("button", { name: /History/ }));
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

  it("renders the A.2 packet row between History and the M1-B gate row", () => {
    render(<DesktopShell />);
    // Corrected: the real NavRow always appends a trailing mono count
    // span ("—") to its own text, exactly like the pre-existing "renders
    // exactly four static nav rows" test already accounts for — this
    // test's first draft omitted that same normalization and failed
    // against the real rendered output.
    const rows = screen
      .getAllByRole("button")
      .map((r) => r.textContent?.replace("—", "").trim());
    expect(rows).toEqual(["Performance", "Agents", "History", "A.2 · Runtime Package", "M1-B gate"]);
  });

  it("selecting the A.2 row shows the real packet thread, not a placeholder", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("A.2");
    // PacketThread's own first fixture message, proving the real
    // component rendered, not a "packet view" placeholder string.
    expect(screen.getByText(PACKET_A2_ENTRIES[0].text)).toBeInTheDocument();
    expect(screen.queryByText("packet view")).not.toBeInTheDocument();
  });

  it("selecting a static row after the packet row correctly unmounts the thread", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
    // Corrected: the real accessible name is "Agents—" (the trailing
    // mono count), so the exact string "Agents" never matches — the same
    // class of fix as the test above, using a regex here instead since
    // this call needs to select one specific row, not compare a full list.
    fireEvent.click(screen.getByRole("button", { name: /^Agents/ }));
    expect(screen.getByText("Agents view")).toBeInTheDocument();
    expect(screen.queryByText(PACKET_A2_ENTRIES[0].text)).not.toBeInTheDocument();
  });

  it("(E7C) selecting the M1-B gate row renders the real GateHeader and GateCriteriaList, not the placeholder", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("M1-B gate");

    // Real GateHeader content.
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
    expect(screen.getByText("approver")).toBeInTheDocument();
    // Real GateCriteriaList content.
    expect(screen.getByText("entry criteria")).toBeInTheDocument();
    expect(screen.getByText("A.0 through A.7 accepted")).toBeInTheDocument();

    expect(screen.queryByText("M1-B gate view")).not.toBeInTheDocument();
  });

  it("(E7C) selecting a different static row after the gate row correctly unmounts GateHeader/GateCriteriaList", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Performance/ }));
    expect(screen.getByText("Performance view")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Overlay and support surfaces" })).not.toBeInTheDocument();
    expect(screen.queryByText("entry criteria")).not.toBeInTheDocument();
  });

  it("(E7C, corrected — Decision Fidelity review finding) the gate view's <main> uses the no-padding .contentGate class, and every other view keeps the padded .content class", () => {
    // The reviewer proved this by mutation-testing: reverting the gate
    // view's className from `styles.contentGate` back to `styles.content`
    // (the exact regression Design Rationale #1 exists to avoid — doubling
    // GateHeader's own 34px gutter) left all other tests passing, since
    // none of them asserted on <main>'s own className. This test compares
    // against the real imported CSS-module identifiers, not hand-typed
    // strings, so it fails under that exact mutation.
    render(<DesktopShell />);
    const main = screen.getByTestId("desktop-shell-main");
    expect(main.className).toBe(styles.content);
    expect(main.className).not.toBe(styles.contentGate);

    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    expect(main.className).toBe(styles.contentGate);
    expect(main.className).not.toBe(styles.content);

    fireEvent.click(screen.getByRole("button", { name: /^Performance/ }));
    expect(main.className).toBe(styles.content);
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above (already reflecting the
Decision Fidelity correction) were applied to this scratch worktree
(`/tmp/maestro-m2-e7c-wire`, branch `architecture/m2-e7c-gate-wiring`,
base `b744d0e`) and run through the real frontend toolchain from
`apps/atlas` (`npm install`, then each script below) a second time,
after the correction, before this packet was finalized as
`MergeReady`.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **23/23 test files, 185/185 tests
  passed** (15 in `DesktopShell.test.tsx`, up from 12 at base; zero
  regressions in the other 22 files, including `GateHeader.test.tsx`
  and `GateCriteriaList.test.tsx`, neither of which this slice
  modifies).
- `npm run build` (`vite build`) — clean, `45 modules transformed`, no
  warnings.
- Every declared `--atlas-*` custom property, and every CSS class
  declared in `DesktopShell.module.css`, was cross-checked
  programmatically against `DesktopShell.tsx`'s own references — zero
  orphans in either direction.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** selecting the "M1-B gate" nav row in
   `DesktopShell` renders the real `GateHeader` and `GateCriteriaList`
   components, completing roadmap item 32 (E7), with zero backend
   change and zero regression to any of the 23 existing test files.
2. **Operating and threat model:** none — pure frontend composition, no
   network call, no command dispatch.
3. **Explicit exclusions:** any modification to `GateHeader.tsx` or
   `GateCriteriaList.tsx` themselves (both stay exactly as already
   reviewed and merged); the mobile bottom-sheet variant of this same
   gate content (roadmap item 36/F4B's own separate scope).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering composition — every rendered surface and every nav
   transition (including unmounting) is exercised by a React Testing
   Library render/interaction test; no browser-based visual
   verification was performed (tooling failure, already disclosed in
   this session for M2-E4/F1/F2/F3/F3B/F3C/E7B/F4A, same root cause) —
   the disclosed ~20px vs. ~50px spacing difference (Design rationale
   #3) is a real, checked CSS-math difference, not a guess.
5. **Acceptance proof:** 23/23 test files, 184/184 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 2 modified files (plus their test
   file), all within `apps/atlas/src/shell`; zero backend files; no
   new third-party dependency; `apps/atlas/src/gate/*` read-only,
   never modified.
7. **Proportionality ceiling:** two new CSS classes, one new import
   pair, one new conditional render branch — no new fixture data
   invented, no new design tokens invented, no component modified.
8. **Stop and escalation rule:** modifying `GateHeader`/
   `GateCriteriaList` to close the disclosed spacing gap exactly, or
   building the mobile bottom-sheet variant, is explicitly out of
   scope — future slices' job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-E7C-GATE-WIRING-01` |
| `phase` | `MergeReady` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-e7c-gate-wiring.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
