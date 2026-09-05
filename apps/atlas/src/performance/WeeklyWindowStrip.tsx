import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { WEEKLY_WINDOW } from "./weeklyWindow";
import styles from "./WeeklyWindowStrip.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1's `PerformanceHeader`. `colors.border` (`#E7E1EE`) is a new real
 * token this program hasn't consumed yet elsewhere; every other value
 * already has established precedent (E1, C7).
 */
const SHELL_VARS = {
  "--atlas-week-border": colors.border,
  "--atlas-week-surface": colors.surface,
  "--atlas-week-label": colors.inkSecondary,
  "--atlas-week-ink": colors.ink,
  "--atlas-week-warning": colors.warningText,
  "--atlas-week-meta": colors.inkMuted,
  "--atlas-week-caption": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function WeeklyWindowStrip() {
  const { reconciledPercent, coarsePercent, unattributedPercent, observedChangePercent, meta, caption } =
    WEEKLY_WINDOW;
  return (
    <div style={SHELL_VARS}>
      <div className={styles.strip}>
        <span className={styles.label}>openai weekly window</span>
        <span className={styles.reconciled}>
          Reconciled: <b className={`${styles.figure} ${styles.figureInk}`}>{reconciledPercent}</b> controlled +{" "}
          <b className={`${styles.figure} ${styles.figureInk}`}>{coarsePercent}</b> coarse +{" "}
          <b className={`${styles.figure} ${styles.figureWarning}`}>{unattributedPercent}</b> unattributed ={" "}
          <b className={`${styles.figure} ${styles.figureInk}`}>{observedChangePercent}</b> observed change
        </span>
        <span className={styles.meta}>{meta}</span>
      </div>
      <div className={styles.caption}>{caption}</div>
    </div>
  );
}

export default WeeklyWindowStrip;
