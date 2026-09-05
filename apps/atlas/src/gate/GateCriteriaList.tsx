import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import {
  GATE_CRITERIA,
  GATE_FOOTER_NOTE,
  GATE_MET_LABEL,
  type GateCriterion,
  type GateCriterionMet,
} from "./fixtures";
import styles from "./GateCriteriaList.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real per-criterion
 * derivation logic (`titleColor`/`evColor`/`markBg`/`markBorder`).
 * Every semantic color is a real B2 token except the unmet-criterion
 * mark's border (`#CFC6D6`): that exact hex also happens to equal
 * `colors.navText`. Checked exhaustively against every other property
 * in that same nav-color group: `colors.navGround`, `.navTextActive`,
 * `.navTextInactive`, `.navActiveBg`, and `.navHoverBg` are all real,
 * consumed values in `DesktopShell.tsx`'s nav sidebar — but
 * `colors.navText` itself is not consumed anywhere in `apps/atlas/src`
 * (grepped directly, zero real usages), and its sibling
 * `colors.navTextDim` likewise has no real consumer — it appears only
 * inside a comment in `DesktopShell.tsx` noting that it happens to
 * equal `colors.inkMuted`, which is the value actually used there.
 * `navText`'s scoping to the dark nav sidebar rests on its name and
 * its position in this real, mostly-consumed group, not on any real
 * usage of the property itself — so it is not reused here as a
 * general-purpose light-mode border gray.
 */
const SHELL_VARS = {
  "--atlas-gate-border": colors.border,
  "--atlas-gate-surface": colors.surface,
  "--atlas-gate-header-border": colors.borderDivider[0],
  "--atlas-gate-label": colors.inkSecondary,
  "--atlas-gate-met-label": colors.inkMuted,
  "--atlas-gate-row-border": colors.borderDivider[1],
  "--atlas-gate-mark-yes": colors.success,
  "--atlas-gate-mark-part": colors.warning,
  "--atlas-gate-mark-no-border": "#CFC6D6",
  "--atlas-gate-title-unmet": colors.inkSecondary,
  "--atlas-gate-title-default": colors.ink,
  "--atlas-gate-detail": colors.inkSecondary,
  "--atlas-gate-ev-yes": colors.successText,
  "--atlas-gate-ev-part": colors.warningText,
  "--atlas-gate-ev-no": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const MARK_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.markYes,
  part: styles.markPart,
  no: styles.markNo,
};

const EVIDENCE_CLASS: Record<GateCriterionMet, string> = {
  yes: styles.evidenceYes,
  part: styles.evidencePart,
  no: styles.evidenceNo,
};

function CriterionRow({ criterion }: { criterion: GateCriterion }) {
  const titleClass = criterion.met === "no" ? styles.titleUnmet : styles.titleDefault;
  return (
    <div className={styles.row}>
      <span className={`${styles.mark} ${MARK_CLASS[criterion.met]}`} aria-hidden="true" />
      <div className={styles.body}>
        <div className={`${styles.title} ${titleClass}`}>{criterion.title}</div>
        <div className={styles.detail}>{criterion.detail}</div>
      </div>
      <span className={`${styles.evidence} ${EVIDENCE_CLASS[criterion.met]}`}>{criterion.evidence}</span>
    </div>
  );
}

/**
 * Renders the gate's real entry-criteria card in full (header,
 * met-count summary, all 5 real criteria rows, and the card's own
 * footer note) — the gate's separate header block (title, state line,
 * Open-gate button, approver note, releases list) is a separate, later
 * slice (a future `E7B`-style candidate) whose lede/approver copy needs
 * the fictional-"Architect agent" adaptation this slice's own content
 * never requires.
 */
export function GateCriteriaList() {
  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.header}>
        entry criteria
        <span className={styles.metLabel}>{GATE_MET_LABEL}</span>
      </div>
      {GATE_CRITERIA.map((criterion) => (
        <CriterionRow key={criterion.title} criterion={criterion} />
      ))}
      <div className={styles.footer}>{GATE_FOOTER_NOTE}</div>
    </div>
  );
}

export default GateCriteriaList;
