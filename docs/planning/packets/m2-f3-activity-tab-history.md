# M2 Wave F — Mobile Activity Tab, History Segment — Candidate 01

**Slice ID:** `MB-SLICE-M2-F3-ACTIVITY-TAB-HISTORY-01`
**Status:** `Draft, pending Decision Fidelity Review`
**Base:** `cf0c25a` (full: `cf0c25ad7d1a5d7f4e659accda83e201adc1b632`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 35, *"F3 — Activity tab: History/Agents/Cost segmented,
reusing E6/E4/E1–E3 data."* This item names three real segments. Like
E1/E1B and E2/E2B before it, this slice splits it into the smallest
independently reviewable piece: the real segmented-control shell
(History/Agents/Cost, all three real and tappable) plus **only the
History segment's real content** (reusing E6). The Agents segment
(reusing E4) and the Cost segment (reusing E1-E3) are separate,
future slices — not built here, not silently dropped; the segmented
control itself already switches to them correctly, it just shows an
honest placeholder until their own slice lands, matching
`MobileShell.tsx`'s own established `${label} tab` placeholder
convention for not-yet-built tabs.

This slice is frontend-only — no backend file touched.

## Evidence

`Atlas Mobile.dc.html:219-249` is the real mobile "Activity" tab (the
reference file's own internal name is `isAct`). It has:

1. **Header** (`:220-227`): a page title `<h1>Activity</h1>` (a
   literal, static UI label, not fixture content) and a real 3-way
   segmented control (`:222-225`) with track background `#EDE9F3`.
2. **History segment** (`:230-249`, the reference file's own default
   selected segment, `hint-placeholder-val="{{ true }}"`, matching its
   real JS default `seg: 'hist'`): real `histStats`
   (`:232-234`), a real timeline (`:236-248`) with a rail line
   (`#E6E0EE`, `:239`) and a dot (outer ring `#F7F5FA`, `:240`,
   simpler than desktop History's own extra urgent-ring layer — no
   second ring exists in this real markup at all), and a trailing note
   (`:249`, literal text `"A.3 through A.7 have not been dispatched."`).

E6's own already-merged `apps/atlas/src/history/fixtures.ts` already
has the real data this segment needs:
`HISTORY_STATS` (4 real stats), `HISTORY_ENTRIES` (10 real entries),
and `HISTORY_KIND_STYLE` (`apps/atlas/src/history/historyStyle.ts`,
the real per-kind tag/dot styling) — none of it modified by this
slice, all of it imported and reused verbatim.

## Design rationale

1. **Reuses E6's fixture and style data verbatim; no new fixture
   content invented.** `HISTORY_STATS`, `HISTORY_ENTRIES`,
   `HISTORY_KIND_STYLE` are imported unmodified from their already-
   merged files.
2. **Does not render an "Open … thread" button**, unlike desktop
   History. The real mobile markup's own `history` entries (checked in
   the reference file's `renderVals()` JS) have no `ref`/button field
   at all on this surface — this is a real, checked simplification of
   the mobile view, not an invented omission.
3. **Reuses `HISTORY_EMPTY_NOTE` (E6's own established constant),
   not the mobile markup's own shorter literal text.** The reference
   file's own line 249 reads *"A.3 through A.7 have not been
   dispatched."* — a slightly different, shorter string than the
   already-merged `HISTORY_EMPTY_NOTE` constant
   (`"A.3 through A.7 have not been dispatched — nothing to record
   yet."`). Reusing the one already-established real constant, rather
   than introducing a second, near-duplicate string for the same real
   fact, matches this program's own precedent (F2 reused C7's real
   eyebrow/title pair rather than the mobile markup's own distinct
   abbreviated header text for the same identity).
4. **Agents and Cost segments are real, tappable, and correctly
   switch the segmented control's own selection state**, but render
   only a placeholder string. This is not a corner cut silently:
   Guards item 4 and the M0-D12 contract both name this explicitly,
   and a dedicated test confirms the segmented control's own
   `aria-current` state is correct for all three segments even though
   only one has real content.
5. **Segmented-control styling reuses the established convention**
   (a CSS class toggle for the selected state, `styles.segSelected`),
   matching E3's `PerfBreakdownCard` — not inline `var()` string
   references, which would be inconsistent with every other real
   component in this codebase (self-caught before dispatch: an earlier
   draft used inline `style={{ background: "var(--atlas-x)" }}`
   conditionals instead of this established class-toggle pattern;
   fixed before finalizing).

## Guards

1. This slice modifies exactly 2 existing files
   (`apps/atlas/src/shell/MobileShell.tsx`,
   `apps/atlas/src/shell/MobileShell.test.tsx`) and adds exactly 3 new
   files (`apps/atlas/src/shell/ActivityTab.tsx`,
   `ActivityTab.module.css`, `ActivityTab.test.tsx`) — no backend
   file, no other frontend file, touched. `apps/atlas/src/history/*`
   (E6's own files) are read-only imports, never modified.
2. `MobileShell.test.tsx`'s pre-existing "tapping a tab" placeholder
   test now taps `"Plan"` instead of `"Activity"` — Plan is the one
   remaining placeholder tab after F1/F2/F3; this is the correct,
   intended consequence of F3 replacing the Activity placeholder, not
   a regression. One new test asserts the real `ActivityTab` renders
   for the Activity tab, scoped to the tab bar's own `<nav>` (its
   segmented control also sets `aria-current`, which would otherwise
   collide with an unscoped current-button query — the same class of
   fix D2/F1/F2 already established for analogous collisions).
3. No `DecisionCard`/`OwnerDecisionCard`/`FidelityRecord`/`CrashCard`/
   `AgentsRoster`/any E1-E3 performance component is rendered anywhere
   in `ActivityTab.tsx` — this slice's scope is the History segment
   only.
4. The Agents and Cost segments render only a placeholder string
   (`"Agents segment"` / `"Cost segment"`) — dedicated tests confirm
   tapping each correctly updates the segmented control's own
   selection state, proving the shell itself is real even though two
   of its three segments' content is not yet built.

## `apps/atlas/src/shell/ActivityTab.tsx` (new)

```typescript
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "../history/fixtures";
import { HISTORY_KIND_STYLE } from "../history/historyStyle";
import styles from "./ActivityTab.module.css";

type ActivitySegment = "hist" | "agents" | "cost";

const SEGMENTS: ReadonlyArray<{ key: ActivitySegment; label: string }> = [
  { key: "hist", label: "History" },
  { key: "agents", label: "Agents" },
  { key: "cost", label: "Cost" },
];

/**
 * Mobile Activity-tab colors from `Atlas Mobile.dc.html`'s real `isAct`
 * markup (lines 219-249 of the reference file), checked directly
 * against `colors.ts`. Real token matches: `colors.segmentedTrack[0]`
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
} as CSSProperties;

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

/**
 * Mobile "Activity" tab — the reference file's own `isAct` view: a
 * page title, a real 3-way segmented control (History/Agents/Cost,
 * defaulting to History, matching the reference file's own real
 * `seg: 'hist'` initial state), and the History segment's real content
 * reusing E6's own `HISTORY_STATS`/`HISTORY_ENTRIES`/`HISTORY_KIND_STYLE`
 * fixture and style data restyled as a simpler mobile timeline (no
 * "Open … thread" button — the real mobile markup has no such control
 * on this surface, checked directly). The Agents and Cost segments are
 * real, tappable, and switch the segmented control's own selection
 * state correctly, but render only a placeholder — reusing E4's
 * `AgentsRoster`/E1-E3's performance data for those two segments is
 * separate, future work (roadmap item 35's own remaining scope),
 * matching this program's own established pattern of splitting an
 * oversized roadmap item into independently reviewable slices (E1/E1B,
 * E2/E2B).
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
        ) : (
          `${SEGMENTS.find((seg) => seg.key === segment)?.label} segment`
        )}
      </div>
    </div>
  );
}

export default ActivityTab;
```

## `apps/atlas/src/shell/ActivityTab.module.css` (new)

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
```

## `apps/atlas/src/shell/ActivityTab.test.tsx` (new)

```typescript
import { render, screen, cleanup, fireEvent } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";

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

  it("tapping Agents or Cost switches the segmented control's own selection and shows a placeholder", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    let current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Agents");
    expect(screen.getByText("Agents segment")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Cost" }));
    current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Cost");
    expect(screen.getByText("Cost segment")).toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ActivityTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## `apps/atlas/src/shell/MobileShell.tsx` (modified — full new content)

```typescript
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { NowTab } from "./NowTab";
import { ChatTab } from "./ChatTab";
import { ActivityTab } from "./ActivityTab";
import styles from "./MobileShell.module.css";

export type MobileShellTab = "now" | "chat" | "plan" | "activity";

const TABS: ReadonlyArray<{ tab: MobileShellTab; label: string }> = [
  { tab: "now", label: "Now" },
  { tab: "chat", label: "Chat" },
  { tab: "plan", label: "Plan" },
  { tab: "activity", label: "Activity" },
];

/**
 * Every value here is either a direct property of the real, reviewed
 * `colors`/`fontFamily` tokens, or — where no token exists yet — a
 * literal with an inline comment naming its actual source (all five
 * non-token values here are from `Atlas Mobile.dc.html`, none
 * invented — corrected from an earlier draft that left one,
 * `backdrop-filter: blur(12px)`, as a bare CSS literal instead of
 * routing it through this same disclosed mechanism). Matches the
 * pattern `DesktopShell.tsx` (B3) already established.
 */
const SHELL_VARS = {
  "--atlas-page-bg-mobile": colors.pageBgMobile,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-font-body": fontFamily.body,
  // Not tokens: the reference file's own tab-bar chrome
  // (Atlas Mobile.dc.html's bottom <nav>) — no equivalent values exist
  // in colors.ts.
  "--atlas-tab-bar-bg": "rgba(255,255,255,.92)",
  "--atlas-tab-bar-border": "#EAE5F0",
  "--atlas-tab-bar-blur": "blur(12px)",
  // Reference file: `const col = k => s.tab === k ? '#5B34E8' : '#9A90A6'`.
  // The selected color is the real `colors.accent` token; the inactive
  // color (#9A90A6) has no equivalent token, so it stays a disclosed
  // literal.
  "--atlas-tab-selected": colors.accent,
  "--atlas-tab-inactive": "#9A90A6",
} as CSSProperties;

const TAB_LABEL: Record<MobileShellTab, string> = {
  now: "Now",
  chat: "Chat",
  plan: "Plan",
  activity: "Activity",
};

export function MobileShell() {
  const [selected, setSelected] = useState<MobileShellTab>("now");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <main className={styles.content}>
        {selected === "now" ? (
          <NowTab />
        ) : selected === "chat" ? (
          <ChatTab onBack={() => setSelected("now")} />
        ) : selected === "activity" ? (
          <ActivityTab />
        ) : (
          `${TAB_LABEL[selected]} tab`
        )}
      </main>
      <nav className={styles.tabBar} aria-label="Atlas tabs">
        {TABS.map((t) => (
          <button
            key={t.tab}
            type="button"
            className={`${styles.tab} ${selected === t.tab ? styles.tabSelected : ""}`}
            aria-current={selected === t.tab ? "true" : undefined}
            onClick={() => setSelected(t.tab)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

export default MobileShell;
```

## `apps/atlas/src/shell/MobileShell.test.tsx` (modified — full new content)

```typescript
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import MobileShell from "./MobileShell";

afterEach(cleanup);

describe("MobileShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, plus the disclosed reference-file literals", () => {
    const { container } = render(<MobileShell />);
    const root = container.firstChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-page-bg-mobile")).toBe(colors.pageBgMobile);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-tab-bar-bg")).toBe("rgba(255,255,255,.92)");
    expect(root.style.getPropertyValue("--atlas-tab-bar-border")).toBe("#EAE5F0");
    expect(root.style.getPropertyValue("--atlas-tab-bar-blur")).toBe("blur(12px)");
    expect(root.style.getPropertyValue("--atlas-tab-selected")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-tab-inactive")).toBe("#9A90A6");
  });

  it("renders exactly four tabs, in the reference file's actual order (not the README prose order)", () => {
    render(<MobileShell />);
    // Scoped to the tab bar itself: F1's real Now-tab content also
    // contains real buttons (the reused owner-decision options), so an
    // unscoped `getAllByRole("button")` now picks those up too.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    const tabs = within(nav).getAllByRole("button");
    expect(tabs.map((t) => t.textContent)).toEqual(["Now", "Chat", "Plan", "Activity"]);
  });

  it("defaults to Now selected, with only one tab marked current, rendering the real Now tab (F1) rather than the placeholder", () => {
    render(<MobileShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("tapping a tab makes it the sole selected tab and updates the content pane", () => {
    render(<MobileShell />);
    // Plan is the one remaining placeholder tab (Now/Chat/Activity all
    // render real content as of F1/F2/F3).
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Plan" }));
    const current = within(nav).getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Plan");
    expect(screen.getByText("Plan tab")).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("(F3) tapping Activity renders the real ActivityTab (F3) rather than the placeholder", () => {
    render(<MobileShell />);
    // Scoped to the tab bar: ActivityTab's own segmented control also
    // sets aria-current on its selected segment button, which would
    // otherwise collide with an unscoped current-button query.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Activity" }));
    const current = within(nav).getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Activity");
    expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
    expect(screen.queryByText("Activity tab")).not.toBeInTheDocument();
  });

  it("(F2) tapping Chat renders the real ChatTab (F2) rather than the placeholder", () => {
    render(<MobileShell />);
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Chat" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Chat");
    expect(screen.getByRole("button", { name: "‹ Now" })).toBeInTheDocument();
    expect(screen.queryByText("Chat tab")).not.toBeInTheDocument();
  });

  it("(F2) ChatTab's own '‹ Now' back button returns to the real Now tab", () => {
    render(<MobileShell />);
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Chat" }));
    fireEvent.click(screen.getByRole("button", { name: "‹ Now" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<MobileShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (`/tmp/maestro-m2-f3`, branch `architecture/m2-f3`, base
`cf0c25a`) and run through the real frontend toolchain from
`apps/atlas` (`npm install`, then each script below), before this
packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean after one self-caught
  fix (an unused `within` import in `ActivityTab.test.tsx`, from an
  earlier draft's abandoned scoping approach).
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **21/21 test files, 157/157 tests
  passed** after two self-caught fixes:
  - `ActivityTab.test.tsx`'s own first draft asserted every
    `HISTORY_STATS` value with a bare `screen.getByText(stat.value)`;
    two real stats ("Corrections spent" and "Decisions recorded")
    share the exact same real value ("1"), causing a genuine
    multiple-elements-found failure on the second one. Fixed by
    checking each stat's label+value as one concatenated text run
    instead (each label is unique even though two values collide).
  - `MobileShell.test.tsx`'s pre-existing "tapping a tab" placeholder
    test taped "Activity" — now real content — and its own unscoped
    `getAllByRole("button", {current:true})` calls would otherwise
    collide with `ActivityTab`'s own segmented control (which also
    sets `aria-current`). Fixed by retargeting the placeholder test to
    "Plan" (the one tab still a placeholder) and scoping the new
    Activity-tab test's current-button assertions to the tab bar's own
    `<nav>`.
- `npm run build` (`vite build`) — clean, `38 modules transformed`, no
  warnings.

A third issue was self-caught during authoring, before any test was
written against it: an early draft of the segmented control's own
selected-state styling used inline `style={{ background: "var(--atlas-x)"
}}` conditionals instead of this codebase's established CSS-class-
toggle convention (`styles.segSelected`, matching E3's
`PerfBreakdownCard`) — fixed before writing tests against it.

No targeted correction was needed against an external Decision
Fidelity review for this candidate — every issue above was found
during this slice's own pre-verification and fixed before submission,
not after.

## M0-D12 bounded quality contract

1. **Protected outcome:** the mobile Atlas app's "Activity" tab
   renders a real, tappable 3-way segmented control and the real
   History segment content (4 real stats, all 10 real timeline
   entries, the real trailing note) with zero backend change and zero
   regression to any of the 20 existing test files.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** the Agents segment (reuses E4, separate
   future slice); the Cost segment (reuses E1-E3, separate future
   slice); F4 (Plan tab); the desktop History's own "Open … thread"
   button (not present in the real mobile markup for this surface).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every rendered surface and every segment
   switch is exercised by a React Testing Library render/interaction
   test; no browser-based visual verification was performed (tooling
   failure, already disclosed in this session for M2-E4/F1/F2, same
   root cause).
5. **Acceptance proof:** 21/21 test files, 157/157 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 2 modified files, 3 new files, all
   within `apps/atlas/src`; zero backend files; no new third-party
   dependency; E6's own files (`history/fixtures.ts`,
   `history/historyStyle.ts`) read-only, never modified.
7. **Proportionality ceiling:** one new presentational component, one
   new CSS module, one three-branch wiring change in an already-real
   shell — no new fixture data invented, no new design tokens
   invented.
8. **Stop and escalation rule:** rendering Agents/Cost segment content,
   or wiring any of the History timeline's entries to real navigation,
   is explicitly out of scope — future slices' job, not this one's to
   silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F3-ACTIVITY-TAB-HISTORY-01` |
| `phase` | `PendingDecisionFidelityReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f3-activity-tab-history.md"]` |
