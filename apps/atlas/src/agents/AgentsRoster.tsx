import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { AGENT_STYLE } from "./agentStyle";
import { AGENTS, AGENTS_STATS, type AgentEntry, type AgentStat } from "./agents";
import styles from "./AgentsRoster.module.css";

/**
 * Every color here is a real B2 token except the two literals
 * `agentStyle.ts` already discloses (`run`'s and `rev`'s own border
 * colors) — the hollow "waiting" dot's border (`#B9AFC4`) is a real
 * token, `colors.borderDashed[2]`, checked directly. The "Open thread"
 * button's border (`#E4DEEE`) and hover background (`#FBFAFE`) are the
 * same two real, previously-disclosed literals this program's own
 * History/Gate-criteria/decision-card slices already use for their own
 * "Open … thread" buttons — reused here, not newly derived. The
 * button's hover border (`#C9BEDC`) is a real token,
 * `colors.focusHoverBorderNeutral`.
 */
const SHELL_VARS = {
  "--atlas-ag-card-surface": colors.surface,
  "--atlas-ag-header-border": colors.borderDivider[0],
  "--atlas-ag-eyebrow": colors.inkFaint,
  "--atlas-ag-name": colors.ink,
  "--atlas-ag-role": colors.inkMuted,
  "--atlas-ag-packet": colors.inkFaint,
  "--atlas-ag-line": colors.inkSecondary,
  "--atlas-ag-bar-track": colors.borderDivider[0],
  "--atlas-ag-progress": colors.inkMuted,
  "--atlas-ag-due": colors.inkMuted,
  "--atlas-ag-due-urgent": colors.warningText,
  "--atlas-ag-footer-border": colors.borderDivider[1],
  "--atlas-ag-footer-bg": colors.focusHoverCard,
  "--atlas-ag-locks": colors.inkMuted,
  "--atlas-ag-button-border": "#E4DEEE",
  "--atlas-ag-button-ink": colors.accent,
  "--atlas-ag-button-hover-border": colors.focusHoverBorderNeutral,
  "--atlas-ag-button-hover-bg": "#FBFAFE",
  "--atlas-ag-wait-dot-border": colors.borderDashed[2],
  "--atlas-ag-stat-accent": colors.accent,
  "--atlas-ag-stat-warning": colors.warningText,
  "--atlas-ag-stat-accent-hover": colors.accentHover,
  "--atlas-ag-stat-ink": colors.ink,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-font-body": fontFamily.body,
} as CSSProperties;

const STAT_VALUE_CLASS: Record<AgentStat["color"], string> = {
  accent: styles.statValueAccent,
  warningText: styles.statValueWarning,
  accentHover: styles.statValueAccentHover,
  ink: styles.statValueInk,
};

function AgentCard({ agent }: { agent: AgentEntry }) {
  const style = AGENT_STYLE[agent.styleKey];
  const isWait = agent.styleKey === "wait";
  const cardVars = {
    "--atlas-ag-card-border": style.border,
    "--atlas-ag-avatar-bg": style.avBg,
    "--atlas-ag-avatar-ink": style.avColor,
    "--atlas-ag-state-ink": style.stateColor,
    "--atlas-ag-bar-fill": style.barColor,
    "--atlas-ag-dot-bg": isWait ? "transparent" : style.barColor,
  } as CSSProperties;

  return (
    <div className={styles.card} style={cardVars}>
      <div className={styles.top}>
        <span className={styles.avatar}>{agent.av}</span>
        <div className={styles.identity}>
          <div className={styles.nameLine}>
            <span className={styles.name}>{agent.name}</span>
            <span className={styles.role}>{agent.role}</span>
          </div>
          <div className={styles.state}>
            <span className={`${styles.stateDot} ${isWait ? styles.stateDotHollow : ""}`} />
            {agent.state}
          </div>
        </div>
        <span className={styles.packet}>{agent.packet}</span>
      </div>
      <div className={styles.line}>{agent.line}</div>
      <div className={styles.progressBlock}>
        <div className={styles.barTrack}>
          <span className={styles.barFill} style={{ width: agent.pct }} />
        </div>
        <div className={styles.progressRow}>
          <span>{agent.progress}</span>
          <span className={agent.urgent ? styles.dueUrgent : styles.due}>{agent.due}</span>
        </div>
      </div>
      <div className={styles.footer}>
        <span className={styles.locks}>{agent.locks}</span>
        <button type="button" className={styles.openButton}>
          Open thread
        </button>
      </div>
    </div>
  );
}

/**
 * Renders the real Agents screen in full: header (eyebrow, title, 4
 * real `agStats`) and all 4 real roster cards. `AGENTS[3]` substitutes
 * the fictional `Architect agent` persona with the real `Coordinator`
 * actor — see `agents.ts`'s own disclosure. The header eyebrow uses
 * `m1-a`, correcting the reference file's own `vennuesign` artifact —
 * see the same disclosure. Every "Open thread" button is a real
 * `<button>` with no `onClick` — genuinely inert, matching this
 * program's own established convention for options rendered but not
 * yet wired.
 */
export function AgentsRoster() {
  return (
    <div style={SHELL_VARS}>
      <div className={styles.head}>
        <div className={styles.eyebrow}>m1-a · agents</div>
        <h1 className={styles.title}>Four agents, one worktree each</h1>
        <div className={styles.stats}>
          {AGENTS_STATS.map((stat) => (
            <span key={stat.label} className={styles.stat}>
              {stat.label}
              <b className={`${styles.statValue} ${STAT_VALUE_CLASS[stat.color]}`}>{stat.value}</b>
            </span>
          ))}
        </div>
      </div>
      <div className={styles.roster}>
        {AGENTS.map((agent) => (
          <AgentCard key={agent.ref + agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

export default AgentsRoster;
