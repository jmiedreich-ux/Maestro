import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { CONTENTION, CONTENTION_CAVEAT, type ContentionEntry, type ContentionStyleKey } from "./contention";
import styles from "./ContentionCard.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1/E1B/E2/E2B/E3's own precedent. The badge bg/ink mapping is
 * transcribed verbatim from the reference file's own real per-row
 * derivation logic (`bg`/`color` in the reference file's `contention`
 * map function).
 */
const SHELL_VARS = {
  "--atlas-ct-surface": colors.surface,
  "--atlas-ct-border": colors.border,
  "--atlas-ct-header-border": colors.borderDivider[0],
  "--atlas-ct-header-label": colors.inkSecondary,
  "--atlas-ct-status": colors.successText,
  "--atlas-ct-row-border": colors.borderDivider[1],
  "--atlas-ct-path": colors.ink,
  "--atlas-ct-note": colors.inkSecondary,
  "--atlas-ct-caveat": colors.inkMuted,
  "--atlas-ct-badge-run-bg": colors.accentWash[0],
  "--atlas-ct-badge-run-ink": colors.accentHover,
  "--atlas-ct-badge-wait-bg": colors.neutralChip,
  "--atlas-ct-badge-wait-ink": colors.inkSecondary,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const BADGE_CLASS: Record<ContentionStyleKey, string> = {
  run: styles.badgeRun,
  wait: styles.badgeWait,
};

function ContentionRow({ entry }: { entry: ContentionEntry }) {
  return (
    <div className={styles.row}>
      <div className={styles.info}>
        <div className={styles.path}>{entry.path}</div>
        <div className={styles.note}>{entry.note}</div>
      </div>
      <span className={`${styles.badge} ${BADGE_CLASS[entry.styleKey]}`}>{entry.holder}</span>
    </div>
  );
}

/**
 * Renders the real contention/lock card in full: header ("contention"
 * label, "no overlap" status), all 3 real `CONTENTION` rows, and the
 * card's own real trailing caveat.
 */
export function ContentionCard() {
  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.header}>
        contention
        <span className={styles.status}>no overlap</span>
      </div>
      {CONTENTION.map((entry) => (
        <ContentionRow key={entry.path} entry={entry} />
      ))}
      <div className={styles.caveat}>{CONTENTION_CAVEAT}</div>
    </div>
  );
}

export default ContentionCard;
