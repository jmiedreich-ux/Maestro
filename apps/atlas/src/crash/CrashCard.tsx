import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { CRASH_EXAMPLE } from "./fixtures";
import styles from "./CrashCard.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real, non-templated crash
 * markup (this card has only one visual treatment, no variant object).
 * Every semantic color here is a real B2 `colors.danger*` token — the
 * cleanest token match of any C-wave card so far. Two values have no
 * equivalent token and stay disclosed literals, checked directly
 * against the reference file: the eyebrow age color (`#B79C99`,
 * distinct from the decision cards' shared `#A1927B` age color) and
 * the option hover background (`#FFFCFB`).
 */
const SHELL_VARS = {
  "--atlas-crash-border": colors.dangerBorder,
  "--atlas-crash-bg": colors.dangerWash,
  "--atlas-crash-ink": colors.dangerText,
  "--atlas-crash-dot": colors.danger,
  "--atlas-crash-age": "#B79C99",
  "--atlas-crash-headline": colors.ink,
  "--atlas-crash-lede": colors.inkSecondary,
  "--atlas-crash-divider": colors.dangerDivider,
  "--atlas-crash-fact-label": colors.inkMuted,
  "--atlas-crash-fact-value": colors.ink,
  "--atlas-crash-surface": colors.surface,
  "--atlas-crash-hover-border": colors.focusHoverBorderRed,
  "--atlas-crash-hover-bg": "#FFFCFB",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * The reference file's `crashed` state is scoped to the same real
 * `A.2` packet C1/C4 already established — not a new scenario. See
 * this slice's packet contract (Corrections 1-5) for the headline,
 * lede, one fact, one option's body, and the footer note, all adapted
 * rather than transcribed verbatim: the reference file's own "still on
 * disk", "locks... preserved", "Worktree: preserved", "Locks stay
 * held", and "Coordinator retried once" claims are either not
 * verifiable against, or directly contradict, `finish_attempt_execution`'s
 * real outcome mapping in `operational_state.py`, which always
 * releases a Failed attempt's lease.
 */
export function CrashCard() {
  const { age, headline, lede, facts, options, footerNote } = CRASH_EXAMPLE;
  return (
    <div className={styles.row} style={SHELL_VARS}>
      <span aria-hidden="true" />
      <div className={styles.card}>
        <div className={styles.head}>
          <div className={styles.eyebrow}>
            <span className={styles.dot} aria-hidden="true" />
            agent stopped unexpectedly
            <span className={styles.age}>{age}</span>
          </div>
          <div className={styles.headline}>{headline}</div>
          <p className={styles.lede}>{lede}</p>
          <div className={styles.facts}>
            {facts.map((fact) => (
              <div key={fact.k} className={styles.fact}>
                <span className={styles.factLabel}>{fact.k}</span>
                <b className={styles.factValue}>{fact.v}</b>
              </div>
            ))}
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
        <div className={styles.footer}>{footerNote}</div>
      </div>
    </div>
  );
}

export default CrashCard;
