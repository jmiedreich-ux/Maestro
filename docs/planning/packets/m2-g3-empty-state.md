# M2 Wave G — `empty` system state (desktop) — Candidate 01

**Slice ID:** `MB-SLICE-M2-G3-EMPTY-STATE-01`
**Status:** `MergeReady`
**Base:** `c8919dd` (full: `c8919dd2aa20db5c461788da0dd0374196357908`, `origin/master`)

## Scope, deliberately minimal

Completes roadmap item 39, *"G3 — `empty` state,"* for the desktop
surface — the last item on the M2 roadmap. Adds `"empty"` as the
fourth and final `SystemState` value, and a full-bleed top-level empty
panel in `DesktopShell` that replaces the nav sidebar and main content
area entirely when a project has no packets yet.

This slice is frontend-only — no backend file touched. It modifies
exactly 5 existing files: `apps/atlas/src/shell/connectionState.ts`/
`.test.ts` and `apps/atlas/src/shell/DesktopShell.tsx`/`.module.css`/
`.test.tsx`. No new component file, no fixture file, touched.

**Explicitly deferred, not silently dropped:** the mobile equivalent
(`MobileShell.tsx` gaining its own first-ever `systemState` prop, plus
its own fresh empty-state markup) is a separate, smaller,
independently-reviewable slice — a future `G3B`-style candidate,
matching this session's own G2/G2B split precedent — not a scope this
single slice absorbs.

## Evidence

The real mockup (`Atlas Explorations.dc.html`, this session's own
cached copy of the design-handoff reference, not checked into this
repository — the same sourcing every prior packet has already
disclosed), lines 8-56, with the surrounding structural context that
resolves this slice's own central design question:

```html
<div style="height:100dvh;...display:flex;flex-direction:column;...">
  <header style="flex:none;...">...top bar, including {{ liveLabel }}...</header>
  <sc-if value="{{ conn.show }}" ...>
  <div style="flex:none;...">...connection strip...</div>
  </sc-if>
  <div style="flex:1;min-height:0;display:grid;grid-template-columns:{{ cols }}">
    <sc-if value="{{ showEmpty }}" hint-placeholder-val="{{ false }}">
    <main style="grid-column:1/-1;min-width:0;min-height:0;display:flex;align-items:center;justify-content:center;padding:40px 34px;background:#FCFBFD">
      <div style="max-width:46ch;text-align:center">
        <div style="display:flex;justify-content:center;gap:6px;margin-bottom:20px">
          <span style="width:34px;height:44px;border-radius:8px;border:1.5px dashed #D6CFE0"></span>
          <span style="...opacity:.7"></span>
          <span style="...opacity:.4"></span>
        </div>
        <h1 style="...font-family:'Bricolage Grotesque',sans-serif;font-size:23px;font-weight:600;letter-spacing:-.02em;line-height:1.2;...">Foundry has no packets yet</h1>
        <p style="margin:9px 0 0;font-size:14.5px;line-height:1.6;color:#6C6376;...">The project is registered but no milestone has been planned. The Architect agent writes the packet plan from your issue; nothing can be dispatched until it exists.</p>
        <div style="display:flex;justify-content:center;gap:9px;margin-top:20px">
          <button style="...background:#5B34E8;color:#fff;..." style-hover="background:#4A28CC">Plan a milestone</button>
          <button style="...border:1px solid #E0DAEA;...background:#fff;color:#221C29;..." style-hover="border-color:#C9BEDC">Link an issue</button>
        </div>
        <div style="margin-top:16px;font-size:12.5px;color:#A79BB4">Registered 2 days ago · no agents attached</div>
      </div>
    </main>
    </sc-if>
    <!-- the real nav + content grid items sit here, as siblings -->
  </div>
</div>
```

**Real, checked, load-bearing structural fact this slice's own design
rests on:** the `<header>` and the `conn.show` connection strip both
sit *outside* the `display:grid` body container entirely — neither is
gated by `showEmpty` in any way. Only the inner nav+main split is
inside that grid, and only that split needs to change for the empty
state.

