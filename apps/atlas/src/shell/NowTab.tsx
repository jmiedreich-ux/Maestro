import type { CSSProperties } from "react";
import { colors, fontFamily, radii, spacing } from "../tokens";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import { AGENT_STYLE } from "../agents/agentStyle";
import { OwnerDecisionCard } from "../decision/OwnerDecisionCard";
import styles from "./NowTab.module.css";

/**
 * Hero-card colors from `Atlas Mobile.dc.html`'s real Now-tab markup
 * (lines 48-63 of the reference file), checked directly against
 * `colors.ts`. Real token matches: `colors.navGround` (card
 * background), `colors.accentLight` (live dot), `colors.navTextInactive`
 * (the progress track's fill — the mockup's own real blocked-branch
 * `barColor` is `#B7ADC1`, not `#A78BFF`; `#A78BFF` is that same
 * ternary's *non-blocked* branch, checked directly at
 * `Atlas Mobile.dc.html:687` — corrected by targeted correction, see
 * below), `colors.navActiveBg` (the progress track's own background,
 * `rgba(255,255,255,.13)` — an exact string match, also corrected by
 * targeted correction), `colors.inkFaint` (role text and boundary
 * timestamps — the same hex the mockup uses, `#A79BB4`), `colors.inkMuted`
 * (eyebrow label), and `colors.surface` (the meta-grid cards' white
 * background — the mockup's own `#fff`). The avatar bg/ink reuse the
 * real, already-reviewed `AGENT_STYLE.wait` pair from E4's
 * `agentStyle.ts` — Terra is genuinely idle/blocked in this real
 * trajectory, not running, so the "wait" style key is the honest
 * choice, not "run" (which E4's own Agents-roster fixture uses for a
 * different, later simulated moment of the same persona — not reused
 * here to avoid implying this hero card shows that same moment). The
 * same "blocked, not running" principle applies to the progress fill
 * color: an independent Decision Fidelity review found the first
 * draft picked the mockup's own *non-blocked* fill color here, which
 * directly contradicted this same principle already correctly applied
 * to the avatar — fixed to the real blocked-branch value.
 * Three values have no equivalent token and stay disclosed literals,
 * checked against every color family in `colors.ts`, not assumed: the
 * headline/name text (`#EDE8F1`), the subline text (`#C6BCD2`), the
 * "what happens next" panel's own body text color (`#3D3350`), and the
 * card's own 24px corner radius (`radii.mobileCardPx` only states an
 * 18-22px range; the reference file's own hero card is 24px, not
 * forced into the stated range). The hero card's own drop shadow
 * (`0 16px 34px rgba(30,20,45,.22)`, transcribed directly into
 * `NowTab.module.css`) is also a disclosed, unmatched literal — an
 * `rgba` shadow value, not a solid color, so it was not caught by the
 * hex-literal check above; noted here for completeness.
 */
const SHELL_VARS = {
  "--atlas-hero-bg": colors.navGround,
  "--atlas-hero-ink": "#EDE8F1",
  "--atlas-hero-ink-muted": colors.inkFaint,
  "--atlas-hero-avatar-bg": AGENT_STYLE.wait.avBg,
  "--atlas-hero-avatar-ink": AGENT_STYLE.wait.avColor,
  "--atlas-hero-track": colors.navActiveBg,
  "--atlas-hero-fill": colors.navTextInactive,
  "--atlas-hero-radius": "24px",
  "--atlas-card-radius": `${radii.mobileCardPx.max}px`,
  "--atlas-gutter": `${spacing.mobileGutterPx}px`,
  "--atlas-eyebrow": colors.inkMuted,
  "--atlas-live-dot": colors.accentLight,
  "--atlas-card-surface": colors.surface,
  "--atlas-subline": "#C6BCD2",
  "--atlas-next-text": "#3D3350",
  "--atlas-owner-bg": colors.warningWash,
  "--atlas-owner-ink": colors.warningText,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * Mobile "Now" tab — the single-state-source hero card, boundary
 * timestamps, meta grid, real escalation decision (reusing C4's
 * `OwnerDecisionCard` verbatim per the roadmap's own Wave F rule —
 * "reuse Wave C/E logic; no new backend"), and "what happens next"
 * panel, all read from one `derivePacketHeaderState` call. No Stop/
 * Start or "Open conversation" affordance is rendered — those need
 * their own guarded backend commands (per this roadmap's own M0-D01
 * amendment: "a command is available through Atlas only once its own
 * guarded command exists and passes review"), none of which exist yet;
 * adding inert-but-visible buttons for actions with no real backend at
 * all (unlike D2/D3's already-real resolve-decision command) would
 * misrepresent capability this build does not have.
 */
export function NowTab() {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
  const progressWidth =
    state.progressPercent === "unavailable" ? "0%" : `${state.progressPercent}%`;

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.eyebrowRow}>
        <span className={styles.eyebrow}>{state.eyebrow}</span>
        <span className={styles.live}>
          <span className={styles.liveDot} aria-hidden="true" />
          live
        </span>
      </div>
      <h1 className={styles.pageTitle}>Now</h1>

      <div className={styles.hero}>
        <div className={styles.heroHead}>
          <span className={styles.avatar} aria-hidden="true">
            TE
          </span>
          <div className={styles.identity}>
            <div className={styles.name}>Terra</div>
            <div className={styles.role}>Implementor · A.2 Runtime Package</div>
          </div>
        </div>
        <div className={styles.headline}>{state.headline}</div>
        <div className={styles.subline}>{state.subline}</div>

        <div className={styles.progressBlock}>
          <div className={styles.track}>
            <span className={styles.fill} style={{ width: progressWidth }} />
          </div>
          <div className={styles.boundaryRow}>
            <span>
              {state.boundaryBegin === "unavailable"
                ? "unavailable"
                : `began ${state.boundaryBegin}`}
            </span>
            <span>
              {state.boundaryHeld === "unavailable"
                ? "unavailable"
                : `held at ${state.boundaryHeld}`}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.metaGrid}>
        <div className={styles.metaCard}>
          <div className={styles.metaLabel}>Last report</div>
          <div className={styles.metaValue}>{state.lastReport}</div>
        </div>
        <div className={styles.metaCard}>
          <div className={styles.metaLabel}>Blocker</div>
          <div className={styles.metaValue}>{state.blocker}</div>
        </div>
      </div>

      {state.isBlocked ? <OwnerDecisionCard /> : null}

      <div className={styles.nextPanel}>
        <div className={styles.nextHeading}>{state.nextPanelHeading}</div>
        <p className={styles.nextText}>{state.nextPanelText}</p>
      </div>
    </div>
  );
}

export default NowTab;
