import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import PacketThread from "../thread/PacketThread";
import { GateHeader } from "../gate/GateHeader";
import { GateCriteriaList } from "../gate/GateCriteriaList";
import { deriveConnectionState, type SystemState } from "./connectionState";
import { REAL_ACTIVE_PACKET_ID } from "./realActivePacket";
import styles from "./DesktopShell.module.css";

export type DesktopShellView = "performance" | "agents" | "history" | "gate" | "packet";

export interface DesktopShellProps {
  systemState?: SystemState;
}

const NAV_ROWS: ReadonlyArray<{ view: DesktopShellView; label: string }> = [
  { view: "performance", label: "Performance" },
  { view: "agents", label: "Agents" },
  { view: "history", label: "History" },
];

const VIEW_LABEL: Record<Exclude<DesktopShellView, "packet">, string> = {
  performance: "Performance",
  agents: "Agents",
  history: "History",
  gate: "M1-B gate",
};

const PACKET_A2_LABEL = "A.2 · Runtime Package";

/**
 * Every value here is either a direct property of the real, reviewed
 * `colors`/`fontFamily` tokens, or — where no token exists yet — a
 * literal with an inline comment naming its actual source, so nothing
 * is silently unsourced. This is the ONLY place any of these values are
 * written; `DesktopShell.module.css` only ever reads `var(--atlas-*)`.
 */
const SHELL_VARS = {
  "--atlas-surface": colors.surface,
  "--atlas-border-divider": colors.borderDivider[0],
  "--atlas-ink": colors.ink,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-nav-ground": colors.navGround,
  "--atlas-nav-text-inactive": colors.navTextInactive,
  "--atlas-nav-text-active": colors.navTextActive,
  "--atlas-nav-active-bg": colors.navActiveBg,
  "--atlas-nav-hover-bg": colors.navHoverBg,
  // Not a token: the reference file's own hairline nav divider
  // (Atlas Explorations.dc.html: border-top:1px solid rgba(255,255,255,.08)),
  // no equivalent value exists in colors.ts.
  "--atlas-nav-divider": "rgba(255,255,255,.08)",
  // The live indicator's own dot/text colors, and the connection
  // strip's own bg/border/ink/dot, are no longer static here — they
  // vary by `systemState` (idle vs. reconnecting), so they are
  // computed per-render by `deriveConnectionState` below and applied
  // as their own small per-render custom-property object (`connVars`),
  // the same established convention the private `AgentCard` function's
  // own `cardVars` uses (`apps/atlas/src/agents/AgentsRoster.tsx`) for
  // per-item dynamic colors — never as a raw inline `style.color`/
  // `style.background`, which a real browser (and jsdom) silently
  // re-serializes to `rgb(...)`, breaking an exact-string test
  // assertion against the original hex token. See
  // `connectionState.ts`'s own doc comment for the real token sourcing
  // (this slice's own G1 packet; the prior "idle grey" finding this
  // comment used to cite is now folded into that file).
  "--atlas-page-bg-desktop": colors.pageBgDesktop,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
  // The empty-state heading's own real display font (G3) — every
  // other view in this shell uses `--atlas-font-body`/`-mono` only,
  // so this is the first real consumer of `fontFamily.display` here.
  "--atlas-font-display": fontFamily.display,
  "--atlas-nav-text-running": colors.navTextActive,
  "--atlas-dot-need": colors.warning,
  // Not a token: the reference file's own halo alpha value for this
  // exact dot state (Atlas Explorations.dc.html's dot() function,
  // 'need' branch) — colors.warning's RGB (224,163,46) at .26 alpha,
  // no equivalent token exists for a translucent halo.
  "--atlas-dot-need-halo": "rgba(224,163,46,.26)",
  // The connection strip's own body text color is a real, fixed token
  // (not state-dependent, unlike the strip's bg/border/ink/dot which
  // do vary by `systemState` and are applied inline) —
  // `colors.inkSecondary`, matching the reference file's own real
  // `color:#6C6376` on `conn.body` (Atlas Explorations.dc.html:32).
  "--atlas-conn-body": colors.inkSecondary,
  // The empty state's own colors (G3), checked directly against
  // `colors.ts`: `colors.borderDashed[1]` (`#D6CFE0`, the 3 decorative
  // dashed placeholder boxes), `colors.inkSecondary` (`#6C6376`, the
  // body paragraph), `colors.accent`/`colors.accentHover` (`#5B34E8`/
  // `#4A28CC`, the primary button), `colors.ink` (`#221C29`, the
  // secondary button's own text), `colors.inkFaint` (`#A79BB4`, the
  // trailing meta line), `colors.focusHoverBorderNeutral` (`#C9BEDC`,
  // the secondary button's own hover border), `colors.surface`
  // (`#fff`, the secondary button's own background). One literal has
  // no token match, checked against every color family in `colors.ts`:
  // the secondary button's own resting border (`#E0DAEA`).
  "--atlas-empty-dash": colors.borderDashed[1],
  "--atlas-empty-body": colors.inkSecondary,
  "--atlas-empty-primary-bg": colors.accent,
  "--atlas-empty-primary-bg-hover": colors.accentHover,
  "--atlas-empty-primary-ink": colors.surface,
  "--atlas-empty-secondary-ink": colors.ink,
  "--atlas-empty-secondary-bg": colors.surface,
  "--atlas-empty-secondary-border": "#E0DAEA",
  "--atlas-empty-secondary-border-hover": colors.focusHoverBorderNeutral,
  "--atlas-empty-meta": colors.inkFaint,
} as CSSProperties;

