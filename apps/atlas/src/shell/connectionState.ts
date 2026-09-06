import { colors } from "../tokens";

/**
 * `systemState` mirrors the reference files' own real prop (`normal |
 * crashed | disconnected | empty`). This slice (G3) adds `empty`,
 * completing the union G1/G2 built toward.
 *
 * `empty` deliberately has NO branch of its own in
 * `deriveConnectionState` below — it is not a silent omission, it is a
 * real, checked fact: `Atlas Explorations.dc.html`'s own `renderVals()`
 * computes an identical `liveLabel`/`liveDot` pair for `empty` and
 * `normal` once G1's own already-established correction is applied
 * (both render `'idle'`, since this app has no real live connection to
 * claim either way — G1's own correction already applies to `empty`
 * too, not just `normal`), and `empty` never shows a connection strip
 * (no equivalent of `conn.show` branches on it). `empty`'s only real,
 * distinct effect is `DesktopShell.tsx`'s own top-level panel swap,
 * not anything `deriveConnectionState` needs to compute differently —
 * falling through to the existing default is the correct behavior, not
 * an oversight. `connectionState.test.ts` asserts this equivalence
 * explicitly, not implicitly.
 */
export type SystemState = "normal" | "disconnected" | "crashed" | "empty";

export type ConnectionSurface = "desktop" | "mobile";

export interface ConnectionStrip {
  show: boolean;
  bg: string;
  border: string;
  ink: string;
  dot: string;
  title: string;
  body: string;
  meta: string;
}

export interface ConnectionState {
  liveLabel: string;
  liveDotColor: string;
  liveTextColor: string;
  strip: ConnectionStrip;
}

const HIDDEN_STRIP: ConnectionStrip = {
  show: false,
  bg: "",
  border: "",
  ink: "",
  dot: "",
  title: "",
  body: "",
  meta: "",
};

/**
 * Single source of truth for both the top-level live indicator and the
 * connection strip — one function drives both surfaces, matching this
 * program's own C7 "one state value, not independently set fields"
 * discipline.
 *
 * `systemState === "normal"` deliberately renders `liveLabel: "idle"`,
 * NOT the reference files' own default `liveLabel: 'live'`
 * (`Atlas Explorations.dc.html`'s `renderVals()`: `sys === 'empty' ?
 * 'idle' : 'live'`). This app has no real live connection at all yet —
 * no SSE stream, no polling, nothing — so claiming "live" would
 * misrepresent a capability this build does not have, the same
 * discipline already applied to every guarded command this program has
 * built (D2/D6: no fictional command option renders as real). This is
 * a disclosed, deliberate correction, not an oversight; it also fixes
 * a pre-existing inconsistency this slice found while building it:
 * `DesktopShell.tsx` already hardcoded "idle" (correct), but
 * `NowTab.tsx` hardcoded "live" unconditionally (not honest) — both
 * now read from this one function instead.
 *
 * `systemState === "disconnected"`'s strip colors are real B2 tokens,
 * checked directly against `colors.ts`: `colors.warningWash` (bg,
 * `#FEF9F0`), `colors.warningBorder` (border, `#F1DEBE`),
 * `colors.warningText` (ink, `#8A5A08`), `colors.warning` (dot,
 * `#E0A32E`) — an exact match on all four, not a single disclosed
 * literal needed. The strip's own body/meta copy differs by real
 * surface, transcribed verbatim from each reference file's own
 * `renderVals()` (`Atlas Explorations.dc.html` desktop: "...not to
 * this window...", `meta: 'retry 3 · 0:12'`; `Atlas Mobile.dc.html`
 * mobile: "...not to this phone...", `meta: 'retry 3'`, no timer
 * suffix — a real, checked difference between the two surfaces, not a
 * transcription slip).
 *
 * `systemState === "crashed"` (G2) strip colors are real B2 tokens,
 * checked directly against `colors.ts`: `colors.dangerWash` (bg,
 * `#FEF7F6`), `colors.dangerBorder` (border, `#EFC9C4`),
 * `colors.dangerText` (ink, `#A63F36`), `colors.danger` (dot,
 * `#C4564A`) — the same 4 real tokens `CrashCard.tsx` (C6) already
 * establishes, an exact match on all four. `title`/`meta` ("Terra is
 * not running" / "stopped 14:58") are identical in both reference
 * files. `body` differs by real surface, transcribed verbatim:
 * `Atlas Explorations.dc.html` desktop: "A.2 stopped without a
 * handoff. Its worktree and locks are held, so A.3 stays
 * undispatchable until this is resolved."; `Atlas Mobile.dc.html`
 * mobile: "A.2 stopped without a handoff. Worktree and locks are
 * held, so A.3 stays undispatchable." — a real, checked, shorter
 * mobile variant (drops "Its" and the trailing "until this is
 * resolved" clause), not a transcription slip, matching the same
 * per-surface-body-copy convention `disconnected` above already
 * established. Both reference files gate this strip only on
 * `systemState`, never on a separate "which packet is open" check —
 * this app has no multi-packet-selection concept at all (every real
 * surface always shows A.2), so the reference files' own `cur.id ===
 * 'A.2'` guard on their equivalent `crashed` flag is always true here
 * and is correctly omitted, not silently dropped.
 */
export function deriveConnectionState(
  systemState: SystemState,
  surface: ConnectionSurface,
): ConnectionState {
  if (systemState === "crashed") {
    return {
      liveLabel: "idle",
      liveDotColor: colors.inkMuted,
      liveTextColor: colors.inkFaint,
      strip: {
        show: true,
        bg: colors.dangerWash,
        border: colors.dangerBorder,
        ink: colors.dangerText,
        dot: colors.danger,
        title: "Terra is not running",
        body:
          surface === "desktop"
            ? "A.2 stopped without a handoff. Its worktree and locks are held, so A.3 stays undispatchable until this is resolved."
            : "A.2 stopped without a handoff. Worktree and locks are held, so A.3 stays undispatchable.",
        meta: "stopped 14:58",
      },
    };
  }

  if (systemState === "disconnected") {
    return {
      liveLabel: "reconnecting",
      liveDotColor: colors.warning,
      liveTextColor: colors.warningText,
      strip: {
        show: true,
        bg: colors.warningWash,
        border: colors.warningBorder,
        ink: colors.warningText,
        dot: colors.warning,
        title: "Reconnecting",
        body:
          surface === "desktop"
            ? "Atlas lost its connection at 14:58. Agents keep working — they report to the Coordinator, not to this window. What you see below is the last state Atlas received."
            : "Atlas lost its connection at 14:58. Agents keep working — they report to the Coordinator, not to this phone. This is the last state received.",
        meta: surface === "desktop" ? "retry 3 · 0:12" : "retry 3",
      },
    };
  }

  return {
    liveLabel: "idle",
    liveDotColor: colors.inkMuted,
    liveTextColor: colors.inkFaint,
    strip: HIDDEN_STRIP,
  };
}