**Real, checked self-contradiction in the reference file, resolved by
this slice, not guessed at.** The same file's own `showNav` formula
(`renderVals()`, elsewhere in the file) is `!mobile || s.tab ===
'plan'` — a formula that never checks `sys === 'empty'` at all. At any
desktop width, `showNav` evaluates `true` unconditionally, regardless
of `sys`. Read literally, the reference file's own code would render
both the full-span (`grid-column:1/-1`) empty panel AND the nav
sidebar simultaneously as CSS grid siblings — an incoherent layout (the
grid's auto-placement algorithm would push the nav into its own,
separate implicit row, since the empty panel already claims the entire
first row). No other real `systemState` value has this conflict —
`crashed`/`disconnected` both render the nav normally, matching
`showNav`'s own literal, correct behavior for those states. This is a
genuine oversight in the reference file, not a deliberate design.
**Resolution:** this slice hides the nav sidebar (and the `<main>` it
normally pairs with) whenever `systemState === "empty"`, matching what
the empty panel's own `grid-column:1/-1` sizing clearly signals was
intended.

## Design rationale

1. **The nav sidebar (and its own `<main>`) do not render at all when
   `systemState === "empty"`** — resolving the reference file's own
   self-contradiction the way its own full-span sizing implies, not a
   guess (see Evidence). The header and connection-strip mechanism
   above `.body` are untouched either way.
2. **Real-mechanism correction, not a persona swap.** The reference
   file's own body copy claims *"The Architect agent writes the packet
   plan from your issue"* — the same class of fully-autonomous,
   not-yet-real capability claim `GateHeader.tsx`'s own `approverNote`
   and `GateSheet.tsx`'s own `mechanismNote` already found and
   corrected (no code anywhere in `services/maestro/maestro/*.py`
   derives a packet plan from an issue automatically). Corrected to
   state the real, current mechanism honestly: no automated plan
   generation exists yet; planning a milestone remains a manual,
   owner-initiated action.
3. **Real, disclosed substitution, not an invented specific.** The
   reference file's own heading names a specific fictional project,
   *"Foundry"* — a name this app has never established anywhere
   (checked directly: zero occurrences of "Foundry" or any of the
   reference file's other example project names, e.g. "VennueSign,"
   anywhere in `apps/atlas/src`). `DesktopShell.tsx`'s own top bar
   already discloses the real fact that no project name is wired
   ("Project name unavailable") — the empty state's own heading reuses
   that same real, honest framing ("This project") instead of
   inventing a specific name the rest of this shell doesn't have.
4. **The trailing meta line and both button labels are transcribed
   verbatim.** "Registered 2 days ago · no agents attached" is
   narrative/descriptive copy about this already-established
   fictional-but-consistent project scenario, not a capability claim,
   so it needs no correction — unlike item 2 above, which describes an
   actual system behavior.
5. **Both action buttons stay real, inert `<button>` elements with no
   `onClick`.** No real "plan a milestone" or "link an issue" command
   exists yet, matching this program's own established "options
   rendered but inert until wired" convention (`AgentsRoster`'s "Open
   thread," `CrashCard`'s own 3 options, `GateSheet`'s disabled "Open
   gate").
6. **`deriveConnectionState` gets no new `"empty"` branch.** This is a
   real, checked fact, not an oversight: the reference file's own
   `renderVals()` computes an identical `liveLabel`/`liveDot` pair for
   `empty` and `normal` once G1's own already-established correction is
   applied (both real states render `'idle'`, since this app has no
   real live connection to claim either way), and `empty` never shows a
   connection strip either. Adding a second, functionally-identical
   branch would be dead-weight duplication, not clarity — the existing
   default already produces the correct output; `connectionState.test
   .ts` proves the equivalence explicitly.

## Guards

1. This slice modifies exactly 5 existing files
   (`connectionState.ts`/`.test.ts`, `DesktopShell.tsx`/`.module.css`/
   `.test.tsx`) — no backend file, no fixture file, no new component
   file, touched.
2. Every other `SystemState` value's own already-reviewed behavior
   (`"normal"`, `"disconnected"`, `"crashed"`) is byte-unchanged.
3. When `systemState !== "empty"`, `DesktopShell`'s own nav/main
   rendering is identical to its pre-slice behavior — the empty-state
   branch is a sibling conditional, not a restructuring of the existing
   path.
