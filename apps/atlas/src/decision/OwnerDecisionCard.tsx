import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { OWNER_DECISION_EXAMPLE } from "./ownerFixtures";
import styles from "./OwnerDecisionCard.module.css";

/**
 * Owner-decision-variant colors from `Atlas Explorations.dc.html`'s
 * `blk` object (`mine === true` branch) plus the two markup-hardcoded
 * values shared with the ruling variant (`age`, `arrow` — already
 * disclosed by C3's `DecisionCard.tsx`). Every semantic color here
 * (`border`, `bg`, `ink`, `dotBg`, `chip`, `chipOn`) is a real B2
 * `colors.warning*` token — a cleaner token match than C3's ruling
 * palette. Two values have no equivalent token and stay disclosed
 * literals, checked directly against the reference file: `dotRing`
 * (derived from `colors.warning`'s RGB) and `chipOnInk` (`#3D2C06`, the
 * "you" chip's dark-brown text — no B2 token matches it). The hover
 * background (`#FFFDF8`) also has no exact token match and stays a
 * disclosed literal; the hover border reuses the real
 * `colors.focusHoverBorderAmber` token.
 */
const SHELL_VARS = {
  "--atlas-owner-border": colors.warningBorder,
  "--atlas-owner-bg": colors.warningWash,
  "--atlas-owner-ink": colors.warningText,
  "--atlas-owner-dot": colors.warning,
  "--atlas-owner-dot-ring": "rgba(224,163,46,.24)",
  "--atlas-owner-chip": colors.warningChip,
  "--atlas-owner-chip-on": colors.warning,
  "--atlas-owner-chip-on-ink": "#3D2C06",
  "--atlas-owner-age": "#A1927B",
  "--atlas-owner-arrow": "#C4AE86",
  "--atlas-owner-lede": colors.inkSecondary,
  "--atlas-owner-why": colors.inkMuted,
  "--atlas-owner-headline": colors.ink,
  "--atlas-owner-surface": colors.surface,
  "--atlas-owner-hover-border": colors.focusHoverBorderAmber,
  "--atlas-owner-hover-bg": "#FFFDF8",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function OwnerDecisionCard() {
  const { age, headline, lede, why, options } = OWNER_DECISION_EXAMPLE;
  return (
    <div className={styles.row} style={SHELL_VARS}>
      <span aria-hidden="true" />
      <div className={styles.card}>
        <div className={styles.head}>
          <div className={styles.eyebrow}>
            <span className={styles.dot} aria-hidden="true" />
            your decision
            <span className={styles.age}>{age}</span>
          </div>
          <div className={styles.headline}>{headline}</div>
          <p className={styles.lede}>{lede}</p>
          <div className={styles.chainRow}>
            <span className={styles.chip}>Terra</span>
            <span className={styles.arrow} aria-hidden="true">
              →
            </span>
            <span className={styles.chip}>Coordinator</span>
            <span className={styles.arrow} aria-hidden="true">
              →
            </span>
            <span className={styles.chipOn}>you</span>
            <span className={styles.why}>{why}</span>
          </div>
        </div>
        <div className={styles.optionList}>
          {options.map((option) => (
            <button key={option.title} type="button" className={styles.option}>
              <div className={styles.optionRow}>
                <b className={styles.optionTitle}>{option.title}</b>
                <span className={styles.optionCost}>{option.cost}</span>
              </div>
              <div className={styles.optionBody}>{option.body}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default OwnerDecisionCard;
