import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { NowTab } from "./NowTab";
import styles from "./MobileShell.module.css";

export type MobileShellTab = "now" | "chat" | "plan" | "activity";

const TABS: ReadonlyArray<{ tab: MobileShellTab; label: string }> = [
  { tab: "now", label: "Now" },
  { tab: "chat", label: "Chat" },
  { tab: "plan", label: "Plan" },
  { tab: "activity", label: "Activity" },
];

/**
 * Every value here is either a direct property of the real, reviewed
 * `colors`/`fontFamily` tokens, or — where no token exists yet — a
 * literal with an inline comment naming its actual source (all five
 * non-token values here are from `Atlas Mobile.dc.html`, none
 * invented — corrected from an earlier draft that left one,
 * `backdrop-filter: blur(12px)`, as a bare CSS literal instead of
 * routing it through this same disclosed mechanism). Matches the
 * pattern `DesktopShell.tsx` (B3) already established.
 */
const SHELL_VARS = {
  "--atlas-page-bg-mobile": colors.pageBgMobile,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-font-body": fontFamily.body,
  // Not tokens: the reference file's own tab-bar chrome
  // (Atlas Mobile.dc.html's bottom <nav>) — no equivalent values exist
  // in colors.ts.
  "--atlas-tab-bar-bg": "rgba(255,255,255,.92)",
  "--atlas-tab-bar-border": "#EAE5F0",
  "--atlas-tab-bar-blur": "blur(12px)",
  // Reference file: `const col = k => s.tab === k ? '#5B34E8' : '#9A90A6'`.
  // The selected color is the real `colors.accent` token; the inactive
  // color (#9A90A6) has no equivalent token, so it stays a disclosed
  // literal.
  "--atlas-tab-selected": colors.accent,
  "--atlas-tab-inactive": "#9A90A6",
} as CSSProperties;

const TAB_LABEL: Record<MobileShellTab, string> = {
  now: "Now",
  chat: "Chat",
  plan: "Plan",
  activity: "Activity",
};

export function MobileShell() {
  const [selected, setSelected] = useState<MobileShellTab>("now");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <main className={styles.content}>
        {selected === "now" ? <NowTab /> : `${TAB_LABEL[selected]} tab`}
      </main>
      <nav className={styles.tabBar} aria-label="Atlas tabs">
        {TABS.map((t) => (
          <button
            key={t.tab}
            type="button"
            className={`${styles.tab} ${selected === t.tab ? styles.tabSelected : ""}`}
            aria-current={selected === t.tab ? "true" : undefined}
            onClick={() => setSelected(t.tab)}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

export default MobileShell;
