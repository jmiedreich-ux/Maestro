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
 * unattributed figure, line 283), `colors.inkFaint` (`#A79BB4` — the
 * weekly-window meta line, matching the real mobile mockup's own
 * literal directly, and separately the split card's own group-name/
 * legend-abs colors, matching E3's own `PerfBreakdownCard.tsx` token
 * choices exactly; **not** a `WeeklyWindowStrip.tsx` precedent for
 * those latter two fields, which has no group/legend layout at all —
 * `WeeklyWindowStrip.tsx`'s own meta field uses `colors.inkMuted`, not
 * `inkFaint` — corrected per Decision Fidelity review),
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
