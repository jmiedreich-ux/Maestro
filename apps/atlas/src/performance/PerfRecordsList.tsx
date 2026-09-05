import { useState, type CSSProperties } from "react";
import { colors, fontFamily, motion } from "../tokens";
import {
  PERF_RECORDS,
  type PerfCostKind,
  type PerfDetailKind,
  type PerfOutcome,
  type PerfRecord,
} from "./perfRecords";
import styles from "./PerfRecordsList.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1/E1B/E2. The outcome-tag, cost-color, and detail-value-color
 * mappings are transcribed verbatim from `Atlas Explorations.dc.html`'s
 * real per-record derivation logic (`tag`/`costColor`/detail-row
 * `color` in the reference file's `perf` map function). The detail
 * panel's background and the row's hover background (both the
 * reference's `#FCFBFD`) real-token-match two different B2 properties
 * at once — `colors.focusHoverCard` and `colors.pageBgDesktop` are both
 * literally `#FCFBFD`, checked directly against `colors.ts`;
 * `focusHoverCard` is used here as the semantically matching token for
 * a hover/focus surface. The reveal animation reuses the real
 * `motion.rise` token (fade + 4px translateY) rather than inventing new
 * values — the reference's own `.18s` duration is `motion.rise`'s
 * stated minimum.
 */
const SHELL_VARS = {
  "--atlas-perf-card-border": colors.border,
  "--atlas-perf-card-border-open": colors.borderStrong[0],
  "--atlas-perf-card-surface": colors.surface,
  "--atlas-perf-row-ink": colors.ink,
  "--atlas-perf-row-faint": colors.inkFaint,
  "--atlas-perf-row-muted": colors.inkMuted,
  "--atlas-perf-row-warning": colors.warningText,
  "--atlas-perf-row-hover-bg": colors.focusHoverCard,
  "--atlas-perf-tag-blocked-bg": colors.warningChip,
  "--atlas-perf-tag-blocked-ink": colors.warningText,
  "--atlas-perf-tag-good-bg": colors.successWash,
  "--atlas-perf-tag-good-ink": colors.successText,
  "--atlas-perf-tag-neutral-bg": colors.neutralChip,
  "--atlas-perf-tag-neutral-ink": colors.inkSecondary,
  "--atlas-perf-detail-border": colors.borderDivider[2],
  "--atlas-perf-detail-bg": colors.focusHoverCard,
  "--atlas-perf-detail-row-divider": colors.borderDivider[1],
  "--atlas-perf-detail-group-name": colors.inkFaint,
  "--atlas-perf-detail-label": colors.inkSecondary,
  "--atlas-perf-detail-note": colors.inkMuted,
  "--atlas-perf-detail-value-default": colors.ink,
  "--atlas-perf-detail-value-ok": colors.successText,
  "--atlas-perf-detail-value-est": colors.warningText,
  "--atlas-perf-detail-value-warn": colors.dangerText,
  "--atlas-perf-detail-value-na": colors.inkFaint,
  "--atlas-perf-rise-translate": `${motion.rise.translateYPx}px`,
  "--atlas-perf-rise-duration": `${motion.rise.durationS.min}s`,
  "--atlas-perf-rise-easing": motion.rise.easing,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const COST_CLASS: Record<PerfCostKind, string> = {
  billed: styles.costBilled,
  est: styles.costEst,
  none: styles.costNone,
};

const DETAIL_VALUE_CLASS: Record<PerfDetailKind, string> = {
  "": styles.detailValueDefault,
  est: styles.detailValueEst,
  ok: styles.detailValueOk,
  warn: styles.detailValueWarn,
  na: styles.detailValueNa,
};

function outcomeClass(outcome: PerfOutcome): string {
  if (outcome === "blocked") return styles.outcomeBlocked;
  if (outcome === "approved" || outcome === "passed") return styles.outcomeGood;
  return styles.outcomeNeutral;
}

function PerfRecordRow({
  record,
  open,
  onToggle,
}: {
  record: PerfRecord;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={`${styles.card} ${open ? styles.cardOpen : ""}`}>
      <button type="button" className={styles.row} onClick={onToggle}>
        <div className={styles.actionCell}>
          <div className={styles.actionLine}>
            <span className={styles.action}>{record.action}</span>
            <span className={styles.packetWho}>
              {record.packet} · {record.who}
            </span>
          </div>
          <div className={styles.model}>{record.model}</div>
        </div>
        <span className={styles.tokens}>{record.tokens}</span>
        <span className={`${styles.cost} ${COST_CLASS[record.costKind]}`}>{record.cost}</span>
        <span className={styles.elapsed}>{record.elapsed}</span>
        <span className={`${styles.outcome} ${outcomeClass(record.outcome)}`}>{record.outcome}</span>
      </button>
      {open && (
        <div className={styles.detail}>
          <div className={styles.detailGrid}>
            {record.groups.map((group) => (
              <div key={group.name} className={styles.detailGroup}>
                <div className={styles.detailGroupName}>{group.name}</div>
                <div className={styles.detailRows}>
                  {group.rows.map((row) => (
                    <div key={row.label} className={styles.detailRow}>
                      <span className={styles.detailLabel}>{row.label}</span>
                      <b className={`${styles.detailValue} ${DETAIL_VALUE_CLASS[row.kind]}`}>{row.value}</b>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className={styles.detailNote}>{record.note}</div>
        </div>
      )}
    </div>
  );
}

/**
 * Renders all 5 real `PERF_RECORDS` with the real click-to-expand
 * behavior and the expandable detail groups this program's own E2
 * packet deferred here. Real accordion: clicking a row's button toggles
 * that record's own detail panel open/closed, closing whichever other
 * record was open (matching the reference file's own single `perfOpen`
 * state field, not one independent boolean per record).
 */
export function PerfRecordsList() {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <div className={styles.list} style={SHELL_VARS}>
      {PERF_RECORDS.map((record) => (
        <PerfRecordRow
          key={record.id}
          record={record}
          open={openId === record.id}
          onToggle={() => setOpenId((current) => (current === record.id ? null : record.id))}
        />
      ))}
    </div>
  );
}

export default PerfRecordsList;
