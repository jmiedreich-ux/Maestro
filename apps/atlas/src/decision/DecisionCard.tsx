import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { RULING_EXAMPLE } from "./fixtures";
import styles from "./DecisionCard.module.css";

/**
 * Ruling-variant colors from `Atlas Explorations.dc.html`'s `blk`
 * object (`mine === false` branch) plus two markup-hardcoded values
 * shared by both variants (`age`, `arrow`). Five have no equivalent B2
 * token and stay disclosed literals, each checked directly against the
 * reference file — see the discrepancy table in this slice's packet
 * contract: `dotRing`, `border`, `bg`, `age`, `arrow`. Every other
 * value below is a direct property of the real `colors` token.
 */
const SHELL_VARS = {
  "--atlas-decision-border": "#DFD8EE",
  "--atlas-decision-bg": "#FBFAFE",
  "--atlas-decision-ink": colors.accentHover,
  "--atlas-decision-dot": colors.accent,
  "--atlas-decision-dot-ring": "rgba(91,52,232,.18)",
  "--atlas-decision-chip": colors.accentWash[2],
  "--atlas-decision-chip-on": colors.accent,
  "--atlas-decision-chip-on-ink": colors.surface,
  "--atlas-decision-age": "#A1927B",
  "--atlas-decision-arrow": "#C4AE86",
  "--atlas-decision-lede": colors.inkSecondary,
  "--atlas-decision-why": colors.inkMuted,
  "--atlas-decision-headline": colors.ink,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function DecisionCard() {
  const { packetId, attemptId, recordedAt, route } = RULING_EXAMPLE;
  return (
    <div className={styles.row} style={SHELL_VARS}>
      <span aria-hidden="true" />
      <div className={styles.card}>
        <div className={styles.eyebrow}>
          <span className={styles.dot} aria-hidden="true" />
          resolved by routing policy
          <span className={styles.age}>recorded {recordedAt}</span>
        </div>
        <div className={styles.headline}>
          {packetId}&rsquo;s independent implementation review was approved — routing moved it to{" "}
          {route.toState} automatically.
        </div>
        <p className={styles.lede}>
          Maestro&rsquo;s routing table advances an approved independent implementation review straight
          to {route.toState} with no human step. This card records that outcome as evidence, not as an
          open question.
        </p>
        <div className={styles.chainRow}>
          <span className={styles.chip}>
            {attemptId} · {route.fromState}
          </span>
          <span className={styles.arrow} aria-hidden="true">
            →
          </span>
          <span className={styles.chip}>
            {route.reviewKind} · {route.verdict}
          </span>
          <span className={styles.arrow} aria-hidden="true">
            →
          </span>
          <span className={styles.chipOn}>{route.toState}</span>
          <span className={styles.why}>
            rule: _REVIEW_ROUTES["{route.fromState}","{route.reviewKind}","{route.verdict}"] → "
            {route.toState}"
          </span>
        </div>
      </div>
    </div>
  );
}

export default DecisionCard;
