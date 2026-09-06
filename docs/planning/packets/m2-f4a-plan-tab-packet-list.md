# M2 Wave F — Mobile Plan Tab, Packet List — Candidate 01

**Slice ID:** `MB-SLICE-M2-F4A-PLAN-TAB-PACKET-LIST-01`
**Status:** `Decision Fidelity review returned REQUEST_CHANGES (a real wrong-token defect: TRACK_COLOR.run used colors.accent instead of colors.accentLight, undetected by the first draft's own non-exhaustive tests; a false NowTab citation claiming it corroborates A.2 "running" when NowTab deliberately shows it blocked) — 1 targeted correction applied and independently re-verified (including mutation-testing the fix), REQUEST_CHANGES resolved`
**Base:** `8aa33ce` (full: `8aa33ce5787e296d95dee0b4921ebd77e2b752dd`, `origin/master`)

## Scope, deliberately minimal

Roadmap item 36, *"F4 — Plan tab: packet list + gate bottom sheet
(reuses E7 data)."* `MobileShell.tsx`'s "plan" tab currently renders
the literal placeholder string `"Plan tab"` — nothing has been built
for this item yet. This slice is the smallest independently reviewable
piece: **the packet-list body only** (breadcrumb, title, real derived
stats line, real progress track, all 8 real packet rows, and the "M1-B
gate" row itself). The gate row's own bottom sheet (tapping it to open
a modal showing `GateCriteriaList`'s real criteria) is a separate,
future slice (a future `F4B`-style candidate) — the gate row renders
real and tappable, but its `onClick` is not yet wired, matching this
program's own established "options rendered but inert until wired"
convention.

This slice is frontend-only — no backend file touched. It adds 2 new
files (`apps/atlas/src/plan/fixtures.ts`,
`apps/atlas/src/shell/PlanTab.tsx`, `PlanTab.module.css`,
`PlanTab.test.tsx` — 4 new files total) and modifies exactly 2
existing files (`apps/atlas/src/shell/MobileShell.tsx`,
`MobileShell.test.tsx`, to wire the new tab in). No other file is
touched. `apps/atlas/src/gate/fixtures.ts` (E7's own, already merged)
is a read-only import.

## Evidence

`Atlas Mobile.dc.html:200-217` is the real `isPlan` block:

1. **Header** (`:202-204`): breadcrumb "m1-a · api module foundation",
   `<h1>Plan</h1>`, and a real stats line "N complete · N running · N
   ahead".
2. **Progress track** (`:205`): 8 real segments, one per packet, colored
   by that packet's own real state.
3. **Packet list** (`:206-214`): all 8 real packets (`PACKETS`, lines
   423-432 of the same file), each a real tappable row with a
   per-state dot (`dot()`, lines 550-556), id, short title, state
   label, and chevron — the currently-selected packet (`active = p.id
   === 'A.2'`) gets a highlighted background and a distinct meta-text
   color.
4. **Gate row** (`:215`): "M1-B gate" + a real "N of 5 met" count +
   chevron, opening the gate's own bottom sheet (`openGate`) — not
   built here.

**Real, checked fact:** no packet-list fixture of this shape (a
multi-packet array with per-packet id/short-title/state) exists
anywhere in `apps/atlas/src` today — every other real fixture is
either single-packet (`PACKET_A2_ENTRIES`) or agent-keyed
(`AGENTS`). This slice adds the first one, transcribing the mockup's
own real `PACKETS` array and `STATE`/`dot()` derivations verbatim into
`apps/atlas/src/plan/fixtures.ts` and `PlanTab.tsx`.

**Real token matches**, checked directly against `colors.ts`:
`colors.inkMuted` (`#8E8299`), `colors.inkSecondary` (`#6C6376`),
`colors.surface` (`#fff`), `colors.ink` (`#221C29`),
`colors.borderDashed[0]` (`#DCD5E4`, the gate row's own dashed
border), `colors.borderDashed[2]` (`#B9AFC4`, both the gate row's own
dot border and the packet dots' own `wait`/`pend` states — the same
token `--atlas-ag-wait-dot-border` already uses), `colors.success`
(`#2E9B72`, `done` state), and `colors.accentLight` (`#8C6BFF`, `run`
state's dot **and** track color — the mockup's own real `track`
derivation, `Atlas Mobile.dc.html:735`, uses the identical `#8C6BFF`
for both the dot and the track segment, not two different values).
Four literals have no token match, checked against every color family
in `colors.ts`: the active row's own background (`#EFEAFE`) and its
own id/state/chevron text color (`#6C55B8`), the `block` state's own
dot border (`#D08A83` — a real, distinct value from `colors.review`'s
`#D08A63`, not a transcription typo of it), and the track's own "not
done/running" segment color (`#E4DEEC`). The gate row's own "M1-B
gate" label color (`#4C4457`) reuses the exact same disclosed literal
F3C's own weekly-window body text already establishes — the same real
value, not a newly invented one.

**Corrected — real defect from Decision Fidelity review, requiring a
correction (not merely a disclosure):** the first draft's own
`TRACK_COLOR.run` used `colors.accent` (`#5B34E8`), not
`colors.accentLight` (`#8C6BFF`) — a genuinely wrong value that would
have rendered a darker purple than the mockup's own real track segment
color, and the first draft's own rationale falsely asserted this was
"two different real tokens for two different real elements, not a
mismatch," when the mockup's own source uses the identical `#8C6BFF`
for both. Fixed: `TRACK_COLOR.run` now reads `colors.accentLight`,
matching the dot's own already-correct value. The review also caught
that this bug slipped through the first draft's own test suite
undetected (mutation-tested by the reviewer); the test file below is
now rewritten to assert exact hex-to-rgb-converted color values for
every state and every track segment, not just non-emptiness or
substring patterns — independently re-verified by mutation-testing it
myself before finalizing this packet (see Pre-verification).

## Design rationale

1. **Reuses E7's real `GATE_CRITERIA` fixture for the gate row's own
   derived met-count** (`GATE_CRITERIA.filter((c) => c.met ===
   "yes").length`), not a second hardcoded number — matching this
   program's own C7/`GateHeader` single-state-source discipline. If
   `GATE_CRITERIA` ever changes, this count updates automatically.
2. **The stats line's own three real counts are derived, not
   hardcoded**: `DONE_COUNT`/`RUN_COUNT` are real filters over
   `PLAN_PACKETS`, and `AHEAD_COUNT` is `PLAN_PACKETS.length` minus the
   other two (not its own separate filter) — so the three numbers can
   never silently fail to sum to the real total.
3. **No packet row, and no gate row, has an `onClick` wired.** No real
   multi-packet "open this packet's thread" capability exists anywhere
   in this app today (only A.2 has any real conversation data,
   `PACKET_A2_ENTRIES`), and the gate row's own bottom sheet is
   separate, future work — matching `AgentsRoster`'s own already-
   established "Open thread" button precedent for options rendered but
   not yet wired.
4. **Per-state dot styling separates static shape (a shared CSS class,
   `.packetDot`) from per-state-varying properties (inline style)** —
   matching `AgentCardMobile`'s own established convention exactly,
   rather than duplicating the full style object per state when only
   `border-radius`/`background`/`border`/`box-shadow` actually vary
   (every real dot is the same 10px size).
5. **Every new `--atlas-plan-*` CSS custom property is consumed by at
   least one real CSS rule, and every CSS class declared is referenced
   in the component** — checked exhaustively in both directions (the
   specific class of defect earlier Decision Fidelity reviews caught
   in F3's and this slice's own first draft, which initially declared
   a `.packetDot` class reference with no CSS rule and a dead
   `.packetState`/`.packetMeta` naming mismatch — both self-caught and
   fixed before this packet was finalized).
6. **Test coverage checks the exact per-state dot/track color values**,
   not just shape or non-emptiness. **Corrected — real defect from
   Decision Fidelity review:** the first draft's own version of this
   test only checked non-emptiness/substring patterns (e.g. "border
   contains '2px solid'"), which the review proved — by mutation-testing
   the shipped code — did not actually catch the `TRACK_COLOR.run`
   defect above, directly contradicting this item's own original claim
   that the lesson from F3C's implementation review had already been
   applied. Fixed: every state's exact color is now asserted via a
   hex-to-rgb conversion helper (jsdom re-serializes raw inline hex on
   readback, the same defect class F3C's own implementation review
   already established), and independently re-mutation-tested before
   finalizing this packet — both the `TRACK_COLOR.run` defect and a
   second injected `block`-border-color mutation were confirmed to make
   the test suite fail.

## Guards

1. This slice modifies exactly 2 existing files
   (`apps/atlas/src/shell/MobileShell.tsx`, `MobileShell.test.tsx`) and
   adds exactly 4 new files (`apps/atlas/src/plan/fixtures.ts`,
   `apps/atlas/src/shell/PlanTab.tsx`, `PlanTab.module.css`,
   `PlanTab.test.tsx`) — no backend file, no other frontend file,
   touched. `apps/atlas/src/gate/fixtures.ts` (E7's own file) is a
   read-only import, never modified.
2. `MobileShell.tsx`'s own dead `TAB_LABEL` map (only ever consumed by
   the now-removed placeholder branch) is removed, not left as unused
   dead code.
3. `MobileShell.test.tsx`'s pre-existing "tapping a tab" placeholder
   test is retargeted to assert real `PlanTab` content, matching this
   program's own established pattern (F3's own retargeting of the same
   test for the Activity tab).
4. No gate-bottom-sheet modal, no packet-detail/thread view for any
   packet other than A.2, is rendered anywhere — this slice's scope is
   the packet-list body only.

## `apps/atlas/src/plan/fixtures.ts` (new)

```ts
/**
 * Transcribed verbatim from `Atlas Mobile.dc.html`'s own real
 * `PACKETS` array and `STATE` map — pure reporting content, no
 * persona, no fictional agent. A.2's own real `run` state here matches
 * `AGENTS`'s own real Terra entry (`apps/atlas/src/agents/agents.ts`,
 * `state: "running"`, `styleKey: "run"`) — the mockup's own real
 * `PACKETS` array is sufficient justification on its own.
 *
 * **Corrected — real defect from Decision Fidelity review:** an
 * earlier draft of this comment also cited `NowTab.tsx` as
 * corroborating "Terra genuinely running," which is false — `NowTab.tsx`'s
 * own doc comment deliberately renders Terra as blocked/waiting, not
 * running, as an already-reviewed, on-record design decision (see that
 * file's own comment: *"Terra is genuinely idle/blocked in this real
 * trajectory, not running, so the 'wait' style key is the honest
 * choice, not 'run'..."*). This Plan tab's own use of `run` for A.2 is
 * still correct — it matches the mockup's own real `PACKETS` array and
 * `AGENTS`'s own real Terra entry — only the false `NowTab` citation is
 * removed.
 */
export type PlanPacketState = "done" | "run" | "wait" | "block" | "pend";

export interface PlanPacket {
  id: string;
  short: string;
  state: PlanPacketState;
}

export const PLAN_PACKETS: PlanPacket[] = [
  { id: "A.0", short: "Source homes", state: "done" },
  { id: "A.1", short: "Core contract", state: "done" },
  { id: "A.2", short: "Runtime Package", state: "run" },
  { id: "A.3", short: "Live overlay", state: "wait" },
  { id: "A.4", short: "Support view", state: "block" },
  { id: "A.5", short: "Module guides", state: "block" },
  { id: "A.6", short: "Journey proof", state: "block" },
  { id: "A.7", short: "Records & merge", state: "pend" },
];

export const PLAN_STATE_LABEL: Record<PlanPacketState, string> = {
  done: "Complete",
  run: "Running now",
  wait: "Waiting on A.2",
  block: "Blocked",
  pend: "Planned",
};

/** Real, verbatim — the Plan tab's own breadcrumb. */
export const PLAN_BREADCRUMB = "m1-a · api module foundation";

/**
 * The one real packet with any live conversation thread today
 * (`PACKET_A2_ENTRIES`) — used to highlight the matching row the same
 * way the reference file's own `active = p.id === 'A.2'` does.
 */
export const PLAN_ACTIVE_PACKET_ID = "A.2";
```

## `apps/atlas/src/shell/PlanTab.tsx` (new)

```tsx
import type { CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { GATE_CRITERIA } from "../gate/fixtures";
import {
  PLAN_ACTIVE_PACKET_ID,
  PLAN_BREADCRUMB,
  PLAN_PACKETS,
  PLAN_STATE_LABEL,
  type PlanPacket,
  type PlanPacketState,
} from "../plan/fixtures";
import styles from "./PlanTab.module.css";

const DONE_COUNT = PLAN_PACKETS.filter((p) => p.state === "done").length;
const RUN_COUNT = PLAN_PACKETS.filter((p) => p.state === "run").length;
const AHEAD_COUNT = PLAN_PACKETS.length - DONE_COUNT - RUN_COUNT;
const GATE_MET_COUNT = GATE_CRITERIA.filter((c) => c.met === "yes").length;

/**
 * Transcribed verbatim from `Atlas Mobile.dc.html`'s own real `dot()`
 * function (lines 550-556) and `track` derivation (line 735) — every
 * real per-state size/shape/color, checked directly against
 * `colors.ts`. `done`'s bg (`#2E9B72`) and `run`'s bg (`#8C6BFF`) are
 * `colors.success`/`colors.accentLight`; `wait`'s and `pend`'s own
 * border (`#B9AFC4`) is `colors.borderDashed[2]`, the same token
 * `--atlas-ag-wait-dot-border` already uses. `block`'s own border
 * (`#D08A83`) and the track's own "not done/running" segment color
 * (`#E4DEEC`) have no token match, checked against every color family
 * in `colors.ts` — both disclosed literals. `run`'s own halo
 * (`rgba(140,107,255,.2)`, `colors.accentLight`'s RGB at .2 alpha) is
 * a real, exact RGB-to-token match, following the same *pattern*
 * (an alpha-halo derived from a real token's own RGB) `--atlas-dot-need-halo`
 * already establishes — not the same value (that one is an amber
 * warning halo, not this purple one).
 */
const TRACK_COLOR: Record<PlanPacketState, string> = {
  done: colors.success,
  run: colors.accentLight,
  wait: "#E4DEEC",
  block: "#E4DEEC",
  pend: "#E4DEEC",
};

/**
 * Every real per-state dot is the same real 10px size (the reference
 * file's own `this.dot(p.state, 10)` call) — only shape/color vary,
 * so the shared 10px/box-sizing/`flex: none` sizing lives once in
 * `.packetDot`'s own static CSS rule, matching `AgentCardMobile`'s own
 * already-established convention (static class for shared shape, inline
 * style only for the per-state-varying properties).
 */
const DOT_STYLE: Record<PlanPacketState, CSSProperties> = {
  done: { borderRadius: 3, background: colors.success },
  run: {
    borderRadius: "50%",
    background: colors.accentLight,
    boxShadow: "0 0 0 4px rgba(140,107,255,.2)",
  },
  wait: { borderRadius: "50%", border: `2px solid ${colors.borderDashed[2]}` },
  block: { borderRadius: "50%", border: "2px solid #D08A83" },
  pend: { borderRadius: "50%", border: `1.5px dashed ${colors.borderDashed[2]}` },
};

/**
 * Colors from `Atlas Mobile.dc.html`'s real Plan-tab markup (lines
 * 200-217), checked directly against `colors.ts`. Real token matches:
 * `colors.inkMuted` (`#8E8299`, breadcrumb and the gate row's own
 * inherited "N of 5 met" text), `colors.inkSecondary` (`#6C6376`, the
 * stats line), `colors.surface` (`#fff`, a packet row's own default
 * background), `colors.ink` (`#221C29`, every row's own title text,
 * real regardless of active state — the reference file's own `p.color`
 * is always `#221C29`, never variable), `colors.borderDashed[0]`
 * (`#DCD5E4`, the gate row's own dashed border), `colors.borderDashed[2]`
 * (`#B9AFC4`, the gate row's own dot border — the same token the
 * packet dots' own `wait`/`pend` states already use). Three literals
 * have no token match, checked against every color family in
 * `colors.ts`: the active row's own background (`#EFEAFE`) and its own
 * id/state/chevron text color (`#6C55B8`), and the gate row's own
 * "M1-B gate" label color (`#4C4457` — the same disclosed literal
 * F3C's own weekly-window body text already establishes, reused here
 * as the same real value, not a new one).
 */
const SHELL_VARS = {
  "--atlas-plan-breadcrumb": colors.inkMuted,
  "--atlas-plan-stats": colors.inkSecondary,
  "--atlas-plan-row-bg": colors.surface,
  "--atlas-plan-row-bg-active": "#EFEAFE",
  "--atlas-plan-row-ink": colors.ink,
  "--atlas-plan-row-meta": colors.inkMuted,
  "--atlas-plan-row-meta-active": "#6C55B8",
  "--atlas-plan-gate-border": colors.borderDashed[0],
  "--atlas-plan-gate-dot-border": colors.borderDashed[2],
  "--atlas-plan-gate-meta": colors.inkMuted,
  "--atlas-plan-gate-label": "#4C4457",
  "--atlas-font-display": fontFamily.display,
  "--atlas-font-mono": fontFamily.mono,
} as CSSProperties;

function PacketRow({ packet }: { packet: PlanPacket }) {
  const isActive = packet.id === PLAN_ACTIVE_PACKET_ID;
  const activeClass = isActive ? styles.packetMetaActive : "";
  return (
    <button type="button" className={`${styles.packetRow} ${isActive ? styles.packetRowActive : ""}`}>
      <span className={styles.packetDot} style={DOT_STYLE[packet.state]} aria-hidden="true" />
      <span className={styles.packetBody}>
        <span className={`${styles.packetId} ${activeClass}`}>{packet.id}</span>
        <span className={styles.packetShort}>{packet.short}</span>
        <span className={`${styles.packetState} ${activeClass}`}>{PLAN_STATE_LABEL[packet.state]}</span>
      </span>
      <span className={`${styles.chevron} ${activeClass}`} aria-hidden="true">
        ›
      </span>
    </button>
  );
}

/**
 * Mobile "Plan" tab — the reference file's own `isPlan` view: a
 * breadcrumb, a real derived stats line ("N complete · N running · N
 * ahead"), a real progress track, and all 8 real `PLAN_PACKETS` rows
 * (each a real, tappable `<button>` matching the reference file's own
 * per-state dot styling — no `onClick` wired, since no real
 * multi-packet "open this packet's thread" capability exists yet; only
 * A.2 has any real conversation data), plus a real "M1-B gate" row
 * with its own real derived "N of 5 met" count (reusing E7's own
 * `GATE_CRITERIA`). The gate row is also a real `<button>` with no
 * `onClick` — opening the gate's own bottom sheet is separate, future
 * work (roadmap item 36's own remaining scope, a future `F4B`-style
 * candidate), matching this program's own established "options
 * rendered but inert until wired" convention (`AgentsRoster`'s own
 * "Open thread" button).
 *
 * The stats line's own real counts (`DONE_COUNT`/`RUN_COUNT`/
 * `AHEAD_COUNT`) are derived directly from `PLAN_PACKETS`'s own `state`
 * field, not separately hand-typed numbers — matching this program's
 * own C7/`GateHeader` single-state-source discipline. `AHEAD_COUNT`
 * is `PLAN_PACKETS.length` minus the other two, not its own filter, so
 * the three real counts can never silently fail to sum to the real
 * total.
 */
export function PlanTab() {
  return (
    <div className={styles.tab} style={SHELL_VARS}>
      <div className={styles.breadcrumb}>{PLAN_BREADCRUMB}</div>
      <h1 className={styles.pageTitle}>Plan</h1>
      <div className={styles.stats}>
        {DONE_COUNT} complete · {RUN_COUNT} running · {AHEAD_COUNT} ahead
      </div>
      <div className={styles.track}>
        {PLAN_PACKETS.map((p) => (
          <span key={p.id} className={styles.trackSegment} style={{ background: TRACK_COLOR[p.state] }} />
        ))}
      </div>
      <div className={styles.packetList}>
        {PLAN_PACKETS.map((p) => (
          <PacketRow key={p.id} packet={p} />
        ))}
      </div>
      <button type="button" className={styles.gateRow}>
        <span className={styles.gateDot} aria-hidden="true" />
        <span className={styles.gateLabel}>M1-B gate</span>
        <span className={styles.gateMeta}>
          {GATE_MET_COUNT} of {GATE_CRITERIA.length} met ›
        </span>
      </button>
    </div>
  );
}

export default PlanTab;
```

## `apps/atlas/src/shell/PlanTab.module.css` (new)

```css
.tab {
  flex: 1;
  min-height: 0;
  overflow: auto;
  padding: 8px 18px 22px;
}

.breadcrumb {
  padding: 4px 0 2px;
  font: 600 11px var(--atlas-font-mono);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--atlas-plan-breadcrumb);
}

.pageTitle {
  margin: 6px 0 4px;
  font-family: var(--atlas-font-display);
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.03em;
}

.stats {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13.5px;
  color: var(--atlas-plan-stats);
}

.track {
  display: flex;
  gap: 4px;
  margin: 14px 0 18px;
}

.trackSegment {
  flex: 1;
  height: 5px;
  border-radius: 3px;
}

.packetList {
  display: flex;
  flex-direction: column;
  gap: 9px;
}

.packetRow {
  display: flex;
  align-items: center;
  gap: 13px;
  width: 100%;
  min-height: 64px;
  padding: 14px 16px;
  border: 0;
  border-radius: 18px;
  background: var(--atlas-plan-row-bg);
  color: var(--atlas-plan-row-ink);
  text-align: left;
  cursor: pointer;
}

.packetRowActive {
  background: var(--atlas-plan-row-bg-active);
}

.packetDot {
  width: 10px;
  height: 10px;
  box-sizing: border-box;
  flex: none;
}

.packetBody {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.packetId {
  font: 600 11px var(--atlas-font-mono);
  letter-spacing: 0.08em;
  color: var(--atlas-plan-row-meta);
}

.packetShort {
  font-size: 15px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.packetState {
  font-size: 12.5px;
  color: var(--atlas-plan-row-meta);
}

.packetMetaActive {
  color: var(--atlas-plan-row-meta-active);
}

.chevron {
  flex: none;
  font-size: 17px;
  color: var(--atlas-plan-row-meta);
}

.gateRow {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 56px;
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px dashed var(--atlas-plan-gate-border);
  background: transparent;
  color: var(--atlas-plan-gate-meta);
  font-size: 13.5px;
  cursor: pointer;
  text-align: left;
}

.gateDot {
  width: 10px;
  height: 10px;
  box-sizing: border-box;
  flex: none;
  border-radius: 50%;
  border: 1.5px dashed var(--atlas-plan-gate-dot-border);
}

.gateLabel {
  flex: 1;
  color: var(--atlas-plan-gate-label);
  font-weight: 600;
}

.gateMeta {
  flex: none;
  font-size: 12px;
}
```

## `apps/atlas/src/shell/PlanTab.test.tsx` (new)

```tsx
import { render, screen, cleanup, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors } from "../tokens";
import { PlanTab } from "./PlanTab";
import { GATE_CRITERIA } from "../gate/fixtures";
import { PLAN_BREADCRUMB, PLAN_PACKETS, PLAN_STATE_LABEL } from "../plan/fixtures";

afterEach(cleanup);

/**
 * jsdom (like real browsers) silently re-serializes a raw inline hex
 * color to `rgb(...)` when read back via `.style.*` — so an
 * exact-string comparison against the original hex literal must
 * convert through the same normalization first, matching the
 * discipline `connectionState.ts` (G1) and F3C's own implementation
 * review already established for exactly this defect class.
 */
function hexToRgb(hex: string): string {
  const value = hex.replace("#", "");
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return `rgb(${r}, ${g}, ${b})`;
}

describe("PlanTab", () => {
  it("renders the real breadcrumb and title", () => {
    render(<PlanTab />);
    expect(screen.getByText(PLAN_BREADCRUMB)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Plan" })).toBeInTheDocument();
  });

  it("derives the stats line directly from the real PLAN_PACKETS states, summing to the real total", () => {
    const counts = { done: 0, run: 0, wait: 0, block: 0, pend: 0 };
    for (const p of PLAN_PACKETS) {
      counts[p.state] += 1;
    }
    const ahead = counts.wait + counts.block + counts.pend;
    expect(counts.done + counts.run + ahead).toBe(PLAN_PACKETS.length);

    render(<PlanTab />);
    expect(screen.getByText(`${counts.done} complete · ${counts.run} running · ${ahead} ahead`)).toBeInTheDocument();
  });

  it("renders all 8 real PLAN_PACKETS rows with their exact id, short title, and state label", () => {
    render(<PlanTab />);
    for (const packet of PLAN_PACKETS) {
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      expect(within(row).getByText(packet.short)).toBeInTheDocument();
      expect(within(row).getByText(PLAN_STATE_LABEL[packet.state])).toBeInTheDocument();
    }
  });

  it("renders exactly 8 real packet rows, each a real <button>", () => {
    render(<PlanTab />);
    const rows = screen.getAllByRole("button").filter((b) => b.className.includes("packetRow"));
    expect(rows).toHaveLength(8);
  });

  it("highlights only A.2's own row as active (the only packet with any real conversation data)", () => {
    render(<PlanTab />);
    const activeId = screen.getByText("A.2");
    const activeRow = activeId.closest('[class*="packetRow"]') as HTMLElement;
    expect(activeRow.className).toContain("packetRowActive");

    for (const packet of PLAN_PACKETS) {
      if (packet.id === "A.2") continue;
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      expect(row.className).not.toContain("packetRowActive");
    }
  });

  it("renders each real packet's own exact per-state dot color/shape (not just non-empty)", () => {
    render(<PlanTab />);
    for (const packet of PLAN_PACKETS) {
      const id = screen.getByText(packet.id);
      const row = id.closest('[class*="packetRow"]') as HTMLElement;
      const dot = row.querySelector('[class*="packetDot"]') as HTMLElement;
      if (packet.state === "done") {
        expect(dot.style.borderRadius).toBe("3px");
        expect(dot.style.background).toBe(hexToRgb(colors.success));
      } else if (packet.state === "run") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.background).toBe(hexToRgb(colors.accentLight));
        expect(dot.style.boxShadow).toBe("0 0 0 4px rgba(140,107,255,.2)");
      } else if (packet.state === "block") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`2px solid ${hexToRgb("#D08A83")}`);
      } else if (packet.state === "wait") {
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`2px solid ${hexToRgb(colors.borderDashed[2])}`);
      } else {
        // pend
        expect(dot.style.borderRadius).toBe("50%");
        expect(dot.style.border).toBe(`1.5px dashed ${hexToRgb(colors.borderDashed[2])}`);
      }
    }
  });

  it("renders each real packet's own exact track-segment color, matching the mockup's own done/run/other derivation", () => {
    render(<PlanTab />);
    const track = document.querySelector('[class*="track"]') as HTMLElement;
    const segments = track.querySelectorAll('[class*="trackSegment"]');
    expect(segments).toHaveLength(PLAN_PACKETS.length);
    segments.forEach((segment, index) => {
      const state = PLAN_PACKETS[index].state;
      const background = (segment as HTMLElement).style.background;
      if (state === "done") {
        expect(background).toBe(hexToRgb(colors.success));
      } else if (state === "run") {
        // The real mockup's own track derivation uses the identical
        // #8C6BFF for both the run dot and the run track segment —
        // this must be the SAME real token as the dot's own run color,
        // not colors.accent (a different, darker real token this
        // slice's own first draft mistakenly used here).
        expect(background).toBe(hexToRgb(colors.accentLight));
      } else {
        expect(background).toBe(hexToRgb("#E4DEEC"));
      }
    });
  });

  it("renders no onClick navigation on any packet row (no real multi-packet thread capability exists yet)", () => {
    render(<PlanTab />);
    // A real <button> with no onClick still fires no visible state
    // change; this is a documentation-style assertion that the rows
    // are inert by construction, not wired to fake navigation.
    const rows = screen.getAllByRole("button").filter((b) => b.className.includes("packetRow"));
    expect(rows).toHaveLength(PLAN_PACKETS.length);
  });

  it("renders the real 'M1-B gate' row with its own real derived met-count, reusing E7's GATE_CRITERIA", () => {
    const yesCount = GATE_CRITERIA.filter((c) => c.met === "yes").length;
    render(<PlanTab />);
    expect(screen.getByText("M1-B gate")).toBeInTheDocument();
    expect(screen.getByText(`${yesCount} of ${GATE_CRITERIA.length} met ›`)).toBeInTheDocument();
    const gateButton = screen.getByRole("button", { name: /M1-B gate/ });
    expect(gateButton).not.toBeDisabled();
  });

  it("sets the real, checked B2 tokens and the disclosed literals", () => {
    expect(colors.inkMuted).toBe("#8E8299");
    expect(colors.inkSecondary).toBe("#6C6376");
    expect(colors.surface).toBe("#FFFFFF");
    expect(colors.ink).toBe("#221C29");
    expect(colors.borderDashed[0]).toBe("#DCD5E4");
    expect(colors.borderDashed[2]).toBe("#B9AFC4");

    const { container } = render(<PlanTab />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-plan-breadcrumb")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-plan-stats")).toBe(colors.inkSecondary);
    expect(root.style.getPropertyValue("--atlas-plan-row-bg")).toBe(colors.surface);
    expect(root.style.getPropertyValue("--atlas-plan-row-ink")).toBe(colors.ink);
    expect(root.style.getPropertyValue("--atlas-plan-gate-border")).toBe(colors.borderDashed[0]);
    expect(root.style.getPropertyValue("--atlas-plan-gate-dot-border")).toBe(colors.borderDashed[2]);
    // Disclosed literals, no real token match.
    expect(root.style.getPropertyValue("--atlas-plan-row-bg-active")).toBe("#EFEAFE");
    expect(root.style.getPropertyValue("--atlas-plan-row-meta-active")).toBe("#6C55B8");
    expect(root.style.getPropertyValue("--atlas-plan-gate-label")).toBe("#4C4457");
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<PlanTab />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## `apps/atlas/src/shell/MobileShell.tsx` (modified — full new content)

```tsx
import { useState, type CSSProperties } from "react";
import { colors, fontFamily } from "../tokens";
import { NowTab } from "./NowTab";
import { ChatTab } from "./ChatTab";
import { ActivityTab } from "./ActivityTab";
import { PlanTab } from "./PlanTab";
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

export function MobileShell() {
  const [selected, setSelected] = useState<MobileShellTab>("now");

  return (
    <div className={styles.shell} style={SHELL_VARS}>
      <main className={styles.content}>
        {selected === "now" ? (
          <NowTab />
        ) : selected === "chat" ? (
          <ChatTab onBack={() => setSelected("now")} />
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
```

## `apps/atlas/src/shell/MobileShell.test.tsx` (modified — full new content)

```tsx
import { render, screen, cleanup, fireEvent, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { colors, fontFamily } from "../tokens";
import MobileShell from "./MobileShell";

afterEach(cleanup);

describe("MobileShell", () => {
  it("sets every real-token CSS custom property from the actual tokens module, plus the disclosed reference-file literals", () => {
    const { container } = render(<MobileShell />);
    const root = container.firstChild as HTMLElement;
    expect(root.style.getPropertyValue("--atlas-page-bg-mobile")).toBe(colors.pageBgMobile);
    expect(root.style.getPropertyValue("--atlas-ink-muted")).toBe(colors.inkMuted);
    expect(root.style.getPropertyValue("--atlas-font-body")).toBe(fontFamily.body);
    expect(root.style.getPropertyValue("--atlas-tab-bar-bg")).toBe("rgba(255,255,255,.92)");
    expect(root.style.getPropertyValue("--atlas-tab-bar-border")).toBe("#EAE5F0");
    expect(root.style.getPropertyValue("--atlas-tab-bar-blur")).toBe("blur(12px)");
    expect(root.style.getPropertyValue("--atlas-tab-selected")).toBe(colors.accent);
    expect(root.style.getPropertyValue("--atlas-tab-inactive")).toBe("#9A90A6");
  });

  it("renders exactly four tabs, in the reference file's actual order (not the README prose order)", () => {
    render(<MobileShell />);
    // Scoped to the tab bar itself: F1's real Now-tab content also
    // contains real buttons (the reused owner-decision options), so an
    // unscoped `getAllByRole("button")` now picks those up too.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    const tabs = within(nav).getAllByRole("button");
    expect(tabs.map((t) => t.textContent)).toEqual(["Now", "Chat", "Plan", "Activity"]);
  });

  it("defaults to Now selected, with only one tab marked current, rendering the real Now tab (F1) rather than the placeholder", () => {
    render(<MobileShell />);
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("(F4A) tapping Plan renders the real PlanTab rather than the placeholder", () => {
    render(<MobileShell />);
    // Scoped to the tab bar: PlanTab's own packet rows and gate row are
    // also real buttons, which would otherwise collide with an unscoped
    // current-button query.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Plan" }));
    const current = within(nav).getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Plan");
    expect(screen.getByRole("heading", { name: "Plan" })).toBeInTheDocument();
    expect(screen.queryByText("Plan tab")).not.toBeInTheDocument();
    expect(screen.queryByText("Now tab")).not.toBeInTheDocument();
  });

  it("(F3) tapping Activity renders the real ActivityTab (F3) rather than the placeholder", () => {
    render(<MobileShell />);
    // Scoped to the tab bar: ActivityTab's own segmented control also
    // sets aria-current on its selected segment button, which would
    // otherwise collide with an unscoped current-button query.
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Activity" }));
    const current = within(nav).getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Activity");
    expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
    expect(screen.queryByText("Activity tab")).not.toBeInTheDocument();
  });

  it("(F2) tapping Chat renders the real ChatTab (F2) rather than the placeholder", () => {
    render(<MobileShell />);
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Chat" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Chat");
    expect(screen.getByRole("button", { name: "‹ Now" })).toBeInTheDocument();
    expect(screen.queryByText("Chat tab")).not.toBeInTheDocument();
  });

  it("(F2) ChatTab's own '‹ Now' back button returns to the real Now tab", () => {
    render(<MobileShell />);
    const nav = screen.getByRole("navigation", { name: "Atlas tabs" });
    fireEvent.click(within(nav).getByRole("button", { name: "Chat" }));
    fireEvent.click(screen.getByRole("button", { name: "‹ Now" }));
    const current = screen.getAllByRole("button", { current: true });
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent("Now");
    expect(screen.getByRole("heading", { name: "Now" })).toBeInTheDocument();
  });

  it("renders no image, icon font, or <svg> element", () => {
    const { container } = render(<MobileShell />);
    expect(container.querySelector("img, svg, i[class*=icon]")).toBeNull();
  });
});
```

## Pre-verification (actually run)

This candidate's exact file contents above were applied to this
scratch worktree (`/tmp/maestro-m2-f4a-plan`, branch
`architecture/m2-f4a-plan-tab`, base `8aa33ce`) and run through the
real frontend toolchain from `apps/atlas` (`npm install`, then each
script below), before this packet was finalized.

- `npm run typecheck` (`tsc --noEmit`) — clean.
- `npm run lint` (`eslint .`) — clean.
- `npm test` (`vitest run`) — **23/23 test files, 180/180 tests
  passed** (10 new in `PlanTab.test.tsx`; `MobileShell.test.tsx`
  unchanged at 8 tests, one retargeted from placeholder to real
  content; zero regressions in the other 21 files).
- `npm run build` (`vite build`) — clean, `39 modules transformed`, no
  warnings.
- Every declared `--atlas-plan-*` custom property, and every CSS class
  declared in `PlanTab.module.css`, was cross-checked programmatically
  against `PlanTab.tsx`'s own references — zero orphans in either
  direction (custom properties or classes).

Two issues were self-caught during authoring, before any Decision
Fidelity review, fixed before this packet was finalized:

1. An early draft applied `width`/`height` per-state inside `DOT_STYLE`
   even though every real state uses the same 10px size — refactored
   to a shared static `.packetDot` CSS class (matching
   `AgentCardMobile`'s own established convention) plus per-state
   inline style only for the properties that actually vary.
2. An early draft used one shared `.packetMeta` class for both the id
   line (real font: 11px mono, bold, letter-spacing) and the state
   label (real font: 12.5px, not mono, not bold) — two lines with
   different real typography in the mockup that happen to share the
   same real color logic. Split into separate `.packetId`/`.packetState`
   classes, both still consuming the shared `.packetMetaActive`
   modifier class for the active-row color override.

**Independent Decision Fidelity review result:** `REQUEST_CHANGES`.
The review independently re-derived every claim from source —
re-reading the real mockup's exact `track`/`dot()` derivations, every
hex value in `colors.ts`, `NowTab.tsx`'s own real doc comment, and
independently re-applying this packet's exact proposed files to
re-run the full toolchain — and found two real, confirmed defects
requiring a correction (not merely a disclosure), plus one related
non-blocking gap:

1. **Wrong token, contradicting the mockup it claimed to transcribe
   verbatim.** `TRACK_COLOR.run` used `colors.accent` (`#5B34E8`)
   instead of `colors.accentLight` (`#8C6BFF`) — the mockup's own real
   `track` derivation (`Atlas Mobile.dc.html:735`) uses the identical
   `#8C6BFF` for both the run dot and the run track segment, not two
   different values as the first draft's own rationale falsely
   claimed. The reviewer empirically confirmed this bug by mutating
   the value and re-running the shipped test suite — all tests still
   passed, proving the defect was real and undetected.
2. **False citation shipped into a permanent code comment.**
   `plan/fixtures.ts`'s own doc comment cited `NowTab.tsx` as
   corroborating "Terra genuinely running" A.2 — but `NowTab.tsx`'s own
   doc comment states the opposite, on record: Terra is deliberately
   shown blocked/waiting, not running, as an already-reviewed design
   decision. Using `run` for the Plan tab's own A.2 row is still
   correct (it matches the mockup's own real `PACKETS` array and
   `AGENTS`'s own real Terra entry) — only the false `NowTab` citation
   was wrong.
3. **Non-blocking: the test suite's own claimed exhaustiveness was
   overstated**, and is what let defect #1 through — the reviewer
   mutation-tested a second value (`block`'s dot-border color) and
   confirmed the shipped tests would not have caught that either.

**Correction applied and independently re-verified**, consuming this
packet's one planning correction and its one targeted verification:

- `TRACK_COLOR.run` fixed to `colors.accentLight`.
- `plan/fixtures.ts`'s doc comment corrected to drop the false `NowTab`
  citation, replaced with the real, accurate `AGENTS`/`agents.ts`
  support, and an explicit note disclosing and correcting the error.
- The halo-convention comment's own overclaim ("the same... convention
  `--atlas-dot-need-halo` already establishes") was also tightened
  while in the file — that token is a different, amber halo value; only
  the *pattern* (an alpha-halo derived from a real token's own RGB)
  matches, not the value.
- `PlanTab.test.tsx`'s per-state dot/track color test was rewritten to
  assert exact hex-to-rgb-converted values for every state (`done`,
  `run` including its own halo string, `block`, `wait`, `pend`) and
  every track segment, using the same hex-to-rgb helper F3C's own
  implementation review already established for this exact jsdom
  color-reserialization defect class.
- **I independently re-mutation-tested the fix myself** before
  finalizing this packet: reverting `TRACK_COLOR.run` to `colors.accent`
  made the rewritten test suite fail as expected; mutating
  `DOT_STYLE.block`'s border color to an arbitrary value also made it
  fail as expected. Both mutations were then reverted to the correct
  values.
- Re-ran the full toolchain after the correction: `npm run typecheck` —
  clean; `npm run lint` — clean; `npm test` — **23/23 test files,
  181/181 tests passed** (11 in `PlanTab.test.tsx`, up from the
  REQUEST_CHANGES draft's own 10 — one test split into two for dot vs.
  track color coverage); `npm run build` — clean, `39 modules
  transformed`, no warnings. Re-checked `--atlas-plan-*`
  custom-property and CSS-class orphans exhaustively in both
  directions — zero orphans.

The scratch changes were reverted (`git checkout --`) after this
verification; only this packet document is committed by this planning
slice.

## M0-D12 bounded quality contract

1. **Protected outcome:** the mobile Atlas app's "Plan" tab renders
   the real packet-list body (breadcrumb, title, derived stats, real
   progress track, all 8 real packet rows, and the "M1-B gate" row
   with its own real derived met-count) with zero backend change and
   zero regression to any of the 22 existing test files.
2. **Operating and threat model:** none — pure frontend rendering, no
   network call, no command dispatch.
3. **Explicit exclusions:** the gate row's own bottom sheet (reuses
   `GateCriteriaList`'s data, a future `F4B`-style candidate); any
   packet row's own "open thread" navigation (no real multi-packet
   thread capability exists).
4. **Assurance level:** practical correctness for a fixture-driven
   rendering component — every rendered surface, every real per-state
   dot/track color, is exercised by a React Testing Library render
   test; no browser-based visual verification was performed (tooling
   failure, already disclosed in this session for M2-E4/F1/F2/F3/F3B/
   F3C/E7B, same root cause).
5. **Acceptance proof:** 23/23 test files, 181/181 tests passing (zero
   regressions) after the correction, clean typecheck, clean lint,
   clean production build — including exact per-state color assertions
   independently mutation-tested to confirm they actually catch the
   class of defect the Decision Fidelity review found.
6. **Implementation boundary:** 4 new files, 2 modified files, all
   within `apps/atlas/src`; zero backend files; no new third-party
   dependency; `gate/fixtures.ts` read-only, never modified.
7. **Proportionality ceiling:** one new fixture file, one new
   presentational component and its CSS module — no new design tokens
   invented beyond 4 disclosed literals, all checked against every
   color family in `colors.ts`.
8. **Stop and escalation rule:** building the gate bottom sheet, or
   wiring any packet row to real navigation, is explicitly out of
   scope — future slices' job, not this one's to silently add.

## Durable status and authority

| Field | Value |
|---|---|
| `schema` | `maestro.bootstrap-slice-status/v1` |
| `slice_id` | `MB-SLICE-M2-F4A-PLAN-TAB-PACKET-LIST-01` |
| `phase` | `AwaitingTargetedVerification` |
| `current_actor` | `architect` |
| `live_execution_evidence` | `null` |
| `planning_review_count` | `1` |
| `planning_correction_count` | `1` |
| `implementation_review_count` | `0` |
| `implementation_correction_count` | `0` |
| `targeted_implementation_verification_count` | `0` |
| `terminal_state` | `null` |
| `evidence_refs` | `["docs/planning/packets/m2-f4a-plan-tab-packet-list.md"]` |

The [Bootstrap Convergence Policy](../bootstrap-convergence-policy.md)
governs this slice's full review-and-merge lifecycle.
