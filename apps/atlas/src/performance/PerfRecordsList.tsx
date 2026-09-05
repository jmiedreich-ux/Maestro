import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { PERF_RECORDS, type PerfCostKind, type PerfOutcome, type PerfRecord } from "./perfRecords";
import styles from "./PerfRecordsList.module.css";

/**
 * Every color here is a real B2 token — no disclosed literal, matching
 * E1/E1B. The outcome-tag and cost-color mappings are transcribed
 * verbatim from `Atlas Explorations.dc.html`'s real per-record
 * derivation logic (`tag`/`costColor` in the reference file's `perf`
 * map function).
 */
const SHELL_VARS = {
  "--atlas-perf-card-border": colors.border,
  "--atlas-perf-card-surface": colors.surface,
  "--atlas-perf-row-ink": colors.ink,
  "--atlas-perf-row-faint": colors.inkFaint,
  "--atlas-perf-row-muted": colors.inkMuted,
  "--atlas-perf-row-warning": colors.warningText,
  "--atlas-perf-tag-blocked-bg": colors.warningChip,
  "--atlas-perf-tag-blocked-ink": colors.warningText,
  "--atlas-perf-tag-good-bg": colors.successWash,
  "--atlas-perf-tag-good-ink": colors.successText,
  "--atlas-perf-tag-neutral-bg": colors.neutralChip,
  "--atlas-perf-tag-neutral-ink": colors.inkSecondary,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const COST_CLASS: Record<PerfCostKind, string> = {
  billed: styles.costBilled,
  est: styles.costEst,
  none: styles.costNone,
};

function outcomeClass(outcome: PerfOutcome): string {
  if (outcome === "blocked") return styles.outcomeBlocked;
  if (outcome === "approved" || outcome === "passed") return styles.outcomeGood;
  return styles.outcomeNeutral;
}

function PerfRecordRow({ record }: { record: PerfRecord }) {
  return (
    <div className={styles.card}>
      <button type="button" className={styles.row}>
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
    </div>
  );
}

/**
 * Renders the collapsed row only for all 5 real `PERF_RECORDS` — the
 * expandable detail groups and the click-to-expand behavior are a
 * separate, later slice (a future `E2B`-style candidate), matching
 * this program's own established header/strip split pattern (E1/E1B).
 * Each row is a real `<button>` (matching the reference file's own
 * markup) with no `onClick` — genuinely inert, not wired yet.
 */
export function PerfRecordsList() {
  return (
    <div className={styles.list} style={SHELL_VARS}>
      {PERF_RECORDS.map((record) => (
        <PerfRecordRow key={record.id} record={record} />
      ))}
    </div>
  );
}

export default PerfRecordsList;
