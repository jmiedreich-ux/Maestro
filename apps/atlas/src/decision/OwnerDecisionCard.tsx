import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { OWNER_DECISION_EXAMPLE } from "./ownerFixtures";
import {
  dispatchCorrection,
  resolveDecisionSentinel,
  type RealActor,
} from "./realDecisionCommands";
import styles from "./OwnerDecisionCard.module.css";

export interface OwnerDecisionCardRealContext {
  packetId: string;
  expectedVersion: number;
  /** Required only for the "Amend the A.1 contract" option's real command. */
  reviewId: string;
  actor: RealActor;
}

export interface OwnerDecisionCardProps {
  /**
   * M3 E5 — when supplied, both option buttons dispatch the real D2/D3
   * commands (record_and_route_review's resolve-decision, and
   * record_and_dispatch_correction via dispatch-correction). Omitted
   * (the default, and every existing caller), both buttons render
   * exactly as before: inert, no onClick at all.
   */
  real?: OwnerDecisionCardRealContext;
}

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

export function OwnerDecisionCard({ real }: OwnerDecisionCardProps = {}) {
  const { age, headline, lede, why, options } = OWNER_DECISION_EXAMPLE;
  const [pendingIndex, setPendingIndex] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleOptionClick(index: number) {
    if (!real || pendingIndex !== null) return;
    setErrorMessage(null);
    setPendingIndex(index);
    try {
      // Real mapping, matching each option's own real body text above:
      // index 0 ("Allow a sentinel version") is D2's real Ready
      // transition; index 1 ("Amend the A.1 contract") is D3's real
      // correction dispatch — the only two options this fixture has.
      if (index === 0) {
        await resolveDecisionSentinel({
          packetId: real.packetId,
          expectedVersion: real.expectedVersion,
          actor: real.actor,
        });
      } else {
        await dispatchCorrection({
          packetId: real.packetId,
          expectedVersion: real.expectedVersion,
          reviewId: real.reviewId,
          actor: real.actor,
        });
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : String(error));
    } finally {
      setPendingIndex(null);
    }
  }

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
          {options.map((option, index) => (
            <button
              key={option.title}
              type="button"
              className={styles.option}
              disabled={real ? pendingIndex !== null : undefined}
              onClick={real ? () => void handleOptionClick(index) : undefined}
            >
              <div className={styles.optionRow}>
                <b className={styles.optionTitle}>{option.title}</b>
                <span className={styles.optionCost}>
                  {real && pendingIndex === index ? "sending…" : option.cost}
                </span>
              </div>
              <div className={styles.optionBody}>{option.body}</div>
            </button>
          ))}
        </div>
        {real && errorMessage && (
          <p className={styles.why} role="alert">
            {errorMessage}
          </p>
        )}
      </div>
    </div>
  );
}

export default OwnerDecisionCard;
