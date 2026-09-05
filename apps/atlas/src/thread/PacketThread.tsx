import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import {
  INITIALS_BY_NAME,
  PACKET_A2_ENTRIES,
  ROLE_LABEL,
  type EntryRoleKey,
  type ThreadEntry,
} from "./fixtures";
import styles from "./PacketThread.module.css";

const SHELL_VARS = {
  "--atlas-ink": colors.ink,
  "--atlas-ink-muted": colors.inkMuted,
  "--atlas-ink-faint": colors.inkFaint,
  "--atlas-font-mono": fontFamily.mono,
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

export function PacketThread() {
  return (
    <div className={styles.thread} style={SHELL_VARS}>
      {PACKET_A2_ENTRIES.map((entry, index) => {
        const showAvatar = computeShowAvatar(PACKET_A2_ENTRIES, index);
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
    </div>
  );
}

export default PacketThread;
