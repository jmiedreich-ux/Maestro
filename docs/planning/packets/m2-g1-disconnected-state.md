# M2 Wave G — Disconnected State (Connection Strip + Live Indicator) — Candidate 01

**Slice ID:** `MB-SLICE-M2-G1-DISCONNECTED-STATE-01`
**Status:** `Decision Fidelity review returned PASS WITH NON-BLOCKING NOTES (a misquoted status-doc citation, an overstated "same gap" framing, and a nonexistent AgentCard.tsx file cited twice instead of AgentsRoster.tsx's own private AgentCard function) — all fixed at zero cost, no planning correction needed`
**Base:** `a72ab45` (full: `a72ab4503228fe69768d9b46d67b2aa33b433a0d`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 37, *"G1 — `disconnected` state: connection strip +
live-indicator flip, driven by A7's reconnect contract."* Investigated
before authoring: **A6 (the SSE event stream, `GET /stream/events`)
and A7 (the reconnect/resync contract) were never built.**
`services/maestro/maestro/read_api.py`'s own module docstring and
`_ROUTES` table are exhaustive — `/health`, `/snapshot/packets`,
`/snapshot/attempts`, `/snapshot/reviews`, `/snapshot/events` only; no
`/stream/events` route, no SSE handling, no last-seen-event-id/gap-
fill logic anywhere in this repository. **Corrected — non-blocking
finding from Decision Fidelity review:** this A6/A7 gap is real and
independently sufficient justification on its own, but it is not
literally identical to what already got C2/D3/D7 rescheduled to M3 —
those three were rescheduled because specific fixture data
(`OwnerDecisionCard`'s `packet_id`, `CrashCard`'s fixture) has no
matching real backend row, a data-availability mismatch, not
specifically the missing stream/reconnect machinery (which C2's own
paragraph names as only part of a "more fundamental" cause). Both are
real, related backend-immaturity gaps recorded in the same M3-target
family, not one and the same finding
(`docs/planning/maestro-development-status.md`, the C2 deferral
paragraph, quoted exactly: *"(Wave A stopped at A5; A6/A7 were never
built)"*). There is also no existing frontend consumer of any kind —
every Atlas component built so far is fixture-driven, none polls or
streams from the backend.

**This slice does not, and cannot, wire a real trigger for the
`disconnected` state** — that requires A6/A7, which do not exist.
Following this program's own established pattern (C1/C6/D2's
"options rendered but inert until the real command exists," and C2/
D3/D7's own precedent of building the presentational piece standalone
before its real-data dependency lands), this slice builds the real,
tested **presentational** connection-strip and live-indicator
component, threaded through an explicit `systemState` prop on
`DesktopShell` and `NowTab` (mirroring the reference files' own real
`systemState` prop mechanism exactly). **The real trigger — what
would ever set `systemState` to `"disconnected"` in the running
app — is A6/A7's own job, rescheduled to M3 alongside C2/D3/D7.**
This is not a corner cut silently: it is disclosed here, in the
roadmap, and in all 3 status docs, exactly like every other
unbuilt-dependency finding this session has made.

This slice is frontend-only — no backend file touched. It adds 2 new
files and modifies 6 existing files, all within `apps/atlas/src/shell`.

## Evidence

**Backend gap** (`services/maestro/maestro/read_api.py`):
- Module docstring (lines 1-2): `"""Loopback-only read API: /health,
  /snapshot/packets, /snapshot/attempts, /snapshot/reviews, and
  /snapshot/events."""`
- `_ROUTES` (lines 305-311): exactly the 5 GET routes named above.
  `_COMMAND_ROUTES` (lines 551-554): exactly `/command/resolve-decision`
  and `/command/resolve-crash`. No stream route of any kind.
- `_handle_snapshot_events` (lines 262-302) is a bounded, paginated,
  historical query (`ORDER BY event_id DESC LIMIT ?+1`) — not a live
  stream, not a reconnect contract.
- Repo-wide search for `stream/events`, `text/event-stream`,
  `EventSource`, `last_seen_event`, `gap_fill`, `resync` across
  `services/` and `apps/` returns zero matches.
- No frontend file anywhere under `apps/atlas/src/` references
  `EventSource`, `useEventStream`, or `stream/events` — every existing
  component (`PacketThread`, `DecisionCard`, `History`,
  `PerformanceHeader`, etc.) is driven by static fixtures, not a
  network call.

