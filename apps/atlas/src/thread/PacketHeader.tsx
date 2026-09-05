import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { derivePacketHeaderState } from "./headerState";
import { PACKET_A2_ENTRIES } from "./fixtures";
import styles from "./PacketHeader.module.css";

/**
 * Colors from `Atlas Explorations.dc.html`'s real packet-header markup.
 * The "need" dot (bg + halo) reuses the exact same real values C1B's
 * `DesktopShell.tsx` already established for the identical real signal
 * (`colors.warning` + `rgba(224,163,46,.26)`) — redeclared here rather
 * than imported, since `DesktopShell.tsx`'s constant is module-private
 * and frozen; both are the same real, checked value, not two different
 * guesses.
 */
const SHELL_VARS = {
  "--atlas-header-surface": colors.surface,
  "--atlas-header-border": colors.borderDivider[0],
  "--atlas-header-eyebrow": colors.inkFaint,
  "--atlas-header-title": colors.ink,
  "--atlas-header-state-color": colors.warningText,
  "--atlas-header-dot": colors.warning,
  "--atlas-header-dot-halo": "rgba(224,163,46,.26)",
  "--atlas-header-summary-border": colors.borderDivider[1],
  "--atlas-header-summary-bg": colors.pageBgDesktop,
  "--atlas-header-label": colors.inkMuted,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * The one, single source of state this header, and any future surface
 * that needs the same summary (a hero card, a "what happens next"
 * panel), should call — see `derivePacketHeaderState`'s own doc
 * comment for why only the real, exercised (blocked) branch renders
 * grounded values today.
 */
export function PacketHeader() {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
  return (
    <div className={styles.head} style={SHELL_VARS}>
      <div className={styles.eyebrow}>{state.eyebrow}</div>
      <h1 className={styles.title}>{state.title}</h1>
      <div className={styles.stateLine}>
        <span className={styles.dot} aria-hidden="true" />
        {state.stateLine}
      </div>
      <div className={styles.summary}>
        <div className={styles.pair}>
          <span className={styles.label}>Last report</span>
          <b className={styles.reportValue}>{state.lastReport}</b>
        </div>
        <div className={styles.pair}>
          <span className={styles.label}>Blocker</span>
          <b className={styles.blockerValue}>{state.blocker}</b>
        </div>
        <div className={styles.pair}>
          <span className={styles.label}>{state.nextLabel}</span>
          <b className={styles.nextValue}>{state.next}</b>
        </div>
      </div>
    </div>
  );
}

export default PacketHeader;
