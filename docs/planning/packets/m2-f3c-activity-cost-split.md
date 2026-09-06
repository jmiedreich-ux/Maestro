# M2 Wave F — Mobile Activity Tab, Cost Segment (Weekly Window + Split) — Candidate 01

**Slice ID:** `MB-SLICE-M2-F3C-ACTIVITY-COST-SPLIT-01`
**Status:** `Awaiting Decision Fidelity review`
**Base:** `8aa33ce` (full: `8aa33ce5787e296d95dee0b4921ebd77e2b752dd`, `origin/master`)

## Scope, deliberately minimal

Continues roadmap item 35, *"F3 — Activity tab: History/Agents/Cost
segmented, reusing E6/E4/E1–E3 data."* History (F3) and Agents (F3B)
are already merged. This slice is the next smallest independently
reviewable piece of the Cost segment: **only its first two real
blocks** — the weekly-window card and the "m1-a split" card (reusing
E1B's `WEEKLY_WINDOW` and E3's `SPLIT`/`SPLIT_BASES` fixture data
verbatim). The "Per action" records list (reusing E2/E2B's data) is a
separate, future slice — not built here, not silently dropped.

This slice is frontend-only — no backend file touched. It modifies
exactly the 3 files F3/F3B already established
(`ActivityTab.tsx`/`.module.css`/`.test.tsx`); no other file is
touched. `apps/atlas/src/performance/*` (E1B's/E3's own files) are
read-only imports, never modified.

## Evidence

`Atlas Mobile.dc.html:280-309` is the exact real markup for these two
blocks, immediately following the Agents segment (`:252-278`) and
immediately preceding the "Per action" records list (`:311-337`,
deferred):

1. **Weekly-window card** (`:281-285`): eyebrow "openai weekly
   window", a sentence — "61% controlled + 14% coarse + " (plain) +
   "**5% unattributed**" (bold, amber `#8A5A08`) + " = " (plain) +
   "**80%**" (bold) + " observed change" (plain) — and a meta line
   "observed 15:02 · local Qwen kept separate" (`#A79BB4`).
2. **"m1-a split" card** (`:287-309`): an eyebrow "m1-a split", a real
   3-way segmented control (`split.bases` — Cost/Tokens/Time, `flex:1`
   each on mobile, unlike desktop's `flex:none`), a "share of {{
   split.basisNote }}" line, then two groups ("by role", "by kind of
   work"), each a stacked percentage bar (`g.parts`, per-part
   `p.w`/`p.color`) plus a legend (dot + label + pct + right-aligned
   abs, one per line — a column layout, unlike desktop's own
   flex-wrap row), and a trailing caveat line.

