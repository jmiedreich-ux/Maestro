# M2 Wave G — `crashed` system state (desktop) — Candidate 01

**Slice ID:** `MB-SLICE-M2-G2-CRASHED-STATE-01`
**Status:** `Awaiting Decision Fidelity review`
**Base:** `a4e881c` (full: `a4e881c687fc0a3f15518365085c85f4c9d5535c`, `origin/master`)

## Scope, deliberately minimal

Completes roadmap item 38, *"G2 — `crashed` state,"* for the desktop
surface. An exhaustive audit earlier this session found that despite
prior status-doc language claiming "G2 covers `crashed` via C6/D6,"
nothing anywhere actually mounted the already-real, already-merged
`CrashCard` (C6) from a real `systemState`-driven switch — this slice
is that real, previously-missing work.

**Real, checked correction of this slice's own initial scope
assumption.** The roadmap's own one-line description calls G2 "the
top-level system banner only." A first reading of that phrase suggests
`CrashCard` might belong inside `DesktopShell.tsx` itself, alongside
the existing connection-strip mechanism. Checking the real mockup
directly (`Atlas Explorations.dc.html`) disproves this: the reference
file defines **two separate, simultaneously-real UI elements** for
`sys === 'crashed'` — a small top connection-strip banner ("Terra is
not running..."), AND a full `CrashCard` feed entry appended to the
end of the packet thread's own scrolling list, inside the same
`<sc-for>` block as every other thread entry. "The top-level system
banner only" in the roadmap's own phrasing turns out to mean *no D7
command-wiring*, not *no `CrashCard`* — confirmed by this session's own
already-merged status-doc correction ("mount `CrashCard` from a real
`systemState`-driven switch"). Both real elements are built here.

This slice is frontend-only — no backend file touched. It modifies
exactly 7 existing files: `apps/atlas/src/shell/connectionState.ts`/
`.test.ts`, `apps/atlas/src/thread/PacketThread.tsx`/`.module.css`/
`.test.tsx`, and `apps/atlas/src/shell/DesktopShell.tsx`/`.test.tsx`.
No fixture file, and neither `CrashCard.tsx` nor `crash/fixtures.ts`,
is modified — both are read-only imports, exactly as already built and
reviewed in C6.

**Explicitly deferred, not silently dropped:** the mobile equivalent
(wiring `ChatTab.tsx`'s own fresh crash-card markup, matching this
program's own established "reuse fixture data, write fresh
surface-specific JSX" convention for every other mobile tab) is a
separate, smaller, independently-reviewable slice — a future
`G2B`-style candidate — matching this session's own F4A/F4B and
E1/E1B split precedent, not a scope this single slice absorbs.

## Evidence

`Atlas Explorations.dc.html`'s `renderVals()` (this session's own
cached copy of the design-handoff reference, not checked into this
repository — the same sourcing every prior packet has already
disclosed):

```js
const sys = this.props.systemState || 'normal';
const crashed = sys === 'crashed' && cur.id === 'A.2';
// ...
conn: offline
  ? { ... }
  : sys === 'crashed'
  ? { show: true, bg: '#FEF7F6', border: '#EFC9C4', ink: '#A63F36', dot: '#C4564A', title: 'Terra is not running',
      body: 'A.2 stopped without a handoff. Its worktree and locks are held, so A.3 stays undispatchable until this is resolved.',
      meta: 'stopped 14:58' }
  : { show: false, ... },
crash: {
  show: crashed, cols: mobile ? '1fr' : '1fr 1fr',
  facts: [ ... ], options: [ ... ],
},
```

And the packet-thread markup itself (lines 417-441), the crash row
appended immediately after the entries' own closing `</sc-for>`,
inside the same scrolling feed:

```
<sc-if value="{{ crash.show }}" hint-placeholder-val="{{ false }}">
<div style="display:grid;grid-template-columns:36px minmax(0,1fr);gap:14px;padding:4px 34px 8px;animation:rise .22s ease-out">
  <span></span>
  <div style="min-width:0;max-width:60ch;border:1px solid #EFC9C4;border-radius:14px;background:#FEF7F6;overflow:hidden">
    ... (the exact real content C6's own CrashCard.tsx already renders)
  </div>
</div>
</sc-if>
```

**Real, checked structural match, not a coincidence:** `CrashCard.tsx`'s
own `.row` CSS (`grid-template-columns: 36px minmax(0, 1fr); gap: 14px;
padding: 4px 34px 8px;`) is byte-identical to the mockup's own crash
row wrapper above, and to `PacketThread.tsx`'s own `.row` grid
(`36px minmax(0, 1fr); gap: 14px;`) — confirming `CrashCard` was
already built to slot directly into this exact feed, matching its own
existing doc comment ("Colors from `Atlas Explorations.dc.html`'s
real, non-templated crash markup").

The mockup's own top connection-strip banner has **no equivalent
literal in `Atlas Mobile.dc.html`'s** `body` field — checked directly,
that file's own crashed-state strip body reads "A.2 stopped without a
handoff. Worktree and locks are held, so A.3 stays undispatchable."
(drops "Its" and the trailing "until this is resolved" clause) — a
real, checked, shorter mobile variant, not a transcription slip,
mirroring this program's own already-established `disconnected`
per-surface-body-copy precedent (G1).

`Atlas Explorations.dc.html`'s own `animation:rise .22s ease-out` on
the crash row is a real, exact match to this program's own
`motion.rise` token at its `durationS.max` (`0.22s`) — a different,
real value from every other `.rise` consumer's own `.min` (`0.18s`)
usage (`PerfRecordsList.tsx`, `ActivityTab.tsx`'s own `RecordCard`
detail reveal), checked directly against the reference file, not a
mismatch.

## Design rationale

1. **`CrashCard` is mounted inside `PacketThread`, not `DesktopShell`
   directly.** The real mockup places it inside the same scrolling
   feed as the thread entries, not as a `DesktopShell`-level sibling —
   confirmed by the identical `36px minmax(0,1fr)` grid shared by all
   three files (mockup, `PacketThread.module.css`, `CrashCard.module
   .css`). `DesktopShell.tsx` only threads its own already-existing
   `systemState` prop one level deeper, to `<PacketThread systemState=
   {systemState} />` — a one-line change.
2. **`CrashCard` is mounted as-is, completely unmodified.** No new
   props, no new fixture data — the same already-reviewed C6 component,
   consumed exactly like `GateHeader`/`GateCriteriaList` are consumed
   unmodified by E7C.
3. **The wrapping `.crashRow` div is animation-only, not a duplicate
   grid/padding wrapper.** `CrashCard`'s own `.row` already supplies
   the exact real grid and padding the mockup specifies — `.crashRow`
   only adds the real entrance `animation: rise .22s ease-out` the
   mockup applies to this element, which `CrashCard.tsx`'s own CSS
   does not itself carry. **Disclosed, not fixed:** this is a minor,
   pre-existing gap in the already-merged `CrashCard.module.css` (it
   never received its own entrance animation in C6) — fixing it there
   directly is outside this wiring-only slice's own proportional scope,
   so the animation is applied at the mounting site instead.
4. **`connectionState.ts`'s new `crashed` branch mirrors `disconnected`'s
   own established shape and per-surface-copy convention exactly** —
   same 4-field real-token strip-color derivation pattern, same
   `surface === "desktop" ? ... : ...` body-copy branch, matching G1's
   own precedent structurally, not reinventing a new derivation shape.
5. **The live indicator stays `"idle"` during a crash, not a new,
   distinct label.** This app has no real live connection at all
   (already established for `normal`) — a crash doesn't change that
   fact, so claiming anything other than the already-honest `"idle"`
   would be a new, unjustified claim. (The real mockup's own `liveLabel`
   formula never special-cases `crashed` either — it falls through to
   `'live'` there, which this program's own G1 precedent already
   corrected to `'idle'` for exactly this reason.)
6. **No multi-packet-selection guard needed.** The reference file's own
   `crashed` flag additionally checks `cur.id === 'A.2'`; this app has
   no packet-switching concept at all (every real surface always shows
   A.2's own data), so that guard is always true here and is correctly
   omitted, not silently dropped.

## Guards

1. This slice modifies exactly 7 existing files
   (`connectionState.ts`/`.test.ts`, `PacketThread.tsx`/`.module.css`/
   `.test.tsx`, `DesktopShell.tsx`/`.test.tsx`) — no backend file, no
   fixture file, touched.
2. `apps/atlas/src/crash/CrashCard.tsx`, `.module.css`, `.test.tsx`,
   and `apps/atlas/src/crash/fixtures.ts` are untouched (zero-diff) —
   `CrashCard` is imported and mounted read-only.
3. Every other `systemState` value's own already-reviewed behavior
   (`"normal"`, `"disconnected"`) is byte-unchanged — this slice's own
   diff is strictly additive (`connectionState.ts` gains a new
   branch first in the if-chain; `PacketThread`'s new content is
   conditionally appended, never replacing existing entries).
4. Every other `DesktopShellView` (`performance`, `agents`, `history`,
   `gate`) renders identically regardless of `systemState` — the
   crashed connection strip is a top-level element shown above the nav
   body on every view (matching `disconnected`'s own already-reviewed
   precedent), and `CrashCard` only ever renders inside the "packet"
   view's own thread.
5. No D7 (recovery-command) wiring is added — `CrashCard`'s own 3
   options remain real, inert `<button>` elements with no `onClick`,
   exactly as C6 already built them.

## `apps/atlas/src/shell/connectionState.ts` (modified — full new content)

```ts
import { colors } from "../tokens";

/**
 * `systemState` mirrors the reference files' own real prop (`normal |
 * crashed | disconnected | empty`). This slice (G2) adds `crashed` to
 * G1's own `normal`/`disconnected` derivation. `empty` (G3) remains a
 * separate, future slice; passing it here would still be a type
 * error, not a silently-wrong render.
 */
export type SystemState = "normal" | "disconnected" | "crashed";

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
```

## `apps/atlas/src/shell/connectionState.test.ts` (modified — full new content)

```ts
import { describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { deriveConnectionState } from "./connectionState";

describe("deriveConnectionState", () => {
  it("normal: live indicator reads 'idle', strip hidden, on both surfaces", () => {
    for (const surface of ["desktop", "mobile"] as const) {
      const state = deriveConnectionState("normal", surface);
      expect(state.liveLabel).toBe("idle");
      expect(state.liveDotColor).toBe(colors.inkMuted);
      expect(state.liveTextColor).toBe(colors.inkFaint);
      expect(state.strip.show).toBe(false);
    }
  });

  it("disconnected: live indicator reads 'reconnecting', using real warning tokens", () => {
    const state = deriveConnectionState("disconnected", "desktop");
    expect(state.liveLabel).toBe("reconnecting");
    expect(state.liveDotColor).toBe(colors.warning);
    expect(state.liveTextColor).toBe(colors.warningText);
  });

  it("disconnected: strip is shown with the real warning-token colors", () => {
    const state = deriveConnectionState("disconnected", "desktop");
    expect(state.strip.show).toBe(true);
    expect(state.strip.bg).toBe(colors.warningWash);
    expect(state.strip.border).toBe(colors.warningBorder);
    expect(state.strip.ink).toBe(colors.warningText);
    expect(state.strip.dot).toBe(colors.warning);
    expect(state.strip.title).toBe("Reconnecting");
  });

  it("disconnected: desktop and mobile strips have different real copy, not a shared string", () => {
    const desktop = deriveConnectionState("disconnected", "desktop");
    const mobile = deriveConnectionState("disconnected", "mobile");
    expect(desktop.strip.body).toContain("this window");
    expect(mobile.strip.body).toContain("this phone");
    expect(desktop.strip.body).not.toBe(mobile.strip.body);
    expect(desktop.strip.meta).toBe("retry 3 · 0:12");
    expect(mobile.strip.meta).toBe("retry 3");
  });

  it("(G2) crashed: live indicator stays 'idle' (this app has no real live connection to claim, even mid-crash)", () => {
    const state = deriveConnectionState("crashed", "desktop");
    expect(state.liveLabel).toBe("idle");
    expect(state.liveDotColor).toBe(colors.inkMuted);
    expect(state.liveTextColor).toBe(colors.inkFaint);
  });

  it("(G2) crashed: strip is shown with the real danger-token colors, matching CrashCard's own mapping", () => {
    const state = deriveConnectionState("crashed", "desktop");
    expect(state.strip.show).toBe(true);
    expect(state.strip.bg).toBe(colors.dangerWash);
    expect(state.strip.border).toBe(colors.dangerBorder);
    expect(state.strip.ink).toBe(colors.dangerText);
    expect(state.strip.dot).toBe(colors.danger);
    expect(state.strip.title).toBe("Terra is not running");
    expect(state.strip.meta).toBe("stopped 14:58");
  });

  it("(G2) crashed: desktop and mobile strips have different real copy, not a shared string", () => {
    const desktop = deriveConnectionState("crashed", "desktop");
    const mobile = deriveConnectionState("crashed", "mobile");
    expect(desktop.strip.body).toBe(
      "A.2 stopped without a handoff. Its worktree and locks are held, so A.3 stays undispatchable until this is resolved.",
    );
    expect(mobile.strip.body).toBe(
      "A.2 stopped without a handoff. Worktree and locks are held, so A.3 stays undispatchable.",
    );
    expect(desktop.strip.body).not.toBe(mobile.strip.body);
  });
});
```

## `apps/atlas/src/thread/PacketThread.tsx` (modified — full new content)

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily, motion } from "../tokens";
import { CrashCard } from "../crash/CrashCard";
import type { SystemState } from "../shell/connectionState";
import {
  INITIALS_BY_NAME,
  PACKET_A2_ENTRIES,
  ROLE_LABEL,
  type EntryRoleKey,
  type ThreadEntry,
} from "./fixtures";
import styles from "./PacketThread.module.css";

export interface PacketThreadProps {
  systemState?: SystemState;
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
export function PacketThread({ systemState = "normal" }: PacketThreadProps = {}) {
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
      {systemState === "crashed" && (
        <div className={styles.crashRow}>
          <CrashCard />
        </div>
      )}
    </div>
  );
}

export default PacketThread;
```

## `apps/atlas/src/thread/PacketThread.module.css` (modified — full new content)

```css
.thread {
  display: flex;
  flex-direction: column;
}

.row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 14px;
  padding: 0 34px;
}

.avatar {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font: 600 11.5px var(--atlas-font-mono);
}

.body {
  min-width: 0;
}

.nameRow {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 2px;
}

.name {
  font-weight: 700;
  font-size: 15px;
  color: var(--atlas-ink);
}

.role {
  font-size: 13px;
  color: var(--atlas-ink-muted);
}

.time {
  color: var(--atlas-ink-faint);
  font: 500 12px var(--atlas-font-mono);
}

.text {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  max-width: 62ch;
  text-wrap: pretty;
}

.crashRow {
  animation: crashRise var(--atlas-crash-row-rise-duration) var(--atlas-crash-row-rise-easing);
}

@keyframes crashRise {
  from {
    opacity: 0;
    transform: translateY(var(--atlas-crash-row-rise-translate));
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## `apps/atlas/src/thread/PacketThread.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { computeShowAvatar, PacketThread } from "./PacketThread";
import { PACKET_A2_ENTRIES, type ThreadEntry } from "./fixtures";
import { CRASH_EXAMPLE } from "../crash/fixtures";

afterEach(cleanup);

describe("PacketThread", () => {
  it("renders all six real fixture messages, in order, with their exact body text", () => {
    render(<PacketThread />);
    const bodies = screen.getAllByText(/./, { selector: "p" }).map((p) => p.textContent);
    expect(bodies).toEqual(PACKET_A2_ENTRIES.map((e) => e.text));
  });

  it("shows the avatar and name row on every entry in this fixture (no consecutive same-author pair without an intervening plan/cadence entry)", () => {
    render(<PacketThread />);
    // Every one of the 6 fixture entries in A.2 is either a different
    // author than the previous one, or immediately follows a
    // plan/cadence-bearing entry from the same author — so all 6 show
    // their own avatar and name row. This is a real, checked property
    // of the actual fixture data, not an assumption.
    expect(screen.getAllByText("Coordinator")).toHaveLength(3);
    expect(screen.getAllByText("Terra")).toHaveLength(3);
  });

  it("shows the correct role label next to each name (Coordinator: none, Terra: Implementor)", () => {
    render(<PacketThread />);
    expect(screen.getAllByText("Implementor")).toHaveLength(3);
  });

  it("renders the Coordinator avatar with the reference file's real background, not the neutralChip token's value", () => {
    // colors.neutralChip is "#F2EEF8" — a real, different token this
    // avatar must NOT use. jsdom reports computed inline styles as
    // rgb(...); #F2EEF8 = rgb(242,238,248), #EFEBF2 (the correct,
    // reference-file value) = rgb(239,235,242) — both spelled out
    // explicitly so this assertion actually distinguishes them, rather
    // than comparing an rgb() string to a hex string that could never
    // match either way.
    expect(colors.neutralChip).toBe("#F2EEF8");
    const { container } = render(<PacketThread />);
    const avatars = Array.from(container.querySelectorAll('[aria-hidden="true"]')).filter(
      (el) => el.textContent === "CO",
    );
    expect(avatars.length).toBeGreaterThan(0);
    for (const avatar of avatars) {
      expect((avatar as HTMLElement).style.background).toBe("rgb(239, 235, 242)");
      expect((avatar as HTMLElement).style.background).not.toBe("rgb(242, 238, 248)");
    }
  });

  it("computeShowAvatar: a real consecutive same-author pair with no intervening card groups (avatar omitted)", () => {
    // Synthetic data, for algorithm verification only — not product
    // fixture content. Two plain messages from the same author with
    // nothing between them.
    const synthetic: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00" },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(synthetic, 0)).toBe(true);
    expect(computeShowAvatar(synthetic, 1)).toBe(false);
  });

  it("computeShowAvatar: never groups across a plan- or cadence-bearing entry, even with the same author", () => {
    const syntheticPlan: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00", plan: { name: "x", summary: "y", steps: [] } },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(syntheticPlan, 1)).toBe(true);

    const syntheticCadence: ThreadEntry[] = [
      { k: "wk", who: "Terra", text: "First.", time: "10:00", cadence: true },
      { k: "wk", who: "Terra", text: "Second.", time: "10:01" },
    ];
    expect(computeShowAvatar(syntheticCadence, 1)).toBe(true);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PacketThread />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });

  it("(G2) does not render the real CrashCard when systemState is 'normal' (the default)", () => {
    render(<PacketThread />);
    expect(screen.queryByText("agent stopped unexpectedly")).toBeNull();
  });

  it("(G2) renders the real CrashCard, after every real entry, when systemState is 'crashed'", () => {
    render(<PacketThread systemState="crashed" />);
    expect(screen.getByText("agent stopped unexpectedly")).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.headline)).toBeInTheDocument();
    expect(screen.getByText(CRASH_EXAMPLE.lede)).toBeInTheDocument();

    // Every real fixture message still renders too, in the same order,
    // before the crash card's own lede paragraph — the crash card is
    // appended, not a replacement of the real thread content. (Both
    // PacketThread's own message text and CrashCard's own lede render
    // as <p> elements, so the crash card's lede is the real 7th match.)
    const bodies = screen.getAllByText(/./, { selector: "p" }).map((p) => p.textContent);
    expect(bodies).toEqual([...PACKET_A2_ENTRIES.map((e) => e.text), CRASH_EXAMPLE.lede]);
  });
});
```

## `apps/atlas/src/shell/DesktopShell.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import PacketThread from "../thread/PacketThread";
import { GateHeader } from "../gate/GateHeader";
import { GateCriteriaList } from "../gate/GateCriteriaList";
import { deriveConnectionState, type SystemState } from "./connectionState";
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
} as CSSProperties;

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
            <PacketThread systemState={systemState} />
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
```

## `apps/atlas/src/shell/DesktopShell.test.tsx` (modified — full new content)

```tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import DesktopShell from "./DesktopShell";
import styles from "./DesktopShell.module.css";

afterEach(cleanup);

describe("DesktopShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, not a hand-copied literal", () => {
    const { container } = render(<DesktopShell />);
    const root = container.firstChild as HTMLElement;
    // Corrected — non-blocking finding from Decision Fidelity review:
    // exhaustively checks every SHELL_VARS entry, including the
    // disclosed non-token literals — a prior draft spot-checked only 5
    // of 14 entries, which would not have caught the wrong-value
    // idle-grey defect review found by hand. G1 removed
    // `--atlas-idle-grey`/`--atlas-idle-label` (the live indicator's
    // colors are now computed per-render by `deriveConnectionState`
    // and applied via inline style, not a fixed custom property) and
    // added `--atlas-conn-body` (the connection strip's own fixed body
    // text color) — this list is updated to match.
    expect(root.style.getPropertyValue("--atlas-surface")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-border-divider")).toBe(colors.borderDivider[0]);
    expect(root.style.getPropertyValue("--atlas-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-nav-ground")).toBe(colors.navGround);
    expect(root.style.getPropertyValue("--atlas-nav-text-inactive")).toBe(colors.navTextInactive);
    expect(root.style.getPropertyValue("--atlas-nav-text-active")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-nav-active-bg")).toBe(colors.navActiveBg);
    expect(root.style.getPropertyValue("--atlas-nav-hover-bg")).toBe(colors.navHoverBg);
    expect(root.style.getPropertyValue("--atlas-nav-divider")).toBe("rgba(255,255,255,.08)");
    expect(root.style.getPropertyValue("--atlas-page-bg-desktop")).toBe(colors.pageBgDesktop);
    expect(root.style.getPropertyValue("--atlas-font-mono")).toBe(fontFamily.mono);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-nav-text-running")).toBe(colors.navTextActive);
    expect(root.style.getPropertyValue("--atlas-dot-need")).toBe(colors.warning);
    expect(root.style.getPropertyValue("--atlas-dot-need-halo")).toBe("rgba(224,163,46,.26)");
    expect(root.style.getPropertyValue("--atlas-conn-body")).toBe(colors.inkSecondary);
  });

  it("defaults to systemState 'normal': live indicator says 'idle' with real idle-token colors, no connection strip", () => {
    render(<DesktopShell />);
    const live = screen.getByText("idle").closest('[class*="liveIndicator"]') as HTMLElement;
    expect(live.style.getPropertyValue("--atlas-conn-live-text")).toBe(colors.inkFaint);
    expect(live.style.getPropertyValue("--atlas-conn-live-dot")).toBe(colors.inkMuted);
    expect(screen.queryByText("Reconnecting")).toBeNull();
  });

  it("systemState 'disconnected': live indicator flips to 'reconnecting' and the real connection strip renders", () => {
    render(<DesktopShell systemState="disconnected" />);
    expect(screen.getByText("reconnecting")).toBeInTheDocument();
    expect(screen.getByText("Reconnecting")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Atlas lost its connection at 14:58. Agents keep working — they report to the Coordinator, not to this window. What you see below is the last state Atlas received.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("retry 3 · 0:12")).toBeInTheDocument();
  });

  it("(G2) systemState 'crashed': the real danger-toned connection strip renders on every view, not just the packet view", () => {
    render(<DesktopShell systemState="crashed" />);
    expect(screen.getByText("Terra is not running")).toBeInTheDocument();
    expect(
      screen.getByText(
        "A.2 stopped without a handoff. Its worktree and locks are held, so A.3 stays undispatchable until this is resolved.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("stopped 14:58")).toBeInTheDocument();
    // The live indicator itself stays "idle" even mid-crash — this app
    // has no real live connection to claim either way.
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("(G2) systemState 'crashed': selecting the A.2 packet row renders the real CrashCard appended to the real thread", () => {
    render(<DesktopShell systemState="crashed" />);
    fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
    expect(screen.getByText("agent stopped unexpectedly")).toBeInTheDocument();
    // The real thread content is still there too — the crash card is
    // appended, not a replacement.
    expect(screen.getByText(PACKET_A2_ENTRIES[0].text)).toBeInTheDocument();
  });

  it("(G2) systemState 'crashed' has no effect on any other view's own content", () => {
    render(<DesktopShell systemState="crashed" />);
    fireEvent.click(screen.getByRole("button", { name: /^History/ }));
    expect(screen.getByText("History view")).toBeInTheDocument();
    expect(screen.queryByText("agent stopped unexpectedly")).toBeNull();
  });

  it("renders the top bar's idle live indicator", () => {
    render(<DesktopShell />);
    expect(screen.getByText("idle")).toBeInTheDocument();
  });

  it("renders the four static nav rows plus the packet row, in order", () => {
    render(<DesktopShell />);
    const rows = screen.getAllByRole("button");
    expect(rows.map((row) => row.textContent?.replace("—", "").trim())).toEqual([
      "Performance",
      "Agents",
      "History",
      "A.2 · Runtime Package",
      "M1-B gate",
    ]);
  });

  it("defaults to Performance selected, with only one row marked current", () => {
    render(<DesktopShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Performance");
    expect(screen.getByText("Performance view")).toBeInTheDocument();
  });

  it("clicking a row makes it the sole selected row and updates the content pane", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /History/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("History");
    expect(screen.getByText("History view")).toBeInTheDocument();
    expect(screen.queryByText("Performance view")).not.toBeInTheDocument();
  });

  it("never renders a literal 0 for the unavailable nav counts", () => {
    render(<DesktopShell />);
    expect(screen.queryByText("0")).not.toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(4);
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<DesktopShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });

  it("renders the A.2 packet row between History and the M1-B gate row", () => {
    render(<DesktopShell />);
    // Corrected: the real NavRow always appends a trailing mono count
    // span ("—") to its own text, exactly like the pre-existing "renders
    // exactly four static nav rows" test already accounts for — this
    // test's first draft omitted that same normalization and failed
    // against the real rendered output.
    const rows = screen
      .getAllByRole("button")
      .map((r) => r.textContent?.replace("—", "").trim());
    expect(rows).toEqual(["Performance", "Agents", "History", "A.2 · Runtime Package", "M1-B gate"]);
  });

  it("selecting the A.2 row shows the real packet thread, not a placeholder", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("A.2");
    // PacketThread's own first fixture message, proving the real
    // component rendered, not a "packet view" placeholder string.
    expect(screen.getByText(PACKET_A2_ENTRIES[0].text)).toBeInTheDocument();
    expect(screen.queryByText("packet view")).not.toBeInTheDocument();
  });

  it("selecting a static row after the packet row correctly unmounts the thread", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /A\.2/ }));
    // Corrected: the real accessible name is "Agents—" (the trailing
    // mono count), so the exact string "Agents" never matches — the same
    // class of fix as the test above, using a regex here instead since
    // this call needs to select one specific row, not compare a full list.
    fireEvent.click(screen.getByRole("button", { name: /^Agents/ }));
    expect(screen.getByText("Agents view")).toBeInTheDocument();
    expect(screen.queryByText(PACKET_A2_ENTRIES[0].text)).not.toBeInTheDocument();
  });

  it("(E7C) selecting the M1-B gate row renders the real GateHeader and GateCriteriaList, not the placeholder", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("M1-B gate");

    // Real GateHeader content.
    expect(screen.getByRole("heading", { name: "Overlay and support surfaces" })).toBeInTheDocument();
    expect(screen.getByText("approver")).toBeInTheDocument();
    // Real GateCriteriaList content.
    expect(screen.getByText("entry criteria")).toBeInTheDocument();
    expect(screen.getByText("A.0 through A.7 accepted")).toBeInTheDocument();

    expect(screen.queryByText("M1-B gate view")).not.toBeInTheDocument();
  });

  it("(E7C) selecting a different static row after the gate row correctly unmounts GateHeader/GateCriteriaList", () => {
    render(<DesktopShell />);
    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    fireEvent.click(screen.getByRole("button", { name: /^Performance/ }));
    expect(screen.getByText("Performance view")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Overlay and support surfaces" })).not.toBeInTheDocument();
    expect(screen.queryByText("entry criteria")).not.toBeInTheDocument();
  });

  it("(E7C, corrected — Decision Fidelity review finding) the gate view's <main> uses the no-padding .contentGate class, and every other view keeps the padded .content class", () => {
    // The reviewer proved this by mutation-testing: reverting the gate
    // view's className from `styles.contentGate` back to `styles.content`
    // (the exact regression Design Rationale #1 exists to avoid — doubling
    // GateHeader's own 34px gutter) left all other tests passing, since
    // none of them asserted on <main>'s own className. This test compares
    // against the real imported CSS-module identifiers, not hand-typed
    // strings, so it fails under that exact mutation.
    render(<DesktopShell />);
    const main = screen.getByTestId("desktop-shell-main");
    expect(main.className).toBe(styles.content);
    expect(main.className).not.toBe(styles.contentGate);

    fireEvent.click(screen.getByRole("button", { name: /^M1-B gate/ }));
    expect(main.className).toBe(styles.contentGate);
    expect(main.className).not.toBe(styles.content);

    fireEvent.click(screen.getByRole("button", { name: /^Performance/ }));
    expect(main.className).toBe(styles.content);
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to a scratch
worktree (branch `architecture/m2-g2-crashed-state`, base `a4e881c`)
and run through the real frontend toolchain from `apps/atlas` (`npm
install`, then each script below) before this packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **25/25 test files, 224/224 tests
  passed** (`connectionState.test.ts`: 7, up from 4;
  `PacketThread.test.tsx`: 9, up from 7; `DesktopShell.test.tsx`: 18,
  up from 15; zero regressions in the other 22 files, including
  `CrashCard.test.tsx`, which this slice does not modify).
- `npm run build` (`vite build`) — clean, `48 modules transformed`
  (up from 45 — `CrashCard.tsx`/`.module.css` and `crash/fixtures.ts`
  are now reachable from the app's own entry point for the first
  time), no warnings.
- Every declared `--atlas-*` custom property, and every CSS class
  declared in `PacketThread.module.css`, was cross-checked
  programmatically against `PacketThread.tsx`'s own references — zero
  orphans in either direction.
- One real test-authoring correction was made during this
  verification pass, caught by the toolchain itself before this
  packet was finalized: the "renders the real CrashCard... when
  systemState is 'crashed'" test's `bodies` assertion initially
  expected only the 6 real thread messages, but `CrashCard`'s own
  `.lede` also renders as a `<p>` element (matching this same file's
  own `getAllByText(/./, { selector: "p" })` query), so the real,
  correct expectation is the 6 messages plus the crash card's own
  lede, in that order — corrected before finalizing.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** selecting `systemState="crashed"` on
   `DesktopShell` shows a real, danger-toned connection strip on every
   view, and shows the real, already-built `CrashCard` appended to the
   real packet thread when the A.2 packet view is selected — completing
   roadmap item 38 (G2) for the desktop surface, with zero backend
   change and zero regression to any of the 22 other existing test
   files.
2. **Operating and threat model:** none — pure frontend rendering of
   already-real, already-reviewed fixture data; no network call, no
   command dispatch.
3. **Explicit exclusions:** any D7 recovery-command wiring (`CrashCard`'s
   3 options remain real, inert buttons, exactly as already built);
   the mobile equivalent (`ChatTab.tsx` wiring, a future `G2B`-style
   candidate); any modification to `CrashCard.tsx`/`crash/fixtures.ts`
   themselves (both read-only, untouched); the empty state (`G3`,
   separate future slice).
4. **Assurance level:** practical correctness for a fixture-driven
   conditional-rendering slice — every rendered surface (connection
   strip on every view, `CrashCard` in the packet view only, no effect
   on any other view) is exercised by a React Testing Library render/
   interaction test; no browser-based visual verification was
   performed (tooling limitation already disclosed for every prior M2
   slice this session); the mockup source is this session's own cached
   copy, not part of this repository, also already-disclosed sourcing.
5. **Acceptance proof:** 25/25 test files, 224/224 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 7 modified files, all within
   `apps/atlas/src/shell` and `apps/atlas/src/thread`; zero backend
   files; no new third-party dependency; `apps/atlas/src/crash/*`
   read-only, never modified.
7. **Proportionality ceiling:** one new branch in `connectionState.ts`,
   one new conditional block in `PacketThread.tsx` (plus an
   animation-only CSS wrapper), one one-line prop-threading change in
   `DesktopShell.tsx` — no new fixture data invented, no new component
   built, no already-reviewed component modified.
8. **Stop and escalation rule:** wiring `CrashCard`'s own recovery
   options to a real command, building the mobile (`ChatTab`)
   equivalent, or fixing `CrashCard.module.css`'s own missing entrance
   animation at its source, are explicitly out of scope — future
   slices' job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-G2-CRASHED-STATE-01` |
| `phase` | `AwaitingReview` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `0` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-g2-crashed-state.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
