import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { deriveRealHeaderState } from "../thread/realHeaderState";
import { splitEntryText } from "../thread/realEventSynthesis";
import { textColorFor } from "../thread/PacketThread";
import { ROLE_LABEL, type EntryRoleKey } from "../thread/fixtures";
import { useRealPacketThread } from "../thread/useRealPacketThread";
import styles from "./ChatTab.module.css";

/**
 * Mobile chat-bubble colors from `Atlas Mobile.dc.html`'s real
 * `isThread` markup (lines 140-192 of the reference file), checked
 * directly against `colors.ts`. Real token matches: `colors.pageBgMobile`
 * (the feed's own background, `#F7F5FA`, line 146), `colors.accentHover`
 * (the "mine" name/bubble accent color, `#4A28CC`, matching the
 * reference file's real `renderVals()` logic — "mine" there means
 * `e.k === 'wk' || e.k === 'ow'`, i.e. Terra's own entries render with
 * this accent; no real entry in `PACKET_A2_ENTRIES` has `k === 'ow'`),
 * `colors.surface` (non-"mine" bubble background, the reference file's
 * own `#fff`), `colors.accentDeepest` (the `ar`-role name color,
 * `#3F1FC0` — unreachable by `PACKET_A2_ENTRIES` today, implemented in
 * full anyway per `nameColorFor`'s own doc comment below), and
 * `colors.borderDivider[0]` (the header's own bottom border,
 * `#EEEAF2` — the same real value C7's `PacketHeader.tsx` already
 * uses for an identical header border). One value has no equivalent
 * token and stays a disclosed literal, checked against every color
 * family: the "mine" bubble's own tinted background (`#EFEAFE`).
 * `colors.inkFaint` matches the role label's own real color (`#A79BB4`,
 * line 149) — self-caught before dispatch: the entry `<time>` element
 * on that same line uses a genuinely *different* real color, `#B9AFC4`,
 * which coincidentally matches a real border token,
 * `colors.borderDashed[2]`, reused here for text — an earlier draft
 * wrongly applied `inkFaint` to both.
 *
 * The header itself deliberately does NOT transcribe the reference
 * file's own literal one-line text, `"A.2 · Runtime Package"`
 * (`Atlas Mobile.dc.html:143`) — that string is neither of this
 * program's two already-established real identity fields
 * (`state.eyebrow`, `"m1-a · a.2"`; `state.title`, the full real
 * work-item name) and inventing a third, distinct abbreviated label
 * would violate this program's own fixture-content discipline. This
 * header instead reuses the exact same eyebrow/title pair C7's
 * `PacketHeader.tsx` already established as this packet's one real
 * identity — the README's own single-state-source rule, applied to a
 * second real surface.
 *
 * Unlike C1's desktop `PacketThread`, this view does NOT reuse
 * `computeShowAvatar`'s same-author grouping: the reference file's own
 * mobile `entries` derivation (`renderVals()`) has no such field at
 * all — every entry's name/role/time row renders unconditionally in
 * the real markup (line 149, inside a plain `sc-for`, no `sc-if`) —
 * so this component matches that literal, real structure rather than
 * importing a desktop-only enhancement the mockup's own mobile view
 * never exhibits.
 */
