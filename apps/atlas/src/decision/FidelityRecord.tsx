import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { FIDELITY_RECORD_EXAMPLE, type FidelityRow } from "./fidelityFixtures";
import styles from "./FidelityRecord.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real, non-templated DF-2
 * markup (this card's colors are hardcoded in the markup, not driven
 * by a `blk`-style variant object — there is only one visual
 * treatment). Three values have no equivalent B2 token and stay
 * disclosed literals, each checked directly against the reference
 * file: `bg` (`#FBFAFE`, already disclosed once by C3's ruling-variant
 * `DecisionCard.tsx`), and the two row-divider colors (`#EDE8F6`,
 * `#F3F0FA`) — close to, but distinct from, `colors.borderDivider`'s
 * three real values. The `drifts` verdict background (`#FBEAE7`) also
 * has no exact token match and stays a disclosed literal, even though
 * this slice's own chosen evidence never exercises the `drifts`
 * verdict — kept for a complete, correct 3-verdict palette matching
 * the reference file's own enumeration, the same reasoning C1 used to
 * keep its full, unexercised avatar palette.
 */
const SHELL_VARS = {
  "--atlas-df-border": colors.borderStrong[1],
  "--atlas-df-bg": "#FBFAFE",
  "--atlas-df-ink": colors.accentHover,
  "--atlas-df-mark-border": colors.accent,
  "--atlas-df-id-color": colors.inkMuted,
  "--atlas-df-subject-color": colors.ink,
  "--atlas-df-against-color": colors.inkMuted,
  "--atlas-df-row-divider-top": "#EDE8F6",
  "--atlas-df-row-divider": "#F3F0FA",
  "--atlas-df-claim-color": colors.ink,
  "--atlas-df-evidence-color": colors.inkMuted,
  "--atlas-df-verdict-matches-bg": colors.successWash,
  "--atlas-df-verdict-matches-color": colors.successText,
  "--atlas-df-verdict-drifts-bg": "#FBEAE7",
  "--atlas-df-verdict-drifts-color": colors.dangerText,
  "--atlas-df-verdict-na-bg": colors.neutralChip,
  "--atlas-df-verdict-na-color": colors.inkSecondary,
  "--atlas-df-bar-bg": colors.accentWash[4],
  "--atlas-df-bar-square": colors.accent,
  "--atlas-df-verdict-text": colors.accentDeepest,
  "--atlas-df-note-color": colors.inkSecondary,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

const VERDICT_CLASS: Record<FidelityRow["verdict"], string> = {
  matches: styles.verdictMatches,
  drifts: styles.verdictDrifts,
  "n/a": styles.verdictNa,
};

/**
 * The reference file nests this card inside a chat message body (no
 * avatar/row grid of its own — see the markup this slice transcribes).
 * There is no message-authoring agent in M2 to attribute it to, so
 * this slice renders the same card markup directly, standalone,
 * exactly like every other C-wave component before its own wiring
 * slice.
 */
export function FidelityRecord() {
  const { id, subject, against, rows, verdict, note } = FIDELITY_RECORD_EXAMPLE;
  return (
    <div className={styles.card} style={SHELL_VARS}>
      <div className={styles.eyebrow}>
        <span className={styles.mark} aria-hidden="true" />
        decision fidelity
        <span className={styles.recordId}>{id}</span>
      </div>
      <div className={styles.head}>
        <div className={styles.subject}>{subject}</div>
        <div className={styles.against}>verified against {against}</div>
      </div>
      <div className={styles.rows}>
        {rows.map((row) => (
          <div key={row.claim} className={styles.row}>
            <div>
              <div className={styles.claim}>{row.claim}</div>
              <div className={styles.evidence}>{row.evidence}</div>
            </div>
            <span className={`${styles.verdictTag} ${VERDICT_CLASS[row.verdict]}`}>{row.verdict}</span>
          </div>
        ))}
      </div>
      <div className={styles.bar}>
        <span className={styles.overallVerdict}>
          <span className={styles.barSquare} aria-hidden="true" />
          {verdict}
        </span>
        <span className={styles.note}>{note}</span>
      </div>
    </div>
  );
}

export default FidelityRecord;
