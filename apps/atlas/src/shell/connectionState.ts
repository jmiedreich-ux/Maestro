import { colors } from "../tokens";

/**
 * `systemState` mirrors the reference files' own real prop (`normal |
 * crashed | disconnected | empty`), but this slice's own derivation
 * only handles the two branches roadmap item 37 (G1) is scoped to —
 * `normal` and `disconnected`. `crashed` (G2) and `empty` (G3) are
 * separate, future slices; passing either of those literal strings
 * here would be a type error, not a silently-wrong render.
 */
export type SystemState = "normal" | "disconnected";

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
 */
export function deriveConnectionState(
  systemState: SystemState,
  surface: ConnectionSurface,
): ConnectionState {
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