const SHELL_VARS = {
  "--atlas-feed-bg": colors.pageBgMobile,
  "--atlas-header-bg": colors.surface,
  "--atlas-header-border": colors.borderDivider[0],
  "--atlas-back": colors.accent,
  "--atlas-title": colors.ink,
  "--atlas-mine-bg": "#EFEAFE",
  "--atlas-other-bg": colors.surface,
  "--atlas-ink-faint": colors.inkFaint,
  // Same real values ActivityTab.tsx's own History-segment timeline
  // uses, reused verbatim so Chat's timeline reads consistently with
  // Activity's timeline, not a near-miss variant.
  "--atlas-rail": "#E6E0EE",
  "--atlas-dot-ring": colors.pageBgMobile,
  "--atlas-time-color": colors.borderDashed[2],
  "--atlas-ink-muted": colors.inkMuted,
  // Same real value C7's `PacketHeader.tsx` already uses for its own
  // state-line/dot color, for the same reason: only the real blocked
  // trajectory exists today, and `colors.warningText`/`colors.warning`
  // are its real, checked colors there.
  "--atlas-state-color": colors.warningText,
  "--atlas-state-dot": colors.warning,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

function isMine(role: EntryRoleKey): boolean {
  return role === "wk" || role === "ow";
}

/**
 * The reference file's own full `nameColor` rule (`renderVals()`):
 * `e.k === 'ow' ? '#4A28CC' : e.k === 'ar' ? '#3F1FC0' : mine ?
 * '#4A28CC' : '#221C29'` — implemented in full, not reduced to the
 * two branches (`wk`/`co`) `PACKET_A2_ENTRIES` actually exercises
 * today, so a future real entry using `ow`/`ar` renders correctly
 * without this function needing a second look. `#4A28CC` is the real
 * `colors.accentHover`; `#3F1FC0` is the real `colors.accentDeepest`.
 */
function nameColorFor(role: EntryRoleKey): string {
  if (role === "ow") return colors.accentHover;
  if (role === "ar") return colors.accentDeepest;
  return isMine(role) ? colors.accentHover : colors.ink;
}

/**
 * Mobile "Chat" tab — the reference file's own `isThread` view,
 * rendering the real packet thread (via `useRealPacketThread`, the same
 * hook `PacketThread.tsx` uses), reusing its role labels and
 * text-color rule (`textColorFor`, exported from `PacketThread.tsx`
 * for this reuse), restyled as chat bubbles per the reference file's
 * own mobile markup, and `deriveRealHeaderState` for the header — a
 * real-data equivalent of C7's `derivePacketHeaderState`, which only
 * ever implemented the fixture's own escalation story and has no real
 * field to read a status from once this tab shows an arbitrary real
 * packet's events. No message composer or send control is
 * rendered: the reference file's own composer
 * (`Atlas Mobile.dc.html:193-197`) has no real backend counterpart
 * anywhere in M1/M2 — no command exists for sending a chat message to
 * an agent — so rendering an inert-but-visible composer would
 * misrepresent a capability this build does not have, the same
 * reasoning F1's `NowTab` already applied to its own excluded
 * Stop/Start/Open-conversation controls.
 */
export function ChatTab({ onBack, packetId }: { onBack: () => void; packetId: string }) {
  const real = useRealPacketThread(packetId);
  const entries = real.entries;
  const state = deriveRealHeaderState(packetId, entries);

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.header}>
        <button type="button" className={styles.back} onClick={onBack}>
          ‹ Now
        </button>
        <span className={styles.eyebrow}>{state.eyebrow}</span>
        <h1 className={styles.title}>{state.title}</h1>
        {state.latestDetail && <div className={styles.latestDetail}>{state.latestDetail}</div>}
        <div className={styles.stateLine}>
          <span className={styles.dot} aria-hidden="true" />
          {state.stateLine}
        </div>
      </div>
      <div className={styles.feed} aria-live="polite">
        {/* Newest first, so the most recent real event is visible
            immediately without scrolling — unlike C1's desktop
            PacketThread, which keeps the reference file's own
            oldest-first order for a continuous scroll-to-read feed. */}
        {[...entries].reverse().map((entry, index) => {
          const { title, detail } = splitEntryText(entry.text);
          const accent = nameColorFor(entry.k);
          return (
            <div key={`${index}-${entry.who}-${entry.time}`} className={styles.row}>
              <div className={styles.railCol}>
                <span className={styles.rail} aria-hidden="true" />
                <span
                  className={styles.entryDot}
                  aria-hidden="true"
                  style={{ borderColor: accent }}
                />
              </div>
              <div className={styles.body}>
                <div className={styles.entryLine}>
                  <span className={styles.tag} style={{ color: accent }}>
                    {entry.who}
                  </span>
                  {ROLE_LABEL[entry.k] && <span className={styles.role}>{ROLE_LABEL[entry.k]}</span>}
                  <time className={styles.entryMeta}>{entry.time}</time>
                </div>
                <div className={styles.entryTitle} style={{ color: textColorFor(entry) }}>
                  {title}
                </div>
                {detail && <div className={styles.entryDetail}>{detail}</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ChatTab;