**Design mockup** (`design_handoff_atlas/README.md`, lines 272-276 and
341-344; both reference `.dc.html` files):
- Desktop: *"`disconnected` — amber connection strip: 'Reconnecting',
  'Atlas lost its connection at 14:58. Agents keep working — they
  report to the Coordinator, not to this window. What you see below
  is the last state Atlas received.', right-side `retry 3 · 0:12`.
  Live indicator flips to amber `reconnecting`."*
- Mobile: same `systemState` prop; the strip's own copy differs by
  surface (see below).
- `Atlas Explorations.dc.html` (desktop): live indicator markup at
  line 25 (`{{ liveColor }}`/`{{ liveDot }}`/`{{ liveLabel }}`);
  connection strip at lines 29-35, positioned directly between
  `</header>` and the body grid; `renderVals()` (lines 724-762)
  computes `liveLabel`/`liveDot`/`liveColor`/`conn.*` from one
  `systemState` prop.
- `Atlas Mobile.dc.html` (mobile): connection strip markup at lines
  41-46, positioned directly between `<h1>Now</h1>` and the hero card;
  `renderVals()` (lines 566-567, 607-613) computes the equivalent
  mobile values — **different copy from desktop**: `"...not to this
  phone..."` / `"This is the last state received."` (vs. desktop's
  `"...not to this window..." / "What you see below is the last state
  Atlas received."`), and `meta: 'retry 3'` (vs. desktop's `'retry 3 ·
  0:12'`, no timer suffix on mobile).
- Every color the `disconnected` branch uses is a real, exact B2
  token, checked directly against `colors.ts`: `colors.warningWash`
  (`#FEF9F0`), `colors.warningBorder` (`#F1DEBE`), `colors.warningText`
  (`#8A5A08`), `colors.warning` (`#E0A32E`) — all four match exactly,
  zero disclosed literals needed for the strip's own state-dependent
  colors.

**Existing shell state** (both already-merged, both checked directly):
- `DesktopShell.tsx`'s own live indicator was already hardcoded to
  literal `"idle"` with `styles.liveDotIdle` — correct, since this app
  has no real live connection.
- `NowTab.tsx`'s own live indicator was hardcoded to literal `"live"`
  unconditionally, using `colors.accentLight` — **not honest**, since
  this app has exactly the same "no real connection" reality
  `DesktopShell.tsx` already correctly reflects. This is a real,
  pre-existing inconsistency this slice found and fixes (see Design
  rationale #1).

## Design rationale

1. **`deriveConnectionState(systemState, surface)` is the single
   source of truth for both the live indicator and the connection
   strip on both surfaces** — one function, matching this program's
   own C7 "one state value, not independently set fields" discipline.
   It deliberately renders `liveLabel: "idle"` for `systemState ===
   "normal"`, **not** the reference files' own default `"live"` — this
   app has no real live connection at all (no SSE, no polling), so
   claiming "live" would misrepresent a capability this build does not
   have, the same discipline already applied to D2/D6 (no fictional
   command option renders as real). This also fixes `NowTab.tsx`'s own
   pre-existing "live" inconsistency described above — both surfaces
   now agree.
2. **Every dynamic color (live dot/text, strip bg/border/ink/dot) is
   applied as a small per-render custom-property object (`connVars`),
   never a raw inline `style.color`/`style.background`.** A raw inline
   color/background value is silently re-serialized to `rgb(...)` by
   both real browsers and jsdom, which would break an exact-string
   test assertion against the original hex token — this mirrors the
   private `AgentCard` function's own already-established `cardVars`
   convention (`apps/atlas/src/agents/AgentsRoster.tsx`, not a
   separate `AgentCard.tsx` file — corrected per Decision Fidelity
   review) for per-item dynamic colors, applied here for per-render
   dynamic colors instead. (Self-caught during authoring, before any
   test was
   written against it — an early draft used raw inline color/
   background directly; fixed before writing tests, avoiding a defect
   class this program's own established convention already exists to
   prevent.)
3. **The strip's own fixed, non-state-dependent body-text color is a
   real per-surface value**, applied as an ordinary static
   `--atlas-conn-body` var (not part of `connVars`, since it never
   changes with `systemState`): `colors.inkSecondary` on desktop
   (`#6C6376`, an exact match), and a disclosed literal `#5C5468` on
   mobile (checked against every color family in `colors.ts`; no
   token matches — a real, different value from desktop's, not
   assumed equal to it).
4. **`SystemState` is typed as exactly `"normal" | "disconnected"`** —
   not the reference files' full `normal | crashed | disconnected |
   empty` enum. `crashed` (G2) and `empty` (G3) are separate, future
   slices with their own real dependencies; including their literal
   strings in this slice's own type would silently invite passing them
   before this function has any real branch for them.
5. **The connection strip is positioned exactly where each reference
   file places it**: `DesktopShell.tsx`, between the `<header>` and
   the body grid (matching `Atlas Explorations.dc.html`'s own markup
   order exactly); `NowTab.tsx`, between the `<h1>Now</h1>` and the
   hero card (matching `Atlas Mobile.dc.html`'s own markup order
   exactly) — checked directly against both reference files' real
   line ordering, not assumed.

## Guards

1. This slice adds exactly 2 new files
   (`apps/atlas/src/shell/connectionState.ts`,
   `connectionState.test.ts`) and modifies exactly 6 existing files
   (`DesktopShell.tsx`, `DesktopShell.module.css`,
   `DesktopShell.test.tsx`, `NowTab.tsx`, `NowTab.module.css`,
   `NowTab.test.tsx`) — no backend file, no other frontend file,
   touched.
2. `DesktopShell`'s and `NowTab`'s own `systemState` prop defaults to
   `"normal"` — every existing caller (`App.tsx`, `MobileShell.tsx`)
   is unaffected; no caller is updated to pass `"disconnected"`, since
   there is no real trigger for it yet (see Scope). The strip renders
   in the running app only when a caller explicitly passes
   `systemState="disconnected"` — which nothing does today. This is
   the same "real, tested, not yet wired to a live trigger" pattern
   already established for `CrashCard` (C6, real and tested, not
   mounted by any live `systemState` switch until G2's own future
   slice).
3. Every `--atlas-conn-*` custom property is consumed by at least one
   real CSS rule in both `DesktopShell.module.css` and
   `NowTab.module.css` — checked exhaustively (the specific class of
   defect an earlier Decision Fidelity review caught in F3's own first
   draft).
4. `DesktopShell.test.tsx`'s pre-existing exhaustive `SHELL_VARS` test
   is updated to remove the two vars this slice deleted
   (`--atlas-idle-grey`, `--atlas-idle-label`, now computed dynamically
   instead) and add the one it introduced (`--atlas-conn-body`) — still
   exhaustive, not spot-checked.
5. No test asserts a raw `.style.color`/`.style.background` value
   against a hex token — every color assertion uses
   `.style.getPropertyValue("--atlas-conn-*")`, per Design rationale
   #2.

## `apps/atlas/src/shell/connectionState.ts` (new)

```ts
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
```

## `apps/atlas/src/shell/connectionState.test.ts` (new)

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
});
```

## `apps/atlas/src/shell/DesktopShell.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import PacketThread from "../thread/PacketThread";
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
        <main className={styles.content}>
          {selected === "packet" ? <PacketThread /> : `${VIEW_LABEL[selected]} view`}
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
```

## `apps/atlas/src/shell/DesktopShell.test.tsx` (modified — full new content)

```tsx
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import DesktopShell from "./DesktopShell";

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
});
```

## `apps/atlas/src/shell/NowTab.tsx` (modified — full new content)

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily, radii, spacing } from "../tokens";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import { AGENT_STYLE } from "../agents/agentStyle";
import { OwnerDecisionCard } from "../decision/OwnerDecisionCard";
import { deriveConnectionState, type SystemState } from "./connectionState";
import styles from "./NowTab.module.css";

export interface NowTabProps {
  systemState?: SystemState;
}

/**
 * Hero-card colors from `Atlas Mobile.dc.html`'s real Now-tab markup
 * (lines 48-63 of the reference file), checked directly against
 * `colors.ts`. Real token matches: `colors.navGround` (card
 * background), `colors.navTextInactive`
 * (the progress track's fill — the mockup's own real blocked-branch
 * `barColor` is `#B7ADC1`, not `#A78BFF`; `#A78BFF` is that same
 * ternary's *non-blocked* branch, checked directly at
 * `Atlas Mobile.dc.html:687` — corrected by targeted correction, see
 * below), `colors.navActiveBg` (the progress track's own background,
 * `rgba(255,255,255,.13)` — an exact string match, also corrected by
 * targeted correction), `colors.inkFaint` (role text and boundary
 * timestamps — the same hex the mockup uses, `#A79BB4`), `colors.inkMuted`
 * (eyebrow label), and `colors.surface` (the meta-grid cards' white
 * background — the mockup's own `#fff`). The avatar bg/ink reuse the
 * real, already-reviewed `AGENT_STYLE.wait` pair from E4's
 * `agentStyle.ts` — Terra is genuinely idle/blocked in this real
 * trajectory, not running, so the "wait" style key is the honest
 * choice, not "run" (which E4's own Agents-roster fixture uses for a
 * different, later simulated moment of the same persona — not reused
 * here to avoid implying this hero card shows that same moment). The
 * same "blocked, not running" principle applies to the progress fill
 * color: an independent Decision Fidelity review found the first
 * draft picked the mockup's own *non-blocked* fill color here, which
 * directly contradicted this same principle already correctly applied
 * to the avatar — fixed to the real blocked-branch value.
 * Three values have no equivalent token and stay disclosed literals,
 * checked against every color family in `colors.ts`, not assumed: the
 * headline/name text (`#EDE8F1`), the subline text (`#C6BCD2`), the
 * "what happens next" panel's own body text color (`#3D3350`), and the
 * card's own 24px corner radius (`radii.mobileCardPx` only states an
 * 18-22px range; the reference file's own hero card is 24px, not
 * forced into the stated range). The hero card's own drop shadow
 * (`0 16px 34px rgba(30,20,45,.22)`, transcribed directly into
 * `NowTab.module.css`) is also a disclosed, unmatched literal — an
 * `rgba` shadow value, not a solid color, so it was not caught by the
 * hex-literal check above; noted here for completeness.
 *
 * The live indicator's own dot/text colors, and the connection strip
 * added below the page title, are no longer static here — they vary
 * by `systemState` (idle vs. reconnecting), computed per-render by
 * `deriveConnectionState` and applied as their own small per-render
 * custom-property object (`connVars`), matching
 * `DesktopShell.tsx`'s own identical convention (never a raw inline
 * `style.color`/`style.background`, which a real browser and jsdom
 * both silently re-serialize to `rgb(...)`, breaking an exact-string
 * test assertion). This slice also corrects a pre-existing
 * inconsistency: this file previously hardcoded the live-indicator
 * text to the literal `"live"` unconditionally, using
 * `colors.accentLight` for its dot — but this app has no real live
 * connection (no SSE stream, no polling) to honestly claim, unlike
 * `DesktopShell.tsx`'s own live indicator, which already correctly
 * said "idle". Both surfaces now read "idle"/"reconnecting" from the
 * same one function — see that function's own doc comment in
 * `connectionState.ts`.
 */