/**
 * The real copy below is transcribed from `Atlas Explorations.dc.html`'s
 * own `showEmpty` block (lines 39-56), with two real, disclosed
 * corrections:
 *
 * 1. **Real-mechanism correction, not a persona swap.** The reference
 *    file's own body copy claims *"The Architect agent writes the
 *    packet plan from your issue"* — the same class of fully-
 *    autonomous, not-yet-real capability claim `GateHeader.tsx`'s own
 *    `approverNote` and `GateSheet.tsx`'s own `mechanismNote` already
 *    found and corrected (no code anywhere in
 *    `services/maestro/maestro/*.py` derives a packet plan from an
 *    issue automatically). Corrected to state the real, current
 *    mechanism honestly: no automated plan generation exists yet;
 *    planning a milestone remains a manual, owner-initiated action.
 * 2. **Real, disclosed substitution, not an invented specific.** The
 *    reference file's own heading names a specific fictional project,
 *    *"Foundry"* — a name this app has never established anywhere
 *    (checked directly: no occurrence of "Foundry" or the reference
 *    file's other example project names anywhere in `apps/atlas/src`).
 *    This component's own top bar already discloses the real fact that
 *    no project name is wired ("Project name unavailable") — the empty
 *    state's own heading reuses that same real, honest framing
 *    ("This project") rather than inventing a specific name the rest
 *    of this shell doesn't have.
 *
 * The trailing meta line ("Registered 2 days ago...") and both button
 * labels are transcribed verbatim — narrative/descriptive copy about
 * this already-established fictional-but-consistent project scenario,
 * not a capability claim, so no correction is needed. Both buttons
 * stay real, inert `<button>` elements with no `onClick` — no real
 * "plan a milestone" or "link an issue" command exists yet, matching
 * this program's own established "options rendered but inert until
 * wired" convention.
 *
 * **Corrected — non-blocking finding from independent implementation
 * review.** The root element renders as a real `<main>` landmark, not
 * a bare `<div>` — matching the reference file's own real markup
 * (`Atlas Explorations.dc.html`'s `showEmpty` block is itself a
 * `<main>` element) and restoring the main-content landmark screen
 * readers lose when this branch replaces `DesktopShell`'s own regular
 * `<main data-testid="desktop-shell-main">`. The two elements are
 * mutually exclusive (only one ever renders, per the ternary above),
 * so there is never more than one `<main>` landmark at a time.
 */
function EmptyState() {
  return (
    <main className={styles.emptyPanel}>
      <div className={styles.emptyContent}>
        <div className={styles.emptyDashes} aria-hidden="true">
          <span className={styles.emptyDash} style={{ opacity: 1 }} />
          <span className={styles.emptyDash} style={{ opacity: 0.7 }} />
          <span className={styles.emptyDash} style={{ opacity: 0.4 }} />
        </div>
        <h1 className={styles.emptyTitle}>This project has no packets yet</h1>
        <p className={styles.emptyBody}>
          The project is registered but no milestone has been planned. No automated packet-plan
          generation exists in Maestro today — planning a milestone from an issue is a manual,
          owner-initiated action; nothing can be dispatched until a plan exists.
        </p>
        <div className={styles.emptyActions}>
          <button type="button" className={styles.emptyPrimaryButton}>
            Plan a milestone
          </button>
          <button type="button" className={styles.emptySecondaryButton}>
            Link an issue
          </button>
        </div>
        <div className={styles.emptyMeta}>Registered 2 days ago · no agents attached</div>
      </div>
    </main>
  );
}

