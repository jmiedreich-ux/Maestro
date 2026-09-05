import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { HISTORY_EMPTY_NOTE, HISTORY_ENTRIES, HISTORY_STATS, type HistoryEntry } from "./fixtures";
import { HISTORY_KIND_STYLE } from "./historyStyle";
import styles from "./History.module.css";

/**
 * Real B2 tokens plus four disclosed literals in this file, checked
 * directly against the reference file: the timeline rail color
 * (`#EDE8F2` — a real, different value from `colors.borderDivider`'s
 * own three entries, not a rounding of one of them), the urgent-dot
 * ring (`rgba(224,163,46,.16)` — derived from `colors.warning`'s RGB,
 * no token for the ring itself), the "Open … thread" button's border
 * (`#E4DEEE` — distinct from `colors.border`/`colors.borderStrong`),
 * and the button's hover background (`#FBFAFE` — the same real
 * literal C3's and C5's own cards already disclosed, reused here, not
 * newly derived). Four in this file; a fifth (`historyStyle.ts`'s
 * `report`-dot `#CFC6D6`) is disclosed separately in that module's own
 * comment — five disclosed literals total across the two new files.
 */
const SHELL_VARS = {
  "--atlas-hist-surface": colors.surface,
  "--atlas-hist-header-border": colors.borderDivider[0],
  "--atlas-hist-eyebrow": colors.inkFaint,
  "--atlas-hist-title": colors.ink,
  "--atlas-hist-lede": colors.inkSecondary,
  "--atlas-hist-rail": "#EDE8F2",
  "--atlas-hist-empty-rail": colors.border,
  "--atlas-hist-button-border": "#E4DEEE",
  "--atlas-hist-button-text": colors.accent,
  "--atlas-hist-button-hover-border": colors.focusHoverBorderNeutral,
  "--atlas-hist-button-hover-bg": "#FBFAFE",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-font-body": fontFamily.body,
} as CSSProperties;

function HistoryRow({ entry }: { entry: HistoryEntry }) {
  const style = HISTORY_KIND_STYLE[entry.kind];
  const dotSize = style.urgent ? "11px" : "10px";
  const dotBg = style.urgent ? style.dotColor : colors.surface;
  const dotBoxShadow = style.urgent
    ? `0 0 0 4px ${colors.pageBgDesktop}, 0 0 0 7px rgba(224,163,46,.16)`
    : `0 0 0 4px ${colors.pageBgDesktop}`;
  return (
    <div className={styles.row}>
      <div className={styles.time}>{entry.time}</div>
      <div className={styles.railWrap}>
        <span className={styles.rail} aria-hidden="true" />
        <span
          className={styles.dot}
          aria-hidden="true"
          style={{
            width: dotSize,
            height: dotSize,
            background: dotBg,
            border: `2px solid ${style.dotColor}`,
            boxShadow: dotBoxShadow,
          }}
        />
      </div>
      <div className={styles.body}>
        <div className={styles.entryLine}>
          <span className={styles.tag} style={{ background: style.tagBg, color: style.tagColor }}>
            {entry.kind}
          </span>
          <span className={styles.entryTitle}>{entry.title}</span>
          <span className={styles.entryPacket}>{entry.packet}</span>
        </div>
        <div className={styles.entryDetail}>
          {entry.who} — {entry.detail}
        </div>
        {entry.ref ? (
          <button type="button" className={styles.openButton}>
            Open {entry.ref} thread
          </button>
        ) : null}
      </div>
    </div>
  );
}

/**
 * Renders the History screen in full: header (eyebrow, title, 4 real
 * stats), the full real 10-entry timeline, and its own trailing
 * placeholder note. Every "Open … thread" button is a real `<button>`
 * with no `onClick` — genuinely inert, matching C4's/C6's established
 * pattern, since there is no real navigation destination wired yet.
 */
export function History() {
  return (
    <div style={SHELL_VARS}>
      <div className={styles.head}>
        <div className={styles.eyebrow}>m1-a · history</div>
        <h1 className={styles.title}>Everything that happened, in order</h1>
        <div className={styles.stats}>
          {HISTORY_STATS.map((stat) => (
            <span key={stat.label} className={styles.stat}>
              {stat.label}
              <b className={styles.statValue}>{stat.value}</b>
            </span>
          ))}
        </div>
      </div>
      <div className={styles.timeline}>
        {HISTORY_ENTRIES.map((entry) => (
          <HistoryRow key={`${entry.time}-${entry.title}`} entry={entry} />
        ))}
        <div className={styles.emptyRow}>
          <span />
          <div className={styles.emptyRail}>
            <span className={styles.emptyRailStub} aria-hidden="true" />
          </div>
          <div className={styles.emptyNote}>{HISTORY_EMPTY_NOTE}</div>
        </div>
      </div>
    </div>
  );
}

export default History;