const SHELL_VARS = {
  "--atlas-hero-bg": colors.navGround,
  "--atlas-hero-ink": "#EDE8F1",
  "--atlas-hero-ink-muted": colors.inkFaint,
  "--atlas-hero-avatar-bg": AGENT_STYLE.wait.avBg,
  "--atlas-hero-avatar-ink": AGENT_STYLE.wait.avColor,
  "--atlas-hero-track": colors.navActiveBg,
  "--atlas-hero-fill": colors.navTextInactive,
  "--atlas-hero-radius": "24px",
  "--atlas-card-radius": `${radii.mobileCardPx.max}px`,
  "--atlas-gutter": `${spacing.mobileGutterPx}px`,
  "--atlas-eyebrow": colors.inkMuted,
  "--atlas-card-surface": colors.surface,
  // The connection strip's own body text color is a real, fixed value
  // (not state-dependent, unlike the strip's bg/border/ink/dot which
  // do vary by `systemState` and are applied inline). `Atlas
  // Mobile.dc.html`'s own real `conn.body` color is `#5C5468` — checked
  // directly against every family in `colors.ts` and matches no real
  // token (desktop's own equivalent, `#6C6376`, IS `colors.inkSecondary`
  // — a real but different value, not assumed equal to mobile's). This
  // stays a disclosed literal.
  "--atlas-conn-body": "#5C5468",
  "--atlas-subline": "#C6BCD2",
  "--atlas-next-text": "#3D3350",
  "--atlas-owner-bg": colors.warningWash,
  "--atlas-owner-ink": colors.warningText,
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-body": fontFamily.body,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

/**
 * Mobile "Now" tab — the single-state-source hero card, boundary
 * timestamps, meta grid, real escalation decision (reusing C4's
 * `OwnerDecisionCard` verbatim per the roadmap's own Wave F rule —
 * "reuse Wave C/E logic; no new backend"), and "what happens next"
 * panel, all read from one `derivePacketHeaderState` call. No Stop/
 * Start or "Open conversation" affordance is rendered — those need
 * their own guarded backend commands (per this roadmap's own M0-D01
 * amendment: "a command is available through Atlas only once its own
 * guarded command exists and passes review"), none of which exist yet;
 * adding inert-but-visible buttons for actions with no real backend at
 * all (unlike D2/D3's already-real resolve-decision command) would
 * misrepresent capability this build does not have.
 */
export function NowTab({ systemState = "normal" }: NowTabProps = {}) {
  const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
  const progressWidth =
    state.progressPercent === "unavailable" ? "0%" : `${state.progressPercent}%`;
  const conn = deriveConnectionState(systemState, "mobile");
  const connVars = {
    "--atlas-conn-live-dot": conn.liveDotColor,
    "--atlas-conn-live-text": conn.liveTextColor,
    "--atlas-conn-strip-bg": conn.strip.bg,
    "--atlas-conn-strip-border": conn.strip.border,
    "--atlas-conn-strip-ink": conn.strip.ink,
    "--atlas-conn-strip-dot": conn.strip.dot,
  } as CSSProperties;

  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.eyebrowRow}>
        <span className={styles.eyebrow}>{state.eyebrow}</span>
        <span className={styles.live} style={connVars}>
          <span className={styles.liveDot} aria-hidden="true" />
          {conn.liveLabel}
        </span>
      </div>
      <h1 className={styles.pageTitle}>Now</h1>

      {conn.strip.show ? (
        <div className={styles.connectionStrip} style={connVars}>
          <div className={styles.connectionTitleRow}>
            <span className={styles.connectionDot} />
            {conn.strip.title}
            <span className={styles.connectionMeta}>{conn.strip.meta}</span>
          </div>
          <div className={styles.connectionBody}>{conn.strip.body}</div>
        </div>
      ) : null}

      <div className={styles.hero}>
        <div className={styles.heroHead}>
          <span className={styles.avatar} aria-hidden="true">
            TE
          </span>
          <div className={styles.identity}>
            <div className={styles.name}>Terra</div>
            <div className={styles.role}>Implementor · A.2 Runtime Package</div>
          </div>
        </div>
        <div className={styles.headline}>{state.headline}</div>
        <div className={styles.subline}>{state.subline}</div>

        <div className={styles.progressBlock}>
          <div className={styles.track}>
            <span className={styles.fill} style={{ width: progressWidth }} />
          </div>
          <div className={styles.boundaryRow}>
            <span>
              {state.boundaryBegin === "unavailable"
                ? "unavailable"
                : `began ${state.boundaryBegin}`}
            </span>
            <span>
              {state.boundaryHeld === "unavailable"
                ? "unavailable"
                : `held at ${state.boundaryHeld}`}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.metaGrid}>
        <div className={styles.metaCard}>
          <div className={styles.metaLabel}>Last report</div>
          <div className={styles.metaValue}>{state.lastReport}</div>
        </div>
        <div className={styles.metaCard}>
          <div className={styles.metaLabel}>Blocker</div>
          <div className={styles.metaValue}>{state.blocker}</div>
        </div>
      </div>

      {state.isBlocked ? <OwnerDecisionCard /> : null}

      <div className={styles.nextPanel}>
        <div className={styles.nextHeading}>{state.nextPanelHeading}</div>
        <p className={styles.nextText}>{state.nextPanelText}</p>
      </div>
    </div>
  );
}

