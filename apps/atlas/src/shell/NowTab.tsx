import type { CSSProperties } from "react";
import { colors, fontFamily, radii, spacing } from "../tokens";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import { AGENT_STYLE } from "../agents/agentStyle";
import { OwnerDecisionCard } from "../decision/OwnerDecisionCard";
import { deriveConnectionState, type SystemState } from "./connectionState";
import styles from "./NowTab.module.css";

export interface NowTabProps {
  systemState?: SystemState;
}

/**
 * Hero-card colors from `Atlas Mobile.dc.html`'s real Now-tab markup
 * (lines 48-63 of the reference file), checked directly against
 * `colors.ts`. Real token matches: `colors.navGround` (card
 * background), `colors.navTextInactive`
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
 *
 * The live indicator's own dot/text colors, and the connection strip
 * added below the page title, are no longer static here — they vary
 * by `systemState` (idle vs. reconnecting), computed per-render by
 * `deriveConnectionState` and applied as their own small per-render
 * custom-property object (`connVars`), matching
 * `DesktopShell.tsx`'s own identical convention (never a raw inline
 * `style.color`/`style.background`, which a real browser and jsdom
 * both silently re-serialize to `rgb(...)`, breaking an exact-string
 * test assertion). This slice also corrects a pre-existing
 * inconsistency: this file previously hardcoded the live-indicator
 * text to the literal `"live"` unconditionally, using
 * `colors.accentLight` for its dot — but this app has no real live
 * connection (no SSE stream, no polling) to honestly claim, unlike
 * `DesktopShell.tsx`'s own live indicator, which already correctly
 * said "idle". Both surfaces now read "idle"/"reconnecting" from the
 * same one function — see that function's own doc comment in
 * `connectionState.ts`.
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
  "--atlas-card-surface": colors.surface,
  // The connection strip's own body text color is a real, fixed value
  // (not state-dependent, unlike the strip's bg/border/ink/dot which
  // do vary by `systemState` and are applied inline). `Atlas
  // Mobile.dc.html`'s own real `conn.body` color is `#5C5468` — checked
  // directly against every family in `colors.ts` and matches no real
  // token (desktop's own equivalent, `#6C6376`, IS `colors.inkSecondary`
  // — a real but different value, not assumed equal to mobile's). This
  // stays a disclosed literal.
  "--atlas-conn-body": "#5C5468",
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
export function NowTab({ systemState = "normal" }: NowTabProps = {}) {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
  const progressWidth =
    state.progressPercent === "unavailable" ? "0%" : `${state.progressPercent}%`;
  const conn = deriveConnectionState(systemState, "mobile");
  const connVars = {
    "--atlas-conn-live-dot": conn.liveDotColor,
    "--atlas-conn-live-text": conn.liveTextColor,
    "--atlas-conn-strip-bg": conn.strip.bg,
    "--atlas-conn-strip-border": conn.strip.border,
    "--atlas-conn-strip-ink": conn.strip.ink,
    "--atlas-conn-strip-dot": conn.strip.dot,
  } as CSSProperties;

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.eyebrowRow}>
        <span className={styles.eyebrow}>{state.eyebrow}</span>
        <span className={styles.live} style={connVars}>
          <span className={styles.liveDot} aria-hidden="true" />
          {conn.liveLabel}
        </span>
      </div>
      <h1 className={styles.pageTitle}>Now</h1>

      {conn.strip.show ? (
        <div className={styles.connectionStrip} style={connVars}>
          <div className={styles.connectionTitleRow}>
            <span className={styles.connectionDot} />
            {conn.strip.title}
            <span className={styles.connectionMeta}>{conn.strip.meta}</span>
          </div>
          <div className={styles.connectionBody}>{conn.strip.body}</div>
        </div>
      ) : null}

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
          <div
            className={styles.track}
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={state.progressPercent === "unavailable" ? undefined : state.progressPercent}
            aria-valuetext={state.progressPercent === "unavailable" ? "unavailable" : undefined}
            aria-label="Task progress"
          >
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
          <div className={styles.metaValueProse}>{state.blocker}</div>
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
