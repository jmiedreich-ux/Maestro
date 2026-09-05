import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import styles from "./DesktopShell.module.css";

export type DesktopShellView = "performance" | "agents" | "history" | "gate";

const NAV_ROWS: ReadonlyArray<{ view: DesktopShellView; label: string }> = [
  { view: "performance", label: "Performance" },
  { view: "agents", label: "Agents" },
  { view: "history", label: "History" },
];

const VIEW_LABEL: Record<DesktopShellView, string> = {
  performance: "Performance",
  agents: "Agents",
  history: "History",
  gate: "M1-B gate",
};

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
  // Corrected — blocking finding from Decision Fidelity review: the
  // README's shell paragraph only says "idle grey" with no exact hex,
  // but the higher-priority reference file (which the README's own
  // Fidelity rule says wins on any disagreement) computes this exact
  // color programmatically for the equivalent `sys === 'empty'` state:
  // `liveDot: ... sys === 'empty' ? '#8E8299' : ...` (Atlas
  // Explorations.dc.html). #8E8299 is exactly `colors.inkMuted` (also
  // equal to `colors.navTextDim`) — a real, exact match, not an
  // inference.
  "--atlas-idle-grey": colors.inkMuted,
  // Same reference-file computation gives the idle label's own text
  // color as `liveColor: '#A79BB4'` for this state — exactly
  // `colors.inkFaint`.
  "--atlas-idle-label": colors.inkFaint,
  "--atlas-page-bg-desktop": colors.pageBgDesktop,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

export function DesktopShell() {
  const [selected, setSelected] = useState<DesktopShellView>("performance");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <header className={styles.topBar}>
        <div className={styles.projectInfo}>
          <span>Project name unavailable</span>
          <span className={styles.milestone}>milestone unavailable</span>
        </div>
        <div className={styles.liveIndicator}>
          <span className={`${styles.liveDot} ${styles.liveDotIdle}`} />
          <span>idle</span>
        </div>
      </header>
      <div className={styles.body}>
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
          <div className={styles.navDivider} />
          <NavRow
            view="gate"
            label={VIEW_LABEL.gate}
            selected={selected === "gate"}
            onSelect={setSelected}
          />
        </nav>
        <main className={styles.content}>{VIEW_LABEL[selected]} view</main>
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