export default NowTab;
```

## `apps/atlas/src/shell/NowTab.module.css` (modified — full new content)

```css
.tab {
  padding: 8px var(--atlas-gutter) 22px;
  font-family: var(--atlas-font-body);
}

.eyebrowRow {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 4px 0 2px;
}

.eyebrow {
  font: 600 11px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-eyebrow);
}

.live {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--atlas-conn-live-text);
  font-size: 12px;
}

.liveDot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--atlas-conn-live-dot);
}

.connectionStrip {
  margin: 0 0 12px;
  padding: 13px 15px;
  border-radius: 18px;
  background: var(--atlas-conn-strip-bg);
  border: 1px solid var(--atlas-conn-strip-border);
}

.connectionTitleRow {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--atlas-conn-strip-ink);
  font-size: 13.5px;
  font-weight: 700;
}

.connectionDot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--atlas-conn-strip-dot);
}

.connectionMeta {
  margin-left: auto;
  font: 500 11px var(--atlas-font-mono);
  color: var(--atlas-eyebrow);
}

.connectionBody {
  margin-top: 5px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--atlas-conn-body);
}

.pageTitle {
  margin: 6px 0 16px;
  font-family: var(--atlas-font-display);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.hero {
  padding: 20px;
  border-radius: var(--atlas-hero-radius);
  background: var(--atlas-hero-bg);
  color: var(--atlas-hero-ink);
  box-shadow: 0 16px 34px rgba(30, 20, 45, 0.22);
}

.heroHead {
  display: flex;
  align-items: center;
  gap: 11px;
}

.avatar {
  width: 36px;
  height: 36px;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--atlas-hero-avatar-bg);
  color: var(--atlas-hero-avatar-ink);
  font: 600 12px var(--atlas-font-mono);
}