4. Both empty-state action buttons are real, inert `<button>` elements
   with no `onClick` — no real command exists to wire them to.
5. No fictional "Architect agent" autonomous-planning claim, and no
   invented specific project name, render anywhere in the empty state.

## Decision Fidelity review result: PASS

An independent review returned a clean **PASS** with rigorous,
targeted scrutiny of this packet's own central, unusually strong
claim — that the real mockup contains a genuine self-contradiction
between the empty panel's full-span sizing and the nav sidebar's own
unconditional visibility rule. The review independently confirmed,
directly against the mockup file: `showNav`'s own formula never checks
`sys`, `empty` is the only real state where this creates a conflict
(`crashed`/`disconnected` have none), and the header/connection-strip
mechanism genuinely sits outside the affected grid. The review also
independently proved the "no new `deriveConnectionState` branch
needed" claim by adding a distinct branch in a scratch copy and
confirming it produced byte-identical output to the no-branch version.
Every color token, the two disclosed content corrections, the diff
scope, and zero CSS orphans were all independently reproduced. No
correction was required; this packet's own code blocks below are
unchanged from what the review verified.

## `apps/atlas/src/shell/connectionState.ts` (modified — full new content)

```ts
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

  it("(G3) empty: derives identically to 'normal' — a real, checked fact, not an unhandled state", () => {
    for (const surface of ["desktop", "mobile"] as const) {
      const empty = deriveConnectionState("empty", surface);
      const normal = deriveConnectionState("normal", surface);
      expect(empty).toEqual(normal);
      expect(empty.liveLabel).toBe("idle");
      expect(empty.strip.show).toBe(false);
    }
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
 */
function EmptyState() {
  return (
    <div className={styles.emptyPanel}>
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
    </div>
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
```

## `apps/atlas/src/shell/DesktopShell.module.css` (modified — full new content)

