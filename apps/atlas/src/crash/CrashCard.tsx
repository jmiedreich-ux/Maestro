import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { CRASH_EXAMPLE } from "./fixtures";
import { redispatchCrash, resolveCrashHold, type RealActor } from "./realCrashCommands";
import styles from "./CrashCard.module.css";

export interface CrashCardRealContext {
  packetId: string;
  expectedVersion: number;
  actor: RealActor;
}

export interface CrashCardProps {
  /**
   * M3 E6 — when supplied, the "Re-dispatch" and "Hold" option buttons
   * dispatch the real redispatch-crash/resolve-crash commands. Omitted
   * (the default, and every existing caller), all three buttons render
   * exactly as before: inert, no onClick. "Resume Terra from the last
   * boundary" is never wired, real or not — see realCrashCommands.ts's
   * own module docstring for why: it has no real backend counterpart.
   */
  real?: CrashCardRealContext;
}

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
export function CrashCard({ real }: CrashCardProps = {}) {
  const { age, headline, lede, facts, options, footerNote } = CRASH_EXAMPLE;
  const [pendingIndex, setPendingIndex] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function handleOptionClick(index: number) {
    // Real mapping, matching each option's own real body text above:
    // index 0 ("Resume...") has no real backend counterpart and is
    // never wired; index 1 ("Re-dispatch...") is the real
    // redispatch-crash command; index 2 ("Hold...") is the already-real
    // resolve-crash command.
    if (!real || index === 0 || pendingIndex !== null) return;
    setErrorMessage(null);
    setPendingIndex(index);
    try {
      if (index === 1) {
        await redispatchCrash({
          packetId: real.packetId,
          expectedVersion: real.expectedVersion,
          actor: real.actor,
        });
      } else {
        await resolveCrashHold({
          packetId: real.packetId,
          expectedVersion: real.expectedVersion,
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
          {options.map((option, index) => (
            <button
              key={option.title}
              type="button"
              className={styles.option}
              disabled={real && index !== 0 ? pendingIndex !== null : undefined}
              onClick={real && index !== 0 ? () => void handleOptionClick(index) : undefined}
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
          <p className={styles.optionBody} role="alert">
            {errorMessage}
          </p>
        )}
        <div className={styles.footer}>{footerNote}</div>
      </div>
    </div>
  );
}

export default CrashCard;