.identity {
  min-width: 0;
  flex: 1;
}

.name {
  font-size: 15px;
  font-weight: 700;
}

.role {
  font-size: 12.5px;
  color: var(--atlas-hero-ink-muted);
}

.headline {
  font-family: var(--atlas-font-display);
  font-size: 27px;
  font-weight: 600;
  letter-spacing: -0.025em;
  margin-top: 16px;
}

.subline {
  font-size: 13.5px;
  color: var(--atlas-subline);
  margin-top: 3px;
}

.progressBlock {
  margin-top: 18px;
}

.track {
  position: relative;
  height: 6px;
  border-radius: 999px;
  background: var(--atlas-hero-track);
}

.fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  border-radius: 999px;
  background: var(--atlas-hero-fill);
}

.boundaryRow {
  display: flex;
  justify-content: space-between;
  margin-top: 9px;
  font: 500 11.5px var(--atlas-font-mono);
  color: var(--atlas-hero-ink-muted);
}

.metaGrid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 12px;
}

.metaCard {
  padding: 15px 16px;
  border-radius: var(--atlas-card-radius);
  background: var(--atlas-card-surface);
}

.metaLabel {
  font-size: 12px;
  color: var(--atlas-eyebrow);
}

.metaValue {
  font-size: 19px;
  font-weight: 600;
  font-family: var(--atlas-font-mono);
  margin-top: 2px;
}

