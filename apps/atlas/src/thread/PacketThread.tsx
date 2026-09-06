import type { CSSProperties } from "react";
import { colors, fontFamily, motion } from "../tokens";
import { CrashCard } from "../crash/CrashCard";
import type { SystemState } from "../shell/connectionState";
import { INITIALS_BY_NAME, ROLE_LABEL, type EntryRoleKey, type ThreadEntry } from "./fixtures";
import { useRealPacketThread } from "./useRealPacketThread";
import styles from "./PacketThread.module.css";

export interface PacketThreadProps {
  systemState?: SystemState;
  /** The real, registered packet id whose thread this renders. */
  packetId: string;
}

/**
 * `--atlas-crash-row-rise-*`: the real crash row's own entrance
 * animation (`Atlas Explorations.dc.html:417`, `animation:rise .22s
 * ease-out`) reuses the same real `motion.rise` token every other
 * reveal in this program already consumes, but at its own real
 * `durationS.max` (`0.22s`) — a different, real value from
 * `PerfRecordsList.tsx`/`ActivityTab.tsx`'s own `.min` (`0.18s`)
 * reveals, checked directly against the reference file, not a
 * mismatch.
 */
const SHELL_VARS = {
  "--atlas-ink": colors.ink,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-ink-faint": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
  "--atlas-crash-row-rise-translate": `${motion.rise.translateYPx}px`,
  "--atlas-crash-row-rise-duration": `${motion.rise.durationS.max}s`,
  "--atlas-crash-row-rise-easing": motion.rise.easing,
} as CSSProperties;

/**
 * `AV` from the reference file. Two values have no equivalent B2 token
 * and stay disclosed literals, each checked directly against
 * `Atlas Explorations.dc.html`'s real `AV` constant, not invented:
 * `co`'s background (`#EFEBF2` — a real, checked mismatch against this
 * codebase's existing `colors.neutralChip`, see the discrepancy table
 * above) and `by`'s background (`#FEF3E2` — never rendered by this
 * slice's chosen `A.2` fixture, which uses only the `co`/`wk` roles,
 * but included here for a complete, correct palette matching the
 * README's own "Avatar palettes" enumeration). Every other value below
 * is a direct property of the real `colors` token.
 */
const AVATAR_PALETTE: Record<EntryRoleKey, { bg: string; ink: string }> = {
  co: { bg: "#EFEBF2", ink: "#4A4155" },
  wk: { bg: colors.accentWash[0], ink: colors.accentHover },
  rv: { bg: colors.reviewWash, ink: colors.reviewText },
  ok: { bg: colors.successWash, ink: colors.successText },
  by: { bg: "#FEF3E2", ink: colors.warningText },
  ow: { bg: colors.accentLight, ink: colors.surface },
  ar: { bg: colors.accentWash[1], ink: colors.accentDeepest },
};

const FALLBACK_INITIALS: Record<EntryRoleKey, string> = {
  co: "CO",
  wk: "TE",
  rv: "CL",
  ok: "CO",
  by: "15",
  ow: "OW",
  ar: "AR",
};

/**
 * The exact grouping rule from `Atlas Explorations.dc.html`'s
 * `renderVals`, minus the `fid` check (that field doesn't exist on
 * `ThreadEntry` yet — C4 adds it, and extends this function's
 * condition then, matching the reference file's own full rule).
 */
export function computeShowAvatar(entries: ThreadEntry[], index: number): boolean {
  const entry = entries[index];
  const prev = entries[index - 1];
  const grouped = !!prev && prev.who === entry.who && !prev.plan && !prev.cadence;
  return !grouped;
}

export function textColorFor(entry: ThreadEntry): string {
  return entry.k === "by" ? colors.inkSecondary : colors.ink;
}

/**
 * `systemState === "crashed"` (G2) appends the real `CrashCard` (C6)
 * after every real entry, matching `Atlas Explorations.dc.html`'s own
 * exact placement (`crash.show`, immediately after the entries'
 * `</sc-for>`, inside the same scrolling feed — not a separate
 * top-level banner or a `DesktopShell`-level insertion). `CrashCard`
 * is mounted as-is, unmodified — its own `.row` grid
 * (`36px minmax(0,1fr)`) already matches this file's own `.row`
 * exactly, confirming both were built from the same real reference
 * grid, not merely similar-looking, and already supplies its own real
 * padding — so the wrapping `.crashRow` here is animation-only (the
 * real entrance `animation:rise .22s ease-out` the reference file
 * applies to this exact element, which `CrashCard.tsx`'s own CSS does
 * not itself carry — a disclosed, minor gap in that already-merged
 * component, not fixed here since modifying it is outside this
 * wiring-only slice's own proportional scope), not a second, duplicate
 * grid/padding wrapper. This app has no multi-packet selection, so the
 * reference file's own `cur.id === 'A.2'` guard on its equivalent
 * `crashed` flag is always true here.
 */
export function PacketThread({ systemState = "normal", packetId }: PacketThreadProps) {
  const real = useRealPacketThread(packetId);
  const entries = real.entries;

  return (
    <div className={styles.thread} style={SHELL_VARS}>
      {real.resyncRequired && (
        <p className={styles.text} role="status">
          Connection to Maestro was interrupted — refreshing.
        </p>
      )}
      {entries.map((entry, index) => {
        const showAvatar = computeShowAvatar(entries, index);
        const palette = AVATAR_PALETTE[entry.k];
        const initials = INITIALS_BY_NAME[entry.who] ?? FALLBACK_INITIALS[entry.k];
        return (
          <div
            key={`${entry.who}-${entry.time}`}
            className={styles.row}
            style={{ paddingTop: showAvatar ? 16 : 2, paddingBottom: showAvatar ? 16 : 2 }}
          >
            {showAvatar ? (
              <span
                className={styles.avatar}
                style={{ background: palette.bg, color: palette.ink }}
                aria-hidden="true"
              >
                {initials}
              </span>
            ) : (
              <span aria-hidden="true" />
            )}
            <div className={styles.body}>
              {showAvatar ? (
                <div className={styles.nameRow}>
                  <span className={styles.name}>{entry.who}</span>
                  <span className={styles.role}>{ROLE_LABEL[entry.k]}</span>
                  <time className={styles.time}>{entry.time}</time>
                </div>
              ) : null}
              <p className={styles.text} style={{ color: textColorFor(entry) }}>
                {entry.text}
              </p>
            </div>
          </div>
        );
      })}
      {systemState === "crashed" && (
        <div className={styles.crashRow}>
          <CrashCard />
        </div>
      )}
    </div>
  );
}

export default PacketThread;
