import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { SPLIT, SPLIT_BASES, type SplitBasisKey, type SplitPart } from "./perfBreakdown";
import styles from "./PerfBreakdownCard.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal. The
 * reference file's real `SPLIT_COLORS` array (`['#5B34E8', '#D08A63',
 * '#2E9B72', '#B9AFC4']`) is exactly `[colors.accent, colors.review,
 * colors.success, colors.borderDashed[2]]`, checked directly against
 * `colors.ts` — four real, different token properties, not a
 * coincidence. The segmented control is the first real consumer of
 * `colors.segmentedTrack`/`colors.segmentedSelected` and
 * `PerfBreakdownCard` renders the first true multi-value toggle
 * (`useState<SplitBasisKey>`) in this codebase, matching the reference
 * file's own `s.basis` state field exactly (one real basis selected at
 * a time, defaulting to `'cost'`).
 */
const SEGMENT_CLASS = [styles.segColor0, styles.segColor1, styles.segColor2, styles.segColor3];

const SHELL_VARS = {
  "--atlas-brk-card-border": colors.border,
  "--atlas-brk-card-surface": colors.surface,
  "--atlas-brk-header-border": colors.borderDivider[0],
  "--atlas-brk-header-label": colors.inkSecondary,
  "--atlas-brk-basis-note": colors.inkMuted,
  "--atlas-brk-track-bg": colors.segmentedTrack[1],
  "--atlas-brk-seg-selected-bg": colors.segmentedSelected,
  "--atlas-brk-seg-selected-ink": colors.ink,
  "--atlas-brk-seg-unselected-ink": colors.inkMuted,
  "--atlas-brk-group-border": colors.borderDivider[1],
  "--atlas-brk-group-name": colors.inkFaint,
  "--atlas-brk-legend-label": colors.inkSecondary,
  "--atlas-brk-legend-pct": colors.ink,
  "--atlas-brk-legend-abs": colors.inkFaint,
  "--atlas-brk-caveat": colors.inkMuted,
  "--atlas-brk-seg-color-0": colors.accent,
  "--atlas-brk-seg-color-1": colors.review,
  "--atlas-brk-seg-color-2": colors.success,
  "--atlas-brk-seg-color-3": colors.borderDashed[2],
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * Transcribed verbatim from the reference file's own bar-width
 * derivation (`w: Math.max(pct, 0.6) + '%'`) — a 0%-share part still
 * renders a thin, visible sliver rather than vanishing entirely.
 */
function barWidth(pct: number): string {
  return `${Math.max(pct, 0.6)}%`;
}

function Bar({ parts }: { parts: SplitPart[] }) {
  return (
    <div className={styles.bar}>
      {parts.map((part, index) => (
        <span
          key={part.label}
          title={`${part.label} · ${part.pct}% · ${part.abs}`}
          className={`${styles.barSegment} ${SEGMENT_CLASS[index]}`}
          style={{ width: barWidth(part.pct) }}
        />
      ))}
    </div>
  );
}

function Legend({ parts }: { parts: SplitPart[] }) {
  return (
    <div className={styles.legend}>
      {parts.map((part, index) => (
        <div key={part.label} className={styles.legendItem}>
          <span className={`${styles.legendDot} ${SEGMENT_CLASS[index]}`} />
          <span className={styles.legendLabel}>{part.label}</span>
          <b className={styles.legendPct}>{part.pct}%</b>
          <span className={styles.legendAbs}>{part.abs}</span>
        </div>
      ))}
    </div>
  );
}

/**
 * Renders the real "m1-a breakdown" card: a real cost/tokens/time
 * segmented control (one real basis selected at a time) driving two
 * real stacked-bar-plus-legend groups ("by role", "by kind of work")
 * and the current basis's own real caveat. `cost.role`'s fourth entry
 * substitutes the fictional `Architect agent` persona with the real
 * `Local Qwen` actor — see `perfBreakdown.ts`'s own disclosure.
 */
export function PerfBreakdownCard() {
  const [basis, setBasis] = useState<SplitBasisKey>("cost");
  const data = SPLIT[basis];

  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.header}>
        <span className={styles.headerLabel}>m1-a breakdown</span>
        <span className={styles.basisNote}>share of {data.note}</span>
        <div className={styles.segmented}>
          {SPLIT_BASES.map((b) => (
            <button
              key={b.key}
              type="button"
              className={`${styles.segButton} ${basis === b.key ? styles.segSelected : ""}`}
              onClick={() => setBasis(b.key)}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>
      <div className={styles.group}>
        <div className={styles.groupName}>by role</div>
        <Bar parts={data.role} />
        <Legend parts={data.role} />
      </div>
      <div className={styles.group}>
        <div className={styles.groupName}>by kind of work</div>
        <Bar parts={data.work} />
        <Legend parts={data.work} />
      </div>
      <div className={styles.caveat}>{data.caveat}</div>
    </div>
  );
}

export default PerfBreakdownCard;