.nextPanel {
  margin-top: 12px;
  padding: 16px;
  border-radius: var(--atlas-card-radius);
  background: var(--atlas-owner-bg);
}

.nextHeading {
  font: 600 11px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-owner-ink);
}

.nextText {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: var(--atlas-next-text);
}
```

## `apps/atlas/src/shell/NowTab.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NowTab } from "./NowTab";
import { derivePacketHeaderState } from "../thread/headerState";
import { PACKET_A2_ENTRIES } from "../thread/fixtures";
import { colors } from "../tokens";

afterEach(cleanup);

describe("NowTab", () => {
  it("renders the real hero card identity, headline, and subline, all from one derived state object", () => {
    const { container } = render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    // Scoped to the hero card: the reused OwnerDecisionCard below it also
    // renders "Terra" (its own real chain-of-escalation chip).
    const hero = container.querySelector('[class*="hero"]') as HTMLElement;
    expect(within(hero).getByText("Terra")).toBeInTheDocument();
    expect(within(hero).getByText("Implementor · A.2 Runtime Package")).toBeInTheDocument();
    // Hardcoded literals, not just cross-checked against the function's own
    // live return value — a wording regression inside
    // derivePacketHeaderState itself must still fail this test.
    expect(state.headline).toBe("Blocked");
    expect(state.subline).toBe("Escalated to you · worktree held");
    expect(within(hero).getByText(state.headline)).toBeInTheDocument();
    expect(within(hero).getByText(state.subline)).toBeInTheDocument();
  });

  it("renders the real 40% progress fill width, derived from the real fixture's plan steps", () => {
    const { container } = render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(state.progressPercent).toBe(40);
    const fill = container.querySelector('[class*="fill"]') as HTMLElement;
    expect(fill.style.width).toBe("40%");
  });

  it("renders the real boundary timestamps", () => {
    render(<NowTab />);
    expect(screen.getByText("began 13:51")).toBeInTheDocument();
    expect(screen.getByText("held at 14:52")).toBeInTheDocument();
  });

  it("renders the meta grid's Last report and Blocker, consistent with the derived state", () => {
    render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    expect(screen.getByText("Last report")).toBeInTheDocument();
    expect(screen.getByText(state.lastReport)).toBeInTheDocument();
    expect(screen.getByText("Blocker")).toBeInTheDocument();
    expect(screen.getByText(state.blocker)).toBeInTheDocument();
  });

  it("renders the real owner-decision card (C4, reused verbatim) because this real trajectory is blocked", () => {
    render(<NowTab />);
    expect(
      screen.getByText(
        "Should a theme-free output get a sentinel version, or does the frozen contract change?",
      ),
    ).toBeInTheDocument();
  });

  it("renders the 'what happens next' panel with the real derived text", () => {
    render(<NowTab />);
    const state = derivePacketHeaderState(PACKET_A2_ENTRIES);
    // Hardcoded literal, not just cross-checked against the function's own
    // live return value — a wording regression inside
    // derivePacketHeaderState itself must still fail this test.
    expect(state.nextPanelText).toBe(
      "Nothing is expected from Terra until you answer — its worktree stays held while the packet is blocked.",
    );
    expect(screen.getByText("what happens next")).toBeInTheDocument();
    expect(screen.getByText(state.nextPanelText)).toBeInTheDocument();
  });

  it("renders no Stop/Start or Open-conversation control (no real backend command exists for them yet)", () => {
    render(<NowTab />);
    expect(screen.queryByRole("button", { name: /stop/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /start/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /open conversation/i })).toBeNull();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<NowTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });

  it("defaults to systemState 'normal': live indicator says 'idle', not the reference file's own default 'live' (this app has no real connection), no connection strip", () => {
    render(<NowTab />);
    const live = screen.getByText("idle").closest('[class*="live"]') as HTMLElement;
    expect(live.style.getPropertyValue("--atlas-conn-live-text")).toBe(colors.inkFaint);
    expect(live.style.getPropertyValue("--atlas-conn-live-dot")).toBe(colors.inkMuted);
    expect(screen.queryByText("Reconnecting")).toBeNull();
  });

  it("systemState 'disconnected': live indicator flips to 'reconnecting' and the real mobile connection strip renders with its own real copy (different from desktop's)", () => {
    render(<NowTab systemState="disconnected" />);
    expect(screen.getByText("reconnecting")).toBeInTheDocument();
    expect(screen.getByText("Reconnecting")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Atlas lost its connection at 14:58. Agents keep working — they report to the Coordinator, not to this phone. This is the last state received.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("retry 3")).toBeInTheDocument();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to this
scratch worktree (`/tmp/maestro-m2-g1-disconnected`, branch
`architecture/m2-g1-disconnected`, base `a72ab45`) and run through the
real frontend toolchain from `apps/atlas` (`npm install`, then each
script below), before this packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **22/22 test files, 165/165 tests
  passed** (4 new in `connectionState.test.ts`; `DesktopShell.test.tsx`
  went from 10 to 12 tests, `NowTab.test.tsx` from 8 to 10; zero
  regressions in the other 18 files).
- `npm run build` (`vite build`) — clean, `39 modules transformed`, no
  warnings.

One issue was self-caught during authoring, before any test was
written against it: an early draft applied the live indicator's and
connection strip's dynamic colors as raw inline `style.color`/
`style.background` — fixed to the `connVars` custom-property
convention (Design rationale #2) before writing any test, since a raw
inline color value is silently re-serialized by both real browsers and
jsdom, which would have broken an exact-string color assertion.

**Independent Decision Fidelity review result:** `PASS WITH
NON-BLOCKING NOTES`, zero blocking findings. The review independently
re-derived every material claim from source — re-reading
`read_api.py`'s exact route tables, re-grepping the whole repo for any
SSE/stream consumer, re-reading both `.dc.html` reference files'
exact line ranges, re-checking every single hex literal in
`colors.ts`, confirming the pre-existing `NowTab.tsx`/`DesktopShell.tsx`
inconsistency via `git show` on the base commit, and independently
re-applying this packet's exact proposed files and re-running the full
toolchain (typecheck/lint/test/build), all reproducing the numbers
above exactly — and found three citation/evidence-framing
inaccuracies, none affecting code correctness, test validity, or the
underlying scope decision, all fixed before freeze at zero cost, no
planning correction consumed:

1. **Misquote of the status doc.** This packet's Scope section quoted
   `docs/planning/maestro-development-status.md`'s C2 deferral
   paragraph as *"Wave A execution stopped at A5 ... A6/A7 were never
   built"* — the real text reads `(Wave A stopped at A5; A6/A7 were
   never built)`, no "execution," different punctuation. Fixed to the
   exact quote.
2. **Overstated "same real gap" framing.** This packet originally
   claimed A6/A7's non-existence is "the same real gap already
   identified and recorded as the reason C2/D3/D7 are rescheduled to
   M3." Re-reading the actual D3 and D7 paragraphs: both were
   rescheduled because specific fixture data
   (`OwnerDecisionCard`'s/`CrashCard`'s `packet_id`) has no matching
   real backend row — a data-availability mismatch, not specifically
   the missing SSE/reconnect machinery (which C2's own paragraph names
   as only part of a "more fundamental" cause). Fixed to describe both
   as real, related backend-immaturity gaps in the same M3-target
   family, not one identical finding — A6/A7's own non-existence
   remains independently sufficient justification for this slice's
   scope regardless.
3. **Nonexistent file cited twice.** Design rationale #2 and the
   `DesktopShell.tsx` `SHELL_VARS` doc comment both cited
   "`AgentCard.tsx`'s own already-established `cardVars` convention" —
   no file named `AgentCard.tsx` exists. `cardVars` is real, but lives
   in a private, unexported `AgentCard` function inside
   `apps/atlas/src/agents/AgentsRoster.tsx`. Fixed both citations to
   name the real file. Re-verified after all three fixes: still
   22/22 test files, 165/165 tests, clean typecheck/lint/build.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** the desktop and mobile shells both render a
   real, tested connection strip and live indicator that flip
   correctly given `systemState="disconnected"`, with zero regression
   to any of the 20 existing test files.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** wiring `systemState` to any real trigger —
   this requires A6 (SSE event stream) and A7 (reconnect/resync
   contract), neither of which exists; both are rescheduled to M3
   alongside C2/D3/D7, the same real missing dependency. `crashed` (G2)
   and `empty` (G3) states are separate, future slices — this slice's
   own `SystemState` type does not even admit those literal strings.
4. **Assurance level:** practical correctness for a fixture/prop-driven
   presentational component — every rendered surface and every state
   transition is exercised by a direct-prop React Testing Library
   render test and a pure-function unit test; no browser-based visual
   verification was performed (tooling failure, already disclosed in
   this session for M2-E4/F1/F2/F3, same root cause). Because no
   caller passes `systemState="disconnected"` today, the strip never
   renders in the actual running app yet — only under direct test
   invocation — an intentional, disclosed limitation matching the
   "real, tested, not yet live-wired" pattern already established for
   `CrashCard` (C6).
5. **Acceptance proof:** 22/22 test files, 165/165 tests passing (zero
   regressions), clean typecheck, clean lint, clean production build.
6. **Implementation boundary:** 2 new files, 6 modified files, all
   within `apps/atlas/src/shell`; zero backend files; no new
   third-party dependency.
7. **Proportionality ceiling:** one new pure-derivation module
   (`connectionState.ts`) and its own prop threaded through two
   already-real shell components — no new fixture data invented, no
   new design tokens invented beyond one disclosed, checked literal
   (mobile's own `#5C5468` body-text color).
8. **Stop and escalation rule:** wiring any real trigger for
   `systemState`, or building the `crashed`/`empty` branches, is
   explicitly out of scope — G2/G3 and the M3 A6/A7 rescheduling are
   separate, already-recorded future work, not this slice's job to
   silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-G1-DISCONNECTED-STATE-01` |
| `phase` | `MergeReady` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `0` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-g1-disconnected-state.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
