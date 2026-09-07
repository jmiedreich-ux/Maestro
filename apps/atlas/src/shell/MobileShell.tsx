import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { NowTab } from "./NowTab";
import { ChatTab } from "./ChatTab";
import { ActivityTab } from "./ActivityTab";
import { PlanTab } from "./PlanTab";
import { REAL_ACTIVE_PACKET_ID } from "./realActivePacket";
import styles from "./MobileShell.module.css";

export type MobileShellTab = "now" | "chat" | "plan" | "activity";

/**
 * A real problem on a real phone: mobile Safari discards a backgrounded
 * tab under memory pressure and reloads it fresh on return, resetting
 * React state — the selected tab kept silently reverting to "Now".
 * Persisting the real selection to localStorage (best-effort; a
 * private-browsing throw just falls back to the in-memory default)
 * survives that reload.
 */
const SELECTED_TAB_STORAGE_KEY = "atlas-mobile-selected-tab";

function isMobileShellTab(value: unknown): value is MobileShellTab {
  return value === "now" || value === "chat" || value === "plan" || value === "activity";
}

function readStoredTab(): MobileShellTab {
  try {
    const stored = window.localStorage.getItem(SELECTED_TAB_STORAGE_KEY);
    return isMobileShellTab(stored) ? stored : "now";
  } catch {
    return "now";
  }
}

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

export function MobileShell() {
  const [selected, setSelectedState] = useState<MobileShellTab>(readStoredTab);

  function setSelected(tab: MobileShellTab) {
    setSelectedState(tab);
    try {
      window.localStorage.setItem(SELECTED_TAB_STORAGE_KEY, tab);
    } catch {
      // Best-effort only — private browsing or a full storage quota
      // throws; the tab still switches for this session either way.
    }
  }

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <main className={styles.content}>
        {selected === "now" ? (
          <NowTab />
        ) : selected === "chat" ? (
          <ChatTab onBack={() => setSelected("now")} packetId={REAL_ACTIVE_PACKET_ID} />
        ) : selected === "activity" ? (
          <ActivityTab />
        ) : (
          <PlanTab />
        )}
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
