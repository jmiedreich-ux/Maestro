import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import {
  PERFORMANCE_LEDE_AFTER,
  PERFORMANCE_LEDE_BEFORE,
  PERFORMANCE_LEDE_CODE,
  PERFORMANCE_STATS,
} from "./fixtures";
import styles from "./PerformanceHeader.module.css";

/**
 * Every color here is a real B2 token — this screen's header has no
 * disclosed literal at all, the cleanest token match of any C/E-wave
 * component so far. `colors.inkFaint` (eyebrow) and `colors.inkSecondary`
 * (lede/stat labels) already have real precedent from C7's
 * `PacketHeader`; `colors.warningText` (the `Estimated` stat) matches
 * this program's own established amber-means-estimate convention.
 */
const SHELL_VARS = {
  "--atlas-perf-surface": colors.surface,
  "--atlas-perf-border": colors.borderDivider[0],
  "--atlas-perf-eyebrow": colors.inkFaint,
  "--atlas-perf-title": colors.ink,
  "--atlas-perf-lede": colors.inkSecondary,
  "--atlas-perf-warning": colors.warningText,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const STAT_VALUE_CLASS: Record<"ink" | "warning", string> = {
  ink: styles.statValueInk,
  warning: styles.statValueWarning,
};

export function PerformanceHeader() {
  return (
    <div className={styles.head} style={SHELL_VARS}>
      <div className={styles.eyebrow}>m1-a · performance</div>
      <h1 className={styles.title}>What each action actually cost</h1>
      <p className={styles.lede}>
        {PERFORMANCE_LEDE_BEFORE}
        <code className={styles.ledeCode}>{PERFORMANCE_LEDE_CODE}</code>
        {PERFORMANCE_LEDE_AFTER}
      </p>
      <div className={styles.stats}>
        {PERFORMANCE_STATS.map((stat) => (
          <span key={stat.label} className={styles.stat}>
            {stat.label}
            <b className={`${styles.statValue} ${STAT_VALUE_CLASS[stat.color]}`}>{stat.value}</b>
          </span>
        ))}
      </div>
    </div>
  );
}

export default PerformanceHeader;
