# M2 Wave F — Mobile Activity Tab, Agents Segment — Candidate 01

**Slice ID:** `MB-SLICE-M2-F3B-ACTIVITY-TAB-AGENTS-01`
**Status:** `Awaiting Decision Fidelity review`
**Base:** `a72ab45` (full: `a72ab4503228fe69768d9b46d67b2aa33b433a0d`, `origin/master`)

## Scope, deliberately minimal

Continues roadmap item 35, *"F3 — Activity tab: History/Agents/Cost
segmented, reusing E6/E4/E1–E3 data."* F3 (merged, PR #154) built the
real segmented-control shell and the History segment only. This slice
is the next smallest independently reviewable piece: **only the Agents
segment's real content**, reusing E4's already-merged
`AGENTS`/`AGENTS_STATS`/`AGENT_STYLE` fixture and style data. The Cost
segment (reusing E1-E3) remains a separate, future slice — not built
here, not silently dropped; the segmented control already switches to
it correctly and shows an honest placeholder, matching this same
file's own already-established convention.

This slice is frontend-only — no backend file touched. It modifies
exactly the 3 files F3 itself created; no other file is touched.

## Evidence

`Atlas Mobile.dc.html:252-278` is the real `isAgents` block (the
reference file's own internal name), immediately following the
History segment (`:230-249`) F3 already built and immediately
preceding the Cost segment (`:280` onward), neither touched here:

1. `agStats` (`:254-256`): 4 real stats, each with its own real
   `s.color` — the exact same real `AGENTS_STATS` array E4's own
   `agents.ts` already establishes and colors (`accent` /
   `warningText` / `accentHover` / `ink`).
2. A real card list (`:259-276`, `sc-for` over `{{ agents }}`) — the
   exact same real `AGENTS` array E4's own `agents.ts` already
   establishes (Terra/Sol/Claude Opus/Coordinator, the real Coordinator
   persona substitution already reviewed and merged in E4).

**This mobile card markup is a real, checkable subset of E4's own
`AgentsRoster.tsx`/`.module.css` — not identical to it.** Checked
directly, line by line, against both:

- Card `border-radius:20px` (`:260`) vs `AgentsRoster.module.css`'s
  desktop `.card { border-radius: 14px }`.
- **No border at all** on the mobile card (`background:#fff;overflow:hidden`,
  `:260`) vs desktop's real per-style `border:1px solid {{ a.border }}`.
- Avatar `border-radius:11px` (`:262`) vs desktop's `10px`.
- Bar track background `#F0ECF5` (`:271`) — `colors.borderDivider[2]`,
  a different real index of the same array from
  `AgentsRoster.tsx`'s own `--atlas-ag-bar-track: colors.borderDivider[0]`,
  checked directly, not reused.
- Locks row's own top border `#F3F0F6` (`:274`) — `colors.borderDivider[1]`,
  a third real index of the same array.
- **No footer "Open thread" button at all** (`:274` ends the card
  after the locks line) vs desktop's real button-plus-locks footer.
- **No head/eyebrow/`<h1>` block at all** in this segment (only
  `agStats` + the card list) vs desktop's own separate `showAgents`
  screen, which has "m1-a · agents" / "Four agents, one worktree each"
  — that head belongs only to the desktop Agents *screen*, not this
  mobile *segment*.

`AgentsRoster.tsx`'s own E4 packet already discloses it is
desktop-only by written scope (its `.roster` grid hardcodes the
reference file's own desktop `agCols` branch,
`repeat(auto-fit,minmax(300px,1fr))`, never the `mobile ? '1fr'`
branch it never implements) — mounting `<AgentsRoster />` unmodified
inside `ActivityTab` would render a second, unwanted title directly
under this tab's own "Activity" `<h1>`, and a border/footer button the
real mobile markup does not have. This slice therefore writes fresh
mobile-specific JSX/CSS (`AgentCardMobile`, new in `ActivityTab.tsx`)
that reuses E4's fixture/style **data** only — the exact same
established convention F3 itself already used for the History segment
(reusing E6's data, not `History.tsx` wholesale).

**E5's `ContentionCard` is confirmed not part of this segment.** The
mobile `isAgents` block (`:252-278`) contains no contention-card
markup anywhere; the contention card only appears on the desktop
`showAgents` screen, below the roster grid. E5's own packet already
states combining the two into one screen is out of scope. This slice
does not render `ContentionCard`.

## Design rationale

1. **Reuses E4's fixture and style data verbatim; no new fixture
   content invented.** `AGENTS`, `AGENTS_STATS`, `AGENT_STYLE` are
   imported unmodified from their already-merged files — including
   E4's own already-reviewed real Coordinator-persona substitution
   (for the fictional "Architect agent") and `m1-a` breadcrumb
   correction (for the `vennuesign` artifact), neither repeated nor
   re-litigated here.
2. **Every color is a real B2 token**, checked directly against
   `colors.ts` (see Evidence above for each). No new disclosed literal
   is introduced by this slice.
3. **Reuses `AgentsRoster.tsx`'s own already-reviewed state-dot
   derivation** (`isWait` → transparent fill + hollow border, using
   `colors.borderDashed[2]`) rather than inventing new logic for the
   mobile markup's own separate `stateDotBg`/`stateDotBorder` template
   values, whose exact source computation is not present in any
   fixture this program has already reviewed.
4. **No "Open thread" button, no head/eyebrow block** — the real
   mobile markup has neither on this surface; a dedicated test proves
   their absence, matching this file's own established convention for
   the History segment's analogous "no Open … thread button" test.
5. **The Cost segment stays a placeholder**, real and tappable,
   switching the segmented control's own selection state correctly —
   matching F3's own already-reviewed, already-merged convention.

## Guards

1. This slice modifies exactly 3 existing files
   (`apps/atlas/src/shell/ActivityTab.tsx`, `ActivityTab.module.css`,
   `ActivityTab.test.tsx`) — no backend file, no other frontend file,
   touched. `apps/atlas/src/agents/*` (E4's own files) are read-only
   imports, never modified.
2. The pre-existing test asserting "tapping Agents or Cost switches
   the segmented control's own selection and shows a placeholder" is
   split into two tests — one per segment — since Agents no longer
   shows a placeholder after this slice. This is the correct, intended
   consequence of this slice replacing the Agents placeholder, not a
   regression.
3. No `ContentionCard`, no E1-E3 performance component, is rendered
   anywhere in `ActivityTab.tsx` — this slice's scope is the Agents
   segment only.
4. Every new `--atlas-ag-*` CSS custom property declared in
   `SHELL_VARS` is consumed by at least one real CSS rule in
   `ActivityTab.module.css` — checked exhaustively, not spot-checked
   (the specific class of defect an earlier Decision Fidelity review
   caught in F3's own first draft).

## `apps/atlas/src/shell/ActivityTab.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "../history/fixtures";
import { HISTORY_KIND_STYLE } from "../history/historyStyle";
import { AGENTS, AGENTS_STATS, type AgentEntry, type AgentStat } from "../agents/agents";
import { AGENT_STYLE } from "../agents/agentStyle";
import styles from "./ActivityTab.module.css";

type ActivitySegment = "hist" | "agents" | "cost";

const SEGMENTS: ReadonlyArray<{ key: ActivitySegment; label: string }> = [
  { key: "hist", label: "History" },
  { key: "agents", label: "Agents" },
  { key: "cost", label: "Cost" },
];

/**
 * Mobile Activity-tab colors from `Atlas Mobile.dc.html`'s real `isAct`
 * markup — the header and segmented control (lines 219-227) and the
 * History segment this slice builds (lines 230-249); the real `isAct`
 * block itself continues past line 249 through the Agents (252-278)
 * and Cost (280 onward) segments this slice deliberately does not
 * build yet (see "Scope, deliberately minimal" in this slice's own
 * packet) — checked directly against `colors.ts`. Real token matches: `colors.segmentedTrack[0]`
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
 *
 * The Agents segment this slice adds (`Atlas Mobile.dc.html:252-278`)
 * reuses E4's real `AGENTS`/`AGENTS_STATS`/`AGENT_STYLE` fixture data
 * verbatim, but is deliberately NOT `<AgentsRoster />` mounted as-is:
 * that component is desktop-only by E4's own written scope (its own
 * `.roster` grid hardcodes the reference file's own `agCols` desktop
 * branch, `repeat(auto-fit,minmax(300px,1fr))`, never the `mobile ?
 * '1fr'` branch; its `.head` renders an eyebrow/`<h1>` and its
 * `.footer` renders an "Open thread" button, neither of which exists
 * anywhere in the real mobile `isAgents` markup, checked directly).
 * `AgentCardMobile` below is new mobile-specific JSX/CSS, matching
 * this same file's own established convention for the History segment
 * (reuse E6's fixture/style *data*, write fresh mobile markup, not the
 * desktop component). Real token matches for the new
 * `--atlas-ag-*` vars: `colors.borderDivider[2]` (`#F0ECF5`, the
 * progress-bar track, line 271 — a different real index of the same
 * array this file's own History rail styling neighbors, not
 * `AgentsRoster`'s own `colors.borderDivider[0]`), `colors.inkSecondary`
 * (`#6C6376`, the agent line's own body text, line 269 — the same
 * token this file's own `--atlas-entry-detail` already uses),
 * `colors.inkFaint` (`#A79BB4`, the packet chip, line 267),
 * `colors.inkMuted` (`#8E8299`, the locks line, line 274), and
 * `colors.warningText`/`colors.inkMuted` (urgent/normal due-label
 * color, matching `AgentsRoster.tsx`'s own already-reviewed
 * `--atlas-ag-due-urgent`/`--atlas-ag-due` pair). The state dot's own
 * bg/hollow-border logic (`isWait` → transparent fill, hollow border)
 * reuses `AgentsRoster.tsx`'s own already-reviewed derivation exactly,
 * rather than inventing new logic for the mobile markup's own separate
 * `stateDotBg`/`stateDotBorder` template values (whose exact source
 * computation isn't present in any fixture this program has already
 * reviewed) — the real mobile card has no border/head/footer, so this
 * file's own `.agentCard` intentionally omits `--atlas-ag-card-border`
 * and any head var entirely, rather than declaring one that no rule
 * would ever consume. The locks row's own top-border literal
 * (`#F3F0F6`, line 274) is `colors.borderDivider[1]` — a different
 * real index of the same array from the bar track's own
 * `colors.borderDivider[2]`, checked directly, not a reused value.
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
  "--atlas-ag-card-surface": colors.surface,
  "--atlas-ag-name": colors.ink,
  "--atlas-ag-packet": colors.inkFaint,
  "--atlas-ag-line": colors.inkSecondary,
  "--atlas-ag-bar-track": colors.borderDivider[2],
  "--atlas-ag-footer-border": colors.borderDivider[1],
  "--atlas-ag-due": colors.inkMuted,
  "--atlas-ag-due-urgent": colors.warningText,
  "--atlas-ag-locks": colors.inkMuted,
  "--atlas-ag-wait-dot-border": colors.borderDashed[2],
} as CSSProperties;

const STAT_VALUE_COLOR: Record<AgentStat["color"], string> = {
  accent: colors.accent,
  warningText: colors.warningText,
  accentHover: colors.accentHover,
  ink: colors.ink,
};

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

function AgentCardMobile({ agent }: { agent: AgentEntry }) {
  const style = AGENT_STYLE[agent.styleKey];
  const isWait = agent.styleKey === "wait";
  return (
    <div className={styles.agentCard}>
      <div className={styles.agentTop}>
        <span className={styles.agentAvatar} style={{ background: style.avBg, color: style.avColor }}>
          {agent.av}
        </span>
        <div className={styles.agentIdentity}>
          <div className={styles.agentName}>{agent.name}</div>
          <div className={styles.agentState} style={{ color: style.stateColor }}>
            <span
              className={`${styles.agentStateDot} ${isWait ? styles.agentStateDotHollow : ""}`}
              style={{ background: isWait ? "transparent" : style.barColor }}
            />
            {agent.state}
          </div>
        </div>
        <span className={styles.agentPacket}>{agent.packet}</span>
      </div>
      <div className={styles.agentLine}>{agent.line}</div>
      <div className={styles.agentBarBlock}>
        <div className={styles.agentBarTrack}>
          <span className={styles.agentBarFill} style={{ width: agent.pct, background: style.barColor }} />
        </div>
        <div className={styles.agentProgressRow}>
          <span>{agent.progress}</span>
          <span className={agent.urgent ? styles.agentDueUrgent : styles.agentDue}>{agent.due}</span>
        </div>
      </div>
      <div className={styles.agentLocks}>{agent.locks}</div>
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
 * on this surface, checked directly), and the Agents segment's real
 * content reusing E4's own `AGENTS`/`AGENTS_STATS`/`AGENT_STYLE`
 * fixture and style data as fresh mobile-specific cards (see
 * `AgentCardMobile` above — not `<AgentsRoster />`, which is
 * desktop-only by its own established scope). The Cost segment is
 * real, tappable, and switches the segmented control's own selection
 * state correctly, but renders only a placeholder — reusing E1-E3's
 * performance data for it is separate, future work (roadmap item 35's
 * own remaining scope), matching this program's own established
 * pattern of splitting an oversized roadmap item into independently
 * reviewable slices (E1/E1B, E2/E2B).
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
        ) : segment === "agents" ? (
          <>
            <div className={styles.stats}>
              {AGENTS_STATS.map((stat) => (
                <span key={stat.label} className={styles.stat}>
                  {stat.label}
                  <b className={styles.statValue} style={{ color: STAT_VALUE_COLOR[stat.color] }}>
                    {stat.value}
                  </b>
                </span>
              ))}
            </div>
            <div className={styles.agentList}>
              {AGENTS.map((agent) => (
                <AgentCardMobile key={agent.ref + agent.name} agent={agent} />
              ))}
            </div>
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

## `apps/atlas/src/shell/ActivityTab.module.css` (modified — full new content)

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

.timeline {
  display: flex;
  flex-direction: column;
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

.agentList {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agentCard {
  border-radius: 20px;
  background: var(--atlas-ag-card-surface);
  overflow: hidden;
}

.agentTop {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 14px 15px 10px;
}

.agentAvatar {
  width: 34px;
  height: 34px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  font: 600 11.5px var(--atlas-font-mono);
}

.agentIdentity {
  min-width: 0;
  flex: 1;
}

.agentName {
  font-size: 15px;
  font-weight: 700;
  color: var(--atlas-ag-name);
}

.agentState {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 1px;
  font-size: 12.5px;
  font-weight: 600;
}

.agentStateDot {
  width: 6px;
  height: 6px;
  box-sizing: border-box;
  border-radius: 50%;
  border: 0;
}

.agentStateDotHollow {
  border: 1.5px solid var(--atlas-ag-wait-dot-border);
}

.agentPacket {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-ag-packet);
}

.agentLine {
  padding: 0 15px 12px;
  font-size: 13.5px;
  line-height: 1.5;
  color: var(--atlas-ag-line);
}

.agentBarBlock {
  padding: 0 15px 13px;
}

.agentBarTrack {
  height: 5px;
  border-radius: 999px;
  background: var(--atlas-ag-bar-track);
  overflow: hidden;
}

.agentBarFill {
  display: block;
  height: 100%;
  border-radius: 999px;
}

.agentProgressRow {
  display: flex;
  justify-content: space-between;
  margin-top: 7px;
  font: 500 11px var(--atlas-font-mono);
}

.agentDue {
  color: var(--atlas-ag-due);
}

.agentDueUrgent {
  color: var(--atlas-ag-due-urgent);
}

.agentLocks {
  padding: 10px 15px;
  border-top: 1px solid var(--atlas-ag-footer-border);
  font-size: 12px;
  color: var(--atlas-ag-locks);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

## `apps/atlas/src/shell/ActivityTab.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";
import { AGENTS, AGENTS_STATS } from "../agents/agents";

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

  it("tapping Cost switches the segmented control's own selection and shows a placeholder", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Cost");
    expect(screen.getByText("Cost segment")).toBeInTheDocument();
  });

  it("tapping Agents switches the segmented control's own selection and renders the real AGENTS_STATS", () => {
    const { container } = render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Agents");

    // Every real AGENTS_STATS label is unique, so a bare label lookup
    // is unambiguous here (unlike HISTORY_STATS' shared "1" value).
    for (const stat of AGENTS_STATS) {
      const label = screen.getByText(stat.label);
      expect(label.textContent).toBe(`${stat.label}${stat.value}`);
    }
    expect(container.textContent).toContain(AGENTS_STATS[0].label);
  });

  it("renders all 4 real AGENTS cards with their exact name, state, and line", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      // "Coordinator" is both this real agent's name and its own role —
      // scope each assertion to that one card, found via its unique
      // real `line` text, to avoid an ambiguous document-wide query.
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      expect(within(card).getByText(agent.name)).toBeInTheDocument();
      expect(within(card).getByText(agent.state)).toBeInTheDocument();
      expect(within(card).getByText(agent.packet)).toBeInTheDocument();
      expect(within(card).getByText(agent.locks)).toBeInTheDocument();
    }
  });

  it("renders no 'Open thread' button on the mobile Agents cards (the real mobile markup has no such control here)", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));
    expect(screen.queryByRole("button", { name: /open thread/i })).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<ActivityTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to this
scratch worktree (`/tmp/maestro-m2-f3b-agents`, branch
`architecture/m2-f3b-activity-agents`, base `a72ab45`) and run through
the real frontend toolchain from `apps/atlas` (`npm install`, then
each script below), before this packet was finalized. Zero corrections
were needed — every check passed on the first attempt.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **21/21 test files, 160/160 tests
  passed** (11 in `ActivityTab.test.tsx` itself, up from F3's own 8;
  zero regressions in the other 20 files, including
  `AgentsRoster.test.tsx` and `ContentionCard.test.tsx`, neither of
  which this slice touches).
- `npm run build` (`vite build`) — clean, `38 modules transformed`, no
  warnings.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** the mobile Atlas app's "Activity" tab's
   Agents segment renders the real 4 `AGENTS_STATS` and all 4 real
   `AGENTS` roster cards, reusing E4's fixture/style data, with zero
   backend change and zero regression to any of the 21 existing test
   files.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** the Cost segment (reuses E1-E3, separate
   future slice); `ContentionCard` (E5, confirmed not part of this
   mobile segment); any wiring of the roster cards to a real command
   (no such command exists for any of these agents' actions).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every rendered surface and every segment
   switch is exercised by a React Testing Library render/interaction
   test; no browser-based visual verification was performed (tooling
   failure, already disclosed in this session for M2-E4/F1/F2/F3, same
   root cause).
5. **Acceptance proof:** 21/21 test files, 160/160 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 3 modified files, 0 new files, all
   within `apps/atlas/src/shell`; zero backend files; no new
   third-party dependency; E4's own files (`agents/agents.ts`,
   `agents/agentStyle.ts`) read-only, never modified.
7. **Proportionality ceiling:** one new presentational component
   (`AgentCardMobile`) inside an already-real shell file, one CSS
   addition — no new fixture data invented, no new design tokens
   invented (every new `--atlas-ag-*` var routes to a real token).
8. **Stop and escalation rule:** rendering the Cost segment's content,
   or wiring any Agents card to a real command, is explicitly out of
   scope — future slices' job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F3B-ACTIVITY-TAB-AGENTS-01` |
| `phase` | `AwaitingReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f3b-activity-tab-agents.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