**Real token matches, checked directly against `colors.ts`:**
`colors.inkMuted` (`#8E8299`, both eyebrows), `colors.warningText`
(`#8A5A08`, the unattributed figure), `colors.inkFaint` (`#A79BB4`,
meta/group-name/legend-abs — matching E1B's `WeeklyWindowStrip.tsx`
and E3's `PerfBreakdownCard.tsx` token choices exactly),
`colors.inkSecondary` (`#6C6376`, the legend label — the same token
this file's own `--atlas-entry-detail`/`--atlas-ag-line` already use),
`colors.segmentedTrack[2]` (`#F2EFF7`, both the segmented control's
own track and the bar's own track — a different real index of the
same array this file's own outer segmented control already uses `[0]`
from), and the exact same 4 real colors E3's own `PerfBreakdownCard.tsx`
already discloses for its own `SEGMENT_CLASS`
(`colors.accent`/`colors.review`/`colors.success`/`colors.borderDashed[2]`).
The weekly-window sentence's own body-text color (`#4C4457`) is a
disclosed literal — checked against every color family in `colors.ts`,
no match.

**Real fact, disclosed, not silently reused.** This slice reuses
`WEEKLY_WINDOW`'s own real `meta` ("observed 15:02 · resets Mon
00:00") and `caption` ("Local Qwen is shown as capacity and time
only...") fields as two separate lines — exactly matching E1B's own
`WeeklyWindowStrip.tsx` rendering — rather than transcribing the
mobile mockup's own shorter, compressed single line ("observed 15:02
· local Qwen kept separate"), which paraphrases both real fields into
one and drops real information. This is the same single-source-of-
identity precedent F3's own `HISTORY_EMPTY_NOTE` reuse and F2's own C7
eyebrow/title reuse already established.

## Design rationale

1. **Reuses E1B's and E3's fixture data verbatim; no new fixture
   content invented.** `WEEKLY_WINDOW`, `SPLIT`, `SPLIT_BASES` are
   imported unmodified — including E3's own already-reviewed real
   Local-Qwen persona substitution (for the fictional "Architect
   agent" in `SPLIT.cost.role`), not repeated or re-litigated here.
2. **Reuses E3's own already-reviewed bar-width derivation**
   (`Math.max(pct, 0.6) + '%'`, a 0%-share part still renders a thin,
   visible sliver) verbatim, rather than inventing new math.
3. **The 4 real segment colors are applied via inline per-index
   style** (`SPLIT_COLORS[index]`), not 4 new CSS classes duplicating
   E3's own static `.segColor0`-`.segColor3` — matching this file's
   own established convention for per-item dynamic coloring
   (`HistoryRow`, `AgentCardMobile`), since the values are always the
   same 4 regardless of which basis is selected but this file already
   has a working inline-style pattern for exactly this shape of data.
4. **Every new `--atlas-week-*`/`--atlas-split-*` CSS custom property
   is consumed by at least one real CSS rule** — checked exhaustively
   (the specific class of defect an earlier Decision Fidelity review
   caught in F3's own first draft).
5. **The Cost segment's own outer selection state no longer needs a
   generic trailing placeholder branch** — with all 3 outer segments
   now real (History, Agents, and this slice's Cost content), the
   ternary chain's final branch renders `<CostSegment />` directly.

## Guards

1. This slice modifies exactly 3 existing files
   (`apps/atlas/src/shell/ActivityTab.tsx`, `ActivityTab.module.css`,
   `ActivityTab.test.tsx`) — no backend file, no other frontend file,
   touched. `apps/atlas/src/performance/*` (E1B's/E3's own files) are
   read-only imports, never modified.
2. The pre-existing test asserting the Cost segment's own placeholder
   text ("Cost segment") is replaced with real-content assertions —
   the correct, intended consequence of this slice replacing that
   placeholder, not a regression.
3. No `PerfBreakdownCard`/`WeeklyWindowStrip`/`PerfRecordsList`
   component is rendered anywhere in `ActivityTab.tsx` — this file
   writes fresh mobile-specific JSX/CSS reusing only the desktop
   components' underlying data, matching this file's own established
   convention for the History and Agents segments.
4. The "Per action" records list (E2/E2B's data) is not rendered here
   — real, tappable segmented-control switching to Cost already shows
   real content (the two cards this slice builds); no placeholder text
   remains for the deferred records list, since simply not rendering
   it yet is not a corner cut requiring one (the segmented control
   itself has no 4th "sub-tab" needing a placeholder — the records
   list is additional content within the same Cost segment, appended
   by the next slice).

## `apps/atlas/src/shell/ActivityTab.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "../history/fixtures";
import { HISTORY_KIND_STYLE } from "../history/historyStyle";
import { AGENTS, AGENTS_STATS, type AgentEntry, type AgentStat } from "../agents/agents";
import { AGENT_STYLE } from "../agents/agentStyle";
import { WEEKLY_WINDOW } from "../performance/weeklyWindow";
import { SPLIT, SPLIT_BASES, type SplitBasisKey, type SplitPart } from "../performance/perfBreakdown";
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
 *
 * **Corrected — non-blocking finding from Decision Fidelity review:**
 * the per-stat value color (`AGENTS_STATS`' own `stat.color` enum) is
 * the exact same 4-value enum `AgentsRoster.tsx` already handles via
 * named CSS custom properties (`--atlas-ag-stat-accent` etc.) plus
 * static classes (`STAT_VALUE_CLASS`) — this file's first draft
 * instead applied it as a raw inline `style={{ color: ... }}`, an
 * undisclosed deviation from that sibling component's own established
 * convention for identical data (both render identically; this was a
 * consistency gap, not a functional defect). Fixed to match:
 * `STAT_VALUE_CLASS` below maps each `stat.color` to a static class
 * consuming one of four new `--atlas-ag-stat-*` vars, exactly mirroring
 * `AgentsRoster.tsx`'s own already-reviewed pattern.
 *
 * The Cost segment's first two real blocks this slice adds
 * (`Atlas Mobile.dc.html:280-309`) reuse E1B's real `WEEKLY_WINDOW`
 * fixture and E3's real `SPLIT`/`SPLIT_BASES` fixture data verbatim —
 * both already real, reviewed, and (for `SPLIT.cost.role`) already
 * carrying the real Local-Qwen persona correction for the fictional
 * "Architect agent," not re-litigated here. Real token matches for the
 * new `--atlas-week-*`/`--atlas-split-*` vars: `colors.inkMuted`
 * (`#8E8299`, both eyebrows — "openai weekly window" line 282,
 * "m1-a split" line 288), `colors.warningText` (`#8A5A08`, the
 * unattributed figure, line 283), `colors.inkFaint` (`#A79BB4`, meta/
 * group-name/legend-abs colors, matching E1B's own `WeeklyWindowStrip.tsx`
 * and E3's own `PerfBreakdownCard.tsx` token choices exactly),
 * `colors.inkSecondary` (`#6C6376`, the legend label, line 303 — the
 * same token this file's own `--atlas-entry-detail` and `--atlas-ag-line`
 * already use), `colors.segmentedTrack[2]` (`#F2EFF7`, both the
 * segmented control's own track and the bar's own track, lines 289/298
 * — the third real index of the array this file's own outer segmented
 * control already uses `[0]` from), and the same 4 real
 * `SPLIT_COLORS` E3's own `PerfBreakdownCard.tsx` already discloses
 * (`colors.accent`/`colors.review`/`colors.success`/`colors.borderDashed[2]`),
 * applied here via inline per-index style rather than E3's own static
 * CSS classes — matching this file's own established convention for
 * per-item dynamic coloring (`HistoryRow`, `AgentCardMobile`), not
 * duplicating four new always-identical CSS classes. The weekly-window
 * sentence's own body-text color (`#4C4457`, line 283) is a disclosed
 * literal, checked against every color family in `colors.ts` — no
 * token matches.
 *
 * **Real fact, disclosed, not silently reused:** this slice reuses
 * `WEEKLY_WINDOW`'s own already-real `meta` ("observed 15:02 · resets
 * Mon 00:00") and `caption` ("Local Qwen is shown as capacity and time
 * only...") fields as two separate lines — exactly matching E1B's own
 * `WeeklyWindowStrip.tsx` rendering — rather than transcribing the
 * mobile mockup's own shorter, compressed single line ("observed 15:02
 * · local Qwen kept separate", line 284), which paraphrases both real
 * fields into one and drops real information. This is the same
 * single-source-of-identity precedent F3's own `HISTORY_EMPTY_NOTE`
 * reuse and F2's own C7 eyebrow/title reuse already established: state
 * the one real fact once, not a second, lossier mockup-specific
 * abbreviation of it.
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
  "--atlas-ag-stat-accent": colors.accent,
  "--atlas-ag-stat-warning": colors.warningText,
  "--atlas-ag-stat-accent-hover": colors.accentHover,
  "--atlas-ag-stat-ink": colors.ink,
  "--atlas-cost-card-surface": colors.surface,
  "--atlas-week-label": colors.inkMuted,
  "--atlas-week-body": "#4C4457",
  "--atlas-week-warning": colors.warningText,
  "--atlas-week-meta": colors.inkFaint,
  "--atlas-week-caption": colors.inkFaint,
  "--atlas-split-track": colors.segmentedTrack[2],
  "--atlas-split-seg-selected-bg": colors.segmentedSelected,
  "--atlas-split-seg-selected-ink": colors.ink,
  "--atlas-split-seg-ink": colors.inkMuted,
  "--atlas-split-basis-note": colors.inkMuted,
  "--atlas-split-group-name": colors.inkFaint,
  "--atlas-split-legend-label": colors.inkSecondary,
  "--atlas-split-legend-pct": colors.ink,
  "--atlas-split-legend-abs": colors.inkFaint,
  "--atlas-split-caveat": colors.inkMuted,
} as CSSProperties;

const SPLIT_COLORS = [colors.accent, colors.review, colors.success, colors.borderDashed[2]];

/**
 * Transcribed verbatim from `PerfBreakdownCard.tsx`'s own bar-width
 * derivation (`w: Math.max(pct, 0.6) + '%'`) — a 0%-share part still
 * renders a thin, visible sliver rather than vanishing entirely.
 */
function barWidth(pct: number): string {
  return `${Math.max(pct, 0.6)}%`;
}

const STAT_VALUE_CLASS: Record<AgentStat["color"], string> = {
  accent: styles.statValueAccent,
  warningText: styles.statValueWarning,
  accentHover: styles.statValueAccentHover,
  ink: styles.statValueInk,
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

function CostSplitGroup({ name, parts }: { name: string; parts: SplitPart[] }) {
  return (
    <div className={styles.splitGroup}>
      <div className={styles.splitGroupName}>{name}</div>
      <div className={styles.splitBar}>
        {parts.map((part, index) => (
          <span
            key={part.label}
            className={styles.splitBarSegment}
            style={{ width: barWidth(part.pct), background: SPLIT_COLORS[index] }}
          />
        ))}
      </div>
      <div className={styles.splitLegend}>
        {parts.map((part, index) => (
          <div key={part.label} className={styles.splitLegendItem}>
            <span className={styles.splitLegendDot} style={{ background: SPLIT_COLORS[index] }} />
            <span className={styles.splitLegendLabel}>{part.label}</span>
            <b className={styles.splitLegendPct}>{part.pct}%</b>
            <span className={styles.splitLegendAbs}>{part.abs}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function CostSegment() {
  const [basis, setBasis] = useState<SplitBasisKey>("cost");
  const data = SPLIT[basis];

  return (
    <>
      <div className={styles.weekCard}>
        <div className={styles.weekLabel}>openai weekly window</div>
        <div className={styles.weekBody}>
          {WEEKLY_WINDOW.reconciledPercent} controlled + {WEEKLY_WINDOW.coarsePercent} coarse +{" "}
          <b className={styles.weekWarning}>{WEEKLY_WINDOW.unattributedPercent} unattributed</b> ={" "}
          <b>{WEEKLY_WINDOW.observedChangePercent}</b> observed change
        </div>
        <div className={styles.weekMeta}>{WEEKLY_WINDOW.meta}</div>
        <div className={styles.weekCaption}>{WEEKLY_WINDOW.caption}</div>
      </div>

      <div className={styles.splitCard}>
        <div className={styles.splitHead}>
          <span className={styles.splitLabel}>m1-a split</span>
        </div>
        <div className={styles.splitSegmented}>
          {SPLIT_BASES.map((b) => (
            <button
              key={b.key}
              type="button"
              className={`${styles.splitSegButton} ${basis === b.key ? styles.splitSegSelected : ""}`}
              onClick={() => setBasis(b.key)}
            >
              {b.label}
            </button>
          ))}
        </div>
        <div className={styles.splitBasisNote}>share of {data.note}</div>
        <CostSplitGroup name="by role" parts={data.role} />
        <CostSplitGroup name="by kind of work" parts={data.work} />
        <div className={styles.splitCaveat}>{data.caveat}</div>
      </div>
    </>
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
 * desktop-only by its own established scope). The Cost segment's real
 * content, reusing E1B's/E3's own fixture data (see `CostSegment`
 * above), begins with this slice — the weekly-window card and the
 * "m1-a split" card. The "Per action" records list (reusing E2/E2B's
 * data) is separate, future work (roadmap item 35's own remaining
 * scope), matching this program's own established pattern of
 * splitting an oversized roadmap item into independently reviewable
 * slices (E1/E1B, E2/E2B, F3/F3B).
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
                  <b className={`${styles.statValue} ${STAT_VALUE_CLASS[stat.color]}`}>{stat.value}</b>
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
          <CostSegment />
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

.statValueAccent {
  color: var(--atlas-ag-stat-accent);
}

.statValueWarning {
  color: var(--atlas-ag-stat-warning);
}

.statValueAccentHover {
  color: var(--atlas-ag-stat-accent-hover);
}

.statValueInk {
  color: var(--atlas-ag-stat-ink);
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

.weekCard {
  padding: 14px 15px;
  border-radius: 18px;
  background: var(--atlas-cost-card-surface);
}

.weekLabel {
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-week-label);
}

.weekBody {
  margin-top: 8px;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--atlas-week-body);
  text-wrap: pretty;
}

.weekWarning {
  color: var(--atlas-week-warning);
}

.weekMeta {
  margin-top: 7px;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-week-meta);
}

.weekCaption {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--atlas-week-caption);
  text-wrap: pretty;
}

.splitCard {
  margin-top: 10px;
  padding: 14px 15px;
  border-radius: 18px;
  background: var(--atlas-cost-card-surface);
}

.splitHead {
  display: flex;
  align-items: center;
  gap: 8px;
}

.splitLabel {
  font: 600 10px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-week-label);
}

.splitSegmented {
  display: flex;
  gap: 3px;
  margin-top: 10px;
  padding: 3px;
  border-radius: 11px;
  background: var(--atlas-split-track);
}

.splitSegButton {
  flex: 1;
  min-height: 34px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--atlas-split-seg-ink);
  cursor: pointer;
  font-size: 12.5px;
  font-weight: 600;
}

.splitSegSelected {
  background: var(--atlas-split-seg-selected-bg);
  color: var(--atlas-split-seg-selected-ink);
}

.splitBasisNote {
  margin-top: 9px;
  font-size: 12.5px;
  color: var(--atlas-split-basis-note);
}

.splitGroup {
  margin-top: 14px;
}

.splitGroupName {
  font: 600 9.5px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-split-group-name);
}

.splitBar {
  display: flex;
  gap: 2px;
  margin-top: 8px;
  height: 11px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--atlas-split-track);
}

.splitBarSegment {
  display: block;
}

.splitLegend {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-top: 9px;
}

.splitLegendItem {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-size: 13px;
}

.splitLegendDot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: 3px;
}

.splitLegendLabel {
  color: var(--atlas-split-legend-label);
}

.splitLegendPct {
  margin-left: auto;
  font-family: var(--atlas-font-mono);
  color: var(--atlas-split-legend-pct);
}

.splitLegendAbs {
  flex: none;
  width: 82px;
  text-align: right;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-split-legend-abs);
}

.splitCaveat {
  margin-top: 12px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--atlas-split-caveat);
  text-wrap: pretty;
}
```

## `apps/atlas/src/shell/ActivityTab.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ActivityTab } from "./ActivityTab";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS } from "../history/fixtures";
import { AGENTS, AGENTS_STATS } from "../agents/agents";
import { WEEKLY_WINDOW } from "../performance/weeklyWindow";
import { SPLIT, SPLIT_BASES } from "../performance/perfBreakdown";

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

  it("tapping Cost switches the segmented control's own selection and renders the real weekly-window card", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));
    const current = screen.getAllByRole("button", { current: true });
    // Scoped to the outer segmented control only: the split card's own
    // segmented control (Cost/Tokens/Time) also uses `aria-current`-free
    // plain buttons here, but its own selected button carries no
    // `current` role attribute, so this stays unambiguous.
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Cost");

    expect(screen.getByText("openai weekly window")).toBeInTheDocument();
    // Real fixture fields, not the mobile mockup's own shorter,
    // compressed single line — see this file's own doc comment.
    expect(screen.getByText(WEEKLY_WINDOW.meta)).toBeInTheDocument();
    expect(screen.getByText(WEEKLY_WINDOW.caption)).toBeInTheDocument();
    expect(screen.getByText(`${WEEKLY_WINDOW.unattributedPercent} unattributed`)).toBeInTheDocument();
    expect(screen.getByText(`${WEEKLY_WINDOW.observedChangePercent}`)).toBeInTheDocument();
  });

  it("renders the real 'm1-a split' card defaulting to the Cost basis, with all real role and work parts", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    expect(screen.getByText("m1-a split")).toBeInTheDocument();
    expect(screen.getByText("by role")).toBeInTheDocument();
    expect(screen.getByText("by kind of work")).toBeInTheDocument();

    const data = SPLIT.cost;
    expect(screen.getByText(`share of ${data.note}`)).toBeInTheDocument();
    expect(screen.getByText(data.caveat)).toBeInTheDocument();
    for (const part of [...data.role, ...data.work]) {
      const label = screen.getByText(part.label);
      const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
      expect(within(item).getByText(`${part.pct}%`)).toBeInTheDocument();
      expect(within(item).getByText(part.abs)).toBeInTheDocument();
    }
  });

  it("tapping Tokens or Time in the split card's own segmented control switches to that basis's real data", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Cost" }));

    for (const basis of SPLIT_BASES) {
      if (basis.key === "cost") continue;
      fireEvent.click(screen.getByRole("button", { name: basis.label }));
      const data = SPLIT[basis.key];
      expect(screen.getByText(`share of ${data.note}`)).toBeInTheDocument();
      expect(screen.getByText(data.caveat)).toBeInTheDocument();
      // The previous basis's own caveat must not linger.
      for (const other of SPLIT_BASES) {
        if (other.key === basis.key) continue;
        expect(screen.queryByText(SPLIT[other.key].caveat)).toBeNull();
      }
      // Every real role/work part for this basis, not just the note/caveat
      // strings — proves the switch re-derives the whole group, not just
      // the two summary lines.
      for (const part of [...data.role, ...data.work]) {
        const label = screen.getByText(part.label);
        const item = label.closest('[class*="splitLegendItem"]') as HTMLElement;
        expect(within(item).getByText(`${part.pct}%`)).toBeInTheDocument();
        expect(within(item).getByText(part.abs)).toBeInTheDocument();
      }
    }
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

  it("renders each real agent's exact progress-bar width, progress label, and due label with the correct urgent styling", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      const fill = card.querySelector('[class*="agentBarFill"]') as HTMLElement;
      expect(fill.style.width).toBe(agent.pct);

      const due = within(card).getByText(agent.due);
      expect(within(card).getByText(agent.progress)).toBeInTheDocument();
      // Only Coordinator's real fixture entry has `urgent: true` — every
      // other real agent must render the non-urgent due class instead.
      expect(due.className).toContain(agent.urgent ? "agentDueUrgent" : "agentDue");
      if (!agent.urgent) {
        expect(due.className).not.toContain("agentDueUrgent");
      }
    }
  });

  it("renders a hollow state dot only for Sol (the real fixture's only 'wait' styleKey), filled for the other 3", () => {
    render(<ActivityTab />);
    fireEvent.click(screen.getByRole("button", { name: "Agents" }));

    for (const agent of AGENTS) {
      const line = screen.getByText(agent.line);
      const card = line.closest('[class*="agentCard"]') as HTMLElement;
      const dot = card.querySelector('[class*="agentStateDot"]') as HTMLElement;
      const isWait = agent.styleKey === "wait";
      expect(dot.className.includes("agentStateDotHollow")).toBe(isWait);
      if (isWait) {
        expect(dot.style.background).toBe("transparent");
      } else {
        expect(dot.style.background).not.toBe("");
        expect(dot.style.background).not.toBe("transparent");
      }
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
scratch worktree (`/tmp/maestro-m2-f3c-cost`, branch
`architecture/m2-f3c-activity-cost`, base `8aa33ce`) and run through
the real frontend toolchain from `apps/atlas` (`npm install`, then
each script below), before this packet was finalized. Zero corrections
were needed — every check passed on the first attempt.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **22/22 test files, 172/172 tests
  passed** (15 in `ActivityTab.test.tsx` itself, up from F3B's own 11;
  zero regressions in the other 21 files, including
  `PerfBreakdownCard.test.tsx` and `WeeklyWindowStrip.test.tsx`,
  neither of which this slice touches).
- `npm run build` (`vite build`) — clean, `39 modules transformed`, no
  warnings.
- Every declared `--atlas-week-*`/`--atlas-split-*`/`--atlas-cost-*`
  custom property was cross-checked programmatically against
  `ActivityTab.module.css`'s own `var(...)` references — zero orphans
  either direction.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** the mobile Atlas app's "Activity" tab's Cost
   segment renders the real weekly-window card and the real "m1-a
   split" card (with its own real 3-way basis toggle), reusing E1B's/
   E3's fixture data, with zero backend change and zero regression to
   any of the 22 existing test files.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** the "Per action" records list (reuses E2/
   E2B, separate future slice); `PerfRecordsList`/`PerfBreakdownCard`/
   `WeeklyWindowStrip` themselves (not rendered — only their data is
   reused, matching this file's own established convention).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every rendered surface and every basis switch
   is exercised by a React Testing Library render/interaction test; no
   browser-based visual verification was performed (tooling failure,
   already disclosed in this session for M2-E4/F1/F2/F3/F3B, same root
   cause).
5. **Acceptance proof:** 22/22 test files, 172/172 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 3 modified files, 0 new files, all
   within `apps/atlas/src/shell`; zero backend files; no new
   third-party dependency; E1B's/E3's own files (`performance/weeklyWindow.ts`,
   `performance/perfBreakdown.ts`) read-only, never modified.
7. **Proportionality ceiling:** two new presentational sub-components
   (`CostSplitGroup`, `CostSegment`) inside an already-real shell file,
   one CSS addition — no new fixture data invented, no new design
   tokens invented (every new var but one routes to a real token; the
   one exception, `#4C4457`, is explicitly disclosed).
8. **Stop and escalation rule:** rendering the "Per action" records
   list, or wiring any Cost-segment content to a real command, is
   explicitly out of scope — a future slice's job, not this one's to
   silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F3C-ACTIVITY-COST-SPLIT-01` |
| `phase` | `AwaitingReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f3c-activity-cost-split.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
