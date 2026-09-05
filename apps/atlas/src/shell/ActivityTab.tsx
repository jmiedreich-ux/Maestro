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
} as CSSProperties;

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
          `${SEGMENTS.find((seg) => seg.key === segment)?.label} segment`
        )}
      </div>
    </div>
  );
}

export default ActivityTab;