```css
.shell {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.topBar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--atlas-surface);
  border-bottom: 1px solid var(--atlas-border-divider);
  padding: 16px 34px 15px;
  flex: 0 0 auto;
}

.projectInfo {
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: var(--atlas-ink);
  font: 600 16px var(--atlas-font-body);
}

.milestone {
  color: var(--atlas-ink-muted);
  font: 400 13.5px var(--atlas-font-body);
}

.liveIndicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--atlas-conn-live-text);
  font: 600 10.5px var(--atlas-font-mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.liveDot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--atlas-conn-live-dot);
}

.connectionStrip {
  flex: none;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 9px 16px;
  background: var(--atlas-conn-strip-bg);
  border-bottom: 1px solid var(--atlas-conn-strip-border);
  color: var(--atlas-conn-strip-ink);
  font-size: 13px;
}

.connectionTitle {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.connectionDot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--atlas-conn-strip-dot);
}

.connectionBody {
  min-width: 0;
  flex: 1;
  line-height: 1.5;
  color: var(--atlas-conn-body);
  text-wrap: pretty;
}

.connectionMeta {
  flex: none;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-conn-strip-ink);
}

.body {
  display: grid;
  grid-template-columns: minmax(230px, 268px) minmax(0, 1fr);
  flex: 1 1 auto;
  min-height: 0;
}

@media (max-width: 900px) {
  .body {
    grid-template-columns: 1fr;
  }
}

.nav {
  background: var(--atlas-nav-ground);
  padding: 16px 10px 22px;
  overflow-y: auto;
}

.navRow {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 0 10px;
  border-radius: 8px;
  color: var(--atlas-nav-text-inactive);
  font: 600 13.5px var(--atlas-font-body);
  cursor: pointer;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
}

.navRow:hover {
  background: var(--atlas-nav-hover-bg);
}

.navRowActive {
  background: var(--atlas-nav-active-bg);
  color: var(--atlas-nav-text-active);
}

.navGlyph {
  width: 8px;
  height: 8px;
  border-radius: 3px;
  background: var(--atlas-ink-muted);
  flex: 0 0 auto;
}

.navLabel {
  flex: 1 1 auto;
}

.navCount {
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-ink-muted);
}

.navDivider {
  height: 1px;
  background: var(--atlas-nav-divider);
  margin: 12px 10px;
}

.content {
  background: var(--atlas-page-bg-desktop);
  overflow-y: auto;
  padding: 34px;
  color: var(--atlas-ink-muted);
  font: 400 13.5px var(--atlas-font-body);
}

.contentGate {
  background: var(--atlas-page-bg-desktop);
  overflow-y: auto;
}

.gateCriteriaWrap {
  padding: 0 34px 30px;
}

.packetRow {
  display: flex;
  align-items: center;
  gap: 11px;
  min-height: 40px;
  padding: 8px 10px;
  border-radius: 8px;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font: 400 14px var(--atlas-font-body);
  color: var(--atlas-nav-text-running);
}

.packetRow:hover {
  background: var(--atlas-nav-hover-bg);
}

.packetRowActive {
  background: var(--atlas-nav-active-bg);
  font-weight: 600;
}

.packetLabel {
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.packetDot {
  flex: none;
  display: inline-block;
  box-sizing: border-box;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--atlas-dot-need);
  box-shadow: 0 0 0 3px var(--atlas-dot-need-halo);
}

.emptyPanel {
  grid-column: 1 / -1;
  min-width: 0;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 34px;
  background: var(--atlas-page-bg-desktop);
}

.emptyContent {
  max-width: 46ch;
  text-align: center;
}

.emptyDashes {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 20px;
}

.emptyDash {
  width: 34px;
  height: 44px;
  border-radius: 8px;
  border: 1.5px dashed var(--atlas-empty-dash);
}

.emptyTitle {
  margin: 0;
  font-family: var(--atlas-font-display);
  font-size: 23px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.2;
  text-wrap: pretty;
}

.emptyBody {
  margin: 9px 0 0;
  font-size: 14.5px;
  line-height: 1.6;
  color: var(--atlas-empty-body);
  text-wrap: pretty;
}

.emptyActions {
  display: flex;
  justify-content: center;
  gap: 9px;
  margin-top: 20px;
}

.emptyPrimaryButton {
  height: 36px;
  padding: 0 15px;
  border: 0;
  border-radius: 9px;
  background: var(--atlas-empty-primary-bg);
  color: var(--atlas-empty-primary-ink);
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 600;
}

.emptyPrimaryButton:hover {
  background: var(--atlas-empty-primary-bg-hover);
}

.emptySecondaryButton {
  height: 36px;
  padding: 0 15px;
  border: 1px solid var(--atlas-empty-secondary-border);
  border-radius: 9px;
  background: var(--atlas-empty-secondary-bg);
  color: var(--atlas-empty-secondary-ink);
  cursor: pointer;
  font-size: 13.5px;
  font-weight: 600;
}

.emptySecondaryButton:hover {
  border-color: var(--atlas-empty-secondary-border-hover);
}

.emptyMeta {
  margin-top: 16px;
  font-size: 12.5px;
  color: var(--atlas-empty-meta);
}
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

  it("(G3) systemState 'empty': renders the real empty-state panel with no nav sidebar and no <main> content view", () => {
    render(<DesktopShell systemState="empty" />);
    expect(screen.getByRole("heading", { name: "This project has no packets yet" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "The project is registered but no milestone has been planned. No automated packet-plan generation exists in Maestro today — planning a milestone from an issue is a manual, owner-initiated action; nothing can be dispatched until a plan exists.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Registered 2 days ago · no agents attached")).toBeInTheDocument();

    // No fictional autonomous-planning claim, and no invented project name.
    expect(screen.queryByText(/Architect agent writes the packet plan/)).toBeNull();
    expect(screen.queryByText(/Foundry/)).toBeNull();

    // Real, disclosed correction: the nav sidebar and every other
    // view's own content are not rendered at all in the empty state.
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.queryByTestId("desktop-shell-main")).toBeNull();
    expect(screen.queryByText("Performance view")).toBeNull();
  });

  it("(G3) systemState 'empty': both action buttons are real, inert <button> elements with no onClick side effect", () => {
    render(<DesktopShell systemState="empty" />);
    const planButton = screen.getByRole("button", { name: "Plan a milestone" });
    const linkButton = screen.getByRole("button", { name: "Link an issue" });
    fireEvent.click(planButton);
    fireEvent.click(linkButton);
    // No visible state change of any kind — still the same empty panel.
    expect(screen.getByRole("heading", { name: "This project has no packets yet" })).toBeInTheDocument();
  });

  it("(G3) systemState 'empty': the top bar and (hidden, since 'empty' shows no strip) connection strip mechanism are unaffected", () => {
    render(<DesktopShell systemState="empty" />);
    expect(screen.getByText("Project name unavailable")).toBeInTheDocument();
    expect(screen.getByText("idle")).toBeInTheDocument();
    expect(screen.queryByText("Reconnecting")).toBeNull();
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
worktree (branch `architecture/m2-g3-empty-state`, base `c8919dd`) and
run through the real frontend toolchain from `apps/atlas` (`npm
install`, then each script below) before this packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **25/25 test files, 228/228 tests
  passed** (`connectionState.test.ts`: 8, up from 7;
  `DesktopShell.test.tsx`: 21, up from 18; zero regressions in the
  other 23 files).
- `npm run build` (`vite build`) — clean, `48 modules transformed`
  (unchanged from G2 — no new files added, only existing files grew),
  no warnings.
- Every declared `--atlas-*` custom property, and every CSS class
  declared in `DesktopShell.module.css`, was cross-checked
  programmatically against `DesktopShell.tsx`'s own references — zero
  orphans in either direction. One real gap was caught and fixed
  during this same pass, before finalizing: the empty-state heading's
  own `var(--atlas-font-display)` reference had no matching `SHELL_VARS`
  entry in the first draft (`fontFamily.display` was never wired) —
  added as its own disclosed, named entry rather than reusing an
  existing one for an unrelated purpose.
- A second real naming issue was caught and fixed during the same
  pass: the primary button's own white text color was first wired
  through the secondary button's own `--atlas-empty-secondary-bg`
  variable (the same real value, `colors.surface`, but a confusing
  cross-semantic reuse) — corrected to its own dedicated
  `--atlas-empty-primary-ink` variable before finalizing.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** `systemState="empty"` renders a real,
   full-bleed empty-state panel in `DesktopShell` — no nav sidebar, no
   other view's content — with real, corrected copy and two real,
   inert action buttons, completing roadmap item 39 (G3) for desktop
   and closing out the entire M2 roadmap's independent-work list with
   zero backend change and zero regression to any of the 23 other
   existing test files.
2. **Operating and threat model:** none — pure frontend conditional
   rendering of static copy; no network call, no command dispatch.
3. **Explicit exclusions:** the mobile equivalent (`MobileShell.tsx`
   gaining its own first-ever `systemState` prop, a future `G3B`-style
   candidate); wiring either action button to a real command (neither
   exists); any modification to `GateHeader.tsx`/`GateCriteriaList.tsx`/
   `CrashCard.tsx`/`PacketThread.tsx` (all untouched).
4. **Assurance level:** practical correctness for a fixture-driven
   conditional-rendering slice — every rendered surface (empty panel
   content, nav/main absence, button inertness, unaffected header/
   connection-strip mechanism) is exercised by a React Testing Library
   render/interaction test; no browser-based visual verification was
   performed (tooling limitation already disclosed for every prior M2
   slice this session); the mockup source is this session's own cached
   copy, not part of this repository, also already-disclosed sourcing.
   This slice's own central design decision (hiding the nav sidebar)
   resolves a genuine self-contradiction in that mockup, not a
   universally-unambiguous spec — disclosed explicitly, not asserted as
   the only possible reading.
5. **Acceptance proof:** 25/25 test files, 228/228 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 5 modified files, all within
   `apps/atlas/src/shell`; zero backend files; no new third-party
   dependency; no other component file touched.
7. **Proportionality ceiling:** one new private component
   (`EmptyState`, inline in `DesktopShell.tsx`, matching `NavRow`'s own
   established "small private helper, same file" precedent) plus a new
   CSS block and one new conditional branch — no new fixture data
   invented, no new exported component file, no already-reviewed
   component modified.
8. **Stop and escalation rule:** building the mobile empty-state
   screen, or wiring either action button to a real command once one
   exists, is explicitly out of scope — future slices' job, not this
   one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-G3-EMPTY-STATE-01` |
| `phase` | `MergeReady` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-g3-empty-state.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