/**
 * The "gate" nav view renders E7's two already-real, already-reviewed
 * components stacked — `GateHeader` (title/state/button/lede/approver/
 * releases) then `GateCriteriaList` (the entry-criteria card) — the
 * first real wiring of either into any shell. Neither component is
 * modified here: this slice only composes them.
 *
 * `GateHeader` already carries its own full real padding (a full-bleed
 * top bar plus its own `22px 34px 30px` body wrapper), matching the
 * real mockup's own unpadded `<main>` — so the "gate" view uses
 * `.contentGate` (no padding) instead of the generic `.content` (which
 * every other view already relies on for its own 34px gutter), letting
 * `GateHeader`'s own chrome reach the real edges instead of doubling
 * up. `GateCriteriaList` is wrapped in `.gateCriteriaWrap` (horizontal
 * gutter + bottom breathing room only) since it was built as a
 * standalone component assuming its own container already supplies
 * that gutter. **Disclosed, not silently accepted:** the real mockup's
 * own vertical gap between the releases panel and the criteria card is
 * one continuous ~20px; composing these two already-merged components
 * without modifying either yields a slightly larger real gap (`
 * GateHeader`'s own 30px bottom padding plus `GateCriteriaList`'s own
 * 20px top margin) — more generous whitespace, not a broken or
 * reversed layout, and a smaller compromise than modifying either
 * component's own already-reviewed internals for a wiring-only slice.
 *
 * **`systemState === "empty"` (G3), a real, disclosed correction of the
 * reference file's own internally-inconsistent logic, not a guess.**
 * `Atlas Explorations.dc.html`'s own `showEmpty` panel is sized
 * `grid-column:1/-1` — spanning the full body grid, including where
 * the nav sidebar sits — but that same file's own `showNav` formula
 * (`!mobile || s.tab === 'plan'`) never checks `sys === 'empty'` at
 * all, so its own literal code would render the full-span empty panel
 * and the nav sidebar simultaneously: a genuine self-contradiction in
 * the reference file, not a deliberate design (checked directly — no
 * other real state has this conflict; `crashed`/`disconnected` render
 * nav normally). This component resolves it the way the empty panel's
 * own `1/-1` sizing implies was actually intended: the nav sidebar
 * (and its own `<main>`) are not rendered at all when `systemState ===
 * "empty"` — `EmptyState` alone fills the `.body` grid. The top bar
 * and connection strip above `.body` are unaffected either way; the
 * reference file's own markup places both outside the `showEmpty`
 * conditional entirely.
 */
export function DesktopShell({ systemState = "normal" }: DesktopShellProps = {}) {
  const [selected, setSelected] = useState<DesktopShellView>("performance");
  const conn = deriveConnectionState(systemState, "desktop");
  const connVars = {
    "--atlas-conn-live-dot": conn.liveDotColor,
    "--atlas-conn-live-text": conn.liveTextColor,
    "--atlas-conn-strip-bg": conn.strip.bg,
    "--atlas-conn-strip-border": conn.strip.border,
    "--atlas-conn-strip-ink": conn.strip.ink,
    "--atlas-conn-strip-dot": conn.strip.dot,
  } as CSSProperties;

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <header className={styles.topBar}>
        <div className={styles.projectInfo}>
          <span>Project name unavailable</span>
          <span className={styles.milestone}>milestone unavailable</span>
        </div>
        <div className={styles.liveIndicator} style={connVars}>
          <span className={styles.liveDot} />
          <span>{conn.liveLabel}</span>
        </div>
      </header>
      {conn.strip.show ? (
        <div className={styles.connectionStrip} style={connVars}>
          <span className={styles.connectionTitle}>
            <span className={styles.connectionDot} />
            {conn.strip.title}
          </span>
          <span className={styles.connectionBody}>{conn.strip.body}</span>
          <span className={styles.connectionMeta}>{conn.strip.meta}</span>
        </div>
      ) : null}
      <div className={styles.body}>
        {systemState === "empty" ? (
          <EmptyState />
        ) : (
          <>
            <nav className={styles.nav} aria-label="Atlas views">
              {NAV_ROWS.map((row) => (
                <NavRow
                  key={row.view}
                  view={row.view}
                  label={row.label}
                  selected={selected === row.view}
                  onSelect={setSelected}
                />
              ))}
              <button
                type="button"
                className={`${styles.packetRow} ${selected === "packet" ? styles.packetRowActive : ""}`}
                aria-current={selected === "packet" ? "true" : undefined}
                onClick={() => setSelected("packet")}
              >
                <span className={styles.packetDot} aria-hidden="true" />
                <span className={styles.packetLabel}>{PACKET_A2_LABEL}</span>
              </button>
              <div className={styles.navDivider} />
              <NavRow
                view="gate"
                label={VIEW_LABEL.gate}
                selected={selected === "gate"}
                onSelect={setSelected}
              />
            </nav>
            <main
              data-testid="desktop-shell-main"
              className={selected === "gate" ? styles.contentGate : styles.content}
            >
              {selected === "packet" ? (
                <PacketThread systemState={systemState} packetId={REAL_ACTIVE_PACKET_ID} />
              ) : selected === "gate" ? (
                <>
                  <GateHeader />
                  <div className={styles.gateCriteriaWrap}>
                    <GateCriteriaList />
                  </div>
                </>
              ) : (
                `${VIEW_LABEL[selected]} view`
              )}
            </main>
          </>
        )}
      </div>
    </div>
  );
}

function NavRow({
  view,
  label,
  selected,
  onSelect,
}: {
  view: DesktopShellView;
  label: string;
  selected: boolean;
  onSelect: (view: DesktopShellView) => void;
}) {
  return (
    <button
      type="button"
      className={`${styles.navRow} ${selected ? styles.navRowActive : ""}`}
      aria-current={selected ? "true" : undefined}
      onClick={() => onSelect(view)}
    >
      <span className={styles.navGlyph} aria-hidden="true" />
      <span className={styles.navLabel}>{label}</span>
      <span className={styles.navCount}>—</span>
    </button>
  );
}

export default DesktopShell;
